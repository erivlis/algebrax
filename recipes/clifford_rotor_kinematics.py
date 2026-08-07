r"""
Real-World Use Case: Clifford Geometric Algebra Cl(3,0) & 3D Rotor Rotations.

Theoretical Foundations & Physics:
1. Clifford Multivectors: Unified representation of scalars, vectors, bivectors, and pseudoscalars.
2. Geometric Product (AB = A . B + A ^ B): Replaces matrix transformations with rotor sandwiching (v' = R v R^\dagger).
3. Gimbal-Lock-Free Rotations: Rotors R = exp(-theta/2 * B) perform smooth spatial rotations.
"""

import math

import algebrax as ax


def main() -> None:
    print('--- Clifford Geometric Algebra Cl(3,0) Kinematics ---')

    cs = ax.semiring.CliffordSemiring(p=3, q=0, r=0)

    # Define 3D vector v = 3 e1 + 4 e2
    v = {(1,): 3.0, (2,): 4.0}
    print('\n[1] Initial 3D Spatial Vector v:')
    print(f'  v = {v[(1,)]} e1 + {v[(2,)]} e2')

    # Vector norm via geometric product: v^2 = |v|^2
    v_sq = cs.mul(v, v)
    norm_sq = v_sq.get((), 0.0)
    print(f'  Geometric Vector Squared v^2 = {norm_sq:.2f} (Magnitude |v| = {math.sqrt(norm_sq):.2f})')
    assert abs(norm_sq - 25.0) < 1e-6

    # Rotate vector v around e12 bivector plane by 90 degrees (pi/2 rad)
    v_rot = ax.clifford.rotor_rotation(v, bivector=(1, 2), angle_rad=math.pi / 2.0, p=3, q=0, r=0)
    print('\n[2] Vector after 90-degree Rotor Rotation in e12 Plane:')
    print(f'  v\' = {v_rot.get((1,), 0.0):.2f} e1 + {v_rot.get((2,), 0.0):.2f} e2')

    # Expected: 3 e1 + 4 e2 rotated +90 deg -> -4 e1 + 3 e2
    assert abs(v_rot.get((1,), 0.0) - (-4.0)) < 1e-6
    assert abs(v_rot.get((2,), 0.0) - 3.0) < 1e-6

    print('\nSuccessfully verified Clifford Geometric Algebra & Rotor Rotations!')


if __name__ == '__main__':
    main()
