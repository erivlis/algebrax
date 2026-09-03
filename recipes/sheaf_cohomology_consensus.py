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
#    $\delta_0(f)_{ij} = f(j) - f(i)$, measuring inconsistency across agent communication channels.
#
# 2. **Sheaf Laplacian Diffusion & Consensus (`algebrax.analysis.laplacian`)**:
#    The Sheaf Laplacian $L = \delta_0^* \delta_0 = \text{div}(\text{grad } f)$ governs multi-robot consensus.
#    Nodes iteratively update their state via $f[t+1] = f[t] - \Delta t \, L(f)$, converging to global consensus.
#
# 3. **Sheaf Monoid Formal Sums (`algebrax.semiring.MonoidAlgebraSemiring`)**:
#    `MonoidAlgebraSemiring` models category formal linear combinations $\mathbb{R}[M]$ over agent observation sections.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Sheaf Coboundary Gradient $\delta_0$ (`analysis.gradient`)

# %%
agent_states = {0: 10.0, 1: 30.0, 2: 20.0, 3: 40.0}

comm_graph = {
    0: [1, 2],
    1: [0, 3],
    2: [0, 3],
    3: [1, 2],
}

coboundary_mismatch = ax.analysis.gradient(agent_states, comm_graph)

print('Initial Agent State Estimates:', agent_states)
print('\nEdge Communication Mismatch grad(f)_ij:')
for u in sorted(coboundary_mismatch.keys()):
    for v, diff in sorted(coboundary_mismatch[u].items()):
        print(f'  Channel ({u} -> {v}): Delta = {diff:+6.1f}')

# %% [markdown]
# ## Step 2: Multi-Agent Sheaf Laplacian Consensus (`analysis.laplacian`)

# %%
weighted_comm = {
    0: {1: 1.0, 2: 1.0},
    1: {0: 1.0, 3: 1.0},
    2: {0: 1.0, 3: 1.0},
    3: {1: 1.0, 2: 1.0},
}

current_f = dict(agent_states)
dt = 0.2

print('\nConsensus Iterations over Sheaf Laplacian L:')
print(f'  Step t= 0: States = {current_f}')

for step in range(1, 11):
    l_f = ax.analysis.laplacian(current_f, weighted_comm)
    current_f = {u: current_f[u] - dt * l_f[u] for u in current_f}

    if step in [1, 2, 5, 10]:
        formatted_f = {u: round(val, 2) for u, val in current_f.items()}
        print(f'  Step t={step:2d}: States = {formatted_f}')

target_consensus = sum(agent_states.values()) / len(agent_states)
print(f'\nTarget Global Mean Consensus: {target_consensus:.2f}')

# %% [markdown]
# ## Step 3: Sheaf Category Formal Observation Sums (`MonoidAlgebraSemiring`)

# %%
sheaf_algebra = ax.semiring.MonoidAlgebraSemiring(ax.semiring.StandardSemiring[float](), zero_key='None')

obs_agent1 = {'Obstacle_A': 0.8, 'Target_X': 0.2}
obs_agent2 = {'Obstacle_A': 0.5, 'Target_Y': 0.5}

section_sum = sheaf_algebra.add(obs_agent1, obs_agent2)

print('\nRobot 1 Observation Section: ', obs_agent1)
print('Robot 2 Observation Section: ', obs_agent2)
print('Combined Sheaf Section Sum:  ', section_sum)


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Sheaf Cohomology & Consensus Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
