---
title: Cellular Sheaves & Network Cohomology
description: Cellular sheaves, vector stalks, restriction maps, sheaf Laplacians, global sections, H^1 obstructions, and harmonic extension.
---

# Cellular Sheaves & Network Cohomology (`algebrax.topology.sheaf`)

A **Cellular Sheaf** $\mathcal{F}$ over a 1-dimensional cell complex (graph) $G = (V, E)$ generalizes scalar graph Laplacians to heterogeneous vector stalks with linear restriction maps. Every vertex $v \in V$ is assigned a vector stalk $\mathcal{F}(v) = \mathbb{R}^{d_v}$, every edge $e \in E$ is assigned an edge stalk $\mathcal{F}(e) = \mathbb{R}^{d_e}$, and each incident vertex-edge pair has a linear restriction map:

$$\rho_{v \trianglelefteq e}: \mathcal{F}(v) \to \mathcal{F}(e)$$

---

## Sheaf Coboundary ($\delta_{\mathcal{F}}$) & Sheaf Laplacian ($L_{\mathcal{F}}$)

1. **Sheaf Coboundary Operator ($\delta_{\mathcal{F}}: C^0(G; \mathcal{F}) \to C^1(G; \mathcal{F})$)**:
   Measures local disagreement across edge stalks:
   $$(\delta_{\mathcal{F}} x)_{e = (u, v)} = \rho_{v \trianglelefteq e} x_v - \rho_{u \trianglelefteq e} x_u$$
2. **Sheaf Laplacian ($L_{\mathcal{F}} = \delta_{\mathcal{F}}^\top \delta_{\mathcal{F}}$) & Dirichlet Energy**:
   A symmetric positive semi-definite linear operator indexed by product keys `(vertex, dim_idx)` whose quadratic form measures total network disagreement:
   $$E_{\mathcal{F}}(x) = \frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2 = \frac{1}{2} \langle x, L_{\mathcal{F}} x \rangle \ge 0$$

---

## Sheaf Cohomology ($H^0$, $H^1$) & Euler–Poincaré Characteristic

- **0-th Sheaf Cohomology / Global Sections (`global_sections_dimension`)**:
  A 0-cochain $x \in C^0(G; \mathcal{F})$ is a global section if neighbors agree across every edge ($\delta_{\mathcal{F}} x = 0 \iff L_{\mathcal{F}} x = 0$):
  $$\dim H^0(G; \mathcal{F}) = \dim \ker \delta_{\mathcal{F}} = \sum_{v \in V} d_v - \operatorname{rank}(\delta_{\mathcal{F}})$$
- **1-st Sheaf Cohomology / Obstructions (`first_cohomology_dimension`)**:
  Measures the dimension of edge-stalk obstructions (holonomy / frustration) that cannot be realized as coboundaries of 0-cochains:
  $$\dim H^1(G; \mathcal{F}) = \dim \operatorname{coker} \delta_{\mathcal{F}} = \sum_{e \in E} d_e - \operatorname{rank}(\delta_{\mathcal{F}})$$
- **Euler–Poincaré Characteristic (`euler_characteristic`)**:
  Satisfies the exact topological invariance law independent of the restriction maps $\rho$:
  $$\chi(G; \mathcal{F}) = \dim C^0(G; \mathcal{F}) - \dim C^1(G; \mathcal{F}) = \dim H^0(G; \mathcal{F}) - \dim H^1(G; \mathcal{F})$$

---

## Python Example: Holonomy, Diffusion & Harmonic Extension

```python
import math
from algebrax.topology import (
    CellularSheaf,
    sheaf_diffusion,
    sheaf_harmonic_extension,
    sheaf_laplacian,
)

# 1. Constant Sheaf: strict generalization of graph Laplacians
graph = {0: {1: 1.0}, 1: {0: 1.0, 2: 2.0}, 2: {1: 2.0}}
constant_sheaf = CellularSheaf.constant(graph, stalk_dim=1)
l_sheaf = sheaf_laplacian(constant_sheaf)
print('Constant Sheaf dim H^0:', constant_sheaf.global_sections_dimension())  # -> 1

# 2. Orthogonal Connection Sheaf on a 3-cycle (SO(2) rotation frames)
rot = lambda theta: [[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]]
ident = [[1.0, 0.0], [0.0, 1.0]]

# Flat bundle: rotation angles sum to 0 -> dim H^0 = 2, dim H^1 = 2
sheaf_flat = CellularSheaf()
sheaf_flat.add_edge(0, 1, dim=2, rho_u=rot(math.pi / 3), rho_v=ident)
sheaf_flat.add_edge(1, 2, dim=2, rho_u=rot(math.pi / 6), rho_v=ident)
sheaf_flat.add_edge(0, 2, dim=2, rho_u=rot(math.pi / 2), rho_v=ident)
print('Flat bundle H^0, H^1:', sheaf_flat.global_sections_dimension(), sheaf_flat.first_cohomology_dimension())
# -> 2, 2

# Frustrated cycle (discrete Mobius bundle): holonomy = -I -> dim H^0 = 0, dim H^1 = 0
sheaf_frustrated = CellularSheaf()
sheaf_frustrated.add_edge(0, 1, dim=2, rho_u=ident, rho_v=ident)
sheaf_frustrated.add_edge(1, 2, dim=2, rho_u=ident, rho_v=ident)
sheaf_frustrated.add_edge(0, 2, dim=2, rho_u=rot(math.pi), rho_v=ident)
print(
    'Frustrated bundle H^0, H^1:',
    sheaf_frustrated.global_sections_dimension(),
    sheaf_frustrated.first_cohomology_dimension(),
)
# -> 0, 0
assert sheaf_flat.euler_characteristic() == sheaf_frustrated.euler_characteristic() == 0

# 3. Sheaf Harmonic Extension (Dirichlet Boundary Value Problem)
path_sheaf = CellularSheaf()
path_sheaf.add_edge(0, 1, dim=1, rho_u=1.0, rho_v=1.0)
path_sheaf.add_edge(1, 2, dim=1, rho_u=1.0, rho_v=1.0)
path_sheaf.add_edge(2, 3, dim=1, rho_u=1.0, rho_v=1.0)

harmonic_state = sheaf_harmonic_extension(
    path_sheaf,
    boundary_values={(0, 0): 0.0, (3, 0): 3.0},
    boundary_vertices={0, 3},
)
print('Harmonic extension:', harmonic_state)
# -> {(0, 0): 0.0, (3, 0): 3.0, (1, 0): 1.0, (2, 0): 2.0}
```

---

## Related Sections & Proposals

* [`EP-0161`: Cellular Sheaves, Restriction Maps & Sheaf Laplacians](../../proposals/EP-0161-cellular-sheaves-and-network-laplacians.md)
* [`EP-0165`: Unified Topology Namespace, Cochain Ring Products & Persistent Cohomology](../../proposals/EP-0165-topology-namespace-and-cohomology-ring.md)
