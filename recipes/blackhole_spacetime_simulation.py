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
# # Schwarzschild Black Hole Spacetime & Gravitational Lensing
#
# ## Theory & Mathematical Foundation
#
# 1. **Schwarzschild Spacetime Metric Tensor (`algebrax.tensor.einsum`)**:
#    The Schwarzschild metric $g_{\mu\nu}$ describes spacetime geometry around a black hole
#    of mass $M$ and Schwarzschild radius $r_s = 2GM/c^2$:
#    $$ds^2 = -\left(1 - \frac{r_s}{r}\right) c^2 dt^2 + \left(1 - \frac{r_s}{r}\right)^{-1} dr^2$$
#    $$+ r^2 d\theta^2 + r^2 \sin^2\theta d\phi^2$$
#    `tensor.einsum` contracts metric $g^{\mu\nu} g_{\nu\alpha} = \delta^\mu_\alpha$.
#
# 2. **Gravitational Redshift & Time Dilation (`algebrax.transforms.z_transform`)**:
#    Photons escaping from radius $r$ experience gravitational redshift
#    $\nu_{\text{obs}} = \nu_{\text{emit}} \sqrt{1 - r_s/r}$.
#    `transforms.z_transform` evaluates complex frequency spectral shifts $X(z)$ near the event horizon.
#
# 3. **Photon Deflection & Spacetime Curvature (`algebrax.analysis.forman_ricci_curvature` & `ax.analysis.gradient`)**:
#    Light rays grazing impact parameter $b$ undergo gravitational deflection $\Delta\phi = \frac{4GM}{c^2 b}$.
#    `forman_ricci_curvature` models localized negative spatial curvature surrounding the photon sphere.
#
# 4. **Bekenstein-Hawking Black Hole Entropy (`algebrax.probability.entropy` & `ax.probability.kl_divergence`)**:
#    Black hole entropy $S_{\text{BH}} = \frac{A}{4 l_P^2}$ scales with event horizon surface area $A = 4\pi r_s^2$.
#    `probability.entropy` and `probability.kl_divergence` audit quantum information scrambling.

# %%
import math

import algebrax as ax

# %% [markdown]
# ## Step 1: Schwarzschild Spacetime Metric Tensor (`tensor.einsum`)
# $g_{\mu\nu}$ defines interval $ds^2$ around Schwarzschild radius $r_s$.

# %%
r_s = 29.5  # km (Schwarzschild event horizon radius)

r_eval = 2.0 * r_s
f_r = 1.0 - (r_s / r_eval)

g_metric = ax.trie.AlgebraicTrie()
g_metric[(0, 0)] = -f_r
g_metric[(1, 1)] = 1.0 / f_r
g_metric[(2, 2)] = r_eval**2
g_metric[(3, 3)] = (r_eval * math.sin(math.pi / 2)) ** 2

g_inv = ax.trie.AlgebraicTrie()
g_inv[(0, 0)] = -1.0 / f_r
g_inv[(1, 1)] = f_r
g_inv[(2, 2)] = 1.0 / (r_eval**2)
g_inv[(3, 3)] = 1.0 / (r_eval**2)

identity_check = ax.tensor.einsum('ma,an->mn', g_inv, g_metric)

print(f'Schwarzschild Event Horizon Radius r_s: {r_s:.1f} km')
print(f'Evaluated Radial Distance r:             {r_eval:.1f} km (r = 2.0 r_s)')
print(f'Time Dilation Metric Factor g_tt:       {g_metric[(0, 0)]:.4f}')
print(f'Radial Spatial Metric Factor g_rr:       {g_metric[(1, 1)]:.4f}')
print('\nMetric Tensor Contraction Identity Check (g^{mu a} * g_{a n}):')
for mu in range(4):
    print(f'  Diagonal Element ({mu}, {mu}): {identity_check[(mu, mu)]:.4f}')

# %% [markdown]
# ## Step 2: Gravitational Redshift & Signal Dilation (`transforms.z_transform`)
# Photons escaping from $r_{\text{eval}}$ experience redshift factor $z_{\text{red}} = \frac{1}{\sqrt{f_r}} - 1$.

# %%
redshift_factor = (1.0 / math.sqrt(f_r)) - 1.0
print(f'\nGravitational Redshift Factor z_red: {redshift_factor * 100:.2f}%')

emitted_signal = {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.4, 4: 0.2}

z_complex = (1.0 + redshift_factor) * (math.cos(math.pi / 4) + 1j * math.sin(math.pi / 4))
redshifted_hz = ax.transforms.z_transform(emitted_signal, z=z_complex)

print('Emitted Photon Pulse Signal h[n]:', emitted_signal)
print(f'Redshifted Z-Transform H(z = {z_complex:.2f}): {redshifted_hz:.4f} (Magnitude = {abs(redshifted_hz):.4f})')

# %% [markdown]
# ## Step 3: Gravitational Lensing Ray Deflection & Spatial Curvature
# Deflection $\Delta\phi = \frac{4GM}{c^2 b} = \frac{2 r_s}{b}$ for impact parameter $b$.

# %%
r_grid = {1: 1.5 * r_s, 2: 2.0 * r_s, 3: 3.0 * r_s, 4: 5.0 * r_s}
potential_field = {node: -0.5 * r_s / r_val for node, r_val in r_grid.items()}

grid_graph = {1: [2], 2: [1, 3], 3: [2, 4], 4: [3]}
field_gradient = ax.analysis.gradient(potential_field, grid_graph)

spacetime_graph = {
    1: {2: 1.5},
    2: {1: 1.5, 3: 2.0},
    3: {2: 2.0, 4: 3.0},
    4: {3: 3.0},
}
ricci_k = ax.analysis.forman_ricci_curvature(spacetime_graph)

b_impact = 3.0 * r_s
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

# %% [markdown]
# ## Step 4: Bekenstein-Hawking Entropy & Quantum Information Audit (`entropy` & `kl_divergence`)
# $S_{\text{BH}} = \frac{A}{4 l_P^2}$ measures black hole microstate information density.

# %%
area_km2 = 4.0 * math.pi * (r_s**2)

infalling_state = {0: 0.70, 1: 0.20, 2: 0.10}
hawking_scrambled = {0: 0.34, 1: 0.33, 2: 0.33}

s_infalling = ax.probability.entropy(infalling_state)
s_hawking = ax.probability.entropy(hawking_scrambled)
info_scrambling_kl = ax.probability.kl_divergence(infalling_state, hawking_scrambled)

print(f'\nEvent Horizon Surface Area A:       {area_km2:.2f} km^2')
print(f'Infalling Matter Entropy S_in:       {s_infalling:.4f} bits')
print(f'Hawking Radiation Thermal Entropy:   {s_hawking:.4f} bits (Near Maximal Thermalization)')
print(f'Information Scrambling KL-Divergence: {info_scrambling_kl:.4f} bits')


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Schwarzschild Black Hole Simulation Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
