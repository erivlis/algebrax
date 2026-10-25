---
title: Simplicial Complexes & Betti Numbers
description: Topological boundary operators, boundary nilpotency, and persistent Betti numbers.
---

# Simplicial Complexes (`algebrax.homology.SimplicialComplex`)

`algebrax.homology` computes topological invariants, boundary operators ($D_k$), and Betti numbers ($\beta_k$)
over abstract simplicial complexes.

## Theoretical Foundations

1. **Boundary Operator ($D_k$)**: Maps each $k$-simplex to its alternating sum of $(k-1)$-faces:
   $$D_k([v_0, \dots, v_k]) = \sum_{i=0}^k (-1)^i [v_0, \dots, \hat{v}_i, \dots, v_k]$$
2. **Homological Nilpotency**: The composition of consecutive boundaries is identically zero:
   $$D_{k-1} \circ D_k = 0$$
3. **Betti Numbers ($\beta_k$)**: The dimension of the $k$-th homology group $H_k = \ker(D_k) / \text{im}(D_{k+1})$:
   $$\beta_k = \dim(\ker D_k) - \text{rank}(D_{k+1})$$

## Usage Example

```python
import algebrax as ax

# Construct hollow circle S^1
edges = [(0, 1), (1, 2), (2, 3), (0, 3)]
sc = ax.homology.SimplicialComplex(edges)

# Verify nilpotency
assert sc.verify_nilpotency(k=1)

# Compute Betti numbers
betti = sc.betti_numbers(max_k=1)
print('Betti numbers:', betti)
# beta_0 = 1 (1 connected component), beta_1 = 1 (1 topological loop)
```

## Persistent Homology, Filtrations & Topological Barcodes

While `SimplicialComplex.betti_numbers` evaluates homology at a single static scale, empirical point clouds and weighted networks require **Persistent Homology** across a multiscale filtration $\emptyset = K_0 \subseteq K_1 \subseteq \dots \subseteq K_m = K$.

`FilteredSimplicialComplex` associates each simplex $\sigma \in K$ with a filtration birth threshold $f(\sigma) \in \mathbb{R}$ satisfying subcomplex monotonicity ($\tau \subseteq \sigma \implies f(\tau) \le f(\sigma)$) and reduces the filtered boundary matrix over $\mathbb{Z}_2$ using the Chen–Kerber clearing (twist) optimization:

```python
import math
import algebrax as ax

# 4 points on a unit square: side length 1.0, diagonal sqrt(2)
s2 = math.sqrt(2.0)
dist_matrix = {
    0: {1: 1.0, 3: 1.0, 2: s2},
    1: {0: 1.0, 2: 1.0, 3: s2},
    2: {1: 1.0, 3: 1.0, 0: s2},
    3: {0: 1.0, 2: 1.0, 1: s2},
}

# Build Vietoris-Rips filtration and compute persistent homology
fsc = ax.homology.FilteredSimplicialComplex.from_vietoris_rips(dist_matrix, max_dim=2)
intervals = fsc.persistent_homology(max_k=1)

# Extract 1D loop intervals [birth, death)
h1_bars = [iv for iv in intervals if iv.dimension == 1]
print(h1_bars[0])  # PersistenceInterval(dimension=1, birth=1.0, death=1.4142..., ...)

# Evaluate multiscale Betti curves, persistence entropy, and bottleneck distance
curve_b1 = ax.homology.betti_curve(intervals, thresholds=[0.5, 1.2, 1.6], dimension=1)
entropy = ax.homology.persistence_entropy(intervals)

# Or compute dual persistent cohomology along with representative Z_2 cocycles
cohom_bars, cocycles = fsc.persistent_cohomology(max_k=1)
```

## Cochain Ring Products (`cup_product` & `cap_product`)

Under the unified `algebrax.topology` namespace (`homology`, `cohomology`, `persistence`, `dec`, `sheaf`), discrete $k$-forms (`Cochain`) form a **graded associative ring** via the Alexander–Whitney **cup product** ($\smile$, or `^`) and pair with homology chains via the **cap product** ($\frown$):

$$(\alpha \smile \beta)(v_0, \dots, v_{p+q}) = \alpha(v_0, \dots, v_p) \otimes_{\mathcal{S}} \beta(v_p, \dots, v_{p+q})$$

$$d(\alpha \smile \beta) = (d\alpha) \smile \beta + (-1)^p \, \alpha \smile (d\beta), \qquad \langle \psi, c \frown \phi \rangle = \langle \phi \smile \psi, c \rangle$$

```python
import algebrax as ax

tet = ax.topology.SimplicialComplex([(0, 1, 2, 3)])
alpha = ax.topology.Cochain({(0, 1): 2.0, (1, 2): 3.0})
beta = ax.topology.Cochain({(1, 2): 4.0, (2, 3): -1.0})

# Cup product (via ^ operator, .cup(), or cup_product)
two_form = alpha ^ beta  # Cochain({(0, 1, 2): 8.0, (1, 2, 3): -3.0}, degree=2)

# Cap product contracting a 2-chain with a 1-cochain into a 1-chain
chain_2 = {(0, 1, 2): 5.0}
one_chain = ax.topology.cap_product(chain_2, alpha)  # {(1, 2): 10.0}
```

## Related Recipes & Applications

* [Topological Homology & Betti Barcodes](../../recipes.md) — Simplicial verification and Betti barcodes.
* [Topological Data Analysis](../../recipes.md) — Persistent homology over point clouds.


