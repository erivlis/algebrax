---
title: "EP-0101: Sparse Chain Complexes & Nilpotent Differential Operators"
description: "Abstracting boundary operators D_k satisfying D_{k-1} o D_k = 0 across graphs, sheaves, and complexes."
icon: lucide/layers
status: final
---

# EP-0101: Sparse Chain Complexes & Nilpotent Differential Operators

| Field       | Value                                                     |
|:------------|:----------------------------------------------------------|
| **EP**      | 0101                                                      |
| **Title**   | Sparse Chain Complexes & Nilpotent Differential Operators |
| **Author**  | Eran Rivlis & Antigravity                                 |
| **Status**  | Final                                                     |
| **Type**    | Standards Track                                           |
| **Created** | 2026-08-01                                                |
| **Updated** | 2026-08-01                                                |

## Abstract

This proposal specifies an extension to `algebrax.analysis`: introducing the `SparseChainComplex` class. It formalizes sequence spaces $C_k$ and sparse boundary operators $D_k: C_k \to C_{k-1}$ enforcing the fundamental nilpotency identity $D_{k-1} \circ D_k = \mathbf{0}$. This foundational abstraction unifies 1D graph Laplacians, Sheaf coboundary gradients $\delta_0$, simplicial homology boundary matrices, and categorical hom-set complexes into a single reusable mathematical container.

---

## Motivation

Currently, `algebrax.analysis` provides isolated functions for graph gradients (`gradient`), graph Laplacians (`laplacian`), and Forman-Ricci curvature (`forman_ricci_curvature`). While powerful, these implementations treat 0D nodes and 1D edges as special cases without providing a formal **Chain Complex** container.

By introducing `SparseChainComplex`:
1. The nilpotency property $D_{k-1} \circ D_k = \mathbf{0}$ is validated automatically across all dimensions using `dot(D_k_minus_1, D_k, semiring=...) == {}`.
2. Combinatorial Laplacians across any dimension $k$ are unified via the Hodge-Laplacian operator:
   $$\Delta_k = D_{k+1} D_{k+1}^T + D_k^T D_k$$
3. Specialized domain modules (`algebrax.homology`, `algebrax.category`) build directly upon `SparseChainComplex` without duplicating matrix boundary code.

---

## Rationale (The Council Framework)

* **Symmetry (Noether)**: Dual relationship between boundary matrix $D_k$ and coboundary matrix $D_k^T$.
* **Falsifiability (Popper)**: Automatic invariant test checking `dot(D_k_minus_1, D_k) == {}`.
* **Clarity (Feynman)**: The Hodge-Laplacian formula $\Delta_k = D_{k+1} D_{k+1}^T + D_k^T D_k$ replaces ad-hoc graph Laplacian formulas with a single, clear differential geometry equation.

---

## Specification

### `SparseChainComplex`
```python
class SparseChainComplex:
    """
    A sequence of vector spaces C_k and sparse boundary matrices D_k satisfying D_{k-1} o D_k = 0.
    """

    def __init__(self, boundary_matrices: dict[int, SparseMatrix]):
        self.boundary_matrices = boundary_matrices

    def verify_nilpotency(self, k: int, semiring: Semiring = StandardSemiring()) -> bool:
        """
        Verify that D_{k-1} o D_k == 0 (empty sparse matrix).
        """
        if k - 1 not in self.boundary_matrices or k not in self.boundary_matrices:
            return True
        d_prev = self.boundary_matrices[k - 1]
        d_curr = self.boundary_matrices[k]
        comp = dot(d_prev, d_curr, semiring=semiring)
        return len(comp) == 0

    def hodge_laplacian(self, k: int) -> SparseMatrix:
        """
        Compute the k-th Hodge-Laplacian L_k = D_{k+1} D_{k+1}^T + D_k^T D_k.
        """
        ...
```

---

## Backwards Compatibility

This proposal extends `algebrax.analysis` and does not break existing functions (`gradient`, `laplacian`, `forman_ricci_curvature`).

---

## Deliverables

1. **Core Implementation**: `SparseChainComplex` added to `src/algebrax/analysis.py`.
2. **Unit Tests**: Added test cases in `tests/algebrax/test_analysis.py` (verifying nilpotency $D_0 \circ D_1 = \mathbf{0}$ and Hodge-Laplacian $\Delta_k$).

---

## Change Log

| Date | Author | Description |
|:---|:---|:---|
| 2026-08-01 | Eran Rivlis & Antigravity | Initial Foundational EP created. |
