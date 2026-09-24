import numpy as np
import pytest

from analysis.methods import get_method

METHODS = ["pearson", "spearman"]


@pytest.mark.parametrize("name", METHODS)
def test_perfect_positive(name):
    x = np.arange(50, dtype=float)
    result = get_method(name).compute(x, 2 * x + 1)
    assert result.coefficient == pytest.approx(1.0)
    assert result.p_value < 1e-6
    assert result.n == 50


@pytest.mark.parametrize("name", METHODS)
def test_perfect_negative(name):
    x = np.arange(50, dtype=float)
    result = get_method(name).compute(x, -x)
    assert result.coefficient == pytest.approx(-1.0)


@pytest.mark.parametrize("name", METHODS)
def test_independent_is_near_zero(name):
    rng = np.random.default_rng(0)
    result = get_method(name).compute(rng.normal(size=2000), rng.normal(size=2000))
    assert abs(result.coefficient) < 0.1
    assert result.p_value > 0.05


def test_constant_input_returns_nan():
    result = get_method("pearson").compute(np.ones(10), np.arange(10, dtype=float))
    assert np.isnan(result.coefficient)


def test_unknown_method():
    with pytest.raises(ValueError):
        get_method("kendall")


def test_ccf_recovers_known_lag():
    rng = np.random.default_rng(0)
    x = rng.normal(size=200)
    shift = 3
    y = np.concatenate([rng.normal(size=shift), x[: len(x) - shift]])
    result = get_method("ccf", max_lag=5).compute(x, y)
    assert result.lag == shift
    assert result.coefficient == pytest.approx(1.0, abs=1e-9)
    assert result.n == len(x) - shift


def test_ccf_zero_lag_matches_pearson():
    rng = np.random.default_rng(1)
    x = rng.normal(size=100)
    y = 2 * x + 1
    result = get_method("ccf", max_lag=5).compute(x, y)
    assert result.lag == 0
    assert result.coefficient == pytest.approx(1.0)


def test_ccf_short_series_returns_nan():
    result = get_method("ccf", max_lag=5).compute(np.arange(5, dtype=float), np.arange(5, dtype=float))
    assert np.isnan(result.coefficient)
    assert result.lag == 0
