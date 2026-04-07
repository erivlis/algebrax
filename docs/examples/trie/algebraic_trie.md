# Algebraic Trie

The `AlgebraicTrie` is a generalization of a Trie (Prefix Tree) that behaves as a Sparse Tensor over a Semiring.

<!-- name: test_algebraic_trie -->

```python linenums="1"
from algebrax.trie import AlgebraicTrie
from algebrax.semiring import StandardSemiring

# Create a Trie that sums values (Standard Semiring)
trie = AlgebraicTrie(StandardSemiring)

# Add paths
trie.add(["home", "user", "docs"], 1)
trie.add(["home", "user", "pics"], 1)
trie.add(["home", "bin"], 1)

# Contract (Sum) over a prefix
# Sum of all paths starting with "home/user"
count = trie.contract(["home", "user"])
print(count)
# output: 2.0
```
