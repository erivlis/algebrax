# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Topological Data Analysis (TDA) & Persistent Homology
#
# ## Theory & Mathematical Foundation
#
# 1. **Transitive Closure & Connected Components Betti Number $\beta_0$ (`BooleanSemiring` & `ax.matrix.power`)**:
#    Boolean Semiring $(\{\text{False}, \text{True}\}, \text{OR}, \text{AND})$ models reachability.
#    Evaluating matrix power $M^N$ over the Boolean semiring yields the transitive closure matrix.
#    The number of distinct equivalence classes in $M^N$ determines the zeroth Betti number $\beta_0(\epsilon)$,
#    which counts connected topological components at filtration radius $\epsilon$.
#
# 2. **Vietoris-Rips Simplicial Edge Curvature (`algebrax.analysis.forman_ricci_curvature`)**:
#    Forman-Ricci curvature $K(e)$ evaluates local topology across 1-simplices (edges) in the
#    simplicial complex. Negative curvature $K < 0$ highlights topological bridge handles (1-cycles / $\beta_1$ loops).
#
# 3. **Boundary Matrix Invariants (`algebrax.matrix.academic.determinant`)**:
#    Evaluating determinants $\det(d_k)$ across simplicial boundary operators $d_k: C_k \to C_{k-1}$
#    audits homology boundary cycle consistency.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Point Cloud Filtration & Zeroth Betti Number $\beta_0$ (Boolean Semiring)
# Transitive closure $M^N$ over `BooleanSemiring` $(\{\text{F}, \text{T}\}, \text{OR}, \text{AND})$
# finds connected component equivalence classes $\beta_0(\epsilon)$.

# %%
point_distances = {
    0: {1: 0.8, 2: 1.1, 3: 4.2},
    1: {0: 0.8, 2: 0.9, 4: 4.5},
    2: {0: 1.1, 1: 0.9, 3: 3.9},
    3: {0: 4.2, 2: 3.9, 4: 1.2},
    4: {1: 4.5, 3: 1.2},
}

eps_threshold = 1.5
adjacency_eps = {}
for u, neighbors in point_distances.items():
    row = {u: True}
    for v, d in neighbors.items():
        if d <= eps_threshold:
            row[v] = True
    adjacency_eps[u] = row

bool_semiring = ax.semiring.BooleanSemiring()
reachability = ax.matrix.power(adjacency_eps, 5, semiring=bool_semiring)

components = set()
for u in sorted(reachability.keys()):
    component_members = tuple(sorted(v for v, connected in reachability[u].items() if connected))
    components.add(component_members)

b_0 = len(components)

print(f'Filtration Threshold Radius Eps: {eps_threshold}')
print('Adjacency Graph (Distance <= 1.5):', adjacency_eps)
print('\nConnected Components at Radius Eps = 1.5:')
for idx, comp in enumerate(sorted(components), 1):
    print(f'  Component {idx}: Points {comp}')

print(f'\nZeroth Betti Number b_0(Eps=1.5): {b_0} (2 Topological Clusters Detected)')

# %% [markdown]
# ## Step 2: Simplicial Complex Edge Curvature (`forman_ricci_curvature`)
# $K < 0$ identifies topological bottleneck bridges connecting clusters;
# $K > 0$ identifies dense 1-simplex cluster triangles.

# %%
simplicial_graph = {
    0: {1: 0.8, 2: 1.1},
    1: {0: 0.8, 2: 0.9},
    2: {0: 1.1, 1: 0.9, 3: 3.9},
    3: {2: 3.9, 4: 1.2},
    4: {3: 1.2},
}

ricci_k = ax.analysis.forman_ricci_curvature(simplicial_graph)

print('\nForman-Ricci Curvature on 1-Simplices (Edges):')
for edge, k_val in sorted(ricci_k.items()):
    bridge_tag = ' <== INTER-CLUSTER TOPOLOGICAL BRIDGE' if k_val < 0 else ' <== INTRA-CLUSTER SIMPLEX'
    print(f'  Simplex {edge}: Curvature K = {k_val:+5.2f}{bridge_tag}')

# %% [markdown]
# ## Step 3: Boundary Operator Matrix Determinant (`ax.matrix.determinant`)
# Computes determinant $\det(K)$ of structural Laplacians/Boundary maps.

# %%
boundary_matrix = {
    0: {0: 2.0, 1: -1.0, 2: -1.0},
    1: {0: -1.0, 1: 2.0, 2: -1.0},
    2: {0: -1.0, 1: -1.0, 2: 2.0},
}

det_b = ax.matrix.academic.determinant(boundary_matrix)

print('\nBoundary Operator Laplacian Matrix K:')
for r in sorted(boundary_matrix.keys()):
    print(f'  Row {r}: {boundary_matrix[r]}')

print(f'\nBoundary Matrix Determinant det(K): {det_b:.2f}')
print('Interpretation: det(K) = 0 confirms presence of 0-mode (connected component invariant).')


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Topological Data Analysis (TDA) Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
