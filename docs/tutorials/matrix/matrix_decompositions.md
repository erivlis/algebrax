---
title: Sparse Matrix Decompositions
description: Tutorial on sparse LU, QR, SVD, and Cholesky matrix factorizations in algebrax.decompose.
---

# Sparse Matrix Decompositions

The **`algebrax.matrix.decompose`** module provides factorizations and matrix decompositions for sparse dictionary matrices.

---

## Supported Decompositions

| Decomposition         | Function        | Invariant                                    | Description                                                              |
|:----------------------|:----------------|:---------------------------------------------|:-------------------------------------------------------------------------|
| **LU (Pivoted)**      | `lu(A)`         | $P \cdot A = L \cdot U$                      | Unit lower-triangular $L$, upper-triangular $U$, permutation matrix $P$. |
| **QR (Gram-Schmidt)** | `qr(A)`         | $A = Q \cdot R$                              | Orthonormal column matrix $Q$ ($Q^T Q = I$), upper-triangular $R$.       |
| **SVD (Truncated)**   | `svd(A, k=...)` | $A \approx U \cdot \text{diag}(S) \cdot V^T$ | Singular vectors $U, V^T$ and singular values vector $S$.                |
| **Cholesky**          | `cholesky(A)`   | $A = L \cdot L^T$                            | Lower-triangular $L$ for symmetric positive-definite matrices.           |

---

## Python Example

```python
from algebrax.matrix.decompose import lu, qr, svd, cholesky
from algebrax.matrix import dot, transpose

# 1. Cholesky Decomposition
A_spd = {
    "0": {"0": 4.0, "1": 12.0},
    "1": {"0": 12.0, "1": 37.0},
}
L = cholesky(A_spd)
print("Cholesky L:", L)
print("L @ L^T == A:", dot(L, transpose(L)) == A_spd)

# 2. LU Decomposition
A = {
    "0": {"0": 1.0, "1": 2.0, "2": 4.0},
    "1": {"0": 3.0, "1": 8.0, "2": 14.0},
    "2": {"0": 2.0, "1": 6.0, "2": 13.0},
}
P, L, U = lu(A)
print("P @ A == L @ U:", dot(P, A) == dot(L, U))

# 3. QR Decomposition
Q, R = qr(A)
print("Q @ R == A:", dot(Q, R) == A)

# 4. Truncated SVD (Top k=1 singular component)
U1, S1, VT1 = svd(A, k=1)
print("Top Singular Value:", S1[0])
```
