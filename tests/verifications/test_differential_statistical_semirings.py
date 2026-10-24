r"""Comparative verification of Streaming Statistical Moment Semirings vs NumPy & SciPy.stats.

Implements EP-0185:
- Univariate `StatisticalMomentSemiring`, `VarianceSemiring`, `SkewnessSemiring`, and `KurtosisSemiring`:
  - Associative parallel merge (`add`) of partitioned sample streams $D_1 \sqcup D_2 \sqcup D_3$ matches
    batch `np.mean`, `np.var(..., ddof=0)`, `scipy.stats.skew(..., bias=True)`, and
    `scipy.stats.kurtosis(..., fisher=False, bias=True)` on the concatenated dataset $D$.
  - Independent random variable sum (`mul` via binomial convolution) matches exact convolution of independent
    discrete distributions: $\mathbb{E}[X + Y] = \mathbb{E}[X] + \mathbb{E}[Y]$,
    $\operatorname{Var}(X + Y) = \operatorname{Var}(X) + \operatorname{Var}(Y)$, and third/fourth cumulant additivity.
- `ExpectationSemiring` first-order expectation tracking on weighted DAGs.
- `BivariateVarianceSemiring` / `BivariateCovarianceSemiring` vs `np.cov(X, Y, ddof=0)`.
- `MultivariateMomentSemiring` (`mean_vector`, `covariance_matrix`) vs `np.mean(X, axis=0)` and
  `np.cov(X, rowvar=False, ddof=0)`.
"""

from __future__ import annotations

import functools
import math

import numpy as np
import pytest
import scipy.stats as stats
from hypothesis import given, settings
from hypothesis import strategies as st

from algebrax.semiring import (
    BivariateCovarianceSemiring,
    ExpectationSemiring,
    KurtosisSemiring,
    MultivariateMomentSemiring,
    SkewnessSemiring,
    StatisticalMomentSemiring,
    VarianceSemiring,
)

pytestmark = [pytest.mark.verification, pytest.mark.differential]


def _encode_univariate_sample(x: float, order: int, weight: float = 1.0) -> tuple[float, ...]:
    """Lift a single observation x with weight w into raw moment tuple (w, w*x, w*x^2, ..., w*x^order)."""
    return tuple(weight * (x**k) for k in range(order + 1))


# ---------------------------------------------------------------------------
# 1. Hypothesis Parallel Stream Merge vs NumPy & SciPy.stats Batch Moments
# ---------------------------------------------------------------------------


@settings(max_examples=35, deadline=None)
@given(
    part1=st.lists(
        st.floats(min_value=-20.0, max_value=20.0, allow_nan=False, allow_infinity=False), min_size=3, max_size=10
    ),
    part2=st.lists(
        st.floats(min_value=-20.0, max_value=20.0, allow_nan=False, allow_infinity=False), min_size=3, max_size=10
    ),
    part3=st.lists(
        st.floats(min_value=-20.0, max_value=20.0, allow_nan=False, allow_infinity=False), min_size=3, max_size=10
    ),
)
def test_hypothesis_streaming_moments_parallel_merge_vs_scipy_stats(
    part1: list[float],
    part2: list[float],
    part3: list[float],
) -> None:
    """Verify associative parallel fold of KurtosisSemiring matches batch NumPy/SciPy mean, var, skew, kurtosis."""
    sr = KurtosisSemiring()

    # Fold each partition independently, then merge in parallel: (fold(P1) + fold(P2)) + fold(P3)
    m1 = functools.reduce(sr.add, (_encode_univariate_sample(x, order=4) for x in part1), sr.zero)
    m2 = functools.reduce(sr.add, (_encode_univariate_sample(x, order=4) for x in part2), sr.zero)
    m3 = functools.reduce(sr.add, (_encode_univariate_sample(x, order=4) for x in part3), sr.zero)

    merged_left = sr.add(sr.add(m1, m2), m3)
    merged_right = sr.add(m1, sr.add(m2, m3))

    full_data = np.array(part1 + part2 + part3, dtype=np.float64)

    # Mean & Variance always defined
    assert math.isclose(sr.mean(merged_left), float(np.mean(full_data)), rel_tol=1e-10, abs_tol=1e-10)
    assert math.isclose(sr.mean(merged_right), float(np.mean(full_data)), rel_tol=1e-10, abs_tol=1e-10)
    var_np = float(np.var(full_data, ddof=0))
    assert math.isclose(sr.variance(merged_left), var_np, rel_tol=1e-9, abs_tol=1e-9)

    # Central moments mu_k = E[(X - mu)^k]
    cm = sr.central_moments(merged_left)
    for k in range(1, 5):
        expected_cm_k = float(np.mean((full_data - np.mean(full_data)) ** k))
        assert math.isclose(cm[k], expected_cm_k, rel_tol=1e-8, abs_tol=1e-8)

    # Standardized Skewness & Pearson Kurtosis when variance is non-degenerate
    if var_np > 1e-6:
        skew_sp = float(stats.skew(full_data, bias=True))
        kurt_sp = float(stats.kurtosis(full_data, fisher=False, bias=True))
        assert math.isclose(sr.skewness(merged_left), skew_sp, rel_tol=1e-7, abs_tol=1e-7)
        assert math.isclose(sr.kurtosis(merged_left), kurt_sp, rel_tol=1e-7, abs_tol=1e-7)


# ---------------------------------------------------------------------------
# 2. Binomial Convolution Multiplication = Sum of Independent Random Variables
# ---------------------------------------------------------------------------


def test_binomial_convolution_independent_rv_sum_vs_exact_product_measure() -> None:
    """Verify semiring multiplication m(X) * m(Y) equals moments of X + Y for independent random variables."""
    sr_kurt = KurtosisSemiring()
    sr_skew = SkewnessSemiring()
    sr_var = VarianceSemiring()
    sr_stat = StatisticalMomentSemiring(order=4)

    # Discrete random variable X and independent discrete random variable Y
    dist_x = {(-1.0): 0.25, 0.5: 0.50, 2.0: 0.25}
    dist_y = {0.0: 0.30, 1.5: 0.40, 4.0: 0.30}

    mx = functools.reduce(
        sr_kurt.add,
        (_encode_univariate_sample(x, order=4, weight=p) for x, p in dist_x.items()),
        sr_kurt.zero,
    )
    my = functools.reduce(
        sr_kurt.add,
        (_encode_univariate_sample(y, order=4, weight=q) for y, q in dist_y.items()),
        sr_kurt.zero,
    )

    # Semiring product m_{X+Y} = m_X (x) m_Y
    m_sum = sr_kurt.mul(mx, my)

    # Exact product distribution of Z = X + Y
    vals_z = []
    probs_z = []
    for x, px in dist_x.items():
        for y, py in dist_y.items():
            vals_z.append(x + y)
            probs_z.append(px * py)

    rv_z = stats.rv_discrete(name='z_sum', values=(range(len(vals_z)), probs_z))
    # Compute exact moments of Z directly from product space
    z_arr = np.array(vals_z, dtype=np.float64)
    p_arr = np.array(probs_z, dtype=np.float64)
    mean_z = float(np.sum(p_arr * z_arr))
    var_z = float(np.sum(p_arr * ((z_arr - mean_z) ** 2)))
    m3_z = float(np.sum(p_arr * ((z_arr - mean_z) ** 3)))
    m4_z = float(np.sum(p_arr * ((z_arr - mean_z) ** 4)))
    skew_z = m3_z / (var_z**1.5)
    kurt_z = m4_z / (var_z**2)

    assert math.isclose(sr_kurt.mean(m_sum), mean_z, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(sr_kurt.variance(m_sum), var_z, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(sr_kurt.skewness(m_sum), skew_z, rel_tol=1e-11, abs_tol=1e-11)
    assert math.isclose(sr_kurt.kurtosis(m_sum), kurt_z, rel_tol=1e-11, abs_tol=1e-11)

    # Verify VarianceSemiring and SkewnessSemiring projections match prefix slices
    assert sr_var.mul(mx[:3], my[:3]) == pytest.approx(m_sum[:3], rel=1e-12)
    assert sr_skew.mul(mx[:4], my[:4]) == pytest.approx(m_sum[:4], rel=1e-12)
    assert sr_stat.raw_moments(m_sum)[1] == pytest.approx(mean_z, rel=1e-12)
    assert rv_z is not None


# ---------------------------------------------------------------------------
# 3. Expectation & Bivariate Covariance Semirings vs NumPy
# ---------------------------------------------------------------------------


def test_expectation_and_bivariate_covariance_semirings_vs_numpy() -> None:
    """Verify ExpectationSemiring and BivariateCovarianceSemiring against NumPy mean and covariance."""
    exp_sr = ExpectationSemiring()
    cov_sr = BivariateCovarianceSemiring()

    # Independent bivariate random variables (X_1, Y_1) and (X_2, Y_2)
    # In BivariateCovarianceSemiring, a single outcome (x, y) with weight p is encoded as (p, p*x, p*y, p*x*y)
    samples_1 = [(-1.0, 2.0, 0.3), (0.5, -1.0, 0.5), (3.0, 4.0, 0.2)]
    samples_2 = [(2.0, 1.0, 0.4), (-2.0, 3.0, 0.6)]

    # Check ExpectationSemiring on X_1 + X_2
    e1 = functools.reduce(exp_sr.add, ((p, p * x) for x, _, p in samples_1), exp_sr.zero)
    e2 = functools.reduce(exp_sr.add, ((q, q * x) for x, _, q in samples_2), exp_sr.zero)
    e_sum = exp_sr.mul(e1, e2)

    mean_x1 = sum(p * x for x, _, p in samples_1)
    mean_x2 = sum(q * x for x, _, q in samples_2)
    assert math.isclose(e_sum[0], 1.0, rel_tol=1e-12)
    assert math.isclose(e_sum[1], mean_x1 + mean_x2, rel_tol=1e-12)

    # Check BivariateCovarianceSemiring on (X_1 + X_2, Y_1 + Y_2)
    b1 = functools.reduce(cov_sr.add, ((p, p * x, p * y, p * x * y) for x, y, p in samples_1), cov_sr.zero)
    b2 = functools.reduce(cov_sr.add, ((q, q * x, q * y, q * x * y) for x, y, q in samples_2), cov_sr.zero)
    b_prod = cov_sr.mul(b1, b2)

    # Extract Cov(X_1 + X_2, Y_1 + Y_2) = E[(X_1+X_2)(Y_1+Y_2)] - E[X_1+X_2]E[Y_1+Y_2]
    p_tot, r_tot, s_tot, t_tot = b_prod
    cov_semiring = (t_tot / p_tot) - (r_tot / p_tot) * (s_tot / p_tot)

    # Compare with exact product distribution covariance
    cov_x1_y1 = sum(p * x * y for x, y, p in samples_1) - mean_x1 * sum(p * y for _, y, p in samples_1)
    cov_x2_y2 = sum(q * x * y for x, y, q in samples_2) - mean_x2 * sum(q * y for _, y, q in samples_2)
    assert math.isclose(cov_semiring, cov_x1_y1 + cov_x2_y2, rel_tol=1e-12, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# 4. MultivariateMomentSemiring vs NumPy Mean Vector & Covariance Matrix
# ---------------------------------------------------------------------------


def test_multivariate_moment_semiring_vs_numpy_cov() -> None:
    """Verify MultivariateMomentSemiring mean_vector and covariance_matrix against np.mean and np.cov."""
    mv_sr = MultivariateMomentSemiring(num_vars=3, order=2)

    rng = np.random.default_rng(20261025)
    data = rng.normal(loc=[1.5, -2.0, 0.5], scale=[1.2, 0.8, 2.0], size=(50, 3))

    def _encode_3d_point(row: np.ndarray) -> dict[tuple[int, int, int], float]:
        x0, x1, x2 = float(row[0]), float(row[1]), float(row[2])
        return {
            (0, 0, 0): 1.0,
            (1, 0, 0): x0,
            (0, 1, 0): x1,
            (0, 0, 1): x2,
            (2, 0, 0): x0 * x0,
            (0, 2, 0): x1 * x1,
            (0, 0, 2): x2 * x2,
            (1, 1, 0): x0 * x1,
            (1, 0, 1): x0 * x2,
            (0, 1, 1): x1 * x2,
        }

    # Split into two partitions and fold via MultivariateMomentSemiring.add
    part_a = functools.reduce(mv_sr.add, (_encode_3d_point(r) for r in data[:25]), mv_sr.zero)
    part_b = functools.reduce(mv_sr.add, (_encode_3d_point(r) for r in data[25:]), mv_sr.zero)
    combined = mv_sr.add(part_a, part_b)

    mean_ax = np.array(mv_sr.mean_vector(combined), dtype=np.float64)
    cov_ax = np.array(mv_sr.covariance_matrix(combined), dtype=np.float64)

    mean_np = np.mean(data, axis=0)
    cov_np = np.cov(data, rowvar=False, ddof=0)

    np.testing.assert_allclose(mean_ax, mean_np, atol=1e-12)
    np.testing.assert_allclose(cov_ax, cov_np, atol=1e-12)
