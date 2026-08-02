---
title: Advanced Matrix Invariants & Academic Operations
description: Guide to determinants, matrix inverses, cofactors, adjugates, and eigenvector centrality in algebrax.matrix.academic.
---

# Advanced Matrix Invariants & Academic Operations

The **`algebrax.matrix.academic`** module provides classical matrix invariants and spectral graph metrics for square
sparse dictionary matrices.

!!! WARNING
    Exact academic functions like `determinant()`, `cofactor()`, and `adjoint()` involve recursive Laplace expansion
    or $O (N^5)$ symbolic expansions. They emit a `PerformanceWarning` for $N > 10$ and are designed for academic
    demonstration and exact symbolic verification.

---

## Academic Functions

| Function                       | Operation       | Description                                                                               |
|:-------------------------------|:----------------|:------------------------------------------------------------------------------------------|
| **`determinant(matrix)`**      | $\det(A)$       | Recursive Laplace expansion determinant of square sparse matrix.                          |
| **`inverse(matrix)`**          | $A^{-1}$        | Matrix inverse computed via adjugate division $A^{-1} = \frac{1}{\det(A)} \text{adj}(A)$. |
| **`cofactor(matrix)`**         | $C_{i,j}$       | Matrix of cofactors $C_{i,j} = (-1)^{i+j} \det(M_{i,j})$.                                 |
| **`adjoint(matrix)`**          | $\text{adj}(A)$ | Classical adjugate matrix (transpose of cofactor matrix).                                 |
| **`eigen_centrality(matrix)`** | $v$             | Principal eigenvector centrality via power iteration for graph analysis.                  |

---

## Code Example

```python
from algebrax.matrix import adjoint, cofactor, determinant, eigen_centrality, inverse

# 1. Square 3x3 Sparse Matrix
A = {
    "0": {"0": 1.0, "1": 2.0, "2": 3.0},
    "1": {"0": 0.0, "1": 1.0, "2": 4.0},
    "2": {"0": 5.0, "1": 6.0, "2": 0.0},
}

# 2. Determinant & Inverse
det_A = determinant(A)
inv_A = inverse(A)
print(f"det(A) = {det_A}")
print("A^-1:", inv_A)

# 3. Cofactor & Adjugate
C = cofactor(A)
adj_A = adjoint(A)

# 4. Network Eigenvector Centrality
adj_matrix = {
    "Alice": {"Bob": 1.0, "Charlie": 1.0},
    "Bob": {"Alice": 1.0, "David": 1.0},
    "Charlie": {"Alice": 1.0},
    "David": {"Bob": 1.0},
}
centrality = eigen_centrality(adj_matrix)
print("Eigenvector Centrality:", centrality)
```
