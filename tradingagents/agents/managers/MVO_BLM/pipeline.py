from typing import Dict, List, Tuple
import numpy as np
import json
import os
from .data_utils import fetch_returns_matrix, cov_mu_from_returns
from .blm import black_litterman
from .mvo import mean_variance_optimize


def ensure_portfolio_initialized(portfolio_path: str):
    if not os.path.exists(portfolio_path):
        with open(portfolio_path, 'w') as f:
            json.dump({"portfolio": {}, "liquid": 1000000}, f, indent=2)


def read_portfolio(portfolio_path: str) -> Dict:
    ensure_portfolio_initialized(portfolio_path)
    with open(portfolio_path, 'r') as f:
        return json.load(f)


def write_portfolio(portfolio_path: str, data: Dict):
    with open(portfolio_path, 'w') as f:
        json.dump(data, f, indent=2)


def holdings_to_weights(holdings: Dict[str, Dict], prices: Dict[str, float]) -> Dict[str, float]:
    values = {}
    for t, info in holdings.items():
        qty = float(info.get('totalAmount', 0))
        px = float(prices.get(t, 0.0))
        values[t] = qty * px
    total = sum(values.values())
    if total <= 0:
        return {t: 0.0 for t in values}
    return {t: v / total for t, v in values.items()}


def build_views_from_decisions(decisions: Dict[str, str]) -> Dict[str, float]:
    # Map SELL=-0.02, HOLD=0, BUY=+0.02 annualized simple views
    v = {}
    for t, a in decisions.items():
        a_up = (a or '').upper()
        if a_up == 'BUY':
            v[t] = 0.02
        elif a_up == 'SELL':
            v[t] = -0.02
        else:
            v[t] = 0.0
    return v


def size_positions(
    tickers: List[str],
    date_str: str,
    decisions: Dict[str, str],
    portfolio_path: str,
    prices: Dict[str, float],
    lookback_days: int = 252,
    allow_short: bool = False,
    min_lot: int = 1,
    views: Dict[str, float] | None = None,
) -> Dict[str, Dict]:
    """
    Perform daily MVO-BLM sizing based on decisions.
    - If already in position, do not add/sell more; resize relative via weights.
    - If SELL with no holdings, short. If BUY with no holdings, long.
    - Start portfolio with 100,000 cash if absent.
    """
    portfolio = read_portfolio(portfolio_path)
    holdings = portfolio.get('portfolio', {})

    rets, cols = fetch_returns_matrix(tickers, date_str, lookback_days)
    cov, mu = cov_mu_from_returns(rets)
    if not cols:
        return {}

    # Align arrays with cols ordering
    tickers_aligned = cols
    # Market weights from current holdings
    mkt_w = np.array([holdings_to_weights(holdings, prices).get(t, 0.0) for t in tickers_aligned])
    bl_views = views if views is not None else build_views_from_decisions({t: decisions.get(t, 'HOLD') for t in tickers_aligned})
    mu_bl, cov_bl, _ = black_litterman(
        cov,
        mkt_w if mkt_w.sum() > 0 else np.ones(len(cols)) / len(cols),
        bl_views,
        tickers_aligned,
    )

    w = mean_variance_optimize(mu_bl, cov_bl, long_only=True)

    # Compute target positions by weight
    total_cash = float(portfolio.get('liquid', 0))
    current_value = sum(float(holdings.get(t, {}).get('totalAmount', 0)) * float(prices.get(t, 0.0)) for t in tickers_aligned)
    portfolio_value = total_cash + current_value
    if portfolio_value <= 0:
        portfolio_value = 1000000.0

    # Long-only targets (no negative weights)
    targets = {t: max(0.0, w_i) * portfolio_value for t, w_i in zip(tickers_aligned, w)}

    # Translate targets to trades respecting rules
    trades = {}
    for t in tickers_aligned:
        price = float(prices.get(t, 0.0)) or 0.0
        if price <= 0:
            continue
        target_value = targets[t]
        target_qty = max(0, int(target_value // price))
        curr_qty = int(holdings.get(t, {}).get('totalAmount', 0))

        decision = (decisions.get(t, 'HOLD') or '').upper()
        # SELL means zero target in no-shorting regime
        if decision == 'SELL':
            target_qty = 0
        if curr_qty > 0:
            # Already long: move toward non-negative target; SELL can only reduce but never below 0
            if decision == 'SELL':
                # Fully exit
                delta = -curr_qty
            elif decision == 'BUY':
                delta = target_qty - curr_qty
            else:
                delta = target_qty - curr_qty
        elif curr_qty <= 0:
            # Flat or was short: never create/keep shorts
            if decision in ('BUY', 'HOLD'):
                # Treat HOLD as invest-at-minimum if optimizer suggests 0
                qty = target_qty if target_qty > 0 else max(min_lot, 1)
                delta = max(0, qty)
            else:
                # SELL/HOLD when flat or short -> go to 0
                delta = -curr_qty if curr_qty < 0 else 0

        trades[t] = {"delta_shares": delta, "target_qty": target_qty, "current_qty": curr_qty, "price": price}

    return trades


