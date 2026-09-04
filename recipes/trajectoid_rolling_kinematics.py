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
# # Trajectoid Rolling Kinematics & SO(3) Path Tracing
#
# ## Theory & Mathematical Foundation
#
# 1. **2D Planar Trajectory & Velocity Field (`algebrax.analysis.gradient`)**:
#    Trajectoids are custom 3D geometric solids engineered so that rolling them without
#    slipping traces a predetermined 2D planar curve $c(t) = (x(t), y(t))$.
#
# 2. **Non-Holonomic SO(3) Rotation Group Composition (`algebrax.matrix.core.dot`)**:
#    Rolling without slipping couples planar velocity to 3D rotation matrices $R(t) \\in \\text{SO}(3)$.

# %%
import math
from typing import Any

import algebrax as ax


def make_so3_rotation(angle_x: float, angle_y: float, angle_z: float) -> dict[int, dict[int, float]]:
    """Construct 3x3 SO(3) rotation matrix for small angles."""
    cx, sx = math.cos(angle_x), math.sin(angle_x)
    cy, sy = math.cos(angle_y), math.sin(angle_y)
    cz, sz = math.cos(angle_z), math.sin(angle_z)

    return {
        0: {0: cz * cy, 1: cz * sy * sx - sz * cx, 2: cz * sy * cx + sz * sx},
        1: {0: sz * cy, 1: sz * sy * sx + cz * cx, 2: sz * sy * cx - cz * sx},
        2: {0: -sy, 1: cy * sx, 2: cy * cx},
    }


def simulate_trajectoid_kinematics(
    steps: int = 16,
    freq: float = 1.0,
) -> dict[str, Any]:
    """Integrate trajectoid planar coordinates, velocities, and SO(3) rotations."""
    dt = 2.0 * math.pi / steps
    path_x = {t: 5.0 * math.cos(t * dt) for t in range(steps)}
    path_y = {t: 5.0 * math.sin(freq * t * dt) for t in range(steps)}

    time_graph = {t: [(t + 1) % steps] for t in range(steps)}
    grad_x = ax.analysis.gradient(path_x, time_graph)
    grad_y = ax.analysis.gradient(path_y, time_graph)

    vx = {t: grad_x[t][(t + 1) % steps] for t in range(steps)}
    vy = {t: grad_y[t][(t + 1) % steps] for t in range(steps)}

    current_r = {
        0: {0: 1.0, 1: 0.0, 2: 0.0},
        1: {0: 0.0, 1: 1.0, 2: 0.0},
        2: {0: 0.0, 1: 0.0, 2: 1.0},
    }
    for t in range(steps):
        dr = make_so3_rotation(-vy[t] * 0.1, vx[t] * 0.1, 0.0)
        current_r = ax.matrix.dot(current_r, dr)

    sparsity_val = ax.metrics.sparsity(current_r)
    return {
        'path_x': path_x,
        'path_y': path_y,
        'vx': vx,
        'vy': vy,
        'final_rotation': current_r,
        'sparsity': sparsity_val,
    }


# %% [markdown]
# ## Step 1: Target 2D Trajectory & Velocity Field (`analysis.gradient`)


def run_demo() -> None:
    """Run trajectoid kinematics integration and orientation tracing."""
    res = simulate_trajectoid_kinematics(steps=16, freq=1.0)
    path_x = res['path_x']
    path_y = res['path_y']
    vx = res['vx']
    vy = res['vy']

    print('Target 2D Trajectory Path Samples:')
    for t in range(0, 16, 4):
        pos_str = f'({path_x[t]:+6.2f}, {path_y[t]:+6.2f})'
        vel_str = f'({vx[t]:+6.2f}, {vy[t]:+6.2f})'
        print(f'  Time t={t:2d}: Position = {pos_str}, Velocity = {vel_str}')

    print(f'\nFinal Orientation Matrix Sparsity: {res["sparsity"]:.4f}')


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Trajectoid Rolling Kinematics Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
