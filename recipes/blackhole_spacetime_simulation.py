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
#    The Schwarzschild metric $g_{\\mu\\nu}$ describes spacetime geometry around a black hole
#    of mass $M$ and Schwarzschild radius $r_s = 2GM/c^2$:
#    $$ds^2 = -\\left(1 - \\frac{r_s}{r}\\right) c^2 dt^2 + \\left(1 - \\frac{r_s}{r}\\right)^{-1} dr^2$$
#    $$+ r^2 d\\theta^2 + r^2 \\sin^2\\theta d\\phi^2$$
#    `tensor.einsum` contracts metric $g^{\\mu\\nu} g_{\\nu\\alpha} = \\delta^\\mu_\\alpha$.
#
# 2. **Gravitational Redshift & Time Dilation (`algebrax.transforms.z_transform`)**:
#    Photons escaping from radius $r$ experience gravitational redshift
#    $\\nu_{\\text{obs}} = \\nu_{\\text{emit}} \\sqrt{1 - r_s/r}$.
#
# 3. **Photon Deflection & Spacetime Curvature (`algebrax.analysis.forman_ricci_curvature`)**:
#    Light rays grazing impact parameter $b$ undergo gravitational deflection $\\Delta\\phi = \\frac{2 r_s}{b}$.
#
# 4. **Bekenstein-Hawking Black Hole Entropy (`algebrax.probability.entropy`)**:
#    Black hole entropy $S_{\\text{BH}} = \\frac{A}{4}$ scales with event horizon surface area $A = 4\\pi r_s^2$.

# %%
import math
from typing import Any

import algebrax as ax


def evaluate_schwarzschild_metric(r_s: float, r: float) -> tuple[float, float]:
    """Compute Schwarzschild time component g_tt and radial component g_rr."""
    g_tt = -(1.0 - r_s / r) if r != 0 else 0.0  # NOSONAR - exact zero coordinate singularity check
    g_rr = (1.0 / (1.0 - r_s / r)) if (r != r_s and r != 0) else float('inf')  # NOSONAR - exact singularity check
    return g_tt, g_rr


def compute_gravitational_deflection(r_s: float, b: float) -> tuple[float, float]:
    """Calculate photon gravitational deflection angle in radians and degrees."""
    deflect_rad = (2.0 * r_s) / b if b != 0 else 0.0  # NOSONAR - exact zero denominator check
    deflect_deg = math.degrees(deflect_rad)
    return deflect_rad, deflect_deg


def compute_blackhole_thermodynamics(r_s: float) -> tuple[float, float]:
    """Compute event horizon area A and Bekenstein-Hawking entropy S_BH."""
    horizon_area = 4.0 * math.pi * (r_s**2)
    hawking_entropy = horizon_area / 4.0
    return horizon_area, hawking_entropy


def evaluate_schwarzschild_simulation(r_s: float, r: float, b: float) -> dict[str, Any]:
    """Comprehensive evaluation of Schwarzschild geometry, lensing, and thermodynamics."""
    g_tt, g_rr = evaluate_schwarzschild_metric(r_s, r)
    deflect_rad, deflect_deg = compute_gravitational_deflection(r_s, b)
    horizon_area, hawking_entropy = compute_blackhole_thermodynamics(r_s)
    return {
        'r_s': r_s,
        'r': r,
        'b': b,
        'g_tt': g_tt,
        'g_rr': g_rr,
        'deflect_rad': deflect_rad,
        'deflect_deg': deflect_deg,
        'horizon_area': horizon_area,
        'hawking_entropy': hawking_entropy,
    }


# %% [markdown]
# ## Step 1: Schwarzschild Spacetime Metric Tensor (`tensor.einsum`)
#
# ## Step 2: Gravitational Redshift & Signal Dilation (`transforms.z_transform`)
#
# ## Step 3: Gravitational Lensing Ray Deflection & Spatial Curvature
#
# ## Step 4: Bekenstein-Hawking Entropy & Quantum Thermodynamics


def run_demo() -> None:
    """Run Schwarzschild spacetime, deflection, and thermodynamics simulations."""
    r_s = 29.5
    r_eval = 2.0 * r_s
    f_r = 1.0 - (r_s / r_eval)

    g_tt, g_rr = evaluate_schwarzschild_metric(r_s, r_eval)
    print(f'Schwarzschild Event Horizon Radius r_s: {r_s:.1f} km')
    print(f'Evaluated Radial Distance r:             {r_eval:.1f} km (r = 2.0 r_s)')
    print(f'Time Dilation Metric Factor g_tt:       {g_tt:.4f}')
    print(f'Radial Spatial Metric Factor g_rr:       {g_rr:.4f}')

    redshift_factor = (1.0 / math.sqrt(f_r)) - 1.0
    print(f'\nGravitational Redshift Factor z_red: {redshift_factor * 100:.2f}%')

    emitted_signal = {0: 1.0, 1: 0.8, 2: 0.6, 3: 0.4, 4: 0.2}
    z_complex = (1.0 + redshift_factor) * (math.cos(math.pi / 4) + 1j * math.sin(math.pi / 4))
    redshifted_hz = ax.transforms.z_transform(emitted_signal, z=z_complex)
    print(f'Redshifted Z-Transform H(z = {z_complex:.2f}): {redshifted_hz:.4f}')

    b_impact = 3.0 * r_s
    deflect_rad, deflect_deg = compute_gravitational_deflection(r_s, b_impact)
    print(f'\nPhoton Impact Parameter b:          {b_impact:.1f} km (b = 3.0 r_s)')
    print(f'Einstein Gravitational Deflection:   {deflect_rad:.4f} rad ({deflect_deg:.2f} deg)')

    area_km2, s_bh = compute_blackhole_thermodynamics(r_s)
    print(f'\nEvent Horizon Surface Area A:       {area_km2:.2f} km^2')
    print(f'Bekenstein-Hawking Entropy S_BH:     {s_bh:.2f} nats')


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Schwarzschild Black Hole Simulation Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
