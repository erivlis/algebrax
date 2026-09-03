---
title: Statistical & Moment Semirings
description: Theoretical foundations, moment-generating algebras, and computational pipelines for Log-Sum-Exp, Dual Numbers, Expectations, Universal Binomial Moments, and Multivariate Covariance Tensors in AlgebraX.
---

# Statistical & Moment Semirings

Statistical and probabilistic modeling on graphs, sequence models (HMMs, WFSTs), and computational graphs frequently requires tracking not just optimal paths, but entire probability distributions and their polynomial moments.

**AlgebraX** provides a unified family of statistical and moment semirings in `algebrax.semiring`:

1. **`LogSemiring`**: $(\mathbb{R} \cup \{-\infty\}, \text{LogSumExp}, +, -\infty, 0)$ for underflow-free partition function summation.
2. **`DualNumberSemiring`**: $\mathbb{R}[\epsilon]/(\epsilon^2)$ for 1st-order forward-mode automatic differentiation and expectations.
3. **`BinomialConvolutionSemiring(order=K)`**: Universal 1D divided power quotient algebra $\mathbb{R}[\epsilon]/(\epsilon^{K+1})$ for Taylor jets and polynomial moments up to arbitrary order $K$.
4. **`StatisticalMomentSemiring(order=K)`**: 1D moment semiring equipped with statistical decoders (`.mean()`, `.variance()`, `.skewness()`, `.kurtosis()`, `.central_moments()`).
5. **Standard 1D Specializations**:
   - `ExpectationSemiring` ($K=1$, carrier 2-tuple $(p, v)$)
   - `VarianceSemiring` ($K=2$, carrier 3-tuple $(p, m_1, m_2)$)
   - `SkewnessSemiring` ($K=3$, carrier 4-tuple $(p, m_1, m_2, m_3)$)
   - `KurtosisSemiring` ($K=4$, carrier 5-tuple $(p, m_1, m_2, m_3, m_4)$)
6. **`BivariateVarianceSemiring`** *(or `BivariateCovarianceSemiring`)*: Bivariate expectation semiring $\mathbb{R}[\epsilon_1, \epsilon_2]/(\epsilon_1^2, \epsilon_2^2)$ (carrier 4-tuple $(p, r, s, t)$) for 2-feature cross-covariance (Li & Eisner, 2009).
7. **`MultivariateMomentSemiring(num_vars=d, order=K)`**: Universal multi-index joint distribution engine for full $d \times d$ **Covariance Matrix $\boldsymbol{\Sigma}$** and **Hessian Matrix $\mathbf{H}$** path propagation.

---

## 1. LogSemiring: The Log-Sum-Exp Free Energy Algebra

In high-dimensional probabilistic graphs, calculating total partition mass $Z = \sum_{i} \prod_{j} p_{ij}$ in standard floating-point arithmetic leads to exponential underflow.

The **LogSemiring** maps real probabilities $p \in [0, 1]$ to log-domain potentials $a = \ln(p) \in \mathbb{R} \cup \{-\infty\}$:

$$\begin{aligned}
a \oplus b &= \ln\left(e^a + e^b\right) = \max(a, b) + \ln\left(1 + e^{-|a - b|}\right) \\
a \otimes b &= a + b \\
\mathbf{0} &= -\infty \quad (\ln 0) \\
\mathbf{1} &= 0.0 \quad (\ln 1)
\end{aligned}$$

### Kleene Star (Geometric Series of Probabilities)
For an edge with log-probability $a < 0$ ($p = e^a < 1$), cyclic feedback sums infinitely to:
$$a^* = \bigoplus_{k=0}^\infty a^{\otimes k} \implies \sum_{k=0}^\infty p^k = \frac{1}{1 - p} \implies \ln\left(\frac{1}{1 - e^a}\right) = -\ln(1 - e^a)$$

### Python Example
```python
import algebrax as ax
import math

semiring = ax.semiring.LogSemiring()

# Log-probabilities for two parallel paths: ln(0.3) and ln(0.5)
log_p1 = math.log(0.3)
log_p2 = math.log(0.5)

# Total probability: 0.3 + 0.5 = 0.8
log_total = semiring.add(log_p1, log_p2)
print("Total Probability:", math.exp(log_total))  # 0.8

# Cyclic feedback loop with prob 0.2: sum_{k=0}^inf 0.2^k = 1 / 0.8 = 1.25
star_val = semiring.star(math.log(0.2))
print("Geometric Series Mass:", math.exp(star_val))  # 1.25
```

---

## 2. Universal 1D Moment Engine: `StatisticalMomentSemiring`

In statistics, the **Moment Generating Function (MGF)** $M_X(\epsilon) = \mathbb{E}[e^{\epsilon X}] = \sum_{k=0}^K m_k \frac{\epsilon^k}{k!}$ is an exponential generating function. When independent random variables add ($X + Y$), their MGFs multiply under **Binomial Convolution**:

$$(\mathbf{u} \otimes \mathbf{v})_k = \sum_{j=0}^k \binom{k}{j} u_j \cdot v_{k-j}$$

[`StatisticalMomentSemiring(order=K)`](file:///C:/dev/erivlis/algebrax/src/algebrax/semiring/statistical.py) computes all raw moments up to order $K$ with precomputed, cached Pascal triangle binomial coefficients.

```python
import algebrax as ax

# Initialize 4th-order moment tracking (capturing Mean, Variance, Skewness, Kurtosis)
sem = ax.semiring.StatisticalMomentSemiring(order=4)

# Transition 1: 50% probability, step cost 2.0 -> (p, p*w, p*w^2, p*w^3, p*w^4)
path1 = (0.5, 0.5 * 2.0, 0.5 * 4.0, 0.5 * 8.0, 0.5 * 16.0)

# Transition 2: 50% probability, step cost 6.0
path2 = (0.5, 0.5 * 6.0, 0.5 * 36.0, 0.5 * 216.0, 0.5 * 1296.0)

# Parallel Union of Paths
bundle = sem.add(path1, path2)

print(f"Mean (μ): {sem.mean(bundle):.2f}")          # 4.00
print(f"Variance (σ²): {sem.variance(bundle):.2f}")  # 4.00
print(f"Skewness (γ1): {sem.skewness(bundle):.2f}")  # 0.00 (Symmetric distribution)
print(f"Kurtosis (β2): {sem.kurtosis(bundle):.2f}")  # 1.00
```

---

## 3. Standard Fixed-Order Moment Classes

AlgebraX provides convenient named subclasses for standard literature compatibility:

* **`ExpectationSemiring()`** ($K=1$): Carrier 2-tuple $(p, v)$ where $v = E[X] \cdot Z$.
* **`VarianceSemiring()`** ($K=2$): Carrier 3-tuple $(p, m_1, m_2)$ where $m_2 = E[X^2] \cdot Z$.
* **`SkewnessSemiring()`** ($K=3$): Carrier 4-tuple $(p, m_1, m_2, m_3)$.
* **`KurtosisSemiring()`** ($K=4$): Carrier 5-tuple $(p, m_1, m_2, m_3, m_4)$.

---

## 4. Bivariate Covariance Tracking: `BivariateVarianceSemiring`

To track cross-covariances between **two distinct features** $X$ and $Y$ (e.g. path latency and monetary cost), **Li & Eisner (2009)** defined the second-order dual semiring over $\mathbb{R}[\epsilon_1, \epsilon_2]/(\epsilon_1^2, \epsilon_2^2)$:

$$\mathbf{u} = (p, r, s, t) = \langle Z, \; \mathbb{E}[X]Z, \; \mathbb{E}[Y]Z, \; \mathbb{E}[XY]Z \rangle$$

$$\text{Cov}(X, Y) = \frac{t}{p} - \left(\frac{r}{p}\right)\left(\frac{s}{p}\right)$$

```python
import algebrax as ax

bivar_sem = ax.semiring.BivariateVarianceSemiring()

# Edge (p=1, X=2, Y=3, XY=6)
e1 = (1.0, 2.0, 3.0, 6.0)
# Edge (p=1, X=1, Y=4, XY=4)
e2 = (1.0, 1.0, 4.0, 4.0)

# Sequential Composition
seq = bivar_sem.mul(e1, e2)
p, r, s, t = seq
print(f"Total Mass: {p}, E[X]: {r/p}, E[Y]: {s/p}, E[XY]: {t/p}")
```

---

## 5. Universal Multivariate Joint Moments & Covariance Matrices

For $d \ge 2$ features and total polynomial degree $K$, [`MultivariateMomentSemiring(num_vars=d, order=K)`](file:///C:/dev/erivlis/algebrax/src/algebrax/semiring/statistical.py) computes the entire joint distribution, returning the **$d$-dimensional Mean Vector** and **$d \times d$ Covariance Matrix $\boldsymbol{\Sigma}$**:

$$(\mathbf{u} \otimes \mathbf{v})_{\boldsymbol{\alpha}} = \sum_{\mathbf{0} \le \boldsymbol{\beta} \le \boldsymbol{\alpha}} \left( \prod_{i=1}^d \binom{\alpha_i}{\beta_i} \right) u_{\boldsymbol{\beta}} \cdot v_{\boldsymbol{\alpha} - \boldsymbol{\beta}}$$

```python
import algebrax as ax

# 2 variables (Latency, Cost), 2nd-order total degree
msem = ax.semiring.MultivariateMomentSemiring(num_vars=2, order=2)

# Path A: 50% prob, Latency=1.0, Cost=2.0
pa = {
    (0, 0): 0.5,
    (1, 0): 0.5 * 1.0,  # E[X]
    (0, 1): 0.5 * 2.0,  # E[Y]
    (2, 0): 0.5 * 1.0,  # E[X^2]
    (0, 2): 0.5 * 4.0,  # E[Y^2]
    (1, 1): 0.5 * 2.0,  # E[XY]
}

# Path B: 50% prob, Latency=3.0, Cost=6.0
pb = {
    (0, 0): 0.5,
    (1, 0): 0.5 * 3.0,
    (0, 1): 0.5 * 6.0,
    (2, 0): 0.5 * 9.0,
    (0, 2): 0.5 * 36.0,
    (1, 1): 0.5 * 18.0,
}

# Parallel branching over graph paths
bundle = msem.add(pa, pb)

means = msem.mean_vector(bundle)
cov = msem.covariance_matrix(bundle)

print(f"Mean Vector [Latency, Cost]: {means}")  # [2.0, 4.0]
print(f"Covariance Matrix Σ:")
print(f"  [{cov[0][0]:.2f}, {cov[0][1]:.2f}]")  # [1.00, 2.00]
print(f"  [{cov[1][0]:.2f}, {cov[1][1]:.2f}]")  # [2.00, 4.00]
```
