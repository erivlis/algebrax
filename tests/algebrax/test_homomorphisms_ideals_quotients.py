"""
Tests for EP-0201: Algebraic Homomorphisms, Ideals & Canonical Quotients.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from algebrax.algebra import (
    CallableHomomorphism,
    CommRing,
    GroupHom,
    Homomorphism,
    Ideal,
    IntegerModuloIdeal,
    KernelIdeal,
    LeftIdeal,
    LieAlgebraHom,
    LieIdeal,
    LinearMap,
    ModularField,
    MonoidAlgebra,
    MonoidAlgebraSemiring,
    NilpotentIdeal,
    PolynomialAlgebra,
    PolynomialTruncationIdeal,
    PrincipalIdeal,
    QuotientAlgebra,
    QuotientMonoidAlgebra,
    QuotientMonoidAlgebraSemiring,
    QuotientRing,
    QuotientSemiring,
    RightIdeal,
    Ring,
    RingHom,
    Semimodule,
    Semiring,
    StandardField,
    SubspaceLieIdeal,
)
from algebrax.lie import se_n, so_n
from algebrax.semiring import StandardSemiring
from algebrax.verification import (
    verify_ideal_absorption_laws,
    verify_lie_algebra_laws,
    verify_quotient_ring_laws,
    verify_ring_homomorphism_laws,
)


def test_homomorphism_protocols_and_composition():
    """Verify runtime_checkable homomorphism protocols and CallableHomomorphism composition."""
    f = CallableHomomorphism(lambda x: x % 5)
    g = CallableHomomorphism(lambda y: y * 2)

    assert isinstance(f, Homomorphism)
    assert isinstance(f, RingHom)
    assert isinstance(f, GroupHom)
    assert isinstance(f, LinearMap)
    assert isinstance(f, LieAlgebraHom)

    fg = g.compose(f)
    assert fg(7) == 4  # (7 % 5) * 2 = 4


def test_integer_modulo_ideal_and_quotient_ring():
    """Verify Z / nZ via IntegerModuloIdeal and QuotientRing satisfies all ring & quotient axioms."""
    z_ring = StandardField(int)
    ideal_6 = IntegerModuloIdeal(6)

    assert isinstance(ideal_6, Ideal)
    assert isinstance(ideal_6, LeftIdeal)
    assert isinstance(ideal_6, RightIdeal)
    assert isinstance(ideal_6, PrincipalIdeal)
    assert ideal_6.generator == 6
    assert 12 in ideal_6
    assert -18 in ideal_6
    assert 7 not in ideal_6
    assert ideal_6.reduce(-1) == 5
    assert ideal_6.reduce(14) == 2

    with pytest.raises(ValueError, match='Modulus must be positive'):
        IntegerModuloIdeal(0)

    ring_samples = [-7, -3, -1, 0, 1, 2, 4, 5, 9]
    ideal_samples = [-12, -6, 0, 6, 12, 18]

    abs_res = verify_ideal_absorption_laws(z_ring, ideal_6, ring_samples, ideal_samples)
    assert abs_res == {
        'zero_containment': True,
        'additive_closure': True,
        'left_absorption': True,
        'right_absorption': True,
    }

    z_mod_6 = QuotientRing(z_ring, ideal_6)
    assert isinstance(z_mod_6, Ring)
    assert isinstance(z_mod_6, CommRing)
    assert z_mod_6.zero == 0
    assert z_mod_6.one == 1
    assert z_mod_6.add(4, 5) == 3
    assert z_mod_6.mul(4, 5) == 2
    assert z_mod_6.neg(2) == 4
    assert z_mod_6.sub(1, 4) == 3
    assert z_mod_6.eq(10, 4) is True
    assert z_mod_6.eq(10, 5) is False

    q_laws = verify_quotient_ring_laws(z_mod_6, [-3, 0, 1, 2, 5], [-6, 0, 6])
    assert all(q_laws.values())


def test_first_isomorphism_theorem_via_kernel_ideal():
    """Verify First Isomorphism Theorem: R / ker(phi) ~= im(phi) for evaluation & modular homomorphisms."""
    z_ring = StandardField(int)
    f5 = ModularField(5)

    # Canonical mod-5 homomorphism phi: Z -> F_5
    phi = CallableHomomorphism(lambda x: x % 5)
    hom_laws = verify_ring_homomorphism_laws(phi, z_ring, f5, [-6, -2, -1, 0, 1, 3, 7])
    assert hom_laws == {
        'zero_preservation': True,
        'one_preservation': True,
        'add_preservation': True,
        'mul_preservation': True,
    }

    ker_phi = KernelIdeal(phi, f5, reducer=lambda x: x % 5)
    assert isinstance(ker_phi, Ideal)
    assert 10 in ker_phi
    assert -15 in ker_phi
    assert 3 not in ker_phi

    # Construct Z / ker(phi) and verify isomorphism with F_5
    quot = QuotientRing(z_ring, ker_phi)
    for a in range(-5, 6):
        for b in range(-5, 6):
            assert quot.add(a, b) == f5.add(phi(a), phi(b))
            assert quot.mul(a, b) == f5.mul(phi(a), phi(b))

    # Polynomial evaluation homomorphism ev_0: Q[x] -> Q mapping p(x) -> p(0)
    q_field = StandardField(Fraction)
    PolynomialAlgebra(StandardSemiring(Fraction))
    ev_0 = CallableHomomorphism(lambda p: p.get(0, Fraction(0)))
    ker_ev0 = KernelIdeal(
        ev_0,
        q_field,
        reducer=lambda p: {0: p[0]} if 0 in p and p[0] != Fraction(0) else {},
    )
    assert {1: Fraction(3), 2: Fraction(-1)} in ker_ev0
    assert {0: Fraction(1), 1: Fraction(2)} not in ker_ev0
    assert ker_ev0.reduce({0: Fraction(5), 2: Fraction(9)}) == {0: Fraction(5)}


def test_polynomial_truncation_and_nilpotent_ideals():
    """Verify truncated polynomial rings Q[x]/(x^n) and NilpotentIdeal dual/hyper-dual reductions."""
    poly_ring = PolynomialAlgebra(StandardSemiring(Fraction))
    trunc_ideal = PolynomialTruncationIdeal(3, zero_coeff=Fraction(0))

    assert isinstance(trunc_ideal, PrincipalIdeal)
    assert trunc_ideal.generator == {3: Fraction(1)}
    assert {3: Fraction(2), 4: Fraction(-1)} in trunc_ideal
    assert {0: Fraction(1), 3: Fraction(2)} not in trunc_ideal
    assert trunc_ideal.quotient_term(3, Fraction(5)) == []
    assert trunc_ideal.quotient_term(2, Fraction(5)) == [(2, Fraction(5))]

    with pytest.raises(ValueError, match='Maximum truncation degree must be positive'):
        PolynomialTruncationIdeal(0)

    ring_samples = [
        {},
        {0: Fraction(1)},
        {0: Fraction(1), 1: Fraction(2)},
        {1: Fraction(-1), 2: Fraction(3)},
    ]
    ideal_samples = [
        {},
        {3: Fraction(1)},
        {3: Fraction(-2), 4: Fraction(5)},
    ]

    abs_laws = verify_ideal_absorption_laws(poly_ring, trunc_ideal, ring_samples, ideal_samples)
    assert all(abs_laws.values())

    # Truncated Taylor series ring Q[x]/(x^3)
    taylor_ring = QuotientRing(poly_ring, trunc_ideal)
    # (1 + x + x^2) * (1 + 2x) = 1 + 3x + 3x^2 + 2x^3 === 1 + 3x + 3x^2 (mod x^3)
    p1 = {0: Fraction(1), 1: Fraction(1), 2: Fraction(1)}
    p2 = {0: Fraction(1), 1: Fraction(2)}
    assert taylor_ring.mul(p1, p2) == {0: Fraction(1), 1: Fraction(3), 2: Fraction(3)}

    # Test MonoidAlgebraSemiring & QuotientMonoidAlgebraSemiring (pure Semiring & Semimodule, no neg)
    mas = MonoidAlgebraSemiring(StandardSemiring(Fraction))
    assert isinstance(mas, Semiring)
    assert isinstance(mas, Semimodule)
    assert not isinstance(mas, Ring)

    qmas = QuotientMonoidAlgebraSemiring(StandardSemiring(Fraction), ideal=trunc_ideal)
    assert isinstance(qmas, Semiring)
    assert isinstance(qmas, Semimodule)
    assert not isinstance(qmas, Ring)
    assert qmas.add({0: Fraction(1), 3: Fraction(7)}, {1: Fraction(2)}) == {0: Fraction(1), 1: Fraction(2)}
    assert qmas.smul(Fraction(2), {0: Fraction(1), 3: Fraction(5)}) == {0: Fraction(2)}
    assert qmas.smul(Fraction(0), {0: Fraction(1)}) == {}
    assert qmas.mul(p1, p2) == {0: Fraction(1), 1: Fraction(3), 2: Fraction(3)}
    assert qmas.mul({}, p2) == {}

    # Test MonoidAlgebra & QuotientMonoidAlgebra (full Algebra & CommRing with neg/sub)
    assert issubclass(PolynomialAlgebra, MonoidAlgebra)
    qma = QuotientMonoidAlgebra(StandardSemiring(Fraction), ideal=trunc_ideal)
    assert isinstance(qma, CommRing)
    assert isinstance(qma, MonoidAlgebra)
    assert qma.neg({0: Fraction(1), 3: Fraction(7)}) == {0: Fraction(-1)}
    assert qma.sub({0: Fraction(3), 3: Fraction(7)}, {0: Fraction(1)}) == {0: Fraction(2)}
    assert qma.mul(p1, p2) == {0: Fraction(1), 1: Fraction(3), 2: Fraction(3)}

    # Also test MonoidAlgebra with a Ring that provides .neg()
    poly_over_field = PolynomialAlgebra(StandardField(Fraction))
    assert poly_over_field.neg({0: Fraction(2), 1: Fraction(-3)}) == {0: Fraction(-2), 1: Fraction(3)}
    assert poly_over_field.sub({0: Fraction(5)}, {0: Fraction(2)}) == {0: Fraction(3)}
    assert poly_over_field.smul(Fraction(3), {1: Fraction(2)}) == {1: Fraction(6)}

    # Also test QuotientSemiring directly
    q_semi = QuotientSemiring(StandardSemiring(int), IntegerModuloIdeal(5))
    assert q_semi.zero == 0
    assert q_semi.one == 1
    assert q_semi.add(3, 4) == 2
    assert q_semi.mul(3, 4) == 2
    assert q_semi.eq(8, 3) is True
    assert q_semi.project(12) == 2
    assert issubclass(QuotientRing, QuotientSemiring)
    assert issubclass(QuotientAlgebra, QuotientRing)

    qma_with_fn = QuotientMonoidAlgebra(
        StandardSemiring(Fraction),
        quotient_fn=trunc_ideal.quotient_term,
        ideal=trunc_ideal,
    )
    assert qma_with_fn.mul(p1, p2) == {0: Fraction(1), 1: Fraction(3), 2: Fraction(3)}

    # NilpotentIdeal (eps^2 = 0)
    nil_ideal = NilpotentIdeal(2)
    assert nil_ideal.generator == 2
    assert 2 in nil_ideal
    assert 1 not in nil_ideal
    assert nil_ideal.reduce(2) is None
    assert nil_ideal.reduce(1) == 1
    assert {2: 4.0, 3: -1.0} in nil_ideal
    assert nil_ideal.reduce({0: 3.0, 1: 2.0, 2: 9.0}) == {0: 3.0, 1: 2.0}

    with pytest.raises(ValueError, match='Nilpotency degree must be positive'):
        NilpotentIdeal(0)


def test_subspace_lie_ideal_and_quotient_lie_algebra():
    """Verify se(3) / R^3 ~= so(3) via SubspaceLieIdeal and QuotientAlgebra."""
    g_se3 = se_n(3)
    g_so3 = so_n(3)

    # In se_n(3), basis indices {0, 1, 2} are rotations and {3, 4, 5} are the abelian translational Lie ideal
    trans_ideal: SubspaceLieIdeal[int, float] = SubspaceLieIdeal({3, 4, 5}, zero_coeff=0.0)
    assert isinstance(trans_ideal, LieIdeal)
    assert {3: 1.0, 4: -2.0} in trans_ideal
    assert {0: 1.0, 3: 2.0} not in trans_ideal

    quot_lie = QuotientAlgebra(g_se3, trans_ideal)
    assert quot_lie.zero == {}
    with pytest.raises(AttributeError, match='does not define a multiplicative identity one'):
        _ = quot_lie.one

    # Check Lie algebra operations and laws on se(3) / R^3
    x = {0: 1.0, 3: 3.0}
    y = {1: 1.0, 4: -2.0}
    assert quot_lie.project(x) == {0: 1.0}
    assert quot_lie.add(x, y) == {0: 1.0, 1: 1.0}
    assert quot_lie.neg(x) == {0: -1.0}
    assert quot_lie.sub(x, y) == {0: 1.0, 1: -1.0}
    assert quot_lie.smul(2.5, x) == {0: 2.5}
    assert quot_lie.eq(x, {0: 1.0, 5: 99.0}) is True

    # [J_01, J_02] = -J_12 in both se(3)/R^3 and so(3)
    assert quot_lie.mul(x, y) == g_so3.mul({0: 1.0}, {1: 1.0})

    # Verify Lie algebra laws on the quotient algebra
    r_field = StandardField(float)
    lie_samples = [
        {},
        {0: 1.0},
        {1: 1.0},
        {2: 1.0},
        {0: 0.5, 1: -0.5},
    ]
    lie_laws = verify_lie_algebra_laws(quot_lie, r_field, [-1.0, 0.0, 2.0], lie_samples)
    assert all(lie_laws.values())

    # Unital QuotientAlgebra test over PolynomialAlgebra
    poly_alg = PolynomialAlgebra(StandardSemiring(Fraction))
    trunc = PolynomialTruncationIdeal(2, zero_coeff=Fraction(0))
    dual_alg = QuotientAlgebra(poly_alg, trunc)
    assert dual_alg.one == {0: Fraction(1)}


def test_verifier_falsification_for_broken_homomorphism_ideal_and_quotient():
    """Verify that EP-0201 verifiers detect broken homomorphisms, non-ideals, and ill-defined quotients."""
    z_ring = StandardField(int)

    # Broken homomorphism: maps x -> x + 1 (violates zero, one, add, mul preservation)
    bad_hom = CallableHomomorphism(lambda x: x + 1)
    hom_res = verify_ring_homomorphism_laws(bad_hom, z_ring, z_ring, [0, 1, 2])
    assert hom_res == {
        'zero_preservation': False,
        'one_preservation': False,
        'add_preservation': False,
        'mul_preservation': False,
    }

    # Broken ideal: subset {1, 2} (misses 0, not additively closed, does not absorb multiplication)
    class NotAnIdeal:
        def contains(self, x: int) -> bool:
            return x in {1, 2}

        def reduce(self, x: int) -> int:
            return x

    bad_ideal = NotAnIdeal()
    ideal_res = verify_ideal_absorption_laws(z_ring, bad_ideal, [0, 1, 3], [1, 2])
    assert ideal_res == {
        'zero_containment': False,
        'additive_closure': False,
        'left_absorption': False,
        'right_absorption': False,
    }

    # Subset containing 0 and closed under negation {-1, 0, 1}, but not closed under addition (1 + 1 = 2)
    class NonAdditiveSubset:
        def contains(self, x: int) -> bool:
            return x in {-1, 0, 1}

        def reduce(self, x: int) -> int:
            return 0 if x in {-1, 0, 1} else x

    non_add = NonAdditiveSubset()
    non_add_res = verify_ideal_absorption_laws(z_ring, non_add, [0, 1, 2], [-1, 0, 1])
    assert non_add_res['zero_containment'] is True
    assert non_add_res['additive_closure'] is False
    assert non_add_res['left_absorption'] is False
    assert non_add_res['right_absorption'] is False

    # Broken quotient ring where reducer does not respect congruence
    bad_quot = QuotientRing(z_ring, non_add)
    q_res = verify_quotient_ring_laws(bad_quot, [0, 1, 2], [1])
    assert q_res['coset_invariance'] is False

    # Also test coset invariance failure only on multiplication
    # Note: AddOnlyReducer is a pure duck-typed class without __contains__,
    # verifying EP-0194 Section 4 (__protocol_attrs__ minimality: {'contains', 'reduce'})
    class AddOnlyReducer:
        def contains(self, x: int) -> bool:
            return x % 4 == 0

        def reduce(self, x: int) -> int:
            return x

    add_only = AddOnlyReducer()
    assert isinstance(add_only, Ideal)
    assert add_only.contains(8) is True
    assert add_only.contains(5) is False

    class BadMulQuotient(QuotientRing[int]):
        def add(self, a: int, b: int) -> int:
            return (a + b) % 4

        def mul(self, a: int, b: int) -> int:
            # Depends on raw representative rather than mod 4 coset
            return a * b

    bad_mul_q = BadMulQuotient(z_ring, add_only)
    q_mul_res = verify_quotient_ring_laws(bad_mul_q, [0, 1, 2], [4])
    assert q_mul_res['coset_invariance'] is False

    # Test KernelIdeal with float and complex codomains for tolerance-based _elements_equal
    r_field = StandardField(float)
    c_field = StandardField(complex)
    ker_float = KernelIdeal(lambda x: x - 1.0, r_field, reducer=lambda x: 1.0)
    assert (1.0 + 1e-12) in ker_float
    assert 2.0 not in ker_float

    ker_complex = KernelIdeal(lambda z: z - (1.0 + 2.0j), c_field, reducer=lambda z: 1.0 + 2.0j)
    assert (1.0 + 2.0j + 1e-12j) in ker_complex
    assert (0.0 + 0.0j) not in ker_complex
