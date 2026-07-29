# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Schwarzschild Black Hole Spacetime & Gravitational Lensing Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Schwarzschild Spacetime Metric Tensor (algebrax.tensor.einsum):
   The Schwarzschild metric g_{mu, nu} describes spacetime geometry around a black hole
   of mass M and Schwarzschild radius r_s = 2GM/c^2:
   ds^2 = -(1 - r_s/r) c^2 dt^2 + (1 - r_s/r)^{-1} dr^2 + r^2 d_theta^2 + r^2 sin^2(theta) d_phi^2.
   `einsum` contracts metric g^{mu nu} g_{nu alpha} = delta^mu_alpha.

2. Gravitational Redshift & Time Dilation (algebrax.transforms.z_transform):
   Photons escaping from radius r experience gravitational redshift nu_obs = nu_emit * sqrt(1 - r_s/r).
   `z_transform` evaluates complex frequency spectral shifts X(z) near the event horizon.

3. Photon Deflection & Spacetime Curvature (algebrax.analysis.forman_ricci_curvature & gradient):
   Light rays grazing impact parameter b undergo gravitational deflection Delta_phi = 4GM / (c^2 b).
   `forman_ricci_curvature` models localized negative spatial curvature surrounding the photon sphere.

4. Bekenstein-Hawking Black Hole Entropy (algebrax.probability.entropy & kl_divergence):
   Black hole entropy S_BH = A / (4 l_P^2) scales with event horizon surface area A = 4 pi r_s^2.
   `entropy` and `kl_divergence` audit quantum information scrambling into Hawking radiation.
================================================================================
"""

import math

from algebrax.analysis import forman_ricci_curvature, gradient
from algebrax.probability import entropy, kl_divergence
from algebrax.tensor import einsum
from algebrax.transforms import z_transform
from algebrax.trie import AlgebraicTrie


def main() -> None:
    print('==========================================================================')
    print('Use Case: Schwarzschild Black Hole Spacetime & Gravitational Lensing')
    print('==========================================================================')
    print('Goal: Combine 5 distinct algebraic tools from algebrax to simulate metric')
    print('      tensors, gravitational redshift, photon ray deflection, and Bekenstein-')
    print('      Hawking black hole entropy.')

    # --- Step 1: Schwarzschild Spacetime Metric Tensor (einsum) ---
    print('\n[Step 1] Schwarzschild Spacetime Metric Tensor (einsum)...')
    print('Explanation: g_{mu nu} defines interval ds^2 around Schwarzschild radius r_s.')

    # Mass M = 10 Solar Masses -> Schwarzschild radius r_s = 29.5 km
    r_s = 29.5  # km (Schwarzschild event horizon radius)

    # Evaluate metric components g_00 (time) and g_11 (radial) at r = 2.0 * r_s
    r_eval = 2.0 * r_s
    f_r = 1.0 - (r_s / r_eval)

    g_metric = AlgebraicTrie()
    g_metric[(0, 0)] = -f_r  # g_tt
    g_metric[(1, 1)] = 1.0 / f_r  # g_rr
    g_metric[(2, 2)] = r_eval**2  # g_theta_theta
    g_metric[(3, 3)] = (r_eval * math.sin(math.pi / 2)) ** 2  # g_phi_phi (at equator theta=pi/2)

    # Inverse metric g^{mu nu}
    g_inv = AlgebraicTrie()
    g_inv[(0, 0)] = -1.0 / f_r
    g_inv[(1, 1)] = f_r
    g_inv[(2, 2)] = 1.0 / (r_eval**2)
    g_inv[(3, 3)] = 1.0 / (r_eval**2)

    # Metric contraction g^{\mu \alpha} g_{\alpha \nu} = \delta^\mu_\nu
    identity_check = einsum('ma,an->mn', g_inv, g_metric)

    print(f'\nSchwarzschild Event Horizon Radius r_s: {r_s:.1f} km')
    print(f'Evaluated Radial Distance r:             {r_eval:.1f} km (r = 2.0 r_s)')
    print(f'Time Dilation Metric Factor g_tt:       {g_metric[(0, 0)]:.4f}')
    print(f'Radial Spatial Metric Factor g_rr:       {g_metric[(1, 1)]:.4f}')
    print('\nMetric Tensor Contraction Identity Check (g^{mu a} * g_{a n}):')
    for mu in range(4):
        print(f'  Diagonal Element ({mu}, {mu}): {identity_check[(mu, mu)]:.4f}')

    # --- Step 2: Gravitational Redshift Z-Transform (z_transform) ---
    print('\n[Step 2] Gravitational Redshift & Signal Dilation (z_transform)...')
    print('Explanation: Photons escaping from r_eval experience redshift factor z_red = 1/sqrt(f_r) - 1.')

    redshift_factor = (1.0 / math.sqrt(f_r)) - 1.0
    print(f'\nGravitational Redshift Factor z_red: {redshift_factor * 100:.2f}%')

    # Emitted discrete photon wave signal h[n]
    emitted_signal = {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.4, 4: 0.2}

    # Redshifted Z-transform at complex frequency z = (1 + z_red) * exp(i * pi/4)
    z_complex = (1.0 + redshift_factor) * (math.cos(math.pi / 4) + 1j * math.sin(math.pi / 4))
    redshifted_hz = z_transform(emitted_signal, z=z_complex)

    print('Emitted Photon Pulse Signal h[n]:', emitted_signal)
    print(f'Redshifted Z-Transform H(z = {z_complex:.2f}): {redshifted_hz:.4f} (Magnitude = {abs(redshifted_hz):.4f})')

    # --- Step 3: Gravitational Lensing Deflection & Curvature (gradient & forman_ricci_curvature) ---
    print('\n[Step 3] Gravitational Lensing Ray Deflection & Spatial Curvature...')
    print('Explanation: Deflection Delta_phi = 4GM / (c^2 b) = 2 r_s / b for impact parameter b.')

    # Gravitational potential field phi(r) = -GM / r = -0.5 * r_s / r
    r_grid = {1: 1.5 * r_s, 2: 2.0 * r_s, 3: 3.0 * r_s, 4: 5.0 * r_s}
    potential_field = {node: -0.5 * r_s / r_val for node, r_val in r_grid.items()}

    grid_graph = {1: [2], 2: [1, 3], 3: [2, 4], 4: [3]}
    field_gradient = gradient(potential_field, grid_graph)

    # Spacetime spatial curvature around photon sphere r = 1.5 r_s
    spacetime_graph = {
        1: {2: 1.5},  # Photon Sphere
        2: {1: 1.5, 3: 2.0},
        3: {2: 2.0, 4: 3.0},
        4: {3: 3.0},
    }
    ricci_k = forman_ricci_curvature(spacetime_graph)

    b_impact = 3.0 * r_s  # Impact parameter
    deflection_angle_rad = 2.0 * r_s / b_impact
    deflection_deg = math.degrees(deflection_angle_rad)

    print(f'\nPhoton Impact Parameter b:          {b_impact:.1f} km (b = 3.0 r_s)')
    print(f'Einstein Gravitational Deflection:   {deflection_angle_rad:.4f} rad ({deflection_deg:.2f} deg)')

    print('\nGravitational Field Radial Gradient d(phi)/dr:')
    for u in sorted(field_gradient.keys()):
        for v, g_val in field_gradient[u].items():
            print(f'  Gradient Edge ({u} -> {v}): Delta_phi = {g_val:+8.4f}')

    print('\nForman-Ricci Spatial Curvature near Photon Sphere:')
    for edge, k_val in sorted(ricci_k.items()):
        print(f'  Edge {edge}: Curvature K = {k_val:+5.2f}')

    # --- Step 4: Bekenstein-Hawking Black Hole Entropy (entropy & kl_divergence) ---
    print('\n[Step 4] Bekenstein-Hawking Entropy & Quantum Information Audit...')
    print('Explanation: S_BH = A / (4 l_P^2) measures black hole microstate information density.')

    # Event horizon surface area A = 4 pi r_s^2
    area_km2 = 4.0 * math.pi * (r_s**2)

    # Infalling matter initial state P(x) vs Hawking radiation scrambled state Q(x)
    infalling_state = {0: 0.70, 1: 0.20, 2: 0.10}
    hawking_scrambled = {0: 0.34, 1: 0.33, 2: 0.33}  # Thermalized max entropy

    s_infalling = entropy(infalling_state)
    s_hawking = entropy(hawking_scrambled)
    info_scrambling_kl = kl_divergence(infalling_state, hawking_scrambled)

    print(f'\nEvent Horizon Surface Area A:       {area_km2:.2f} km^2')
    print(f'Infalling Matter Entropy S_in:       {s_infalling:.4f} bits')
    print(f'Hawking Radiation Thermal Entropy:   {s_hawking:.4f} bits (Near Maximal Thermalization)')
    print(f'Information Scrambling KL-Divergence: {info_scrambling_kl:.4f} bits')

    print('\n==========================================================================')
    print('Use Case Completed: Schwarzschild Black Hole Simulation Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
