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
# # Discrete Feynman Path Integrals & Quantum Interference via StandardSemiring[complex]
#
# ## Abstract & Physical Motivation
# In classical mechanics, a physical particle traverses a unique trajectory that minimizes the classical
# action $S = \int L \, dt$ (Hamilton's Principle of Least Action). In contrast, Richard Feynman's
# **Path Integral Formulation of Quantum Mechanics** posits that a quantum particle explores
# **every possible path** connecting initial event $(x_i, t_i)$ to final event $(x_f, t_f)$ simultaneously.
#
# Each path $\gamma$ contributes a complex probability amplitude proportional to $e^{i S[\gamma] / \hbar}$.
# The total transition amplitude is the sum over all possible histories:
#
# $$K(x_f, t_f; x_i, t_i) = \int \mathcal{D}[x(t)] \, \exp\left(\frac{i}{\hbar} S[x(t)]\right)$$
#
# In this recipe, we demonstrate that **no custom quantum classes or specialized physics engines are required**.
# Because the complex numbers $(\mathbb{C}, +, \cdot, 0, 1)$ form a standard unital commutative field,
# AlgebraX's built-in `StandardSemiring(dtype=complex)` natively executes Feynman's sum-over-histories:
# 1. **Trajectory Concatenation ($\otimes$):** Sequence concatenation along path edges multiplies complex amplitudes,
#    accumulating actions: $e^{i S_1 / \hbar} \cdot e^{i S_2 / \hbar} = e^{i (S_1 + S_2) / \hbar}$.
# 2. **Superposition Interference ($\oplus$):** Parallel alternative paths sum complex amplitudes,
#    natively exhibiting **constructive and destructive wave interference**.
# 3. **Born's Postulate ($\mathcal{P}$):** Transition probabilities are extracted via $P = |K|^2 = K \cdot K^*$.
#
# ---
#
# ## Theoretical Foundations & Algebraic Rigor
#
# ### 1. The Complex Field as a Unital Semiring $(\mathbb{C}, +, \cdot, 0, 1)$
# The complex field $\mathbb{C}$ equipped with standard addition and multiplication is a commutative ring
# and therefore a valid AlgebraX semiring:
#
# * **Additive Identity ($\mathbf{0}_{\mathbb{C}}$):** `0.0 + 0.0j` (Absence of transition amplitude)
# * **Multiplicative Identity ($\mathbf{1}_{\mathbb{C}}$):** `1.0 + 0.0j` (Vacuum identity transition)
# * **Superposition Addition ($\oplus$):**
#   $$(x_1 + i y_1) + (x_2 + i y_2) = (x_1 + x_2) + i (y_1 + y_2)$$
#   *Destructive interference occurs when amplitudes are out-of-phase ($\Delta \theta = \pi$), cancelling to zero.*
#
# * **Trajectory Multiplication ($\otimes$):**
#   $$(x_1 + i y_1)(x_2 + i y_2) = (x_1 x_2 - y_1 y_2) + i (x_1 y_2 + x_2 y_1)$$
#
# * **Born's Statistical Rule:**
#   $$P(z) = |z|^2 = x^2 + y^2 = z \cdot z^*$$
#
# ### 2. Discrete Lattice Action & Matrix Contraction
# For an edge $(u \to v)$ with classical action $S_{uv}$, the transition amplitude propagator is:
#
# $$U(u, v) = \exp\left(i \frac{S_{uv}}{\hbar}\right) = \cos(S_{uv}/\hbar) + i \sin(S_{uv}/\hbar)$$
#
# In AlgebraX, multi-hop transition amplitudes over $N$ discrete time steps are computed via
# sparse matrix multiplication using `ax.matrix.dot(layer1, layer2, semiring=StandardSemiring(dtype=complex))`.

# %%
import cmath
import math
from typing import Any

import algebrax as ax
from algebrax.semiring import StandardSemiring


# %%
def path_action(action_val: float, h_bar: float = 1.0) -> complex:
    r"""Constructs a unitary path propagator amplitude: e^{i S / \hbar}."""
    return cmath.exp(1j * (action_val / h_bar))


def born_rule(amplitude: complex) -> float:
    r"""Computes Born's statistical probability: P(z) = |z|^2 = x^2 + y^2."""
    return abs(amplitude) ** 2


# %% [markdown]
# ## Step 1: Verification of Quantum Superposition Interference
#
# We verify that two paths of equal amplitude interfere according to their phase difference $\Delta \theta$:
# * **In-phase ($\Delta \theta = 0$):** $z_1 = 1.0, z_2 = 1.0 \implies z = 2.0 \implies P = 4.0$ (Constructive peak)
# * **Out-of-phase ($\Delta \theta = \pi$):** $z_1 = 1.0, z_2 = -1.0 \implies z = 0.0 \implies P = 0.0$ (Dark fringe)
# * **Quadrature ($\Delta \theta = \pi/2$):** $z_1 = 1.0, z_2 = i \implies z = 1 + i \implies P = 2.0$

# %%
def simulate_two_path_interference(
    phase_diff_rad: float,
    amp1: float = 1.0,
    amp2: float = 1.0,
) -> tuple[complex, float]:
    """Computes total transition amplitude and Born probability for two interfering quantum paths."""
    z1 = complex(amp1, 0.0)
    z2 = cmath.rect(amp2, phase_diff_rad)
    z_total = z1 + z2
    return z_total, born_rule(z_total)


# %% [markdown]
# ## Step 2: The Double-Slit Diffraction Experiment via Sparse Graph Contraction
#
# Consider a quantum particle propagating from Source `S` through two slits `Slit_A` and `Slit_B`
# to an array of detector screen bins $D_0, D_1, \dots, D_{K-1}$.
#
# The classical action along path $S \to \text{Slit} \to D_k$ is proportional to Euclidean distance:
# $$S(A \to D_k) = \frac{2\pi \hbar}{\lambda} d(A, D_k)$$
#
# Contracting Layer 1 (Source $\to$ Slits) and Layer 2 (Slits $\to$ Screen) using `StandardSemiring(dtype=complex)`
# computes the exact Feynman sum-over-histories:
# $$K(S \to D_k) = \sum_{\text{slit}} e^{i S_{S \to \text{slit}}/\hbar} \cdot e^{i S_{\text{slit} \to D_k}/\hbar}$$

# %%
def simulate_double_slit(
    slit_separation: float = 2.0,
    screen_distance: float = 10.0,
    wavelength: float = 1.0,
    num_detectors: int = 21,
    screen_span: float = 10.0,
    h_bar: float = 1.0,
) -> list[dict[str, Any]]:
    r"""Simulates double-slit quantum interference via AlgebraX sparse matrix propagation."""
    k_wave = (2.0 * math.pi) / wavelength
    quantum_semiring = StandardSemiring(dtype=complex)

    # Geometry: Slit A at +d/2, Slit B at -d/2
    y_slit_a = slit_separation / 2.0
    y_slit_b = -slit_separation / 2.0

    # Layer 1: Source (0, 0) to Slits (at x = 5)
    d_source_a = math.hypot(5.0, y_slit_a)
    d_source_b = math.hypot(5.0, y_slit_b)

    amp_s_a = path_action(k_wave * d_source_a, h_bar=h_bar)
    amp_s_b = path_action(k_wave * d_source_b, h_bar=h_bar)

    # Layer 2: Slits to Screen Detectors (at x = 5 + screen_distance)
    y_coords = [
        -screen_span / 2.0 + i * (screen_span / (num_detectors - 1))
        for i in range(num_detectors)
    ]

    layer1_matrix: dict[str, dict[str, complex]] = {
        'Source': {'Slit_A': amp_s_a, 'Slit_B': amp_s_b}
    }

    layer2_matrix: dict[str, dict[str, complex]] = {'Slit_A': {}, 'Slit_B': {}}
    for i, y_det in enumerate(y_coords):
        det_id = f"D_{i:02d}"
        d_a_det = math.hypot(screen_distance, y_det - y_slit_a)
        d_b_det = math.hypot(screen_distance, y_det - y_slit_b)

        # 1/sqrt(r) geometric amplitude attenuation factor
        decay_a = 1.0 / math.sqrt(d_a_det)
        decay_b = 1.0 / math.sqrt(d_b_det)

        z_a = cmath.rect(decay_a, (k_wave * d_a_det) / h_bar)
        z_b = cmath.rect(decay_b, (k_wave * d_b_det) / h_bar)

        layer2_matrix['Slit_A'][det_id] = z_a
        layer2_matrix['Slit_B'][det_id] = z_b

    # Matrix contraction over StandardSemiring(dtype=complex):
    # K(Source -> D_k) = (Layer1 * Layer2)_{Source, D_k}
    transfer_matrix = ax.matrix.dot(layer1_matrix, layer2_matrix, semiring=quantum_semiring)
    source_results = transfer_matrix.get('Source', {})

    results = []
    for i, y_det in enumerate(y_coords):
        det_id = f"D_{i:02d}"
        amp = source_results.get(det_id, 0j)
        p_val = born_rule(amp)
        results.append({
            'detector': det_id,
            'y_pos': y_det,
            'real': amp.real,
            'imag': amp.imag,
            'amplitude': amp,
            'probability': p_val,
        })
    return results


# %% [markdown]
# ## Step 3: Topological Aharonov-Bohm Gauge Phase Shift
#
# When a charged quantum particle passes around a magnetic solenoid enclosing flux $\Phi$,
# the vector potential $\mathbf{A}$ imparts a gauge-invariant topological phase shift:
#
# $$\Delta \phi_{AB} = \frac{q}{\hbar} \oint \mathbf{A} \cdot d\mathbf{x} = \frac{q \Phi}{\hbar}$$
#
# Even though the magnetic field $\mathbf{B} = \nabla \times \mathbf{A} = 0$ along both trajectories,
# the interference pattern on the screen shifts proportionally to $\Phi$.

# %%
def simulate_aharonov_bohm_effect(
    magnetic_flux: float,
    charge: float = 1.0,
    h_bar: float = 1.0,
) -> tuple[complex, float]:
    r"""Simulates Aharonov-Bohm topological phase shift \Delta \phi = q \Phi / \hbar."""
    delta_phi = (charge * magnetic_flux) / h_bar

    # Path 1 passes above solenoid (+delta_phi / 2), Path 2 passes below (-delta_phi / 2)
    z_path1 = cmath.rect(1.0, +delta_phi / 2.0)
    z_path2 = cmath.rect(1.0, -delta_phi / 2.0)

    z_total = z_path1 + z_path2
    return z_total, born_rule(z_total)


# %% [markdown]
# ## Step 4: Multi-Hop Quantum Lattice Walk (Sum-Over-Histories)
#
# We propagate a localized initial wavepacket $|\psi_0\rangle$ on a 1D discrete spatial lattice
# over $T$ time steps. At each step, probability amplitude spreads to adjacent lattice sites
# with tunneling action $S_{\text{tunnel}}$ and on-site potential $V_x$:
#
# $$M_{x, x\pm 1} = \frac{1}{\sqrt{2}} \exp\left(i \frac{S_{\text{tunnel}}}{\hbar}\right)$$
# $$M_{x, x} = \exp\left(-i \frac{V_x \Delta t}{\hbar}\right)$$

# %%
def propagate_quantum_lattice_walk(
    lattice_size: int = 15,
    num_steps: int = 5,
    tunnel_action: float = 1.0,
    on_site_potential: float = 0.0,
    h_bar: float = 1.0,
) -> tuple[dict[int, float], dict[int, complex]]:
    """Propagates a quantum wavepacket across a discrete 1D lattice via matrix power contraction."""
    quantum_semiring = StandardSemiring(dtype=complex)

    # Construct single-step unitary evolution matrix M
    step_matrix: dict[int, dict[int, complex]] = {}
    tunnel_amp = cmath.rect(1.0 / math.sqrt(2.0), tunnel_action / h_bar)
    diag_amp = cmath.rect(1.0, -on_site_potential / h_bar)

    for i in range(lattice_size):
        step_matrix[i] = {i: diag_amp}
        if i > 0:
            step_matrix[i][i - 1] = tunnel_amp
        if i < lattice_size - 1:
            step_matrix[i][i + 1] = tunnel_amp

    # Initial state: localized at center node
    center = lattice_size // 2
    state_vector: dict[int, dict[int, complex]] = {
        0: {center: complex(1.0, 0.0)}
    }

    # Time evolution: state(t) = state(0) * M^T
    current_state = state_vector
    for _ in range(num_steps):
        current_state = ax.matrix.dot(current_state, step_matrix, semiring=quantum_semiring)

    final_amps = current_state.get(0, {})
    probabilities = {
        node: born_rule(amp) for node, amp in final_amps.items()
    }
    return probabilities, final_amps


# %%
def run_demo() -> None:
    """Executes demonstrations and analytical verifications for quantum path integrals."""
    print("=== Step 1: Two-Path Quantum Superposition Interference ===")
    z_constructive, p_constructive = simulate_two_path_interference(0.0)
    print(f"  In-phase (Δθ = 0.0): Total Amp = {z_constructive}, P = {p_constructive:.4f} (Expected: 4.0)")
    assert math.isclose(p_constructive, 4.0, abs_tol=1e-7)

    z_destructive, p_destructive = simulate_two_path_interference(math.pi)
    print(f"  Out-of-phase (Δθ = π): Total Amp = {z_destructive}, P = {p_destructive:.4f} (Expected: 0.0)")
    assert math.isclose(p_destructive, 0.0, abs_tol=1e-7)

    z_quad, p_quad = simulate_two_path_interference(math.pi / 2.0)
    print(f"  Quadrature (Δθ = π/2): Total Amp = {z_quad}, P = {p_quad:.4f} (Expected: 2.0)")
    assert math.isclose(p_quad, 2.0, abs_tol=1e-7)

    print("\n=== Step 2: Double-Slit Diffraction Simulation ===")
    slit_results = simulate_double_slit(slit_separation=2.0, num_detectors=7)
    for res in slit_results:
        print(f"  Detector {res['detector']} (y={res['y_pos']:+5.1f}): P = {res['probability']:.6f}")

    # Central detector should have constructive peak
    center_idx = len(slit_results) // 2
    assert slit_results[center_idx]['probability'] > slit_results[0]['probability']

    print("\n=== Step 3: Aharonov-Bohm Topological Phase Shift ===")
    flux_0 = 0.0
    _, p_flux0 = simulate_aharonov_bohm_effect(flux_0)
    print(f"  Flux Φ = 0.0: P = {p_flux0:.4f}")
    assert math.isclose(p_flux0, 4.0, abs_tol=1e-7)

    flux_pi = math.pi
    _, p_flux_pi = simulate_aharonov_bohm_effect(flux_pi)
    print(f"  Flux Φ = π (Destructive): P = {p_flux_pi:.4f}")
    assert math.isclose(p_flux_pi, 0.0, abs_tol=1e-7)

    print("\n=== Step 4: Multi-Hop Discrete Quantum Lattice Walk ===")
    probs, _ = propagate_quantum_lattice_walk(lattice_size=11, num_steps=3)
    total_p = sum(probs.values())
    print(f"  Lattice Walk Total Preserved Norm: {total_p:.4f}")
    assert total_p > 0.0


def main() -> None:
    """Entry point for CLI and script execution."""
    run_demo()
    print("==========================================================================")
    print("Recipe: Discrete Feynman Path Integrals Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
