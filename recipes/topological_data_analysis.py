# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Topological Data Analysis (TDA) & Persistent Homology Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Transitive Closure & Connected Components Betti Number b_0 (ax.semiring.BooleanSemiring & matrix.power):
   ax.semiring.BooleanSemiring ({False, True}, OR, AND) models reachability.
   Computing matrix ax.matrix.power M^N over ax.semiring.BooleanSemiring yields the transitive closure matrix.
   The number of distinct equivalence classes in M^N determines the zeroth Betti number b_0(Eps),
   which counts connected topological components at filtration radius Eps.

2. Vietoris-Rips Simplicial Edge Curvature (algebrax.analysis.forman_ricci_curvature):
   Forman-Ricci curvature K(e) evaluates local topology across 1-simplices (edges) in the
   simplicial complex. Negative curvature K < 0 highlights topological bridge handles (1-cycles / b_1 loops),
   while positive curvature K > 0 highlights dense geometric clusters.

3. Boundary Matrix Invariants (algebrax.matrix.academic.determinant):
   Evaluating determinants det(d_k) and matrix ranks across simplicial boundary operators
   d_k: C_k -> C_{k-1} audits homology boundary cycle consistency.
================================================================================
"""

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Topological Data Analysis (TDA) & Persistent Homology')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to evaluate Boolean')
    print('      reachability connected components (b_0), Forman-Ricci simplicial edge')
    print('      curvatures, and boundary operator matrix determinants.')

    # --- Step 1: Point Cloud Filtration & Zeroth Betti Number b_0 (ax.semiring.BooleanSemiring) ---
    print('\n[Step 1] Vietoris-Rips Filtration & Betti Number b_0 (ax.semiring.BooleanSemiring)...')
    print('Explanation: Transitive closure M^N over ax.semiring.BooleanSemiring ({F, T}, OR, AND)')
    print('             finds connected component equivalence classes b_0(Eps).')

    # Point cloud distance matrix for 5 data points
    # Points 0, 1, 2 form Cluster A (distances ~1.0); Points 3, 4 form Cluster B (distances ~1.2)
    # Distance between Cluster A and B is ~4.0
    point_distances = {
        0: {1: 0.8, 2: 1.1, 3: 4.2},
        1: {0: 0.8, 2: 0.9, 4: 4.5},
        2: {0: 1.1, 1: 0.9, 3: 3.9},
        3: {0: 4.2, 2: 3.9, 4: 1.2},
        4: {1: 4.5, 3: 1.2},
    }

    # Filtration at Radius Eps = 1.5
    eps_threshold = 1.5
    adjacency_eps = {}
    for u, neighbors in point_distances.items():
        row = {u: True}  # Self-loop
        for v, d in neighbors.items():
            if d <= eps_threshold:
                row[v] = True
        adjacency_eps[u] = row

    # Transitive Closure M^5 over ax.semiring.BooleanSemiring
    bool_semiring = ax.semiring.BooleanSemiring()
    reachability = ax.matrix.power(adjacency_eps, 5, semiring=bool_semiring)

    # Extract unique connected components (zeroth Betti number b_0)
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

    # --- Step 2: Simplicial Complex Edge Curvature (ax.analysis.forman_ricci_curvature) ---
    print('\n[Step 2] Simplicial Complex Forman-Ricci Edge Curvature (ax.analysis.forman_ricci_curvature)...')
    print('Explanation: K < 0 identifies topological bottleneck bridges connecting clusters;')
    print('             K > 0 identifies dense 1-simplex cluster triangles.')

    # Simplicial complex graph at higher filtration threshold Eps = 4.0 (bridge 2-3 forms)
    simplicial_graph = {
        0: {1: 0.8, 2: 1.1},
        1: {0: 0.8, 2: 0.9},
        2: {0: 1.1, 1: 0.9, 3: 3.9},  # Edge (2, 3) is the inter-cluster bridge
        3: {2: 3.9, 4: 1.2},
        4: {3: 1.2},
    }

    ricci_k = ax.analysis.forman_ricci_curvature(simplicial_graph)

    print('\nForman-Ricci Curvature on 1-Simplices (Edges):')
    for edge, k_val in sorted(ricci_k.items()):
        bridge_tag = ' <== INTER-CLUSTER TOPOLOGICAL BRIDGE' if k_val < 0 else ' <== INTRA-CLUSTER SIMPLEX'
        print(f'  Simplex {edge}: Curvature K = {k_val:+5.2f}{bridge_tag}')

    # --- Step 3: Boundary Operator Matrix Determinant ---
    print('\n[Step 3] Boundary Operator Matrix Determinant (ax.matrix.determinant)...')
    print('Explanation: Computes ax.matrix.determinant det(K) of structural Laplacians/Boundary maps.')

    # 3x3 Boundary Laplacian matrix for Cluster A 1-simplices
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

    print('\n==========================================================================')
    print('Use Case Completed: Topological Data Analysis (TDA) Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
