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
    r"""The Log-Sum-Exp semiring over the extended real numbers.

    Algebraic Signature:
        $\langle \mathbb{R} \cup \{-\infty\}, \oplus_{\log}, +, -\infty, 0.0 \rangle$

    Carrier:
        `float` (Real numbers extended with $-\infty$, representing log-probabilities $\ln(p)$).

    Operations:
        - Addition ($\oplus_{\log}$): Log-sum-exp, $\ln(e^a + e^b) = \max(a, b) + \ln(1 + e^{-|a - b|})$.
        - Multiplication ($\otimes$): Standard addition, $a + b$ (representing $e^a \cdot e^b = e^{a+b}$).
        - Zero Element ($\mathbb{0}$): $-\infty$ (`float('-inf')`).
        - One Element ($\mathbb{1}$): $0.0$.

    Properties:
        Commutative, associative, distributed, idempotent under zero.

    Applications:
        Numerically stable probabilistic inference, Hidden Markov Models, Forward-Backward algorithm.
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
    r"""The First-Order Expectation Semiring (Eisner, 2002).

    Algebraic Signature:
        $\langle \mathbb{R}_{\ge 0} \times \mathbb{R}, \oplus, \otimes, (0.0, 0.0), (1.0, 0.0) \rangle$

    Carrier:
        `tuple[float, float]` (Pair $(p, v)$ where $p$ is probability mass and $v = p \cdot w$).

    Operations:
        - Addition ($\oplus$): Componentwise addition $(p_1 + p_2, v_1 + v_2)$.
        - Multiplication ($\otimes$): Semiring convolution $(p_1 p_2, p_1 v_2 + p_2 v_1)$ isomorphic to dual numbers.
        - Zero Element ($\mathbb{0}$): $(0.0, 0.0)$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0)$.

    Properties:
        Commutative, associative, isomorphic to $\mathbb{R}[\varepsilon]/(\varepsilon^2)$.

    Applications:
        Expectation tracking in weighted automata, speech recognition, NLP parsers.
    """


class BivariateVarianceSemiring(Semiring[tuple[float, float, float, float]]):
    r"""The Bivariate Second-Order Expectation and Covariance Semiring (Li & Eisner, 2009).

    Algebraic Signature:
        $\langle \mathbb{R}^4_{\mathrm{cov}}, \oplus, \otimes, \mathbf{0}, \mathbf{1} \rangle$

    Carrier:
        `tuple[float, float, float, float]` (4-tuple $(p, r, s, t)$ representing $p$, moments $r, s$, and $t$).

    Operations:
        - Addition ($\oplus$): Componentwise addition $(p_1+p_2, r_1+r_2, s_1+s_2, t_1+t_2)$.
        - Multiplication ($\otimes$): Cross-product convolution in $\mathbb{R}[\varepsilon_1, \varepsilon_2]/I$.
        - Zero Element ($\mathbb{0}$): $(0.0, 0.0, 0.0, 0.0)$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0, 0.0, 0.0)$.

    Properties:
        Commutative, associative, ring quotient isomorphic to $\mathbb{R}[\varepsilon_1, \varepsilon_2]/I$.

    Applications:
        Bivariate covariances, Hessians, joint second central moments of two random variables.
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
    r"""Univariate arbitrary-order statistical moment semiring.

    Algebraic Signature:
        $\langle \mathbb{R}^{K+1}, \oplus, \otimes_{\mathrm{binom}}, \mathbf{0}, \mathbf{e}_0 \rangle$

    Carrier:
        `tuple[float, ...]` ($(K+1)$-tuple of raw unnormalized moments $(m_0, m_1, \dots, m_K)$).

    Operations:
        - Addition ($\oplus$): Elementwise vector addition $(m + m')_k = m_k + m'_k$.
        - Multiplication ($\otimes$): Binomial convolution $(m \otimes m')_k = \sum_{j=0}^k \binom{k}{j} m_j m'_{k-j}$.
        - Zero Element ($\mathbb{0}$): $(0.0, \dots, 0.0)$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0, \dots, 0.0)$.

    Properties:
        Commutative, associative, ring quotient isomorphic to $\mathbb{R}[\varepsilon]/(\varepsilon^{K+1})$.

    Applications:
        Statistical moments, mean, variance, skewness, kurtosis, and forward-mode autodiff.
    """

    def raw_moments(self, m: tuple[float, ...]) -> list[float]:
        p = m[0]
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
            return [float('nan')] * len(m)
        return [val / p for val in m]

    def central_moments(self, m: tuple[float, ...]) -> list[float]:
        """Compute all central moments μ_k = E[(X - μ)^k] from raw moments."""
        p = m[0]
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
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
        if m[0] == 0.0:  # NOSONAR - exact zero denominator singularity check
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
    r"""Univariate second-order moment and variance semiring.

    Algebraic Signature:
        $\langle \mathbb{R}^3_{\mathrm{var}}, \oplus, \otimes_{\mathrm{binom}}, \mathbf{0}, \mathbf{e}_0 \rangle$

    Carrier:
        `tuple[float, float, float]` (3-tuple $(p, m_1, m_2)$ of total probability, first, and second raw moments).

    Operations:
        - Addition ($\oplus$): Elementwise addition $(p_1+p_2, m_{1,1}+m_{1,2}, m_{2,1}+m_{2,2})$.
        - Multiplication ($\otimes$): Binomial convolution over order 2.
        - Zero Element ($\mathbb{0}$): $(0.0, 0.0, 0.0)$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0, 0.0)$.

    Properties:
        Commutative, associative, ring quotient isomorphic to $\mathbb{R}[\varepsilon]/(\varepsilon^3)$.

    Applications:
        Path variance tracking, risk-sensitive routing, portfolio variance in DAGs.
    """

    def __init__(self) -> None:
        super().__init__(order=2)


class SkewnessSemiring(StatisticalMomentSemiring):
    r"""Univariate third-order moment and skewness semiring.

    Algebraic Signature:
        $\langle \mathbb{R}^4_{\mathrm{skew}}, \oplus, \otimes_{\mathrm{binom}}, \mathbf{0}, \mathbf{e}_0 \rangle$

    Carrier:
        `tuple[float, float, float, float]` (4-tuple $(p, m_1, m_2, m_3)$ of probability and moments up to order 3).

    Operations:
        - Addition ($\oplus$): Elementwise addition.
        - Multiplication ($\otimes$): Binomial convolution over order 3.
        - Zero Element ($\mathbb{0}$): $(0.0, 0.0, 0.0, 0.0)$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0, 0.0, 0.0)$.

    Properties:
        Commutative, associative, ring quotient isomorphic to $\mathbb{R}[\varepsilon]/(\varepsilon^4)$.

    Applications:
        Asymmetry analysis, third central moment tracking, tail-risk assessment in networks.
    """

    def __init__(self) -> None:
        super().__init__(order=3)


class KurtosisSemiring(StatisticalMomentSemiring):
    r"""Univariate fourth-order moment and kurtosis semiring.

    Algebraic Signature:
        $\langle \mathbb{R}^5_{\mathrm{kurt}}, \oplus, \otimes_{\mathrm{binom}}, \mathbf{0}, \mathbf{e}_0 \rangle$

    Carrier:
        `tuple[float, float, float, float, float]` (5-tuple $(p, m_1, m_2, m_3, m_4)$ of moments up to order 4).

    Operations:
        - Addition ($\oplus$): Elementwise addition.
        - Multiplication ($\otimes$): Binomial convolution over order 4.
        - Zero Element ($\mathbb{0}$): $(0.0, 0.0, 0.0, 0.0, 0.0)$.
        - One Element ($\mathbb{1}$): $(1.0, 0.0, 0.0, 0.0, 0.0)$.

    Properties:
        Commutative, associative, ring quotient isomorphic to $\mathbb{R}[\varepsilon]/(\varepsilon^5)$.

    Applications:
        Heavy-tail risk, fourth central moment tracking, kurtosis profiling in stochastic models.
    """

    def __init__(self) -> None:
        super().__init__(order=4)


class MultivariateMomentSemiring(MultivariateBinomialConvolutionSemiring):
    r"""Multivariate moment semiring for mean vectors, covariance matrices, and Hessians.

    Algebraic Signature:
        $\langle \mathbb{R}^M, \oplus, \otimes_{\mathrm{multinom}}, \mathbf{0}, \mathbf{e}_0 \rangle$

    Carrier:
        `dict[tuple[int, ...], float]` (Sparse map from multi-index $\boldsymbol{\alpha}$ to $m_{\boldsymbol{\alpha}}$).

    Operations:
        - Addition ($\oplus$): Elementwise dictionary coefficient addition.
        - Multiplication ($\otimes$): Multinomial convolution over bounded total degree.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{(0, ..., 0): 1.0}`.

    Properties:
        Commutative, associative, ring quotient isomorphic to $\mathbb{R}[\boldsymbol{\varepsilon}]/I$.

    Applications:
        Multivariate mean vectors, joint covariance matrices, multidimensional risk routing.
    """

    def mean_vector(self, m: dict[tuple[int, ...], float]) -> list[float]:
        p = m.get((0,) * self.num_vars, 0.0)
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
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
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
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
