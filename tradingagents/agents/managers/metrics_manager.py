import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

EPSILON = 1e-9


def _daterange(start_dt: datetime, end_dt: datetime) -> List[str]:
    days = (end_dt - start_dt).days
    return [(start_dt + timedelta(n)).strftime("%Y-%m-%d") for n in range(days + 1)]


def _load_values(out_root: str, ordered_days: List[str]) -> Dict[str, float]:
    values: Dict[str, float] = {}
    for d in ordered_days:
        snap_path = Path(out_root) / d / f"portfolio_snapshot_{d}.json"
        if not snap_path.exists():
            continue
        try:
            data = json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        portfolio = data.get("portfolio", {}) if isinstance(data.get("portfolio"), dict) else {}
        liquid = float(data.get("liquid", 0.0) or 0.0)
        total = liquid
        for _, info in portfolio.items():
            qty = float(info.get("totalAmount", 0.0) or 0.0)
            px = float(info.get("last_price", 0.0) or 0.0)
            total += qty * px
        values[d] = total
    return values


def update_metrics_for_date(trade_date: str, out_root: str = "testing", model_name: str = "unknown-model") -> None:
    """Compute rolling performance up to trade_date and update snapshots and portfolio.json.

    - Adds portfolio_value, cash, buying_power, daily_return, cumulative_return, drawdown,
      rolling_sharpe, rolling_sortino, rolling_calmar to the day's snapshot.
    - Updates testing/portfolio.json with rolling summary under "metrics".
    - Writes/updates a statistics file under testing/ named
      f"{model_name}[first_day]-[{trade_date}]-statistics.json" with a compact summary only.
    """
    try:
        end_dt = datetime.strptime(trade_date, "%Y-%m-%d")
    except Exception:
        return

    # Find earliest snapshot to start rolling from
    root = Path(out_root)
    days_present = sorted([p.name for p in root.iterdir() if p.is_dir() and len(p.name) == 10 and p.name[4] == '-' and p.name[7] == '-'])
    days_present = [d for d in days_present if d <= trade_date]
    if not days_present:
        return
    start_date = days_present[0]
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    ordered_days = [d for d in _daterange(start_dt, end_dt) if (root / d / f"portfolio_snapshot_{d}.json").exists()]
    if not ordered_days:
        return

    values = _load_values(out_root, ordered_days)
    if not values:
        return

    # Daily returns, cumulative, drawdowns
    first_val = values[ordered_days[0]]
    daily_returns: Dict[str, float] = {}
    cumulative_returns: Dict[str, float] = {}
    drawdowns: Dict[str, float] = {}
    running_peak = -float("inf")
    prev_val = None
    for d in ordered_days:
        val = values[d]
        if prev_val is None or prev_val == 0:
            r = 0.0
        else:
            r = (val - prev_val) / (prev_val + EPSILON)
        daily_returns[d] = r
        cumulative_returns[d] = (val - first_val) / (first_val + EPSILON)
        running_peak = max(running_peak, val)
        drawdowns[d] = 0.0 if running_peak <= 0 else (val - running_peak) / (running_peak + EPSILON)
        prev_val = val

    # Rolling Sharpe/Sortino/Calmar
    rolling_sharpe: Dict[str, float] = {}
    rolling_sortino: Dict[str, float] = {}
    rolling_calmar: Dict[str, float] = {}
    series: List[float] = []
    for i, d in enumerate(ordered_days):
        r = daily_returns[d]
        series.append(r)
        mean_r = sum(series) / max(len(series), 1)
        var_r = sum((x - mean_r) ** 2 for x in series) / max(len(series) - 1, 1)
        std_r = (var_r ** 0.5) if var_r > 0 else 0.0
        negs = [min(x, 0.0) for x in series]
        if any(negs):
            mean_down = sum((x) ** 2 for x in negs) / max(len([x for x in negs if x < 0]), 1)
            down_dev = (abs(mean_down) ** 0.5)
        else:
            down_dev = 0.0
        rolling_sharpe[d] = mean_r / (std_r + EPSILON)
        rolling_sortino[d] = mean_r / (down_dev + EPSILON)
        max_dd_so_far = min(drawdowns[x] for x in ordered_days[: i + 1])
        rolling_calmar[d] = cumulative_returns[d] / (abs(max_dd_so_far) + EPSILON)

    # Update the latest snapshot
    latest = ordered_days[-1]
    snap_path = root / latest / f"portfolio_snapshot_{latest}.json"
    try:
        snap = json.loads(snap_path.read_text(encoding="utf-8"))
    except Exception:
        snap = {}
    # Recompute portfolio value and cash for completeness
    portfolio = snap.get("portfolio", {}) if isinstance(snap.get("portfolio"), dict) else {}
    liquid = float(snap.get("liquid", 0.0) or 0.0)
    total_val = liquid
    for _, info in portfolio.items():
        qty = float(info.get("totalAmount", 0.0) or 0.0)
        px = float(info.get("last_price", 0.0) or 0.0)
        total_val += qty * px
    prev_val_local = values.get(ordered_days[-2]) if len(ordered_days) > 1 else None
    day_ret = 0.0 if not prev_val_local or prev_val_local == 0 else (total_val - prev_val_local) / (prev_val_local + EPSILON)
    snap["portfolio_value"] = total_val
    snap["cash"] = liquid
    snap["buying_power"] = liquid
    snap["daily_return"] = day_ret
    snap["cumulative_return"] = cumulative_returns[latest]
    snap["drawdown"] = drawdowns[latest]
    snap["rolling_sharpe"] = rolling_sharpe[latest]
    snap["rolling_sortino"] = rolling_sortino[latest]
    snap["rolling_calmar"] = rolling_calmar[latest]
    snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")

    # Update top-level portfolio.json metrics
    try:
        portfolio_json = Path("testing/portfolio.json").resolve()
        if portfolio_json.exists():
            port = json.loads(portfolio_json.read_text(encoding="utf-8"))
            port["metrics"] = {
                "as_of": latest,
                "total_return": cumulative_returns[latest],
                "max_drawdown": min(drawdowns.values()) if drawdowns else 0.0,
                "rolling_sharpe": rolling_sharpe[latest],
                "rolling_sortino": rolling_sortino[latest],
                "rolling_calmar": rolling_calmar[latest],
            }
            portfolio_json.write_text(json.dumps(port, indent=2), encoding="utf-8")
    except Exception:
        pass

    # Do NOT write per-day statistics files here. Final statistics are computed once at the end
    # of a multi-day run by the testing harness (compute_backtest_statistics).


