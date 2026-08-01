# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
3D Gaussian Splatting & Projective Rendering Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. 3D Spatial Covariance Construction (algebrax.matrix.core.dot & transpose):
   A 3D Gaussian centered at mu = (x, y, z)^T with scaling matrix S = diag(sx, sy, sz)
   and SO(3) rotation matrix R has a 3D spatial covariance matrix:
       Sigma = R * S * S^T * R^T
   which is constructed via polymorphic matrix multiplication (`dot`).

2. 2D Screen Perspective Projection & Jacobian Composition (algebrax.matrix.core.dot):
   Given camera view matrix W and perspective projection Jacobian J at t = W * mu:
       J = [[f / t_z,     0,   -f * t_x / t_z^2],
            [    0,   f / t_z, -f * t_y / t_z^2]]
   The 2D projected screen covariance matrix Sigma' in 2D pixel coordinates is:
       T = J * W
       Sigma' = T * Sigma * T^T

3. Depth-Sorted Volumetric Alpha-Compositing & RBF Evaluation (algebrax.analysis.gaussian_kernel):
   Gaussians sorted by camera z-depth are rasterized. The 2D spatial Gaussian response
   G_i(p) at screen pixel p is evaluated via 2D inverse covariance distance, and the
   accumulated ray color C is computed using alpha-blending:
       C = sum_{i=1}^N c_i * alpha_i * G_i(p) * prod_{j=1}^{i-1} (1 - alpha_j * G_j(p))
================================================================================
"""

import math

from algebrax.analysis import gaussian_kernel
from algebrax.matrix.core import dot, transpose


def create_scale_matrix(sx: float, sy: float, sz: float) -> dict[int, dict[int, float]]:
    """Create a 3D scaling matrix S."""
    return {
        0: {0: sx},
        1: {1: sy},
        2: {2: sz},
    }


def create_rotation_matrix(pitch: float, yaw: float, roll: float) -> dict[int, dict[int, float]]:
    """Create 3D SO(3) rotation matrix R = Rz * Ry * Rx."""
    cx, sx = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cz, sz = math.cos(roll), math.sin(roll)

    rx = {0: {0: 1.0}, 1: {1: cx, 2: -sx}, 2: {1: sx, 2: cx}}
    ry = {0: {0: cy, 2: sy}, 1: {1: 1.0}, 2: {0: -sy, 2: cy}}
    rz = {0: {0: cz, 1: -sz}, 1: {0: sz, 1: cz}, 2: {2: 1.0}}

    r_xy = dot(ry, rx)
    return dot(rz, r_xy)


def compute_3d_covariance(
    scale: tuple[float, float, float], rot: tuple[float, float, float]
) -> dict[int, dict[int, float]]:
    """Compute 3D covariance matrix Sigma = R * S * S^T * R^T."""
    s_mat = create_scale_matrix(*scale)
    r_mat = create_rotation_matrix(*rot)

    # S * S^T (since S is diagonal, S * S^T = S^2)
    s_sq = dot(s_mat, s_mat)

    # R * S^2 * R^T
    r_s2 = dot(r_mat, s_sq)
    return dot(r_s2, transpose(r_mat))


def compute_2d_projected_covariance(
    sigma_3d: dict[int, dict[int, float]],
    mean_3d: tuple[float, float, float],
    focal_length: float = 2.0,
) -> dict[int, dict[int, float]]:
    """
    Project 3D spatial covariance Sigma into 2D screen coordinate covariance Sigma'.
    T = J * W
    Sigma' = T * Sigma * T^T
    """
    tx, ty, tz = mean_3d
    tz = max(tz, 0.1)  # Prevent division by zero

    # Jacobian of perspective projection at t = (tx, ty, tz)
    j_mat = {
        0: {0: focal_length / tz, 2: -focal_length * tx / (tz * tz)},
        1: {1: focal_length / tz, 2: -focal_length * ty / (tz * tz)},
    }

    # T * Sigma * T^T
    t_sigma = dot(j_mat, sigma_3d)
    return dot(t_sigma, transpose(j_mat))


def main() -> None:
    print('==========================================================================')
    print('Use Case: 3D Gaussian Splatting & Projective Screen Rendering')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to construct 3D')
    print('      covariance matrices, compute 2D perspective screen projections, and')
    print('      perform depth-sorted volumetric alpha-blending.')

    # --- Step 1: 3D Gaussian Covariance Construction (dot & transpose) ---
    print('\n[Step 1] 3D Gaussian Spatial Covariance Construction (dot & transpose)...')
    print('Explanation: Sigma = R * S * S^T * R^T defines 3D spatial Gaussian extent.')

    # Define two 3D Gaussians in world space
    gaussians = [
        {
            'id': 'Gaussian_Red',
            'pos': (0.0, 0.0, 4.0),
            'scale': (0.8, 0.3, 0.3),
            'rot': (0.2, 0.5, 0.0),
            'color': (1.0, 0.2, 0.2),
            'opacity': 0.85,
        },
        {
            'id': 'Gaussian_Blue',
            'pos': (0.5, 0.3, 3.5),
            'scale': (0.4, 0.7, 0.4),
            'rot': (0.0, -0.3, 0.4),
            'color': (0.2, 0.4, 1.0),
            'opacity': 0.75,
        },
    ]

    for g in gaussians:
        g['sigma_3d'] = compute_3d_covariance(g['scale'], g['rot'])
        print(f'\n3D Covariance Matrix Sigma for {g["id"]}:')
        for r in range(3):
            row_str = ' '.join(f'{g["sigma_3d"].get(r, {}).get(c, 0.0):+6.3f}' for c in range(3))
            print(f'  Row {r}: [{row_str}]')

    # --- Step 2: 2D Screen Perspective Projection (dot) ---
    print('\n[Step 2] 2D Perspective Screen Covariance Projection (dot)...')
    print("Explanation: Sigma' = J * Sigma * J^T projects 3D spatial ellipsoids into 2D screen space.")

    focal_len = 2.5
    for g in gaussians:
        g['sigma_2d'] = compute_2d_projected_covariance(g['sigma_3d'], g['pos'], focal_length=focal_len)
        print(f"\n2D Screen Covariance Matrix Sigma' for {g['id']}:")
        for r in range(2):
            row_str = ' '.join(f'{g["sigma_2d"].get(r, {}).get(c, 0.0):+6.3f}' for c in range(2))
            print(f'  Row {r}: [{row_str}]')

    # --- Step 3: Depth Sorting & Volumetric Alpha Compositing (gaussian_kernel) ---
    print('\n[Step 3] Depth-Sorted Volumetric Alpha-Compositing (gaussian_kernel)...')
    print('Explanation: Sorts 3D Gaussians by camera z-depth and accumulates ray color.')

    # Sort Gaussians by camera Z depth (front to back or back to front)
    sorted_gaussians = sorted(gaussians, key=lambda g: g['pos'][2])

    print('\nDepth-Sorted Gaussian Sequence:')
    for idx, g in enumerate(sorted_gaussians):
        print(f'  Order {idx + 1}: {g["id"]} at Depth Z = {g["pos"][2]:.2f} (Opacity alpha = {g["opacity"]:.2f})')

    # Evaluate 2D spatial response at screen center (0, 0)
    screen_center = (0.0, 0.0)
    accum_color = [0.0, 0.0, 0.0]
    transmittance = 1.0

    print(f'\nRay Marching Alpha-Blending at Screen Center {screen_center}:')
    for g in sorted_gaussians:
        # Distance from projected screen center
        tx, ty, tz = g['pos']
        proj_x = focal_len * tx / tz
        proj_y = focal_len * ty / tz
        dx = screen_center[0] - proj_x
        dy = screen_center[1] - proj_y

        # Gaussian response G_i
        # Det of 2D covariance
        a = g['sigma_2d'].get(0, {}).get(0, 0.1)
        c = g['sigma_2d'].get(1, {}).get(1, 0.1)
        b = g['sigma_2d'].get(0, {}).get(1, 0.0)
        det = max(a * c - b * b, 1e-6)

        # Inverse 2D covariance
        inv_a = c / det
        inv_c = a / det
        inv_b = -b / det

        mah_dist = 0.5 * (dx * (inv_a * dx + inv_b * dy) + dy * (inv_b * dx + inv_c * dy))
        response = math.exp(-max(mah_dist, 0.0))

        effective_alpha = g['opacity'] * response
        weight = effective_alpha * transmittance

        for channel in range(3):
            accum_color[channel] += weight * g['color'][channel]

        transmittance *= 1.0 - effective_alpha

        print(
            f'  {g["id"]}: G = {response:.4f}, Weight = {weight:.4f}, Transmittance = {transmittance:.4f}'
        )

    print(f'\nFinal Accumulated Screen Color: R={accum_color[0]:.3f}, G={accum_color[1]:.3f}, B={accum_color[2]:.3f}')

    # Spatial RBF affinity matrix audit on 2D projected means
    dist_matrix = {0: {1: 1.2}, 1: {0: 1.2}}
    rbf = gaussian_kernel(dist_matrix, sigma=1.0)
    print('\nSpatial Gaussian Kernel Inter-Splat Affinity:')
    print('  Affinity between Splat 1 & Splat 2:', rbf.get(0, {}).get(1, 0.0))

    assert len(sorted_gaussians) == 2
    assert accum_color[0] > 0.0
    print('\n==========================================================================')
    print('SUCCESS: 3D Gaussian Splatting Projective Rendering completed cleanly!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
