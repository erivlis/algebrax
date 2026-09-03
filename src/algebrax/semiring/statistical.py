"""
Probability, expectation, and moment semirings.
"""

import math

from algebrax.semiring._base import Semiring
from algebrax.semiring.algebraic import (
    BinomialConvolutionSemiring,
    DualNumberSemiring,
    MultivariateBinomialConvolutionSemiring,
)


class LogSemiring(Semiring[float]):
    """
    The Log-Sum-Exp algebra.
    (R U {-inf}, logaddexp, +, -inf, 0)
    Used for: Probabilistic inference in log-domain (avoids underflow).
    Values represent log-probabilities.
    """

    @property
    def zero(self) -> float:
        return float('-inf')

    @property
    def one(self) -> float:
        return 0.0

    def add(self, a: float, b: float) -> float:
        # log(exp(a) + exp(b))
        if a == float('-inf'):
            return b
        if b == float('-inf'):
            return a

        # Numerical stability: log(exp(a) + exp(b)) = max + log(exp(a-max) + exp(b-max))
        max_val = max(a, b)
        return max_val + math.log(math.exp(a - max_val) + math.exp(b - max_val))

    def mul(self, a: float, b: float) -> float:
        # log(exp(a) * exp(b)) = a + b
        return a + b

    def nsum(self, a: float, n: int) -> float:
        if n < 0:
            raise ValueError('LogSemiring does not support negative nsum')
        # log(n * exp(a)) = log(n) + a
        if n == 0:
            return float('-inf')
        if a == float('-inf'):
            return float('-inf')
        return a + math.log(n)

    def power(self, a: float, n: int) -> float:
        return a * n

    def star(self, a: float) -> float:
        if a >= 0.0:
            return float('inf')
        return -math.log1p(-math.exp(a))


class ExpectationSemiring(DualNumberSemiring):
    """
    The First-Order Expectation Semiring (Eisner, 2002).
    Domain alias for DualNumberSemiring used in probabilistic modeling,
    weighted finite-state transducers, and Hidden Markov Models.

    Values are pairs (p, v) where:
    - p: Path probability (total probability mass Z)
    - v: Feature reward / expectation contribution (v = p * w)
    """


class BivariateVarianceSemiring(Semiring[tuple[float, float, float, float]]):
    """
    The Bivariate Second-Order Expectation / Covariance Semiring (Li & Eisner, 2009).
    Values are 4-tuples (p, r, s, t) corresponding to R[ε1, ε2] / (ε1^2, ε2^2).
    Used for: Computing Bivariate Covariances, Hessians, and joint second central moments of 2 variables.

    - p: Total probability (Z)
    - r: First moment along feature X (E[X] * Z)
    - s: First moment along feature Y (E[Y] * Z)
    - t: Second raw cross-moment (E[XY] * Z)

    Cov(X, Y) = (t/p) - (r/p)*(s/p).
    """

    @property
    def zero(self) -> tuple[float, float, float, float]:
        return 0.0, 0.0, 0.0, 0.0

    @property
    def one(self) -> tuple[float, float, float, float]:
        return 1.0, 0.0, 0.0, 0.0

    def add(
        self, a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        return a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3]

    def mul(
        self, a: tuple[float, float, float, float], b: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        p1, r1, s1, t1 = a
        p2, r2, s2, t2 = b

        # p = p1 * p2
        p = p1 * p2

        # r = p1*r2 + p2*r1
        r = p1 * r2 + p2 * r1

        # s = p1*s2 + p2*s1
        s = p1 * s2 + p2 * s1

        # t = p1*t2 + p2*t1 + r1*s2 + r2*s1
        t = p1 * t2 + p2 * t1 + r1 * s2 + r2 * s1

        return p, r, s, t

    def nsum(self, a: tuple[float, float, float, float], n: int) -> tuple[float, float, float, float]:
        if n == 0:
            return 0.0, 0.0, 0.0, 0.0
        return a[0] * n, a[1] * n, a[2] * n, a[3] * n

    def power(self, a: tuple[float, float, float, float], n: int) -> tuple[float, float, float, float]:
        if n == 0:
            return 1.0, 0.0, 0.0, 0.0
        res = (1.0, 0.0, 0.0, 0.0)
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        raise NotImplementedError('Kleene star not implemented for BivariateVarianceSemiring')


BivariateCovarianceSemiring = BivariateVarianceSemiring


class StatisticalMomentSemiring(BinomialConvolutionSemiring):
    """
    1D Statistical moment semiring with central moments, mean, variance, skewness, kurtosis.
    Subclasses BinomialConvolutionSemiring to provide statistical metric decoders.
    """

    def raw_moments(self, m: tuple[float, ...]) -> list[float]:
        p = m[0]
        if p == 0.0:
            return [float('nan')] * len(m)
        return [val / p for val in m]

    def central_moments(self, m: tuple[float, ...]) -> list[float]:
        """Compute all central moments μ_k = E[(X - μ)^k] from raw moments."""
        p = m[0]
        if p == 0.0:
            return [float('nan')] * len(m)
        raw = [val / p for val in m]
        mu = raw[1] if len(raw) > 1 else 0.0
        pascal = self._pascal

        central = [1.0]  # μ_0 = 1
        for k in range(1, len(raw)):
            val = sum(pascal[k][j] * ((-mu) ** (k - j)) * raw[j] for j in range(k + 1))
            central.append(val)
        return central

    def mean(self, m: tuple[float, ...]) -> float:
        if m[0] == 0.0:
            return float('nan')
        return m[1] / m[0]

    def variance(self, m: tuple[float, ...]) -> float:
        cm = self.central_moments(m)
        return cm[2] if len(cm) > 2 else 0.0

    def skewness(self, m: tuple[float, ...]) -> float:
        cm = self.central_moments(m)
        if len(cm) <= 3 or cm[2] <= 0.0:
            return float('nan')
        return cm[3] / (cm[2] ** 1.5)

    def kurtosis(self, m: tuple[float, ...]) -> float:
        cm = self.central_moments(m)
        if len(cm) <= 4 or cm[2] <= 0.0:
            return float('nan')
        return cm[4] / (cm[2] ** 2)


class VarianceSemiring(StatisticalMomentSemiring):
    """
    Univariate 2nd-order moment and variance semiring over R[ε]/(ε^3).
    Values are 3-tuples (p, m1, m2) representing:
    - p: Total probability mass (Z = sum p_i)
    - m1: First raw moment (sum p_i x_i = E[X] * Z)
    - m2: Second raw moment (sum p_i x_i^2 = E[X^2] * Z)

    Statistical metrics:
    - Mean: mu = m1 / p
    - Variance: var = (m2 / p) - mu^2
    """

    def __init__(self) -> None:
        super().__init__(order=2)


class SkewnessSemiring(StatisticalMomentSemiring):
    """
    Univariate 3rd-order moment and skewness semiring over R[ε]/(ε^4).
    Values are 4-tuples (p, m1, m2, m3) representing:
    - p: Total probability mass (Z = sum p_i)
    - m1: First raw moment (sum p_i x_i = E[X] * Z)
    - m2: Second raw moment (sum p_i x_i^2 = E[X^2] * Z)
    - m3: Third raw moment (sum p_i x_i^3 = E[X^3] * Z)

    Statistical metrics:
    - Mean: mu = m1 / p
    - Variance: var = (m2 / p) - mu^2
    - Third Central Moment: mu3 = (m3 / p) - 3*mu*(m2 / p) + 2*mu^3
    - Skewness: gamma1 = mu3 / (var^1.5)
    """

    def __init__(self) -> None:
        super().__init__(order=3)


class KurtosisSemiring(StatisticalMomentSemiring):
    """Univariate 4th-order moment semiring (order=4). Carrier is 5-tuple (p, m1, m2, m3, m4)."""

    def __init__(self) -> None:
        super().__init__(order=4)


class MultivariateMomentSemiring(MultivariateBinomialConvolutionSemiring):
    """Multivariate moment semiring with mean vectors, covariance matrices, and Hessians."""

    def mean_vector(self, m: dict[tuple[int, ...], float]) -> list[float]:
        p = m.get((0,) * self.num_vars, 0.0)
        if p == 0.0:
            return [float('nan')] * self.num_vars
        means = []
        for i in range(self.num_vars):
            idx = tuple(1 if j == i else 0 for j in range(self.num_vars))
            means.append(m.get(idx, 0.0) / p)
        return means

    def covariance_matrix(self, m: dict[tuple[int, ...], float]) -> list[list[float]]:
        if self.order < 2:
            raise ValueError(f'Covariance matrix calculation requires order >= 2, but instance has order={self.order}')
        p = m.get((0,) * self.num_vars, 0.0)
        if p == 0.0:
            return [[float('nan')] * self.num_vars for _ in range(self.num_vars)]
        means = self.mean_vector(m)
        d = self.num_vars
        cov = [[0.0] * d for _ in range(d)]
        for i in range(d):
            for j in range(i, d):
                idx = [0] * d
                idx[i] += 1
                idx[j] += 1
                raw_ij = m.get(tuple(idx), 0.0) / p
                val = raw_ij - (means[i] * means[j])
                cov[i][j] = val
                cov[j][i] = val
        return cov
