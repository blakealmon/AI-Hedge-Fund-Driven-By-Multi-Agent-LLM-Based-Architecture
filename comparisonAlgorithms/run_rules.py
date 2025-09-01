import argparse
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pandas as pd

from .data_loading import load_price_csv
from .rules import (
    macd_rule,
    kdj_rule,
    rsi_rule,
    zmr_rule,
    sma_crossover_rule,
    kdj_rsi_combo_rule,  # added
)

RULES = {
    "MACD": macd_rule,
    # "KDJ": kdj_rule,
    # "RSI": rsi_rule,
    "ZMR": zmr_rule,
    "SMA": sma_crossover_rule,
    "KDJ_RSI": kdj_rsi_combo_rule,  # combined confluence rule
}


def simulate_rule(name: str, rule_fn, df: pd.DataFrame, start_date: str, days: int, budget: float,
                  position_step: float = 0.25):
    """Simulate one rule over a window with incremental scaling.

    position_step: fraction of capital to add/remove on each buy/sell signal (default 0.25).
    This increases trade frequency compared to all-in/all-out logic.
    """
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be DatetimeIndex (date parsed earlier)")

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid start_date format: {e}") from e

    window_mask = df.index >= pd.Timestamp(start_date)
    window_index = df.index[window_mask]
    window_dates = window_index[:days]
    if len(window_dates) < days:
        raise ValueError(f"Not enough trading days after {start_date} (needed {days}, have {len(window_dates)})")

    cash = budget
    shares = 0
    trades = 0
    target_position = 0.0  # 0..1 fraction of capital deployed
    equity_curve = []

    for day in window_dates:
        day_df = df.loc[:day]
        close_price = float(day_df['close'].iloc[-1])
        # Get signal (may be None early due to insufficient data)
        try:
            signal = rule_fn(day_df)
        except Exception as e:
            # If rule raises, treat as hold
            signal = None
        decision = signal.decision if signal else 'hold'

        # Adjust target position fraction
        if decision == 'buy':
            target_position = min(1.0, target_position + position_step)
        elif decision == 'sell':
            target_position = max(0.0, target_position - position_step)
        # hold => no change

        # Compute desired shares based on target position and current equity
        current_equity = cash + shares * close_price
        desired_value = target_position * current_equity
        desired_shares = int(desired_value // close_price) if close_price > 0 else 0

        if desired_shares > shares:  # need to buy more
            add_shares = desired_shares - shares
            cost = add_shares * close_price
            if cost > cash:  # adjust to available cash
                add_shares = int(cash // close_price)
                cost = add_shares * close_price
            if add_shares > 0:
                shares += add_shares
                cash -= cost
                trades += 1
        elif desired_shares < shares:  # need to sell some
            sell_shares = shares - desired_shares
            proceeds = sell_shares * close_price
            if sell_shares > 0:
                shares -= sell_shares
                cash += proceeds
                trades += 1

        equity = cash + shares * close_price
        equity_curve.append({
            'date': day.strftime('%Y-%m-%d'),
            'equity': equity,
            'cash': cash,
            'shares': shares,
            'close': close_price,
            'decision': decision,
            'target_position': target_position,
        })

    final_close = df.at[window_dates[-1], 'close']
    try:
        final_price = float(final_close)
    except (TypeError, ValueError):
        final_price = float(pd.to_numeric(final_close))
    final_equity = cash + shares * final_price
    return {
        'rule': name,
        'start_date': start_date,
        'days': days,
        'initial_budget': budget,
        'final_equity': final_equity,
        'return_pct': (final_equity / budget - 1.0) * 100.0,
        'trades': trades,
        'holding_shares': shares,
        'equity_curve': equity_curve,
    }


def run_single_snapshot(df: pd.DataFrame):
    # Original single-evaluation behavior
    from .rules import evaluate_all_rules
    signals = evaluate_all_rules(df)
    print("Signals (single snapshot):")
    for name, sig in signals.items():
        print(f"{name}: decision={sig.decision} value={sig.value:.4f} rationale={sig.rationale}")
    return {k: sig.__dict__ for k, sig in signals.items()}


def run_parallel_simulation(df: pd.DataFrame, start_date: str, days: int, budget: float, max_workers: int | None):
    futures = []
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for name, fn in RULES.items():
            futures.append(ex.submit(simulate_rule, name, fn, df, start_date, days, budget))
        for fut in as_completed(futures):
            results.append(fut.result())
    # Sort results by return descending
    results.sort(key=lambda r: r['return_pct'], reverse=True)
    return results


def main():
    parser = argparse.ArgumentParser(description="Evaluate or simulate technical rules (MACD, KDJ, RSI, ZMR, SMA) on a price CSV.")
    parser.add_argument("csv", help="Path to OHLCV CSV (date, open, high, low, close, volume)")
    parser.add_argument("--out", help="Optional output JSON path", default=None)
    parser.add_argument("--start-date", dest="start_date", help="Start date YYYY-MM-DD for 30-day (or --days) simulation; if omitted runs single snapshot")
    parser.add_argument("--days", type=int, default=30, help="Number of trading days to simulate (default 30)")
    parser.add_argument("--budget", type=float, default=1000000.0, help="Initial budget (default 1000000)")
    parser.add_argument("--workers", type=int, default=None, help="Parallel worker threads (default len(rules))")
    args = parser.parse_args()

    df = load_price_csv(args.csv)

    if args.start_date:
        max_workers = args.workers or len(RULES)
        sim_results = run_parallel_simulation(df, args.start_date, args.days, args.budget, max_workers)
        print(f"\nSimulation Results ({args.days} days starting {args.start_date}, budget {args.budget:,.2f}):")
        for r in sim_results:
            print(f"{r['rule']}: final_equity={r['final_equity']:,.2f} return={r['return_pct']:.2f}% trades={r['trades']} shares={r['holding_shares']}")
        output_obj = {res['rule']: res for res in sim_results}
    else:
        output_obj = run_single_snapshot(df)

    if args.out:
        Path(args.out).write_text(json.dumps(output_obj, indent=2), encoding="utf-8")
        print(f"Saved JSON -> {args.out}")


if __name__ == "__main__":
    main()
