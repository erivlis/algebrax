---
title: Tensor Einsum
description: Einstein summation over arbitrary semirings in AlgebraX.
---

# Tensor Einsum (`algebrax.tensor.einsum`)

`algebrax.tensor.einsum` executes generalized Einstein summation contractions over sparse dictionary tensors
and `AlgebraicTrie` structures under arbitrary semirings.

## Syntax & Semantics

```python
import algebrax as ax

# Matrix multiplication: C_ik = sum_j A_ij * B_jk
C = ax.tensor.einsum('ij,jk->ik', A, B, semiring=ax.semiring.StandardSemiring())

# Trace: Tr(A) = sum_i A_ii
tr = ax.tensor.einsum('ii->', A)

# Hadamard product: C_ij = A_ij * B_ij
hadamard = ax.tensor.einsum('ij,ij->ij', A, B)
```

## Related Recipes & Applications

* [Schwarzschild Black Hole Spacetime](../../recipes.md) — Spacetime metric tensor contraction.
* [Sparse Tensor Einsum](../../recipes.md) — High-dimensional contractions across semirings.
