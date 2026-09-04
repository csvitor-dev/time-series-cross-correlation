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
