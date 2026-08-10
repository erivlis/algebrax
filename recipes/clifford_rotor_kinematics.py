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
# # Clifford Geometric Algebra $C\ell(3,0)$ & 3D Rotor Rotations
#
# ## Theoretical Foundations & Physics
# 1. **Clifford Multivectors**: Unified representation of scalars, vectors, bivectors, and pseudoscalars.
# 2. **Geometric Product** ($AB = A \cdot B + A \wedge B$): Replaces matrix
#    transformations with rotor sandwiching ($v' = R v R^\dagger$).
# 3. **Gimbal-Lock-Free Rotations**: Rotors $R = \exp(-\frac{\theta}{2} B)$ perform
#    smooth spatial rotations without matrix decomposition overhead.

# %%
import math

import algebrax as ax

# %% [markdown]
# ## Step 1: Initial 3D Spatial Vector & Geometric Magnitude ($v^2 = |v|^2$)

# %%
cs = ax.semiring.CliffordSemiring(p=3, q=0, r=0)

v = {(1,): 3.0, (2,): 4.0}
print("Initial 3D Spatial Vector v:")
print(f"  v = {v[(1,)]} e1 + {v[(2,)]} e2")

v_sq = cs.mul(v, v)
norm_sq = v_sq.get((), 0.0)
print(f"  Geometric Vector Squared v^2 = {norm_sq:.2f} (Magnitude |v| = {math.sqrt(norm_sq):.2f})")
assert abs(norm_sq - 25.0) < 1e-6

# %% [markdown]
# ## Step 2: 90-Degree Rotor Rotation in $e_{12}$ Plane ($v' = R v R^\dagger$)

# %%
v_rot = ax.clifford.rotor_rotation(v, bivector=(1, 2), angle_rad=math.pi / 2.0, p=3, q=0, r=0)
print("Vector after 90-degree Rotor Rotation in e12 Plane:")
print(f"  v' = {v_rot.get((1,), 0.0):.2f} e1 + {v_rot.get((2,), 0.0):.2f} e2")

assert abs(v_rot.get((1,), 0.0) - (-4.0)) < 1e-6
assert abs(v_rot.get((2,), 0.0) - 3.0) < 1e-6


def main() -> None:
    """Entry point for CLI execution."""
    print("==========================================================================")
    print("Recipe: Clifford Geometric Algebra & Rotor Rotations Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
