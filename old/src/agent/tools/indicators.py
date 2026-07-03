"""Agent-local market analysis helpers."""

from math import sqrt
from typing import Iterable, List, Optional, Sequence


def moving_average(values: Iterable[float], window: int) -> Optional[float]:
    series = list(values)
    if not series:
        return None
    tail = series[-window:]
    return sum(tail) / len(tail)


def pct_change(start: float, end: float) -> float:
    if start == 0:
        return 0.0
    return (end / start - 1) * 100


def ema(values: Sequence[float], window: int) -> Optional[float]:
    if not values:
        return None
    alpha = 2 / (window + 1)
    current = float(values[0])
    for value in values[1:]:
        current = alpha * float(value) + (1 - alpha) * current
    return current


def rsi(values: Sequence[float], window: int = 14) -> Optional[float]:
    if len(values) < window + 1:
        return None
    gains: List[float] = []
    losses: List[float] = []
    for prev, cur in zip(values[-window - 1:-1], values[-window:]):
        diff = float(cur) - float(prev)
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values: Sequence[float]) -> dict:
    if len(values) < 35:
        return {"macd": None, "signal": None, "histogram": None}
    macd_series = []
    for idx in range(26, len(values) + 1):
        slice_values = values[:idx]
        fast = ema(slice_values, 12)
        slow = ema(slice_values, 26)
        if fast is not None and slow is not None:
            macd_series.append(fast - slow)
    signal = ema(macd_series, 9) if len(macd_series) >= 9 else None
    macd_value = macd_series[-1] if macd_series else None
    histogram = macd_value - signal if macd_value is not None and signal is not None else None
    return {"macd": macd_value, "signal": signal, "histogram": histogram}


def bollinger(values: Sequence[float], window: int = 20, width: float = 2.0) -> dict:
    if len(values) < window:
        return {"upper": None, "middle": None, "lower": None, "position": None}
    tail = [float(v) for v in values[-window:]]
    middle = sum(tail) / window
    variance = sum((v - middle) ** 2 for v in tail) / window
    stdev = sqrt(variance)
    upper = middle + width * stdev
    lower = middle - width * stdev
    latest = float(values[-1])
    band_width = upper - lower
    position = (latest - lower) / band_width if band_width else 0.5
    return {"upper": upper, "middle": middle, "lower": lower, "position": position}


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], window: int = 14) -> Optional[float]:
    if len(closes) < window + 1:
        return None
    true_ranges = []
    for idx in range(1, len(closes)):
        high = float(highs[idx])
        low = float(lows[idx])
        prev_close = float(closes[idx - 1])
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    tail = true_ranges[-window:]
    return sum(tail) / len(tail) if tail else None


def slope(values: Sequence[float], window: int = 20) -> Optional[float]:
    if len(values) < 2:
        return None
    tail = [float(v) for v in values[-window:]]
    if len(tail) < 2 or tail[0] == 0:
        return None
    return pct_change(tail[0], tail[-1]) / len(tail)


def support_resistance(highs: Sequence[float], lows: Sequence[float], lookback: int = 40) -> dict:
    if not highs or not lows:
        return {"support": None, "resistance": None}
    return {
        "support": min(float(v) for v in lows[-lookback:]),
        "resistance": max(float(v) for v in highs[-lookback:]),
    }
