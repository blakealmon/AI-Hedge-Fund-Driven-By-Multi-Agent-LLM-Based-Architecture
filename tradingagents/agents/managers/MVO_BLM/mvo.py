from typing import Dict, List, Tuple
import numpy as np


def mean_variance_optimize(
    mu: np.ndarray,
    cov: np.ndarray,
    long_only: bool = False,
) -> np.ndarray:
    """
    Simple risk-aversion 1 optimizer: w ~ inv(cov) * mu, normalized.
    If long_only, negative weights are floored to zero before normalization.
    """
    inv_cov = np.linalg.pinv(cov)
    w = inv_cov.dot(mu)
    if long_only:
        w = np.clip(w, 0, None)
    s = w.sum()
    if s == 0:
        n = len(w)
        return np.ones(n) / n
    return w / s


def to_target_values(weights: np.ndarray, portfolio_value: float) -> Dict[str, float]:
    return {"_vector": (weights * portfolio_value).tolist()}


