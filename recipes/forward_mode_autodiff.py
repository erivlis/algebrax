# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Forward-Mode Automatic Differentiation via Standard Semiring Polymorphism
#
# ## Abstract
# This recipe demonstrates how **AlgebraX's Polymorphic Semiring Engine** performs exact, machine-precision
# **Forward-Mode Automatic Differentiation (AD)** without symbolic compilation, reverse-mode tapes, or
# heavyweight external dependencies (like PyTorch or JAX).
#
# By defining lightweight carrier types—univariate `DualNumber` ($a + b\epsilon, \epsilon^2 = 0$) and
# multivariate `GradientDualNumber` ($a + \nabla f \cdot \boldsymbol{\epsilon}$) backed by AlgebraX's native
# `SparseVector`—we demonstrate that:
# 1. Standard algebraic matrix operations (`ax.matrix.dot`, `ax.matrix.power`, `ax.tensor.einsum`) seamlessly
#    propagate function evaluations alongside exact directional derivatives and full Jacobian vectors in a
#    single forward pass.
# 2. Because dual numbers form a unital commutative ring over standard arithmetic, `ax.semiring.StandardSemiring(dtype=DualNumber)`
#    executes automatic differentiation out-of-the-box with **zero modifications to the AlgebraX library core**.
#
# ---
#
# ## Theoretical Foundations & Algebraic Rigor
#
# ### 1. The Dual Number Ring as a Quotient Polynomial Ring
# Formally, the dual numbers are defined as the quotient ring:
# $$\mathbb{D} = \mathbb{R}[\epsilon] / (\epsilon^2)$$
# where $\epsilon \neq 0$ is a nilpotent infinitesimal indeterminate such that $\epsilon^2 = 0$.
#
# ### 2. Algebraic Emergence of Calculus (Product & Quotient Rules)
# The rules of differential calculus are not ad-hoc heuristics injected into the algebra; they are
# **inescapable algebraic consequences** of polynomial expansion modulo $\epsilon^2$:
#
# * **Multiplication $\implies$ Product Rule**:
#   $$(a + b\epsilon)(c + d\epsilon) = ac + ad\epsilon + bc\epsilon + bd\mathbf{\epsilon^2} = ac + (ad + bc)\epsilon$$
#
# * **Division $\implies$ Quotient Rule**:
#   Inverting $(c + d\epsilon)$ using the conjugate $(c - d\epsilon)$:
#   $$\frac{1}{c + d\epsilon} = \frac{c - d\epsilon}{(c + d\epsilon)(c - d\epsilon)} = \frac{c - d\epsilon}{c^2 - d^2\epsilon^2} = \frac{1}{c} - \frac{d}{c^2}\epsilon$$
#   $$\frac{a + b\epsilon}{c + d\epsilon} = (a + b\epsilon)\left(\frac{1}{c} - \frac{d}{c^2}\epsilon\right) = \frac{a}{c} + \frac{bc - ad}{c^2}\epsilon$$
#
# ### 3. Analytic & Transcendental Functions via Formal Power Series
# For any smooth/analytic function $f: \mathbb{R} \to \mathbb{R}$, its extension to dual numbers
# $f: \mathbb{D} \to \mathbb{D}$ is evaluated via its formal Taylor series:
# $$f(a + b\epsilon) = \sum_{k=0}^{\infty} \frac{f^{(k)}(a)}{k!} (b\epsilon)^k = f(a) + f'(a)(b\epsilon) + \frac{f''(a)}{2!}\underbrace{(b\epsilon)^2}_{=0} + \dots$$
# Because $\epsilon^k = 0$ for all $k \ge 2$, **all higher-order terms vanish identically and exactly**:
# $$f(a + b\epsilon) \equiv f(a) + f'(a)b\epsilon$$
# Thus, computing transcendental functions ($\exp, \sin, \cos, \log$) on dual numbers represents the
# exact, truncation-error-free sum of the infinite series in $\mathbb{D}$.
#
# ### 4. Geometric Interpretation & Semiring Polymorphism
# Geometrically (in Grothendieck scheme theory and synthetic differential geometry), dual numbers
# represent points with an attached infinitesimal tangent vector (the tangent bundle $T\mathbb{R}$).
#
# Because $(\mathbb{D}, +, \cdot, 0, 1)$ forms a unital commutative ring, `algebrax.semiring.StandardSemiring(dtype=DualNumber)`
# executes exact multi-hop forward-mode automatic differentiation across sparse matrices and tensors
# with **zero modifications to the core library**.

# %%
import math
from typing import Self

import algebrax as ax
from algebrax.typing import SparseVector

# %% [markdown]
# ## Step 1: Definition of the Dual Number Carrier Type

# %%
class DualNumber:
    r"""First-order dual number x + x'\epsilon with \epsilon^2 = 0."""
    __slots__ = ('der', 'val')

    def __init__(self, val: float | int = 0.0, der: float | int = 0.0) -> None:
        self.val = float(val)
        self.der = float(der)

    def __repr__(self) -> str:
        return f"DualNumber({self.val:.4f}, der={self.der:.4f})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DualNumber):
            return math.isclose(self.val, other.val, rel_tol=1e-9) and math.isclose(self.der, other.der, rel_tol=1e-9)
        if isinstance(other, (int, float)):
            return math.isclose(self.val, float(other), rel_tol=1e-9) and math.isclose(self.der, 0.0, rel_tol=1e-9)
        return False

    def __add__(self, other: Self | float | int) -> Self:
        o = other if isinstance(other, DualNumber) else DualNumber(other)
        return DualNumber(self.val + o.val, self.der + o.der)

    def __radd__(self, other: Self | float | int) -> Self:
        return self.__add__(other)

    def __sub__(self, other: Self | float | int) -> Self:
        o = other if isinstance(other, DualNumber) else DualNumber(other)
        return DualNumber(self.val - o.val, self.der - o.der)

    def __rsub__(self, other: Self | float | int) -> Self:
        o = other if isinstance(other, DualNumber) else DualNumber(other)
        return o.__sub__(self)

    def __mul__(self, other: Self | float | int) -> Self:
        o = other if isinstance(other, DualNumber) else DualNumber(other)
        # Product rule: (fg)' = f'g + fg'
        return DualNumber(self.val * o.val, self.der * o.val + self.val * o.der)

    def __rmul__(self, other: Self | float | int) -> Self:
        return self.__mul__(other)

    def __truediv__(self, other: Self | float | int) -> Self:
        o = other if isinstance(other, DualNumber) else DualNumber(other)
        if o.val == 0.0:
            raise ZeroDivisionError("Division by dual number with zero primal part.")
        # Quotient rule: (f/g)' = (f'g - fg') / g^2
        return DualNumber(self.val / o.val, (self.der * o.val - self.val * o.der) / (o.val ** 2))

    def __pow__(self, power: float | int) -> Self:
        p = float(power)
        return DualNumber(self.val ** p, p * (self.val ** (p - 1)) * self.der)

    def __neg__(self) -> "DualNumber":
        return DualNumber(-self.val, -self.der)

    def __abs__(self) -> "DualNumber":
        if self.val == 0.0:
            raise ValueError("Derivative of absolute value is undefined at 0.")
        sign = 1.0 if self.val > 0.0 else -1.0
        return DualNumber(abs(self.val), sign * self.der)

    # --- Exponential, Logarithmic & Root Functions ---

    def exp(self) -> "DualNumber":
        r"""Exponential: \exp(x + x'\epsilon) = \exp(x) + \exp(x)x'\epsilon."""
        e = math.exp(self.val)
        return DualNumber(e, e * self.der)

    def log(self, base: float | None = None) -> "DualNumber":
        r"""Natural or arbitrary base logarithm: \ln(x + x'\epsilon) = \ln(x) + (x'/x)\epsilon."""
        if self.val <= 0.0:
            raise ValueError("Logarithm undefined for non-positive primal values.")
        if base is None:
            return DualNumber(math.log(self.val), self.der / self.val)
        if base <= 0.0 or base == 1.0:
            raise ValueError("Logarithm base must be positive and not equal to 1.")
        return DualNumber(math.log(self.val, base), self.der / (self.val * math.log(base)))

    def sqrt(self) -> "DualNumber":
        r"""Square root: \sqrt{x + x'\epsilon} = \sqrt{x} + (x' / (2\sqrt{x}))\epsilon."""
        if self.val < 0.0:
            raise ValueError("Square root undefined for negative primal values.")
        if self.val == 0.0:
            raise ZeroDivisionError("Derivative of square root is singular at 0.")
        s = math.sqrt(self.val)
        return DualNumber(s, self.der / (2.0 * s))

    # --- Trigonometric Functions ---

    def sin(self) -> "DualNumber":
        r"""Sine: \sin(x + x'\epsilon) = \sin(x) + \cos(x)x'\epsilon."""
        return DualNumber(math.sin(self.val), math.cos(self.val) * self.der)

    def cos(self) -> "DualNumber":
        r"""Cosine: \cos(x + x'\epsilon) = \cos(x) - \sin(x)x'\epsilon."""
        return DualNumber(math.cos(self.val), -math.sin(self.val) * self.der)

    def tan(self) -> "DualNumber":
        r"""Tangent: \tan(x + x'\epsilon) = \tan(x) + (1 + \tan^2(x))x'\epsilon."""
        t = math.tan(self.val)
        return DualNumber(t, (1.0 + t * t) * self.der)

    def asin(self) -> "DualNumber":
        r"""Arcsine: \arcsin(x + x'\epsilon) = \arcsin(x) + (x' / \sqrt{1 - x^2})\epsilon."""
        if abs(self.val) >= 1.0:
            raise ValueError("Arcsine derivative singular or undefined for |x| >= 1.")
        return DualNumber(math.asin(self.val), self.der / math.sqrt(1.0 - self.val ** 2))

    def acos(self) -> "DualNumber":
        r"""Arccosine: \arccos(x + x'\epsilon) = \arccos(x) - (x' / \sqrt{1 - x^2})\epsilon."""
        if abs(self.val) >= 1.0:
            raise ValueError("Arccosine derivative singular or undefined for |x| >= 1.")
        return DualNumber(math.acos(self.val), -self.der / math.sqrt(1.0 - self.val ** 2))

    def atan(self) -> "DualNumber":
        r"""Arctangent: \arctan(x + x'\epsilon) = \arctan(x) + (x' / (1 + x^2))\epsilon."""
        return DualNumber(math.atan(self.val), self.der / (1.0 + self.val ** 2))

    # --- Hyperbolic & Activation Functions ---

    def sinh(self) -> "DualNumber":
        r"""Hyperbolic sine: \sinh(x + x'\epsilon) = \sinh(x) + \cosh(x)x'\epsilon."""
        return DualNumber(math.sinh(self.val), math.cosh(self.val) * self.der)

    def cosh(self) -> "DualNumber":
        r"""Hyperbolic cosine: \cosh(x + x'\epsilon) = \cosh(x) + \sinh(x)x'\epsilon."""
        return DualNumber(math.cosh(self.val), math.sinh(self.val) * self.der)

    def tanh(self) -> "DualNumber":
        r"""Hyperbolic tangent: \tanh(x + x'\epsilon) = \tanh(x) + (1 - \tanh^2(x))x'\epsilon."""
        th = math.tanh(self.val)
        return DualNumber(th, (1.0 - th * th) * self.der)

    def sigmoid(self) -> "DualNumber":
        r"""Logistic Sigmoid: \sigma(x) = 1 / (1 + \exp(-x)), \sigma'(x) = \sigma(x)(1 - \sigma(x))."""
        s = 1.0 / (1.0 + math.exp(-self.val))
        return DualNumber(s, s * (1.0 - s) * self.der)

    def relu(self) -> "DualNumber":
        r"""Rectified Linear Unit (ReLU)."""
        if self.val > 0.0:
            return DualNumber(self.val, self.der)
        return DualNumber(0.0, 0.0)


# %% [markdown]
# ## Step 2: Elementary Transcendental Functions ($\ln$, $\sqrt{\cdot}$, $\tanh$, $\sigma$)
#
# Exact differentiation through non-linear functions and composite expressions with machine precision:

# %%
x = DualNumber(val=1.0, der=1.0)  # Variable x = 1.0 with seed dx/dx = 1.0

# 1. Natural logarithm: d/dx [ln(x)] = 1/x -> at x=1, val=0, der=1.0
log_x = x.log()
assert math.isclose(log_x.val, 0.0)
assert math.isclose(log_x.der, 1.0)

# 2. Square root: d/dx [sqrt(x)] = 1 / (2*sqrt(x)) -> at x=1, val=1.0, der=0.5
sqrt_x = x.sqrt()
assert math.isclose(sqrt_x.val, 1.0)
assert math.isclose(sqrt_x.der, 0.5)

# 3. Logistic Sigmoid: d/dx [sigmoid(x)] at x=0.0
x0 = DualNumber(val=0.0, der=1.0)
sig_x0 = x0.sigmoid()
assert math.isclose(sig_x0.val, 0.5)
assert math.isclose(sig_x0.der, 0.25)

# 4. Non-linear Composite Function: g(x) = ln(x) * sqrt(x) + sin(x)
# Analytical: g(1.0) = sin(1.0), g'(1.0) = 1.0 + cos(1.0)
g_x = (x.log() * x.sqrt()) + x.sin()
print("Composite Function g(x) = ln(x)*sqrt(x) + sin(x) at x=1.0:")
print(f"  Exact Value g(1) = {g_x.val:.6f}")
print(f"  Exact Derivative g'(1) = {g_x.der:.6f}")

expected_val = math.sin(1.0)
expected_der = 1.0 + math.cos(1.0)
assert math.isclose(g_x.val, expected_val, rel_tol=1e-9)
assert math.isclose(g_x.der, expected_der, rel_tol=1e-9)


# %% [markdown]
# ## Step 3: Multi-Variable Differential Algebra & Gradient Bundles
#
# ### Mathematical Foundation: Multi-Nilpotent Quotient Algebra
# For functions of multiple parameters $(w_1, w_2, \dots, w_n)$, we generalize the dual ring to the
# multi-indeterminate quotient ring:
# $$\mathbb{D}^n = \mathbb{R}[\epsilon_1, \dots, \epsilon_n] / \langle \epsilon_i \epsilon_j = 0 \quad \forall i, j \rangle$$
#
# Every element $Z \in \mathbb{D}^n$ represents a primal scalar value $v \in \mathbb{R}$ accompanied by a
# differential 1-form / gradient vector $\mathbf{g} = \nabla f \in \mathbb{R}^n$:
# $$Z = v + \sum_{i=1}^n g_i \epsilon_i = v + \nabla f \cdot \boldsymbol{\epsilon}$$
#
# ### Sparse Vector Gradient Representation (`SparseVector[str, float]`)
# In large graphs and neural networks with millions of parameters, any given local edge or node operation
# only depends on a tiny subset of parameters (sparsity). Rather than allocating dense vectors of size $n$,
# `GradientDualNumber` represents the gradient as an AlgebraX `SparseVector` mapping `{var_name: partial_der}`:
#
# * **Linearity of Gradients ($+$ and $-$):**
#   $$\nabla (f \pm g) = \nabla f \pm \nabla g \implies \text{Merge and add/subtract sparse keys}$$
#
# * **Multivariate Leibniz Product Rule ($\cdot$):**
#   $$(u + \nabla u \cdot \boldsymbol{\epsilon})(v + \nabla v \cdot \boldsymbol{\epsilon}) = uv + (u \nabla v + v \nabla u) \cdot \boldsymbol{\epsilon} + \sum_{i,j} \nabla_i u \nabla_j v \underbrace{\epsilon_i \epsilon_j}_{=0} = uv + (u \nabla v + v \nabla u) \cdot \boldsymbol{\epsilon}$$
#
# * **Multivariate Chain Rule for Analytic Functions ($f: \mathbb{R} \to \mathbb{R}$):**
#   $$f(v + \nabla v \cdot \boldsymbol{\epsilon}) = f(v) + f'(v) (\nabla v \cdot \boldsymbol{\epsilon}) \implies \text{Scale all gradient components by } f'(v)$$

# %%
class GradientDualNumber:
    r"""Multi-variable dual number over \mathbb{R}[\epsilon_1, ..., \epsilon_n] / (\epsilon_i \epsilon_j = 0).

    Tracks sparse gradient 1-forms \nabla f as SparseVector[str, float] {param_name: \partial f / \partial param_name}.
    """
    __slots__ = ('grad', 'val')

    def __init__(
        self,
        val: float | int = 0.0,
        grad: SparseVector[str, float] | None = None,
    ) -> None:
        self.val = float(val)
        self.grad: dict[str, float] = {
            k: float(v)
            for k, v in (grad or {}).items()
            if not math.isclose(float(v), 0.0, abs_tol=1e-12)
        }

    def __repr__(self) -> str:
        grad_str = ", ".join(f"{k}: {v:.4f}" for k, v in sorted(self.grad.items()))
        return f"GradientDualNumber({self.val:.4f}, \u2207={{{grad_str}}})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GradientDualNumber):
            if not math.isclose(self.val, other.val, rel_tol=1e-9):
                return False
            all_keys = set(self.grad) | set(other.grad)
            return all(math.isclose(self.grad.get(k, 0.0), other.grad.get(k, 0.0), rel_tol=1e-9) for k in all_keys)
        if isinstance(other, (int, float)):
            return math.isclose(self.val, float(other), rel_tol=1e-9) and len(self.grad) == 0
        return False

    def __neg__(self) -> "GradientDualNumber":
        return GradientDualNumber(-self.val, {k: -v for k, v in self.grad.items()})

    def __add__(self, other: Self | float | int) -> "GradientDualNumber":
        o = other if isinstance(other, GradientDualNumber) else GradientDualNumber(other)
        all_keys = set(self.grad) | set(o.grad)
        new_grad = {k: self.grad.get(k, 0.0) + o.grad.get(k, 0.0) for k in all_keys}
        return GradientDualNumber(self.val + o.val, new_grad)

    def __radd__(self, other: Self | float | int) -> "GradientDualNumber":
        return self.__add__(other)

    def __sub__(self, other: Self | float | int) -> "GradientDualNumber":
        o = other if isinstance(other, GradientDualNumber) else GradientDualNumber(other)
        all_keys = set(self.grad) | set(o.grad)
        new_grad = {k: self.grad.get(k, 0.0) - o.grad.get(k, 0.0) for k in all_keys}
        return GradientDualNumber(self.val - o.val, new_grad)

    def __rsub__(self, other: Self | float | int) -> "GradientDualNumber":
        o = other if isinstance(other, GradientDualNumber) else GradientDualNumber(other)
        return o.__sub__(self)

    def __mul__(self, other: Self | float | int) -> "GradientDualNumber":
        o = other if isinstance(other, GradientDualNumber) else GradientDualNumber(other)
        # Multivariate product rule: \nabla(uv) = u \nabla v + v \nabla u
        all_keys = set(self.grad) | set(o.grad)
        new_grad = {k: self.grad.get(k, 0.0) * o.val + self.val * o.grad.get(k, 0.0) for k in all_keys}
        return GradientDualNumber(self.val * o.val, new_grad)

    def __rmul__(self, other: Self | float | int) -> "GradientDualNumber":
        return self.__mul__(other)

    def __truediv__(self, other: Self | float | int) -> "GradientDualNumber":
        o = other if isinstance(other, GradientDualNumber) else GradientDualNumber(other)
        if o.val == 0.0:
            raise ZeroDivisionError("Division by zero in GradientDualNumber.")
        # Multivariate quotient rule: \nabla(u/v) = (v \nabla u - u \nabla v) / v^2
        all_keys = set(self.grad) | set(o.grad)
        denom = o.val ** 2
        new_grad = {k: (self.grad.get(k, 0.0) * o.val - self.val * o.grad.get(k, 0.0)) / denom for k in all_keys}
        return GradientDualNumber(self.val / o.val, new_grad)

    def __pow__(self, power: float | int) -> "GradientDualNumber":
        p = float(power)
        factor = p * (self.val ** (p - 1))
        return GradientDualNumber(self.val ** p, {k: v * factor for k, v in self.grad.items()})

    def exp(self) -> "GradientDualNumber":
        e = math.exp(self.val)
        return GradientDualNumber(e, {k: v * e for k, v in self.grad.items()})

    def log(self) -> "GradientDualNumber":
        if self.val <= 0.0:
            raise ValueError("Logarithm undefined for non-positive values.")
        return GradientDualNumber(math.log(self.val), {k: v / self.val for k, v in self.grad.items()})

    def sin(self) -> "GradientDualNumber":
        s, c = math.sin(self.val), math.cos(self.val)
        return GradientDualNumber(s, {k: v * c for k, v in self.grad.items()})

    def cos(self) -> "GradientDualNumber":
        s, c = math.sin(self.val), math.cos(self.val)
        return GradientDualNumber(c, {k: -v * s for k, v in self.grad.items()})


# %% [markdown]
# ### Verification: Multivariate Non-Linear Function
# Let $F(x, y, z) = x^2 y + y \ln(z) + \exp(x z)$ at point $(x=2, y=3, z=1)$:
# * $F(2, 3, 1) = 2^2 \cdot 3 + 3 \ln(1) + \exp(2) = 12 + e^2 \approx 19.389056$
# * $\frac{\partial F}{\partial x} = 2 x y + z \exp(x z) = 12 + e^2 \approx 19.389056$
# * $\frac{\partial F}{\partial y} = x^2 + \ln(z) = 4 + 0 = 4.0$
# * $\frac{\partial F}{\partial z} = \frac{y}{z} + x \exp(x z) = 3 + 2 e^2 \approx 17.778112$

# %%
x_var = GradientDualNumber(val=2.0, grad={'x': 1.0})
y_var = GradientDualNumber(val=3.0, grad={'y': 1.0})
z_var = GradientDualNumber(val=1.0, grad={'z': 1.0})

F_val = (x_var ** 2) * y_var + y_var * z_var.log() + (x_var * z_var).exp()

print("Multivariate Evaluation of F(x, y, z):")
print(f"  F(2, 3, 1) = {F_val.val:.6f}")
print(f"  \u2207F = {F_val.grad}")

e2 = math.exp(2.0)
assert math.isclose(F_val.val, 12.0 + e2, rel_tol=1e-9)
assert math.isclose(F_val.grad['x'], 12.0 + e2, rel_tol=1e-9)
assert math.isclose(F_val.grad['y'], 4.0, rel_tol=1e-9)
assert math.isclose(F_val.grad['z'], 3.0 + 2.0 * e2, rel_tol=1e-9)

# %% [markdown]
# ## Step 4: Single-Variable Sensitivity Propagation in Graph Transmission
#
# ### Physical & Network Context: Path Transmission Sensitivities
# In network flow analysis (e.g., electrical grids, telecommunication routing, hydraulic piping),
# a graph's adjacency matrix $A$ represents transmission capacities between nodes. The matrix
# power / product $(A^2)_{ij} = \sum_k A_{ik} \cdot A_{kj}$ represents the total 2-hop flow capacity
# along all paths from source node $i$ to target node $j$.
#
# When an edge parameter $x$ (e.g., bandwidth, conductance, pipe diameter) is perturbed, how does
# the total multi-hop flow $(A^2)_{ij}$ respond?
#
# ### Algebraic Propagation via `StandardSemiring(DualNumber)`
# By parameterizing edge $(0 \to 1)$ as the dual number $x + 1\cdot\epsilon$ (with tangent seed
# $dx/dx = 1.0$) and keeping other edges constant ($y + 0\cdot\epsilon$), a single matrix multiplication
# `ax.matrix.dot(network, network, semiring=StandardSemiring(DualNumber))` simultaneously evaluates:
#
# 1. **Total Path Transmission (Primal):**
#    $$(A^2)_{0,2} = A_{0,1} \cdot A_{1,2} = x \cdot y = 2.0 \cdot 3.0 = 6.0$$
#
# 2. **Exact Marginal Sensitivity (Tangent):**
#    $$\frac{d}{dx} (A^2)_{0,2} = \frac{d}{dx} (A_{0,1} A_{1,2}) = \left(\frac{dA_{0,1}}{dx}\right) A_{1,2} + A_{0,1} \left(\frac{dA_{1,2}}{dx}\right) = (1.0)(3.0) + (2.0)(0.0) = 3.0$$
#
# This computes exact parameter sensitivities across arbitrary graph topologies without numerical
# perturbations or finite-difference approximations.

# %%
# Configure standard semiring parameterized by DualNumber
dual_semiring = ax.semiring.StandardSemiring(dtype=DualNumber)

# Sparse adjacency matrix where edge (0 -> 1) is parameterized by x = 2.0 with tangent dx/dx = 1.0
# and edge (1 -> 2) has weight y = 3.0 (constant, dy/dx = 0.0)
network = {
    0: {1: DualNumber(val=2.0, der=1.0), 2: DualNumber(val=5.0, der=0.0)},
    1: {2: DualNumber(val=3.0, der=0.0)},
}

# 2-step path transmission via matrix multiplication: A^2
path_2step = ax.matrix.dot(network, network, semiring=dual_semiring)

print("2-Step Network Path Transmission with Exact Sensitivities (d/dx):")
for src in sorted(path_2step):
    for dst, dual_val in sorted(path_2step[src].items()):
        print(f"  Path ({src} -> {dst}): Value = {dual_val.val:.2f}, Sensitivity d/dx = {dual_val.der:.2f}")

# Analytical verification: Path 0 -> 1 -> 2 has value x * y = 2.0 * 3.0 = 6.0, d/dx = y = 3.0
assert path_2step[0][2].val == 6.0
assert path_2step[0][2].der == 3.0

# %% [markdown]
# ## Step 5: Multi-Variable Gradient Flow across Multi-Hop Graphs
#
# ### Distributed Parameter Routing & Backpropagation-Free Jacobians
# In complex networks (e.g., Markov Decision Processes, Multi-Layer Perceptrons, Supply-Chain Pipelines),
# multiple edges are parameterized by independent tunable weights $(w_1, w_2, w_3)$.
#
# Consider a diamond routing topology from Source `A` to Sink `D`:
# * **Path 1 ($A \to B \to D$):** Traverses edge $(A \to B)$ with weight $w_1 = 1.5$ and edge $(B \to D)$ with weight $w_3 = 3.0$.
#   Flow contribution: $f_1(w_1, w_3) = w_1 \cdot w_3 = 1.5 \cdot 3.0 = 4.5$.
# * **Path 2 ($A \to C \to D$):** Traverses edge $(A \to C)$ with weight $w_2 = 2.0$ and fixed edge $(C \to D)$ with constant weight $4.0$.
#   Flow contribution: $f_2(w_2) = w_2 \cdot 4.0 = 2.0 \cdot 4.0 = 8.0$.
#
# The total combined transmission $F(w_1, w_2, w_3)$ is:
# $$F(w_1, w_2, w_3) = f_1(w_1, w_3) + f_2(w_2) = w_1 w_3 + 4.0 w_2 = 4.5 + 8.0 = 12.5$$
#
# ### The Analytic Gradient $\nabla F$
# The exact partial derivatives with respect to each independent network parameter are:
# * $\frac{\partial F}{\partial w_1} = w_3 = 3.0$ &nbsp; *(sensitivity to upstream edge $A \to B$)*
# * $\frac{\partial F}{\partial w_2} = 4.0$ &nbsp; *(sensitivity to alternate route $A \to C$)*
# * $\frac{\partial F}{\partial w_3} = w_1 = 1.5$ &nbsp; *(sensitivity to downstream bottleneck $B \to D$)*
#
# By executing a single sparse contraction `ax.matrix.dot(param_network, param_network)` over
# `StandardSemiring(GradientDualNumber)`, the complete multi-parameter gradient vector
# $\nabla F = (\frac{\partial F}{\partial w_1}, \frac{\partial F}{\partial w_2}, \frac{\partial F}{\partial w_3})$
# is computed in a single forward pass without maintaining computation graphs or tape structures.

# %%
grad_semiring = ax.semiring.StandardSemiring(dtype=GradientDualNumber)

# Network with multiple named parameters (w1, w2, w3) seeded with their basis unit partials:
param_network = {
    'A': {'B': GradientDualNumber(1.5, {'w1': 1.0}), 'C': GradientDualNumber(2.0, {'w2': 1.0})},
    'B': {'D': GradientDualNumber(3.0, {'w3': 1.0})},
    'C': {'D': GradientDualNumber(4.0, {})},
}

result = ax.matrix.dot(param_network, param_network, semiring=grad_semiring)
total_flow_ad = result['A']['D']

print(f"\nMulti-Variable Flow from A to D: {total_flow_ad}")
print(f"  Primal Value F(w1, w2, w3) = {total_flow_ad.val:.4f}")
print(f"  \u2207F = {total_flow_ad.grad}")

# Verification of exact analytical gradients:
assert total_flow_ad.val == 12.5
assert total_flow_ad.grad['w1'] == 3.0
assert total_flow_ad.grad['w2'] == 4.0
assert total_flow_ad.grad['w3'] == 1.5


# %%
def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Forward-Mode Automatic Differentiation Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
