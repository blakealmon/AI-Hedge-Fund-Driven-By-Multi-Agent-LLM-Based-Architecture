import os
import json
import math
from typing import List, Dict

import numpy as np

from mvo.data import read_prices_csv, previous_trading_day
from mvo.optimizer import mean_variance_optimize, black_litterman, build_views_from_prices
from mvo.portfolio import load_snapshot, save_snapshot, update_snapshot_prices, holdings_to_weights, apply_target_weights, apply_partial_target_weights, force_cash_non_negative
from mvo.reporting import render_resizing_report
from mvo.scheduler import biweekly_rebalance_days
from mvo.llm_views import LLMViewsGenerator
from mvo.metrics import rolling_sharpe, rolling_sortino, rolling_calmar


TESTING_DIR = os.path.dirname(os.path.abspath(__file__))
PRICES_CSV = os.path.join(TESTING_DIR, "stock_prices.csv")


def get_last_existing_snapshot_dir(base_dir: str, start_date: str) -> str:
    # find latest prior folder with portfolio_snapshot_*.json
    candidates = []
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if not os.path.isdir(path):
            continue
        if name < start_date:
            snap = os.path.join(path, f"portfolio_snapshot_{name}.json")
            if os.path.exists(snap):
                candidates.append(name)
    if not candidates:
        # fallback to root portfolio.json
        return ""
    return sorted(candidates)[-1]


def covariance_from_returns(returns: np.ndarray) -> np.ndarray:
    if returns.ndim != 2:
        raise ValueError("returns must be 2D (T x N)")
    if returns.shape[0] < 2:
        return np.eye(returns.shape[1]) * 1e-4
    return np.cov(returns, rowvar=False) + 1e-8 * np.eye(returns.shape[1])


def run(start_date: str = "2025-01-06") -> None:
    base_dir = TESTING_DIR

    dates, date_to_prices = read_prices_csv(PRICES_CSV)
    dates_sorted = sorted(dates)

    # determine rebalancing days
    rebalance_days = set(biweekly_rebalance_days(dates_sorted, start_date))

    # starting portfolio: previous folder snapshot or portfolio.json in root
    prev_dir = get_last_existing_snapshot_dir(base_dir, start_date)
    if prev_dir:
        prev_path = os.path.join(base_dir, prev_dir, f"portfolio_snapshot_{prev_dir}.json")
        snapshot = load_snapshot(prev_path)
    else:
        snapshot = load_snapshot(os.path.join(base_dir, "portfolio.json"))

    # union of tickers from snapshot portfolio
    tickers = list(snapshot.get("portfolio", {}).keys())

    # set up LLM views generator
    api_key = os.getenv("OPENAI_API_KEY")
    llm_key = os.getenv("SK_PROJ_KEY")
    if not api_key and llm_key:
        api_key = llm_key
    llm = LLMViewsGenerator(api_key=api_key)
    use_llm_api = os.getenv("USE_LLM_API", "0") == "1"

    # track portfolio daily returns for metrics
    daily_returns = []

    # progress log file
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    progress_path = os.path.join(results_dir, "progress.log")

    # walk through dates from start_date to last available
    for d in dates_sorted:
        if d < start_date:
            continue
        print(f"Processing {d} ...", flush=True)
        try:
            with open(progress_path, "a") as pf:
                pf.write(f"{d} start\n")
        except Exception:
            pass
        day_dir = os.path.join(base_dir, d)
        os.makedirs(day_dir, exist_ok=True)

        prices_today: Dict[str, float] = date_to_prices.get(d, {})
        # daily snapshot update if not rebalance
        if d not in rebalance_days:
            updated = update_snapshot_prices(json.loads(json.dumps(snapshot)), prices_today)
            # enforce non-negative cash in all written snapshots
            updated = force_cash_non_negative(updated, prices_today)
            save_snapshot(os.path.join(day_dir, f"portfolio_snapshot_{d}.json"), updated)
            # compute portfolio daily return
            mv_prev = sum(
                float(info.get("totalAmount", 0)) * float(info.get("last_price", 0.0))
                for info in snapshot.get("portfolio", {}).values()
            )
            mv_today = sum(
                float(info.get("totalAmount", 0)) * float(prices_today.get(t, info.get("last_price", 0.0)))
                for t, info in snapshot.get("portfolio", {}).items()
            )
            cash_prev = float(snapshot.get("cash", 0.0))
            equity_prev = mv_prev + cash_prev
            r = (mv_today - mv_prev) / equity_prev if equity_prev > 0 else 0.0
            daily_returns.append(r)
            snapshot = updated
            try:
                with open(progress_path, "a") as pf:
                    pf.write(f"{d} snapshot\n")
            except Exception:
                pass
            print(f"{d} snapshot written", flush=True)
            continue

        # Rebalance using MVO-BLM
        # build returns window (use last 10 trading days for LLM views; last 60 for covariance)
        idx = dates_sorted.index(d)
        # Strictly avoid lookahead: only use dates strictly before d
        window_start_cov = max(0, idx - 60)
        window_dates = dates_sorted[window_start_cov:idx]
        returns_rows: List[List[float]] = []
        for i in range(1, len(window_dates)):
            prev_prices = date_to_prices.get(window_dates[i - 1], {})
            cur_prices = date_to_prices.get(window_dates[i], {})
            row = []
            for t in tickers:
                if t in prev_prices and t in cur_prices and prev_prices[t] > 0:
                    r = (cur_prices[t] / prev_prices[t]) - 1.0
                else:
                    r = 0.0
                row.append(r)
            returns_rows.append(row)
        returns_arr = np.array(returns_rows) if returns_rows else np.zeros((0, len(tickers)))

        # historical estimates (shorter window to reduce instability)
        if returns_arr.shape[0] > 0:
            mu_hist = np.clip(returns_arr.mean(axis=0), -0.02, 0.02)
            cov = covariance_from_returns(returns_arr)
            # shrink covariance slightly to reduce leverage to tiny variances
            cov = 0.9 * cov + 0.1 * np.mean(np.diag(cov)) * np.eye(cov.shape[0])
        else:
            mu_hist = np.zeros(len(tickers))
            cov = np.eye(len(tickers)) * 1e-4

        # market weights from current holdings
        market_w = np.array(holdings_to_weights(snapshot, tickers))
        if market_w.sum() == 0:
            market_w = np.ones(len(tickers)) / max(1, len(tickers))

        # LLM-generated views per paper: use last two weeks (approx 10 trading days)
        window_start_llm = max(0, idx - 10)
        window_dates_llm = dates_sorted[window_start_llm:idx]
        # Limit optimization universe for speed: keep top N by current market value
        N = 50
        portfolio = snapshot.get("portfolio", {})
        mv_pairs = []
        for t in tickers:
            qty = float(portfolio.get(t, {}).get("totalAmount", 0))
            px = float(prices_today.get(t, portfolio.get(t, {}).get("last_price", 0.0)))
            mv_pairs.append((t, qty * px))
        mv_pairs.sort(key=lambda x: x[1], reverse=True)
        opt_universe = [t for t, _ in mv_pairs[:N]]

        # For LLM views, restrict to top 10 of that universe
        top_views = opt_universe[:10]
        per_ticker_returns: Dict[str, List[float]] = {t: [] for t in top_views}
        for i in range(1, len(window_dates_llm)):
            prev_prices = date_to_prices.get(window_dates_llm[i - 1], {})
            cur_prices = date_to_prices.get(window_dates_llm[i], {})
            for t in top_views:
                if t in prev_prices and t in cur_prices and prev_prices[t] > 0:
                    per_ticker_returns[t].append((cur_prices[t] / prev_prices[t]) - 1.0)
        P_opt, Q, Omega = llm.generate(d, top_views, per_ticker_returns, num_samples=30, use_api=use_llm_api)
        # Expand P to full universe (K x N) selecting columns for opt_universe
        K = len(top_views)
        N_full = len(tickers)
        P = np.zeros((K, N_full))
        idxs_full = [tickers.index(t) for t in top_views]
        for i, j in enumerate(idxs_full):
            P[i, j] = 1.0

        # get BL-implied expected returns
        risk_aversion = 5.0
        mu_bl = black_litterman(market_w, cov, risk_aversion, P, Q, tau=0.05, Omega=Omega)

        # optimize
        # align mu_bl/cov to full ticker list by embedding opt_universe weights and zero otherwise
        # compute target weights for opt_universe only
        # map indices
        idx_map = {t: i for i, t in enumerate(opt_universe)}
        # reduce covariance to opt universe
        # Build expected returns vector for opt universe
        mu_opt = np.array([mu_bl[t] if isinstance(t, int) else mu_bl[tickers.index(t)] for t in opt_universe]) if len(opt_universe) > 0 else np.array([])
        # Build covariance for opt universe from full cov
        if len(opt_universe) > 0:
            idxs = [tickers.index(t) for t in opt_universe]
            cov_opt = cov[np.ix_(idxs, idxs)]
            target_w_opt = mean_variance_optimize(mu_opt, cov_opt, risk_aversion=risk_aversion, long_only=True)
        else:
            target_w_opt = np.array([])
        # convert to partial weights dict for top 10 holders only (reduce churn)
        top10 = opt_universe[:10]
        partial = {}
        s = 0.0
        for t, w in zip(opt_universe, target_w_opt.tolist() if target_w_opt.size else []):
            if t in top10:
                partial[t] = max(0.0, float(w))
                s += partial[t]
        if s > 0:
            for t in list(partial.keys()):
                partial[t] /= s
        # apply partial rebalance to avoid removing other holdings and prevent negative cash
        new_snapshot, changes = apply_partial_target_weights(snapshot, prices_today, partial)
        # enforce non-negative cash before writing
        new_snapshot = force_cash_non_negative(new_snapshot, prices_today)

        # write outputs: snapshot and resizingReport.md
        save_snapshot(os.path.join(day_dir, f"portfolio_snapshot_{d}.json"), new_snapshot)
        report = render_resizing_report(d, changes)
        with open(os.path.join(day_dir, "resizingReport.md"), "w") as f:
            f.write(report)

        # compute day return using pre-trade holdings to post-trade prices (approximation)
        mv_prev = sum(
            float(info.get("totalAmount", 0)) * float(info.get("last_price", 0.0))
            for info in snapshot.get("portfolio", {}).values()
        )
        mv_today = sum(
            float(info.get("totalAmount", 0)) * float(prices_today.get(t, info.get("last_price", 0.0)))
            for t, info in snapshot.get("portfolio", {}).items()
        )
        cash_prev = float(snapshot.get("cash", 0.0))
        equity_prev = mv_prev + cash_prev
        r = (mv_today - mv_prev) / equity_prev if equity_prev > 0 else 0.0
        daily_returns.append(r)
        snapshot = new_snapshot
        try:
            with open(progress_path, "a") as pf:
                pf.write(f"{d} rebalance\n")
        except Exception:
            pass
        print(f"{d} rebalance written", flush=True)

    # After loop: write results summary with rolling metrics
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    sharpe = rolling_sharpe(daily_returns, window=20)
    sortino = rolling_sortino(daily_returns, window=20)
    calmar = rolling_calmar(daily_returns, window=60)
    with open(os.path.join(results_dir, "rolling_metrics.json"), "w") as f:
        json.dump({"dates": [d for d in dates_sorted if d >= start_date], "sharpe": sharpe, "sortino": sortino, "calmar": calmar}, f, indent=2)


if __name__ == "__main__":
    run()


