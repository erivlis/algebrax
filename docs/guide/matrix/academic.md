---
title: Advanced Matrix Invariants & Academic Operations
description: Guide to determinants, matrix inverses, cofactors, and adjugates in algebrax.matrix.academic.
---

# Advanced Matrix Invariants & Academic Operations

The **`algebrax.matrix.academic`** module provides classical matrix invariants for square sparse dictionary matrices.

!!! WARNING
    Exact academic functions like `determinant()`, `cofactor()`, and `adjoint()` involve recursive Laplace expansion
    or $O (N^5)$ symbolic expansions. They emit a `PerformanceWarning` for $N > 10$ and are designed for academic
    demonstration and exact symbolic verification.

---

## Academic Functions

| Function                  | Operation       | Description                                                                               |
|:--------------------------|:----------------|:------------------------------------------------------------------------------------------|
| **`determinant(matrix)`** | $\det(A)$       | Recursive Laplace expansion determinant of square sparse matrix.                          |
| **`inverse(matrix)`**     | $A^{-1}$        | Matrix inverse computed via adjugate division $A^{-1} = \frac{1}{\det(A)} \text{adj}(A)$. |
| **`cofactor(matrix)`**    | $C_{i,j}$       | Matrix of cofactors $C_{i,j} = (-1)^{i+j} \det(M_{i,j})$.                                 |
| **`adjoint(matrix)`**     | $\text{adj}(A)$ | Classical adjugate matrix (transpose of cofactor matrix).                                 |

> [!NOTE]
> For graph spectral analysis and node ranking (`eigen_centrality`, `pagerank`, `fiedler_vector`), see [Discrete Calculus & Spectral Graph Theory](../analysis/discrete_calculus.md).

---

## Code Example

```python
import algebrax as ax

# 1. Square 3x3 Sparse Matrix
A = {
    "0": {"0": 1.0, "1": 2.0, "2": 3.0},
    "1": {"0": 0.0, "1": 1.0, "2": 4.0},
    "2": {"0": 5.0, "1": 6.0, "2": 0.0},
}

# 2. Determinant & Inverse
det_A = ax.matrix.determinant(A)
inv_A = ax.matrix.inverse(A)
print(f"det(A) = {det_A}")
print("A^-1:", inv_A)

# 3. Cofactor & Adjugate
C = ax.matrix.cofactor(A)
adj_A = ax.matrix.adjoint(A)
print("Cofactor Matrix:", C)
print("Adjugate Matrix:", adj_A)
```
