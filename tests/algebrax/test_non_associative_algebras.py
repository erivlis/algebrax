"""Tests for EP-0204: Jordan, Alternative, Octonion, Malcev, and Poisson Algebras."""

from __future__ import annotations

import pytest

from algebrax.algebra import (
    AlternativeAlgebra,
    ImaginaryOctonionMalcevAlgebra,
    JordanAlgebra,
    MalcevAlgebra,
    NonAssocAlgebra,
    OctonionAlgebra,
    PoissonAlgebra,
    StandardField,
    SymmetricMatrixJordanAlgebra,
)
from algebrax.verification import (
    semiring_elements_equal,
    verify_alternative_laws,
    verify_jordan_laws,
    verify_malcev_laws,
    verify_non_assoc_algebra_laws,
    verify_poisson_laws,
)


def test_symmetric_matrix_jordan_algebra_laws() -> None:
    jordan = SymmetricMatrixJordanAlgebra()
    assert isinstance(jordan, JordanAlgebra)
    assert isinstance(jordan, NonAssocAlgebra)
    assert jordan.zero == {}

    m1 = {0: {0: 2.0, 1: 1.0}, 1: {0: 1.0, 1: 3.0}}
    m2 = {0: {0: -1.0, 1: 4.0}, 1: {0: 4.0, 1: 2.0}}
    m3 = {0: {0: 0.5, 1: -2.0}, 1: {0: -2.0, 1: 1.5}}

    assert jordan.sub(m1, m1) == {}
    assert jordan.smul(2.0, {0: {0: 1.5}}) == {0: {0: 3.0}}
    assert jordan.smul(0.0, m1) == {}

    res = verify_jordan_laws(jordan, [m1, m2, m3])
    assert all(res.values())

    na_res = verify_non_assoc_algebra_laws(jordan, StandardField(float), [-1.0, 0.5, 2.0], [m1, m2, m3])
    assert all(na_res.values())


def test_octonion_algebra_alternative_and_division_laws() -> None:
    octo = OctonionAlgebra()
    assert isinstance(octo, AlternativeAlgebra)
    assert isinstance(octo, NonAssocAlgebra)
    assert octo.zero == {}
    assert octo.one == {0: 1.0}
    assert octo.smul(0.0, {1: 3.0}) == {}

    e1 = {1: 1.0}
    e2 = {2: 1.0}
    e4 = {4: 1.0}

    # Verify non-associativity on (e1 * e2) * e4 != e1 * (e2 * e4)
    assoc_124 = octo.associator(e1, e2, e4)
    assert assoc_124 == {7: 2.0}

    # Verify alternative laws on non-trivial octonions
    a = {0: 1.0, 1: 2.0, 3: -1.0, 6: 0.5}
    b = {0: -0.5, 2: 1.5, 4: 2.0, 7: -1.0}
    c = {1: -1.0, 2: 0.5, 5: 3.0}

    alt_res = verify_alternative_laws(octo, [a, b, c])
    assert all(alt_res.values())

    # Verify Hurwitz norm composition law: ||a * b||^2 == ||a||^2 * ||b||^2
    ab = octo.mul(a, b)
    assert abs(octo.norm_sq(ab) - octo.norm_sq(a) * octo.norm_sq(b)) < 1e-10

    # Verify multiplicative inverse: a * a^-1 == 1 and a^-1 * a == 1
    a_inv = octo.inv(a)
    assert semiring_elements_equal(octo.mul(a, a_inv), octo.one, tol=1e-10)
    assert semiring_elements_equal(octo.mul(a_inv, a), octo.one, tol=1e-10)
    assert octo.sub(a, a) == {}

    with pytest.raises(ZeroDivisionError, match='Cannot invert zero octonion'):
        octo.inv({})


def test_imaginary_octonion_malcev_algebra_laws() -> None:
    malcev = ImaginaryOctonionMalcevAlgebra()
    assert isinstance(malcev, MalcevAlgebra)
    assert malcev.zero == {}
    assert malcev.smul(2.0, {1: 1.5}) == {1: 3.0}

    x = {1: 1.0, 2: -0.5, 4: 2.0}
    y = {2: 1.0, 3: 1.5, 6: -1.0}
    z = {1: -0.5, 5: 1.0, 7: 2.0}

    res = verify_malcev_laws(malcev, [x, y, z])
    assert all(res.values())


def test_poisson_algebra_protocol_and_laws() -> None:
    # Canonical 2D phase space polynomial Poisson algebra over span{1, q, p, qp}
    # {q^a p^b, q^c p^d} = (a*d - b*c) q^{a+c-1} p^{b+d-1}
    class PhaseSpacePoisson(PoissonAlgebra[float, dict[tuple[int, int], float]]):
        @property
        def zero(self) -> dict[tuple[int, int], float]:
            return {}

        def add(
            self,
            a: dict[tuple[int, int], float],
            b: dict[tuple[int, int], float],
        ) -> dict[tuple[int, int], float]:
            out = dict(a)
            for k, v in b.items():
                nv = out.get(k, 0.0) + v
                if abs(nv) > 1e-12:
                    out[k] = nv
                else:
                    out.pop(k, None)
            return out

        def neg(self, a: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
            return {k: -v for k, v in a.items() if abs(v) > 1e-12}

        def smul(self, r: float, m: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
            return {k: r * v for k, v in m.items() if abs(r * v) > 1e-12}

        def mul(
            self,
            a: dict[tuple[int, int], float],
            b: dict[tuple[int, int], float],
        ) -> dict[tuple[int, int], float]:
            out: dict[tuple[int, int], float] = {}
            for (qa, pa), va in a.items():
                for (qb, pb), vb in b.items():
                    key = (qa + qb, pa + pb)
                    nv = out.get(key, 0.0) + va * vb
                    if abs(nv) > 1e-12:
                        out[key] = nv
                    else:
                        out.pop(key, None)
            return out

        def bracket(
            self,
            a: dict[tuple[int, int], float],
            b: dict[tuple[int, int], float],
        ) -> dict[tuple[int, int], float]:
            out: dict[tuple[int, int], float] = {}
            for (qa, pa), va in a.items():
                for (qb, pb), vb in b.items():
                    coeff = float(qa * pb - pa * qb) * va * vb
                    if abs(coeff) <= 1e-12:
                        continue
                    key = (qa + qb - 1, pa + pb - 1)
                    if key[0] < 0 or key[1] < 0:
                        continue
                    nv = out.get(key, 0.0) + coeff
                    if abs(nv) > 1e-12:
                        out[key] = nv
                    else:
                        out.pop(key, None)
            return out

    poisson = PhaseSpacePoisson()
    assert isinstance(poisson, PoissonAlgebra)

    q = {(1, 0): 1.0}
    p = {(0, 1): 1.0}
    qp = {(1, 1): 1.0}

    assert poisson.bracket(q, p) == {(0, 0): 1.0}
    res = verify_poisson_laws(poisson, [q, p, qp])
    assert all(res.values())


def test_non_assoc_verifiers_negative_cases() -> None:
    class BadNonAssoc:
        @property
        def zero(self) -> int:
            return 0

        def add(self, a: int, b: int) -> int:
            return a + b

        def neg(self, a: int) -> int:
            return -a

        def mul(self, a: int, b: int) -> int:
            return a - 2 * b  # Non-commutative, non-alternative, non-anticommutative

        def bracket(self, a: int, b: int) -> int:
            return a + b + 1  # Violates anticommutativity, Jacobi, and Leibniz

    bad = BadNonAssoc()
    j_res = verify_jordan_laws(bad, [1, 2, 3])
    assert not j_res['commutativity']
    assert not j_res['jordan_identity']

    alt_res = verify_alternative_laws(bad, [1, 2, 3])
    assert not alt_res['left_alternative']
    assert not alt_res['right_alternative']
    assert not alt_res['flexible']

    m_res = verify_malcev_laws(bad, [1, 2, 3])
    assert not m_res['anticommutativity']
    assert not m_res['malcev_identity']

    p_res = verify_poisson_laws(bad, [1, 2, 3])
    assert not p_res['anticommutativity']
    assert not p_res['jacobi_identity']
    assert not p_res['leibniz_rule']

