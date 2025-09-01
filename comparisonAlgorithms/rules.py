from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd
from .indicators import macd, kdj, rsi, zmr, sma

@dataclass
class Signal:
    name: str
    value: Any
    decision: str  # 'buy', 'sell', 'hold'
    rationale: str


def macd_rule(df: pd.DataFrame) -> Optional[Signal]:
    macd_line, signal_line, hist = macd(df['close'])
    if len(hist.dropna()) < 3:
        return None
    # Classic crossover conditions
    cross_up = macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]
    cross_down = macd_line.iloc[-2] > signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]
    # Additional momentum conditions to increase trade frequency
    hist_rising = hist.iloc[-3] < hist.iloc[-2] < hist.iloc[-1]
    hist_falling = hist.iloc[-3] > hist.iloc[-2] > hist.iloc[-1]
    zero_cross_up = hist.iloc[-2] < 0 <= hist.iloc[-1]
    zero_cross_down = hist.iloc[-2] > 0 >= hist.iloc[-1]

    if cross_up or zero_cross_up or hist_rising:
        return Signal('MACD', float(hist.iloc[-1]), 'buy',
                      'MACD bullish (crossover/zero-cross/momentum rising)')
    if cross_down or zero_cross_down or hist_falling:
        return Signal('MACD', float(hist.iloc[-1]), 'sell',
                      'MACD bearish (crossover/zero-cross/momentum falling)')
    return Signal('MACD', float(hist.iloc[-1]), 'hold', 'MACD mixed')


def kdj_rule(df: pd.DataFrame) -> Optional[Signal]:
    K, D, J = kdj(df)
    if K.isna().iloc[-1] or D.isna().iloc[-1]:
        return None
    # Crossover logic (increases frequency)
    k_cross_up = K.iloc[-2] < D.iloc[-2] and K.iloc[-1] > D.iloc[-1]
    k_cross_down = K.iloc[-2] > D.iloc[-2] and K.iloc[-1] < D.iloc[-1]
    overbought = K.iloc[-1] > 80 and D.iloc[-1] > 80
    oversold = K.iloc[-1] < 20 and D.iloc[-1] < 20
    if k_cross_up or (oversold and J.iloc[-1] < 10):
        return Signal('KDJ', float(J.iloc[-1]), 'buy', 'K%D bullish crossover / oversold rebound')
    if k_cross_down or (overbought and J.iloc[-1] > 90):
        return Signal('KDJ', float(J.iloc[-1]), 'sell', 'K%D bearish crossover / overbought fade')
    return Signal('KDJ', float(J.iloc[-1]), 'hold', 'KDJ neutral')


def rsi_rule(df: pd.DataFrame, low: int = 30, high: int = 70) -> Optional[Signal]:
    val = rsi(df['close'])
    if val.isna().iloc[-1]:
        return None
    current = val.iloc[-1]
    # Midline (50) cross signals to increase activity
    mid_cross_up = val.iloc[-2] < 50 <= current
    mid_cross_down = val.iloc[-2] > 50 >= current
    if current < low or mid_cross_up and current < 55:  # allow early buy when regaining strength
        return Signal('RSI', float(current), 'buy', 'RSI oversold or crossing above 50')
    if current > high or mid_cross_down and current > 45:  # early sell when weakening
        return Signal('RSI', float(current), 'sell', 'RSI overbought or dropping below 50')
    return Signal('RSI', float(current), 'hold', 'RSI neutral')


def zmr_rule(df: pd.DataFrame) -> Optional[Signal]:
    z_score, momentum_ratio = zmr(df['close'])
    if momentum_ratio.isna().iloc[-1]:
        return None
    mr = momentum_ratio.iloc[-1]
    # Lower thresholds for more frequent trades
    if mr > 0.5:
        return Signal('ZMR', float(mr), 'buy', 'Momentum positive (ZMR > 0.5)')
    if mr < -0.5:
        return Signal('ZMR', float(mr), 'sell', 'Momentum negative (ZMR < -0.5)')
    return Signal('ZMR', float(mr), 'hold', 'Momentum neutral band')


def sma_crossover_rule(df: pd.DataFrame, fast: int = 10, slow: int = 30) -> Optional[Signal]:
    # Shorter windows for higher signal frequency
    if len(df) < slow + 5:
        return None
    fast_ma = sma(df['close'], fast)
    slow_ma = sma(df['close'], slow)
    spread = fast_ma.iloc[-1] - slow_ma.iloc[-1]
    prev_spread = fast_ma.iloc[-2] - slow_ma.iloc[-2]
    cross_up = prev_spread < 0 and spread > 0
    cross_down = prev_spread > 0 and spread < 0
    widening_bull = spread > 0 and spread > prev_spread * 1.05  # fast pulling away upward
    widening_bear = spread < 0 and spread < prev_spread * 1.05  # fast pulling away downward (more negative)
    if cross_up or widening_bull:
        return Signal(f'SMA_{fast}_{slow}', float(spread), 'buy', 'Fast SMA bullish (cross/widening)')
    if cross_down or widening_bear:
        return Signal(f'SMA_{fast}_{slow}', float(spread), 'sell', 'Fast SMA bearish (cross/widening)')
    return Signal(f'SMA_{fast}_{slow}', float(spread), 'hold', 'SMA neutral')


def kdj_rsi_combo_rule(df: pd.DataFrame) -> Optional[Signal]:
    """Combined KDJ + RSI rule for confluence-based signals.

    Logic:
      - Build a score from KDJ cross/overbought/oversold and RSI oversold/overbought/midline crosses.
      - +1 for each bullish condition, -1 for each bearish condition.
      - Decision: score >= 1 => buy; score <= -1 => sell; else hold.
    """
    K, D, J = kdj(df)
    r = rsi(df['close'])
    if K.isna().iloc[-1] or D.isna().iloc[-1] or r.isna().iloc[-1]:
        return None
    score = 0
    notes = []

    # KDJ signals
    k_cross_up = K.iloc[-2] < D.iloc[-2] and K.iloc[-1] > D.iloc[-1]
    k_cross_down = K.iloc[-2] > D.iloc[-2] and K.iloc[-1] < D.iloc[-1]
    overbought = K.iloc[-1] > 80 and D.iloc[-1] > 80
    oversold = K.iloc[-1] < 20 and D.iloc[-1] < 20
    if k_cross_up or (oversold and J.iloc[-1] < 10):
        score += 1; notes.append('KDJ bullish')
    if k_cross_down or (overbought and J.iloc[-1] > 90):
        score -= 1; notes.append('KDJ bearish')

    # RSI signals
    r_curr = r.iloc[-1]
    r_prev = r.iloc[-2]
    r_mid_cross_up = r_prev < 50 <= r_curr
    r_mid_cross_down = r_prev > 50 >= r_curr
    if r_curr < 30 or (r_mid_cross_up and r_curr < 55):
        score += 1; notes.append('RSI bullish')
    if r_curr > 70 or (r_mid_cross_down and r_curr > 45):
        score -= 1; notes.append('RSI bearish')

    if score >= 1:
        decision = 'buy'
    elif score <= -1:
        decision = 'sell'
    else:
        decision = 'hold'
    # Value: average of normalized J (scaled ~0-1 via /100) and RSI/100
    value = (min(max(J.iloc[-1]/100.0, -1), 2) + r_curr/100.0) / 2
    rationale = ' | '.join(notes) if notes else 'No clear combined signal'
    return Signal('KDJ_RSI', float(value), decision, rationale)


def evaluate_all_rules(df: pd.DataFrame) -> Dict[str, Signal]:
    """Run all rule functions and return their signals."""
    rules = [macd_rule, kdj_rule, rsi_rule, zmr_rule, sma_crossover_rule, kdj_rsi_combo_rule]
    results: Dict[str, Signal] = {}
    for rule in rules:
        try:
            sig = rule(df)
        except TypeError:
            sig = rule(df)  # fallback
        if sig:
            results[sig.name] = sig
    return results
