from typing import List, Tuple
import numpy as np


def rolling_sharpe(returns: List[float], window: int = 20) -> List[float]:
    r = np.array(returns, dtype=float)
    out = []
    for i in range(len(r)):
        s = max(0, i - window + 1)
        w = r[s : i + 1]
        # use sample std (ddof=1) for unbiased volatility estimate
        vol = np.std(w, ddof=1) if w.size > 1 else 0.0
        if w.size < 2 or vol <= 0:
            out.append(float("nan"))
        else:
            out.append(float(np.mean(w) / vol * np.sqrt(252)))
    return out


def rolling_sortino(returns: List[float], window: int = 20) -> List[float]:
    r = np.array(returns, dtype=float)
    out = []
    for i in range(len(r)):
        s = max(0, i - window + 1)
        w = r[s : i + 1]
        # downside semideviation over the full window: sqrt(mean(min(w,0)^2))
        downside = np.minimum(w, 0.0)
        dd = float(np.sqrt(np.mean(np.square(downside)))) if w.size > 0 else 0.0
        if w.size < 2 or dd <= 0:
            out.append(float("nan"))
        else:
            out.append(float(np.mean(w) / dd * np.sqrt(252)))
    return out


def rolling_calmar(returns: List[float], window: int = 60) -> List[float]:
    r = np.array(returns, dtype=float)
    cum = np.cumprod(1.0 + r)
    out = []
    for i in range(len(r)):
        s = max(0, i - window + 1)
        # annualized return approx (daily compounding)
        period = i - s + 1
        if period < 2:
            out.append(float("nan"))
            continue
        ret = (cum[i] / (cum[s - 1] if s > 0 else 1.0)) ** (252.0 / period) - 1.0
        # max drawdown over window
        window_cum = cum[s : i + 1]
        peak = np.maximum.accumulate(window_cum)
        mdd = np.max((peak - window_cum) / peak) if peak.size > 0 else 0.0
        if mdd == 0:
            out.append(float("nan"))
        else:
            out.append(float(ret / mdd))
    return out


