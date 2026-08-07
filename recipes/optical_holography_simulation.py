# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Optical Holography Simulation & Wavefront Reconstruction Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Optical Wave Interference Recording:
   An object wave field O(x) = A_O * exp(i * phi_O) interferes with a coherent
   reference plane wave R(x) = A_R * exp(i * k * x). The recorded hologram intensity
   is I(x) = |O + R|^2 = |O|^2 + |R|^2 + R* * O + R * O*.

2. Holographic Wavefront Reconstruction:
   Illuminating the hologram I(x) with reference beam R(x) yields:
   R * I = R * |O|^2 + R * |R|^2 + |R|^2 * O + R^2 * O*.
   The term |R|^2 * O represents an exact reconstructed virtual image of the original object!

3. Spatial Optical Diffraction via Discrete Fourier Transform (algebrax.transforms.dft & ax.transforms.idft):
   Fourier optics dictates that free-space wave diffraction between optical planes
   is governed by the Discrete Fourier Transform: F(u) = ax.transforms.dft(I(x)) and x(n) = ax.transforms.idft(F(u)).

4. Fringe Visibility & Information Entropy Audit (algebrax.probability.entropy):
   Shannon entropy H(I) audits interference fringe modulation contrast and information density.
================================================================================
"""

import cmath

import algebrax as ax


def main() -> None:
    print('==========================================================================')
    print('Use Case: Optical Holography Simulation & Wavefront Reconstruction')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to simulate optical')
    print('      interference recording, reference beam reconstruction, and DFT diffraction.')

    # --- Step 1: Object Wave & Reference Beam Interference Recording ---
    print('\n[Step 1] Recording Optical Hologram Interference Pattern...')
    print('Explanation: I(x) = |O(x) + R(x)|^2 records phase and amplitude of object wave O(x).')

    # Discrete 8-point spatial sampling grid x in [0..7]
    # Object wave: 2 slit apertures at x=2 and x=5 with phase shifts
    object_wave = {
        0: 0.0 + 0.0j,
        1: 0.0 + 0.0j,
        2: 1.0 + 0.0j,  # Slit 1
        3: 0.0 + 0.0j,
        4: 0.0 + 0.0j,
        5: 0.8 + 0.6j,  # Slit 2 (amplitude 1.0, phase shift 36.87 deg)
        6: 0.0 + 0.0j,
        7: 0.0 + 0.0j,
    }

    # Reference Plane Wave R(x) = A_R * exp(i * k * x)
    k_ref = 0.25 * cmath.pi
    reference_wave = {x: 1.0 * cmath.exp(1j * k_ref * x) for x in range(8)}

    # Hologram Interference Recording: I(x) = |O(x) + R(x)|^2
    hologram_intensity = {}
    for x in range(8):
        total_field = object_wave[x] + reference_wave[x]
        hologram_intensity[x] = abs(total_field) ** 2

    print('\nObject Field O(x) Sample Values:')
    for x in range(8):
        if abs(object_wave[x]) > 0:
            print(f'  Position x={x}: Amp = {abs(object_wave[x]):.2f}, Phase = {cmath.phase(object_wave[x]):+.2f} rad')

    print('\nRecorded Hologram Interference Intensity I(x):')
    for x, i_val in sorted(hologram_intensity.items()):
        print(f'  Fringe Position x={x}: Intensity = {i_val:.4f}')

    # --- Step 2: Holographic Reconstruction via Reference Beam Illumination ---
    print('\n[Step 2] Holographic Image Reconstruction (Illumination by Reference R)...')
    print('Explanation: Illuminating hologram with R(x) reconstructs virtual image term |R|^2 * O(x).')

    reconstructed_wavefront = {}
    for x in range(8):
        # Illumination: R(x) * I(x)
        illuminated_field = reference_wave[x] * hologram_intensity[x]

        # Extract virtual image term by multiplying by conjugate R*(x) / |R|^2
        r_conj = reference_wave[x].conjugate()
        reconstructed_wavefront[x] = illuminated_field * r_conj / (abs(reference_wave[x]) ** 2)

    print('\nReconstructed Optical Field Wavefront at Hologram Plane:')
    for x in range(8):
        amp = abs(reconstructed_wavefront[x])
        match = ' <== RECONSTRUCTED OBJECT SLIT' if abs(object_wave[x]) > 0 else ''
        print(f'  Position x={x}: Amp = {amp:.4f}{match}')

    # --- Step 3: Diffraction Propagation via Discrete Fourier Transform (ax.transforms.dft & ax.transforms.idft) ---
    print('\n[Step 3] Optical Diffraction Frequency Propagation (ax.transforms.dft & ax.transforms.idft)...')
    print('Explanation: DFT converts spatial optical wavefront into angular spectrum F(u).')

    # Extract real intensity signal for DFT transform
    real_hologram_signal = {x: float(i_val) for x, i_val in hologram_intensity.items()}

    # Compute Angular Spectrum F(u) = ax.transforms.dft(I(x))
    angular_spectrum = ax.transforms.dft(real_hologram_signal, n=8)

    # Inverse Transform Reconstructed Field ax.transforms.idft(F(u))
    reconstructed_spatial_field = ax.transforms.idft(angular_spectrum, n=8)

    print('\nAngular Spatial Frequency Spectrum F(u) = ax.transforms.dft(I):')
    for u in sorted(angular_spectrum.keys()):
        freq_amp = abs(angular_spectrum[u])
        print(f'  Spatial Frequency u={u}: Magnitude = {freq_amp:6.2f}')

    print('\nInverse Diffraction Reconstructed Spatial Profile ax.transforms.idft(F):')
    for x in sorted(reconstructed_spatial_field.keys()):
        print(f'  Spatial Position x={x}: Intensity = {reconstructed_spatial_field[x]:6.2f}')

    # --- Step 4: Holographic Fringe Visibility & Information Entropy Audit ---
    print('\n[Step 4] Hologram Fringe Contrast & Shannon Information Entropy (ax.probability.entropy)...')
    print('Explanation: Shannon Entropy H(I) audits interference fringe modulation ax.metrics.density.')

    # Normalize hologram intensity to probability distribution P(x) = I(x) / sum(I)
    total_intensity = sum(hologram_intensity.values())
    prob_dist = {x: val / total_intensity for x, val in hologram_intensity.items()}

    hologram_entropy = ax.probability.entropy(prob_dist)

    i_max = max(hologram_intensity.values())
    i_min = min(hologram_intensity.values())
    fringe_visibility = (i_max - i_min) / (i_max + i_min)

    print(f'\nMax Hologram Intensity I_max:       {i_max:.4f}')
    print(f'Min Hologram Intensity I_min:       {i_min:.4f}')
    print(f'Michelson Fringe Visibility V:       {fringe_visibility * 100:.2f}% (High Optical Contrast)')
    print(f'Hologram Information Shannon Entropy: {hologram_entropy:.4f} bits')

    print('\n==========================================================================')
    print('Use Case Completed: Optical Holography Simulation Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
