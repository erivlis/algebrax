---
title: Core Sparse Matrix Operations
description: Comprehensive guide to basic sparse dictionary matrix operations in algebrax.matrix.core.
---

# Core Sparse Matrix Operations

The **`algebrax.matrix.core`** module provides fundamental primitives for manipulating sparse dictionary matrices
(`SparseMatrix[K, V] = dict[K, dict[K, V]]`) over numerical fields and general semirings.

---

## Overview of Core Primitives

| Function                                       | Signature / Operation                      | Mathematical Meaning                                                                                             |
|:-----------------------------------------------|:-------------------------------------------|:-----------------------------------------------------------------------------------------------------------------|
| **`add(m1, m2, semiring=...)`**                | $M_1 \oplus M_2$                           | Element-wise matrix addition over standard arithmetic or any `Semiring` with identity pruning.                   |
| **`subtract(m1, m2)`**                         | $M_1 - M_2$                                | Element-wise matrix subtraction with zero-pruning.                                                               |
| **`dot(m1, m2, semiring=...)`**                | $M_1 \otimes M_2$                          | Matrix multiplication over standard arithmetic or custom semirings (instance, class, or string alias).           |
| **`commutator(m1, m2)`**                       | $[M_1, M_2] = M_1 M_2 - M_2 M_1$           | Lie commutator bracket of two matrices.                                                                          |
| **`transpose(matrix)`**                        | $M^T$                                      | Swaps rows and columns: $M^T[c, r] = M[r, c]$.                                                                   |
| **`inner(v1, v2, semiring=...)`**              | $\langle v_1, v_2 \rangle$                 | Vector inner product over a semiring.                                                                            |
| **`frobenius_inner(m1, m2, conjugate=...)`**   | $\langle M_1, M_2 \rangle_F$               | Frobenius (Hilbert-Schmidt) inner product with optional complex conjugation or semiring dispatch.                |
| **`power(matrix, n, semiring=...)`**           | $M^n$                                      | Fast binary exponentiation matrix power.                                                                         |
| **`mat_vec(matrix, vector, semiring=...)`**    | $M \cdot v$                                | Matrix-vector multiplication over a semiring.                                                                    |
| **`vec_mat(vector, matrix, semiring=...)`**    | $v^T \cdot M$                              | Vector-matrix multiplication over a semiring.                                                                    |
| **`vec_add(u, v)`**                            | $u + v$                                    | Sparse vector addition with automatic zero-pruning.                                                              |
| **`vec_scale(u, scalar)`**                     | $\alpha u$                                 | Sparse scalar-vector multiplication.                                                                             |
| **`vec_axpy(a, x, y)`**                        | $a x + y$                                  | Fused sparse BLAS-1 update (`axpy`) with zero-tolerance pruning.                                                 |
| **`vec_norm(u, p=2)`**                         | $\|u\|_p$                                  | Sparse vector $\ell_p$ norm ($p=1, 2, \infty$, or general $p > 0$).                                              |
| **`vec_clean(u, tol=1e-14)`**                  | $\{k: u_k \mid                             | u_k                                                                                                              | > \text{tol}\}$       | Prunes near-zero entries from a sparse vector.                                                                   |
| **`laplacian_matrix(matrix, normalized=...)`** | $L = D - W$                                | Combinatorial, symmetric normalized ($L_{\mathrm{sym}}$), or random-walk ($L_{\mathrm{rw}}$) Laplacian operator. |
| **`trace(matrix, semiring=...)`**              | $\operatorname{Tr}(M) = \bigoplus M_{i,i}$ | Diagonal trace reduction over standard arithmetic or any `Semiring`.                                             |
| **`inverse(matrix, tol=...)`**                 | $M^{-1}$                                   | Sparse matrix inversion via single-pass augmented Gauss-Jordan elimination with partial pivoting.                |
| **`block_diag(*matrices)`**                    | $\operatorname{diag}(M_1, M_2, \dots)$     | Direct sum block-diagonal matrix construction.                                                                   |
| **`hstack(matrices)`**                         | $[M_1 \mid M_2]$                           | Horizontal concatenation along column dimensions.                                                                |
| **`vstack(matrices)`**                         | $\begin{bmatrix} M_1 \\ M_2 \end{bmatrix}$ | Vertical concatenation along row dimensions.                                                                     |
| **`block(matrix, rows, cols)`**                | $M[\text{rows}, \text{cols}]$              | Slice sub-matrix with index re-basing to 0.                                                                      |
| **`kronecker_delta(i, j)`**                    | $\delta_{i, j}$                            | Returns 1 if $i = j$, else 0.                                                                                    |

---

## Code Example

```python
import algebrax as ax

# 1. Define sparse matrices
A = {
    'node_A': {'node_A': 1.0, 'node_B': 2.0},
    'node_B': {'node_A': 3.0, 'node_B': 4.0},
}
B = {
    'node_A': {'node_A': 0.5, 'node_B': 1.5},
    'node_B': {'node_A': 2.5, 'node_B': 3.5},
}

# 2. Addition & Transpose
A_plus_B = ax.matrix.add(A, B)
A_T = ax.matrix.transpose(A)

# 3. Matrix Power (A^3)
A_cubed = ax.matrix.power(A, 3)

# 4. Matrix-Vector Multiplication
v = {'node_A': 10.0, 'node_B': 20.0}
Av = ax.matrix.mat_vec(A, v)
print('A * v:', Av)  # -> {'node_A': 50.0, 'node_B': 110.0}

# 5. Graph Laplacian Operator (L = D - W)
graph = {
    'node_A': {'node_B': 2.0},
    'node_B': {'node_A': 2.0},
}
L = ax.matrix.laplacian_matrix(graph)
print('Laplacian Matrix:', L)
# -> {'node_A': {'node_A': 2.0, 'node_B': -2.0}, 'node_B': {'node_A': -2.0, 'node_B': 2.0}}
```
