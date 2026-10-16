---
title: Sparse Chain Complexes & Simplicial Homology
description: Tutorial on SparseChainComplex, nilpotency verification, Hodge-Laplacians, and Betti numbers.
---

# Sparse Chain Complexes & Simplicial Homology

The **`SparseChainComplex`** in `algebrax.homology` and **`SimplicialComplex`** in `algebrax.homology` formalize sequence spaces $C_k$ and sparse boundary operators $D_k: C_k \to C_{k-1}$ enforcing the fundamental nilpotency identity:

$$D_{k-1} \circ D_k = \mathbf{0}$$

---

## Topological Betti Numbers

Betti numbers $\beta_k$ count topological holes:
- $\beta_0$: Number of connected components
- $\beta_1$: Number of 1D circular loops
- $\beta_2$: Number of 2D enclosed voids

$$\beta_k = \dim(\ker D_k) - \text{rank}(D_{k+1})$$

---

## Python Example: Simplicial Complex Betti Numbers

```python
import algebrax as ax

# 1. 1D Hollow Ring Topology (S^1)
ring_edges = [(0, 1), (1, 2), (2, 3), (0, 3)]
sc_ring = ax.homology.SimplicialComplex(ring_edges)

# Verify Nilpotency D0 o D1 == 0
assert sc_ring.verify_nilpotency(k=1)

# Compute Betti Numbers
betti_ring = sc_ring.betti_numbers(max_k=1)
print(f'1D Ring Betti Numbers: beta_0={betti_ring[0]}, beta_1={betti_ring[1]}')
# Output: 1D Ring Betti Numbers: beta_0=1, beta_1=1

# 2. 3D Solid Tetrahedron Topology
sc_tet = ax.homology.SimplicialComplex([(0, 1, 2, 3)])
betti_tet = sc_tet.betti_numbers(max_k=2)
print(f'Solid Tetrahedron Betti Numbers: beta_0={betti_tet[0]}, beta_1={betti_tet[1]}, beta_2={betti_tet[2]}')
# Output: Solid Tetrahedron Betti Numbers: beta_0=1, beta_1=0, beta_2=0
```

---

## Alternating Cochains & Discrete Differential Forms (`Cochain`)

The **`Cochain[K, V]`** carrier in `algebrax.homology` (also exported in `algebrax.analysis`) represents an alternating discrete differential $k$-form $\omega \in C^k(K; R)$ satisfying permutation parity antisymmetry:

$$\omega(v_{\pi(0)}, \dots, v_{\pi(k)}) = \operatorname{sgn}(\pi)\,\omega(v_0, \dots, v_k)$$

`Cochain` implements `Mapping[tuple[K, ...], V]`, making it directly compatible with `SparseVector` operators (`mat_vec`, `inner`, `vec_axpy`) while automatically canonicalizing simplex orientations and annihilating degenerate simplices:

```python
from algebrax.homology import Cochain, SimplicialComplex, coboundary
from algebrax.matrix import mat_vec

# 1-cochain initialized with arbitrary edge orientation
omega = Cochain({(1, 0): 5.0, (1, 2): -3.0})
print(omega[(0, 1)])  # -> -5.0 (canonical orientation)
print(omega[(1, 0)])  # -> +5.0 (reversed orientation flips sign)
print(omega.get((0, 0)))  # -> 0.0 (degenerate simplex vanishes)

# Exterior derivative d_0 via coboundary operator
sc = SimplicialComplex([(0, 1, 2)])
f0 = Cochain.from_nodes({0: 1.0, 1: 4.0, 2: -2.0})
df = Cochain(mat_vec(coboundary(sc, 0), f0), degree=1)
print(df[(0, 1)], df[(1, 2)])  # -> 3.0, -6.0
```
