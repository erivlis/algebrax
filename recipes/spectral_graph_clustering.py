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
import math

import algebrax as ax
from algebrax.semiring import Semiring

# %% [markdown]
# ## Step 1: Initializing Research Collaboration Network (8 Researchers)
# Two distinct research clusters (AI Lab: 0, 1, 2, 3 and Quantum Lab: 4, 5, 6, 7) connected by
# cross-disciplinary bridge edges between nodes 2 and 4, and 3 and 5.

# %%
collaboration_network = {
    0: {1: 3.0, 2: 2.0, 3: 1.0},
    1: {0: 3.0, 2: 2.0, 3: 2.0},
    2: {0: 2.0, 1: 2.0, 3: 3.0, 4: 1.0},  # Inter-cluster bridge to 4
    3: {0: 1.0, 1: 2.0, 2: 3.0, 5: 1.0},  # Inter-cluster bridge to 5
    4: {2: 1.0, 5: 3.0, 6: 2.0, 7: 2.0},  # Inter-cluster bridge to 2
    5: {3: 1.0, 4: 3.0, 6: 2.0, 7: 3.0},  # Inter-cluster bridge to 3
    6: {4: 2.0, 5: 2.0, 7: 4.0},
    7: {4: 2.0, 5: 3.0, 6: 4.0},
}

researchers = {
    0: 'Alice (AI Theory)',
    1: 'Bob (Deep Learning)',
    2: 'Charlie (Optimization)',
    3: 'Diana (Graph ML)',
    4: 'Evan (Quantum Info)',
    5: 'Fiona (Qiskit Dev)',
    6: 'George (Quantum Hardware)',
    7: 'Hannah (Quantum Optics)',
}

print('Collaboration Network Topology:')
for u in sorted(collaboration_network.keys()):
    neighbors_str = ', '.join([f'{v} (w={w:.1f})' for v, w in collaboration_network[u].items()])
    print(f'  Researcher {u} [{researchers[u]}]: -> {neighbors_str}')

# %% [markdown]
# ## Step 2: Constructing Combinatorial and Symmetric Graph Laplacians
# Computes sparse operator matrices $L = D - W$ and $L_{\mathrm{sym}} = D^{-1/2} L D^{-1/2}$.

# %%
lap_comb = ax.matrix.laplacian_matrix(collaboration_network)
lap_sym = ax.matrix.laplacian_matrix(collaboration_network, normalized='sym')

print('\nCombinatorial Laplacian L (Diagonal Degrees):')
for u in sorted(lap_comb.keys()):
    d_u = lap_comb[u].get(u, 0.0)
    print(f'  Node {u}: Degree d_{u} = {d_u:.1f}')

# %% [markdown]
# ## Step 3: Computing Algebraic Connectivity & Fiedler Vector
# Solves for $\lambda_2$ and $\mathbf{v}_2$ using sparse Rayleigh Quotient Conjugate Gradient (RQ-CG).

# %%
lambda_2, fiedler = ax.analysis.fiedler_vector(collaboration_network)
alg_conn = ax.analysis.algebraic_connectivity(collaboration_network)

print(f'\nAlgebraic Connectivity (lambda_2): {lambda_2:.6f}')
assert math.isclose(lambda_2, alg_conn)

print('\nFiedler Vector v_2 (Cluster Embedding):')
for u in sorted(fiedler.keys()):
    cluster_hint = 'Cluster A' if fiedler[u] >= 0 else 'Cluster B'
    print(f'  Node {u} [{researchers[u]}]: v_2 = {fiedler[u]:+.4f} [{cluster_hint}]')

# %% [markdown]
# ## Step 4: Spectral Bipartitioning & Cheeger Conductance Cut
# Partitions the network along the zero-crossing of the Fiedler vector and measures cut quality.

# %%
cluster_a, cluster_b, metrics = ax.analysis.spectral_bipartition(collaboration_network, method='sign')

print('\nSpectral Bipartition Results:')
print('  Cluster A (AI Lab):', sorted(cluster_a))
print('  Cluster B (Quantum Lab):', sorted(cluster_b))
print('\nCheeger Cut Quality Metrics:')
for metric_name, val in metrics.items():
    print(f'  {metric_name:<16}: {val:.4f}')

# %% [markdown]
# ## Step 5: Iterative Laplacian Smoothing & Heat Diffusion
# Simulates temperature/signal diffusion on the manifold $\mathbf{u}^{(t+1)} = (I - \tau L) \mathbf{u}^{(t)}$.
# Demonstrates monotonic decrease of discrete Dirichlet energy.


# %%
def dirichlet_energy(lap, u_vec):
    lu = ax.matrix.mat_vec(lap, u_vec)
    return 0.5 * sum(u_vec[k] * lu.get(k, 0.0) for k in u_vec)


# Noisy initial signal (e.g. localized grant funding)
initial_signal = {0: 100.0, 1: 0.0, 2: 10.0, 3: 0.0, 4: 0.0, 5: 50.0, 6: 0.0, 7: 0.0}
e_init = dirichlet_energy(lap_comb, initial_signal)
print(f'\nInitial Dirichlet Energy: {e_init:.4f}')

print('\nLaplacian Smoothing Progress:')
for steps in [1, 5, 10, 25]:
    smoothed = ax.analysis.laplacian_smoothing(initial_signal, collaboration_network, steps=steps, tau=0.05)
    e_smooth = dirichlet_energy(lap_comb, smoothed)
    pct_red = (1 - e_smooth / e_init) * 100
    print(f'  After {steps:>2} diffusion steps: Dirichlet Energy = {e_smooth:>8.4f} (Reduction: {pct_red:.1f}%)')

# %% [markdown]
# ## Step 6: Full Eigenspectrum Analysis
# Evaluates the complete spectrum $0 = \lambda_1 \le \lambda_2 \le \dots \le \lambda_8$ via cyclic Jacobi sweeps.

# %%
eigenvals, _ = ax.analysis.laplacian_spectrum(collaboration_network)
print('\nFull Laplacian Spectrum:')
for idx, val in enumerate(eigenvals):
    print(f'  lambda_{idx + 1} = {val:.4f}')

spectral_gap = eigenvals[1] - eigenvals[0]
print(f'\nSpectral Gap (lambda_2 - lambda_1): {spectral_gap:.4f}')
