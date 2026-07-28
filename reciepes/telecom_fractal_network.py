# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Telecommunications Signal Encoding & Fractal Network Dynamics Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Orthogonal Bitstream Encoding (algebrax.transforms.walsh_hadamard):
   The Fast Walsh-Hadamard Transform (FWHT) maps a 2^k boolean telemetry payload
   into an orthogonal spectrum X[k] = sum_m x[m] (-1)^popcount(k AND m).
   Self-inverses WHT(WHT(x)) = N * x enable error-correcting decoding over noisy channels.

2. Network Flow Divergence & Laplacian (algebrax.analysis.laplacian & divergence):
   - Laplacian (L = D - A): Captures structural graph diffusion dynamics.
   - Divergence (div(F)_i = sum_j F_ij): Measures net traffic flow entering or leaving
     each mesh node i to isolate network sinks (div < 0) and sources (div > 0).

3. Spatial Fractal Box Dimension (algebrax.metrics.box_counting_dimension):
   The Minkowski-Bouligand box dimension D_0 = lim_{eps -> 0} ln N(eps) / ln(1/eps)
   quantifies spatial coverage density and multi-scale scaling of cell tower placement.
================================================================================
"""

from algebrax.analysis import divergence, laplacian
from algebrax.metrics import box_counting_dimension
from algebrax.transforms import walsh_hadamard


def main() -> None:
    print('==========================================================================')
    print('Use Case: Telecommunications Signal Encoding & Fractal Network Dynamics')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to encode signals via WHT,')
    print('      analyze graph Laplacian flow divergence, and measure spatial fractal dimension.')

    # --- Step 1: Walsh-Hadamard Signal Encoding & Decoding ---
    print('\n[Step 1] Orthogonal Telemetry Encoding (walsh_hadamard)...')
    print('Explanation: Transformed 8-bit telemetry payload into Hadamard spectrum.')
    print('             WHT spectrum spreads energy orthogonally across frequency Walsh codes.')

    telemetry_payload = {0: 1.0, 1: -1.0, 2: 1.0, 3: 1.0, 4: -1.0, 5: 1.0, 6: -1.0, 7: -1.0}
    wht_spectrum = walsh_hadamard(telemetry_payload, n=8)

    # Reconstruct via dual WHT application (WHT(WHT(x)) = N * x)
    reconstructed = {k: v / 8.0 for k, v in walsh_hadamard(wht_spectrum, n=8).items()}

    print(f'Original 8-bit Telemetry Stream: {telemetry_payload}')
    print('\nWalsh-Hadamard Spectrum (WHT):')
    for k in sorted(wht_spectrum.keys()):
        print(f'  Walsh Code {k}: {wht_spectrum[k]:+6.1f}')

    print(f'\nReconstructed Payload (1/N * WHT^2): {reconstructed}')
    print(f'Exact Reconstruction Match: {telemetry_payload == reconstructed}')

    # --- Step 2: Mesh Network Flow Divergence & Laplacian ---
    print('\n[Step 2] Mesh Network Traffic Flow & Laplacian (laplacian & divergence)...')
    print('Explanation: Laplacian L = D - A defines connectivity diffusion, while discrete')
    print('             divergence div(F) pinpoints network traffic bottlenecks and sinks.')

    # 4-Node Mesh Network Adjacency
    mesh_graph = {
        0: {1: 1.0, 2: 1.0},
        1: {0: 1.0, 2: 1.0, 3: 1.0},
        2: {0: 1.0, 1: 1.0, 3: 1.0},
        3: {1: 1.0, 2: 1.0},
    }

    # Signal Field on Mesh Nodes (Signal Strength in dBm)
    signal_field = {0: 100.0, 1: 80.0, 2: 60.0, 3: 40.0}
    lap_vector = laplacian(signal_field, mesh_graph)

    # Traffic Flow Matrix F (positive value F_ij implies net traffic from i to j)
    traffic_flow = {
        0: {1: 45.0, 2: 30.0},
        1: {3: 50.0},
        2: {3: 20.0},
        3: {},
    }

    flow_div = divergence(traffic_flow)

    print('\nGraph Laplacian Signal Vector L(f) = div(grad f):')
    for r in sorted(lap_vector.keys()):
        print(f'  Node {r}: {lap_vector[r]:+6.1f} dBm')

    print('\nNetwork Traffic Divergence div(F):')
    for node, div_val in sorted(flow_div.items()):
        role = 'SOURCE (Net Outflow)' if div_val > 0 else ('SINK (Net Inflow)' if div_val < 0 else 'BALANCED')
        print(f'  Node {node}: {div_val:+6.1f} Mbps [{role}]')

    # --- Step 3: Spatial Fractal Coverage Dimension ---
    print('\n[Step 3] Spatial Cell Tower Fractal Dimension (box_counting_dimension)...')
    print('Explanation: Box-counting dimension D_0 measures self-similar spatial scaling.')

    # 2D Grid coordinates of 16 distributed cell tower sites
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

    fractal_dim = box_counting_dimension(tower_points, min_box_size=1, max_box_size=4)
    print(f'\nSpatial Tower Grid Points: {len(tower_points)} locations')
    print(f'Minkowski-Bouligand Box Dimension D_0: {fractal_dim:.4f}')

    print('\n==========================================================================')
    print('Use Case Completed: Telecommunications & Fractal Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
