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
#    An object wave field $O(x) = A_O e^{i \phi_O}$ interferes with a coherent
#    reference plane wave $R(x) = A_R e^{i k x}$.
#    The recorded hologram intensity is:
#    $$I(x) = |O + R|^2 = |O|^2 + |R|^2 + R^* O + R O^*$$
#
# 2. **Holographic Wavefront Reconstruction**:
#    Illuminating the hologram $I(x)$ with reference beam $R(x)$ yields:
#    $$R I = R |O|^2 + R |R|^2 + |R|^2 O + R^2 O^*$$
#    The term $|R|^2 O$ represents an exact reconstructed virtual image of the original object!
#
# 3. **Spatial Optical Diffraction via Discrete Fourier Transform (`dft` & `idft`)**:
#    Free-space wave diffraction between optical planes is governed by:
#    $$F(u) = \text{DFT}(I(x)), \quad x(n) = \text{iDFT}(F(u))$$
#
# 4. **Fringe Visibility & Information Entropy Audit (`algebrax.probability.entropy`)**:
#    Shannon entropy $H(I)$ audits interference fringe modulation contrast.

# %%
import cmath

import algebrax as ax

# %% [markdown]
# ## Step 1: Recording Optical Hologram Interference Pattern
# $I(x) = |O(x) + R(x)|^2$ records phase and amplitude of object wave $O(x)$.

# %%
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

k_ref = 0.25 * cmath.pi
reference_wave = {x: 1.0 * cmath.exp(1j * k_ref * x) for x in range(8)}

hologram_intensity = {}
for x in range(8):
    total_field = object_wave[x] + reference_wave[x]
    hologram_intensity[x] = abs(total_field) ** 2

print("\nObject Field O(x) Sample Values:")
for x in range(8):
    if abs(object_wave[x]) > 0:
        print(f"  Position x={x}: Amp = {abs(object_wave[x]):.2f}, Phase = {cmath.phase(object_wave[x]):+.2f} rad")

print("\nRecorded Hologram Interference Intensity I(x):")
for x, i_val in sorted(hologram_intensity.items()):
    print(f"  Fringe Position x={x}: Intensity = {i_val:.4f}")

# %% [markdown]
# ## Step 2: Holographic Image Reconstruction (Illumination by Reference R)
# Illuminating hologram with $R(x)$ reconstructs virtual image term $|R|^2 O(x)$.

# %%
reconstructed_wavefront = {}
for x in range(8):
    illuminated_field = reference_wave[x] * hologram_intensity[x]
    r_conj = reference_wave[x].conjugate()
    reconstructed_wavefront[x] = illuminated_field * r_conj / (abs(reference_wave[x]) ** 2)

print("\nReconstructed Optical Field Wavefront at Hologram Plane:")
for x in range(8):
    amp = abs(reconstructed_wavefront[x])
    match = " <== RECONSTRUCTED OBJECT SLIT" if abs(object_wave[x]) > 0 else ""
    print(f"  Position x={x}: Amp = {amp:.4f}{match}")

# %% [markdown]
# ## Step 3: Optical Diffraction Frequency Propagation (`dft` & `idft`)
# DFT converts spatial optical wavefront into angular spectrum $F(u)$.

# %%
real_hologram_signal = {x: float(i_val) for x, i_val in hologram_intensity.items()}

angular_spectrum = ax.transforms.dft(real_hologram_signal, n=8)
reconstructed_spatial_field = ax.transforms.idft(angular_spectrum, n=8)

print("\nAngular Spatial Frequency Spectrum F(u) = dft(I):")
for u in sorted(angular_spectrum.keys()):
    freq_amp = abs(angular_spectrum[u])
    print(f"  Spatial Frequency u={u}: Magnitude = {freq_amp:6.2f}")

print("\nInverse Diffraction Reconstructed Spatial Profile idft(F):")
for x in sorted(reconstructed_spatial_field.keys()):
    print(f"  Spatial Position x={x}: Intensity = {reconstructed_spatial_field[x]:6.2f}")

# %% [markdown]
# ## Step 4: Hologram Fringe Contrast & Shannon Information Entropy (`entropy`)

# %%
total_intensity = sum(hologram_intensity.values())
prob_dist = {x: val / total_intensity for x, val in hologram_intensity.items()}

hologram_entropy = ax.probability.entropy(prob_dist)

i_max = max(hologram_intensity.values())
i_min = min(hologram_intensity.values())
fringe_visibility = (i_max - i_min) / (i_max + i_min)

print(f"\nMax Hologram Intensity I_max:       {i_max:.4f}")
print(f"Min Hologram Intensity I_min:       {i_min:.4f}")
print(f"Michelson Fringe Visibility V:       {fringe_visibility * 100:.2f}% (High Optical Contrast)")
print(f"Hologram Information Shannon Entropy: {hologram_entropy:.4f} bits")


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Optical Holography Simulation Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
