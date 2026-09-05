# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = "..", editable = true }
# ///

# %% [markdown]
# # Spectral Graph Clustering & Manifold Smoothing
#
# ## Theory & Mathematical Foundation
#
# 1. **Graph Laplacian Operator ($L = D - W$)**:
#    The unnormalized combinatorial Laplacian $L = D - W$ and the symmetric normalized Laplacian
#    $L_{\mathrm{sym}} = D^{-1/2} L D^{-1/2} = I - D^{-1/2} W D^{-1/2}$ act as discrete Laplace-Beltrami operators
#    governing diffusion, wave propagation, and harmonic functions on graph manifolds.
#
# 2. **Fiedler Eigenvalue & Cheeger's Inequality**:
#    The second smallest eigenvalue $\lambda_2$ (algebraic connectivity) and its associated eigenvector $\mathbf{v}_2$
#    (the Fiedler vector) minimize the continuous Rayleigh quotient on the subspace orthogonal to $\mathbf{1}$:
#    $$\lambda_2 = \min_{\mathbf{x} \perp \mathbf{1}, \|\mathbf{x}\|_2=1} \mathbf{x}^T L \mathbf{x}$$
#    By Cheeger's inequality, $\lambda_2$ tightly bounds the optimal graph conductance $h(G)$:
#    $$\frac{\lambda_2}{2} \le h(G) \le \sqrt{2 \lambda_2}$$
#
# 3. **Laplacian Smoothing & Dirichlet Energy Minimization**:
#    Applying discrete Euler integration of the heat equation $\mathbf{u}^{(t+1)} = (I - \tau L) \mathbf{u}^{(t)}$
#    monotonically minimizes the discrete Dirichlet energy $E(\mathbf{u}) = \frac{1}{2} \mathbf{u}^T L \mathbf{u}$,
#    acting as a spectral low-pass filter that removes localized high-frequency spatial noise.

# %%
from collections.abc import Mapping
from typing import Any

import algebrax as ax

# %%
# Benchmark collaboration network (8 researchers across AI and Quantum labs)
collaboration_network: dict[int, dict[int, float]] = {
    0: {1: 3.0, 2: 2.0, 3: 1.0},
    1: {0: 3.0, 2: 2.0, 3: 2.0},
    2: {0: 2.0, 1: 2.0, 3: 3.0, 4: 1.0},  # Inter-cluster bridge to 4
    3: {0: 1.0, 1: 2.0, 2: 3.0, 5: 1.0},  # Inter-cluster bridge to 5
    4: {2: 1.0, 5: 3.0, 6: 2.0, 7: 2.0},  # Inter-cluster bridge to 2
    5: {3: 1.0, 4: 3.0, 6: 2.0, 7: 3.0},  # Inter-cluster bridge to 3
    6: {4: 2.0, 5: 2.0, 7: 4.0},
    7: {4: 2.0, 5: 3.0, 6: 4.0},
}

researchers: dict[int, str] = {
    0: 'Alice (AI Theory)',
    1: 'Bob (Deep Learning)',
    2: 'Charlie (Optimization)',
    3: 'Diana (Graph ML)',
    4: 'Evan (Quantum Info)',
    5: 'Fiona (Qiskit Dev)',
    6: 'George (Quantum Hardware)',
    7: 'Hannah (Quantum Optics)',
}


# %%
def dirichlet_energy(
    lap: Mapping[Any, Mapping[Any, float]],
    u_vec: Mapping[Any, float],
) -> float:
    """Calculate discrete Dirichlet energy 0.5 * u^T L u on the graph manifold."""
    lu = ax.matrix.mat_vec(lap, u_vec)
    return 0.5 * sum(u_vec[k] * lu.get(k, 0.0) for k in u_vec)


def compute_spectral_clustering(
    graph: Mapping[Any, Mapping[Any, float]],
    method: str = 'sign',
) -> dict[str, Any]:
    """Execute spectral graph clustering: Laplacians, algebraic connectivity, Fiedler vector, Cheeger cut."""
    lap_comb = ax.matrix.laplacian_matrix(graph)
    lap_sym = ax.matrix.laplacian_matrix(graph, normalized='sym')
    lambda_2, fiedler = ax.analysis.fiedler_vector(graph)
    cluster_a, cluster_b, metrics = ax.analysis.spectral_bipartition(graph, method=method)
    eigenvals, _ = ax.analysis.laplacian_spectrum(graph)
    spectral_gap = eigenvals[1] - eigenvals[0] if len(eigenvals) >= 2 else 0.0

    return {
        'lap_comb': lap_comb,
        'lap_sym': lap_sym,
        'lambda_2': lambda_2,
        'fiedler': fiedler,
        'cluster_a': cluster_a,
        'cluster_b': cluster_b,
        'metrics': metrics,
        'eigenvalues': eigenvals,
        'spectral_gap': spectral_gap,
    }


def simulate_manifold_diffusion(
    graph: Mapping[Any, Mapping[Any, float]],
    initial_signal: Mapping[Any, float],
    steps: int = 10,
    tau: float = 0.05,
) -> dict[str, Any]:
    """Simulate heat/signal diffusion u^(t+1) = (I - tau * L) u^t and evaluate Dirichlet energy."""
    lap_comb = ax.matrix.laplacian_matrix(graph)
    e_init = dirichlet_energy(lap_comb, initial_signal)
    smoothed = ax.analysis.laplacian_smoothing(initial_signal, graph, steps=steps, tau=tau)
    e_smooth = dirichlet_energy(lap_comb, smoothed)
    pct_red = (1 - e_smooth / e_init) * 100 if e_init > 1e-12 else 0.0

    return {
        'initial_signal': dict(initial_signal),
        'smoothed_signal': smoothed,
        'initial_energy': e_init,
        'final_energy': e_smooth,
        'energy_reduction_pct': pct_red,
    }


# %%
def run_demo() -> None:
    """Run full demonstration of spectral graph clustering and manifold smoothing."""
    print('Collaboration Network Topology:')
    for u in sorted(collaboration_network.keys()):
        neighbors_str = ', '.join([f'{v} (w={w:.1f})' for v, w in collaboration_network[u].items()])
        print(f'  Researcher {u} [{researchers[u]}]: -> {neighbors_str}')

    # Step 2 & 3: Spectral Clustering
    results = compute_spectral_clustering(collaboration_network, method='sign')

    print('\nCombinatorial Laplacian L (Diagonal Degrees):')
    for u in sorted(results['lap_comb'].keys()):
        d_u = results['lap_comb'][u].get(u, 0.0)
        print(f'  Node {u}: Degree d_{u} = {d_u:.1f}')

    print(f"\nAlgebraic Connectivity (lambda_2): {results['lambda_2']:.6f}")

    print('\nFiedler Vector v_2 (Cluster Embedding):')
    for u in sorted(results['fiedler'].keys()):
        cluster_hint = 'Cluster A' if results['fiedler'][u] >= 0 else 'Cluster B'
        print(f"  Node {u} [{researchers[u]}]: v_2 = {results['fiedler'][u]:+.4f} [{cluster_hint}]")

    print('\nSpectral Bipartition Results:')
    print('  Cluster A (AI Lab):', sorted(results['cluster_a']))
    print('  Cluster B (Quantum Lab):', sorted(results['cluster_b']))

    print('\nCheeger Cut Quality Metrics:')
    for metric_name, val in results['metrics'].items():
        print(f'  {metric_name:<16}: {val:.4f}')

    # Step 5: Laplacian Smoothing & Heat Diffusion
    initial_signal = {0: 100.0, 1: 0.0, 2: 10.0, 3: 0.0, 4: 0.0, 5: 50.0, 6: 0.0, 7: 0.0}
    lap_comb = results['lap_comb']
    e_init = dirichlet_energy(lap_comb, initial_signal)
    print(f'\nInitial Dirichlet Energy: {e_init:.4f}')

    print('\nLaplacian Smoothing Progress:')
    for steps in [1, 5, 10, 25]:
        diff_res = simulate_manifold_diffusion(collaboration_network, initial_signal, steps=steps, tau=0.05)
        e_smooth = diff_res['final_energy']
        pct_red = diff_res['energy_reduction_pct']
        print(f'  After {steps:>2} diffusion steps: Dirichlet Energy = {e_smooth:>8.4f} (Reduction: {pct_red:.1f}%)')

    # Step 6: Full Laplacian Spectrum
    print('\nFull Laplacian Spectrum:')
    for idx, val in enumerate(results['eigenvalues']):
        print(f'  lambda_{idx + 1} = {val:.4f}')
    print(f"\nSpectral Gap (lambda_2 - lambda_1): {results['spectral_gap']:.4f}")


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Spectral Graph Clustering Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
