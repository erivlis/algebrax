"""
Clifford Geometric Algebra Cl(p, q, r) & Multivector Rotors.

Summary:
    3D & Spacetime Geometric Rotations — rotates vectors using multivector rotors
    without matrix conversions or gimbal lock.

This module provides multivector geometric product AB = A . B + A ^ B over Clifford blade keys
and spatial/spacetime rotor transformations without matrix conversions or gimbal lock.
"""

import math

from algebrax.semiring.algebraic import CliffordSemiring
from algebrax.typing import SparseVector


def geometric_product(
        a: SparseVector[tuple[int, ...], float],
        b: SparseVector[tuple[int, ...], float],
        p: int = 3,
        q: int = 0,
        r: int = 0,
) -> SparseVector[tuple[int, ...], float]:
    """
    Compute the Clifford Geometric Product A * B over blade keys.

    Args:
        a: First multivector vector (mapping blade index tuples to float coefficients).
        b: Second multivector vector.
        p: Number of positive-signature basis vectors (default 3).
        q: Number of negative-signature basis vectors (default 0).
        r: Number of zero-signature basis vectors (default 0).

    Returns:
        The geometric product multivector.

    Example:
        >>> e1 = {(0,): 1.0}
        >>> e2 = {(1,): 1.0}
        >>> prod = geometric_product(e1, e2, p=3)
        >>> prod == {(0, 1): 1.0}
        True
    """
    cs = CliffordSemiring(p=p, q=q, r=r)
    return cs.mul(a, b)


def rotor_rotation(
        v: SparseVector[tuple[int, ...], float],
        bivector: tuple[int, int],
        angle_rad: float,
        p: int = 3,
        q: int = 0,
        r: int = 0,
) -> SparseVector[tuple[int, ...], float]:
    """
    Rotate a vector/multivector v using Rotor R = exp(-theta/2 * B) = cos(theta/2) - sin(theta/2) * B.
    v' = R * v * R^dag.

    Args:
        v: Vector or multivector to rotate.
        bivector: Plane of rotation tuple, e.g. (0, 1) for the xy-plane.
        angle_rad: Rotation angle in radians.
        p: Number of positive basis vectors.
        q: Number of negative basis vectors.
        r: Number of zero basis vectors.

    Returns:
        Rotated vector/multivector.

    Example:
        >>> import math
        >>> v = {(0,): 1.0}  # x-axis unit vector
        >>> v_rot = rotor_rotation(v, bivector=(0, 1), angle_rad=math.pi / 2)
        >>> math.isclose(v_rot.get((1,), 0.0), 1.0, abs_tol=1e-6)
        True
    """
    cs = CliffordSemiring(p=p, q=q, r=r)
    half_a = angle_rad / 2.0
    c = math.cos(half_a)
    s = math.sin(half_a)

    # Rotor R = cos(half_a) - sin(half_a) * bivector
    rotor_r = {(): c, bivector: -s}
    rotor_r_dag = {(): c, bivector: s}

    # v' = R * v * R^dag
    r_v = cs.mul(rotor_r, v)
    return cs.mul(r_v, rotor_r_dag)
