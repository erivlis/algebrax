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
# # Topological Neural Networks (TNN): Simplicial Convolution & Hodge Flow Denoising
#
# ## Theory & Mathematical Foundation
#
# Standard Graph Neural Networks (GNNs) operate exclusively on 1-skeletons (vertices and pairwise edges).
# However, many real-world physical and network processes—such as fluid dynamics, oceanic circulation,
# electrical power flux, and transportation routing—natively reside on **higher-order simplices**:
# edges (1-simplices, flux/current), triangles (2-simplices, circulation/vorticity), and tetrahedral volumes.
#
# A **Topological Neural Network (TNN)**, specifically a **Simplicial Convolutional Network (SCNN)**,
# generalizes message passing to cellular domains through **boundary operators** and **Hodge Laplacians**:
#
# 1. **Boundary and Coboundary Maps**:
#    - $\partial_1 = B_1: C_1 \to C_0$ (maps 1-simplices/edges to 0-simplices/vertices; discrete divergence).
#    - $d_0 = B_1^T: C_0 \to C_1$ (maps 0-simplices to 1-simplices; discrete gradient).
#    - $\partial_2 = B_2: C_2 \to C_1$ (maps 2-simplices/faces to 1-simplices/edges; discrete curl boundary).
#    - $d_1 = B_2^T: C_1 \to C_2$ (evaluates circulation/curl around faces).
#
# 2. **Hodge 1-Laplacian Decomposition**:
#    The 1-Laplacian $\Delta_1$ decomposes into two distinct geometric interactions:
#    $$\Delta_1 = L_1^{\text{down}} + L_1^{\text{up}} = B_1^T B_1 + B_2 B_2^T$$
#    - **Lower Laplacian ($L_1^{\text{down}} = B_1^T B_1$)**:
#      Models interactions between edges that share a common vertex.
#    - **Upper Laplacian ($L_1^{\text{up}} = B_2 B_2^T$)**:
#      Models interactions between edges that co-bound a common 2-simplex (triangle).
#    - **Harmonic Space ($\ker(\Delta_1)$)**:
#      Spanned by topological non-bounding cycles (holes, $\beta_1$).
#
# 3. **Simplicial Convolutional Layer**:
#    For an edge signal $\mathbf{h}_1 \in \mathbb{R}^{|E|}$ and node potential $\mathbf{h}_0 \in \mathbb{R}^{|V|}$:
#    $$\mathbf{h}_1^{(t+1)} = \sigma \left(
#        W_{\text{self}} \mathbf{h}_1^{(t)}
#        + W_{\text{down}} L_1^{\text{down}} \mathbf{h}_1^{(t)}
#        + W_{\text{up}} L_1^{\text{up}} \mathbf{h}_1^{(t)}
#        + W_{\text{grad}} B_1^T \mathbf{h}_0
#    \right)$$
#
# 4. **Helmholtz-Hodge Decomposition Audit**:
#    Any reconstructed edge flow decomposes into mutually orthogonal subspaces:
#    $$\omega = \omega_{\text{exact}} \oplus \omega_{\text{coexact}} \oplus \omega_{\text{harmonic}}$$
#    A physically conservative flow past a topological obstacle must preserve the harmonic circulation
#    while eliminating divergence noise ($\omega_{\text{exact}} \to 0$).

# %%
from algebrax.homology import SimplicialComplex, helmholtz_hodge_decomposition
from algebrax.matrix.core import add, dot, mat_vec, transpose
from algebrax.typing import SparseMatrix

# %% [markdown]
# ## Step 1: Simplicial Complex & Topological Hole Invariant ($\beta_1 = 1$)
#
# We construct a triangulated annulus (a disk with a central topological hole).
# Inner boundary vertices: `{0, 1, 2}` (the hole / obstacle).
# Outer boundary vertices: `{3, 4, 5}`.
# Connecting triangles fill the annulus, creating non-trivial first homology ($\beta_1 = 1$).


# %%
def build_annulus_simplicial_complex() -> SimplicialComplex:
    """Build a triangulated planar annulus with Betti numbers (beta_0=1, beta_1=1, beta_2=0)."""
    annulus_triangles = [
        (0, 1, 3),
        (1, 3, 4),
        (1, 2, 4),
        (2, 4, 5),
        (2, 0, 5),
        (0, 5, 3),
    ]
    return SimplicialComplex(annulus_triangles)


sc = build_annulus_simplicial_complex()
betti = sc.betti_numbers(max_k=2)

print('=' * 60)
print('1. SIMPLICIAL COMPLEX TOPOLOGY')
print('=' * 60)
print(f'Betti Numbers: beta_0 = {betti[0]} (components), beta_1 = {betti[1]} (holes), beta_2 = {betti[2]} (voids)')
print(f'Total 0-simplices (Vertices)  : {len(sc._simplices.get(0, set()))}')
print(f'Total 1-simplices (Edges)     : {len(sc._simplices.get(1, set()))}')
print(f'Total 2-simplices (Triangles) : {len(sc._simplices.get(2, set()))}')
print(f'Boundary nilpotency verified  : {sc.verify_nilpotency(1)}')


# %% [markdown]
# ## Step 2: Simplicial Operators & Hodge 1-Laplacian ($L_1^{\text{down}}$ & $L_1^{\text{up}}$)
#
# We extract the boundary matrices $B_1 = \partial_1$ and $B_2 = \partial_2$, and compute
# the lower and upper Hodge 1-Laplacians using sparse matrix products.


# %%
class SimplicialHodgeOperators:
    """Computes and caches boundary and Hodge Laplacian operators for a SimplicialComplex."""

    def __init__(self, complex: SimplicialComplex):
        self.complex = complex
        self.b1: SparseMatrix = complex.boundary_matrices.get(1, {})
        self.b2: SparseMatrix = complex.boundary_matrices.get(2, {})
        self.b1_t: SparseMatrix = transpose(self.b1)
        self.b2_t: SparseMatrix = transpose(self.b2)

        # L_down = B_1^T * B_1 (edge interaction through shared vertices)
        self.l1_down: SparseMatrix = dot(self.b1_t, self.b1) if self.b1 else {}

        # L_up = B_2 * B_2^T (edge interaction through shared triangles)
        self.l1_up: SparseMatrix = dot(self.b2, self.b2_t) if self.b2 else {}

        # Combined Hodge 1-Laplacian: Delta_1 = L_down + L_up
        self.l1_full: SparseMatrix = add(self.l1_down, self.l1_up)


ops = SimplicialHodgeOperators(sc)

print('\n' + '=' * 60)
print('2. HODGE 1-LAPLACIAN STRUCTURE')
print('=' * 60)
print(f'Boundary B_1 shape: {len(ops.b1)} vertices x {len(ops.b1_t)} edges')
print(f'Boundary B_2 shape: {len(ops.b2)} edges x {len(ops.b2_t)} triangles')
print(f'L1_down nonzero entries: {sum(len(row) for row in ops.l1_down.values())}')
print(f'L1_up   nonzero entries: {sum(len(row) for row in ops.l1_up.values())}')


# %% [markdown]
# ## Step 3: Physical Ground-Truth Flow & Synthetic Corruption
#
# We generate a ground-truth conservative circulation flowing around the central obstacle.
# Then, we inject synthetic noise:
# - Spurious divergence sources/sinks on vertices (corrupting the exact gradient component)
# - Missing observations on 33% of the edges

# %%
# Canonical edges from complex
all_edges = sorted(sc._simplices[1])

# Ground truth: uniform circular circulation around the obstacle
# Inner edges: (0, 1), (1, 2), (0, 2)
# Outer edges: (3, 4), (4, 5), (3, 5)
ground_truth_flow: dict[tuple[int, ...], float] = {
    (0, 1): 2.0,
    (1, 2): 2.0,
    (0, 2): -2.0,
    (3, 4): 1.5,
    (4, 5): 1.5,
    (3, 5): -1.5,
    (0, 3): 0.5,
    (1, 4): 0.5,
    (2, 5): 0.5,
    (1, 3): -0.5,
    (2, 4): -0.5,
    (0, 5): -0.5,
}

# Ensure all edges are mapped
for e in all_edges:
    if e not in ground_truth_flow:
        ground_truth_flow[e] = 0.0

# Node driving potential (inflow at node 3, outflow at node 5)
node_potential: dict[tuple[int, ...], float] = {
    (0,): 0.0,
    (1,): 0.0,
    (2,): 0.0,
    (3,): 1.0,
    (4,): 0.0,
    (5,): -1.0,
}

# Add synthetic noise and dropouts
noisy_flow: dict[tuple[int, ...], float] = {}
for i, e in enumerate(all_edges):
    true_val = ground_truth_flow[e]
    # Introduce deterministic perturbations: noise and edge dropouts
    if i % 3 == 0:
        noisy_flow[e] = 0.0  # Missing sensor observation
    else:
        noise = 1.2 if (i % 2 == 1) else -1.2
        noisy_flow[e] = true_val + noise

print('\n' + '=' * 60)
print('3. FLOW OBSERVATION & SENSOR NOISE')
print('=' * 60)
initial_mse = sum((noisy_flow[e] - ground_truth_flow[e]) ** 2 for e in all_edges) / len(all_edges)
print(f'Initial Noisy Flow MSE: {initial_mse:.4f}')


# %% [markdown]
# ## Step 4: Simplicial Convolutional Network (SCNN) Architecture
#
# We build a parameterized Simplicial Convolution Layer:
#
# $$
# \mathbf{z}_1 = w_{\text{self}} \mathbf{h}_1 + w_{\text{down}} L_1^{\text{down}} \mathbf{h}_1
# + w_{\text{up}} L_1^{\text{up}} \mathbf{h}_1 + w_{\text{grad}} B_1^T \mathbf{h}_0
# $$
#
# With learnable weights $\mathbf{w} = [w_{\text{self}}, w_{\text{down}}, w_{\text{up}}, w_{\text{grad}}]$.
# We implement analytic forward and backward passes using native AlgebraX sparse operations.


# %%
class SimplicialConvFilter:
    """Differentiable Simplicial Convolutional Filter over 1-simplices."""

    def __init__(
        self,
        operators: SimplicialHodgeOperators,
        w_self: float = 0.5,
        w_down: float = 0.0,
        w_up: float = 0.0,
        w_grad: float = 0.0,
    ):
        self.ops = operators
        self.w_self = w_self
        self.w_down = w_down
        self.w_up = w_up
        self.w_grad = w_grad

    def forward(
        self,
        h1: dict[tuple[int, ...], float],
        h0: dict[tuple[int, ...], float],
    ) -> tuple[dict[tuple[int, ...], float], dict[str, dict[tuple[int, ...], float]]]:
        """Compute simplicial convolution and return (output, cache_for_backward)."""
        # Message passing components
        m_self = {e: h1.get(e, 0.0) for e in all_edges}
        m_down = mat_vec(self.ops.l1_down, h1)
        m_up = mat_vec(self.ops.l1_up, h1)
        m_grad = mat_vec(self.ops.b1_t, h0)

        out: dict[tuple[int, ...], float] = {}
        for e in all_edges:
            val = (
                self.w_self * m_self.get(e, 0.0)
                + self.w_down * m_down.get(e, 0.0)
                + self.w_up * m_up.get(e, 0.0)
                + self.w_grad * m_grad.get(e, 0.0)
            )
            out[e] = val

        cache = {
            'm_self': m_self,
            'm_down': m_down,
            'm_up': m_up,
            'm_grad': m_grad,
        }
        return out, cache

    def train_step(
        self,
        h1_noisy: dict[tuple[int, ...], float],
        h0: dict[tuple[int, ...], float],
        y_true: dict[tuple[int, ...], float],
        lr: float = 0.01,
    ) -> tuple[float, dict[str, float]]:
        """Perform one step of gradient descent to minimize MSE loss."""
        y_pred, cache = self.forward(h1_noisy, h0)

        n = len(all_edges)
        loss = sum((y_pred[e] - y_true[e]) ** 2 for e in all_edges) / n

        # Upstream gradient dl / dy_pred
        dl_dy = {e: (2.0 / n) * (y_pred[e] - y_true[e]) for e in all_edges}

        # Parameter gradients
        grad_w_self = sum(dl_dy[e] * cache['m_self'].get(e, 0.0) for e in all_edges)
        grad_w_down = sum(dl_dy[e] * cache['m_down'].get(e, 0.0) for e in all_edges)
        grad_w_up = sum(dl_dy[e] * cache['m_up'].get(e, 0.0) for e in all_edges)
        grad_w_grad = sum(dl_dy[e] * cache['m_grad'].get(e, 0.0) for e in all_edges)

        # Gradient descent update
        self.w_self -= lr * grad_w_self
        self.w_down -= lr * grad_w_down
        self.w_up -= lr * grad_w_up
        self.w_grad -= lr * grad_w_grad

        grads = {
            'w_self': grad_w_self,
            'w_down': grad_w_down,
            'w_up': grad_w_up,
            'w_grad': grad_w_grad,
        }
        return loss, grads


# %% [markdown]
# ## Step 5: Training the Topological Neural Network
#
# We train the `SimplicialConvFilter` over 60 epochs using gradient descent.
# The network simultaneously learns:
# 1. Intra-simplex diffusion along vertex boundaries via $L_1^{\text{down}}$
# 2. Curl propagation around 2-simplex faces via $L_1^{\text{up}}$
# 3. Inter-simplex potential integration from 0-simplices via $B_1^T$

# %%
tnn_model = SimplicialConvFilter(ops, w_self=0.2, w_down=0.05, w_up=0.05, w_grad=0.05)

print('\n' + '=' * 60)
print('4. SIMPLICIAL CONVOLUTION OPTIMIZATION (TRAINING)')
print('=' * 60)

losses: list[float] = []
for epoch in range(1, 61):
    loss, grads = tnn_model.train_step(noisy_flow, node_potential, ground_truth_flow, lr=0.005)
    losses.append(loss)
    if epoch in (1, 10, 25, 40, 60):
        print(
            f'Epoch {epoch:02d} | Loss (MSE): {loss:.5f} | '
            f'Weights: [w_self={tnn_model.w_self:.3f}, w_down={tnn_model.w_down:.3f}, '
            f'w_up={tnn_model.w_up:.3f}, w_grad={tnn_model.w_grad:.3f}]'
        )

# Evaluate recovered flow
recovered_flow, _ = tnn_model.forward(noisy_flow, node_potential)
final_mse = sum((recovered_flow[e] - ground_truth_flow[e]) ** 2 for e in all_edges) / len(all_edges)
print(
    f'\nFinal Recovered Flow MSE: {final_mse:.5f} (Reduced from {initial_mse:.5f}, '
    f'{((initial_mse - final_mse) / initial_mse) * 100:.1f}% error reduction)'
)


# %% [markdown]
# ## Step 6: Helmholtz-Hodge Decomposition Audit
#
# We mathematically audit the quality of the flow before and after TNN processing using
# `algebrax.homology.helmholtz_hodge_decomposition`.
#
# - **Exact Component ($\omega_{\text{exact}} = d_0 \alpha$)**: Gradient / irrotational flow (noise artifacts).
# - **Coexact Component ($\omega_{\text{coexact}} = \delta_2 \beta$)**: Solenoidal / divergence-free rotational flow.
# - **Harmonic Component ($\gamma \in \ker(\Delta_1)$)**: Circulation around the topological hole ($\beta_1$).


# %%
def compute_energy_profile(flow: dict[tuple[int, ...], float]) -> dict[str, float]:
    """Decompose flow via Helmholtz-Hodge and return the energy in each component."""
    decomp = helmholtz_hodge_decomposition(sc, flow)
    exact_energy = sum(v**2 for v in decomp.exact.values())
    coexact_energy = sum(v**2 for v in decomp.coexact.values())
    harmonic_energy = sum(v**2 for v in decomp.harmonic.values())
    total = exact_energy + coexact_energy + harmonic_energy
    return {
        'exact': exact_energy,
        'coexact': coexact_energy,
        'harmonic': harmonic_energy,
        'total': total,
    }


hodge_true = compute_energy_profile(ground_truth_flow)
hodge_noisy = compute_energy_profile(noisy_flow)
hodge_recovered = compute_energy_profile(recovered_flow)

print('\n' + '=' * 60)
print('5. HELMHOLTZ-HODGE TOPOLOGICAL DECOMPOSITION AUDIT')
print('=' * 60)
print(f'{"Component":<15} | {"Ground Truth":<14} | {"Noisy Observed":<14} | {"TNN Recovered":<14}')
print('-' * 65)
for comp in ('exact', 'coexact', 'harmonic', 'total'):
    print(
        f'{comp.capitalize():<15} | '
        f'{hodge_true[comp]:<14.4f} | '
        f'{hodge_noisy[comp]:<14.4f} | '
        f'{hodge_recovered[comp]:<14.4f}'
    )


# %% [markdown]
# ## Step 7: Ablation Study — Why the Upper Laplacian ($L_1^{\text{up}}$) is Essential
#
# Standard GNNs only pass information along shared vertices ($L_1^{\text{down}}$).
# What happens if we ablate $L_1^{\text{up}}$ ($w_{\text{up}} = 0$)?
#
# Without $L_1^{\text{up}}$, the network is blind to 2-simplex circulation (faces),
# failing to reconstruct the divergence-free circulation across triangles.

# %%
# Ablated Model without 2D face message passing (L1_up disabled)
ablated_model = SimplicialConvFilter(ops, w_self=0.2, w_down=0.05, w_up=0.0, w_grad=0.05)

for _ in range(60):
    # Train only w_self, w_down, and w_grad
    ablated_model.w_up = 0.0  # Force zero
    loss, grads = ablated_model.train_step(noisy_flow, node_potential, ground_truth_flow, lr=0.005)
    ablated_model.w_up = 0.0

ablated_flow, _ = ablated_model.forward(noisy_flow, node_potential)
ablated_mse = sum((ablated_flow[e] - ground_truth_flow[e]) ** 2 for e in all_edges) / len(all_edges)

print('\n' + '=' * 60)
print('6. ABLATION STUDY: TOPOLOGICAL EXPRESSIVITY')
print('=' * 60)
print(f'Full TNN (with L1_down + L1_up) MSE : {final_mse:.5f}')
print(f'Ablated GNN (without L1_up)    MSE : {ablated_mse:.5f}')
advantage = ((ablated_mse - final_mse) / ablated_mse) * 100
print(f'Topological 2-Simplex Advantage     : {advantage:.1f}% lower error with Simplicial 2-Faces!')
print('=' * 60)
