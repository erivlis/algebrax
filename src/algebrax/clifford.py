"""
Clifford Geometric Algebra Cl(p, q, r) & Multivector Rotors (EP-0111).

This module provides multivector geometric product AB = A . B + A ^ B over Clifford blade keys
and spatial/spacetime rotor transformations without matrix conversions or gimbal lock.
"""

import math
from collections.abc import Iterable

from algebrax.semiring import QuotientMonoidAlgebraSemiring, StandardSemiring
from algebrax.typing import SparseVector


def _clifford_blade_mul(
    k1: tuple[int, ...], k2: tuple[int, ...], p: int = 3, q: int = 0, r: int = 0
) -> list[tuple[tuple[int, ...], float]]:
    """
    Canonical blade reduction for Clifford Algebra Cl(p, q, r).
    e_i^2 = +1 (i <= p), -1 (p < i <= p+q), 0 (i > p+q).
    """
    combined = list(k1 + k2)
    n = len(combined)
    sign = 1.0

    # Insertion sort to count inversions (sign flips)
    for i in range(n):
        for j in range(i + 1, n):
            if combined[i] > combined[j]:
                combined[i], combined[j] = combined[j], combined[i]
                sign = -sign

    # Reduce adjacent pairs (e_i * e_i)
    canonical: list[int] = []
    i = 0
    while i < len(combined):
        if i + 1 < len(combined) and combined[i] == combined[i + 1]:
            idx = combined[i]
            if idx <= p:
                sign *= 1.0
            elif idx <= p + q:
                sign *= -1.0
            else:
                return []  # e_k^2 = 0 degenerate
            i += 2
        else:
            canonical.append(combined[i])
            i += 1

    return [(tuple(canonical), sign)]


class CliffordSemiring(QuotientMonoidAlgebraSemiring[tuple[int, ...], float]):
    """
    Clifford Geometric Algebra Cl(p, q, r) Semiring.
    Values are multivectors represented as dict[tuple[int, ...], float].
    """

    def __init__(self, p: int = 3, q: int = 0, r: int = 0):
        self.p = p
        self.q = q
        self.r = r

        def key_op(k1: tuple[int, ...], k2: tuple[int, ...]) -> tuple[int, ...]:
            return k1 + k2

        def quotient_fn(key: tuple[int, ...], coeff: float) -> Iterable[tuple[tuple[int, ...], float]]:
            reds = _clifford_blade_mul(key, (), p=self.p, q=self.q, r=self.r)
            return [(k, c * coeff) for k, c in reds]

        super().__init__(
            coeff_semiring=StandardSemiring[float](),
            key_op=key_op,
            zero_key=(),
            quotient_fn=quotient_fn,
        )


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
