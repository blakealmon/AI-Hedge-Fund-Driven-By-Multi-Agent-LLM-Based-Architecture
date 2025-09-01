import json
import os
import math
from typing import Dict, Tuple, List


def load_snapshot(path: str) -> Dict:
    with open(path, "r") as f:
        return json.load(f)


def save_snapshot(path: str, snapshot: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)


def compute_market_value(snapshot: Dict) -> float:
    portfolio = snapshot.get("portfolio", {})
    total = 0.0
    for ticker, info in portfolio.items():
        qty = float(info.get("totalAmount", 0))
        price = float(info.get("last_price", 0.0))
        total += qty * price
    return total


def update_snapshot_prices(snapshot: Dict, prices: Dict[str, float]) -> Dict:
    portfolio = snapshot.get("portfolio", {})
    for ticker, info in portfolio.items():
        if ticker in prices:
            info["last_price"] = float(prices[ticker])
    # update totals
    market_value = compute_market_value(snapshot)
    cash = float(snapshot.get("cash", 0.0))
    net_liq = market_value + cash
    snapshot["portfolio_value"] = net_liq
    snapshot["net_liquidation"] = net_liq
    snapshot["liquid"] = cash
    snapshot["buying_power"] = net_liq
    return snapshot


def holdings_to_weights(snapshot: Dict, tickers: List[str]) -> List[float]:
    market_value = compute_market_value(snapshot)
    if market_value <= 0:
        return [0.0 for _ in tickers]
    weights = []
    portfolio = snapshot.get("portfolio", {})
    for t in tickers:
        qty = float(portfolio.get(t, {}).get("totalAmount", 0))
        price = float(portfolio.get(t, {}).get("last_price", 0.0))
        w = (qty * price) / market_value if market_value > 0 else 0.0
        weights.append(w)
    return weights


def apply_target_weights(
    snapshot_prev: Dict,
    tickers: List[str],
    prices: Dict[str, float],
    target_weights: List[float],
) -> Tuple[Dict, List[Tuple[str, int, int]]]:

    portfolio_prev = snapshot_prev.get("portfolio", {})
    cash_prev = float(snapshot_prev.get("cash", 0.0))
    # compute current market value using latest prices
    temp = {"portfolio": json.loads(json.dumps(portfolio_prev)), "cash": cash_prev}
    temp = update_snapshot_prices(temp, prices)
    market_value = compute_market_value(temp)
    total_equity = market_value + cash_prev

    # target dollar per ticker
    target_dollars = [max(0.0, w) * total_equity for w in target_weights]

    # construct new snapshot
    new_portfolio: Dict[str, Dict] = {}
    changes: List[Tuple[str, int, int]] = []
    cash = cash_prev

    for ticker, td in zip(tickers, target_dollars):
        price = float(prices.get(ticker, 0.0))
        if price <= 0:
            # keep existing holdings if any
            prev_qty = int(portfolio_prev.get(ticker, {}).get("totalAmount", 0))
            if prev_qty > 0:
                new_portfolio[ticker] = {
                    "totalAmount": prev_qty,
                    "last_price": price if price > 0 else float(portfolio_prev.get(ticker, {}).get("last_price", 0.0)),
                    "entry_price": float(portfolio_prev.get(ticker, {}).get("entry_price", 0.0)),
                }
            continue

        target_qty = int(td // price)
        prev_qty = int(portfolio_prev.get(ticker, {}).get("totalAmount", 0))

        # adjust cash for delta shares
        delta_qty = target_qty - prev_qty
        cash -= delta_qty * price

        if target_qty > 0:
            prev_entry = float(portfolio_prev.get(ticker, {}).get("entry_price", 0.0))
            if delta_qty > 0 and prev_qty > 0:
                # weighted average cost for buys
                new_entry = ((prev_qty * prev_entry) + (delta_qty * price)) / float(prev_qty + delta_qty)
            elif delta_qty > 0 and prev_qty == 0:
                new_entry = price
            else:
                # on sell or no change, keep prior entry
                new_entry = prev_entry
            new_portfolio[ticker] = {
                "totalAmount": target_qty,
                "last_price": price,
                "entry_price": float(new_entry),
            }
        if prev_qty != target_qty:
            changes.append((ticker, prev_qty, target_qty))

    # keep tickers not priced today as-is
    for ticker, info in portfolio_prev.items():
        if ticker not in new_portfolio and ticker not in prices:
            new_portfolio[ticker] = {
                "totalAmount": int(info.get("totalAmount", 0)),
                "last_price": float(info.get("last_price", 0.0)),
                "entry_price": float(info.get("entry_price", 0.0)),
            }

    # finalize snapshot
    new_snapshot = {
        "portfolio": new_portfolio,
        "cash": float(cash),
    }
    new_snapshot = update_snapshot_prices(new_snapshot, prices)
    return new_snapshot, changes


def apply_partial_target_weights(
    snapshot_prev: Dict,
    prices: Dict[str, float],
    target_weights_partial: Dict[str, float],
) -> Tuple[Dict, List[Tuple[str, int, int]]]:

    portfolio_prev = snapshot_prev.get("portfolio", {})
    cash = float(snapshot_prev.get("cash", 0.0))

    # Update prices first for accurate valuations
    temp = {"portfolio": json.loads(json.dumps(portfolio_prev)), "cash": cash}
    temp = update_snapshot_prices(temp, prices)
    initial_total_equity = compute_market_value(temp) + float(temp.get("cash", 0.0))

    # Compute subset equity (only rebalance within the subset), not full portfolio
    market_value_total = compute_market_value(temp)
    subset_value = 0.0
    for t in target_weights_partial.keys():
        qty = float(temp.get("portfolio", {}).get(t, {}).get("totalAmount", 0))
        px = float(prices.get(t, temp.get("portfolio", {}).get(t, {}).get("last_price", 0.0)))
        subset_value += qty * px
    # Budget is current subset value plus available cash
    total_equity = subset_value + cash

    # Determine target dollars for subset only, cap per-name to 5% of total portfolio equity
    total_portfolio_equity = market_value_total + cash
    per_name_cap = 0.05 * total_portfolio_equity
    target_dollars = {}
    for t, w in target_weights_partial.items():
        dollars = max(0.0, w) * total_equity
        target_dollars[t] = min(dollars, per_name_cap)
    target_qty = {}
    for t, dollars in target_dollars.items():
        px = float(prices.get(t, portfolio_prev.get(t, {}).get("last_price", 0.0)))
        if px <= 0:
            target_qty[t] = int(portfolio_prev.get(t, {}).get("totalAmount", 0))
        else:
            target_qty[t] = int(dollars // px)

    # First, sell down within subset to free cash
    changes: List[Tuple[str, int, int]] = []
    for t, tq in target_qty.items():
        prev_q = int(portfolio_prev.get(t, {}).get("totalAmount", 0))
        px = float(prices.get(t, portfolio_prev.get(t, {}).get("last_price", 0.0)))
        if tq < prev_q:
            sell_q = prev_q - tq
            cash += sell_q * px
            changes.append((t, prev_q, tq))

    # Then, buy within remaining budget for those needing increase
    buy_reqs = []
    for t, tq in target_qty.items():
        prev_q = int(portfolio_prev.get(t, {}).get("totalAmount", 0))
        if tq > prev_q:
            px = float(prices.get(t, portfolio_prev.get(t, {}).get("last_price", 0.0)))
            need_q = tq - prev_q
            cost = need_q * px
            buy_reqs.append((t, need_q, px, cost))

    total_cost = sum(c for _, _, _, c in buy_reqs)
    scale = 1.0
    # Global cap: don't deploy more than available cash or 5% of total portfolio equity
    allowable_budget = min(cash, 0.05 * total_portfolio_equity)
    if total_cost > allowable_budget and total_cost > 0:
        scale = allowable_budget / total_cost

    # Apply buys with scaling if needed
    new_portfolio = json.loads(json.dumps(portfolio_prev))
    applied_buys = []  # track (t, buy_q, px)
    for t, need_q, px, cost in buy_reqs:
        buy_q = int(need_q * scale)
        if buy_q <= 0:
            continue
        prev_q = int(new_portfolio.get(t, {}).get("totalAmount", 0))
        new_q = prev_q + buy_q
        cash -= buy_q * px
        prev_entry = float(new_portfolio.get(t, {}).get("entry_price", 0.0))
        if prev_q > 0:
            new_entry = ((prev_q * prev_entry) + (buy_q * px)) / float(new_q)
        else:
            new_entry = px
        new_portfolio[t] = {
            "totalAmount": new_q,
            "last_price": px,
            "entry_price": float(new_entry),
        }
        changes.append((t, prev_q, new_q))
        applied_buys.append((t, buy_q, px))

    # Final guard: never allow negative cash due to rounding
    if cash < 0 and applied_buys:
        # Unwind buys starting from largest cash usage
        applied_buys.sort(key=lambda x: x[1] * x[2], reverse=True)
        for t, bq, px in applied_buys:
            if cash >= 0:
                break
            # remove 1 share at a time until cash >= 0 or no more to unwind
            while bq > 0 and cash < 0:
                prev_q = int(new_portfolio.get(t, {}).get("totalAmount", 0))
                if prev_q <= 0:
                    break
                # unwind one share
                new_q = prev_q - 1
                cash += px
                # recompute entry stays the same (removing a share at cost basis doesn't change average cost)
                prev_entry = float(new_portfolio.get(t, {}).get("entry_price", 0.0))
                new_portfolio[t]["totalAmount"] = new_q
                new_portfolio[t]["last_price"] = px
                new_portfolio[t]["entry_price"] = prev_entry
                bq -= 1
        # remove any tickers that reached zero
        for t in list(new_portfolio.keys()):
            if int(new_portfolio[t].get("totalAmount", 0)) <= 0:
                del new_portfolio[t]

    # If cash is still negative (e.g., inherited from prior days or no buys to unwind),
    # enforce emergency sells across holdings to bring cash to non-negative.
    if cash < 0:
        shortfall = -cash
        # Build sell candidates from all holdings with positive quantity and valid prices
        sell_candidates = []  # (ticker, qty, px, market_value)
        for t, info in list(new_portfolio.items()):
            qty = int(info.get("totalAmount", 0))
            if qty <= 0:
                continue
            px = float(prices.get(t, info.get("last_price", 0.0)))
            if px <= 0:
                continue
            sell_candidates.append((t, qty, px, qty * px))
        # Sort by largest market value first to minimize churn
        sell_candidates.sort(key=lambda x: x[3], reverse=True)
        for t, qty, px, _ in sell_candidates:
            if shortfall <= 0:
                break
            # Compute shares to sell to cover remaining shortfall
            sell_qty = min(qty, int(math.ceil(shortfall / px)))
            if sell_qty <= 0:
                continue
            prev_q = int(new_portfolio.get(t, {}).get("totalAmount", 0))
            new_q = prev_q - sell_qty
            cash += sell_qty * px
            shortfall = max(0.0, shortfall - sell_qty * px)
            # Keep entry price constant on sells
            prev_entry = float(new_portfolio.get(t, {}).get("entry_price", 0.0))
            new_portfolio[t]["totalAmount"] = new_q
            new_portfolio[t]["last_price"] = px
            new_portfolio[t]["entry_price"] = prev_entry
            changes.append((t, prev_q, new_q))
        # Drop any positions that went to zero
        for t in list(new_portfolio.keys()):
            if int(new_portfolio[t].get("totalAmount", 0)) <= 0:
                del new_portfolio[t]

    # Ensure all other tickers are preserved unchanged
    # Update prices and totals
    new_snapshot = {"portfolio": new_portfolio, "cash": float(cash)}
    new_snapshot = update_snapshot_prices(new_snapshot, prices)
    # Enforce equity invariance (no jump in net_liquidation due to rebalancing)
    after_equity = compute_market_value(new_snapshot) + float(new_snapshot.get("cash", 0.0))
    delta = initial_total_equity - after_equity
    if abs(delta) > 1e-6:
        new_snapshot["cash"] = float(new_snapshot.get("cash", 0.0) + delta)
        # Recompute aggregates
        new_snapshot = update_snapshot_prices(new_snapshot, prices)
    return new_snapshot, changes

def force_cash_non_negative(snapshot: Dict, prices: Dict[str, float]) -> Dict:
    """
    Ensure snapshot cash is non-negative by selling largest positions first at provided prices.
    Keeps entry prices unchanged on sells. Removes positions that reach zero.
    """
    cash = float(snapshot.get("cash", 0.0))
    if cash >= 0:
        return update_snapshot_prices(snapshot, prices)
    portfolio = json.loads(json.dumps(snapshot.get("portfolio", {})))
    shortfall = -cash
    sell_candidates = []  # (ticker, qty, px, mv)
    for t, info in portfolio.items():
        qty = int(info.get("totalAmount", 0))
        if qty <= 0:
            continue
        px = float(prices.get(t, info.get("last_price", 0.0)))
        if px <= 0:
            continue
        sell_candidates.append((t, qty, px, qty * px))
    sell_candidates.sort(key=lambda x: x[3], reverse=True)
    for t, qty, px, _ in sell_candidates:
        if shortfall <= 0:
            break
        sell_qty = min(qty, int(math.ceil(shortfall / px)))
        if sell_qty <= 0:
            continue
        prev_q = int(portfolio.get(t, {}).get("totalAmount", 0))
        new_q = prev_q - sell_qty
        cash += sell_qty * px
        shortfall = max(0.0, shortfall - sell_qty * px)
        prev_entry = float(portfolio.get(t, {}).get("entry_price", 0.0))
        portfolio[t]["totalAmount"] = new_q
        portfolio[t]["last_price"] = px
        portfolio[t]["entry_price"] = prev_entry
    for t in list(portfolio.keys()):
        if int(portfolio[t].get("totalAmount", 0)) <= 0:
            del portfolio[t]
    out = {"portfolio": portfolio, "cash": float(max(0.0, cash))}
    return update_snapshot_prices(out, prices)


