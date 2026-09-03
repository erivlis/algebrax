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
# # Control Theory, State-Space Systems & Dynamical Stability
#
# ## Theory & Mathematical Foundation
#
# 1. **Discrete State-Space System Matrix Powers (`ax.matrix.power` & `ax.matrix.dot`)**:
#    Discrete state-space dynamics $x[k+1] = A x[k] + B u[k]$ propagate over time.
#    Matrix powers $A^k$ compute the autonomous multi-step state transition matrix.
#
# 2. **Z-Transform Transfer Functions (`algebrax.transforms.z_transform`)**:
#    The Z-transform maps impulse response sequences $h[n]$ into discrete-time
#    frequency transfer functions $H(z) = \sum_n h[n] z^{-n}$.
#
# 3. **Characteristic Matrix Invariants & Stability (`algebrax.matrix.academic.determinant`)**:
#    Evaluating system matrix determinants $\det(sI - A)$ audits characteristic polynomial
#    roots and dynamical stability.

# %%
import cmath

import algebrax as ax

# %% [markdown]
# ## Step 1: Discrete State Transition Dynamics ($A^k$)
# $A^k$ computes multi-step autonomous state propagation $x[k] = A^k x[0]$.

# %%
a_matrix = {
    0: {0: 0.9, 1: 0.2},
    1: {0: -0.1, 1: 0.8},
}

initial_state = {0: 10.0, 1: 0.0}

print('System Dynamics Matrix A:')
for r in sorted(a_matrix.keys()):
    print(f'  Row {r}: {a_matrix[r]}')

print('\nState Trajectory over Multi-Step Transitions:')
for k in [1, 2, 5, 10]:
    a_k = ax.matrix.power(a_matrix, k)
    x1_k = a_k[0].get(0, 0.0) * initial_state[0] + a_k[0].get(1, 0.0) * initial_state[1]
    x2_k = a_k[1].get(0, 0.0) * initial_state[0] + a_k[1].get(1, 0.0) * initial_state[1]
    print(f'  Step k={k:2d}: Position x1 = {x1_k:6.3f}, Velocity x2 = {x2_k:6.3f}')

# %% [markdown]
# ## Step 2: Impulse Response Z-Transform Transfer Function $H(z)$ (`z_transform`)
# $H(z) = \sum_n h[n] z^{-n}$ maps discrete impulse response to the Z-domain.

# %%
impulse_response = {0: 1.0, 1: 0.5, 2: 0.25, 3: 0.125, 4: 0.0625}

z_eval = 0.8 + 0.6j
h_z = ax.transforms.z_transform(impulse_response, z=z_eval)

print('Impulse Response Sequence h[n]:', impulse_response)
print(f'Transfer Function H(z = {z_eval}): {h_z:.4f} (Magnitude = {abs(h_z):.4f})')

# %% [markdown]
# ## Step 3: Characteristic Matrix Stability Audit (`ax.matrix.determinant`)
# $\det(I - A)$ audits discrete pole locations and asymptotic stability.

# %%
char_matrix = {
    0: {0: 1.0 - 0.9, 1: -0.2},
    1: {0: 0.1, 1: 1.0 - 0.8},
}

det_char = ax.matrix.academic.determinant(char_matrix)

print('Characteristic Matrix (I - A):')
for r in sorted(char_matrix.keys()):
    print(f'  Row {r}: {char_matrix[r]}')

print(f'\nCharacteristic Determinant det(I - A): {det_char:.4f}')
is_stable = det_char > 0
print(f'Asymptotic Stability Audit: {"STABLE SYSTEM" if is_stable else "UNSTABLE SYSTEM"}')


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Control Theory & State-Space Systems Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
