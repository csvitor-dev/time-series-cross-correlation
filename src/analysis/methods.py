from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy import stats

from analysis.dcca import rho_q
from analysis.information import linfoot, mutual_information
from config import AnalysisConfig


@dataclass(frozen=True)
class CorrelationResult:
    coefficient: float
    p_value: float
    n: int
    lag: int = 0


class CorrelationMethod(ABC):
    name: str

    @classmethod
    def from_config(cls, cfg: AnalysisConfig) -> CorrelationMethod:
        return cls()

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

    @classmethod
    def from_config(cls, cfg: AnalysisConfig) -> CCFMethod:
        return cls(cfg.ccf_max_lag)

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


def _surrogate_null(
    statistic: Callable[[np.ndarray, np.ndarray], float],
    x: np.ndarray,
    y: np.ndarray,
    surrogates: int,
    seed: int,
) -> np.ndarray:
    n = len(y)
    min_shift = max(1, n // 10)
    shifts = np.arange(min_shift, n - min_shift + 1)
    if surrogates <= 0 or len(shifts) == 0:
        return np.empty(0)
    rng = np.random.default_rng(seed)
    chosen = rng.choice(shifts, size=min(surrogates, len(shifts)), replace=False)
    return np.array([statistic(x, np.roll(y, int(k))) for k in chosen])


def _p_value(observed: float, null: np.ndarray) -> float:
    if len(null) == 0 or np.isnan(observed):
        return float("nan")
    return float((1 + np.sum(np.abs(null) >= abs(observed))) / (1 + len(null)))


class MutualInformationMethod(CorrelationMethod):
    name = "mi"

    def __init__(self, bins: int = 8, surrogates: int = 199, seed: int = 0):
        self._bins = bins
        self._surrogates = surrogates
        self._seed = seed

    @classmethod
    def from_config(cls, cfg: AnalysisConfig) -> MutualInformationMethod:
        return cls(cfg.mi_bins, cfg.surrogates, cfg.seed)

    def _statistic(self, x: np.ndarray, y: np.ndarray) -> float:
        return mutual_information(x, y, self._bins)

    def compute(self, x: np.ndarray, y: np.ndarray) -> CorrelationResult:
        if len(x) < 4 * self._bins or np.std(x) == 0 or np.std(y) == 0:
            return CorrelationResult(coefficient=float("nan"), p_value=float("nan"), n=len(x))
        observed = self._statistic(x, y)
        null = _surrogate_null(self._statistic, x, y, self._surrogates, self._seed)
        bias = float(null.mean()) if len(null) else 0.0
        return CorrelationResult(linfoot(observed - bias), _p_value(observed, null), len(x))


class RhoDCCAMethod(CorrelationMethod):
    name = "rho_dcca"

    def __init__(self, scale: int = 20, q: float = 2.0, surrogates: int = 199, seed: int = 0):
        if q <= 0:
            raise ValueError("q deve ser > 0")
        self._scale = scale
        self._q = q
        self._surrogates = surrogates
        self._seed = seed

    @classmethod
    def from_config(cls, cfg: AnalysisConfig) -> RhoDCCAMethod:
        return cls(cfg.dcca_scale, 2.0, cfg.surrogates, cfg.seed)

    def _statistic(self, x: np.ndarray, y: np.ndarray) -> float:
        return rho_q(x, y, self._scale, self._q)

    def compute(self, x: np.ndarray, y: np.ndarray) -> CorrelationResult:
        if len(x) < 2 * (self._scale + 1) or np.std(x) == 0 or np.std(y) == 0:
            return CorrelationResult(coefficient=float("nan"), p_value=float("nan"), n=len(x))
        observed = self._statistic(x, y)
        null = _surrogate_null(self._statistic, x, y, self._surrogates, self._seed)
        return CorrelationResult(observed, _p_value(observed, null), len(x))


class MFDCCAMethod(RhoDCCAMethod):
    name = "mf_dcca"

    def __init__(self, scale: int = 20, q: float = 4.0, surrogates: int = 199, seed: int = 0):
        super().__init__(scale, q, surrogates, seed)

    @classmethod
    def from_config(cls, cfg: AnalysisConfig) -> MFDCCAMethod:
        return cls(cfg.dcca_scale, cfg.mfdcca_q, cfg.surrogates, cfg.seed)


METHODS: dict[str, type[CorrelationMethod]] = {
    PearsonMethod.name: PearsonMethod,
    SpearmanMethod.name: SpearmanMethod,
    CCFMethod.name: CCFMethod,
    MutualInformationMethod.name: MutualInformationMethod,
    RhoDCCAMethod.name: RhoDCCAMethod,
    MFDCCAMethod.name: MFDCCAMethod,
}


def get_method(name: str, cfg: AnalysisConfig | None = None) -> CorrelationMethod:
    try:
        cls = METHODS[name]
    except KeyError:
        raise ValueError(f"método de correlação desconhecido: {name}") from None
    return cls.from_config(cfg or AnalysisConfig())
