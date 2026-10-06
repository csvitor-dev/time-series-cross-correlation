from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

from config import DecompositionConfig


@dataclass(frozen=True)
class Decomposition:
    observed: np.ndarray
    trend: np.ndarray
    seasonal: np.ndarray
    resid: np.ndarray


class Decomposer(ABC):
    name: str

    @abstractmethod
    def decompose(self, values: np.ndarray) -> Decomposition: ...


class MovingAverageDecomposer(Decomposer):
    name = "moving_average"

    def __init__(self, window: int = 30):
        if window < 2:
            raise ValueError("ma_window deve ser >= 2")
        self._window = window

    def decompose(self, values: np.ndarray) -> Decomposition:
        observed = np.asarray(values, dtype=float)
        trend = (
            pd.Series(observed)
            .rolling(self._window, center=True, min_periods=1)
            .mean()
            .to_numpy()
        )
        seasonal = np.zeros_like(observed)
        return Decomposition(observed, trend, seasonal, observed - trend)


class STLDecomposer(Decomposer):
    name = "stl"

    def __init__(self, period: int = 30, robust: bool = True):
        if period < 2:
            raise ValueError("stl_period deve ser >= 2")
        self._period = period
        self._robust = robust

    def decompose(self, values: np.ndarray) -> Decomposition:
        observed = np.asarray(values, dtype=float)
        if len(observed) < 2 * self._period + 1:
            raise ValueError("série curta demais para o stl_period configurado")
        fit = STL(observed, period=self._period, robust=self._robust).fit()
        return Decomposition(
            observed,
            np.asarray(fit.trend),
            np.asarray(fit.seasonal),
            np.asarray(fit.resid),
        )


def get_decomposer(name: str, cfg: DecompositionConfig = DecompositionConfig()) -> Decomposer:
    if name == MovingAverageDecomposer.name:
        return MovingAverageDecomposer(cfg.ma_window)
    if name == STLDecomposer.name:
        return STLDecomposer(cfg.stl_period, cfg.stl_robust)
    raise ValueError(f"método de decomposição desconhecido: {name}")
