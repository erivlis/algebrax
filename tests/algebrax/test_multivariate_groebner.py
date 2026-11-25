"""Unit, law-verification, and falsification tests for MultivariatePolynomialAlgebra and GroebnerIdeal."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from algebrax.algebra import (
    Algebra,
    CommRing,
    Field,
    FinitelyGeneratedIdeal,
    GaloisField,
    GroebnerIdeal,
    HasBasis,
    HasDerivation,
    Ideal,
    ModularField,
    MultivariatePolynomialAlgebra,
    PoissonAlgebra,
    QuotientRing,
    StandardField,
    groebner_basis,
    monomial_add,
    monomial_divides,
    monomial_lcm,
    monomial_sub,
    order_key_grevlex,
    order_key_grlex,
    order_key_lex,
)
from algebrax.semiring import StandardSemiring
from algebrax.verification import (
    verify_algebra_laws,
    verify_comm_ring_laws,
    verify_field_laws,
    verify_groebner_basis_laws,
    verify_ideal_absorption_laws,
    verify_poisson_laws,
)

# =============================================================================
# 1. Monomial Operations & Admissible Orderings
# =============================================================================


def test_monomial_arithmetic_and_divisibility() -> None:
    """Verify exponent tuple addition, subtraction, divisibility, and LCM."""
    a = (2, 1, 0)
    b = (1, 3, 2)
    assert monomial_add(a, b) == (3, 4, 2)
    assert monomial_sub((3, 4, 2), a) == b
    assert monomial_divides((1, 1, 0), a)
    assert not monomial_divides(b, a)
    assert monomial_lcm(a, b) == (2, 3, 2)


def test_monomial_orderings_distinguish_lex_grlex_grevlex() -> None:
    """Verify lex, grlex, and grevlex produce their canonical distinct orderings."""
    # Classic Cox-Little-O'Shea tie-breaker test:
    # x^2 z = (2, 0, 1) vs x y^2 = (1, 2, 0) (both total degree 3)
    # In grlex: (2, 0, 1) > (1, 2, 0).
    # In grevlex: rightmost difference is z^1 vs z^0 -> z^0 wins -> (1, 2, 0) > (2, 0, 1)!
    m1 = (2, 0, 1)
    m2 = (1, 2, 0)
    assert order_key_grlex(m1) > order_key_grlex(m2)
    assert order_key_grevlex(m2) > order_key_grevlex(m1)

    # lex ignores total degree: x = (1, 0, 0) > y^5 = (0, 5, 0)
    assert order_key_lex((1, 0, 0)) > order_key_lex((0, 5, 0))
    assert order_key_grlex((0, 5, 0)) > order_key_grlex((1, 0, 0))
    assert order_key_grevlex((0, 5, 0)) > order_key_grevlex((1, 0, 0))


# =============================================================================
# 2. MultivariatePolynomialAlgebra Core Operations & Protocol Compliance
# =============================================================================


def test_multivariate_polynomial_ring_algebra_and_derivation_laws() -> None:
    """Verify CommRing, Algebra, HasDerivation protocols and core arithmetic over Q."""
    q_field = StandardField(Fraction)
    ring = MultivariatePolynomialAlgebra(q_field, n_vars=2, order='grevlex')
    assert isinstance(ring, CommRing)
    assert isinstance(ring, Algebra)
    assert isinstance(ring, HasDerivation)
    assert isinstance(ring, PoissonAlgebra)

    x, y = ring.gen(0), ring.gen(1)
    f = ring.add(ring.mul(x, x), ring.smul(Fraction(2), y))  # x^2 + 2y
    g = ring.sub(ring.mul(x, y), ring.const(Fraction(3)))  # xy - 3

    samples = [ring.zero, ring.one, x, y, f, g]
    r_samples = [Fraction(0), Fraction(1), Fraction(-2, 3), Fraction(5, 2)]

    assert all(verify_comm_ring_laws(ring, samples).values())
    assert all(verify_algebra_laws(ring, q_field, r_samples, samples).values())

    assert ring.lm(f) == (2, 0)
    assert ring.lc(f) == Fraction(1)
    assert ring.lt(ring.smul(Fraction(3), f)) == ((2, 0), Fraction(3))
    assert ring.make_monic(ring.smul(Fraction(4, 5), f)) == f
    assert ring.make_monic({}) == {}
    assert ring.const(Fraction(0)) == {}

    # Exact rational evaluation
    assert ring.eval(f, (Fraction(3, 2), Fraction(-1, 4))) == Fraction(9, 4) - Fraction(1, 2)
    assert ring.eval(g, (Fraction(2), Fraction(5))) == Fraction(7)


def test_multivariate_polynomial_input_validation() -> None:
    """Verify invalid constructor parameters, zero lm, and out-of-range indices raise cleanly."""
    q_field = StandardField(Fraction)
    with pytest.raises(TypeError):
        MultivariatePolynomialAlgebra(StandardSemiring(int), n_vars=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match='n_vars'):
        MultivariatePolynomialAlgebra(q_field, n_vars=0)
    with pytest.raises(ValueError, match='monomial order'):
        MultivariatePolynomialAlgebra(q_field, n_vars=2, order='invalid')  # type: ignore[arg-type]

    ring = MultivariatePolynomialAlgebra(q_field, n_vars=2)
    with pytest.raises(IndexError):
        ring.gen(2)
    with pytest.raises(IndexError):
        ring.diff(ring.one, var_index=2)
    with pytest.raises(ValueError, match='zero polynomial'):
        ring.lm(ring.zero)
    with pytest.raises(ValueError, match='evaluation point'):
        ring.eval(ring.one, (Fraction(1),))


def test_formal_derivation_and_poisson_bracket_laws() -> None:
    """Verify Leibniz rule for formal diff and full PoissonAlgebra axioms on 2D & 4D phase space."""
    q_field = StandardField(Fraction)

    # 2D phase space (q, p)
    ring2 = MultivariatePolynomialAlgebra(q_field, n_vars=2)
    q, p = ring2.gen(0), ring2.gen(1)
    assert ring2.poisson_bracket(q, p) == ring2.one
    assert ring2.poisson_bracket(p, q) == ring2.neg(ring2.one)

    h = ring2.add(ring2.smul(Fraction(1, 2), ring2.mul(p, p)), ring2.smul(Fraction(1, 2), ring2.mul(q, q)))
    f = ring2.mul(q, p)
    g = ring2.add(ring2.mul(q, q), ring2.smul(Fraction(3), p))
    assert all(verify_poisson_laws(ring2, [ring2.zero, ring2.one, q, p, h, f, g]).values())

    # 4D phase space (q1, q2, p1, p2): canonical angular momentum L = q1*p2 - q2*p1
    ring4 = MultivariatePolynomialAlgebra(q_field, n_vars=4)
    q1, q2, p1, p2 = (ring4.gen(i) for i in range(4))
    ang_mom = ring4.sub(ring4.mul(q1, p2), ring4.mul(q2, p1))
    r_sq = ring4.add(ring4.mul(q1, q1), ring4.mul(q2, q2))
    p_sq = ring4.add(ring4.mul(p1, p1), ring4.mul(p2, p2))
    # Angular momentum commutes with isotropic Hamiltonian H = (p^2 + r^2)/2
    assert ring4.poisson_bracket(ang_mom, ring4.add(p_sq, r_sq)) == {}
    assert all(verify_poisson_laws(ring4, [q1, p1, ang_mom, r_sq, p_sq]).values())

    # Odd n_vars must reject canonical symplectic Poisson bracket
    ring3 = MultivariatePolynomialAlgebra(q_field, n_vars=3)
    with pytest.raises(ValueError, match='even number'):
        ring3.poisson_bracket(ring3.gen(0), ring3.gen(1))


def test_formal_derivation_over_finite_field_characteristic_p() -> None:
    """Verify d/dx (x^p) == 0 over F_p = ModularField(p)."""
    fp = ModularField(5)
    ring = MultivariatePolynomialAlgebra(fp, n_vars=2)
    x = ring.gen(0)
    x5 = {(5, 0): 1, (3, 1): 2, (1, 0): 4}
    # d/dx(x^5 + 2 x^3 y + 4 x) = 5 x^4 + 6 x^2 y + 4 == x^2 y + 4 (mod 5)
    assert ring.diff(x5, var_index=0) == {(2, 1): 1, (0, 0): 4}
    assert ring.diff(x, var_index=1) == {}


def test_univariate_gcd_and_square_free_part_char0_and_char_p() -> None:
    """Verify exact univariate GCD and square-free part over both Q and F_p."""
    # Characteristic 0 over Q
    q_field = StandardField(Fraction)
    ring_q = MultivariatePolynomialAlgebra(q_field, n_vars=2)
    x = ring_q.gen(0)
    y = ring_q.gen(1)
    lin1 = ring_q.sub(x, ring_q.one)  # x - 1
    lin2 = ring_q.sub(x, ring_q.const(Fraction(2)))  # x - 2
    lin3 = ring_q.add(x, ring_q.const(Fraction(3)))  # x + 3

    f_q = ring_q.mul(ring_q.mul(lin1, lin1), lin2)  # (x-1)^2 (x-2)
    g_q = ring_q.mul(lin1, lin3)  # (x-1)(x+3)
    assert ring_q.univariate_gcd(f_q, g_q, var_index=0) == lin1
    assert ring_q.square_free_part(f_q, var_index=0) == ring_q.mul(lin1, lin2)
    assert ring_q.square_free_part(ring_q.const(Fraction(7)), var_index=0) == ring_q.one
    assert ring_q.square_free_part(ring_q.zero, var_index=0) == {}

    # Reject multivariate polynomial in univariate_gcd / square_free_part
    with pytest.raises(ValueError, match='not univariate'):
        ring_q.univariate_gcd(ring_q.add(x, y), lin1, var_index=0)

    # Characteristic p = 3: (x - 1)(x - 2)^3 has pure p-th power factor (x - 2)^3!
    f3 = ModularField(3)
    ring_p = MultivariatePolynomialAlgebra(f3, n_vars=2)
    xp = ring_p.gen(0)
    p1 = ring_p.sub(xp, ring_p.one)  # x - 1
    p2 = ring_p.sub(xp, ring_p.const(2))  # x - 2
    p2_cubed = ring_p.mul(ring_p.mul(p2, p2), p2)  # (x - 2)^3 = x^3 - 2 (mod 3)
    f_mixed = ring_p.mul(ring_p.mul(p1, p1), p2_cubed)  # (x - 1)^2 (x - 2)^3
    assert ring_p.square_free_part(p2_cubed, var_index=0) == p2
    assert ring_p.square_free_part(f_mixed, var_index=0) == ring_p.mul(p1, p2)


# =============================================================================
# 3. Exact-Field Guardrail Falsification (Popper Exactness Mandate)
# =============================================================================


@pytest.mark.parametrize(
    'bad_field',
    [
        StandardField(float),
        StandardField(complex),
    ],
)
def test_exact_field_guardrail_rejects_ieee754_fields(bad_field: Field[Any]) -> None:
    """GroebnerIdeal and groebner_basis must strictly reject IEEE-754 float/complex fields."""
    ring = MultivariatePolynomialAlgebra(bad_field, n_vars=2, order='grevlex')
    x, y = ring.gen(0), ring.gen(1)
    gens = [ring.sub(ring.mul(x, x), y)]

    with pytest.raises(TypeError, match='exact Field'):
        groebner_basis(ring, gens)

    with pytest.raises(TypeError, match='exact Field'):
        GroebnerIdeal(ring, gens)


def test_groebner_basis_rejects_unknown_method() -> None:
    """Unknown method keyword raises ValueError."""
    ring = MultivariatePolynomialAlgebra(StandardField(Fraction), n_vars=2)
    with pytest.raises(ValueError, match='Unknown groebner_basis method'):
        groebner_basis(ring, [ring.gen(0)], method='magic')  # type: ignore[arg-type]


# =============================================================================
# 4. Buchberger vs. F4 Equivalence, Edge Cases, & Galois Field GF(p^m)
# =============================================================================


def _twisted_cubic(ring: MultivariatePolynomialAlgebra[Any]) -> list[dict[tuple[int, ...], Any]]:
    x, y, z = ring.gen(0), ring.gen(1), ring.gen(2)
    return [ring.sub(ring.mul(x, x), y), ring.sub(ring.mul(x, y), z)]


def _cyclic3(ring: MultivariatePolynomialAlgebra[Any]) -> list[dict[tuple[int, ...], Any]]:
    x, y, z = ring.gen(0), ring.gen(1), ring.gen(2)
    return [
        ring.add(ring.add(x, y), z),
        ring.add(ring.add(ring.mul(x, y), ring.mul(y, z)), ring.mul(z, x)),
        ring.sub(ring.mul(ring.mul(x, y), z), ring.one),
    ]


def _cyclic4(ring: MultivariatePolynomialAlgebra[Any]) -> list[dict[tuple[int, ...], Any]]:
    x, y, z, w = (ring.gen(i) for i in range(4))
    return [
        ring.add(ring.add(x, y), ring.add(z, w)),
        ring.add(ring.add(ring.mul(x, y), ring.mul(y, z)), ring.add(ring.mul(z, w), ring.mul(w, x))),
        ring.add(
            ring.add(ring.mul(ring.mul(x, y), z), ring.mul(ring.mul(y, z), w)),
            ring.add(ring.mul(ring.mul(z, w), x), ring.mul(ring.mul(w, x), y)),
        ),
        ring.sub(ring.mul(ring.mul(x, y), ring.mul(z, w)), ring.one),
    ]


def _robot_2r_ik(
    ring: MultivariatePolynomialAlgebra[Any],
    conv: Any,
) -> list[dict[tuple[int, ...], Any]]:
    c1, s1, c2, s2 = (ring.gen(i) for i in range(4))
    return [
        ring.sub(ring.add(ring.smul(conv(3), c1), ring.smul(conv(2), c2)), ring.const(conv(3))),
        ring.sub(ring.add(ring.smul(conv(3), s1), ring.smul(conv(2), s2)), ring.const(conv(2))),
        ring.sub(ring.add(ring.mul(c1, c1), ring.mul(s1, s1)), ring.one),
        ring.sub(ring.add(ring.mul(c2, c2), ring.mul(s2, s2)), ring.one),
    ]


@pytest.mark.parametrize('order', ['grevlex', 'grlex', 'lex'])
def test_buchberger_and_f4_produce_identical_bases_over_rationals(order: Any) -> None:
    """Verify Buchberger and F4 produce identical unique reduced monic bases across all monomial orders."""
    q_field = StandardField(Fraction)

    ring3 = MultivariatePolynomialAlgebra(q_field, n_vars=3, order=order)
    for gens in (_twisted_cubic(ring3), _cyclic3(ring3)):
        gb_b = groebner_basis(ring3, gens, method='buchberger')
        gb_f = groebner_basis(ring3, gens, method='f4')
        assert gb_b == gb_f
        ideal = GroebnerIdeal(ring3, gens, method='auto')
        assert list(ideal.basis) == gb_f
        assert all(verify_groebner_basis_laws(ring3, ideal).values())

    ring4 = MultivariatePolynomialAlgebra(q_field, n_vars=4, order=order)
    for gens in (_cyclic4(ring4), _robot_2r_ik(ring4, Fraction)):
        gb_b = groebner_basis(ring4, gens, method='buchberger')
        gb_f = groebner_basis(ring4, gens, method='f4')
        assert gb_b == gb_f
        ideal = GroebnerIdeal(ring4, gens)
        assert all(verify_groebner_basis_laws(ring4, ideal).values())


def test_groebner_edge_cases_zero_unit_and_single_generator() -> None:
    """Verify zero ideal, unit ideal (inconsistent system), and principal ideal edge cases."""
    q_field = StandardField(Fraction)
    ring = MultivariatePolynomialAlgebra(q_field, n_vars=2, order='grevlex')
    x, y = ring.gen(0), ring.gen(1)

    # Zero ideal: empty generators or all-zero generators
    zero_ideal = GroebnerIdeal(ring, [ring.zero])
    assert zero_ideal.basis == ()
    assert not zero_ideal.is_unit()
    assert zero_ideal.contains(ring.zero)
    assert not zero_ideal.contains(x)
    assert zero_ideal.reduce(x) == x
    assert all(verify_groebner_basis_laws(ring, zero_ideal).values())

    # Unit ideal: inconsistent system x - 1 = 0, x - 2 = 0
    for method in ('buchberger', 'f4'):
        unit_ideal = GroebnerIdeal(
            ring,
            [ring.sub(x, ring.one), ring.sub(x, ring.const(Fraction(2)))],
            method=method,  # type: ignore[arg-type]
        )
        assert unit_ideal.is_unit()
        assert unit_ideal.basis == (ring.one,)
        assert unit_ideal.contains(y)
        assert unit_ideal.reduce(y) == {}
        assert all(verify_groebner_basis_laws(ring, unit_ideal).values())

    # Direct constant generator
    const_unit = GroebnerIdeal(ring, [ring.const(Fraction(5)), x])
    assert const_unit.is_unit()
    assert const_unit.basis == (ring.one,)

    # Single generator
    single = GroebnerIdeal(ring, [ring.smul(Fraction(3), ring.sub(ring.mul(x, x), y))])
    assert len(single.basis) == 1
    assert single.basis[0] == ring.sub(ring.mul(x, x), y)
    assert all(verify_groebner_basis_laws(ring, single).values())


def test_groebner_over_finite_field_and_galois_extension_gf_p_m() -> None:
    """Verify exact Groebner ideals over ModularField(p) and GaloisField GF(2^2)."""
    # 1. ModularField(101)
    f101 = ModularField(101)
    ring_p = MultivariatePolynomialAlgebra(f101, n_vars=3, order='lex')
    gens_p = _cyclic3(ring_p)
    assert groebner_basis(ring_p, gens_p, method='buchberger') == groebner_basis(ring_p, gens_p, method='f4')
    ideal_p = GroebnerIdeal(ring_p, gens_p)
    assert all(verify_groebner_basis_laws(ring_p, ideal_p).values())

    # 2. GaloisField GF(2^2) = F_2[t] / (t^2 + t + 1)
    gf4 = GaloisField(p=2, irreduc_poly=(1, 1, 1))
    assert isinstance(gf4, Field)
    gf4_elems = [{}, {0: 1}, {1: 1}, {0: 1, 1: 1}]
    assert all(verify_field_laws(gf4, gf4_elems).values())

    ring_gf = MultivariatePolynomialAlgebra(gf4, n_vars=2, order='grevlex')
    x, y = ring_gf.gen(0), ring_gf.gen(1)
    alpha = {1: 1}  # primitive element t in GF(4) with t^2 + t + 1 = 0
    # Ideal <x^2 - alpha, x*y - 1> over GF(4)
    gens_gf = [
        ring_gf.sub(ring_gf.mul(x, x), ring_gf.const(alpha)),
        ring_gf.sub(ring_gf.mul(x, y), ring_gf.one),
    ]
    gb_b = groebner_basis(ring_gf, gens_gf, method='buchberger')
    gb_f = groebner_basis(ring_gf, gens_gf, method='f4')
    assert gb_b == gb_f
    ideal_gf = GroebnerIdeal(ring_gf, gens_gf)
    assert not ideal_gf.is_unit()
    # Since x^2 = alpha and xy = 1, we must have y^2 = alpha^{-1} = alpha + 1 = {0: 1, 1: 1}
    assert ideal_gf.contains(ring_gf.sub(ring_gf.mul(y, y), ring_gf.const({0: 1, 1: 1})))
    assert all(verify_groebner_basis_laws(ring_gf, ideal_gf).values())

    # Also test square_free_part over GF(4) on (x - alpha)^2 = x^2 + alpha^2 (pure 2nd power)
    f_sq = ring_gf.mul(ring_gf.sub(x, ring_gf.const(alpha)), ring_gf.sub(x, ring_gf.const(alpha)))
    assert ring_gf.square_free_part(f_sq, var_index=0) == ring_gf.sub(x, ring_gf.const(alpha))


# =============================================================================
# 5. GroebnerIdeal Protocols, QuotientRing Integration & Oracle Falsification
# =============================================================================


def test_groebner_ideal_protocols_absorption_and_quotient_ring() -> None:
    """Verify FinitelyGeneratedIdeal / Ideal protocols, absorption laws, and QuotientRing arithmetic."""
    q_field = StandardField(Fraction)
    ring = MultivariatePolynomialAlgebra(q_field, n_vars=2, order='grevlex')
    x, y = ring.gen(0), ring.gen(1)

    # Coordinate ring Q[x, y] / <x^2 - y, y - 1> ~= Q[x] / <x^2 - 1>
    g1 = ring.sub(ring.mul(x, x), y)
    g2 = ring.sub(y, ring.one)
    ideal = GroebnerIdeal(ring, [g1, g2])

    assert isinstance(ideal, Ideal)
    assert isinstance(ideal, FinitelyGeneratedIdeal)
    assert isinstance(ideal, HasBasis)

    assert ring.sub(ring.mul(x, x), ring.one) in ideal
    assert x not in ideal

    ring_samples = [ring.zero, ring.one, x, y, ring.add(x, y), ring.mul(x, y)]
    ideal_samples = [*ideal.basis, ring.mul(x, g1)]
    assert all(verify_ideal_absorption_laws(ring, ideal, ring_samples, ideal_samples).values())

    coord_ring = QuotientRing(ring, ideal)
    assert coord_ring.mul(x, x) == ring.one
    assert coord_ring.project(y) == ring.one
    assert coord_ring.eq(ring.mul(x, ring.mul(x, x)), x)


def test_verify_groebner_basis_laws_falsifies_non_groebner_and_non_reduced_bases() -> None:
    """Popper falsification: verify_groebner_basis_laws must detect tampered non-Groebner or non-reduced bases."""
    q_field = StandardField(Fraction)
    ring = MultivariatePolynomialAlgebra(q_field, n_vars=3, order='lex')
    gens = _twisted_cubic(ring)  # [x^2 - y, xy - z]: NOT a Groebner basis under lex (S-poly is y^2 - xz)

    class _TamperedIdeal:
        def __init__(self, basis: tuple[dict[tuple[int, ...], Fraction], ...]) -> None:
            self.generators = tuple(gens)
            self._basis = basis

        @property
        def basis(self) -> tuple[dict[tuple[int, ...], Fraction], ...]:
            return self._basis

        def reduce(self, element: dict[tuple[int, ...], Fraction]) -> dict[tuple[int, ...], Fraction]:
            return ring.reduce_poly(element, self._basis)

        def contains(self, element: dict[tuple[int, ...], Fraction]) -> bool:
            return len(self.reduce(element)) == 0

    # 1. Incomplete non-Groebner basis fails Buchberger criterion
    tampered_incomplete = _TamperedIdeal(tuple(gens))
    res_incomplete = verify_groebner_basis_laws(ring, tampered_incomplete)  # type: ignore[arg-type]
    assert res_incomplete['buchberger_criterion'] is False

    # 2. Non-monic scaled basis fails basis_monic
    valid = GroebnerIdeal(ring, gens)
    non_monic = (ring.smul(Fraction(2), valid.basis[0]), *valid.basis[1:])
    res_non_monic = verify_groebner_basis_laws(ring, _TamperedIdeal(non_monic))  # type: ignore[arg-type]
    assert res_non_monic['basis_monic'] is False

    # 3. Non-reduced basis (extra redundant multiple x * g_0) fails basis_reduced
    redundant = (*valid.basis, ring.mul(ring.gen(0), valid.basis[0]))
    res_redundant = verify_groebner_basis_laws(ring, _TamperedIdeal(redundant))  # type: ignore[arg-type]
    assert res_redundant['basis_reduced'] is False
