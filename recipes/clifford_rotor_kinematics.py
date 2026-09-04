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
# # Clifford Geometric Algebra $C\\ell(3,0)$ & 3D Rotor Rotations
#
# ## Theoretical Foundations & Physics
# 1. **Clifford Multivectors**: Unified representation of scalars, vectors, bivectors, and pseudoscalars.
# 2. **Geometric Product** ($AB = A \\cdot B + A \\wedge B$): Replaces matrix
#    transformations with rotor sandwiching ($v' = R v R^\\dagger$).
# 3. **Gimbal-Lock-Free Rotations**: Rotors $R = \\exp(-\\frac{\\theta}{2} B)$ perform
#    smooth spatial rotations without matrix decomposition overhead.

# %%
import math

import algebrax as ax


def apply_rotor_rotation(
    v: dict[tuple[int, ...], float],
    angle_rad: float,
    plane: tuple[int, int] = (1, 2),
    p: int = 3,
    q: int = 0,
    r: int = 0,
) -> dict[tuple[int, ...], float]:
    """Execute sandwich product rotation v' = R v R^dagger in arbitrary Clifford signature."""
    return ax.clifford.rotor_rotation(v, bivector=plane, angle_rad=angle_rad, p=p, q=q, r=r)


def compute_geometric_magnitude(
    v: dict[tuple[int, ...], float],
    p: int = 3,
    q: int = 0,
    r: int = 0,
) -> float:
    """Calculate geometric multivector magnitude |v| = sqrt(scalar(v * v^rev))."""
    cs = ax.clifford.CliffordSemiring(p=p, q=q, r=r)
    v_sq = cs.mul(v, v)
    norm_sq = v_sq.get((), 0.0)
    return math.sqrt(max(0.0, norm_sq))


# %% [markdown]
# ## Step 1: Initial 3D Spatial Vector & Geometric Magnitude ($v^2 = |v|^2$)
#
# ## Step 2: 90-Degree Rotor Rotation in $e_{12}$ Plane ($v' = R v R^\\dagger$)


def run_demo() -> None:
    """Run Clifford multivector rotor rotations and invariant magnitudes."""
    v = {(1,): 3.0, (2,): 4.0}
    print('Initial 3D Spatial Vector v:')
    print(f'  v = {v[(1,)]} e1 + {v[(2,)]} e2')

    mag = compute_geometric_magnitude(v, p=3, q=0, r=0)
    print(f'  Geometric Vector Magnitude |v| = {mag:.2f}')
    assert abs(mag - 5.0) < 1e-6

    v_rot = apply_rotor_rotation(v, angle_rad=math.pi / 2.0, plane=(1, 2), p=3, q=0, r=0)
    print('Vector after 90-degree Rotor Rotation in e12 Plane:')
    print(f"  v' = {v_rot.get((1,), 0.0):.2f} e1 + {v_rot.get((2,), 0.0):.2f} e2")

    assert abs(v_rot.get((1,), 0.0) - (-4.0)) < 1e-6
    assert abs(v_rot.get((2,), 0.0) - 3.0) < 1e-6


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Clifford Geometric Algebra & Rotor Rotations Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
