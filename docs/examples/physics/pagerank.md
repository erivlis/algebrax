# PageRank (Algebraic)

**PageRank** is the stationary distribution of a random walk on a graph.
Algebraically, it is the principal eigenvector of the transition matrix.

We can compute it using **Power Iteration** (repeated matrix-vector multiplication).

$$v_{t+1} = \alpha M v_t + (1-\alpha) \frac{1}{N} \mathbf{1}$$

Where:
*   $M$ is the column-stochastic transition matrix.
*   $\alpha$ is the damping factor (usually 0.85).

<!-- name: test_pagerank -->

```python linenums="1"
from algebrax.semiring import StandardSemiring
from algebrax.matrix import dot

def pagerank(graph, alpha=0.85, iterations=20):
    # 1. Convert Adjacency to Stochastic Matrix M
    # Each column must sum to 1.
    # Since our matrix is row-based (dict[row][col]), we normalize rows
    # and then multiply v * M (row vector * matrix).
    
    M = {}
    nodes = set(graph.keys())
    for u, neighbors in graph.items():
        nodes.update(neighbors.keys())
        degree = len(neighbors)
        if degree > 0:
            M[u] = {v: 1.0 / degree for v in neighbors}
        else:
            # Dangling node (sink): distribute to everyone (or self)
            # Simplified: stay put
            M[u] = {u: 1.0}
            
    all_nodes = sorted(list(nodes))
    N = len(all_nodes)
    
    # 2. Initialize Rank Vector (Uniform)
    v = {node: 1.0 / N for node in all_nodes}
    
    # 3. Power Iteration
    semiring = StandardSemiring()
    
    for _ in range(iterations):
        # v_new = v * M
        # We treat v as a 1xN matrix for the library
        v_matrix = {0: v}
        res_matrix = dot(v_matrix, M, semiring=semiring)
        v_next_raw = res_matrix.get(0, {})
        
        # Apply Damping Factor
        # v = alpha * (v * M) + (1-alpha) / N
        v_next = {}
        teleport = (1 - alpha) / N
        
        for node in all_nodes:
            val = v_next_raw.get(node, 0.0)
            v_next[node] = alpha * val + teleport
            
        v = v_next
        
    return v

# Web Graph
# A -> B, C
# B -> C
# C -> A
web = {
    'A': {'B': 1, 'C': 1},
    'B': {'C': 1},
    'C': {'A': 1}
}

ranks = pagerank(web)
# Sort by rank
sorted_ranks = sorted(ranks.items(), key=lambda x: x[1], reverse=True)

print("PageRank:")
for node, rank in sorted_ranks:
    print(f"{node}: {rank:.4f}")
```
