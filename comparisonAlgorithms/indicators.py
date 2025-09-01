import pandas as pd
import numpy as np

# --- Helper Moving Averages ---

def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()

def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()

# --- Core Indicators ---

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

# KDJ (Stochastic + J line)

def kdj(df: pd.DataFrame, period: int = 9, k_smooth: int = 3, d_smooth: int = 3):
    low_min = df['low'].rolling(period).min()
    high_max = df['high'].rolling(period).max()
    rsv = (df['close'] - low_min) * 100 / (high_max - low_min)
    k = rsv.ewm(alpha=1/k_smooth, adjust=False).mean()
    d = k.ewm(alpha=1/d_smooth, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j

# RSI

def rsi(close: pd.Series, period: int = 14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val

# Z-score Momentum Ratio (simplified example of custom ZMR metric)

def zmr(close: pd.Series, lookback: int = 20):
    returns = close.pct_change()
    mean = returns.rolling(lookback).mean()
    std = returns.rolling(lookback).std()
    z_score = (returns - mean) / std
    # Momentum ratio: current z over rolling |z| mean
    denom = z_score.abs().rolling(lookback).mean()
    momentum_ratio = z_score / denom
    return z_score, momentum_ratio
