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
# # Sheaf Cohomology & Multi-Agent Network Consensus
#
# ## Theory & Mathematical Foundation
#
# 1. **Sheaf Restriction & Coboundary Operators (`analysis.gradient` & `analysis.divergence`)**:
#    Cellular Sheaves assign vector spaces (stalks) to nodes and edges.
#    The discrete exterior derivative $d_0$ acts as the 0-th coboundary operator
#    $\\delta_0(f)_{ij} = f(j) - f(i)$, measuring inconsistency across agent communication channels.
#
# 2. **Sheaf Laplacian Diffusion & Consensus (`algebrax.analysis.laplacian`)**:
#    The Sheaf Laplacian $L = \\delta_0^* \\delta_0 = \\text{div}(\\text{grad } f)$ governs multi-robot consensus.
#    Nodes iteratively update their state via $f[t+1] = f[t] - \\Delta t \\, L(f)$, converging to global consensus.
#
# 3. **Sheaf Monoid Formal Sums (`algebrax.semiring.MonoidAlgebraSemiring`)**:
#    `MonoidAlgebraSemiring` models category formal linear combinations
#    $\\mathbb{R}[M]$ over agent observation sections.

# %%
from typing import Any

import algebrax as ax


def compute_sheaf_coboundary(
    agent_states: dict[Any, float],
    comm_graph: dict[Any, list[Any]],
) -> dict[Any, dict[Any, float]]:
    """Evaluate discrete 0-th coboundary gradient mismatch across communication channels."""
    return ax.analysis.gradient(agent_states, comm_graph)


def simulate_sheaf_consensus(
    agent_states: dict[Any, float],
    comm_graph: dict[Any, dict[Any, float]] | None = None,
    steps: int = 10,
    dt: float = 0.2,
) -> dict[Any, float]:
    """Iterate multi-agent consensus updates over Sheaf Laplacian diffusion."""
    if comm_graph is None:
        comm_graph = {
            0: {1: 1.0, 2: 1.0},
            1: {0: 1.0, 3: 1.0},
            2: {0: 1.0, 3: 1.0},
            3: {1: 1.0, 2: 1.0},
        }
    current_f = dict(agent_states)
    for _ in range(steps):
        l_f = ax.analysis.laplacian(current_f, comm_graph)
        current_f = {u: current_f[u] - dt * l_f.get(u, 0.0) for u in current_f}
    return current_f


def combine_sheaf_observations(
    obs_agent1: dict[str, float],
    obs_agent2: dict[str, float],
) -> dict[str, float]:
    """Combine robot local observation sections via MonoidAlgebraSemiring formal sum."""
    sheaf_algebra = ax.semiring.MonoidAlgebraSemiring(ax.semiring.StandardSemiring[float](), zero_key='None')
    return sheaf_algebra.add(obs_agent1, obs_agent2)


# %% [markdown]
# ## Step 1: Sheaf Coboundary Gradient $\\delta_0$ (`analysis.gradient`)
#
# ## Step 2: Multi-Agent Sheaf Laplacian Consensus (`analysis.laplacian`)
#
# ## Step 3: Sheaf Category Formal Observation Sums (`MonoidAlgebraSemiring`)


def run_demo() -> None:
    """Run Sheaf cohomology coboundary and consensus diffusion demonstrations."""
    agent_states = {0: 10.0, 1: 30.0, 2: 20.0, 3: 40.0}
    comm_graph_unweighted = {
        0: [1, 2],
        1: [0, 3],
        2: [0, 3],
        3: [1, 2],
    }

    coboundary_mismatch = compute_sheaf_coboundary(agent_states, comm_graph_unweighted)
    print('Initial Agent State Estimates:', agent_states)
    print('\nEdge Communication Mismatch grad(f)_ij:')
    for u in sorted(coboundary_mismatch.keys()):
        for v, diff in sorted(coboundary_mismatch[u].items()):
            print(f'  Channel ({u} -> {v}): Delta = {diff:+6.1f}')

    weighted_comm = {
        0: {1: 1.0, 2: 1.0},
        1: {0: 1.0, 3: 1.0},
        2: {0: 1.0, 3: 1.0},
        3: {1: 1.0, 2: 1.0},
    }

    current_f = dict(agent_states)
    print('\nConsensus Iterations over Sheaf Laplacian L:')
    print(f'  Step t= 0: States = {current_f}')

    for step in [1, 2, 5, 10]:
        stepped_f = simulate_sheaf_consensus(agent_states, weighted_comm, steps=step, dt=0.2)
        formatted_f = {u: round(val, 2) for u, val in stepped_f.items()}
        print(f'  Step t={step:2d}: States = {formatted_f}')

    target_consensus = sum(agent_states.values()) / len(agent_states)
    print(f'\nTarget Global Mean Consensus: {target_consensus:.2f}')

    obs_agent1 = {'Obstacle_A': 0.8, 'Target_X': 0.2}
    obs_agent2 = {'Obstacle_A': 0.5, 'Target_Y': 0.5}
    section_sum = combine_sheaf_observations(obs_agent1, obs_agent2)
    print('\nRobot 1 Observation Section: ', obs_agent1)
    print('Robot 2 Observation Section: ', obs_agent2)
    print('Combined Sheaf Section Sum:  ', section_sum)


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Sheaf Cohomology & Consensus Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
