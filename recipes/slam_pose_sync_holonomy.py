# %%
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Multi-Robot Pose Synchronization & Loop-Closure Fault Detection (SLAM)
#
# ## Discrete Gauge Connections, Connection Laplacians & Holonomy Curvature
# In multi-robot localization and visual SLAM, agents measure noisy pairwise relative rotations $R_{uv} \in SO(2)$
# across a pose graph. This recipe combines **Phase 7 Fiber Bundles** (`algebrax.topology.bundle`, `k_theory`) with
# **Phase 1 Sparse Linear Solvers** (`algebrax.matrix.solve`) and **Phase 2 Geometric Rotors**:
#
# 1. **Gauge Connection Pose Graph (`DiscreteOrthogonalConnection`)**: Models relative rotations
#    $\rho(u, v) = R(\theta_v - \theta_u)$ across camera/robot pairs.
# 2. **Global Synchronization via Connection Laplacian (`build_connection_laplacian`)**: Solves the grounded linear
#    system $L_\nabla x = \mathbf{0}$ (with anchor frame `cam_0 = [1, 0]^T`) to recover all global orientations.
# 3. **Gauge Covariance Invariance (`apply_gauge_transformation`)**: Demonstrates that rotating a robot's local frame
#    by $g_u \in SO(2)$ transforms solutions covariantly while leaving physical holonomy invariant.
# 4. **Automated Loop-Closure Fault Detection (`compute_face_holonomy`, `is_flat_bundle`)**: Detects corrupted
#    pairwise odometry measurements by inspecting discrete triangle Wilson loops $\operatorname{Hol}(f) \ne I_2$.

# %%
from __future__ import annotations

import math

import algebrax as ax
from algebrax.topology import (
    DiscreteOrthogonalConnection,
    apply_gauge_transformation,
    build_connection_laplacian,
    compute_face_curvature_angle,
    compute_face_holonomy,
    is_flat_bundle,
)
from algebrax.verification import (
    verify_connection_inversion,
    verify_gauge_covariance,
)

# %% [markdown]
# ## 1. Consistent Multi-Robot Pose Graph & Connection Laplacian Synchronization
#
# Four cameras (`'cam_0'`..`'cam_3'`) observe two adjacent triangle loops sharing edge `('cam_0', 'cam_2')`.
# Given exact relative rotations $\rho(u, v) = R(\theta_v - \theta_u)$, the discrete bundle is flat
# ($\operatorname{Hol}(f) = I_2$), and anchoring `cam_0` at heading $0$ in $L_\nabla x = 0$ recovers every
# robot's global orientation vector $(\cos \theta_i, \sin \theta_i)$.

# %%
def rot2d(theta: float) -> dict[int, dict[int, float]]:
    c, s = math.cos(theta), math.sin(theta)
    return {0: {0: c, 1: -s}, 1: {0: s, 1: c}}


true_headings = {
    'cam_0': 0.0,
    'cam_1': 0.75,
    'cam_2': -0.55,
    'cam_3': 1.40,
}

adjacency = {
    'cam_0': ['cam_1', 'cam_2', 'cam_3'],
    'cam_1': ['cam_0', 'cam_2'],
    'cam_2': ['cam_0', 'cam_1', 'cam_3'],
    'cam_3': ['cam_0', 'cam_2'],
}
faces = [
    ('cam_0', 'cam_1', 'cam_2'),
    ('cam_0', 'cam_2', 'cam_3'),
]

conn = DiscreteOrthogonalConnection(fiber_dim=2)
undirected_edges: list[tuple[str, str]] = []
for u, nbrs in adjacency.items():
    for v in nbrs:
        if u < v:
            conn.set_transport(u, v, rot2d(true_headings[v] - true_headings[u]))
            undirected_edges.append((u, v))

assert is_flat_bundle(conn, faces)
assert verify_connection_inversion(conn, undirected_edges)


def solve_anchored_headings(
    connection: DiscreteOrthogonalConnection,
    anchor: str = 'cam_0',
) -> dict[str, float]:
    """Recover global SO(2) headings by anchoring cam_0 = (1, 0) in L_nabla * x = 0."""
    l_conn = build_connection_laplacian(connection, adjacency)
    anchor_val = {0: 1.0, 1: 0.0}

    reduced_mat: dict[tuple[str, int], dict[tuple[str, int], float]] = {}
    rhs: dict[tuple[str, int], float] = {}
    for row_key, row_dict in l_conn.items():
        if row_key[0] == anchor:
            continue
        r_out: dict[tuple[str, int], float] = {}
        rhs_val = 0.0
        for col_key, val in row_dict.items():
            if col_key[0] == anchor:
                rhs_val -= val * anchor_val[col_key[1]]
            else:
                r_out[col_key] = val
        reduced_mat[row_key] = r_out
        if abs(rhs_val) > 1e-15:
            rhs[row_key] = rhs_val

    sol = ax.matrix.solve(reduced_mat, rhs)
    recovered: dict[str, float] = {anchor: 0.0}
    for cam in sorted(adjacency.keys()):
        if cam != anchor:
            vx = sol.get((cam, 0), 0.0)
            vy = sol.get((cam, 1), 0.0)
            recovered[cam] = math.atan2(vy, vx)
    return recovered


recovered = solve_anchored_headings(conn)
print('Synchronized Robot Headings (True vs. Recovered):')
for cam, theta_true in true_headings.items():
    print(f'  {cam}: true={theta_true:+.4f} rad | recovered={recovered[cam]:+.4f} rad')
    assert math.isclose(recovered[cam], theta_true, abs_tol=1e-9)

# %% [markdown]
# ## 2. Local Reference-Frame Gauge Transformation Invariance
#
# If `'cam_2'` shifts its local compass zero-reference by $+0.9$ rad ($g_2 = R(0.9)$), `apply_gauge_transformation`
# updates adjacent relative measurements covariantly without altering loop curvature or physical alignment.

# %%
gauge = {'cam_2': rot2d(0.9)}
conn_gauged = apply_gauge_transformation(conn, gauge)
assert is_flat_bundle(conn_gauged, faces)
assert verify_gauge_covariance(conn, adjacency, gauge)

recovered_gauged = solve_anchored_headings(conn_gauged)
print('\nAfter +0.90 rad local frame rotation on cam_2:')
print(f'  Recovered cam_2 = {recovered_gauged["cam_2"]:+.4f} (expected {true_headings["cam_2"] + 0.9:+.4f})')
assert math.isclose(recovered_gauged['cam_2'], true_headings['cam_2'] + 0.9, abs_tol=1e-9)

# %% [markdown]
# ## 3. Automated Loop-Closure Fault Detection via Face Holonomy
#
# Suppose a perceptual aliasing bug corrupts the loop-closure measurement on edge `('cam_1', 'cam_2')` by
# $+90^\circ$ ($\pi / 2$). Computing `compute_face_curvature_angle` on every cycle immediately isolates the
# faulty triangle (`cam_0 - cam_1 - cam_2`) while clearing clean triangles (`cam_0 - cam_2 - cam_3`).

# %%
corrupted = DiscreteOrthogonalConnection(fiber_dim=2)
for u, nbrs in adjacency.items():
    for v in nbrs:
        if u < v:
            delta = true_headings[v] - true_headings[u]
            if (u, v) == ('cam_1', 'cam_2'):
                delta += math.pi / 2.0  # Inject +90 deg loop-closure outlier
            corrupted.set_transport(u, v, rot2d(delta))

print('\nLoop-Closure Holonomy Audit:')
assert not is_flat_bundle(corrupted, faces)
for face in faces:
    hol = compute_face_holonomy(corrupted, face)
    err_rad = compute_face_curvature_angle(corrupted, face)
    status = 'FAULT DETECTED' if abs(err_rad) > 1e-6 else 'CLEAN'
    hol_00 = hol.get(0, {}).get(0, 0.0)
    print(f'  Cycle {face}: curvature error = {math.degrees(err_rad):+.2f} deg [{status}] | Hol_00={hol_00:+.3f}')

assert math.isclose(compute_face_curvature_angle(corrupted, faces[0]), math.pi / 2.0, abs_tol=1e-9)
assert math.isclose(compute_face_curvature_angle(corrupted, faces[1]), 0.0, abs_tol=1e-9)
