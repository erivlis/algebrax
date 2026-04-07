# Boolean Semiring (Reachability)

The **Boolean Semiring** uses $(\lor, \land)$. It answers "Is there a path?" without counting them.
Matrix multiplication yields the **Transitive Closure** (Reachability).

*   **Add**: $\lor$ (OR)
*   **Mul**: $\land$ (AND)

<!-- name: test_boolean_semiring -->

```python linenums="1"
from algebrax.semiring import BooleanSemiring
from algebrax.matrix import dot, power

# Graph Connectivity
# 0 -> 1
# 1 -> 2
# 3 -> 4 (Disconnected component)
graph = {
    0: {1: True},
    1: {2: True},
    3: {4: True}
}

semiring = BooleanSemiring()

# Reachability in exactly 2 steps
step2 = dot(graph, graph, semiring=semiring)
print(f"0 -> 2 reachable in 2 steps? {step2.get(0, {}).get(2, False)}")
# output: True

# Full Transitive Closure (Reachability)
# For a graph with N nodes, closure is (I + A)^N
# Or just sum of powers.
# Let's check if 0 can reach 2 eventually.
# We use power() which does binary exponentiation.
# For N=5, power 5 covers all paths <= 5 length.

# Add self-loops (Identity) to allow "staying" at a node
# This makes A^k include all paths of length <= k
n_nodes = 5
for i in range(n_nodes):
    if i not in graph: graph[i] = {}
    graph[i][i] = True

closure = power(graph, n_nodes, semiring=semiring)

print(f"0 -> 2 reachable? {closure.get(0, {}).get(2, False)}")
print(f"0 -> 4 reachable? {closure.get(0, {}).get(4, False)}")
# output: True
# output: False
```
