# Provenance Semiring (History Tracking)

The **Provenance Semiring** ($N[X]$) tracks *which* facts contributed to a result and *how many times*.
Values are polynomials where variables represent edges or facts.

<!-- name: test_provenance_semiring -->

```python linenums="1"
from algebrax.semiring import ProvenanceSemiring
from algebrax.matrix import dot

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
paths_len_2 = dot(graph, graph, semiring=ProvenanceSemiring())

print(paths_len_2[0][2])
# output: {('x', 'y'): 1}
```
