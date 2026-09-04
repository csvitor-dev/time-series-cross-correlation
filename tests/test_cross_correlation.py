from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from analysis.cross_correlation import CrossCorrelationEngine
from config import AnalysisConfig, Window

CFG = AnalysisConfig(
    methods=["pearson"],
    window=Window(start="09:00", end="10:59", tz="America/Sao_Paulo"),
    stability_subwindows=3,
)
NOON_UTC = 1_781_697_600  # 2026-06-17 09:00 America/Sao_Paulo


def _day_frame(day: date, rng: np.random.Generator) -> pd.DataFrame:
    minutes = 120
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, minutes)))
    base = NOON_UTC + (day - date(2026, 6, 17)).days * 86_400
    return pd.DataFrame(
        {
            "time": [base + 60 * i for i in range(minutes)],
            "close": close,
            "imputed": [False] * minutes,
            "date": [day.isoformat()] * minutes,
        }
    )


def _frames(n: int) -> dict[date, pd.DataFrame]:
    rng = np.random.default_rng(7)
    days = [date(2026, 6, 17) + timedelta(days=k) for k in range(n)]
    return {d: _day_frame(d, rng) for d in days}


def test_pair_count_and_lower_triangle_only():
    n = 6
    output = CrossCorrelationEngine(CFG).run(_frames(n))
    pairs = output.pairs["pearson"]
    assert len(pairs) == n * (n - 1) // 2
    assert (pairs["d_i"] > pairs["d_j"]).all()
    assert (pairs["lag_days"] > 0).all()


def test_matrix_is_symmetric_with_unit_diagonal_and_dn_first():
    output = CrossCorrelationEngine(CFG).run(_frames(5))
    matrix = output.matrix["pearson"]
    assert list(matrix.columns) == list(matrix.index)
    assert matrix.columns[0] == "2026-06-21"
    assert matrix.columns[-1] == "2026-06-17"
    assert np.allclose(np.diag(matrix), 1.0)
    assert np.allclose(matrix.to_numpy(), matrix.to_numpy().T, equal_nan=True)


def test_coverage_reported_per_day():
    output = CrossCorrelationEngine(CFG).run(_frames(3))
    assert set(output.coverage) == {date(2026, 6, 17), date(2026, 6, 18), date(2026, 6, 19)}
    assert all(0.0 <= c <= 1.0 for c in output.coverage.values())
