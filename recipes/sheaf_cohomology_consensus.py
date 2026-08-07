# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Sheaf Cohomology & Multi-Agent Network Consensus Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Sheaf Restriction & Coboundary Operators (algebrax.analysis.gradient & ax.analysis.divergence):
   Cellular Sheaves assign vector spaces (stalks) to nodes and edges.
   The discrete exterior derivative d0 (ax.analysis.gradient) acts as the 0-th ax.homology.coboundary operator
   delta_0(f)_ij = f(j) - f(i), measuring inconsistency across agent communication channels.

2. Sheaf Laplacian Diffusion & Consensus (algebrax.analysis.laplacian):
   The Sheaf Laplacian L = delta_0* delta_0 = div(grad f) governs multi-robot consensus.
   Nodes iteratively update their state via f[t+1] = f[t] - dt * L(f), converging to global
   consensus when the kernel ker(L) contains non-trivial global sections.

3. Sheaf Monoid Formal Sums (algebrax.semiring.MonoidAlgebraSemiring):
   ax.semiring.MonoidAlgebraSemiring models category formal linear combinations R[M] over agent
   observation sections.
================================================================================
"""

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Sheaf Cohomology & Multi-Agent Network Consensus')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to evaluate cellular')
    print('      sheaf gradients, Laplacian consensus diffusion, and formal monoid sections.')

    # --- Step 1: Sheaf Restriction Mismatch & Coboundary Gradient (ax.analysis.gradient) ---
    print('\n[Step 1] Sheaf Coboundary Gradient delta_0 (ax.analysis.gradient)...')
    print('Explanation: grad(f)_ij = f(j) - f(i) evaluates inconsistency across agent channels.')

    # 4 Autonomous Robots with initial sensor state estimates (e.g. Temperature / Heading)
    agent_states = {0: 10.0, 1: 30.0, 2: 20.0, 3: 40.0}

    # Communication Graph Topology
    comm_graph = {
        0: [1, 2],
        1: [0, 3],
        2: [0, 3],
        3: [1, 2],
    }

    # Sheaf Coboundary Gradient delta_0(f)
    coboundary_mismatch = ax.analysis.gradient(agent_states, comm_graph)

    print('\nInitial Agent State Estimates:', agent_states)
    print('\nEdge Communication Mismatch grad(f)_ij:')
    for u in sorted(coboundary_mismatch.keys()):
        for v, diff in sorted(coboundary_mismatch[u].items()):
            print(f'  Channel ({u} -> {v}): Delta = {diff:+6.1f}')

    # --- Step 2: Sheaf Laplacian Diffusion & Multi-Agent Consensus (ax.analysis.laplacian) ---
    print('\n[Step 2] Multi-Agent Sheaf Laplacian Consensus (ax.analysis.laplacian)...')
    print('Explanation: f[t+1] = f[t] - dt * L(f) diffuses state differences toward consensus.')

    # Build weighted graph adjacency for Laplacian L
    weighted_comm = {
        0: {1: 1.0, 2: 1.0},
        1: {0: 1.0, 3: 1.0},
        2: {0: 1.0, 3: 1.0},
        3: {1: 1.0, 2: 1.0},
    }

    current_f = dict(agent_states)
    dt = 0.2  # Diffusion step size

    print('\nConsensus Iterations over Sheaf Laplacian L:')
    print(f'  Step t= 0: States = {current_f}')

    for step in range(1, 11):
        l_f = ax.analysis.laplacian(current_f, weighted_comm)
        # Gradient descent update: f = f - dt * L(f)
        current_f = {u: current_f[u] - dt * l_f[u] for u in current_f}

        if step in [1, 2, 5, 10]:
            formatted_f = {u: round(val, 2) for u, val in current_f.items()}
            print(f'  Step t={step:2d}: States = {formatted_f}')

    target_consensus = sum(agent_states.values()) / len(agent_states)
    print(f'\nTarget Global Mean Consensus: {target_consensus:.2f}')

    # --- Step 3: Sheaf Category Formal Sums (ax.semiring.MonoidAlgebraSemiring) ---
    print('\n[Step 3] Sheaf Category Formal Observation Sums (ax.semiring.MonoidAlgebraSemiring)...')
    print('Explanation: Formal linear combinations R[M] combine localized agent observation sections.')

    sheaf_algebra = ax.semiring.MonoidAlgebraSemiring(ax.semiring.StandardSemiring[float](), zero_key='None')

    # Robot 1 local section observation map
    obs_agent1 = {'Obstacle_A': 0.8, 'Target_X': 0.2}

    # Robot 2 local section observation map
    obs_agent2 = {'Obstacle_A': 0.5, 'Target_Y': 0.5}

    # Combined Sheaf Observation Section Sum
    section_sum = sheaf_algebra.add(obs_agent1, obs_agent2)

    print('\nRobot 1 Observation Section: ', obs_agent1)
    print('Robot 2 Observation Section: ', obs_agent2)
    print('Combined Sheaf Section Sum:  ', section_sum)

    print('\n==========================================================================')
    print('Use Case Completed: Sheaf Cohomology & Consensus Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
