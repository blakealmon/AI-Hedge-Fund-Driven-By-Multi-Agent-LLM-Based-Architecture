from typing import Dict, List, Tuple, Optional
import numpy as np


def mean_variance_optimize(
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    risk_aversion: float = 3.0,
    long_only: bool = True,
) -> np.ndarray:

    n = expected_returns.shape[0]
    if covariance.shape != (n, n):
        raise ValueError("Covariance shape mismatch")

    # Quadratic utility: maximize mu^T w - (risk_aversion/2) w^T Sigma w
    # -> Solve equivalent to minimize (risk_aversion/2) w^T Sigma w - mu^T w
    # Closed form for unconstrained: w* = (1/risk_aversion) Sigma^{-1} mu
    try:
        inv_cov = np.linalg.pinv(covariance)
    except np.linalg.LinAlgError:
        inv_cov = np.linalg.pinv(covariance + 1e-6 * np.eye(n))

    raw_weights = (1.0 / risk_aversion) * inv_cov @ expected_returns

    if long_only:
        raw_weights = np.maximum(raw_weights, 0.0)

    # Normalize to sum to 1 if any positive weight exists; otherwise equal weight
    s = raw_weights.sum()
    if s > 0:
        weights = raw_weights / s
    else:
        weights = np.ones(n) / n
    return weights


def black_litterman(
    market_weights: np.ndarray,
    covariance: np.ndarray,
    risk_aversion: float,
    P: np.ndarray,
    Q: np.ndarray,
    tau: float = 0.05,
    Omega: Optional[np.ndarray] = None,
) -> np.ndarray:

    n = market_weights.shape[0]
    inv_cov = np.linalg.pinv(covariance)
    # Implied equilibrium returns: pi = lambda * Sigma * w_m
    pi = risk_aversion * covariance @ market_weights

    if P.size == 0:
        return pi

    # Black-Litterman posterior
    tauSigma = tau * covariance
    if Omega is None or Omega.size == 0:
        Omega = np.diag(np.maximum(np.diag(P @ tauSigma @ P.T), 1e-8))
    M = np.linalg.pinv(inv_cov + P.T @ np.linalg.pinv(Omega) @ P)
    mu_bl = M @ (inv_cov @ pi + P.T @ np.linalg.pinv(Omega) @ Q)
    return mu_bl


def build_views_from_prices(
    tickers: List[str],
    price_t_minus_1: Dict[str, float],
    price_t: Dict[str, float],
    top_k: int = 10,
) -> Tuple[np.ndarray, np.ndarray, List[int]]:

    # simple view: top_k by daily return expected to outperform the average
    rets = []
    idxs = []
    for i, t in enumerate(tickers):
        if t in price_t and t in price_t_minus_1 and price_t_minus_1[t] > 0:
            r = (price_t[t] / price_t_minus_1[t]) - 1.0
            rets.append((r, i))
    rets.sort(reverse=True)

    selected = [i for _, i in rets[:top_k]]
    P = []
    Q = []
    for i in selected:
        row = np.zeros(len(tickers))
        row[i] = 1.0
        P.append(row)
        Q.append(0.002)  # small positive tilt
    if len(P) == 0:
        return np.zeros((0, len(tickers))), np.zeros((0,)), []
    return np.vstack(P), np.array(Q), selected


