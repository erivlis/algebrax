"""
Clifford Geometric Algebra Cl(p, q, r) & Multivector Rotors (EP-0111).

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
    Compute the Clifford Geometric Product A * B.
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
