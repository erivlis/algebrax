# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Control Theory, State-Space Systems & Dynamical Stability Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Discrete State-Space System Matrix Powers (algebrax.matrix.core.power & ax.matrix.dot):
   Discrete state-space dynamics x[k+1] = A * x[k] + B * u[k] propagate over time.
   Matrix powers A^k compute the autonomous multi-step state transition matrix.

2. Z-Transform Transfer Functions (algebrax.transforms.z_transform):
   The Z-transform maps impulse response sequences h[n] into discrete-time
   frequency transfer functions H(z) = sum_{n} h[n] z^{-n}.

3. Characteristic Matrix Invariants & Stability (algebrax.matrix.academic.determinant):
   Evaluating system matrix determinants det(sI - A) audits characteristic polynomial
   roots and dynamical stability.
================================================================================
"""

import cmath

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Control Theory, State-Space Systems & Dynamical Stability')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to evaluate discrete')
    print('      state transition powers A^k, Z-transform transfer functions H(z),')
    print('      and characteristic matrix determinants.')

    # --- Step 1: Discrete State-Space Transition Matrix (A^k) ---
    print('\n[Step 1] Discrete State Transition Dynamics (A^k)...')
    print('Explanation: A^k computes multi-step autonomous state propagation x[k] = A^k * x[0].')

    # 2x2 State-Space Dynamics Matrix A (Position x1, Velocity x2)
    # x1[k+1] = 0.9 * x1[k] + 0.2 * x2[k]
    # x2[k+1] = -0.1 * x1[k] + 0.8 * x2[k]
    a_matrix = {
        0: {0: 0.9, 1: 0.2},
        1: {0: -0.1, 1: 0.8},
    }

    # Initial state vector x[0] = [10.0, 0.0] (Initial displacement)
    initial_state = {0: 10.0, 1: 0.0}

    print('\nSystem Dynamics Matrix A:')
    for r in sorted(a_matrix.keys()):
        print(f'  Row {r}: {a_matrix[r]}')

    print('\nState Trajectory over Multi-Step Transitions:')
    for k in [1, 2, 5, 10]:
        a_k = ax.matrix.power(a_matrix, k)
        # x[k] = A^k * x[0]
        x1_k = a_k[0].get(0, 0.0) * initial_state[0] + a_k[0].get(1, 0.0) * initial_state[1]
        x2_k = a_k[1].get(0, 0.0) * initial_state[0] + a_k[1].get(1, 0.0) * initial_state[1]
        print(f'  Step k={k:2d}: Position x1 = {x1_k:6.3f}, Velocity x2 = {x2_k:6.3f}')

    # --- Step 2: Impulse Response Z-Transform Transfer Function H(z) ---
    print('\n[Step 2] Impulse Response Z-Transform Transfer Function (ax.transforms.z_transform)...')
    print('Explanation: H(z) = sum_{n} h[n] z^{-n} maps discrete impulse response to Z-domain.')

    # Discrete impulse response sequence h[n]
    impulse_response = {0: 1.0, 1: 0.5, 2: 0.25, 3: 0.125, 4: 0.0625}

    # Evaluate H(z) at complex z = 0.8 + 0.6j
    z_eval = 0.8 + 0.6j
    h_z = ax.transforms.z_transform(impulse_response, z=z_eval)

    print('\nImpulse Response Sequence h[n]:', impulse_response)
    print(f'Transfer Function H(z = {z_eval}): {h_z:.4f} (Magnitude = {abs(h_z):.4f})')

    # --- Step 3: Characteristic Determinant & Stability Audit ---
    print('\n[Step 3] Characteristic Matrix Stability Audit (ax.matrix.determinant)...')
    print('Explanation: det(I - A) audits discrete pole locations and asymptotic stability.')

    # Characteristic Matrix (I - A)
    char_matrix = {
        0: {0: 1.0 - 0.9, 1: -0.2},
        1: {0: 0.1, 1: 1.0 - 0.8},
    }

    det_char = ax.matrix.academic.determinant(char_matrix)

    print('\nCharacteristic Matrix (I - A):')
    for r in sorted(char_matrix.keys()):
        print(f'  Row {r}: {char_matrix[r]}')

    print(f'\nCharacteristic Determinant det(I - A): {det_char:.4f}')
    is_stable = det_char > 0
    print(f'Asymptotic Stability Audit: {"STABLE SYSTEM" if is_stable else "UNSTABLE SYSTEM"}')

    print('\n==========================================================================')
    print('Use Case Completed: Control Theory & State-Space Systems Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
