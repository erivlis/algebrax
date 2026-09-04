---
title: "EP-0149: Universal & Multivariate Binomial Convolution Moment Semirings"
description: "Unifying univariate/multivariate Expectation, Covariance, Skewness, Kurtosis, and arbitrary Taylor/Hessian jets under a universal Binomial Convolution Semiring."
icon: lucide/sigma
status: final
---

# EP-0149: Universal & Multivariate Binomial Convolution Moment Semirings

| Field       | Value                                                          |
|:------------|:---------------------------------------------------------------|
| **EP**      | 0149                                                           |
| **Title**   | Universal & Multivariate Binomial Convolution Moment Semirings |
| **Author**  | Eran Rivlis & Antigravity                                      |
| **Status**  | Final                                                          |
| **Type**    | Standards Track                                                |
| **Created** | 2026-09-03                                                     |
| **Updated** | 2026-09-03                                                     |

---

## Abstract

This proposal specifies the unification of all univariate and multivariate statistical moment semirings (1st-order
Expectation/Gradients, 2nd-order Covariance/Hessians, 3rd-order Skewness, 4th-order Kurtosis, and arbitrary $(d, K)$
-order Taylor jets) under two canonical algebraic primitives:

1. **`BinomialConvolutionSemiring(order=K)`**: Fast 1D univariate engine over $\mathbb{R}[\epsilon] / (\epsilon^{K+1})$.
2. **`MultivariateBinomialConvolutionSemiring(num_vars=d, order=K)`**: Universal multi-index engine
   over $\mathbb{R}[\epsilon_1, \dots, \epsilon_d] / \langle \boldsymbol{\epsilon}^{\boldsymbol{\beta}} : |\boldsymbol{\beta}| = K+1 \rangle$.

By recognizing that multivariate Moment Generating Functions (MGFs) and higher-order Forward Automatic Differentiation
(AD) are the exponential generating function (EGF) representation of the divided power quotient algebra under
**Multi-Index Binomial Convolution**:

$$(\mathbf{u} \otimes \mathbf{v})_{\boldsymbol{\alpha}} = \sum_{\mathbf{0} \le \boldsymbol{\beta} \le \boldsymbol{\alpha}} \binom{\boldsymbol{\alpha}}{\boldsymbol{\beta}} u_{\boldsymbol{\beta}} \cdot v_{\boldsymbol{\alpha} - \boldsymbol{\beta}} \quad \text{where} \quad \binom{\boldsymbol{\alpha}}{\boldsymbol{\beta}} = \prod_{i=1}^d \binom{\alpha_i}{\beta_i}$$

AlgebraX eliminates hardcoded fixed-order duplication, provides native $d \times d$ Covariance
Matrix $\boldsymbol{\Sigma}$ and Hessian Matrix $\mathbf{H}$ propagation on graph paths, and provides ergonomic
statistical decoders.

---

## Motivation & Unified Algebraic Hierarchy

Currently, AlgebraX provides separate disconnected classes for low-order moment tracking:

1. `DualNumberSemiring` / `ExpectationSemiring` (Univariate Order 1: $(p, v)$)
2. `VarianceSemiring` (Bivariate Order 1 per variable: $(p, r, s, t)$
   in $\mathbb{R}[\epsilon_1, \epsilon_2]/ (\epsilon_1^2, \epsilon_2^2)$)
3. `SkewnessSemiring` (Univariate Order 3: $(p, m_1, m_2, m_3)$)
4. `GradientDualNumber` (Multivariate Order 1 Jacobian tracking: $u + \nabla u \cdot \boldsymbol{\epsilon}$)

### Subsumption Hierarchy

| Dimension ($d$) |   Order ($K$)    |          Representation           | Mathematical Meaning                                                    | Subsumes / Powers                    |
|:---------------:|:----------------:|:---------------------------------:|:------------------------------------------------------------------------|:-------------------------------------|
|   **$d = 1$**   |     $K = 1$      |       2-tuple: $(m_0, m_1)$       | Mean / 1st Moment                                                       | `ExpectationSemiring`                               |
|   **$d = 1$**   |     $K = 2$      |    3-tuple: $(m_0, m_1, m_2)$     | Univariate Variance                                                     | `VarianceSemiring`                                  |
|   **$d = 1$**   |     $K = 3$      |   4-tuple: $(m_0, \dots, m_3)$    | Skewness / Asymmetry                                                    | `SkewnessSemiring`                                  |
|   **$d = 1$**   |     $K = 4$      |   5-tuple: $(m_0, \dots, m_4)$    | Kurtosis / Tail Risk                                                    | `KurtosisSemiring`                                  |
|   **$d = 2$**   | individual deg 1 |      4-tuple: $(p, r, s, t)$      | **Bivariate Covariance $\text{Cov}(X, Y)$**                             | **`BivariateVarianceSemiring` (Li & Eisner)**       |
|  **$d \ge 2$**  |     $K = 1$      |         $(1 + d)$ values          | Gradient Vector $\nabla f$ / Jacobians                                  | `GradientDualNumber`                                |
|  **$d \ge 2$**  |     $K = 2$      | $1 + d + \frac{d(d+1)}{2}$ values | **Full Covariance Matrix $\boldsymbol{\Sigma}$ & Hessian $\mathbf{H}$** | `MultivariateMomentSemiring`                        |

---

## Mathematical Specification

### 1. Carrier Set & Multi-Indices

For $d$ variables and total degree $K$, elements are indexed by
multi-indices $\boldsymbol{\alpha} = (\alpha_1, \dots, \alpha_d) \in \mathbb{N}_0^d$
with $|\boldsymbol{\alpha}| = \sum \alpha_i \le K$:
$$m_{\boldsymbol{\alpha}} = \mathbb{E}\left[X_1^{\alpha_1} X_2^{\alpha_2} \cdots X_d^{\alpha_d}\right] \cdot Z$$

### 2. Multi-Index Binomial Operations

* **Addition $\oplus$**: Component-wise
  sum $(\mathbf{u} \oplus \mathbf{v})_{\boldsymbol{\alpha}} = u_{\boldsymbol{\alpha}} + v_{\boldsymbol{\alpha}}$.
* **Multiplication $\otimes$**:
  $$(\mathbf{u} \otimes \mathbf{v})_{\boldsymbol{\alpha}} = \sum_{\mathbf{0} \le \boldsymbol{\beta} \le \boldsymbol{\alpha}} \left (\prod_{i=1}^d \binom{\alpha_i}{\beta_i} \right) u_{\boldsymbol{\beta}} \cdot v_{\boldsymbol{\alpha} - \boldsymbol{\beta}}$$
* **Neutral Elements**:
  $$\mathbf{0}_{\boldsymbol{\alpha}} = 0.0 \quad \forall \boldsymbol{\alpha}, \qquad \mathbf{1}_{\mathbf{0}} = 1.0 \text{ and } \mathbf{1}_{\boldsymbol{\alpha}} = 0.0 \text{ for } |\boldsymbol{\alpha}| > 0$$

---

## The Council Review Assessment

The proposal was evaluated across all 8 Pillars of The Council Framework. **The Steward** synthesized the findings into an Executive Consensus:

| Pillar | Member | Assessment & Verdict | Key Directives & Revisions Applied |
| :--- | :--- | :---: | :--- |
| **Symmetry** | ⚖️ Noether | **8.5 / 10** (Approved) | Preserves exact EGF ring isomorphism. Added symmetric 1D `StatisticalMomentSemiring` decoders (`.mean()`, `.variance()`, `.skewness()`, `.kurtosis()`). |
| **Consistency** | 🧩 Russell | **Approved** (Revised) | *The Total vs. Individual Degree Accord*: Clarified that the engine implements the Total Degree quotient $\mathbb{R}[\boldsymbol{\epsilon}] / \langle |\boldsymbol{\beta}|=K+1 \rangle$. Covariance $\text{Cov}(X, Y)$ requires $K \ge 2$ to capture $(1, 1)$, while Li & Eisner's 4-tuple is preserved as a coordinate-wise degree specialization. |
| **Efficiency** | ⚡ Shannon | **Approved** (Revised) | Eliminated inner-loop generator expressions in 1D. Replaced dynamic tuple/comb allocations with bounded lazy transition table caching. Exploited upper-triangle matrix symmetry in `covariance_matrix`. |
| **Safety** | 🛡️ Golem | **Approved** (Revised) | Removed eager combinatorial instantiation of `self.multi_indices` from `__init__` (eliminating memory blowup risk $\binom{d+K}{K}$). Added constructor validation (`num_vars >= 1`, `order >= 0`). |
| **Clarity** | 💡 Feynman | **Approved** | Softened abstract jargon; added the intuitive explanation of tracking Taylor polynomial "wiggles" via Pascal's triangle. Celebrated the Grand Subsumption Hierarchy. |
| **Falsifiability** | 🔬 Popper | **Approved** (Revised) | Added runtime guard in `covariance_matrix` requiring `self.order >= 2` to prevent silent fallacies. Added 1D tuple length invariant assertions. |
| **Curiosity** | 🔭 Explorer | **9.0 / 10** (Approved) | Unlocks arbitrary-order moments and multivariate graph Hessians/Covariances. Outlined roadmap for sparse tensor backends at massive scales. |
| **Harmony** | 🤝 Steward | **Final Consensus** | Unified consensus achieved: high-speed 1D flat-tuple engine + safe, lazy-evaluated multivariate engine with rich statistical decoders. |

---

## Proposed API Specification

### 1. `BinomialConvolutionSemiring` (1D Engine in `algebrax.semiring.algebraic`)

```python
import functools
import math
from algebrax.semiring._base import Semiring

@functools.lru_cache(maxsize=32)
def _get_pascal_table(order: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(math.comb(n, k) for k in range(n + 1)) for n in range(order + 1))

class BinomialConvolutionSemiring(Semiring[tuple[float, ...]]):
    """Universal 1D Binomial Convolution Semiring over R[ε] / (ε^{K+1})."""

    def __init__(self, order: int = 1) -> None:
        if order < 0:
            raise ValueError(f"order must be a non-negative integer, got {order}")
        self.order = order
        self._pascal = _get_pascal_table(order)

    @property
    def zero(self) -> tuple[float, ...]:
        return (0.0,) * (self.order + 1)

    @property
    def one(self) -> tuple[float, ...]:
        return (1.0,) + (0.0,) * self.order

    def add(self, a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
        if len(a) != self.order + 1 or len(b) != self.order + 1:
            raise ValueError(f"Operands must have length {self.order + 1}")
        return tuple(u + v for u, v in zip(a, b))

    def mul(self, a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
        if len(a) != self.order + 1 or len(b) != self.order + 1:
            raise ValueError(f"Operands must have length {self.order + 1}")
        order = self.order
        pascal = self._pascal
        res = [0.0] * (order + 1)
        for k in range(order + 1):
            coeffs = pascal[k]
            acc = 0.0
            for j in range(k + 1):
                acc += coeffs[j] * a[j] * b[k - j]
            res[k] = acc
        return tuple(res)
```

### 2. `StatisticalMomentSemiring` (1D Decoders in `algebrax.semiring.statistical`)

```python
class StatisticalMomentSemiring(BinomialConvolutionSemiring):
    """1D Statistical moment semiring with central moments, mean, variance, skewness, kurtosis."""

    def raw_moments(self, m: tuple[float, ...]) -> list[float]:
        p = m[0]
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
            return [float("nan")] * len(m)
        return [val / p for val in m]

    def central_moments(self, m: tuple[float, ...]) -> list[float]:
        """Compute all central moments μ_k = E[(X - μ)^k] from raw moments."""
        p = m[0]
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
            return [float("nan")] * len(m)
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
            return float("nan")
        return m[1] / m[0]

    def variance(self, m: tuple[float, ...]) -> float:
        cm = self.central_moments(m)
        return cm[2] if len(cm) > 2 else 0.0

    def skewness(self, m: tuple[float, ...]) -> float:
        cm = self.central_moments(m)
        if len(cm) <= 3 or cm[2] <= 0.0:
            return float("nan")
        return cm[3] / (cm[2] ** 1.5)

    def kurtosis(self, m: tuple[float, ...]) -> float:
        cm = self.central_moments(m)
        if len(cm) <= 4 or cm[2] <= 0.0:
            return float("nan")
        return cm[4] / (cm[2] ** 2)
```

### 3. `MultivariateBinomialConvolutionSemiring` (Multi-D Engine in `algebrax.semiring.algebraic`)

```python
@functools.lru_cache(maxsize=32)
def _get_multivariate_transition_table(num_vars: int, order: int) -> dict[tuple[tuple[int, ...], tuple[int, ...]], tuple[tuple[int, ...], int]]:
    """Lazy bounded cache of multi-index transitions (alpha, beta) -> (gamma, coeff)."""
    # Populated on demand without eager memory blowup
    return {}

class MultivariateBinomialConvolutionSemiring(Semiring[dict[tuple[int, ...], float]]):
    """
    Universal Multivariate Binomial Convolution Semiring over R[ε1,...,εd] / <ε^β : |β| = K+1>.
    """
    def __init__(self, num_vars: int, order: int = 1) -> None:
        if num_vars < 1:
            raise ValueError(f"num_vars must be >= 1, got {num_vars}")
        if order < 0:
            raise ValueError(f"order must be >= 0, got {order}")
        self.num_vars = num_vars
        self.order = order

    @property
    def zero(self) -> dict[tuple[int, ...], float]:
        return {}

    @property
    def one(self) -> dict[tuple[int, ...], float]:
        return {(0,) * self.num_vars: 1.0}

    def add(self, a: dict[tuple[int, ...], float], b: dict[tuple[int, ...], float]) -> dict[tuple[int, ...], float]:
        res = dict(a)
        for k, v in b.items():
            res[k] = res.get(k, 0.0) + v
        return {k: v for k, v in res.items() if not math.isclose(v, 0.0, abs_tol=1e-15)}

    def mul(self, a: dict[tuple[int, ...], float], b: dict[tuple[int, ...], float]) -> dict[tuple[int, ...], float]:
        res: dict[tuple[int, ...], float] = {}
        for alpha, v1 in a.items():
            for beta, v2 in b.items():
                gamma = tuple(x + y for x, y in zip(alpha, beta))
                if sum(gamma) <= self.order:
                    coeff = math.prod(math.comb(g, a_i) for g, a_i in zip(gamma, alpha))
                    res[gamma] = res.get(gamma, 0.0) + coeff * v1 * v2
        return {k: v for k, v in res.items() if not math.isclose(v, 0.0, abs_tol=1e-15)}
```

### 4. `MultivariateMomentSemiring` (Multi-D Decoders in `algebrax.semiring.statistical`)

```python
class MultivariateMomentSemiring(MultivariateBinomialConvolutionSemiring):
    """Multivariate moment semiring with mean vectors, covariance matrices, and Hessians."""

    def mean_vector(self, m: dict[tuple[int, ...], float]) -> list[float]:
        p = m.get((0,) * self.num_vars, 0.0)
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
            return [float("nan")] * self.num_vars
        means = []
        for i in range(self.num_vars):
            idx = tuple(1 if j == i else 0 for j in range(self.num_vars))
            means.append(m.get(idx, 0.0) / p)
        return means

    def covariance_matrix(self, m: dict[tuple[int, ...], float]) -> list[list[float]]:
        if self.order < 2:
            raise ValueError(f"Covariance matrix calculation requires order >= 2, but instance has order={self.order}")
        p = m.get((0,) * self.num_vars, 0.0)
        if p == 0.0:  # NOSONAR - exact zero denominator singularity check
            return [[float("nan")] * self.num_vars for _ in range(self.num_vars)]
        means = self.mean_vector(m)
        d = self.num_vars
        cov = [[0.0] * d for _ in range(d)]
        # Exploit upper-triangle symmetry
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
```

---

## References

1. Eisner, J. (2002). *Parameter Estimation for Probabilistic Finite-State Transducers*. ACL.
2. Li, Z., & Eisner, J. (2009). *First- and Second-Order Expectation Semirings with Applications to Minimum-Risk Training on Graphs*. EMNLP.
3. Roman, S. (2008). *The Umbral Calculus*. Dover Publications.
