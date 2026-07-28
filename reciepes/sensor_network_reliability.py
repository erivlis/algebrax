# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Sensor Network Reliability & Spatial Heat Gradient Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Maximum Path Link Reliability (algebrax.semiring.ViterbiSemiring & matrix.power):
   ViterbiSemiring is the Max-Product semiring ([0, 1], max, *).
   Matrix powers M^k over ViterbiSemiring evaluate multi-hop network paths, returning
   the maximum end-to-end transmission success probability P_max(u -> v).

2. Spatial RBF Kernel & Thermal Gradient (algebrax.analysis.gaussian_kernel & gradient):
   - Gaussian RBF Kernel K_ij = exp(-d_ij^2 / (2 * sigma^2)): Converts physical sensor
     distances d_ij into spatial similarity weights.
   - Gradient grad(T)_ij = T_j - T_i: Computes node-to-edge temperature differences
     to detect thermal flux boundaries.

3. Structural Sparsity Metrics (algebrax.metrics.sparsity & density):
   `sparsity` and `density` quantify the proportion of active communication links
   versus potential connections in large IoT sensor topologies.
================================================================================
"""

from algebrax.analysis import gaussian_kernel, gradient
from algebrax.matrix.core import power
from algebrax.metrics import density, sparsity
from algebrax.semiring import ViterbiSemiring


def main() -> None:
    print('==========================================================================')
    print('Use Case: Sensor Network Reliability & Spatial Heat Gradient Analysis')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to compute Viterbi link')
    print('      reliabilities, spatial Gaussian RBF kernels, and temperature gradients.')

    # --- Step 1: Max-Product Link Reliability via ViterbiSemiring ---
    print('\n[Step 1] Multi-Hop Max-Product Reliability (ViterbiSemiring)...')
    print('Explanation: ViterbiSemiring ([0, 1], max, *) finds the single most reliable')
    print('             transmission path probability P_max(u -> v) across lossy wireless links.')

    # Wireless Sensor Mesh Link Probabilities (Success Rate)
    link_probabilities = {
        0: {1: 0.90, 2: 0.70},
        1: {2: 0.85, 3: 0.95},
        2: {3: 0.60},
        3: {},
    }

    viterbi = ViterbiSemiring()
    rel_2step = power(link_probabilities, 2, semiring=viterbi)
    rel_3step = power(link_probabilities, 3, semiring=viterbi)

    p_03_via_2 = rel_2step.get(0, {}).get(3, 0.0)
    p_03_via_3 = rel_3step.get(0, {}).get(3, 0.0)
    best_p = max(p_03_via_2, p_03_via_3)

    print('Link Success Probabilities Graph: ', link_probabilities)
    print(f'2-Hop Max Reliability (Node 0 -> Node 3): {p_03_via_2 * 100:.2f}%')
    print(f'3-Hop Max Reliability (Node 0 -> Node 3): {p_03_via_3 * 100:.2f}%')
    print(f'Optimal End-to-End Reliability P_max(0 -> 3): {best_p * 100:.2f}%')

    # --- Step 2: Spatial RBF Gaussian Kernel & Structural Metrics ---
    print('\n[Step 2] Spatial RBF Gaussian Kernel & Sparsity Audit (gaussian_kernel)...')
    print('Explanation: Converts sensor distance matrix into similarity matrix K_ij = exp(-d^2 / 2sigma^2).')

    sensor_distances = {
        0: {1: 1.5, 2: 3.0},
        1: {0: 1.5, 2: 1.0, 3: 4.0},
        2: {0: 3.0, 1: 1.0, 3: 2.0},
        3: {1: 4.0, 2: 2.0},
    }

    rbf_similarity = gaussian_kernel(sensor_distances, sigma=2.0)
    net_density = density(rbf_similarity, capacity=16)
    net_sparsity = sparsity(rbf_similarity, capacity=16)

    print('\nSpatial Gaussian RBF Similarity Matrix (sigma=2.0):')
    for r in sorted(rbf_similarity.keys()):
        print(f'  Sensor {r}: {rbf_similarity[r]}')

    print(f'\nNetwork Connectivity Density:  {net_density * 100:.1f}%')
    print(f'Network Structural Sparsity:   {net_sparsity * 100:.1f}%')

    # --- Step 3: Discrete Temperature Gradient (exterior derivative d0) ---
    print('\n[Step 3] Discrete Thermal Flux Gradient (gradient)...')
    print('Explanation: Computes grad(T)_ij = T_j - T_i to isolate thermal flux boundaries.')

    # Sensor temperature readings in Celsius
    temp_field = {0: 22.0, 1: 45.0, 2: 48.0, 3: 23.0}
    topology_graph = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1, 3], 3: [1, 2]}

    temp_grad = gradient(temp_field, topology_graph)

    print('\nSensor Thermal Readings (°C): ', temp_field)
    print('\nNode-to-Edge Thermal Gradient grad(T)_ij (°C):')
    for u in sorted(temp_grad.keys()):
        for v, grad_val in sorted(temp_grad[u].items()):
            tag = ' <== THERMAL FLUX BOUNDARY' if abs(grad_val) > 20.0 else ''
            print(f'  Edge ({u} -> {v}): Delta T = {grad_val:+6.1f} °C{tag}')

    print('\n==========================================================================')
    print('Use Case Completed: Sensor Network Reliability & Heat Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
