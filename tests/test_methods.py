import numpy as np
import pytest

from analysis.methods import get_method
from config import AnalysisConfig

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
    result = get_method("ccf", AnalysisConfig(ccf_max_lag=5)).compute(x, y)
    assert result.lag == shift
    assert result.coefficient == pytest.approx(1.0, abs=1e-9)
    assert result.n == len(x) - shift


def test_ccf_zero_lag_matches_pearson():
    rng = np.random.default_rng(1)
    x = rng.normal(size=100)
    y = 2 * x + 1
    result = get_method("ccf", AnalysisConfig(ccf_max_lag=5)).compute(x, y)
    assert result.lag == 0
    assert result.coefficient == pytest.approx(1.0)


def test_ccf_short_series_returns_nan():
    result = get_method("ccf", AnalysisConfig(ccf_max_lag=5)).compute(np.arange(5, dtype=float), np.arange(5, dtype=float))
    assert np.isnan(result.coefficient)
    assert result.lag == 0


FAST = AnalysisConfig(surrogates=49, dcca_scale=10)


@pytest.mark.parametrize("name", ["mi", "rho_dcca", "mf_dcca"])
def test_surrogate_methods_on_independent_series(name):
    rng = np.random.default_rng(2)
    result = get_method(name, FAST).compute(rng.normal(size=400), rng.normal(size=400))
    assert abs(result.coefficient) < 0.15
    assert result.p_value > 0.05
    assert result.n == 400


@pytest.mark.parametrize("name", ["mi", "rho_dcca", "mf_dcca"])
def test_surrogate_methods_detect_linear_dependence(name):
    rng = np.random.default_rng(3)
    x = rng.normal(size=400)
    result = get_method(name, FAST).compute(x, x + 0.3 * rng.normal(size=400))
    assert result.coefficient > 0.8
    assert result.p_value < 0.05


@pytest.mark.parametrize("name", ["mi", "rho_dcca", "mf_dcca"])
def test_surrogate_methods_are_reproducible(name):
    rng = np.random.default_rng(4)
    x, y = rng.normal(size=300), rng.normal(size=300)
    method = get_method(name, FAST)
    assert method.compute(x, y) == method.compute(x, y)


def test_mi_captures_nonlinear_dependence_missed_by_pearson():
    rng = np.random.default_rng(5)
    x = rng.normal(size=500)
    y = x**2 + 0.1 * rng.normal(size=500)
    assert abs(get_method("pearson").compute(x, y).coefficient) < 0.15
    result = get_method("mi", FAST).compute(x, y)
    assert result.coefficient > 0.7
    assert result.p_value < 0.05


def test_mi_is_non_negative_for_anticorrelated_series():
    rng = np.random.default_rng(6)
    x = rng.normal(size=400)
    assert get_method("mi", FAST).compute(x, -x).coefficient > 0.9


@pytest.mark.parametrize("name", ["rho_dcca", "mf_dcca"])
def test_dcca_perfect_correlation(name):
    rng = np.random.default_rng(7)
    x = rng.normal(size=300)
    method = get_method(name, FAST)
    assert method.compute(x, 2 * x + 1).coefficient == pytest.approx(1.0)
    assert method.compute(x, -x).coefficient == pytest.approx(-1.0)


def test_mf_dcca_with_q2_matches_rho_dcca():
    rng = np.random.default_rng(8)
    x = rng.normal(size=300)
    y = 0.5 * x + rng.normal(size=300)
    cfg = FAST.model_copy(update={"mfdcca_q": 2.0})
    rho = get_method("rho_dcca", cfg).compute(x, y)
    mf = get_method("mf_dcca", cfg).compute(x, y)
    assert mf.coefficient == pytest.approx(rho.coefficient)


@pytest.mark.parametrize("q", [0.5, 1.0, 4.0, 8.0])
def test_mf_dcca_is_bounded(q):
    rng = np.random.default_rng(9)
    x = rng.standard_t(3, size=300)
    y = 0.6 * x + rng.standard_t(3, size=300)
    cfg = FAST.model_copy(update={"mfdcca_q": q})
    assert -1.0 <= get_method("mf_dcca", cfg).compute(x, y).coefficient <= 1.0


def test_mf_dcca_rejects_non_positive_q():
    with pytest.raises(ValueError):
        get_method("mf_dcca", AnalysisConfig(mfdcca_q=0.0))


@pytest.mark.parametrize("name", ["mi", "rho_dcca", "mf_dcca"])
def test_surrogate_methods_short_series_return_nan(name):
    x = np.arange(10, dtype=float)
    result = get_method(name, FAST).compute(x, x[::-1].copy())
    assert np.isnan(result.coefficient)
    assert np.isnan(result.p_value)
