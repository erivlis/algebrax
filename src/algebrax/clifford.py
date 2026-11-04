"""
Clifford Geometric Algebra Cl(p, q, r), Generalized & Quantum Clifford Algebras, and Multivector Rotors.

Summary:
    3D & Spacetime Geometric Rotations — rotates vectors using multivector rotors
    without matrix conversions or gimbal lock.

This module provides multivector geometric product AB = A . B + A ^ B over Clifford blade keys,
generalized clock-and-shift algebras, braided quantum Clifford algebras, and spatial/spacetime
rotor transformations without matrix conversions or gimbal lock.
"""

from __future__ import annotations

import cmath
import math
from collections.abc import Iterable

from algebrax.algebra._monoid_algebra import QuotientMonoidAlgebraSemiring
from algebrax.semiring.arithmetic import StandardSemiring
from algebrax.typing import SparseVector

__all__ = [
    'CliffordAlgebra',
    'GeneralizedCliffordAlgebra',
    'QuantumCliffordAlgebra',
    'gca_product',
    'geometric_product',
    'quantum_clifford_product',
    'rotor_rotation',
]


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
            elif idx <= p + q + r:
                return []  # e_k^2 = 0 degenerate generator
            else:
                raise ValueError(f'Generator index {idx} exceeds Clifford dimension p+q+r={p + q + r}')
            i += 2
        else:
            canonical.append(combined[i])
            i += 1

    return [(tuple(canonical), sign)]


class CliffordAlgebra(QuotientMonoidAlgebraSemiring[tuple[int, ...], float]):
    r"""The Clifford Geometric Algebra $\mathcal{C}\ell(p, q, r)$ over $\mathbb{R}$.

    Algebraic Signature:
        $\langle \mathcal{C}\ell(p, q, r), +, \wedge_{\mathcal{C}\ell}, \emptyset, \{(): 1.0\} \rangle$

    Carrier:
        `dict[tuple[int, ...], float]` (Sparse multivectors mapping sorted basis blades to real coefficients).

    Operations:
        - Addition ($+$): Elementwise multivector addition.
        - Multiplication ($\wedge_{\mathcal{C}\ell}$): Geometric product with basis blade reduction $e_i^2 = +1, -1, 0$.
        - Negation ($-a$): Blade-wise sign flip.
        - Subtraction ($a - b$): Direct elementwise difference with zero-cleaning.
        - Scalar Multiplication ($r \cdot m$): Real scalar scaling.
        - Zero Element ($\mathbb{0}$): `{}` (empty multivector).
        - One Element ($\mathbb{1}$): `{(): 1.0}` (scalar unit blade).

    Properties:
        Associative, non-commutative graded geometric algebra, distributive, satisfies Ring and Algebra protocols.

    Applications:
        Rotations and reflections, computer vision, robotics, relativistic physics.
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

    def neg(self, a: SparseVector[tuple[int, ...], float]) -> SparseVector[tuple[int, ...], float]:
        """Additive inverse of a multivector with zero-cleaning."""
        return {k: -v for k, v in a.items() if abs(v) > 1e-14}

    def sub(
        self,
        a: SparseVector[tuple[int, ...], float],
        b: SparseVector[tuple[int, ...], float],
    ) -> SparseVector[tuple[int, ...], float]:
        """Direct elementwise difference: a - b."""
        result = dict(a)
        for k, v in b.items():
            diff = result.get(k, 0.0) - v
            if abs(diff) > 1e-14:
                result[k] = diff
            elif k in result:
                del result[k]
        return result

    def smul(self, r: float, m: SparseVector[tuple[int, ...], float]) -> SparseVector[tuple[int, ...], float]:
        """Scalar multiplication: r * m."""
        if abs(r) <= 1e-14:
            return {}
        return {k: r * v for k, v in m.items() if abs(r * v) > 1e-14}



def _gca_blade_mul(
    k1: tuple[int, ...],
    k2: tuple[int, ...],
    n_order: int = 3,
    num_generators: int = 2,
    signatures: tuple[complex, ...] | None = None,
) -> list[tuple[tuple[int, ...], complex]]:
    """
    Canonical basis reduction for Generalized Clifford Algebra C_n^(m).
    Generators satisfy:
        e_j * e_k = omega * e_k * e_j  (for j < k, omega = exp(2*pi*i / n))
        e_j^n = alpha_j * 1  (default alpha_j = 1.0)
    Keys are non-negative integer exponent tuples (k_1, ..., k_m) with 0 <= k_j < n.
    """
    m = num_generators
    sigs = tuple([1.0 + 0j] * m) if signatures is None else signatures
    k1_pad = tuple(k1) + (0,) * max(0, m - len(k1))
    k2_pad = tuple(k2) + (0,) * max(0, m - len(k2))

    phase_exp = 0
    scalar_mult = 1.0 + 0j
    res_k: list[int] = []

    for j in range(m):
        for k in range(j + 1, m):
            phase_exp = (phase_exp - k1_pad[k] * k2_pad[j]) % n_order

    for j in range(m):
        tot = k1_pad[j] + k2_pad[j]
        res_k.append(tot % n_order)
        if tot >= n_order:
            scalar_mult *= sigs[j] ** (tot // n_order)

    omega = cmath.exp(2j * cmath.pi / n_order)
    phase_factor = (omega**phase_exp) * scalar_mult
    return [(tuple(res_k), phase_factor)]


class GeneralizedCliffordAlgebra(QuotientMonoidAlgebraSemiring[tuple[int, ...], complex]):
    r"""The Generalized Clifford Algebra $C_n^{(m)}$ Semiring (Clock-and-Shift Algebra).

    Algebraic Signature:
        $\langle C_n^{(m)}, +, \ast_{\mathrm{GCA}}, \emptyset, \{(0, \dots, 0): 1+0j\} \rangle$

    Carrier:
        `dict[tuple[int, ...], complex]` (Sparse map from exponent $m$-tuples in $\mathbb{Z}_n^m$ to complex values).

    Operations:
        - Addition ($+$): Elementwise complex multivector addition.
        - Multiplication ($\ast_{\mathrm{GCA}}$): Braiding $e_j e_k = \omega e_k e_j$ ($\omega = e^{2\pi i/n}$),
          $e_j^n = \alpha_j \mathbf{1}$.
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{(0, ..., 0): 1+0j}`.

    Properties:
        Associative, non-commutative, $\mathbb{Z}_n$-graded quotient algebra.

    Applications:
        Higher-order Weyl-Heisenberg groups, parafermion zero modes, quantum error correction over qudits.
    """

    def __init__(
        self,
        n_order: int = 3,
        num_generators: int = 2,
        signatures: tuple[complex, ...] | None = None,
    ):
        self.n_order = n_order
        self.num_generators = num_generators
        self.signatures = signatures

        def key_op(k1: tuple[int, ...], k2: tuple[int, ...]) -> tuple[int, ...]:
            k1_p = tuple(k1) + (0,) * max(0, self.num_generators - len(k1))
            k2_p = tuple(k2) + (0,) * max(0, self.num_generators - len(k2))
            return k1_p + k2_p

        def quotient_fn(key: tuple[int, ...], coeff: complex) -> Iterable[tuple[tuple[int, ...], complex]]:
            k1 = key[: self.num_generators]
            k2 = key[self.num_generators :]
            reds = _gca_blade_mul(
                k1, k2, n_order=self.n_order, num_generators=self.num_generators, signatures=self.signatures
            )
            return [(k, c * coeff) for k, c in reds]

        super().__init__(
            coeff_semiring=StandardSemiring[complex](),
            key_op=key_op,
            zero_key=tuple([0] * num_generators),
            quotient_fn=quotient_fn,
        )



def _quantum_clifford_blade_mul(
    k1: tuple[int, ...],
    k2: tuple[int, ...],
    q: complex = 1.0 + 0j,
    num_generators: int = 2,
    signatures: tuple[complex, ...] | None = None,
) -> list[tuple[tuple[int, ...], complex]]:
    """
    Canonical basis reduction for q-Deformed Quantum Clifford Algebra Cl_q(m).
    Generators satisfy:
        e_j * e_k = -q * e_k * e_j  (for j < k)
        e_j^2 = alpha_j * 1  (default alpha_j = 1.0)
    Keys are binary index tuples (k_1, ..., k_m) with k_j in {0, 1}.
    """
    m = num_generators
    sigs = tuple([1.0 + 0j] * m) if signatures is None else signatures
    k1_pad = tuple(k1) + (0,) * max(0, m - len(k1))
    k2_pad = tuple(k2) + (0,) * max(0, m - len(k2))

    inversions = 0
    scalar_mult = 1.0 + 0j
    res_k: list[int] = []

    for j in range(m):
        for k in range(j + 1, m):
            inversions += k1_pad[k] * k2_pad[j]

    for j in range(m):
        tot = k1_pad[j] + k2_pad[j]
        res_k.append(tot % 2)
        if tot >= 2:
            scalar_mult *= sigs[j] ** (tot // 2)

    phase_factor = ((-q) ** inversions) * scalar_mult
    return [(tuple(res_k), phase_factor)]


class QuantumCliffordAlgebra(QuotientMonoidAlgebraSemiring[tuple[int, ...], complex]):
    r"""The $q$-Deformed Quantum Clifford Algebra $\mathcal{C}\ell_q(m)$ Semiring.

    Algebraic Signature:
        $\langle \mathcal{C}\ell_q(m), +, \ast_q, \emptyset, \{(0, \dots, 0): 1+0j\} \rangle$

    Carrier:
        `dict[tuple[int, ...], complex]` (Sparse map from binary multi-indices $\{0, 1\}^m$ to complex amplitudes).

    Operations:
        - Addition ($+$): Elementwise complex multivector addition.
        - Multiplication ($\ast_q$): Braided product with $e_j e_k = -q e_k e_j$ ($j < k$)
          and $e_j^2 = \alpha_j \mathbf{1}$.
        - Zero Element ($\mathbb{0}$): `{}` (empty multivector).
        - One Element ($\mathbb{1}$): `{(0, ..., 0): 1+0j}`.

    Properties:
        Braided, associative, recovers standard Clifford algebra when $q = 1$.

    Applications:
        Quantum groups, anyonic statistics, topological quantum computing.
    """

    def __init__(
        self,
        q: complex = 1.0 + 0j,
        num_generators: int = 2,
        signatures: tuple[complex, ...] | None = None,
    ):
        self.q = q
        self.num_generators = num_generators
        self.signatures = signatures

        def key_op(k1: tuple[int, ...], k2: tuple[int, ...]) -> tuple[int, ...]:
            k1_p = tuple(k1) + (0,) * max(0, self.num_generators - len(k1))
            k2_p = tuple(k2) + (0,) * max(0, self.num_generators - len(k2))
            return k1_p + k2_p

        def quotient_fn(key: tuple[int, ...], coeff: complex) -> Iterable[tuple[tuple[int, ...], complex]]:
            k1 = key[: self.num_generators]
            k2 = key[self.num_generators :]
            reds = _quantum_clifford_blade_mul(
                k1, k2, q=self.q, num_generators=self.num_generators, signatures=self.signatures
            )
            return [(k, c * coeff) for k, c in reds]

        super().__init__(
            coeff_semiring=StandardSemiring[complex](),
            key_op=key_op,
            zero_key=tuple([0] * num_generators),
            quotient_fn=quotient_fn,
        )



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
    gca = GeneralizedCliffordAlgebra(n_order=n_order, num_generators=num_generators, signatures=signatures)
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
    qc = QuantumCliffordAlgebra(q=q, num_generators=num_generators, signatures=signatures)
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
    cs = CliffordAlgebra(p=p, q=q, r=r)
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
    cs = CliffordAlgebra(p=p, q=q, r=r)
    half_a = angle_rad / 2.0
    c = math.cos(half_a)
    s = math.sin(half_a)

    # Rotor R = cos(half_a) - sin(half_a) * bivector
    rotor_r = {(): c, bivector: -s}
    rotor_r_dag = {(): c, bivector: s}

    # v' = R * v * R^dag
    r_v = cs.mul(rotor_r, v)
    return cs.mul(r_v, rotor_r_dag)
