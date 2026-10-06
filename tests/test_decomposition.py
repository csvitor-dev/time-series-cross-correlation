import numpy as np
import pytest

from analysis.decomposition import MovingAverageDecomposer, STLDecomposer, get_decomposer
from config import DecompositionConfig


def _trend_plus_cycle(n: int = 300, period: int = 30) -> tuple[np.ndarray, np.ndarray]:
    t = np.arange(n, dtype=float)
    trend = 100 + 0.05 * t
    rng = np.random.default_rng(0)
    return trend + np.sin(2 * np.pi * t / period) + rng.normal(0, 0.05, n), trend


@pytest.mark.parametrize("name", ["moving_average", "stl"])
def test_components_add_up_to_observed(name):
    values, _ = _trend_plus_cycle()
    result = get_decomposer(name).decompose(values)
    assert len(result.trend) == len(values)
    assert np.allclose(result.trend + result.seasonal + result.resid, values)


@pytest.mark.parametrize("name", ["moving_average", "stl"])
def test_trend_recovers_linear_drift(name):
    values, trend = _trend_plus_cycle()
    result = get_decomposer(name).decompose(values)
    inner = slice(30, -30)
    assert np.max(np.abs(result.trend[inner] - trend[inner])) < 0.2


def test_moving_average_has_no_seasonal_component():
    values, _ = _trend_plus_cycle()
    result = MovingAverageDecomposer(30).decompose(values)
    assert not result.seasonal.any()


def test_stl_extracts_periodic_component():
    values, _ = _trend_plus_cycle()
    result = STLDecomposer(30).decompose(values)
    t = np.arange(len(values))
    assert np.corrcoef(result.seasonal, np.sin(2 * np.pi * t / 30))[0, 1] > 0.95


def test_stl_rejects_short_series():
    with pytest.raises(ValueError):
        STLDecomposer(30).decompose(np.arange(40, dtype=float))


def test_config_parameters_are_applied():
    cfg = DecompositionConfig(ma_window=5, stl_period=10)
    values = np.arange(10, dtype=float) ** 2
    trend = get_decomposer("moving_average", cfg).decompose(values).trend
    assert trend[5] == pytest.approx(np.mean(values[3:8]))


def test_unknown_decomposer():
    with pytest.raises(ValueError):
        get_decomposer("x11")
