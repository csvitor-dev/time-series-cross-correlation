from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class CorrelationResult:
    coefficient: float
    p_value: float
    n: int
    lag: int = 0


class CorrelationMethod(ABC):
    name: str

    @abstractmethod
    def compute(self, x: np.ndarray, y: np.ndarray) -> CorrelationResult: ...


class PearsonMethod(CorrelationMethod):
    name = "pearson"

    def compute(self, x: np.ndarray, y: np.ndarray) -> CorrelationResult:
        if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
            return CorrelationResult(coefficient=float("nan"), p_value=float("nan"), n=len(x))
        result = stats.pearsonr(x, y)
        return CorrelationResult(float(result.statistic), float(result.pvalue), len(x))


class SpearmanMethod(CorrelationMethod):
    name = "spearman"

    def compute(self, x: np.ndarray, y: np.ndarray) -> CorrelationResult:
        if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
            return CorrelationResult(coefficient=float("nan"), p_value=float("nan"), n=len(x))
        result = stats.spearmanr(x, y)
        return CorrelationResult(float(result.statistic), float(result.pvalue), len(x))


def _shift(x: np.ndarray, y: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    if lag > 0:
        return x[: len(x) - lag], y[lag:]
    if lag < 0:
        return x[-lag:], y[: len(y) + lag]
    return x, y


class CCFMethod(CorrelationMethod):
    name = "ccf"

    def __init__(self, max_lag: int = 5):
        self._max_lag = max_lag

    def compute(self, x: np.ndarray, y: np.ndarray) -> CorrelationResult:
        best = CorrelationResult(coefficient=float("nan"), p_value=float("nan"), n=len(x), lag=0)
        if self._max_lag <= 0 or len(x) < 3 + 2 * self._max_lag:
            return best
        for lag in range(-self._max_lag, self._max_lag + 1):
            xs, ys = _shift(x, y, lag)
            if len(xs) < 3 or np.std(xs) == 0 or np.std(ys) == 0:
                continue
            result = stats.pearsonr(xs, ys)
            if np.isnan(best.coefficient) or abs(result.statistic) > abs(best.coefficient):
                best = CorrelationResult(
                    coefficient=float(result.statistic),
                    p_value=float(result.pvalue),
                    n=len(xs),
                    lag=lag,
                )
        return best


METHODS: dict[str, type[CorrelationMethod]] = {
    PearsonMethod.name: PearsonMethod,
    SpearmanMethod.name: SpearmanMethod,
    CCFMethod.name: CCFMethod,
}


def get_method(name: str, max_lag: int = 5) -> CorrelationMethod:
    try:
        cls = METHODS[name]
    except KeyError:
        raise ValueError(f"método de correlação desconhecido: {name}") from None
    return cls(max_lag) if cls is CCFMethod else cls()
