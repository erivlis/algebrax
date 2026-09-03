---
title: Statistical & Moment Semirings
description: Theoretical foundations, moment-generating algebras, and computational pipelines for Log-Sum-Exp, Dual Numbers, Expectations, Variances, and Skewness in AlgebraX.
---

# Statistical & Moment Semirings

Statistical and probabilistic modeling on graphs, sequence models (HMMs, WFSTs), and computational graphs frequently requires tracking not just optimal paths, but entire probability distributions and their polynomial moments.

**AlgebraX** provides five foundational statistical semirings in `algebrax.semiring`:

1. **`LogSemiring`**: $(\mathbb{R} \cup \{-\infty\}, \text{LogSumExp}, +, -\infty, 0)$ for underflow-free partition function summation and belief propagation.
2. **`DualNumberSemiring`**: $\mathbb{R}[\epsilon]/(\epsilon^2)$ for exact forward-mode automatic differentiation.
3. **`ExpectationSemiring`**: First-order expectations $(p, v)$ over stochastic paths (Eisner, 2002).
4. **`VarianceSemiring`**: Second-order expectations and covariances $(p, r, s, t)$ in $\mathbb{R}[\epsilon_1, \epsilon_2] / (\epsilon_1^2, \epsilon_2^2)$ (Li & Eisner, 2009).
5. **`SkewnessSemiring`** *(or `ThirdMomentSemiring`)*: Third-order raw moments and distribution asymmetry $(p, m_1, m_2, m_3)$ in $\mathbb{R}[\epsilon]/(\epsilon^4)$.

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

## 2. DualNumberSemiring: Quotient Ring $\mathbb{R}[\epsilon]/(\epsilon^2)$

The dual numbers form a commutative ring extending the real field by an infinitesimal nilpotent indeterminate $\epsilon$ satisfying $\epsilon^2 = 0$:

$$\mathbb{D} = \mathbb{R}[\epsilon] / (\epsilon^2) = \{u + u'\epsilon \mid u, u' \in \mathbb{R}\}$$

* **Addition**: $(u_1 + u_1'\epsilon) + (u_2 + u_2'\epsilon) = (u_1 + u_2) + (u_1' + u_2')\epsilon$
* **Multiplication (Leibniz Product Rule)**:
  $$(u_1 + u_1'\epsilon)(u_2 + u_2'\epsilon) = u_1 u_2 + (u_1 u_2' + u_2 u_1')\epsilon + u_1' u_2' \mathbf{\epsilon^2} = (u_1 u_2) + (u_1 u_2' + u_2 u_1')\epsilon$$

Because dual numbers form a unital ring, computing sparse matrix powers and determinants over `DualNumberSemiring` evaluates the output values and exact gradients simultaneously in a single pass.

```python
import algebrax as ax

dual_sem = ax.semiring.DualNumberSemiring()

# Function: f(x) = x^3 at x = 2.0 (seed x' = 1.0)
x = (2.0, 1.0)
x3 = dual_sem.power(x, 3)

val, deriv = x3
print(f"f(2) = {val:.1f}, f'(2) = {deriv:.1f}")  # f(2) = 8.0, f'(2) = 12.0
```

---

## 3. ExpectationSemiring: First-Order Path Expectations

Introduced by **Jason Eisner (2002)** for natural language processing, speech recognition, and weighted finite-state automata, the **ExpectationSemiring** is a domain specialization of the Dual Number Ring.

Values are pairs $(p, v) \in \mathbb{R}_{\ge 0} \times \mathbb{R}$ where:
* $p = \sum_{\pi} P(\pi)$: Total probability mass of paths.
* $v = \sum_{\pi} P(\pi) W(\pi)$: Total probability-weighted reward/feature value ($E[W] \cdot p$).

### Operations
$$\begin{aligned}
(p_1, v_1) \oplus (p_2, v_2) &= (p_1 + p_2, \; v_1 + v_2) \\
(p_1, v_1) \otimes (p_2, v_2) &= (p_1 p_2, \; p_1 v_2 + p_2 v_1) \\
\mathbf{0} &= (0.0, 0.0) \\
\mathbf{1} &= (1.0, 0.0)
\end{aligned}$$

Expected value over the path bundle is extracted as $\mu = \frac{v}{p}$.

---

## 4. VarianceSemiring: Second Central Moments & Covariances

To compute risk, variance, and second-order Taylor terms, **Li & Eisner (2009)** extended the expectation semiring to second-order dual numbers:

$$\mathbb{D}^{(2)} = \mathbb{R}[\epsilon_1, \epsilon_2] / (\epsilon_1^2, \epsilon_2^2)$$

Values are 4-tuples $(p, r, s, t) \in \mathbb{R}^4$:
* $p$: Total probability mass $Z$.
* $r, s$: First moments along features $X_1$ and $X_2$ ($E[X] \cdot Z$).
* $t$: Second raw cross-moment ($E[X_1 X_2] \cdot Z$).

### Multiplication
$$\begin{aligned}
p &= p_1 p_2 \\
r &= p_1 r_2 + p_2 r_1 \\
s &= p_1 s_2 + p_2 s_1 \\
t &= p_1 t_2 + p_2 t_1 + r_1 s_2 + r_2 s_1
\end{aligned}$$

### Variance Recovery
When $r = s$ (tracking a single random variable $X$):
$$\text{Var}(X) = \frac{t}{p} - \left(\frac{r}{p}\right)^2$$

---

## 5. SkewnessSemiring: Third Moments & Distribution Asymmetry

The **SkewnessSemiring** (or `ThirdMomentSemiring`) generalizes moment propagation to the 3rd-order divided power quotient ring:

$$\mathbb{D}^{(3)} = \mathbb{R}[\epsilon] / (\epsilon^4)$$

Values are 4-tuples $(p, m_1, m_2, m_3) \in \mathbb{R}^4$:
* $p = \sum p_i$: Total probability mass $Z$.
* $m_1 = \sum p_i x_i$: 1st raw moment ($E[X] \cdot Z$).
* $m_2 = \sum p_i x_i^2$: 2nd raw moment ($E[X^2] \cdot Z$).
* $m_3 = \sum p_i x_i^3$: 3rd raw moment ($E[X^3] \cdot Z$).

### Binomial Moment Convolution
Under serial composition ($x = x_A + x_B$), independent moments convolve via binomial coefficients:
$$\begin{aligned}
p &= p_1 p_2 \\
m_1 &= p_1 m_{1,2} + p_2 m_{1,1} \\
m_2 &= p_1 m_{2,2} + 2 m_{1,1} m_{1,2} + p_2 m_{2,1} \\
m_3 &= p_1 m_{3,2} + 3 m_{2,1} m_{1,2} + 3 m_{1,1} m_{2,2} + p_2 m_{3,1}
\end{aligned}$$

### Statistical Metrics
$$\begin{aligned}
\text{Mean } \mu &= \frac{m_1}{p} \\
\text{Variance } \sigma^2 &= \frac{m_2}{p} - \mu^2 \\
\text{3rd Central Moment } \mu_3 &= \frac{m_3}{p} - 3\mu \frac{m_2}{p} + 2\mu^3 \\
\text{Skewness } \gamma_1 &= \frac{\mu_3}{\sigma^3}
\end{aligned}$$

---

## 6. End-to-End Example: Graph Path Risk & Skewness Analysis

```python
import algebrax as ax

sem = ax.semiring.SkewnessSemiring()

# Define transitions: (prob, m1, m2, m3) where m_k = p * w^k
# Path 1: 50% prob, weight 2.0 -> (0.5, 0.5*2, 0.5*4, 0.5*8)
path1 = (0.5, 1.0, 2.0, 4.0)

# Path 2: 50% prob, weight 6.0 -> (0.5, 0.5*6, 0.5*36, 0.5*216)
path2 = (0.5, 3.0, 18.0, 108.0)

# Parallel sum (Union of paths)
bundle = sem.add(path1, path2)
p, m1, m2, m3 = bundle

mean = m1 / p
var = (m2 / p) - mean**2
mu3 = (m3 / p) - 3 * mean * (m2 / p) + 2 * (mean**3)
skewness = mu3 / (var ** 1.5)

print(f"Total Mass (Z): {p:.2f}")
print(f"Expected Cost (μ): {mean:.2f}")
print(f"Variance (σ²): {var:.2f}")
print(f"Skewness (γ1): {skewness:.4f}")
```
