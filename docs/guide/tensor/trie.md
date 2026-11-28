---
title: Algebraic Trie
description: Generalized prefix trees behaving as sparse tensors over arbitrary semirings.
---

# Algebraic Trie (`algebrax.trie.AlgebraicTrie`)

The `AlgebraicTrie` is a generalization of a Trie (Prefix Tree) that behaves as a Sparse Tensor over a Semiring.

<!-- name: test_algebraic_trie -->

```python linenums="1"
import algebrax as ax

# Create a Trie that sums values (Standard ax.semiring.Semiring)
trie = ax.trie.AlgebraicTrie(ax.semiring.StandardSemiring)

# Add paths
trie.add(['home', 'user', 'docs'], 1)
trie.add(['home', 'user', 'pics'], 1)
trie.add(['home', 'bin'], 1)

# Contract (Sum) over a prefix
# Sum of all paths starting with "home/user"
count = trie.contract(['home', 'user'])
print(count)
# output: 2.0
```

## Parameterized Semirings, $O(1)$ Length & Pickling

`AlgebraicTrie` accepts live parameterized `Semiring` instances (such as `ModularField(7)`, `GaloisField(3, [1, 0, 1])`, `CliffordAlgebra(2, 0, 0)`, or `TropicalSemiring()`), semiring classes, or catalog strings. Live semiring parameters are preserved across `pickle` serialization, `len(trie)` runs in $O(1)$ time, and `add()` prunes entries that cancel to algebraic zero along with any emptied intermediate branches:

```python
import pickle

from algebrax.algebra import ModularField
from algebrax.semiring import GaloisField, TropicalSemiring
from algebrax.trie import AlgebraicTrie

# 1. Exact modular arithmetic over GF(7) with automatic zero cancellation
f7 = ModularField(7)
mod_trie = AlgebraicTrie(f7)
mod_trie.add(('a', 0), 4)
mod_trie.add(('a', 0), 3)  # 4 + 3 == 0 mod 7 -> entry & empty branch pruned
assert len(mod_trie) == 0

# 2. Galois field GF(3^2) = F_3[x]/(x^2 + 1) preserved across pickle
gf9 = GaloisField(3, [1, 0, 1])
gf_trie = AlgebraicTrie(gf9)
gf_trie[('x',)] = {1: 1}
restored = pickle.loads(pickle.dumps(gf_trie))
assert restored.semiring.p == 3 and restored[('x',)] == {1: 1}

# 3. Tropical min-plus prefix aggregation
trop_trie = AlgebraicTrie(TropicalSemiring())
trop_trie.add(('route', 'fast'), 2.5)
trop_trie.add(('route', 'slow'), 9.0)
assert trop_trie.contract(('route',)) == 2.5
```

