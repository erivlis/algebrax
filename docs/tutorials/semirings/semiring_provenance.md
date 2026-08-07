---
title: Provenance Semiring
description: Provenance Semiring for tracking which facts contributed to a result and how many times.
---

# Provenance Semiring (History Tracking)

The **Provenance Semiring** ($\mathbb{N}[X]$) is a specialized subclass of the [Monoid Algebra Semiring](semiring_monoid_algebra.md) that tracks *which* facts contributed to a result and *how many times*.
Values are multivariate polynomials represented as mappings from sorted variable tuples (monomials) to occurrence counts in $\mathbb{N}$.

<!-- name: test_provenance_semiring -->

```python linenums="1"
import algebrax as ax

# Graph with labeled edges
# 0 -> 1 (label 'x')
# 1 -> 2 (label 'y')
# 0 -> 2 (label 'z')
graph = {
    0: {1: {('x',): 1}, 2: {('z',): 1}},
    1: {2: {('y',): 1}}
}

# Paths of length 2
# 0->1->2: x * y = xy
# 0->2: (length 1, not in result)
paths_len_2 = ax.matrix.dot(graph, graph, semiring=ax.semiring.ProvenanceSemiring())

print(paths_len_2[0][2])
# output: {('x', 'y'): 1}
```
