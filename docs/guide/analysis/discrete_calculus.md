---
title: Discrete Calculus & Differential Geometry
description: Forman-Ricci curvature, gradient, divergence, graph Laplacian diffusion, and kernel metrics.
---

# Discrete Calculus & Differential Geometry (`algebrax.analysis`)

`algebrax.analysis` provides discrete exterior calculus operators on graphs and cellular complexes:

1. **Forman-Ricci Curvature (`forman_ricci_curvature`)**: Evaluates geometric Ricci curvature on network edges.
2. **Coboundary Gradient (`gradient`)**: Discrete exterior derivative $d_0 f(i, j) = f(j) - f(i)$.
3. **Discrete Divergence (`divergence`)**: Adjoint boundary codifferential measuring net nodal flux.
4. **Sheaf & Graph Laplacian (`laplacian`)**: Diffusion operator $L = \text{div}(\text{grad } f)$.
5. **Gaussian Radial Basis Kernel (`gaussian_kernel`)**: Continuous geometric embedding.

## Usage Example

```python
import algebrax as ax

graph = {
    0: {1: 1.0, 2: 1.0},
    1: {0: 1.0, 2: 1.0, 3: 1.0},
    2: {0: 1.0, 1: 1.0, 3: 1.0},
    3: {1: 1.0, 2: 1.0},
}

# Compute Forman-Ricci edge curvature
curvature = ax.analysis.forman_ricci_curvature(graph)
print("Edge Curvatures:", curvature)

# Discrete scalar field diffusion
states = {0: 10.0, 1: 20.0, 2: 30.0, 3: 40.0}
l_diff = ax.analysis.laplacian(states, graph)
print("Laplacian Diffusion Flux:", l_diff)
```

## Related Recipes & Applications

* [Urban Traffic Resilience](../../recipes.md) — Highway choke-point detection via `forman_ricci_curvature`.
* [Sheaf Cohomology Consensus](../../recipes.md) — Multi-robot convergence via `laplacian` diffusion.
