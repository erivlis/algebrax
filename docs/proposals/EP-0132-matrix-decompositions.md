---
title: "EP-0132: Matrix Decompositions — LU, QR, SVD"
description: "Sparse dictionary-based matrix decomposition primitives completing the Noether symmetry of construction/deconstruction."
icon: lucide/split
status: final
---

# EP-0132: Matrix Decompositions — LU, QR, SVD

| Field       | Value                               |
|:------------|:------------------------------------|
| **EP**      | 0132                                |
| **Title**   | Matrix Decompositions — LU, QR, SVD |
| **Author**  | Eran Rivlis & Antigravity           |
| **Status**  | Final                               |
| **Type**    | Standards Track                     |
| **Created** | 2026-08-02                          |
| **Updated** | 2026-08-02                          |

## Abstract

The library provides matrix construction primitives (`dot`, `power`, `add`, `transpose`, `determinant`,
`inverse`) but lacks the dual *deconstruction* primitives. This proposal introduces sparse dictionary-based LU, QR, and
SVD decompositions in a new `algebrax.decompose` module.

## Motivation

**Noether (Symmetry):** *"Does the API feel balanced?"* Every mathematical construction has a natural dual
deconstruction. The library can *build* matrices via `dot` and `power` but cannot *factor* them. This creates an
asymmetry that Noether's pillar demands we resolve.

## Specification

### Module: `algebrax.matrix.decompose`

```python
def lu(matrix: SparseMatrix) -> tuple[SparseMatrix, SparseMatrix, SparseMatrix]:
    """LU decomposition with partial pivoting: P @ A = L @ U"""

def qr(matrix: SparseMatrix) -> tuple[SparseMatrix, SparseMatrix]:
    """QR decomposition via modified Gram-Schmidt: A = Q @ R"""

def svd(matrix: SparseMatrix) -> tuple[SparseMatrix, SparseVector, SparseMatrix]:
    """Truncated SVD for sparse matrices: A ≈ U @ diag(S) @ V^T"""

def cholesky(matrix: SparseMatrix) -> SparseMatrix:
    """Cholesky decomposition for positive-definite matrices: A = L @ L^T"""
```

### Falsifiable Invariants

- `dot(P, A) == dot(L, U)` for LU
- `dot(Q, R) == A` and `dot(transpose(Q), Q) == I` for QR
- `dot(U, dot(diag(S), transpose(V))) ≈ A` for SVD
- `dot(L, transpose(L)) == A` for Cholesky

## Backwards Compatibility

Purely additive. New module `algebrax.decompose`.

## Change Log

* **2026-08-02:** Initial Draft.
* **2026-08-02:** Implemented `algebrax.decompose` (`lu`, `qr`, `svd`, `cholesky`) and unit tests (278 tests passing). Status → Final.
