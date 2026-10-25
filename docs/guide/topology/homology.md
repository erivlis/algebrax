---
title: Homology & Chain Complexes
description: Simplicial complexes, sparse chain complexes, boundary nilpotency, and static Betti numbers.
---

# Homology & Chain Complexes (`algebrax.topology.homology`)

`algebrax.topology.homology` (re-exported at the top level of `algebrax.topology` and `algebrax.homology`) formalizes sequence spaces $C_k(K; R)$ and sparse boundary operators $\partial_k: C_k \to C_{k-1}$ over abstract simplicial complexes and general chain complexes.

---

## Theoretical Foundations

1. **Boundary Operator ($\partial_k$)**: Maps each oriented $k$-simplex $[v_0, \dots, v_k]$ to the alternating sum of its $(k-1)$-faces:
   $$\partial_k([v_0, \dots, v_k]) = \sum_{i=0}^k (-1)^i [v_0, \dots, \hat{v}_i, \dots, v_k]$$
2. **Homological Nilpotency**: The boundary of a boundary is identically zero:
   $$\partial_{k-1} \circ \partial_k = \mathbf{0}$$
3. **Betti Numbers ($\beta_k$)**: The rank of the $k$-th homology group $H_k(K) = \ker(\partial_k) / \operatorname{im}(\partial_{k+1})$ counts $k$-dimensional topological holes:
   - $\beta_0$: Connected components
   - $\beta_1$: 1D circular loops / tunnels
   - $\beta_2$: 2D enclosed voids / cavities
   $$\beta_k = \dim(\ker \partial_k) - \operatorname{rank}(\partial_{k+1})$$

---

## Simplicial Complexes (`SimplicialComplex`)

`SimplicialComplex` automatically enforces downward face closure ($\sigma \in K, \tau \subseteq \sigma \implies \tau \in K$), canonicalizes vertex ordering, constructs sparse boundary matrices $\partial_k$, and computes Betti numbers:

```python
import algebrax as ax

# 1. 1D Hollow Circle Topology (S^1)
ring_edges = [(0, 1), (1, 2), (2, 3), (0, 3)]
sc_ring = ax.topology.SimplicialComplex(ring_edges)

# Verify homological nilpotency: d_0 o d_1 == 0
assert sc_ring.verify_nilpotency(k=1)

# Compute Betti numbers
betti_ring = sc_ring.betti_numbers(max_k=1)
print(f'1D Ring Betti Numbers: beta_0={betti_ring[0]}, beta_1={betti_ring[1]}')
# Output: 1D Ring Betti Numbers: beta_0=1, beta_1=1

# 2. 3D Solid Tetrahedron Topology (contractible)
sc_tet = ax.topology.SimplicialComplex([(0, 1, 2, 3)])
betti_tet = sc_tet.betti_numbers(max_k=2)
print(f'Solid Tetrahedron Betti Numbers: {betti_tet}')
# Output: {0: 1, 1: 0, 2: 0}
```

---

## General Sparse Chain Complexes (`SparseChainComplex`)

When working with non-simplicial cell complexes (such as cubical complexes, CW complexes, or algebraic chain complexes), construct `SparseChainComplex` directly from a dictionary of boundary matrices `{k: D_k}`:

```python
from algebrax.topology import SparseChainComplex

# Boundary matrices for a 1D cycle with 3 vertices and 3 edges
d1 = {
    (0,): {(0, 1): -1.0, (0, 2): -1.0},
    (1,): {(0, 1): 1.0, (1, 2): -1.0},
    (2,): {(0, 2): 1.0, (1, 2): 1.0},
}
cc = SparseChainComplex({1: d1})
assert cc.verify_nilpotency(k=1)
print('Betti numbers:', cc.betti_numbers(max_k=1))
# Output: {0: 1, 1: 1}
```

---

## Related Sections & Recipes

* [Cohomology & Ring Products](cohomology.md) — Dual cochains, coboundary operators, and Alexander–Whitney cup/cap products.
* [Persistent Homology & Barcodes](persistence.md) — Multi-scale filtrations, barcodes, and bottleneck stability.
* [Topological Homology & Betti Barcodes](../../recipes.md) — Executable scripts and topological verification recipes.
