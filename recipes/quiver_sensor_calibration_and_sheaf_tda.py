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
# # Heterogeneous Multi-Sensor Calibration & Quiver-Sheaf Diagnostics
#
# ## Path Algebras, Gabriel's ADE Trichotomy & Cellular Sheaf Disagreement Energy
# Autonomous robots fuse sensors of **different state dimensions**—such as a 3D LiDAR point-cloud frame
# ($\mathbb{R}^3$), 2D stereo camera image planes ($\mathbb{R}^2$), and a 1D laser altimeter ($\mathbb{R}^1$). Unlike
# homogeneous pose graphs where every node carries the same group dimension, heterogeneous calibration graphs are
# naturally modeled as **Quiver Representations**:
#
# 1. **Multi-Hop Coordinate Composition (`QuiverRepresentation`, `path_algebra`)**: Composes chains of linear sensor
#    projections algebraically in $K Q$, automatically rejecting incompatible sensor hops via orthogonal idempotents
#    and verifying unit-rescaling gauge morphisms.
# 2. **Calibration Solvability (`classify_representation_type`, `tits_quadratic_form`, `gabriel_positive_roots`)**:
#    Applies Gabriel's ADE theorem to classify sensor-wiring diagrams as **finite-type** (discrete root modes, no hidden
#    continuous gauge ambiguity), **tame** (1-parameter matrix-pencil / loop-holonomy modulus), or **wild**.
# 3. **Real-Time Sensor Drift Detection (`to_cellular_sheaf`, `from_cellular_sheaf`)**: Bridges the quiver
#    representation into a 1D `CellularSheaf` to count global consistent state degrees of freedom ($\dim H^0$) and flag
#    miscalibrated camera channels via sheaf Dirichlet disagreement energy.

# %%
from __future__ import annotations

import math

import algebrax as ax
from algebrax.algebra import StandardField, path_algebra
from algebrax.rep import (
    Quiver,
    QuiverRepresentation,
    bgp_reflect_dimension,
    classify_dynkin_type,
    classify_representation_type,
    cycle_quiver,
    dynkin_quiver,
    from_cellular_sheaf,
    gabriel_positive_roots,
    kronecker_quiver,
    tits_quadratic_form,
    to_cellular_sheaf,
)
from algebrax.verification import (
    verify_quiver_morphism_commutation,
    verify_tits_positive_definiteness,
)

# %% [markdown]
# ## 1. Heterogeneous Multi-Sensor Suite & Path Algebra Operator Composition
#
# An aerial drone carries four coordinate frames: `'lidar_3d'` ($\mathbb{R}^3$), `'cam_left'` ($\mathbb{R}^2$),
# `'cam_right'` ($\mathbb{R}^2$), and `'altimeter_1d'` ($\mathbb{R}^1$). Directed arrows represent calibrated linear
# observation/rectification maps. In the path algebra $\mathbb{R}Q$, `p_proj_left * p_rectify` represents the two-hop
# transform `'lidar_3d' -> 'cam_left' -> 'cam_right'`, while invalid sensor chains annihilate to `{}` automatically.

# %%
sensor_quiver = Quiver.from_edges(
    vertices=('lidar_3d', 'cam_left', 'cam_right', 'altimeter_1d'),
    edge_specs=[
        ('proj_left', 'lidar_3d', 'cam_left'),
        ('rectify_lr', 'cam_left', 'cam_right'),
        ('beam_z', 'lidar_3d', 'altimeter_1d'),
    ],
)

sensor_rep = QuiverRepresentation(
    quiver=sensor_quiver,
    dimensions={'lidar_3d': 3, 'cam_left': 2, 'cam_right': 2, 'altimeter_1d': 1},
    edge_maps={
        # Orthographic + shear camera projection R^3 -> R^2
        'proj_left': {
            0: {0: 1.0, 2: 0.25},
            1: {1: 1.0, 2: -0.15},
        },
        # Stereo rectification transform R^2 -> R^2
        'rectify_lr': {
            0: {0: 0.98, 1: -0.05},
            1: {0: 0.05, 1: 1.02},
        },
        # Vertical rangefinder extraction R^3 -> R^1
        'beam_z': {
            0: {2: 1.0},
        },
    },
)

kq = path_algebra(sensor_quiver, StandardField())
p_proj = kq.arrow('proj_left')
p_rectify = kq.arrow('rectify_lr')
two_hop_path = kq.mul(p_proj, p_rectify)
invalid_path = kq.mul(kq.arrow('beam_z'), p_rectify)

assert invalid_path == {}  # Target 'altimeter_1d' != source 'cam_left'

# Evaluate composite two-hop operator lidar_3d -> cam_right in the direct-sum space R^8
direct_product = ax.matrix.dot(sensor_rep.edge_maps['rectify_lr'], sensor_rep.edge_maps['proj_left'])
global_composite = kq.evaluate_in_rep(two_hop_path, sensor_rep)
assert global_composite == ax.matrix.dot(
    kq.evaluate_in_rep(p_rectify, sensor_rep),
    kq.evaluate_in_rep(p_proj, sensor_rep),
)
# Extract the 2x3 block from lidar_3d (cols 0..2) to cam_right (rows 5..6)
cam_right_offset = sensor_rep.dimensions['lidar_3d'] + sensor_rep.dimensions['cam_left']
local_composite = {r - cam_right_offset: row for r, row in global_composite.items()}
assert local_composite == direct_product

print('Heterogeneous Drone Sensor Quiver (A_4 Tree Orientation):')
print(f'  Two-hop path element: {two_hop_path}')
print(f'  Extracted R^3 -> R^2 composite matrix: {local_composite}')

# Verify unit-change morphism (meters -> millimeters on 3D/1D, 2x pixel binning on cameras)
unit_scales = {'lidar_3d': 1000.0, 'cam_left': 0.5, 'cam_right': 0.5, 'altimeter_1d': 1000.0}
rescaled_maps = {
    edge: {
        r: {
            c: val * (unit_scales[sensor_quiver.target[edge]] / unit_scales[sensor_quiver.source[edge]])
            for c, val in row.items()
        }
        for r, row in mat.items()
    }
    for edge, mat in sensor_rep.edge_maps.items()
}
rescaled_rep = QuiverRepresentation(
    quiver=sensor_quiver,
    dimensions=sensor_rep.dimensions,
    edge_maps=rescaled_maps,
)
gauge_morphism = {
    v: {i: {i: unit_scales[v]} for i in range(sensor_rep.dimensions[v])}
    for v in sensor_quiver.vertices
}
assert all(verify_quiver_morphism_commutation(sensor_rep, rescaled_rep, gauge_morphism).values())

# %% [markdown]
# ## 2. Diagnosing Sensor-Network Calibration Topologies via Gabriel's ADE Theorem
#
# Before deploying an extrinsic calibration solver, the **underlying wiring topology** determines whether linear maps
# can harbor continuous unobservable moduli:
# - **Finite ADE ($A_4$ pipeline, $D_4$ 3-sensor star hub)**: Positive-definite Tits form $q_Q(\mathbf{d}) > 0$; every
#   indecomposable coupling corresponds to a discrete positive root $\alpha \in \Phi^+$ with $q_Q(\alpha) = 1$.
# - **Tame Euclidean ($\widetilde{A}_1$ dual stereo, $\widetilde{A}_2$ 3-sensor loop)**: Semidefinite $q_Q(\delta) = 0$,
#   introducing a 1-parameter continuous eigenvalue/holonomy modulus.
# - **Wild ($3$-arrow Kronecker)**: Indefinite $q_Q(\mathbf{d}) < 0$ with undecidable coupled moduli.

# %%
star_hub_d4 = dynkin_quiver('D', 4, orientation='alternating')
dual_stereo = kronecker_quiver(2)
loop_3 = cycle_quiver(3)
triple_wild = kronecker_quiver(3)

topologies = [
    ('Drone 4-Sensor Tree', sensor_quiver, [1, 1, 1, 1]),
    ('Central IMU 3-Sensor Star Hub', star_hub_d4, [1, 2, 1, 1]),
    ('Dual-Mode Stereo Pencils', dual_stereo, [1, 1]),
    ('Closed 3-Sensor Odometry Ring', loop_3, [1, 1, 1]),
    ('Triple-Arrow Redundant Link', triple_wild, [1, 1]),
]

print('\nGabriel ADE Calibration Topology Diagnostic:')
for name, q_net, probe_dim in topologies:
    r_type = classify_representation_type(q_net)
    dynkin = classify_dynkin_type(q_net)
    q_val = tits_quadratic_form(q_net, probe_dim)
    print(f'  {name:<30} | Dynkin={dynkin:<4} | type={r_type:<6} | q_Q({probe_dim}) = {q_val:+d}')

assert all(verify_tits_positive_definiteness(sensor_quiver).values())
assert all(verify_tits_positive_definiteness(star_hub_d4).values())
assert classify_representation_type(dual_stereo) == 'tame'
assert tits_quadratic_form(dual_stereo, [1, 1]) == 0
assert classify_representation_type(loop_3) == 'tame'
assert tits_quadratic_form(loop_3, [1, 1, 1]) == 0
assert classify_representation_type(triple_wild) == 'wild'
assert tits_quadratic_form(triple_wild, [1, 1]) == -1

d4_roots = gabriel_positive_roots(star_hub_d4)
# Reflecting sincere root {0: 1, 1: 1, 2: 1, 3: 1} at hub sink 1 yields highest root {0: 1, 1: 2, 2: 1, 3: 1}
highest_d4_root = bgp_reflect_dimension(star_hub_d4, {0: 1, 1: 1, 2: 1, 3: 1}, 1)
print(f'  D_4 star hub positive roots = {len(d4_roots)}; BGP-reflected highest root = {highest_d4_root}')
assert len(d4_roots) == 12
assert highest_d4_root == {0: 1, 1: 2, 2: 1, 3: 1}
assert highest_d4_root in d4_roots

# %% [markdown]
# ## 3. Quiver-to-Cellular-Sheaf Bridge for Real-Time Sensor Disagreement Auditing
#
# Converting `sensor_rep` into a 1D `CellularSheaf` via `to_cellular_sheaf` equips the heterogeneous calibration graph
# with a symmetric positive-semidefinite Sheaf Laplacian $L_{\mathcal{F}} = \delta_{\mathcal{F}}^T\delta_{\mathcal{F}}$:
# - Its global section space $\dim H^0(G; \mathcal{F}) = 3$ confirms that a single 3D LiDAR target position uniquely
#   determines all downstream 2D camera pixels and 1D altimeter readings, with zero obstruction ($\dim H^1 = 0$).
# - When a mechanical bump corrupts `'cam_right'` by $(+0.4, -0.3)$ pixels, `sheaf.dirichlet_energy` immediately flags
#   the non-zero inconsistency residual while passing clean observations with $E_{\mathcal{F}} = 0$.

# %%
sheaf = to_cellular_sheaf(sensor_rep)
roundtrip_rep = from_cellular_sheaf(sheaf, mode='direct')
assert roundtrip_rep.dimensions == sensor_rep.dimensions

h0_dim = sheaf.global_sections_dimension()
h1_dim = sheaf.first_cohomology_dimension()
print(f'\nSensor Cellular Sheaf Cohomology: dim H^0 = {h0_dim} (3D target DoF), dim H^1 = {h1_dim}')
assert h0_dim == 3
assert h1_dim == 0

# True 3D landmark in LiDAR frame: p = (2.0, -1.0, 4.0) meters
p_lidar = {0: 2.0, 1: -1.0, 2: 4.0}
p_cam_left = ax.matrix.mat_vec(sensor_rep.edge_maps['proj_left'], p_lidar)
p_cam_right = ax.matrix.mat_vec(sensor_rep.edge_maps['rectify_lr'], p_cam_left)
p_altimeter = ax.matrix.mat_vec(sensor_rep.edge_maps['beam_z'], p_lidar)

clean_section: dict[tuple[str, int], float] = {}
for frame, vec in (
    ('lidar_3d', p_lidar),
    ('cam_left', p_cam_left),
    ('cam_right', p_cam_right),
    ('altimeter_1d', p_altimeter),
):
    for coord_idx, val in vec.items():
        clean_section[(frame, coord_idx)] = val

bumped_section = dict(clean_section)
bumped_section[('cam_right', 0)] += 0.40
bumped_section[('cam_right', 1)] -= 0.30

energy_clean = sheaf.dirichlet_energy(clean_section)
energy_bumped = sheaf.dirichlet_energy(bumped_section)

print(f'  Clean multi-sensor observation Dirichlet energy  = {energy_clean:.12f}')
print(f'  Bumped cam_right (+0.40, -0.30) Dirichlet energy = {energy_bumped:.6f} [DRIFT DETECTED]')

assert math.isclose(energy_clean, 0.0, abs_tol=1e-12)
# Exact sheaf residual norm: 0.5 * (0.40^2 + (-0.30)^2) = 0.125
assert math.isclose(energy_bumped, 0.125, abs_tol=1e-12)
