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

## Parameterized Semirings & Hash-Join Contraction

`einsum`, `outer_product`, and `dot` normalize live `Semiring` instances, classes, and catalog names, preserving exact parameters on the returned `AlgebraicTrie`. Multi-operand contractions execute left-to-right **hash-join indexing** on shared subscripts with eager projection of dead indices (scaling linearly $O(N)$ on diagonal contractions like `'ii,ii,ii->i'` rather than $O(N^3)$), and `dot` safely returns an empty `AlgebraicTrie` on empty operands:

```python
from algebrax.algebra import ModularField
from algebrax.semiring import GaloisField, TropicalSemiring
from algebrax.tensor import einsum, outer_product
from algebrax.trie import AlgebraicTrie

# 1. Exact modular contraction over GF(7) (preserves p=7 on output trie)
f7 = ModularField(7)
u = AlgebraicTrie(f7)
u[(0,)] = 3
u[(1,)] = 4
outer_f7 = outer_product(u, u, semiring=f7)
assert outer_f7.semiring.p == 7 and outer_f7[(0, 0)] == 2  # 9 mod 7

# 2. Contraction over GaloisField GF(3^2) = F_3[x]/(x^2 + 1)
gf9 = GaloisField(3, [1, 0, 1])
v = AlgebraicTrie(gf9)
v[(0,)] = {1: 1}  # x
v[(1,)] = gf9.one
assert len(einsum('i,i->', v, v, semiring=gf9)) == 0  # x^2 + 1 = 0 pruned

# 3. Tropical min-plus shortest two-hop paths
trop = TropicalSemiring()
edges = {(0, 1): 2.0, (1, 2): 3.0, (0, 2): 10.0}
two_hop = einsum('ij,jk->ik', edges, edges, semiring=trop)
assert two_hop[(0, 2)] == 5.0
```

## Related Recipes & Applications

* [Schwarzschild Black Hole Spacetime](../../recipes.md) — Spacetime metric tensor contraction.
* [Sparse Tensor Einsum](../../recipes.md) — High-dimensional contractions across semirings.

