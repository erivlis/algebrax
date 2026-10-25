---
title: Persistent Homology & Barcodes
description: Multi-scale simplicial filtrations, persistent homology and cohomology barcodes, Betti curves, persistence entropy, and bottleneck distance.
---

# Persistent Homology & Barcodes (`algebrax.topology.persistence`)

While `SimplicialComplex.betti_numbers` evaluates topology at a single static scale, empirical point clouds and weighted networks require **Persistent Homology** across a monotone multiscale filtration:

$$\emptyset = K_0 \subseteq K_1 \subseteq \dots \subseteq K_m = K$$

`algebrax.topology.persistence` tracks the birth threshold $b_i$ and death threshold $d_j$ of every $k$-dimensional topological feature across the filtration, summarizing multiscale topology as a barcode of half-open intervals $[b_i, d_j)$.

---

## Simplicial Filtrations (`FilteredSimplicialComplex`)

`FilteredSimplicialComplex` associates each simplex $\sigma \in K$ with a filtration birth threshold $f(\sigma) \in \mathbb{R}$ satisfying subcomplex monotonicity ($\tau \subseteq \sigma \implies f(\tau) \le f(\sigma)$):

1. **`from_vietoris_rips(distance_matrix, max_dim=2, max_edge_length=inf)`**: Constructs the Vietoris–Rips clique filtration from a sparse pairwise distance matrix where:
   $$f(\sigma) = \max_{u, v \in \sigma} d(u, v)$$
2. **`from_lower_star(complex, vertex_values)`**: Constructs the sublevel-set lower-star filtration of a scalar vertex function $h: V \to \mathbb{R}$ where:
   $$f(\sigma) = \max_{v \in \sigma} h(v)$$

---

## Persistent Homology & Dual Persistent Cohomology

AlgebraX provides both primal and dual persistence reduction algorithms over $\mathbb{Z}_2$:

- **`persistent_homology`**: Reduces the filtered boundary matrix $\partial$ using the **Chen–Kerber clearing (twist) optimization** (processing dimensions top-down so pivot rows of $(k+1)$-boundaries immediately clear $k$-cycle columns in $O(1)$).
- **`persistent_cohomology`**: Implements the **De Silva–Morozov–Vejdemo-Johansson dual cocycle reduction** on $d = \partial^\top \pmod 2$. By Universal Coefficient Duality, it yields the exact same `list[PersistenceInterval]` barcode as `persistent_homology` while additionally returning explicit $\mathbb{Z}_2$ **cocycle representatives** (`dict[PersistenceInterval, set[tuple[int, ...]]]`) for circular coordinates and cohomology ring analysis.

```python
import math
import algebrax as ax

# 4 points on a unit square: side length 1.0, diagonals sqrt(2)
s2 = math.sqrt(2.0)
dist_matrix = {
    0: {1: 1.0, 3: 1.0, 2: s2},
    1: {0: 1.0, 2: 1.0, 3: s2},
    2: {1: 1.0, 3: 1.0, 0: s2},
    3: {0: 1.0, 2: 1.0, 1: s2},
}

# 1. Build Vietoris-Rips filtration
fsc = ax.topology.FilteredSimplicialComplex.from_vietoris_rips(dist_matrix, max_dim=2)

# 2. Compute persistent homology barcode
intervals = fsc.persistent_homology(max_k=1)
h1_bars = [iv for iv in intervals if iv.dimension == 1]
print(h1_bars[0])
# PersistenceInterval(dimension=1, birth=1.0, death=1.4142135623730951, ...)

# 3. Compute dual persistent cohomology and inspect representative Z_2 1-cocycles
cohom_bars, cocycles = fsc.persistent_cohomology(max_k=1)
assert cohom_bars == intervals
```

---

## Barcode Summaries & Bottleneck Distance

To compare persistence diagrams and feed topological summaries into downstream analysis:

- **`betti_curve(intervals, thresholds, dimension=None)`**: Evaluates multi-scale Betti numbers $\beta_k(t) = |\{[b, d) \mid b \le t < d\}|$ at each threshold $t$.
- **`persistence_entropy(intervals, dimension=None)`**: Computes the Shannon entropy $H = -\sum_i p_i \ln p_i$ of normalized finite interval lifetimes $p_i = (d_i - b_i) / \sum_j (d_j - b_j)$.
- **`bottleneck_distance(diagram_a, diagram_b, dimension=None)`**: Computes the exact bottleneck metric $d_B(D_1, D_2) = \inf_\gamma \sup_{x \in D_1} \|x - \gamma(x)\|_\infty$ via binary search over candidate critical distances paired with Hopcroft–Karp bipartite matching ($O(n^{2.5} \log n)$).

```python
from algebrax.topology import betti_curve, bottleneck_distance, persistence_entropy

curve_b1 = betti_curve(intervals, thresholds=[0.5, 1.2, 1.6], dimension=1)
print('Betti-1 curve:', curve_b1)  # [0, 1, 0]

entropy = persistence_entropy(intervals, dimension=0)
print('H_0 Persistence Entropy:', entropy)

# Bottleneck stability under small metric perturbation
dist = bottleneck_distance(intervals, cohom_bars, dimension=1)
assert dist == 0.0
```

---

## Related Sections & Proposals

* [`EP-0162`: Persistent Homology, Simplicial Filtrations & Topological Barcodes](../../proposals/EP-0162-persistent-homology-and-topological-barcodes.md)
* [`EP-0165`: Unified Topology Namespace, Cochain Ring Products & Persistent Cohomology](../../proposals/EP-0165-topology-namespace-and-cohomology-ring.md)
