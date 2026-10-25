---
title: Discrete Exterior Calculus & Hodge Theory
description: Exterior derivative, codifferential, metric Hodge star, Hodge k-Laplacian, and Helmholtz-Hodge flow decomposition.
---

# Discrete Exterior Calculus & Hodge Theory (`algebrax.topology.dec`)

`algebrax.topology.dec` (also exported in `algebrax.topology`, `algebrax.homology`, and `algebrax.analysis`) implements Discrete Exterior Calculus (DEC) and Hodge theory on weighted simplicial complexes.

---

## Core Differential & Metric Operators

Given a simplicial complex $K$ equipped with positive inner-product weights $w_k \succ 0$ (representing primal/dual cell volume ratios):

1. **Exterior Derivative ($d_k = \partial_{k+1}^\top: C^k \to C^{k+1}$)**:
   Computed via `exterior_derivative(complex, k)`. Satisfies $d_{k+1} \circ d_k = 0$.
2. **Diagonal Metric Hodge Star ($\star_k: C^k \to C^k$)**:
   Computed via `hodge_star(complex, k, weights=...)`. Scales each canonical $k$-simplex by its positive metric weight $w_k(\sigma) > 0$ (or $w_k(\sigma)^{-1}$ when `inverse=True`).
3. **Hilbert Adjoint Codifferential ($\delta_k: C^k \to C^{k-1}$)**:
   Computed via `codifferential(complex, k, weights_k=..., weights_km1=...)`:
   $$\delta_k = \star_{k-1}^{-1} \, \partial_k \, \star_k$$
   Satisfies $\langle d_{k-1} \alpha, \beta \rangle_{W_k} = \langle \alpha, \delta_k \beta \rangle_{W_{k-1}}$ and $\delta_{k-1} \circ \delta_k = 0$.
4. **Hodge $k$-Laplacian ($\Delta_k: C^k \to C^k$)**:
   Computed via `hodge_laplacian(complex, k, ...)`:
   $$\Delta_k = d_{k-1} \delta_k + \delta_{k+1} d_k$$
   At $k=0$ with unit weights, $\Delta_0$ recovers the combinatorial graph Laplacian $L = D - A$. At $k=1$, the harmonic kernel $\ker(\Delta_1) \cong H^1(K; \mathbb{R})$ isolates global topological circulation around 1D holes.

---

## Helmholtz–Hodge Flow Decomposition (`helmholtz_hodge_decomposition`)

Every discrete 1-cochain (edge flow) $\omega \in C^1(K; \mathbb{R})$ decomposes uniquely into three mutually $W_1$-orthogonal components (`HodgeDecomposition`):

$$\omega = \underbrace{d_0 \alpha}_{\text{exact (gradient)}} + \underbrace{\delta_2 \beta}_{\text{coexact (curl)}} + \underbrace{\gamma}_{\text{harmonic}}$$

1. **Exact ($d_0 \alpha \in \operatorname{im} d_0$)**: Curl-free flow driven by scalar vertex potentials $\alpha \in C^0(K; \mathbb{R})$ ($\operatorname{curl}(d_0 \alpha) = d_1(d_0 \alpha) = 0$).
2. **Coexact ($\delta_2 \beta \in \operatorname{im} \delta_2$)**: Divergence-free local rotational eddies circulating around filled 2-simplices (triangles) ($\operatorname{div}(\delta_2 \beta) = -\delta_1(\delta_2 \beta) = 0$).
3. **Harmonic ($\gamma \in \ker \Delta_1$)**: Simultaneously curl-free and divergence-free global circulation wrapping around 1D topological holes.

```python
from algebrax.topology import SimplicialComplex, helmholtz_hodge_decomposition

# Complex with a filled triangle (0, 1, 2) and a hollow loop (1, 2)-(2, 3)-(1, 3)
sc = SimplicialComplex([(0, 1, 2), (1, 3), (2, 3)])
flow = {(0, 1): 2.5, (1, 2): 3.5, (2, 0): 1.5, (2, 3): 2.0, (3, 1): 2.0}

decomp = helmholtz_hodge_decomposition(sc, flow)
print('Exact (gradient) flow:', decomp.exact)
print('Coexact (triangular curl) flow:', decomp.coexact)
print('Harmonic (topological cycle) flow:', decomp.harmonic)
print('Node potential alpha:', decomp.potential)
print('Triangle curl potential beta:', decomp.copotential)
```

---

## Related Sections

* [Cohomology & Ring Products](cohomology.md) — `Cochain` carrier and `from_flow` / `to_flow` graph flow conversions.
* [Discrete Calculus & Spectral Graph Theory](../analysis/discrete_calculus.md) — Graph Laplacians, Fiedler vectors, and Forman–Ricci curvature.
