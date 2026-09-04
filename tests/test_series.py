import numpy as np
import pandas as pd
import pytest

from analysis.series import align, day_series
from config import AnalysisConfig, Window

CFG = AnalysisConfig(window=Window(start="09:00", end="09:04", tz="America/Sao_Paulo"))
NOON_UTC = 1_781_697_600  # 2026-06-17 09:00 America/Sao_Paulo


def _frame(closes, imputed=None):
    n = len(closes)
    return pd.DataFrame(
        {
            "time": [NOON_UTC + 60 * i for i in range(n)],
            "close": closes,
            "imputed": imputed if imputed is not None else [False] * n,
            "date": ["2026-06-17"] * n,
        }
    )


def test_log_return_and_grid_length():
    series = day_series(_frame([100.0, 101.0, 102.0]), CFG)
    assert len(series.values) == 4
    assert series.values[0] == pytest.approx(np.log(101 / 100))
    assert series.values[1] == pytest.approx(np.log(102 / 101))
    assert series.values[2] == 0.0


def test_coverage_counts_real_minutes():
    series = day_series(_frame([100.0, 101.0, 102.0]), CFG)
    assert series.coverage == pytest.approx(3 / 5)


def test_imputed_rows_do_not_count_as_coverage():
    series = day_series(_frame([100.0] * 5, imputed=[False, False, True, True, True]), CFG)
    assert series.coverage == pytest.approx(2 / 5)


def test_align_truncates_to_shortest():
    a = day_series(_frame([100.0, 101.0, 102.0]), CFG)
    b = day_series(_frame([100.0, 99.0]), CFG)
    x, y = align(a, b)
    assert len(x) == len(y)
