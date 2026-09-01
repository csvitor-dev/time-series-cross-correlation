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


METHODS: dict[str, type[CorrelationMethod]] = {
    PearsonMethod.name: PearsonMethod,
    SpearmanMethod.name: SpearmanMethod,
}


def get_method(name: str) -> CorrelationMethod:
    try:
        return METHODS[name]()
    except KeyError:
        raise ValueError(f"método de correlação desconhecido: {name}") from None
