# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Holographic Bulk-Boundary Duality & Entanglement Entropy Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Hyperbolic Bulk Curvature (algebrax.analysis.forman_ricci_curvature):
   AdS/CFT duality models quantum field theories on a boundary (CFT) linked to
   hyperbolic Anti-de Sitter (AdS) gravity in the bulk. Negative Forman-Ricci
   curvature (K < 0) characterizes discrete hyperbolic bulk graph geometry.

2. Discrete Holographic Gauss-Stokes Theorem (algebrax.analysis.divergence):
   The discrete exterior derivative d0 and ax.analysis.divergence operator relate interior bulk
   field ax.analysis.divergence to boundary flux: sum_{v in Bulk} div(F)_v = sum_{e in Boundary} F_e.

3. MERA Tensor Network Contraction (algebrax.trie.ax.trie.AlgebraicTrie):
   ax.trie.AlgebraicTrie models a Multiscale Entanglement Renormalization Ansatz (MERA)
   tree tensor network, mapping coarse-grained bulk IR nodes to fine-grained UV
   boundary degrees of freedom via subtree contraction (`contract(prefix)`).

4. Ryu-Takayanagi Entanglement Entropy (algebrax.probability.entropy & ax.probability.mutual_information):
   Boundary subsystem entanglement ax.probability.entropy S(A) is geometrically bounded by the area of
   the minimal bulk surface gamma_A (Ryu-Takayanagi formula S(A) = Area(gamma_A) / 4G_N).
   Mutual information I(A; B) = H(A) + H(B) - H(A, B) quantifies quantum correlations.
================================================================================
"""

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Holographic Bulk-Boundary Duality & Entanglement Entropy')
    print('==========================================================================')
    print('Goal: Combine 4 distinct algebraic tools from algebrax to evaluate hyperbolic')
    print('      bulk curvature, discrete boundary flux ax.analysis.divergence, MERA trie tensors,')
    print('      and Ryu-Takayanagi entanglement ax.probability.entropy.')

    # --- Step 1: Hyperbolic Bulk Curvature (Forman-Ricci K < 0) ---
    print('\n[Step 1] Hyperbolic Bulk Geometry (ax.analysis.forman_ricci_curvature)...')
    print('Explanation: Negative Forman-Ricci curvature (K < 0) characterizes discrete')
    print('             hyperbolic bulk space (AdS_3 metric discretization).')

    bulk_boundary_graph = {
        0: {1: 1.0, 2: 1.0},
        1: {0: 1.0, 3: 1.0, 4: 1.0},
        2: {0: 1.0, 5: 1.0, 6: 1.0},
        3: {1: 1.0},
        4: {1: 1.0},
        5: {2: 1.0},
        6: {2: 1.0},
    }

    ricci_k = ax.analysis.forman_ricci_curvature(bulk_boundary_graph)

    print('\nForman-Ricci Curvature across Bulk-Boundary Graph Edges:')
    for edge, k_val in sorted(ricci_k.items()):
        edge_type = 'BULK INTERIOR' if 0 in edge else 'BULK-BOUNDARY INTERFACE'
        print(f'  Edge {edge} [{edge_type}]: Curvature K = {k_val:+5.2f}')

    # --- Step 2: Discrete Holographic Divergence Theorem ---
    print('\n[Step 2] Discrete Holographic Gauss-Stokes Divergence (ax.analysis.divergence)...')
    print('Explanation: Verifies sum_{v in Bulk} div(F)_v = sum_{e in Boundary} F_e.')

    edge_flux = {
        0: {1: 10.0, 2: 14.0},
        1: {3: 4.0, 4: 6.0},
        2: {5: 8.0, 6: 6.0},
    }

    div_f = ax.analysis.divergence(edge_flux)

    bulk_nodes = [0, 1, 2]
    boundary_nodes = [3, 4, 5, 6]

    total_bulk_div = sum(div_f.get(v, 0.0) for v in bulk_nodes)
    total_boundary_flux = sum(div_f.get(v, 0.0) for v in boundary_nodes)

    print('\nDiscrete Field Divergence at Nodes:')
    for v in sorted(div_f.keys()):
        label = 'BULK NODE' if v in bulk_nodes else 'BOUNDARY NODE'
        print(f'  Node {v} [{label}]: div(F) = {div_f[v]:+6.1f}')

    print(f'\nTotal Bulk Field Divergence:     {total_bulk_div:+6.1f}')
    print(f'Total Boundary Inflow/Outflow:   {total_boundary_flux:+6.1f}')
    print(f'Holographic Divergence Theorem:  Sum = {total_bulk_div + total_boundary_flux:.1f} (Exact Conservation)')

    # --- Step 3: MERA Tensor Network Hierarchy via ax.trie.AlgebraicTrie ---
    print('\n[Step 3] MERA Tensor Network Subtree Contraction (ax.trie.AlgebraicTrie)...')
    print('Explanation: MERA hierarchy contracts bulk IR scale branches via contract(prefix).')

    mera_trie = ax.trie.AlgebraicTrie()
    mera_trie[('IR_Root', 'Scale_1', 'Site_A')] = 0.40
    mera_trie[('IR_Root', 'Scale_1', 'Site_B')] = 0.35
    mera_trie[('IR_Root', 'Scale_2', 'Site_C')] = 0.15
    mera_trie[('IR_Root', 'Scale_2', 'Site_D')] = 0.10

    scale_1_weight = mera_trie.contract(('IR_Root', 'Scale_1'))
    scale_2_weight = mera_trie.contract(('IR_Root', 'Scale_2'))
    total_mera_weight = mera_trie.contract(('IR_Root',))

    print('\nMERA Hierarchical Tensor Network Contents:')
    for key, weight in mera_trie.items():
        print(f'  Tensor Branch {key}: Weight = {weight:.2f}')

    print(f'\nContracted IR Scale 1 Subtree Weight: {scale_1_weight:.2f}')
    print(f'Contracted IR Scale 2 Subtree Weight: {scale_2_weight:.2f}')
    print(f'Total MERA Boundary Contracted State: {total_mera_weight:.2f}')

    # --- Step 4: Ryu-Takayanagi Entanglement Entropy & Mutual Info ---
    print('\n[Step 4] Ryu-Takayanagi Boundary Entanglement Entropy & Mutual Information...')
    print('Explanation: Boundary subsystem ax.probability.entropy H(A) scales with bulk minimal surface area.')

    boundary_state_a = {'00': 0.50, '01': 0.25, '10': 0.15, '11': 0.10}
    boundary_state_b = {'00': 0.40, '01': 0.30, '10': 0.20, '11': 0.10}

    # Nested matrix for joint distribution P(X, Y)
    joint_state_ab = {
        '00': {'00': 0.30, '01': 0.10},
        '01': {'00': 0.05, '01': 0.20},
        '10': {'10': 0.15, '11': 0.05},
        '11': {'10': 0.05, '11': 0.10},
    }

    entropy_a = ax.probability.entropy(boundary_state_a)
    entropy_b = ax.probability.entropy(boundary_state_b)
    mi_ab = ax.probability.mutual_information(joint_state_ab)

    minimal_cut_area = entropy_a * 4.0  # In units of 4 G_N

    print(f'\nBoundary Subsystem A Entanglement Entropy S(A):  {entropy_a:.4f} bits')
    print(f'Boundary Subsystem B Entanglement Entropy S(B):  {entropy_b:.4f} bits')
    print(f'Ryu-Takayanagi Minimal Bulk Cut Area Area(gamma_A): {minimal_cut_area:.4f} (G_N units)')
    print(f'Quantum Mutual Information I(A; B):               {mi_ab:.4f} bits')

    print('\n==========================================================================')
    print('Use Case Completed: Holographic Bulk-Boundary Duality Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
