"""
Clifford Geometric Algebra Cl(p, q, r) & Multivector Rotors.

Summary:
    3D & Spacetime Geometric Rotations — rotates vectors using multivector rotors
    without matrix conversions or gimbal lock.

This module provides multivector geometric product AB = A . B + A ^ B over Clifford blade keys
and spatial/spacetime rotor transformations without matrix conversions or gimbal lock.
"""

import math

from algebrax.semiring.algebraic import (
    CliffordSemiring,
    GeneralizedCliffordSemiring,
    QuantumCliffordSemiring,
)
from algebrax.typing import SparseVector


def gca_product(
    a: SparseVector[tuple[int, ...], complex],
    b: SparseVector[tuple[int, ...], complex],
    n_order: int = 3,
    num_generators: int = 2,
    signatures: tuple[complex, ...] | None = None,
) -> SparseVector[tuple[int, ...], complex]:
    """
    Compute the Generalized Clifford Algebra (GCA) product A * B.
    e_j * e_k = omega * e_k * e_j  (for j < k, omega = exp(2*pi*i / n)).

    Args:
        a: First GCA multivector.
        b: Second GCA multivector.
        n_order: Cyclic root-of-unity order n (default 3).
        num_generators: Number of generators m (default 2).
        signatures: Nilpotence signatures alpha_j where e_j^n = alpha_j * 1.

    Returns:
        The GCA product multivector.
    """
    gca = GeneralizedCliffordSemiring(n_order=n_order, num_generators=num_generators, signatures=signatures)
    return gca.mul(a, b)


def quantum_clifford_product(
    a: SparseVector[tuple[int, ...], complex],
    b: SparseVector[tuple[int, ...], complex],
    q: complex = 1.0 + 0j,
    num_generators: int = 2,
    signatures: tuple[complex, ...] | None = None,
) -> SparseVector[tuple[int, ...], complex]:
    """
    Compute the q-Deformed Quantum Clifford product A * B.
    e_j * e_k = -q * e_k * e_j  (for j < k).

    Args:
        a: First quantum multivector.
        b: Second quantum multivector.
        q: Deformation parameter q (default 1.0 + 0j).
        num_generators: Number of generators m (default 2).
        signatures: Signature factors where e_j^2 = alpha_j * 1.

    Returns:
        The Quantum Clifford product multivector.
    """
    qc = QuantumCliffordSemiring(q=q, num_generators=num_generators, signatures=signatures)
    return qc.mul(a, b)


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
