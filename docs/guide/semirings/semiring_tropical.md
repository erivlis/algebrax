---
title: Tropical Semiring
---

# Tropical Semiring (Shortest Path)

The **Tropical Semiring** uses $(\min, +)$.

Matrix multiplication becomes the shortest path algorithm.


<!-- name: test_tropical_semiring -->

```python linenums="1"
from algebrax.semiring import TropicalSemiring
from algebrax.matrix import dot

# Graph Adjacency Matrix (Weights = Costs)
# 0 -> 1 (cost 2)
# 1 -> 2 (cost 3)
# 0 -> 2 (cost 10)
graph = {
    0: {1: 2.0, 2: 10.0},
    1: {2: 3.0}
}

# Shortest path of length 2
# path(0->2) = min(
#   cost(0->1) + cost(1->2),  # 2 + 3 = 5
#   cost(0->2) + cost(2->2)   # 10 + inf = inf
# )
paths_len_2 = dot(graph, graph, semiring=TropicalSemiring())
print(paths_len_2[0][2])
# output: 5.0
```
