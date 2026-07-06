from typing import List, Tuple

import numpy as np


def calculate_sma(data: List[float], period: int) -> List[float]:
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(data[i - period + 1:i + 1]) / period)
    return result


def calculate_ema(data: List[float], period: int, smoothing: float = 2.0) -> List[float]:
    result = []
    multiplier = smoothing / (1 + period)
    
    for i in range(len(data)):
        if i == 0:
            result.append(data[i])
        elif i < period - 1:
            result.append(None)
        elif i == period - 1:
            sma = sum(data[i - period + 1:i + 1]) / period
            result.append(sma)
        else:
            ema = data[i] * multiplier + result[i - 1] * (1 - multiplier)
            result.append(ema)
    return result


def calculate_macd(
    data: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[List[float], List[float], List[float]]:
    fast_ema = calculate_ema(data, fast_period)
    slow_ema = calculate_ema(data, slow_period)
    
    macd_line = []
    for i in range(len(data)):
        if fast_ema[i] is None or slow_ema[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(fast_ema[i] - slow_ema[i])
    
    signal_line = calculate_ema([x if x is not None else 0 for x in macd_line], signal_period)
    
    histogram = []
    for i in range(len(data)):
        if macd_line[i] is None or signal_line[i] is None:
            histogram.append(None)
        else:
            histogram.append(macd_line[i] - signal_line[i])
    
    return macd_line, signal_line, histogram


def calculate_rsi(data: List[float], period: int = 14) -> List[float]:
    result = []
    gains = []
    losses = []
    
    for i in range(len(data)):
        if i == 0:
            result.append(None)
            gains.append(0)
            losses.append(0)
        else:
            change = data[i] - data[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
            
            if i < period:
                result.append(None)
            else:
                avg_gain = sum(gains[i - period + 1:i + 1]) / period
                avg_loss = sum(losses[i - period + 1:i + 1]) / period
                
                if avg_loss == 0:
                    result.append(100.0)
                else:
                    rs = avg_gain / avg_loss
                    result.append(100 - (100 / (1 + rs)))
    return result


def calculate_bollinger_bands(
    data: List[float],
    period: int = 20,
    num_std: float = 2.0,
) -> Tuple[List[float], List[float], List[float]]:
    sma = calculate_sma(data, period)
    
    upper_band = []
    lower_band = []
    
    for i in range(len(data)):
        if i < period - 1:
            upper_band.append(None)
            lower_band.append(None)
        else:
            window = data[i - period + 1:i + 1]
            std = np.std(window)
            if sma[i] is not None:
                upper_band.append(sma[i] + num_std * std)
                lower_band.append(sma[i] - num_std * std)
            else:
                upper_band.append(None)
                lower_band.append(None)
    
    return upper_band, sma, lower_band


def calculate_momentum(data: List[float], period: int = 10) -> List[float]:
    result = []
    for i in range(len(data)):
        if i < period:
            result.append(None)
        else:
            result.append(data[i] - data[i - period])
    return result


def calculate_roc(data: List[float], period: int = 12) -> List[float]:
    result = []
    for i in range(len(data)):
        if i < period:
            result.append(None)
        else:
            if data[i - period] == 0:
                result.append(None)
            else:
                result.append((data[i] - data[i - period]) / data[i - period] * 100)
    return result


def calculate_volume_ma(data: List[float], period: int = 20) -> List[float]:
    return calculate_sma(data, period)
