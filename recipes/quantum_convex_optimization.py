# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Quantum Spin-Chain State & Convex Optimization Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Fenchel-Legendre Convex Conjugate (algebrax.transforms.legendre_fenchel):
   The Legendre-Fenchel transform f*(s) = sup_x { s * x - f(x) } computes the dual
   convex conjugate. In statistical thermodynamics and optimization, this maps energy
   landscapes to dual Helmholtz free energy conjugate functions.

2. Composite Quantum Spin Tensors (algebrax.matrix.core.block_diag & ax.matrix.trace):
   - Block Diagonal Product (ax.matrix.block_diag([H1, H2])): Constructs direct sum composite
     spin Hamiltonians H = H1 (+) H2 for decoupled quantum subsystems.
   - Trace Tr(H) = sum_i H_ii: Computes quantum expectation invariant ax.matrix.trace sums.

3. Probabilistic Quantum State Transition Automaton (algebrax.automata.simulate_nfa):
   `ax.automata.simulate_nfa` simulates non-deterministic and probabilistic state transitions over
   superposition channels (e.g. ground state -> excited state -> decay).
================================================================================
"""

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Quantum Spin-Chain State & Convex Optimization')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to evaluate Fenchel-Legendre')
    print('      convex conjugates, ax.matrix.block diagonal Hamiltonians, and NFA probabilistic transitions.')

    # --- Step 1: Fenchel-Legendre Convex Conjugate ---
    print('\n[Step 1] Fenchel-Legendre Convex Conjugate (ax.transforms.legendre_fenchel)...')
    print('Explanation: Computes dual conjugate energy f*(s) = sup_x { s * x - f(x) }')
    print('             for convex quadratic cost function f(x) = 0.5 * x^2.')

    convex_signal = {x: 0.5 * (x**2) for x in range(-5, 6)}
    print(f'Primal Function Sample f(x): {convex_signal}')

    slopes = [-2.0, -1.0, 0.0, 1.0, 2.0]
    print('\nLegendre-Fenchel Dual Conjugate Values f*(s):')
    for s in slopes:
        f_star_s = ax.transforms.legendre_fenchel(convex_signal, slope=s)
        print(f'  Slope s = {s:+4.1f} -> Dual Conjugate f*(s) = {f_star_s:6.2f}')

    # --- Step 2: Block Diagonal Spin Hamiltonian & Matrix Trace ---
    print('\n[Step 2] Multi-Qubit Block Diagonal Hamiltonian & Trace (ax.matrix.block_diag & ax.matrix.trace)...')
    print('Explanation: Computes decoupled block diagonal Hamiltonian H = H1 (+) H2 and matrix trace Tr(H).')

    # Subsystem Hamiltonians
    h1 = {0: {0: 1.0, 1: 0.5}, 1: {0: 0.5, 1: -1.0}}
    h2 = {0: {0: 2.0, 1: 0.1}, 1: {0: 0.1, 1: -2.0}}

    composite_hamiltonian = ax.matrix.core.block_diag([h1, h2])
    tr_h = ax.matrix.trace(composite_hamiltonian)

    print('\nSubsystem H1 Matrix:')
    for r in sorted(h1.keys()):
        print(f'  Row {r}: {h1[r]}')

    print('\nSubsystem H2 Matrix:')
    for r in sorted(h2.keys()):
        print(f'  Row {r}: {h2[r]}')

    print('\nComposite Block Diagonal Matrix H = H1 (+) H2:')
    for r in sorted(composite_hamiltonian.keys()):
        print(f'  Row {r}: {composite_hamiltonian[r]}')

    print(f'\nComposite Hamiltonian Trace Tr(H): {tr_h:.2f}')

    # --- Step 3: Probabilistic State Machine Simulation (NFA) ---
    print('\n[Step 3] Probabilistic Quantum Decay Automaton (ax.automata.simulate_nfa)...')
    print('Explanation: Simulates NFA state transitions over superposition channels.')

    quantum_nfa = {
        0: {'pulse': {0: 0.5, 1: 0.5}},  # 50% chance to excite
        1: {'pulse': {1: 0.7, 2: 0.3}},  # 30% chance to decay
        2: {'pulse': {2: 1.0}},  # Decay sink
    }

    start_distribution = {0: 1.0}
    pulse_sequence = ['pulse', 'pulse', 'pulse']

    final_distribution = ax.automata.simulate_nfa(start_distribution, pulse_sequence, quantum_nfa)

    print('\nInitial State Distribution: ', start_distribution)
    print('Applied Pulse Sequence:     ', pulse_sequence)
    print('Final State Probability Distribution:')
    for state, prob in sorted(final_distribution.items()):
        labels = {0: '|0> Ground', 1: '|1> Excited', 2: '|d> Decayed'}
        print(f'  State {state} [{labels[state]}]: {prob * 100:.2f}%')

    print('\n==========================================================================')
    print('Use Case Completed: Quantum Spin-Chain & Convex Optimization Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
