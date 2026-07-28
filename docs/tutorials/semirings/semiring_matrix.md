---
title: Matrix Semirings
---

# Advanced Semirings (Matrix / Fiber Bundles)

These semirings use **Matrices** as values, allowing for non-commutative operations.
This models **Gauge Theory**, **Robotics Kinematics**, and **Currency Arbitrage**.

!!! note "Dependency"
This example requires `numpy`.

<!-- name: test_matrix_semiring -->

```python linenums="1"
import numpy as np
from algebrax.semiring import Semiring


class MatrixSemiring(Semiring[np.ndarray]):
    """
    Models a Vector Bundle connection (Parallel Transport).
    Elements are matrices.
    Plus: Element-wise Min (Aggregation).
    Times: Matrix Multiplication (Composition).
    """

    def __init__(self, dim: int):
        self.dim = dim

    @property
    def zero(self) -> np.ndarray:
        # Identity for 'Plus' (Infinity for distance)
        return np.full((self.dim, self.dim), np.inf)

    @property
    def one(self) -> np.ndarray:
        # Identity for 'Times' (Identity Matrix)
        return np.eye(self.dim)

    def add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.minimum(a, b)

    def mul(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        # Non-Commutative! Order matters.
        return a @ b

    def nsum(self, a: np.ndarray, n: int) -> np.ndarray:
        # Scalar multiplication in Min-Plus is just 'a' (idempotent)
        # But for matrices, it's element-wise min n times... which is just 'a'.
        return a

    def power(self, a: np.ndarray, n: int) -> np.ndarray:
        # Matrix power using binary exponentiation
        if n == 0: return self.one
        res = self.one
        base = a
        while n > 0:
            if n % 2 == 1:
                res = self.mul(res, base)
            base = self.mul(base, base)
            n //= 2
        return res

    def star(self, a: np.ndarray) -> np.ndarray:
        # Kleene star for matrices (I + A + A^2 + ...)
        # In Tropical Matrix semiring, this solves All-Pairs Shortest Path
        # Usually implemented via Floyd-Warshall, but here's the series definition.
        # For small N, we can just sum powers up to N.
        res = self.one
        term = a
        for _ in range(self.dim):  # A^dim is usually enough for convergence in graphs
            res = self.add(res, term)
            term = self.mul(term, a)
        return res


# Usage: Currency Arbitrage / Coordinate Transform
dim = 2
ms = MatrixSemiring(dim)


# Transformation A -> B (e.g., Rotate 90 degrees)
# In Tropical context, this would be costs. Let's use standard matrix mul for rotation.
# Wait, MatrixSemiring above is Min-Plus. Let's define a Standard Matrix Semiring for Rotation.

class StandardMatrixSemiring(MatrixSemiring):
    @property
    def zero(self): return np.zeros((self.dim, self.dim))

    def add(self, a, b): return a + b

    def mul(self, a, b): return a @ b


sms = StandardMatrixSemiring(2)
rot90 = np.array([[0, -1], [1, 0]])
rot180 = sms.mul(rot90, rot90)

print("Rotation 180:\n", rot180)
# [[-1, 0], [0, -1]]
```
