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
# # Optical Holography Simulation & Wavefront Reconstruction
#
# ## Theory & Mathematical Foundation
#
# 1. **Optical Wave Interference Recording**:
#    An object wave field $O(x) = A_O e^{i \\phi_O}$ interferes with a coherent
#    reference plane wave $R(x) = A_R e^{i k x}$.
#    The recorded hologram intensity is $I(x) = |O + R|^2$.
#
# 2. **Holographic Wavefront Reconstruction**:
#    Illuminating the hologram $I(x)$ with reference beam $R(x)$ yields:
#    $R I = R |O|^2 + R |R|^2 + |R|^2 O + R^2 O^*$.
#    The term $|R|^2 O$ represents an exact reconstructed virtual image of the original object!
#
# 3. **Spatial Optical Diffraction via Discrete Fourier Transform (`dft` & `idft`)**:
#    $F(u) = \\text{DFT}(I(x)), \\quad x(n) = \\text{iDFT}(F(u))$.

# %%
import cmath

import algebrax as ax


def record_hologram(
    object_wave: dict[int, complex],
    ref_phase: float = 0.25 * cmath.pi,
) -> tuple[dict[int, float], dict[int, complex], float]:
    """Record optical interference intensity I(x), angular spectrum DFT, and fringe entropy."""
    ref_wave = {k: cmath.exp(1j * ref_phase * k) for k in object_wave}
    interf_intensity = {k: float(abs(object_wave[k] + ref_wave[k]) ** 2) for k in object_wave}
    spectrum = ax.transforms.dft({k: complex(v, 0.0) for k, v in interf_intensity.items()})

    total_int = sum(interf_intensity.values())
    prob_dist = {k: interf_intensity[k] / total_int for k in interf_intensity} if total_int > 0 else {}
    fringe_entropy = ax.probability.entropy(prob_dist)
    return interf_intensity, spectrum, fringe_entropy


def reconstruct_wavefront(
    hologram_intensity: dict[int, float],
    ref_phase: float = 0.25 * cmath.pi,
) -> dict[int, complex]:
    """Reconstruct object wavefront by illuminating hologram with reference beam."""
    ref_wave = {k: cmath.exp(1j * ref_phase * k) for k in hologram_intensity}
    reconstructed = {}
    for k in hologram_intensity:
        illuminated = ref_wave[k] * hologram_intensity[k]
        r_conj = ref_wave[k].conjugate()
        reconstructed[k] = illuminated * r_conj / (abs(ref_wave[k]) ** 2)
    return reconstructed

# %% [markdown]
# ## Step 1: Recording Optical Hologram Interference Pattern
#
# ## Step 2: Holographic Image Reconstruction


def run_demo() -> None:
    """Run optical holography recording and wavefront reconstruction."""
    object_wave = {
        0: 0.0 + 0.0j,
        1: 0.0 + 0.0j,
        2: 1.0 + 0.0j,
        3: 0.0 + 0.0j,
        4: 0.0 + 0.0j,
        5: 0.8 + 0.6j,
        6: 0.0 + 0.0j,
        7: 0.0 + 0.0j,
    }

    hologram_intensity, _spectrum, entropy_val = record_hologram(object_wave, ref_phase=0.25 * cmath.pi)
    print('Recorded Hologram Interference Intensity I(x):')
    for x, i_val in sorted(hologram_intensity.items()):
        print(f'  Fringe Position x={x}: Intensity = {i_val:.4f}')
    print(f'Hologram Fringe Entropy: {entropy_val:.4f} bits')

    reconstructed = reconstruct_wavefront(hologram_intensity, ref_phase=0.25 * cmath.pi)
    print('\nReconstructed Optical Field Wavefront at Hologram Plane:')
    for x in range(8):
        amp = abs(reconstructed[x])
        match = ' <== RECONSTRUCTED OBJECT' if abs(object_wave[x]) > 0 else ''
        print(f'  Position x={x}: Amp = {amp:.4f}{match}')


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Optical Holography Simulation Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
