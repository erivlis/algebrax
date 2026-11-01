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

# Define 2D sparse tensors with tuple keys (row, col)
A = {(0, 0): 1.0, (0, 1): 2.0, (1, 0): 3.0, (1, 1): 4.0}
B = {(0, 0): 5.0, (0, 1): 6.0, (1, 0): 7.0, (1, 1): 8.0}

# 1. Matrix multiplication: C_ik = sum_j A_ij * B_jk
C = ax.tensor.einsum('ij,jk->ik', A, B, semiring=ax.semiring.StandardSemiring())
assert dict(C) == {(0, 0): 19.0, (0, 1): 22.0, (1, 0): 43.0, (1, 1): 50.0}

# 2. Trace: Tr(A) = sum_i A_ii
tr = ax.tensor.einsum('ii->', A)
assert dict(tr) == {(): 5.0}  # A_00 + A_11 = 1.0 + 4.0 = 5.0

# 3. Hadamard product: C_ij = A_ij * B_ij
hadamard = ax.tensor.einsum('ij,ij->ij', A, B)
assert dict(hadamard) == {(0, 0): 5.0, (0, 1): 12.0, (1, 0): 21.0, (1, 1): 32.0}
```

## Related Recipes & Applications

* [Schwarzschild Black Hole Spacetime](../../recipes.md) — Spacetime metric tensor contraction.
* [Sparse Tensor Einsum](../../recipes.md) — High-dimensional contractions across semirings.
