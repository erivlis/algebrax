---
title: Core Sparse Matrix Operations
description: Comprehensive guide to basic sparse dictionary matrix operations in algebrax.matrix.core.
---

# Core Sparse Matrix Operations

The **`algebrax.matrix.core`** module provides fundamental primitives for manipulating sparse dictionary matrices (`SparseMatrix[K, V] = dict[K, dict[K, V]]`) over numerical fields and general semirings.

---

## Overview of Core Primitives

| Function | Signature / Operation | Mathematical Meaning |
|:---|:---|:---|
| **`add(m1, m2)`** | $M_1 + M_2$ | Element-wise matrix addition with zero-pruning. |
| **`dot(m1, m2, semiring=...)`** | $M_1 \cdot M_2$ | Matrix multiplication over standard arithmetic or custom semirings. |
| **`transpose(matrix)`** | $M^T$ | Swaps rows and columns: $M^T[c, r] = M[r, c]$. |
| **`inner(v1, v2, semiring=...)`** | $\langle v_1, v_2 \rangle$ | Vector inner product over a semiring. |
| **`power(matrix, n, semiring=...)`** | $M^n$ | Fast binary exponentiation matrix power. |
| **`mat_vec(matrix, vector)`** | $M \cdot v$ | Matrix-vector multiplication. |
| **`vec_mat(vector, matrix)`** | $v^T \cdot M$ | Vector-matrix multiplication. |
| **`hstack(matrices)`** | $[M_1 \mid M_2]$ | Horizontal concatenation along column dimensions. |
| **`vstack(matrices)`** | $\begin{bmatrix} M_1 \\ M_2 \end{bmatrix}$ | Vertical concatenation along row dimensions. |
| **`block(matrix, rows, cols)`** | $M[\text{rows}, \text{cols}]$ | Slice sub-matrix with index re-basing to 0. |

---

## Code Example

```python
import algebrax as ax

# 1. Define sparse matrices
A = {
    "node_A": {"node_A": 1.0, "node_B": 2.0},
    "node_B": {"node_A": 3.0, "node_B": 4.0},
}
B = {
    "node_A": {"node_A": 0.5, "node_B": 1.5},
    "node_B": {"node_A": 2.5, "node_B": 3.5},
}

# 2. Addition & Transpose
A_plus_B = ax.matrix.add(A, B)
A_T = ax.matrix.transpose(A)

# 3. Matrix Power (A^3)
A_cubed = ax.matrix.power(A, 3)

# 4. Matrix-Vector Multiplication
v = {"node_A": 10.0, "node_B": 20.0}
Av = ax.matrix.mat_vec(A, v)
print("A * v:", Av)  # -> {'node_A': 50.0, 'node_B': 110.0}
```
