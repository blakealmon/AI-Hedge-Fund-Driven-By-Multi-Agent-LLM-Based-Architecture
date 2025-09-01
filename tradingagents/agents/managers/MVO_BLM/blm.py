from typing import Dict, List, Tuple
import numpy as np


def black_litterman(
    cov: np.ndarray,
    market_weights: np.ndarray,
    views: Dict[str, float],
    tickers: List[str],
    risk_aversion: float = 3.0,
    tau: float = 0.025,
    omega_scale: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Basic Black-Litterman combining equilibrium returns with absolute views.

    Returns (mu_bl, cov_bl, pi)
    """
    n = len(tickers)
    cov = np.asarray(cov)
    w_mkt = market_weights.reshape((n,))
    w_mkt = w_mkt / (w_mkt.sum() if w_mkt.sum() != 0 else 1.0)

    # Equilibrium returns (reverse optimization)
    pi = risk_aversion * cov.dot(w_mkt)

    # Views as absolute on each asset (P = I, Q = views vector)
    Q = np.zeros(n)
    for i, t in enumerate(tickers):
        Q[i] = views.get(t, 0.0)
    P = np.eye(n)

    # Uncertainty (Omega) as scaled diagonal of tau*cov
    omega = omega_scale * np.diag(np.diag(P.dot(tau * cov).dot(P.T)))

    # BL posterior
    inv_tau_cov = np.linalg.inv(tau * cov)
    omega_inv = np.linalg.inv(omega)
    middle = inv_tau_cov + P.T.dot(omega_inv).dot(P)
    right = inv_tau_cov.dot(pi) + P.T.dot(omega_inv).dot(Q)
    mu_bl = np.linalg.inv(middle).dot(right)
    cov_bl = np.linalg.inv(middle)

    return mu_bl, cov_bl, pi


