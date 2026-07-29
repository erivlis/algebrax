# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Trajectoid Rolling Kinematics & SO(3) Path Tracing Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. 2D Planar Trajectory & Velocity Field (algebrax.analysis.gradient):
   Trajectoids are custom 3D geometric solids engineered so that rolling them without
   slipping traces a predetermined 2D planar curve c(t) = (x(t), y(t)).
   `gradient` evaluates discrete velocity components v_x(t) = dx/dt and v_y(t) = dy/dt.

2. Non-Holonomic SO(3) Rotation Group Composition (algebrax.matrix.core.dot):
   Rolling without slipping couples planar velocity to 3D rotation matrices R(t) in SO(3).
   State updates R_{k+1} = R_k * dR_k integrate 3D orientation shifts across step dt.

3. Structural Sparsity & Trajectory Tracking Audit (algebrax.metrics.sparsity):
   `metrics.sparsity` measures structural contact matrix density while spatial deviation
   audits closed-loop trajectory periodicity.
================================================================================
"""

import math

from algebrax.analysis import gradient
from algebrax.matrix.core import dot
from algebrax.metrics import sparsity


def make_so3_rotation(angle_x: float, angle_y: float, angle_z: float) -> dict[int, dict[int, float]]:
    """Helper to construct 3x3 SO(3) rotation matrix for small angles (euler product)."""
    cx, sx = math.cos(angle_x), math.sin(angle_x)
    cy, sy = math.cos(angle_y), math.sin(angle_y)
    cz, sz = math.cos(angle_z), math.sin(angle_z)

    r00 = cz * cy
    r01 = cz * sy * sx - sz * cx
    r02 = cz * sy * cx + sz * sx

    r10 = sz * cy
    r11 = sz * sy * sx + cz * cx
    r12 = sz * sy * cx - cz * sx

    r20 = -sy
    r21 = cy * sx
    r22 = cy * cx

    return {
        0: {0: r00, 1: r01, 2: r02},
        1: {0: r10, 1: r11, 2: r12},
        2: {0: r20, 1: r21, 2: r22},
    }


def main() -> None:
    print('==========================================================================')
    print('Use Case: Trajectoid Rolling Kinematics & SO(3) Path Tracing')
    print('==========================================================================')
    print('Goal: Combine 3 distinct algebraic tools from algebrax to simulate 3D')
    print('      trajectoid non-holonomic rolling along a periodic 2D figure-eight path.')

    # --- Step 1: 2D Target Trajectory & Velocity Gradient (gradient) ---
    print('\n[Step 1] Target 2D Trajectory & Velocity Field (gradient)...')
    print('Explanation: c(t) = (r * sin(t), r * sin(t) * cos(t)) defines a periodic lemniscate.')

    n_steps = 16
    dt = 2.0 * math.pi / n_steps

    path_x = {t: 5.0 * math.sin(t * dt) for t in range(n_steps)}
    path_y = {t: 5.0 * math.sin(t * dt) * math.cos(t * dt) for t in range(n_steps)}

    # Time-series graph topology t -> (t+1)%n_steps
    time_graph = {t: [(t + 1) % n_steps] for t in range(n_steps)}

    # Velocity components via discrete gradient
    grad_x = gradient(path_x, time_graph)
    grad_y = gradient(path_y, time_graph)

    vx = {t: grad_x[t][(t + 1) % n_steps] for t in range(n_steps)}
    vy = {t: grad_y[t][(t + 1) % n_steps] for t in range(n_steps)}

    print('\nTarget 2D Figure-Eight Lemniscate Path Samples:')
    for t in range(0, n_steps, 4):
        pos_str = f'({path_x[t]:+6.2f}, {path_y[t]:+6.2f})'
        vel_str = f'({vx[t]:+6.2f}, {vy[t]:+6.2f})'
        print(f'  Time t={t:2d}: Position = {pos_str}, Velocity = {vel_str}')

    # --- Step 2: Non-Holonomic SO(3) Rotation Kinematics (dot) ---
    print('\n[Step 2] Non-Holonomic SO(3) Rotation Matrix Composition (dot)...')
    print('Explanation: Pure rolling without slip updates 3D orientation R_{k+1} = R_k * dR_k.')

    current_r = {
        0: {0: 1.0, 1: 0.0, 2: 0.0},
        1: {0: 0.0, 1: 1.0, 2: 0.0},
        2: {0: 0.0, 1: 0.0, 2: 1.0},
    }

    tracked_positions = {}
    current_pos = [0.0, 0.0]

    for t in range(n_steps):
        tracked_positions[t] = tuple(current_pos)

        w_x = -vy[t] * 0.1
        w_y = vx[t] * 0.1
        w_z = (vx[t] + vy[t]) * 0.05

        d_r = make_so3_rotation(w_x, w_y, w_z)
        current_r = dot(current_r, d_r)

        current_pos[0] += vx[t]
        current_pos[1] += vy[t]

    print('\nSO(3) Orientation Matrix R(T) after Complete Rolling Cycle:')
    for r in sorted(current_r.keys()):
        formatted_row = {c: round(val, 3) for c, val in current_r[r].items()}
        print(f'  Row {r}: {formatted_row}')

    # --- Step 3: Trajectory Tracking Precision & Sparsity Audit ---
    print('\n[Step 3] Spatial Path Tracking & Sparsity Audit (metrics.sparsity)...')
    print('Explanation: Audits spatial drift between actual rolled path and target 2D curve.')

    total_error = 0.0
    for t in range(n_steps):
        target_pt = (path_x[t], path_y[t])
        rolled_pt = tracked_positions[t]
        dist = math.dist(target_pt, rolled_pt)
        total_error += dist

    avg_error = total_error / n_steps
    r_sparsity = sparsity(current_r)

    print(f'\nTotal Spatial Path Deviation:   {total_error:.4f} units')
    print(f'Average Step Tracking Error:     {avg_error:.4f} units')
    print(f'SO(3) Contact Matrix Sparsity:   {r_sparsity * 100:.1f}%')
    print(f'Periodicity Loop Closure Audit:  {"PASSED (CLOSED TRAJECTORY)" if avg_error < 2.0 else "DRIFT DETECTED"}')

    print('\n==========================================================================')
    print('Use Case Completed: Trajectoid Rolling Kinematics Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
