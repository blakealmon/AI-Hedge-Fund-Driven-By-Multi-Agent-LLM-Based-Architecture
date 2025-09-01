import argparse
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import pandas_market_calendars as mcal  # type: ignore
except Exception:
    mcal = None

import yfinance as yf  # fallback only

from tradingagents.agents.managers.MVO_BLM.pipeline import size_positions
from tradingagents.dataflows import interface as data_interface
from tradingagents.default_config import DEFAULT_CONFIG


def _normalize_base(sym: str) -> str:
    return str(sym).strip().upper().lstrip("$")


def _normalize_for_yf(sym: str) -> str:
    # Yahoo prefers hyphen for share classes, not dot
    return _normalize_base(sym).replace(".", "-")


def _load_tickers(path: str | None) -> List[str]:
    if not path:
        return []
    p = Path(path).resolve()
    if not p.exists():
        return []
    txt = p.read_text(encoding="utf-8")
    raw = [x.strip() for x in txt.replace("\n", " ").replace(",", " ").split(" ") if x.strip()]
    seen = set()
    out: List[str] = []
    for t in raw:
        u = _normalize_base(t)
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _market_days(start_date: str, end_date: str) -> List[str]:
    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")
    if mcal is not None:
        nyse = mcal.get_calendar("XNYS")
        schedule = nyse.schedule(start_date=sd.strftime("%Y-%m-%d"), end_date=ed.strftime("%Y-%m-%d"))
        return [d.strftime("%Y-%m-%d") for d in schedule.index]
    # Fallback: weekdays
    days: List[str] = []
    d = sd
    while d <= ed:
        if d.weekday() < 5:
            days.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return days


def _generate_llm_views(tickers: List[str], date_str: str) -> Dict[str, float]:
    # Lightweight view generator: bias to small positive expected returns
    # to open long-only positions when pipelines are skipped.
    # Values are clamped in size_positions; keep within [-0.1, 0.1].
    views: Dict[str, float] = {t: 0.02 for t in tickers}
    return views


def _get_prices_for_date(tickers: List[str], date_str: str) -> Dict[str, float]:
    prices: Dict[str, float] = {}
    for t in tickers:
        try:
            prices[t] = float(data_interface.get_close_price(t, date_str))
        except Exception:
            try:
                start = datetime.strptime(date_str, "%Y-%m-%d")
                end = start + timedelta(days=1)
                hist = yf.Ticker(_normalize_for_yf(t)).history(start=start, end=end)
                prices[t] = float(hist["Close"].iloc[-1]) if not hist.empty else 0.0
            except Exception:
                prices[t] = 0.0
    return prices


def _execute_trades_long_only(
    trades: Dict[str, Dict],
    decisions: Dict[str, str],
    portfolio_path: Path,
) -> Dict:
    try:
        with open(portfolio_path, "r") as f:
            data = json.load(f)
    except Exception:
        data = {"portfolio": {}, "liquid": 1000000}

    if "portfolio" not in data or not isinstance(data["portfolio"], dict):
        data["portfolio"] = {}
    if "liquid" not in data or not isinstance(data["liquid"], (int, float)):
        data["liquid"] = 1000000

    for sym, tr in (trades or {}).items():
        price = float(tr.get("price", 0.0) or 0.0)
        if price <= 0:
            continue
        holdings = data["portfolio"].get(sym, {"totalAmount": 0})
        current_qty = int(holdings.get("totalAmount", 0))
        proposed_target = int(tr.get("target_qty", current_qty + int(tr.get("delta_shares", 0))))
        target_qty = max(0, proposed_target)  # enforce long-only
        delta = target_qty - current_qty

        if delta > 0:
            max_affordable = int((float(data.get("liquid", 0.0)) // price))
            buy_qty = min(delta, max_affordable)
            if buy_qty <= 0:
                # cannot afford; skip
                holdings["last_price"] = price
                data["portfolio"][sym] = holdings
                continue
            cost = buy_qty * price
            prev_qty = int(holdings.get("totalAmount", 0))
            new_qty = prev_qty + buy_qty
            holdings["totalAmount"] = new_qty
            holdings["last_price"] = price
            prev_entry = float(holdings.get("entry_price", 0.0) or 0.0)
            if prev_qty > 0 and prev_entry > 0:
                holdings["entry_price"] = ((prev_entry * prev_qty) + (price * buy_qty)) / max(new_qty, 1)
            else:
                holdings["entry_price"] = price
            data["liquid"] = float(data.get("liquid", 0.0)) - cost
            data["portfolio"][sym] = holdings
        elif delta < 0:
            sell_qty = min(abs(delta), max(0, current_qty))
            new_qty = current_qty - sell_qty
            proceeds = sell_qty * price
            holdings["totalAmount"] = new_qty
            holdings["last_price"] = price
            if new_qty == 0:
                holdings["entry_price"] = 0.0
            data["liquid"] = float(data.get("liquid", 0.0)) + proceeds
            data["portfolio"][sym] = holdings
        else:
            # HOLD
            holdings["last_price"] = price
            data["portfolio"][sym] = holdings

    with open(portfolio_path, "w") as f:
        json.dump(data, f, indent=2)
    return data


def _snapshot(date_str: str, data: Dict, out_date_dir: Path, portfolio_path: Path | None = None) -> None:
    # Revalue last_price using official resolver for accuracy
    persisted = dict(data)
    for sym, info in list(persisted.get("portfolio", {}).items()):
        try:
            px = float(data_interface.get_close_price(sym, date_str))
        except Exception:
            px = float(info.get("last_price", 0.0) or 0.0)
        info["last_price"] = px
        persisted["portfolio"][sym] = info

    liquid_cash = float(persisted.get("liquid", 0.0) or 0.0)
    net_liq = liquid_cash
    for sym, info in persisted.get("portfolio", {}).items():
        qty = float(info.get("totalAmount", 0) or 0)
        px = float(info.get("last_price", 0.0) or 0.0)
        net_liq += qty * px

    enriched = dict(persisted)
    enriched["net_liquidation"] = net_liq
    enriched["portfolio_value"] = net_liq
    enriched["cash"] = liquid_cash
    enriched["buying_power"] = net_liq

    snap_path = out_date_dir / f"portfolio_snapshot_{date_str}.json"
    snap_path.write_text(json.dumps(enriched, indent=2), encoding="utf-8")
    # Persist revalued state so subsequent days build from this snapshot
    if portfolio_path is not None:
        try:
            portfolio_path.write_text(json.dumps(enriched, indent=2), encoding="utf-8")
        except Exception:
            pass
    print(f"📸 Portfolio snapshot saved -> {snap_path.as_posix()}")


def _build_schedule(start: str, end: str, anchor: str, cadence_days: int) -> List[str]:
    valid_days = _market_days(start, end)
    if not valid_days:
        return []
    # First rebalance at first valid day >= anchor
    anchor_idx = None
    for i, d in enumerate(valid_days):
        if d >= anchor:
            anchor_idx = i
            break
    if anchor_idx is None:
        return []
    dates: List[str] = []
    i = anchor_idx
    while i < len(valid_days):
        dates.append(valid_days[i])
        i += cadence_days
    return dates


def main():
    parser = argparse.ArgumentParser(description="Run MVO-BLM sizing on specified dates or on an anchored cadence.")
    parser.add_argument("--outdir", default="testing", help="Output directory (default: testing)")
    parser.add_argument("--tickers-file", default=str((Path.cwd() / "config" / "universe_tickers.txt").resolve()), help="Path to tickers file")
    parser.add_argument("--dates", default=None, help="Comma-separated list of YYYY-MM-DD rebalance dates")
    parser.add_argument("--start", default=None, help="Start date YYYY-MM-DD (for cadence mode)")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD (for cadence mode)")
    parser.add_argument("--anchor", default="2025-01-14", help="First rebalance date (default: 2025-01-14)")
    parser.add_argument("--cadence", type=int, default=10, help="Cadence in market days (default: 10)")
    args = parser.parse_args()

    out_root = Path(args.outdir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    universe = _load_tickers(args.tickers_file) or ["AAPL", "AMZN", "GOOG", "META", "NVDA"]
    portfolio_path = (Path.cwd() / "testing" / "portfolio.json").resolve()
    if not portfolio_path.exists():
        portfolio_path.parent.mkdir(parents=True, exist_ok=True)
        portfolio_path.write_text(json.dumps({"portfolio": {}, "liquid": 1000000}, indent=2), encoding="utf-8")

    # Build schedule and full market-day range
    cadence_mode = False
    if args.dates:
        target_dates = [d.strip() for d in args.dates.split(",") if d.strip()]
        full_days = list(target_dates)
    else:
        if not args.start or not args.end:
            raise SystemExit("Either --dates or both --start and --end must be provided")
        cadence_mode = True
        target_dates = _build_schedule(args.start, args.end, args.anchor, args.cadence)
        full_days = _market_days(args.start, args.end)

    if not target_dates:
        print("No target dates to run.")
        return

    print(f"🟢 MVO-BLM Runner starting for {len(target_dates)} rebalance dates: {', '.join(target_dates[:5])}{' ...' if len(target_dates) > 5 else ''}")

    # In cadence mode, write revaluation snapshots on non-rebalance days too
    day_iterable = full_days if cadence_mode else target_dates
    target_set = set(target_dates)

    for date_str in day_iterable:
        out_date_dir = out_root / date_str
        out_date_dir.mkdir(parents=True, exist_ok=True)

        if date_str not in target_set and cadence_mode:
            # Non-rebalance market day: revaluation-only snapshot
            print(f"⏩ Reval-only snapshot for {date_str} (no MVO-BLM run)")
            # Ensure no extra reports exist on non-rebalance days
            try:
                rr = out_date_dir / "resizingReport.md"
                if rr.exists():
                    rr.unlink()
            except Exception:
                pass
            try:
                por = out_date_dir / "portfolio_optimizer_report.md"
                if por.exists():
                    por.unlink()
            except Exception:
                pass
            try:
                with open(portfolio_path, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {"portfolio": {}, "liquid": 1000000}
            _snapshot(date_str, data, out_date_dir, portfolio_path)
            continue

        print(f"🧮 [MVO-BLM] Preparing views for {date_str} ({len(universe)} tickers)...")
        llm_views = _generate_llm_views(universe, date_str)
        decisions = {t: ("BUY" if llm_views.get(t, 0.0) > 0 else ("SELL" if llm_views.get(t, 0.0) < 0 else "HOLD")) for t in universe}

        print(f"🧮 [MVO-BLM] Fetching prices for {date_str}...")
        prices = _get_prices_for_date(universe, date_str)
        if sum(1 for p in prices.values() if (p or 0.0) > 0) == 0:
            print(f"Skipping {date_str}: no usable prices for any tickers.")
            try:
                with open(portfolio_path, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {"portfolio": {}, "liquid": 1000000}
            _snapshot(date_str, data, out_date_dir, portfolio_path)
            continue

        print(f"🚀 [MVO-BLM] Running sizing (long-only) for {date_str}...")
        t0 = time.time()
        trades = size_positions(universe, date_str, decisions, str(portfolio_path), prices, views=llm_views)
        elapsed = round(time.time() - t0, 2)
        print(f"✅ [MVO-BLM] Completed sizing for {date_str} in {elapsed}s")

        rr_lines = [f"# Resizing Report ({date_str})\n", "## Trades\n"]
        for t in universe:
            tr = trades.get(t)
            if tr:
                rr_lines.append(f"- {t}: delta={tr.get('delta_shares')}, target_qty={tr.get('target_qty')}, current_qty={tr.get('current_qty')}, price={tr.get('price')}")
            else:
                rr_lines.append(f"- {t}: no change")
        (out_date_dir / "resizingReport.md").write_text("\n".join(rr_lines), encoding="utf-8")

        data_after = _execute_trades_long_only(trades, decisions, portfolio_path)
        _snapshot(date_str, data_after, out_date_dir, portfolio_path)

    print("✅ MVO-BLM Runner finished.")


if __name__ == "__main__":
    main()


