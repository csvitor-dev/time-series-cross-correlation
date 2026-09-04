from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from analysis.methods import CorrelationMethod, get_method
from analysis.series import DaySeries, align, day_series
from config import AnalysisConfig


@dataclass(frozen=True)
class AnalysisOutput:
    pairs: dict[str, pd.DataFrame]
    matrix: dict[str, pd.DataFrame]
    coverage: dict[date, float]


class CrossCorrelationEngine:
    def __init__(self, cfg: AnalysisConfig):
        self._cfg = cfg

    def run(self, day_frames: dict[date, pd.DataFrame]) -> AnalysisOutput:
        days = sorted(day_frames)
        series = [day_series(day_frames[d], self._cfg) for d in days]
        methods = [get_method(name) for name in self._cfg.methods]

        pairs = {m.name: self._pairs(days, series, m) for m in methods}
        matrix = {m.name: self._matrix(days, pairs[m.name]) for m in methods}
        coverage = {s.day: s.coverage for s in series}
        return AnalysisOutput(pairs=pairs, matrix=matrix, coverage=coverage)

    def _pairs(
        self, days: list[date], series: list[DaySeries], method: CorrelationMethod
    ) -> pd.DataFrame:
        rows = []
        for i in range(len(days) - 1, 0, -1):
            for j in range(i - 1, -1, -1):
                x, y = align(series[i], series[j])
                result = method.compute(x, y)
                rows.append(
                    {
                        "method": method.name,
                        "d_i": days[i].isoformat(),
                        "d_j": days[j].isoformat(),
                        "lag_days": (days[i] - days[j]).days,
                        "coefficient": result.coefficient,
                        "p_value": result.p_value,
                        "n": result.n,
                        "stability_std": self._stability(x, y, method),
                    }
                )
        return pd.DataFrame(
            rows,
            columns=[
                "method",
                "d_i",
                "d_j",
                "lag_days",
                "coefficient",
                "p_value",
                "n",
                "stability_std",
            ],
        )

    def _stability(
        self, x: np.ndarray, y: np.ndarray, method: CorrelationMethod
    ) -> float:
        k = self._cfg.stability_subwindows
        if k < 2 or len(x) < 3 * k:
            return float("nan")
        coeffs = [
            method.compute(xs, ys).coefficient
            for xs, ys in zip(np.array_split(x, k), np.array_split(y, k))
        ]
        return float(np.nanstd(coeffs))

    @staticmethod
    def _matrix(days: list[date], pairs: pd.DataFrame) -> pd.DataFrame:
        labels = [d.isoformat() for d in reversed(days)]
        matrix = pd.DataFrame(np.eye(len(labels)), index=labels, columns=labels)
        for row in pairs.itertuples(index=False):
            matrix.loc[row.d_i, row.d_j] = row.coefficient
            matrix.loc[row.d_j, row.d_i] = row.coefficient
        return matrix
