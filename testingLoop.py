import argparse
import copy
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple
import time

from tradingagents.graph.trading_graph import TradingAgentsGraph  # [`tradingagents.graph.trading_graph.TradingAgentsGraph`](tradingagents/graph/trading_graph.py)
from tradingagents.default_config import DEFAULT_CONFIG  # [`DEFAULT_CONFIG`](tradingagents/default_config.py)
import dotenv
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.agents.managers.MVO_BLM import size_positions
from tradingagents.dataflows import interface as data_interface
import yfinance as yf
from tradingagents.agents.managers.MVO_BLM import size_positions
from tradingagents.dataflows import interface as data_interface
import yfinance as yf


#./venv/bin/python testingLoop.py AAPL 2025-07-09 2025-07-10 --batch-5-range --outdir testing | cat


dotenv.load_dotenv()

def daterange(start: datetime, end: datetime):
    days = (end - start).days
    for n in range(days + 1):
        yield start + timedelta(n)


def run_range(
    ticker: str,
    start_date: str,
    end_date: str,
    outdir: str = "testing",
    debug: bool = False,
    deep_copy_config: bool = True,
    fail_fast: bool = False,
    show_trace: bool = False,
):
    # Validate dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e} (expected YYYY-MM-DD)") from e
    if end_dt < start_dt:
        raise ValueError("end_date must be >= start_date")

    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Start banner
    print(f"🟢 Starting testing run: {ticker.upper()} {start_date} -> {end_date} | outdir={outdir}")

    base_config = copy.deepcopy(DEFAULT_CONFIG) if deep_copy_config else DEFAULT_CONFIG.copy()
    graph = TradingAgentsGraph(debug=debug, config=base_config)

    for current in daterange(start_dt, end_dt):
        day_str = current.strftime("%Y-%m-%d")
        fname = f"{ticker.upper()}_{day_str}.txt"
        fpath = out_path / fname
        if fpath.exists():
            print(f"⏭️  Skip {day_str} (exists)")
            continue

        print(f"🚀 {ticker.upper()} {day_str} starting")
        try:
            final_state, final_decision = graph.propagate(ticker, day_str)
        except KeyboardInterrupt:
            print("🛑 Interrupted by user.")
            break
        except Exception as e:
            print(f"❌ Error {day_str}: {e}")
            if show_trace:
                traceback.print_exc()
            if fail_fast:
                raise
            continue

        decision_str = final_decision if isinstance(final_decision, str) else str(final_decision)

        # Optional: pull rationale and optimizer excerpt if present
        rationale = ""
        optimizer_excerpt = ""
        if isinstance(final_state, dict):
            rationale = final_state.get("final_trade_rationale") or ""
            po = final_state.get("portfolio_optimization_state") or {}
            if isinstance(po, dict):
                exec_info = po.get("execution") or {}
                if exec_info:
                    optimizer_excerpt = f"Optimizer Execution: {exec_info}"

        content_lines = [
            f"TICKER: {ticker.upper()}",
            f"DATE: {day_str}",
            f"DECISION: {decision_str}",
        ]
        if rationale or optimizer_excerpt:
            content_lines.append("RATIONALE:")
            if rationale:
                content_lines.append(rationale)
            if optimizer_excerpt:
                content_lines.append(optimizer_excerpt)
        file_text = "\n".join(content_lines) + "\n"

        try:
            fpath.write_text(file_text, encoding="utf-8")
            print(f"✅ Saved -> {fpath}")
        except Exception as e:
            print(f"❌ Write failed {fpath}: {e}")

        # Optional: reset per-day mutable internal state if API exposed
        reset_fn = getattr(graph, "reset_daily_state", None)
        if callable(reset_fn):
            reset_fn()

    print("🏁 Completed range.")


def _extract_action_and_rationale(final_state, final_decision) -> Tuple[str, str]:
    try:
        action = None
        # Prefer explicit final_decision if BUY/SELL/HOLD
        if isinstance(final_decision, str) and final_decision.upper() in {"BUY", "SELL", "HOLD"}:
            action = final_decision.upper()
        # Check portfolio optimizer execution
        if not action and isinstance(final_state, dict):
            po = final_state.get("portfolio_optimization_state") or {}
            if isinstance(po, dict):
                exec_info = po.get("execution") or {}
                if isinstance(exec_info, dict) and exec_info.get("action"):
                    action = str(exec_info.get("action")).upper()
        # Parse from trader plan text
        if not action and isinstance(final_state, dict):
            plan = final_state.get("trader_investment_plan") or ""
            text = str(plan).upper()
            if "FINAL TRANSACTION PROPOSAL: **BUY**" in text:
                action = "BUY"
            elif "FINAL TRANSACTION PROPOSAL: **SELL**" in text:
                action = "SELL"
            elif "FINAL TRANSACTION PROPOSAL: **HOLD**" in text:
                action = "HOLD"
        if not action:
            action = "HOLD"
        rationale = ""
        if isinstance(final_state, dict):
            rationale = final_state.get("final_trade_rationale") or ""
        return action, rationale
    except Exception:
        return str(final_decision), ""


def _weights_from_actions(actions: Dict[str, str]) -> Dict[str, float]:
    # Simple heuristic: BUY=1.5, HOLD=1.0, SELL=0.2, then normalize
    raw = {}
    for t, a in actions.items():
        a_up = (a or "").upper()
        score = 1.0
        if a_up == "BUY":
            score = 1.5
        elif a_up == "SELL":
            score = 0.2
        elif a_up == "HOLD":
            score = 1.0
        raw[t] = max(0.0, float(score))
    s = sum(raw.values()) or 1.0
    return {t: round(v / s, 4) for t, v in raw.items()}


def run_batch5_single_day(
    date_str: str,
    out_root: str = "testing",
    debug: bool = False,
    deep_copy_config: bool = True,
    fail_fast: bool = False,
    show_trace: bool = False,
):
    tickers = ["AAPL", "AMZN", "GOOG", "META", "NVDA"]
    out_date_dir = Path(out_root) / date_str
    out_date_dir.mkdir(parents=True, exist_ok=True)

    base_config = copy.deepcopy(DEFAULT_CONFIG) if deep_copy_config else DEFAULT_CONFIG.copy()
    graph = TradingAgentsGraph(debug=debug, config=base_config)

    print(f"🟢 Starting batch-5 testing run for {date_str}: {', '.join(tickers)} | outdir={out_date_dir}")
    t0 = time.time()

    decisions: Dict[str, str] = {}
    rationales: Dict[str, str] = {}

    for ticker in tickers:
        print(f"🚀 {ticker} {date_str} starting")
        try:
            final_state, final_decision = graph.propagate(ticker, date_str)
        except Exception as e:
            print(f"❌ Error {ticker} {date_str}: {e}")
            if show_trace:
                traceback.print_exc()
            if fail_fast:
                raise
            continue

        action, rationale = _extract_action_and_rationale(final_state, final_decision)
        decisions[ticker] = action
        rationales[ticker] = rationale

        file_text = "\n".join([
            f"TICKER: {ticker}",
            f"DATE: {date_str}",
            f"DECISION: {action}",
            "RATIONALE:", 
            rationale or "",
        ]) + "\n"
        (out_date_dir / f"{ticker}.txt").write_text(file_text, encoding="utf-8")
        print(f"✅ Saved -> {(out_date_dir / f'{ticker}.txt').as_posix()}")

    # Consolidated portfolio optimization based on decisions
    weights = _weights_from_actions(decisions)
    toolkit = Toolkit(config=base_config)
    # Optional: include risk parity as a reference baseline
    try:
        rp = toolkit.get_portfolio_risk_parity.invoke({})
    except Exception:
        rp = {"error": "risk parity unavailable"}
    runtime_s = round(time.time() - t0, 2)
    runtime_hms = f"{int(runtime_s//3600):02d}:{int((runtime_s%3600)//60):02d}:{int(runtime_s%60):02d}"

    lines = []
    lines.append(f"# Batch Portfolio Optimizer Report ({date_str})\n")
    lines.append(f"- Runtime: {runtime_hms} ({runtime_s}s)\n")
    lines.append("## Decisions\n")
    for t in tickers:
        if t in decisions:
            lines.append(f"- {t}: {decisions[t]}")
    lines.append("\n## Suggested Weights (normalized from decisions)\n")
    for t, w in weights.items():
        lines.append(f"- {t}: {w}")
    lines.append("\n## Risk Parity Reference\n")
    lines.append("```json")
    import json as _json
    lines.append(_json.dumps(rp, indent=2))
    lines.append("```")
    (out_date_dir / "portfolio_optimizer_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Saved -> {(out_date_dir / 'portfolio_optimizer_report.md').as_posix()}")

    # Resizing report via MVO-BLM (preview of deltas)
    def _get_prices_for_date(tks, d):
        prices: Dict[str, float] = {}
        for t in tks:
            try:
                prices[t] = float(data_interface.get_price_from_csv(t, d))
            except Exception:
                try:
                    hist = yf.Ticker(t).history(period="1d")
                    prices[t] = float(hist['Close'].iloc[-1]) if not hist.empty else 0.0
                except Exception:
                    prices[t] = 0.0
        return prices

    prices = _get_prices_for_date(tickers, date_str)
    # Use testing/portfolio.json for isolation from main config
    portfolio_path = str((Path.cwd() / "testing" / "portfolio.json").resolve())
    trades = size_positions(tickers, date_str, decisions, portfolio_path, prices)
    rr_lines = [f"# Resizing Report ({date_str})\n", "## Trades\n"]
    for t in tickers:
        tr = trades.get(t)
        if tr:
            rr_lines.append(f"- {t}: delta={tr.get('delta_shares')}, target_qty={tr.get('target_qty')}, current_qty={tr.get('current_qty')}, price={tr.get('price')}")
        else:
            rr_lines.append(f"- {t}: no change")
    (out_date_dir / "resizingReport.md").write_text("\n".join(rr_lines), encoding="utf-8")
    print(f"✅ Saved -> {(out_date_dir / 'resizingReport.md').as_posix()}")


def main():
    parser = argparse.ArgumentParser(
        description="Run trading agents over a date range; persist decisions as TICKER_DATE.txt."
    )
    parser.add_argument("ticker", help="Ticker symbol (e.g. AAPL)")
    parser.add_argument("start_date", help="Start date YYYY-MM-DD")
    parser.add_argument("end_date", nargs='?', default=None, help="End date YYYY-MM-DD (optional; defaults to start_date)")
    parser.add_argument("--outdir", default="testing", help="Output directory (default: testing)")
    parser.add_argument("--debug", action="store_true", help="Enable graph debug mode")
    parser.add_argument("--shallow-config", action="store_true", help="Use shallow copy of DEFAULT_CONFIG")
    parser.add_argument("--fail-fast", action="store_true", help="Abort on first error")
    parser.add_argument("--trace", action="store_true", help="Show full tracebacks on errors")
    parser.add_argument("--single-day", action="store_true", help="Run for a single day (end_date = start_date)")
    parser.add_argument("--batch-5", action="store_true", help="Run batch for AAPL, AMZN, GOOG, META, NVDA for a single day")
    parser.add_argument("--batch-5-range", action="store_true", help="Run batch-5 for each day in range")
    args = parser.parse_args()

    resolved_end_date = args.start_date if (args.single_day or not args.end_date) else args.end_date

    if args.batch_5:
        # Force single-day batch for the requested date
        run_batch5_single_day(
            date_str=args.start_date,
            out_root=args.outdir,
            debug=args.debug,
            deep_copy_config=not args.shallow_config,
            fail_fast=args.fail_fast,
            show_trace=args.trace,
        )
    elif args.batch_5_range:
        start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(resolved_end_date, "%Y-%m-%d")
        cur = start_dt
        while cur <= end_dt:
            day = cur.strftime("%Y-%m-%d")
            run_batch5_single_day(
                date_str=day,
                out_root=args.outdir,
                debug=args.debug,
                deep_copy_config=not args.shallow_config,
                fail_fast=args.fail_fast,
                show_trace=args.trace,
            )
            cur += timedelta(days=1)
    else:
        run_range(
            args.ticker,
            args.start_date,
            resolved_end_date,
            args.outdir,
            args.debug,
            deep_copy_config=not args.shallow_config,
            fail_fast=args.fail_fast,
            show_trace=args.trace,
        )


if __name__ == "__main__":
    main()