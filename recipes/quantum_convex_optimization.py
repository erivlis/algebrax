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
# # Quantum Spin-Chain State & Convex Optimization
#
# ## Theory & Mathematical Foundation
#
# 1. **Fenchel-Legendre Convex Conjugate (`algebrax.transforms.legendre_fenchel`)**:
#    The Legendre-Fenchel transform $f^*(s) = \sup_x \{ s x - f(x) \}$ computes the
#    dual convex conjugate mapping energy landscapes to dual Helmholtz free energy conjugate functions.
#
# 2. **Composite Quantum Spin Tensors (`ax.matrix.core.block_diag` & `ax.matrix.trace`)**:
#    - **Block Diagonal Product** (`block_diag([H1, H2])`): Constructs direct sum
#      composite spin Hamiltonians $H = H_1 \oplus H_2$ for decoupled quantum subsystems.
#    - **Trace** ($\text{Tr}(H) = \sum_i H_{ii}$): Computes quantum expectation invariant trace sums.
#
# 3. **Probabilistic Quantum State Transition Automaton (`algebrax.automata.simulate_nfa`)**:
#    `simulate_nfa` simulates non-deterministic and probabilistic state transitions over superposition channels.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Fenchel-Legendre Convex Conjugate (`legendre_fenchel`)
# Computes dual conjugate energy $f^*(s) = \sup_x \{ s x - f(x) \}$ for convex quadratic cost function $f(x) = 0.5 x^2$.

# %%
convex_signal = {x: 0.5 * (x**2) for x in range(-5, 6)}
print(f"Primal Function Sample f(x): {convex_signal}")

slopes = [-2.0, -1.0, 0.0, 1.0, 2.0]
print("\nLegendre-Fenchel Dual Conjugate Values f*(s):")
for s in slopes:
    f_star_s = ax.transforms.legendre_fenchel(convex_signal, slope=s)
    print(f"  Slope s = {s:+4.1f} -> Dual Conjugate f*(s) = {f_star_s:6.2f}")

# %% [markdown]
# ## Step 2: Multi-Qubit Block Diagonal Hamiltonian & Trace (`block_diag` & `trace`)
# Computes decoupled block diagonal Hamiltonian $H = H_1 \oplus H_2$ and matrix trace $\text{Tr}(H)$.

# %%
h1 = {0: {0: 1.0, 1: 0.5}, 1: {0: 0.5, 1: -1.0}}
h2 = {0: {0: 2.0, 1: 0.1}, 1: {0: 0.1, 1: -2.0}}

composite_hamiltonian = ax.matrix.core.block_diag([h1, h2])
tr_h = ax.matrix.trace(composite_hamiltonian)

print("\nSubsystem H1 Matrix:")
for r in sorted(h1.keys()):
    print(f"  Row {r}: {h1[r]}")

print("\nSubsystem H2 Matrix:")
for r in sorted(h2.keys()):
    print(f"  Row {r}: {h2[r]}")

print("\nComposite Block Diagonal Matrix H = H1 (+) H2:")
for r in sorted(composite_hamiltonian.keys()):
    print(f"  Row {r}: {composite_hamiltonian[r]}")

print(f"\nComposite Hamiltonian Trace Tr(H): {tr_h:.2f}")

# %% [markdown]
# ## Step 3: Probabilistic Quantum Decay Automaton (`simulate_nfa`)

# %%
quantum_nfa = {
    0: {"pulse": {0: 0.5, 1: 0.5}},
    1: {"pulse": {1: 0.7, 2: 0.3}},
    2: {"pulse": {2: 1.0}},
}

start_distribution = {0: 1.0}
pulse_sequence = ["pulse", "pulse", "pulse"]

final_distribution = ax.automata.simulate_nfa(start_distribution, pulse_sequence, quantum_nfa)

print("\nInitial State Distribution: ", start_distribution)
print("Applied Pulse Sequence:     ", pulse_sequence)
print("Final State Probability Distribution:")
for state, prob in sorted(final_distribution.items()):
    labels = {0: "|0> Ground", 1: "|1> Excited", 2: "|d> Decayed"}
    print(f"  State {state} [{labels[state]}]: {prob * 100:.2f}%")


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Quantum Spin-Chain Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
