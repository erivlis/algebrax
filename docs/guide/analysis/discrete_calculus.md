---
title: Discrete Calculus & Differential Geometry
description: Forman-Ricci curvature, gradient, divergence, graph Laplacian diffusion, and kernel metrics.
---

# Discrete Calculus & Spectral Graph Theory (`algebrax.analysis`)

`algebrax.analysis` provides discrete exterior calculus operators, spectral graph analysis, and network dynamics:

1. **Graph Laplacian Linear Operator (`laplacian_matrix`)**: Constructs combinatorial ($L = D - W$), symmetric
   normalized ($L_{\mathrm{sym}} = D^{-1/2} L D^{-1/2}$), and random-walk normalized ($L_{\mathrm{rw}} = D^{-1} L$)
   operators.
2. **Fiedler Vector & Algebraic Connectivity (`fiedler_vector`, `algebraic_connectivity`)**: Computes the second
   smallest Laplacian eigenvalue $\lambda_2$ and eigenvector $\mathbf{v}_2$ via Rayleigh Quotient Conjugate Gradient
   (RQ-CG).
3. **Spectral Graph Bipartitioning (`spectral_bipartition`)**: Dissects networks along structural Cheeger cutlines using
   sign ($\theta=0$) or balanced median ($\theta = \text{median} (\mathbf{v}_2)$) thresholds.
4. **Laplacian Smoothing & Heat Diffusion (`laplacian_smoothing`)**: Minimizes discrete Dirichlet
   energy $E (\mathbf{u}) = \frac{1}{2} \mathbf{u}^T L \mathbf{u}$ via $S$ Euler diffusion
   contractions $\mathbf{u}^{ (t+1)} = (I - \tau L) \mathbf{u}^{ (t)}$.
5. **Full Eigenspectrum (`laplacian_spectrum`)**: Diagonalizes small-to-medium network Laplacians ($N \le 150$) via
   cyclic Jacobi sweeps.
6. **Forman-Ricci Curvature (`forman_ricci_curvature`)**: Evaluates geometric Ricci curvature on network edges.
7. **Coboundary Gradient (`gradient`)**: Discrete exterior derivative $d_0 f (i, j) = f (j) - f (i)$.
8. **Discrete Divergence (`divergence`)**: Adjoint boundary codifferential measuring net nodal flux.
9. **Field Laplacian Operator (`laplacian`)**: Direct evaluation of the 0-form field
   action $\Delta f = \text{div} (\text{grad } f)$.
10. **Algebraic PageRank (`pagerank`)**: Solves for stationary random walk distributions with teleportation restart.

---

## Spectral Graph Theory & Clustering

### 1. Constructing the Graph Laplacian

```python
import algebrax as ax

# Barbell network: two K3 cliques connected by a bridge edge (2 <-> 3)
graph = {
    0: {1: 1.0, 2: 1.0},
    1: {0: 1.0, 2: 1.0},
    2: {0: 1.0, 1: 1.0, 3: 1.0},
    3: {2: 1.0, 4: 1.0, 5: 1.0},
    4: {3: 1.0, 5: 1.0},
    5: {3: 1.0, 4: 1.0},
}

# Combinatorial Laplacian L = D - W
L = ax.matrix.laplacian_matrix(graph)

# Symmetric normalized Laplacian L_sym = D^{-1/2} L D^{-1/2}
L_sym = ax.matrix.laplacian_matrix(graph, normalized="sym")
```

### 2. Algebraic Connectivity & Cheeger Bipartitioning

The Fiedler eigenvalue $\lambda_2$ quantifies how easily a network can be partitioned into disconnected components.
Cheeger's inequality bounds the optimal conductance $h (G)$:
$$\frac{\lambda_2}{2} \le h (G) \le \sqrt{2 \lambda_2}$$

```python
# Compute Fiedler eigenvalue and vector
lambda_2, fiedler = ax.analysis.fiedler_vector(graph)
print(f"Algebraic Connectivity lambda_2: {lambda_2:.4f}")

# Optimal spectral bipartition
cluster_a, cluster_b, metrics = ax.analysis.spectral_bipartition(graph, method="sign")
print("Cluster A:", cluster_a)
print("Cluster B:", cluster_b)
print("Cut Quality Metrics:", metrics)
# Output:
# Cluster A: {0, 1, 2}, Cluster B: {3, 4, 5}
# cut_size: 1.0, conductance: 0.1428, ratio_cut: 0.6667
```

### 3. Laplacian Smoothing (Heat Diffusion on Signals)

Laplacian smoothing filters spatial high-frequency noise from node signals while preserving global topological features:

```python
# Signal with localized noise
noisy_signal = {0: 10.0, 1: 0.0, 2: 0.0, 3: 10.0, 4: 0.0, 5: 0.0}

# 10 Euler diffusion steps with rate tau=0.1
smoothed_signal = ax.analysis.laplacian_smoothing(noisy_signal, graph, steps=10, tau=0.1)
print("Smoothed Field:", smoothed_signal)
```

---

## Discrete Exterior Calculus & Curvature

```python
# Compute Forman-Ricci edge curvature to detect highway choke points
curvature = ax.analysis.forman_ricci_curvature(graph)
print("Edge Curvatures:", curvature)

# Discrete scalar field diffusion flux (divergence of gradient)
states = {0: 10.0, 1: 20.0, 2: 30.0, 3: 40.0, 4: 20.0, 5: 10.0}
flux = ax.analysis.laplacian(states, graph)
print("Laplacian Diffusion Flux:", flux)
```

---

## Related Recipes & Applications

* [Spectral Graph Clustering & Manifold Smoothing](../../recipes.md#spectral-graph-clustering-manifold-smoothing) — Community discovery and heat diffusion smoothing on collaboration networks.
* [Urban Traffic Resilience](../../recipes.md) — Highway choke-point detection via `forman_ricci_curvature`.
* [Sheaf Cohomology Consensus](../../recipes.md) — Multi-robot convergence via `laplacian` diffusion.

