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
# # Telecommunications Signal Encoding & Fractal Network Dynamics
#
# ## Theory & Mathematical Foundation
#
# 1. **Orthogonal Bitstream Encoding (`algebrax.transforms.walsh_hadamard`)**:
#    The Fast Walsh-Hadamard Transform (FWHT) maps a $2^k$ telemetry payload
#    into an orthogonal spectrum $X[k] = \sum_m x[m] (-1)^{\text{popcount}(k \text{ AND } m)}$.
#    Self-inverses $\text{WHT}(\text{WHT}(x)) = N x$ enable error-correcting decoding over noisy channels.
#
# 2. **Network Flow Divergence & Laplacian (`algebrax.analysis.laplacian` & `ax.analysis.divergence`)**:
#    - **Laplacian** ($L = D - A$): Captures structural graph diffusion dynamics.
#    - **Divergence** ($\text{div}(F)_i = \sum_j F_{ij}$): Measures net traffic flow entering or leaving each mesh node.
#
# 3. **Spatial Fractal Box Dimension (`algebrax.metrics.box_counting_dimension`)**:
#    The Minkowski-Bouligand box dimension $D_0 = \lim_{\epsilon \to 0} \frac{\ln N(\epsilon)}{\ln(1/\epsilon)}$
#    quantifies spatial coverage density and multi-scale scaling.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Orthogonal Telemetry Encoding (`walsh_hadamard`)

# %%
telemetry_payload = {0: 1.0, 1: -1.0, 2: 1.0, 3: 1.0, 4: -1.0, 5: 1.0, 6: -1.0, 7: -1.0}
wht_spectrum = ax.transforms.walsh_hadamard(telemetry_payload, n=8)

reconstructed = {k: v / 8.0 for k, v in ax.transforms.walsh_hadamard(wht_spectrum, n=8).items()}

print(f"Original 8-bit Telemetry Stream: {telemetry_payload}")
print("\nWalsh-Hadamard Spectrum (WHT):")
for k in sorted(wht_spectrum.keys()):
    print(f"  Walsh Code {k}: {wht_spectrum[k]:+6.1f}")

print(f"\nReconstructed Payload (1/N * WHT^2): {reconstructed}")
print(f"Exact Reconstruction Match: {telemetry_payload == reconstructed}")

# %% [markdown]
# ## Step 2: Mesh Network Traffic Flow & Laplacian (`laplacian` & `divergence`)

# %%
mesh_graph = {
    0: {1: 1.0, 2: 1.0},
    1: {0: 1.0, 2: 1.0, 3: 1.0},
    2: {0: 1.0, 1: 1.0, 3: 1.0},
    3: {1: 1.0, 2: 1.0},
}

signal_field = {0: 100.0, 1: 80.0, 2: 60.0, 3: 40.0}
lap_vector = ax.analysis.laplacian(signal_field, mesh_graph)

traffic_flow = {
    0: {1: 45.0, 2: 30.0},
    1: {3: 50.0},
    2: {3: 20.0},
    3: {},
}

flow_div = ax.analysis.divergence(traffic_flow)

print("\nGraph Laplacian Signal Vector L(f) = div(grad f):")
for r in sorted(lap_vector.keys()):
    print(f"  Node {r}: {lap_vector[r]:+6.1f} dBm")

print("\nNetwork Traffic Divergence div(F):")
for node, div_val in sorted(flow_div.items()):
    role = "SOURCE (Net Outflow)" if div_val > 0 else ("SINK (Net Inflow)" if div_val < 0 else "BALANCED")
    print(f"  Node {node}: {div_val:+6.1f} Mbps [{role}]")

# %% [markdown]
# ## Step 3: Spatial Cell Tower Fractal Dimension (`box_counting_dimension`)

# %%
tower_points = {
    (0, 0): 1.0,
    (0, 1): 1.0,
    (1, 0): 1.0,
    (1, 1): 1.0,
    (4, 4): 1.0,
    (4, 5): 1.0,
    (5, 4): 1.0,
    (5, 5): 1.0,
    (0, 4): 1.0,
    (1, 5): 1.0,
    (4, 0): 1.0,
    (5, 1): 1.0,
}

fractal_dim = ax.metrics.box_counting_dimension(tower_points, min_box_size=1, max_box_size=4)
print(f"\nSpatial Tower Grid Points: {len(tower_points)} locations")
print(f"Minkowski-Bouligand Box Dimension D_0: {fractal_dim:.4f}")


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Telecommunications & Fractal Analysis Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
