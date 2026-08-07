# Algebraic Trie

The `AlgebraicTrie` is a generalization of a Trie (Prefix Tree) that behaves as a Sparse Tensor over a Semiring.

<!-- name: test_algebraic_trie -->

```python linenums="1"
import algebrax as ax

# Create a Trie that sums values (Standard ax.semiring.Semiring)
trie = ax.trie.AlgebraicTrie(ax.semiring.StandardSemiring)

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
