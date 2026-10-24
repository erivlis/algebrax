"""
Property-based axiomatic verification for algebraic structures.

Generalizes tests/algebrax/test_verification.py by testing algebraic axioms
(associativity, commutativity, identities, distributivity, annihilation)
across infinite random input domains via Hypothesis.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import algebrax as ax
from algebrax.semiring import (
    ArcticSemiring,
    BooleanSemiring,
    LogSemiring,
    StandardSemiring,
    TropicalSemiring,
    ViterbiSemiring,
)
from algebrax.verification import semiring_elements_equal

pytestmark = [pytest.mark.verification, pytest.mark.axiomatic]


# ---------------------------------------------------------------------------
# Exact Rational Axiom Properties (Strictly Zero Floating-Point Contamination)
# ---------------------------------------------------------------------------


@given(
    a=st.fractions(min_value=-1000, max_value=1000, max_denominator=100),
    b=st.fractions(min_value=-1000, max_value=1000, max_denominator=100),
    c=st.fractions(min_value=-1000, max_value=1000, max_denominator=100),
)
@settings(max_examples=30)
def test_standard_semiring_exact_rational_axioms(a: Fraction, b: Fraction, c: Fraction) -> None:
    """Verify that StandardSemiring satisfies ring/semiring axioms exactly over Fraction."""
    sr = StandardSemiring(Fraction)

    # Additive associativity: (a + b) + c == a + (b + c)
    assert sr.add(sr.add(a, b), c) == sr.add(a, sr.add(b, c))

    # Additive commutativity: a + b == b + a
    assert sr.add(a, b) == sr.add(b, a)

    # Multiplicative associativity: (a * b) * c == a * (b * c)
    assert sr.mul(sr.mul(a, b), c) == sr.mul(a, sr.mul(b, c))

    # Multiplicative commutativity: a * b == b * a
    assert sr.mul(a, b) == sr.mul(b, a)

    # Left Distributivity: a * (b + c) == (a * b) + (a * c)
    lhs_left = sr.mul(a, sr.add(b, c))
    rhs_left = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert lhs_left == rhs_left

    # Right Distributivity: (a + b) * c == (a * c) + (b * c)
    lhs_right = sr.mul(sr.add(a, b), c)
    rhs_right = sr.add(sr.mul(a, c), sr.mul(b, c))
    assert lhs_right == rhs_right

    # Identities & Annihilation
    assert sr.add(a, sr.zero) == a
    assert sr.mul(a, sr.one) == a
    assert sr.mul(a, sr.zero) == sr.zero
    assert sr.mul(sr.zero, a) == sr.zero


# ---------------------------------------------------------------------------
# Tropical (Min-Plus) Semiring Axioms
# ---------------------------------------------------------------------------

tropical_strategy = st.one_of(
    st.just(float('inf')),
    st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
)


@given(a=tropical_strategy, b=tropical_strategy, c=tropical_strategy)
@settings(max_examples=30)
def test_tropical_semiring_axiomatic_properties(a: float, b: float, c: float) -> None:
    """Verify Min-Plus (Tropical) Semiring properties under random values."""
    sr = TropicalSemiring()

    # Additive commutativity: min(a, b) == min(b, a)
    assert semiring_elements_equal(sr.add(a, b), sr.add(b, a))

    # Additive associativity: min(min(a, b), c) == min(a, min(b, c))
    assert semiring_elements_equal(sr.add(sr.add(a, b), c), sr.add(a, sr.add(b, c)))

    # Multiplicative associativity: (a + b) + c == a + (b + c)
    assert semiring_elements_equal(sr.mul(sr.mul(a, b), c), sr.mul(a, sr.mul(b, c)))

    # Additive Identity: min(a, +inf) == a
    assert semiring_elements_equal(sr.add(a, sr.zero), a)

    # Multiplicative Identity: a + 0.0 == a
    assert semiring_elements_equal(sr.mul(a, sr.one), a)

    # Annihilation by Zero (+inf): a + (+inf) == +inf
    assert semiring_elements_equal(sr.mul(a, sr.zero), sr.zero)
    assert semiring_elements_equal(sr.mul(sr.zero, a), sr.zero)

    # Left Distributivity: a + min(b, c) == min(a + b, a + c)
    lhs_dist = sr.mul(a, sr.add(b, c))
    rhs_dist = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert semiring_elements_equal(lhs_dist, rhs_dist)


# ---------------------------------------------------------------------------
# Arctic (Max-Plus) Semiring Axioms
# ---------------------------------------------------------------------------

arctic_strategy = st.one_of(
    st.just(float('-inf')),
    st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
)


@given(a=arctic_strategy, b=arctic_strategy, c=arctic_strategy)
@settings(max_examples=30)
def test_arctic_semiring_axiomatic_properties(a: float, b: float, c: float) -> None:
    """Verify Max-Plus (Arctic) Semiring properties under random values."""
    sr = ArcticSemiring()

    # Additive commutativity: max(a, b) == max(b, a)
    assert semiring_elements_equal(sr.add(a, b), sr.add(b, a))

    # Additive associativity: max(max(a, b), c) == max(a, max(b, c))
    assert semiring_elements_equal(sr.add(sr.add(a, b), c), sr.add(a, sr.add(b, c)))

    # Additive Identity: max(a, -inf) == a
    assert semiring_elements_equal(sr.add(a, sr.zero), a)

    # Multiplicative Identity: a + 0.0 == a
    assert semiring_elements_equal(sr.mul(a, sr.one), a)

    # Annihilation by Zero (-inf)
    assert semiring_elements_equal(sr.mul(a, sr.zero), sr.zero)
    assert semiring_elements_equal(sr.mul(sr.zero, a), sr.zero)

    # Distributivity
    lhs = sr.mul(a, sr.add(b, c))
    rhs = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert semiring_elements_equal(lhs, rhs)


# ---------------------------------------------------------------------------
# Boolean Semiring Axioms (OR / AND)
# ---------------------------------------------------------------------------


@given(a=st.booleans(), b=st.booleans(), c=st.booleans())
def test_boolean_semiring_axiomatic_properties(a: bool, b: bool, c: bool) -> None:
    """Verify Boolean Semiring (OR, AND, False, True)."""
    sr = BooleanSemiring()

    # Associativity & Commutativity
    assert sr.add(sr.add(a, b), c) == sr.add(a, sr.add(b, c))
    assert sr.mul(sr.mul(a, b), c) == sr.mul(a, sr.mul(b, c))
    assert sr.add(a, b) == sr.add(b, a)
    assert sr.mul(a, b) == sr.mul(b, a)

    # Distributivity
    assert sr.mul(a, sr.add(b, c)) == sr.add(sr.mul(a, b), sr.mul(a, c))

    # Identities & Annihilation
    assert sr.add(a, sr.zero) == a
    assert sr.mul(a, sr.one) == a
    assert sr.mul(a, sr.zero) == sr.zero


# ---------------------------------------------------------------------------
# Viterbi Semiring Axioms (Probabilistic Path Monoid: Max / Product)
# ---------------------------------------------------------------------------

viterbi_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


@given(a=viterbi_strategy, b=viterbi_strategy, c=viterbi_strategy)
@settings(max_examples=30)
def test_viterbi_semiring_axiomatic_properties(a: float, b: float, c: float) -> None:
    """Verify Viterbi Semiring (max, *, 0.0, 1.0) on probability interval [0, 1]."""
    sr = ViterbiSemiring()

    # Commutativity & Associativity
    assert semiring_elements_equal(sr.add(a, b), sr.add(b, a))
    assert semiring_elements_equal(sr.add(sr.add(a, b), c), sr.add(a, sr.add(b, c)))
    assert semiring_elements_equal(sr.mul(sr.mul(a, b), c), sr.mul(a, sr.mul(b, c)))

    # Identities & Annihilation
    assert semiring_elements_equal(sr.add(a, sr.zero), a)
    assert semiring_elements_equal(sr.mul(a, sr.one), a)
    assert semiring_elements_equal(sr.mul(a, sr.zero), sr.zero)

    # Distributivity: a * max(b, c) == max(a * b, a * c) for positive a
    lhs = sr.mul(a, sr.add(b, c))
    rhs = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert semiring_elements_equal(lhs, rhs, tol=1e-6)
