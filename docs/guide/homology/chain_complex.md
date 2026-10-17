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

---

## Cellular Sheaves & Sheaf Laplacians (`CellularSheaf`)

A **Cellular Sheaf** $\mathcal{F}$ over a 1-dimensional cell complex (graph) $G = (V, E)$ generalizes scalar graph Laplacians to heterogeneous vector stalks with linear restriction maps. Every vertex $v \in V$ is assigned a vector stalk $\mathcal{F}(v) = \mathbb{R}^{d_v}$, every edge $e \in E$ is assigned an edge stalk $\mathcal{F}(e) = \mathbb{R}^{d_e}$, and each incident vertex-edge pair has a linear restriction map:

$$\rho_{v \trianglelefteq e}: \mathcal{F}(v) \to \mathcal{F}(e)$$

### Sheaf Coboundary Operator ($\delta_{\mathcal{F}}$)

The 0-th sheaf coboundary operator $\delta_{\mathcal{F}}: C^0(G; \mathcal{F}) \to C^1(G; \mathcal{F})$ measures local disagreement across edge stalks:

$$(\delta_{\mathcal{F}} x)_{e = (u, v)} = \rho_{v \trianglelefteq e} x_v - \rho_{u \trianglelefteq e} x_u$$

### Sheaf Laplacian ($L_{\mathcal{F}}$) & Dirichlet Energy

The Sheaf Laplacian $L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$ is a symmetric positive semi-definite linear operator indexed natively by product keys `(vertex, dim_idx)`. The associated **Dirichlet Energy** measures total network disagreement:

$$E_{\mathcal{F}}(x) = \frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2 = \frac{1}{2} \langle x, L_{\mathcal{F}} x \rangle \ge 0$$

### Global Sections ($H^0(G; \mathcal{F})$)

A 0-cochain $x \in C^0(G; \mathcal{F})$ is a **global section** if neighbors agree everywhere:

$$\delta_{\mathcal{F}} x = 0 \iff L_{\mathcal{F}} x = 0 \iff x \in H^0(G; \mathcal{F})$$

The dimension of the space of global sections is computed directly via rank-nullity:

$$\dim H^0(G; \mathcal{F}) = \sum_{v \in V} d_v - \operatorname{rank}(\delta_{\mathcal{F}})$$

### Python Example: Cellular Sheaves & Harmonic Extension

```python
import math
from algebrax.analysis import (
    CellularSheaf,
    sheaf_diffusion,
    sheaf_harmonic_extension,
    sheaf_laplacian,
)

# 1. Constant Sheaf: strict generalization of graph Laplacians
graph = {0: {1: 1.0}, 1: {0: 1.0, 2: 2.0}, 2: {1: 2.0}}
constant_sheaf = CellularSheaf.constant(graph, stalk_dim=1)
l_sheaf = sheaf_laplacian(constant_sheaf)
print('Constant Sheaf global sections:', constant_sheaf.global_sections_dimension())  # -> 1

# 2. Orthogonal Connection Sheaf on a 3-cycle (SO(2) rotation frames)
# Flat holonomy: rotation angles sum to 0 -> dim H^0 = 2
rot = lambda theta: [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
ident = [[1.0, 0.0], [0.0, 1.0]]

sheaf_flat = CellularSheaf()
sheaf_flat.add_edge(0, 1, dim=2, rho_u=rot(math.pi / 3), rho_v=ident)
sheaf_flat.add_edge(1, 2, dim=2, rho_u=rot(math.pi / 6), rho_v=ident)
sheaf_flat.add_edge(0, 2, dim=2, rho_u=rot(math.pi / 2), rho_v=ident)
print('Flat bundle dim H^0:', sheaf_flat.global_sections_dimension())  # -> 2

# Frustrated cycle (discrete Mobius bundle): holonomy = -I -> dim H^0 = 0
sheaf_frustrated = CellularSheaf()
sheaf_frustrated.add_edge(0, 1, dim=2, rho_u=ident, rho_v=ident)
sheaf_frustrated.add_edge(1, 2, dim=2, rho_u=ident, rho_v=ident)
sheaf_frustrated.add_edge(0, 2, dim=2, rho_u=rot(math.pi), rho_v=ident)
print('Frustrated bundle dim H^0:', sheaf_frustrated.global_sections_dimension())  # -> 0

# 3. Sheaf Harmonic Extension (Dirichlet Boundary Problem)
path_sheaf = CellularSheaf()
path_sheaf.add_edge(0, 1, dim=1, rho_u=1.0, rho_v=1.0)
path_sheaf.add_edge(1, 2, dim=1, rho_u=1.0, rho_v=1.0)
path_sheaf.add_edge(2, 3, dim=1, rho_u=1.0, rho_v=1.0)

boundary_conditions = {(0, 0): 0.0, (3, 0): 3.0}
harmonic_state = sheaf_harmonic_extension(
    path_sheaf,
    boundary_values=boundary_conditions,
    boundary_vertices={0, 3},
)
print('Harmonic extension:', harmonic_state)
# -> {(0, 0): 0.0, (3, 0): 3.0, (1, 0): 1.0, (2, 0): 2.0}
```
