from typing import Dict, List, Tuple
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta


def fetch_returns_matrix(tickers: List[str], end_date: str, lookback_days: int = 252) -> Tuple[np.ndarray, List[str]]:
    end = datetime.strptime(end_date, "%Y-%m-%d")
    start = end - timedelta(days=lookback_days + 30)
    prices = []
    cols = []
    for t in tickers:
        try:
            hist = yf.Ticker(t).history(start=start, end=end)
            if len(hist) > 2:
                cols.append(t)
                prices.append(hist['Close'].values)
        except Exception:
            continue
    if not prices:
        return np.zeros((0, 0)), []
    # align by min length
    min_len = min(len(p) for p in prices)
    prices = [p[-min_len:] for p in prices]
    mat = np.vstack(prices).T
    rets = (mat[1:] / mat[:-1] - 1.0)
    return rets, cols


def cov_mu_from_returns(returns: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if returns.size == 0:
        return np.zeros((0, 0)), np.zeros((0,))
    # Ensure 2D shape: (T, N)
    if returns.ndim == 1:
        returns = returns.reshape(-1, 1)
    cov = np.cov(returns.T) * 252
    # Coerce 0-d cov (single asset) to 1x1
    if np.ndim(cov) == 0:
        cov = np.array([[float(cov)]])
    mu = returns.mean(axis=0) * 252
    mu = np.atleast_1d(mu).reshape(-1)
    return cov, mu


