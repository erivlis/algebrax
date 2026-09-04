---
title: Optimization & Path Semirings
description: Tropical, Arctic, Viterbi, Reliability, Bottleneck, and MinTimes semirings in AlgebraX.
---

# Optimization Semirings (`algebrax.semiring.optimization`)

Optimization semirings replace standard addition with extremum selection ($\\min$ or $\\max$), transforming
linear algebraic matrix multiplication into dynamic programming, shortest-path, and bottleneck algorithms.

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

---

# Viterbi Algorithm (Hidden Markov Models)

The **Viterbi Algorithm** finds the most likely sequence of hidden states in a Hidden Markov Model (HMM). Algebraically,
this is matrix multiplication over the **Max-Product Semiring** $(\max, \times)$.

* **Add**: $\max$ (Select the best path).
* **Mul**: $\times$ (Combine probabilities).

<!-- name: test_viterbi_semiring -->

```python linenums="1"
import algebrax as ax

# HMM State Transition (Probability of A->B)
# Healthy (H), Fever (F)
transitions = {
    'H': {'H': 0.7, 'F': 0.3},
    'F': {'H': 0.4, 'F': 0.6}
}

# Emission Probabilities (State -> Observation)
# Normal (N), Cold (C), Dizzy (D)
emissions = {
    'H': {'N': 0.5, 'C': 0.4, 'D': 0.1},
    'F': {'N': 0.1, 'C': 0.3, 'D': 0.6}
}

# Initial State Distribution
start = {'H': 0.6, 'F': 0.4}

# Observation Sequence: Normal -> Cold -> Dizzy
obs_seq = ['N', 'C', 'D']

# Viterbi Step
# Current State Probabilities
current_probs = start

semiring = ax.semiring.ViterbiSemiring()

for obs in obs_seq:
    # 1. Emission: Multiply current state prob by emission prob
    # This is a diagonal matrix multiplication or element-wise product
    after_emission = {}
    for state, prob in current_probs.items():
        p_emit = emissions[state].get(obs, 0.0)
        after_emission[state] = semiring.mul(prob, p_emit)

    # 2. Transition: Propagate to next state (Matrix Vector Mul)
    # next_state = current * transition_matrix
    # We use ax.matrix.dot() but we need to format vectors as matrices for the library
    # or just do it manually for this vector-matrix step.

    # Let's use the library's ax.matrix.dot product.
    # Vector as 1xN matrix: {0: {'H': p1, 'F': p2}}
    vec_matrix = {0: after_emission}

    # Transition matrix needs to be in the right format
    # transitions is already dict-of-dicts

    next_step = ax.matrix.dot(vec_matrix, transitions, semiring=semiring)
    current_probs = next_step[0]

print(f"Final Probabilities: {current_probs}")
# The max value indicates the probability of the most likely path ending in that state.
```

---

# Capacity Bottlenecks & Multiplicative Optimization Semirings

Standard shortest-path routing over the `TropicalSemiring` $(\min, +)$ minimizes additive edge weights (distance, latency). However, network routing, hydraulics, and financial loss propagation often demand optimizing **throughput capacity** or **multiplicative attenuation**.

**AlgebraX** provides two specialized optimization semirings in `algebrax.semiring`:

1. **`BottleneckSemiring`**: $(\mathbb{R} \cup \{\pm\infty\}, \max, \min, -\infty, \infty)$ for the **Widest Path Problem** (maximum bottleneck bandwidth).
2. **`MinTimesSemiring`**: $(\mathbb{R}_{\ge 0} \cup \{\infty\}, \min, \cdot, \infty, 1)$ for **Multiplicative Path Penalties** and loss factor minimization.

---

## 1. BottleneckSemiring: The Max-Min Capacity Algebra

In IP packet routing and fluid networks, the effective bandwidth of a path is determined by its narrowest bottleneck link:

$$\text{Capacity}(\pi) = \min_{e \in \pi} c(e)$$

To find the path that maximizes this bottleneck capacity:

$$\begin{aligned}
a \oplus b &= \max(a, b) \quad \text{(Pick the wider alternative path)} \\
a \otimes b &= \min(a, b) \quad \text{(Bottleneck throughput along a serial pipeline)} \\
\mathbf{0} &= -\infty \quad \text{(No capacity / disconnected)} \\
\mathbf{1} &= \infty \quad \text{(Infinite capacity / frictionless connection)}
\end{aligned}$$

### Solving Maximum Bottleneck Paths via Matrix Power
Let $C$ be the capacity matrix of a flow network where $C_{ij}$ is the bandwidth of edge $(i, j)$:

```python
import algebrax as ax

bottleneck = ax.semiring.BottleneckSemiring()

# Network capacity graph:
# 0 -> 1: bandwidth 100 Mbps
# 1 -> 2: bandwidth 20 Mbps
# 0 -> 3: bandwidth 50 Mbps
# 3 -> 2: bandwidth 40 Mbps
adj = {
    0: {1: 100.0, 3: 50.0},
    1: {2: 20.0},
    3: {2: 40.0},
    2: {}
}

# Compute 2-hop maximum bottleneck paths: C^2
paths_2hop = ax.matrix.power(adj, 2, semiring=bottleneck)

# Path 0 -> 1 -> 2 has capacity min(100, 20) = 20
# Path 0 -> 3 -> 2 has capacity min(50, 40) = 40
# Max bottleneck capacity from 0 to 2 = max(20, 40) = 40.0
print("Max Bottleneck Capacity (0 -> 2):", paths_2hop[0][2])  # 40.0
```

---

## 2. MinTimesSemiring: Multiplicative Cost & Attenuation

In optical fiber networks, financial currency exchange fees, and probabilistic error attenuation, link costs multiply rather than add:

$$\text{Total Penalty}(\pi) = \prod_{e \in \pi} w(e)$$

To minimize total multiplicative penalty:

$$\begin{aligned}
a \oplus b &= \min(a, b) \quad \text{(Select path with lowest total penalty factor)} \\
a \otimes b &= a \cdot b \quad \text{(Cascade multiplicative loss factors)} \\
\mathbf{0} &= \infty \quad \text{(Infinite penalty / impassable)} \\
\mathbf{1} &= 1.0 \quad \text{(Zero penalty / neutral multiplier)}
\end{aligned}$$

### Isomorphism to Tropical Semiring
`MinTimesSemiring` on $\mathbb{R}_{>0}$ is isomorphic to `TropicalSemiring` $(\mathbb{R}, \min, +)$ under the bijective natural logarithm transformation $\psi(x) = \ln(x)$:

$$\ln(\min(a, b)) = \min(\ln a, \ln b), \qquad \ln(a \cdot b) = \ln a + \ln b$$

### Python Example
```python
import algebrax as ax

min_times = ax.semiring.MinTimesSemiring()

# Multiplicative cost graph:
# 0 -> 1: factor 1.2, 1 -> 2: factor 1.5 (total = 1.2 * 1.5 = 1.80)
# 0 -> 3: factor 2.0, 3 -> 2: factor 0.8 (total = 2.0 * 0.8 = 1.60)
adj_mult = {
    0: {1: 1.2, 3: 2.0},
    1: {2: 1.5},
    3: {2: 0.8},
    2: {}
}

res = ax.matrix.power(adj_mult, 2, semiring=min_times)
print("Optimal Multiplicative Factor (0 -> 2):", res[0][2])  # 1.60
```

---

## Related Recipes & Applications

* [Urban Traffic Resilience](../../recipes.md) — Shortest-path routing via `TropicalSemiring`.
* [Sensor Network Reliability](../../recipes.md) — Multi-hop link survival via `ViterbiSemiring`.
* [Quant Trading & Portfolio Filtering](../../recipes.md) — Maximum cumulative yield selection via `ArcticSemiring`.
