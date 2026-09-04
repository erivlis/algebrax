# AlgebraX Feature Expansion Session

---

## 💻 Part 1: Mapping Code to Advanced Theoretical Frameworks

Your current library features map directly to high-level mathematical branches:

1. **Viterbi & Tropical Semirings:** Map directly to **Tropical Geometry**, an area of algebraic geometry where
   classical shapes are translated into combinatorial graph structures via Min-Plus algebra.
2. **String Concatenation Semiring:** Connects natively to **Formal Language Theory** and automata syntax parsing.
3. **Clifford Semiring:** Directly implements **Geometric Algebra**, providing the foundations for physics simulations
   (e.g., General Relativity or Quantum mechanics) completely free of gimbal lock.

---

## 🛠️ Part 2: Architecture for the Dual Semiring (Automatic Differentiation)

To bridge your discrete combinatorial engine into continuous calculus, you can expand `AlgebraX` with a **Dual Numbers
Semiring**. This enables exact, truncation-error-free forward-mode automatic differentiation natively inside your sparse
tensors.

### 1. Scalar Dual Number Class Implementation

Below is the mathematical architecture tracking elementary functions via the Taylor series first-order truncation rule
($f (x + x'\epsilon) = f (x) + f' (x)x'\epsilon$ where $\epsilon^2 = 0$):

```python
import math


class DualNumber:
    def __init__(self, val: float, der: float = 0.0):
        self.val = val
        self.der = der  # Tracks the exact first derivative

    def __repr__(self):
        return f"Dual({self.val}, {self.der})"

    # --- Addition and Multiplication Axioms (Semiring Interface) ---
    def __add__(self, other):
        if not isinstance(other, DualNumber):
            other = DualNumber(other)
        return DualNumber(self.val + other.val, self.der + other.der)

    def __mul__(self, other):
        if not isinstance(other, DualNumber):
            other = DualNumber(other)
        # Implements the Product Rule of Calculus: (fg)' = f'g + fg'
        return DualNumber(self.val * other.val, self.val * other.der + self.der * other.val)

    # --- Division (Quotient Rule Extension) ---
    def __truediv__(self, other):
        if not isinstance(other, DualNumber):
            other = DualNumber(other)
        if other.val == 0:
            raise ZeroDivisionError("Division by a dual number with a zero real part.")
        fx = self.val / other.val
        fdashx = (self.der * other.val - self.val * other.der) / (other.val ** 2)
        return DualNumber(fx, fdashx)

    # --- Advanced Elementary Functions (Chain Rule) ---
    def sin(self) -> "DualNumber":
        return DualNumber(math.sin(self.val), math.cos(self.val) * self.der)

    def cos(self) -> "DualNumber":
        return DualNumber(math.cos(self.val), -math.sin(self.val) * self.der)

    def exp(self) -> "DualNumber":
        fx = math.exp(self.val)
        return DualNumber(fx, fx * self.der)

    def log(self) -> "DualNumber":
        if self.val <= 0:
            raise ValueError("Logarithm undefined for non-positive values.")
        return DualNumber(math.log(self.val), (1.0 / self.val) * self.der)

    def __pow__(self, power: float) -> "DualNumber":
        fx = math.pow(self.val, power)
        fdashx = power * math.pow(self.val, power - 1)
        return DualNumber(fx, fdashx * self.der)
```

### 2. Multi-Variable Expansion: Sparse Gradient Dual Numbers

By taking advantage of your library's talent for handling sparse key-value mechanics, you can swap out the single
`float` derivative slot for a sparse `dict`. This allows tracking gradients relative to multiple parameter indices
simultaneously across tensor contractions:

```python
class SparseGradDualNumber:
    def __init__(self, val: float, der: dict[str, float] = None):
        self.val = val
        self.der = der if der is not None else {}  # Keys represent variable tokens (e.g., 'w_1')

    def __repr__(self):
        return f"Val: {self.val}, Grads: {self.der}"

    def add(self, other: "SparseGradDualNumber") -> "SparseGradDualNumber":
        # Linearity of gradients
        new_der = {
            k: self.der.get(k, 0.0) + other.der.get(k, 0.0)
            for k in set(self.der) | set(other.der)
        }
        return SparseGradDualNumber(self.val + other.val, new_der)

    def mul(self, other: "SparseGradDualNumber") -> "SparseGradDualNumber":
        # Multi-variable partial product rule: d(fg) = f'g + fg'
        new_der = {}
        for k in set(self.der) | set(other.der):
            self_part = self.der.get(k, 0.0) * other.val
            other_part = self.val * other.der.get(k, 0.0)
            new_der[k] = self_part + other_part
        return SparseGradDualNumber(self.val * other.val, new_der)
```

By computing sparse tensor contractions over this wrapper, your library automatically scales into a fully functional
machine learning backpropagation engine using nothing but raw algebraic primitives.