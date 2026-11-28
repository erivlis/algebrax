---
title: Sparse Matrix Decompositions
description: Tutorial on sparse LU, QR, SVD, and Cholesky matrix factorizations in algebrax.matrix.decompose.
---

# Sparse Matrix Decompositions

The **`algebrax.matrix.decompose`** module provides factorizations and matrix decompositions for sparse dictionary matrices.

---

## Supported Decompositions & Elimination Kernels

All matrix factorizations and triangular solvers order homogeneous comparable keys (`int`, `tuple`, `str`) naturally via
`algebrax.converters.canonical_sort_keys` (preventing lexicographic `'10' < '2'` inversions) and preserve exact pivot
alignment on rectangular and disjoint-key matrices.

| Operation / Decomposition | Function | Invariant | Description |
|:--------------------------|:---------|:----------|:------------|
| **LU (Pivoted)** | `lu_decompose(A, field=...)` | $P \cdot A = L \cdot U$ | Unit lower-triangular $L$, upper-triangular $U$, permutation matrix $P$ over float/complex or exact `Field[V]`. |
| **Linear Solve / Inverse** | `solve(A, b, field=...)`, `inv(A, field=...)` | $A x = b$, $A A^{-1} = I$ | Reuses a single $O(N^3)$ LU factorization; detects omitted-zero singular domains cleanly. |
| **QR (Gram-Schmidt)** | `qr(A)` | $A = Q \cdot R$ | Orthonormal column matrix $Q$ ($Q^T Q = I$), upper-triangular $R$. |
| **SVD (Truncated)** | `svd(A, k=...)` | $A \approx U \cdot \text{diag}(S) \cdot V^T$ | Singular vectors $U, V^T$ and singular values vector $S$. |
| **Cholesky** | `cholesky(A)` | $A = L \cdot L^T$ | Lower-triangular $L$ for symmetric positive-definite matrices; validates symmetry across the full row/column domain. |
| **Sparse RREF** | `sparse_rref(A, field=...)` | $(R, \text{pivots})$ | `Field[V]`-polymorphic sparse Reduced Row Echelon Form on `RectSparseMatrix[R, C, V]`. |
| **Sparse Rank** | `rank(A, field=...)` | $\operatorname{rank}_{\mathbb{K}}(A)$ | Forward-only sparse elimination (no back-substitution fill-in) with exact or partial pivoting. |
| **Sparse Nullspace** | `nullspace(A, cols=..., field=...)` | $\ker_{\mathbb{K}}(A)$ | Exact sparse kernel basis honoring omitted all-zero domain columns via `cols`. |

---

## Python Example

```python
import algebrax as ax

# 1. Cholesky Decomposition
A_spd = {
    '0': {'0': 4.0, '1': 12.0},
    '1': {'0': 12.0, '1': 37.0},
}
L = ax.matrix.cholesky(A_spd)
print('Cholesky L:', L)
print('L @ L^T == A:', ax.matrix.dot(L, ax.matrix.transpose(L)) == A_spd)

# 2. LU Decomposition
A = {
    '0': {'0': 1.0, '1': 2.0, '2': 4.0},
    '1': {'0': 3.0, '1': 8.0, '2': 14.0},
    '2': {'0': 2.0, '1': 6.0, '2': 13.0},
}
P, L, U = ax.matrix.lu_decompose(A)
print('P @ A == L @ U:', ax.matrix.dot(P, A) == ax.matrix.dot(L, U))

# 3. QR Decomposition
Q, R = ax.matrix.qr(A)
print('Q @ R == A:', ax.matrix.dot(Q, R) == A)

# 4. Truncated SVD (Top k=1 singular component)
U1, S1, VT1 = ax.matrix.svd(A, k=1)
print('Top Singular Value:', S1[0])
```
