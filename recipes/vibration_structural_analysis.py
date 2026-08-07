# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Vibration Structural Analysis & Signal Processing Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Permutation Symmetries (algebrax.group.compose & ax.group.signature):
   Permutation mappings represent spatial rotations and reflections of multi-rotor
   turbine systems. Composing permutations (P2 o P1) models sequential rotation,
   while `ax.group.signature(P)` computes parity (+1 for even rotations, -1 for reflections).

2. Structural Resonant Determinants (algebrax.matrix.academic.determinant):
   The ax.matrix.determinant det(K - omega^2 M) of the structural stiffness and mass matrix
   vanishes (det = 0) at characteristic resonant frequencies.

3. Analytic Signal Envelope (algebrax.transforms.hilbert):
   The Hilbert transform H{x[n]} forms an analytic signal a[n] = x[n] + j H{x[n]}.
   The magnitude |a[n]| represents the instantaneous amplitude envelope, isolating
   vibration spikes and structural fatigue in noisy sensor data.
================================================================================
"""

import math

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Vibration Structural Analysis & Signal Processing')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to model turbine')
    print('      rotor symmetries, compute stiffness determinants, and extract Hilbert envelopes.')

    # --- Step 1: Permutation Symmetries (Group Theory) ---
    print('\n[Step 1] Turbine Rotor Permutation Symmetries (Group Theory)...')
    print('Explanation: Permutations model physical rotations (r) and reflections (s)')
    print('             across a 4-rotor turbine. Composing permutations tracks total motion.')

    # 4-Rotor System: nodes {0, 1, 2, 3}
    rot_90 = {0: 1, 1: 2, 2: 3, 3: 0}  # 90 degree counter-clockwise rotation
    flip_h = {0: 1, 1: 0, 2: 3, 3: 2}  # Horizontal reflection

    combined_motion = ax.group.compose(rot_90, flip_h)

    print(f'90° Rotation Permutation (r): {rot_90} [Parity sgn: {ax.group.signature(rot_90):+d}]')
    print(f'Horizontal Flip Permutation (s): {flip_h} [Parity sgn: {ax.group.signature(flip_h):+d}]')
    print(f'Combined Motion (s o r):        {combined_motion} [Parity sgn: {ax.group.signature(combined_motion):+d}]')

    # --- Step 2: Structural Coupling Matrix Determinant ---
    print('\n[Step 2] Structural Stiffness Coupling Determinant (ax.matrix.determinant)...')
    print('Explanation: The ax.matrix.determinant det(K) of the stiffness matrix indicates structural')
    print('             rigidity and detects singular (unconstrained) mechanical modes.')

    # 3x3 Mechanical Stiffness Coupling Matrix K
    stiffness_matrix = {
        0: {0: 4.0, 1: -2.0, 2: 0.0},
        1: {0: -2.0, 1: 5.0, 2: -3.0},
        2: {0: 0.0, 1: -3.0, 2: 4.0},
    }

    det_k = ax.matrix.academic.determinant(stiffness_matrix)
    print('\nStiffness Matrix K:')
    for r in sorted(stiffness_matrix.keys()):
        print(f'  Row {r}: {stiffness_matrix[r]}')

    print(f'\nSystem Stiffness Determinant det(K): {det_k:.2f}')
    if det_k > 0:
        print('Status: STABLE RIGID STRUCTURE (Non-singular, det(K) > 0)')
    else:
        print('Status: WARNING - SINGULAR UNCONSTRAINED STRUCTURE (det(K) = 0)')

    # --- Step 3: Hilbert Transform Instantaneous Amplitude Envelope ---
    print('\n[Step 3] Instantaneous Vibration Envelope Extraction (ax.transforms.hilbert)...')
    print('Explanation: Computes the Hilbert transform H{x[n]} to construct analytic signal')
    print('             a[n] = x[n] + j H{x[n]} and extract amplitude envelope |a[n]|.')

    # Synthetic 16-sample vibration signal with a transient burst spike at sample 8
    n_samples = 16
    raw_vibration = {i: math.sin(2 * math.pi * i / 4) * (3.0 if 6 <= i <= 10 else 1.0) for i in range(n_samples)}

    analytic_signal = ax.transforms.hilbert(raw_vibration, n=n_samples)

    print('\nVibration Sensor Signal & Instantaneous Envelope:')
    print('  Index | Raw Signal x[n] | Analytic Envelope |a[n]|')
    print('  -----------------------------------------------')
    for i in range(n_samples):
        raw_val = raw_vibration.get(i, 0.0)
        complex_val = analytic_signal.get(i, 0j)
        envelope_mag = abs(complex_val)
        tag = ' <== TRANSIENT BURST SPIKE' if envelope_mag > 2.0 else ''
        print(f'  {i:5d} | {raw_val:14.4f} | {envelope_mag:20.4f}{tag}')

    print('\n==========================================================================')
    print('Use Case Completed: Vibration Structural Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
