"""Small agent-local indicator helpers."""

from typing import Iterable, Optional


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

