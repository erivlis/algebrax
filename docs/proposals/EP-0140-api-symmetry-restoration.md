---
title: "EP-0140: API Symmetry Restoration — Inverse Transforms & Recomposition"
description: "Restores API duality by adding missing inverse operations for transforms, decompositions, tensors, and homology."
icon: lucide/flip-horizontal-2
status: draft
---

# EP-0140: API Symmetry Restoration — Inverse Transforms & Recomposition

| Field       | Value                                                      |
|:------------|:-----------------------------------------------------------|
| **EP**      | 0140                                                       |
| **Title**   | API Symmetry Restoration — Inverse Transforms & Recomposition |
| **Author**  | Eran Rivlis & Antigravity                                  |
| **Status**  | Draft                                                      |
| **Type**    | Standards Track                                            |
| **Created** | 2026-08-02                                                 |
| **Updated** | 2026-08-02                                                 |

## Abstract

Every mathematical construction has a natural dual deconstruction. The Grand Council Assessment (Noether)
identified 8 missing inverse/dual operations across 4 modules. This proposal restores full API symmetry.

## Motivation

The library provides `dft` ↔ `idft`, `dense_to_sparse` ↔ `sparse_to_dense`, and `gradient` ↔ `divergence` as
complete dual pairs. However, several operations lack their inverse counterpart, breaking round-trip capability
and preventing verification of factorization correctness.

## Specification

### 1. Matrix Factorization Recomposition (`algebrax.matrix.decompose`)

```python
def recompose_lu(P: SparseMatrix, L: SparseMatrix, U: SparseMatrix) -> SparseMatrix:
    """Reconstruct A from LU factorization: A = P^T @ L @ U"""

def recompose_qr(Q: SparseMatrix, R: SparseMatrix) -> SparseMatrix:
    """Reconstruct A from QR factorization: A = Q @ R"""

def recompose_svd(U: SparseMatrix, S: SparseVector, V_T: SparseMatrix) -> SparseMatrix:
    """Reconstruct A from SVD: A = U @ diag(S) @ V_T"""

def recompose_cholesky(L: SparseMatrix) -> SparseMatrix:
    """Reconstruct A from Cholesky: A = L @ L^T"""
```

### 2. Inverse Signal Transforms (`algebrax.transforms`)

```python
def iwalsh_hadamard(signal: SparseVector, n: int | None = None) -> SparseVector:
    """Inverse Walsh-Hadamard transform: X_k = (1/N) * WHT(x)_k"""

def iz_transform(X: Callable, signal_length: int, radius: float = 1.0) -> SparseVector:
    """Inverse Z-transform via contour integration approximation."""

def deconvolve(signal: SparseVector, kernel: SparseVector) -> SparseVector:
    """Spectral deconvolution: recover f from g = f * kernel via DFT division."""
```

### 3. Tensor Inverse (`algebrax.tensor`)

```python
def unpermute_tensor(tensor: SparseTensor, axes: tuple[int, ...], original_axes: tuple[int, ...]) -> SparseTensor:
    """Inverse axis permutation restoring original tensor index order."""
```

### 4. Coboundary Operator (`algebrax.homology`)

```python
def coboundary(complex: SparseChainComplex, k: int) -> SparseMatrix:
    """Coboundary operator d^k = D_{k+1}^T : C^k -> C^{k+1}"""

def cohomology_rank(complex: SparseChainComplex, k: int) -> int:
    """Compute k-th cohomology rank: dim(ker d^k) - dim(im d^{k-1})"""
```

## Falsifiable Invariants

- `recompose_lu(P, L, U) ≈ A` (original matrix, within float tolerance)
- `recompose_qr(Q, R) ≈ A`
- `recompose_svd(U, S, V_T) ≈ A`
- `recompose_cholesky(L) ≈ A`
- `iwalsh_hadamard(walsh_hadamard(x)) ≈ x` (round-trip identity)
- `deconvolve(convolve(f, k), k) ≈ f`
- `coboundary(complex, k) == transpose(boundary(complex, k+1))`

## Backwards Compatibility

Purely additive. New functions in existing modules.

## Change Log

* **2026-08-02:** Initial Draft from Grand Council Assessment (Noether).
