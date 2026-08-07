---
title: Tropical Semiring
description: Tropical Semiring for shortest path algorithms.
---

# Tropical Semiring (Shortest Path)

The **Tropical Semiring** uses $(\min, +)$.

Matrix multiplication becomes the shortest path algorithm.


<!-- name: test_tropical_semiring -->

```python linenums="1"
import algebrax as ax

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
paths_len_2 = ax.matrix.dot(graph, graph, semiring=ax.semiring.TropicalSemiring())
print(paths_len_2[0][2])
# output: 5.0
```
