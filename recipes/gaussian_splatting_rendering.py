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
# # 3D Gaussian Splatting & Projective Rendering
#
# ## Theory & Mathematical Foundation
#
# 1. **3D Spatial Covariance Construction (`ax.matrix.dot` & `ax.matrix.transpose`)**:
#    A 3D Gaussian centered at $\mu = (x, y, z)^T$ with scaling matrix $S = \text{diag}(s_x, s_y, s_z)$
#    and $\text{SO}(3)$ rotation matrix $R$ has 3D spatial covariance:
#    $$\Sigma = R S S^T R^T$$
#    constructed via polymorphic matrix multiplication (`ax.matrix.dot`).
#
# 2. **2D Screen Perspective Projection & Jacobian Composition (`ax.matrix.dot`)**:
#    Given perspective projection Jacobian $J$ at camera coordinate $t = W \mu$:
#    $$J = \begin{bmatrix} f / t_z & 0 & -f t_x / t_z^2 \\ 0 & f / t_z & -f t_y / t_z^2 \end{bmatrix}$$
#    The 2D projected screen covariance matrix $\Sigma'$ in 2D pixel coordinates is:
#    $$\Sigma' = J \Sigma J^T$$
#
# 3. **Depth-Sorted Volumetric Alpha-Compositing & RBF Evaluation (`algebrax.analysis.gaussian_kernel`)**:
#    Gaussians sorted by camera z-depth are rasterized via alpha-blending:
#    $$C = \sum_{i=1}^N c_i \alpha_i G_i(p) \prod_{j=1}^{i-1} (1 - \alpha_j G_j(p))$$

# %%
import math

import algebrax as ax


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

    r_xy = ax.matrix.dot(ry, rx)
    return ax.matrix.dot(rz, r_xy)


def compute_3d_covariance(
    scale: tuple[float, float, float], rot: tuple[float, float, float]
) -> dict[int, dict[int, float]]:
    """Compute 3D covariance matrix Sigma = R * S * S^T * R^T."""
    s_mat = create_scale_matrix(*scale)
    r_mat = create_rotation_matrix(*rot)

    s_sq = ax.matrix.dot(s_mat, s_mat)
    r_s2 = ax.matrix.dot(r_mat, s_sq)
    return ax.matrix.dot(r_s2, ax.matrix.transpose(r_mat))


def compute_2d_projected_covariance(
    sigma_3d: dict[int, dict[int, float]],
    mean_3d: tuple[float, float, float],
    focal_length: float = 2.0,
) -> dict[int, dict[int, float]]:
    """Project 3D spatial covariance Sigma into 2D screen coordinate covariance Sigma'."""
    tx, ty, tz = mean_3d
    tz = max(tz, 0.1)

    j_mat = {
        0: {0: focal_length / tz, 2: -focal_length * tx / (tz * tz)},
        1: {1: focal_length / tz, 2: -focal_length * ty / (tz * tz)},
    }

    t_sigma = ax.matrix.dot(j_mat, sigma_3d)
    return ax.matrix.dot(t_sigma, ax.matrix.transpose(j_mat))


# %% [markdown]
# ## Step 1: 3D Gaussian Spatial Covariance Construction ($\Sigma = R S S^T R^T$)

# %%
gaussians = [
    {
        "id": "Gaussian_Red",
        "pos": (0.0, 0.0, 4.0),
        "scale": (0.8, 0.3, 0.3),
        "rot": (0.2, 0.5, 0.0),
        "color": (1.0, 0.2, 0.2),
        "opacity": 0.85,
    },
    {
        "id": "Gaussian_Blue",
        "pos": (0.5, 0.3, 3.5),
        "scale": (0.4, 0.7, 0.4),
        "rot": (0.0, -0.3, 0.4),
        "color": (0.2, 0.4, 1.0),
        "opacity": 0.75,
    },
]

for g in gaussians:
    g["sigma_3d"] = compute_3d_covariance(g["scale"], g["rot"])
    print(f"\n3D Covariance Matrix Sigma for {g['id']}:")
    for r in range(3):
        row_str = " ".join(f"{g['sigma_3d'].get(r, {}).get(c, 0.0):+6.3f}" for c in range(3))
        print(f"  Row {r}: [{row_str}]")

# %% [markdown]
# ## Step 2: 2D Perspective Screen Covariance Projection ($\Sigma' = J \Sigma J^T$)

# %%
focal_len = 2.5
for g in gaussians:
    g["sigma_2d"] = compute_2d_projected_covariance(g["sigma_3d"], g["pos"], focal_length=focal_len)
    print(f"\n2D Screen Covariance Matrix Sigma' for {g['id']}:")
    for r in range(2):
        row_str = " ".join(f"{g['sigma_2d'].get(r, {}).get(c, 0.0):+6.3f}" for c in range(2))
        print(f"  Row {r}: [{row_str}]")

# %% [markdown]
# ## Step 3: Depth Sorting & Volumetric Alpha Compositing (`gaussian_kernel`)

# %%
sorted_gaussians = sorted(gaussians, key=lambda g: g["pos"][2])

print("\nDepth-Sorted Gaussian Sequence:")
for idx, g in enumerate(sorted_gaussians):
    print(f"  Order {idx + 1}: {g['id']} at Depth Z = {g['pos'][2]:.2f} (Opacity alpha = {g['opacity']:.2f})")

screen_center = (0.0, 0.0)
accum_color = [0.0, 0.0, 0.0]
transmittance = 1.0

print(f"\nRay Marching Alpha-Blending at Screen Center {screen_center}:")
for g in sorted_gaussians:
    tx, ty, tz = g["pos"]
    proj_x = focal_len * tx / tz
    proj_y = focal_len * ty / tz
    dx = screen_center[0] - proj_x
    dy = screen_center[1] - proj_y

    a = g["sigma_2d"].get(0, {}).get(0, 0.1)
    c = g["sigma_2d"].get(1, {}).get(1, 0.1)
    b = g["sigma_2d"].get(0, {}).get(1, 0.0)
    det = max(a * c - b * b, 1e-6)

    inv_a = c / det
    inv_c = a / det
    inv_b = -b / det

    mah_dist = 0.5 * (dx * (inv_a * dx + inv_b * dy) + dy * (inv_b * dx + inv_c * dy))
    response = math.exp(-max(mah_dist, 0.0))

    effective_alpha = g["opacity"] * response
    weight = effective_alpha * transmittance

    for channel in range(3):
        accum_color[channel] += weight * g["color"][channel]

    transmittance *= 1.0 - effective_alpha

    print(f"  {g['id']}: G = {response:.4f}, Weight = {weight:.4f}, Transmittance = {transmittance:.4f}")

print(f"\nFinal Accumulated Screen Color: R={accum_color[0]:.3f}, G={accum_color[1]:.3f}, B={accum_color[2]:.3f}")

dist_matrix = {0: {1: 1.2}, 1: {0: 1.2}}
rbf = ax.analysis.gaussian_kernel(dist_matrix, sigma=1.0)
print("\nSpatial Gaussian Kernel Inter-Splat Affinity:")
print("  Affinity between Splat 1 & Splat 2:", rbf.get(0, {}).get(1, 0.0))

assert len(sorted_gaussians) == 2
assert accum_color[0] > 0.0


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: 3D Gaussian Splatting Projective Rendering Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
