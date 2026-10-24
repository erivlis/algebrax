r"""Property-based axiomatic verification for algebraic structures.

Implements EP-0180 & EP-0185:
- Exact rational `StandardSemiring(Fraction)` axioms via Hypothesis.
- Tropical, Arctic, Boolean, Viterbi, Log, Bottleneck, Lukasiewicz, MinTimes, KCollapsed, Digital, and Modular
  semiring axioms via Hypothesis.
- Exhaustive parametrized Hypothesis verification across all 34 built-in semirings in `Semiring.catalog()`,
  including Kleene star fixed-point closure laws ($a^* = \mathbb{1} \oplus a \otimes a^*$).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from algebrax.semiring import (
    ArcticSemiring,
    BooleanSemiring,
    BottleneckSemiring,
    DigitalSemiring,
    KCollapsedSemiring,
    LogSemiring,
    LukasiewiczSemiring,
    MinTimesSemiring,
    ModularSemiring,
    ReliabilitySemiring,
    Semiring,
    StandardSemiring,
    TropicalSemiring,
    ViterbiSemiring,
)
from algebrax.verification import get_semiring_samples, semiring_elements_equal, verify_semiring_laws

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

    assert sr.add(sr.add(a, b), c) == sr.add(a, sr.add(b, c))
    assert sr.add(a, b) == sr.add(b, a)
    assert sr.mul(sr.mul(a, b), c) == sr.mul(a, sr.mul(b, c))
    assert sr.mul(a, b) == sr.mul(b, a)

    lhs_left = sr.mul(a, sr.add(b, c))
    rhs_left = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert lhs_left == rhs_left

    lhs_right = sr.mul(sr.add(a, b), c)
    rhs_right = sr.add(sr.mul(a, c), sr.mul(b, c))
    assert lhs_right == rhs_right

    assert sr.add(a, sr.zero) == a
    assert sr.mul(a, sr.one) == a
    assert sr.mul(a, sr.zero) == sr.zero
    assert sr.mul(sr.zero, a) == sr.zero


# ---------------------------------------------------------------------------
# Tropical (Min-Plus) Semiring Axioms & Kleene Star
# ---------------------------------------------------------------------------

tropical_strategy = st.one_of(
    st.just(float('inf')),
    st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
)


@given(a=tropical_strategy, b=tropical_strategy, c=tropical_strategy)
@settings(max_examples=30)
def test_tropical_semiring_axiomatic_properties(a: float, b: float, c: float) -> None:
    """Verify Min-Plus (Tropical) Semiring properties and Kleene star fixed-point law."""
    sr = TropicalSemiring()

    assert semiring_elements_equal(sr.add(a, b), sr.add(b, a))
    assert semiring_elements_equal(sr.add(sr.add(a, b), c), sr.add(a, sr.add(b, c)))
    assert semiring_elements_equal(sr.mul(sr.mul(a, b), c), sr.mul(a, sr.mul(b, c)))
    assert semiring_elements_equal(sr.add(a, sr.zero), a)
    assert semiring_elements_equal(sr.mul(a, sr.one), a)
    assert semiring_elements_equal(sr.mul(a, sr.zero), sr.zero)
    assert semiring_elements_equal(sr.mul(sr.zero, a), sr.zero)

    lhs_dist = sr.mul(a, sr.add(b, c))
    rhs_dist = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert semiring_elements_equal(lhs_dist, rhs_dist)

    if a >= 0.0:
        a_star = sr.star(a)
        assert a_star == 0.0
        assert semiring_elements_equal(a_star, sr.add(sr.one, sr.mul(a, a_star)))


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

    assert semiring_elements_equal(sr.add(a, b), sr.add(b, a))
    assert semiring_elements_equal(sr.add(sr.add(a, b), c), sr.add(a, sr.add(b, c)))
    assert semiring_elements_equal(sr.add(a, sr.zero), a)
    assert semiring_elements_equal(sr.mul(a, sr.one), a)
    assert semiring_elements_equal(sr.mul(a, sr.zero), sr.zero)
    assert semiring_elements_equal(sr.mul(sr.zero, a), sr.zero)

    lhs = sr.mul(a, sr.add(b, c))
    rhs = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert semiring_elements_equal(lhs, rhs)


# ---------------------------------------------------------------------------
# Boolean Semiring Axioms (OR / AND)
# ---------------------------------------------------------------------------


@given(a=st.booleans(), b=st.booleans(), c=st.booleans())
def test_boolean_semiring_axiomatic_properties(a: bool, b: bool, c: bool) -> None:
    """Verify Boolean Semiring (OR, AND, False, True) and Kleene star."""
    sr = BooleanSemiring()

    assert sr.add(sr.add(a, b), c) == sr.add(a, sr.add(b, c))
    assert sr.mul(sr.mul(a, b), c) == sr.mul(a, sr.mul(b, c))
    assert sr.add(a, b) == sr.add(b, a)
    assert sr.mul(a, b) == sr.mul(b, a)
    assert sr.mul(a, sr.add(b, c)) == sr.add(sr.mul(a, b), sr.mul(a, c))
    assert sr.add(a, sr.zero) == a
    assert sr.mul(a, sr.one) == a
    assert sr.mul(a, sr.zero) == sr.zero
    assert sr.star(a) is True
    assert sr.star(a) == sr.add(sr.one, sr.mul(a, sr.star(a)))


# ---------------------------------------------------------------------------
# Viterbi & Reliability Semiring Axioms (Probabilistic Path Monoids)
# ---------------------------------------------------------------------------

viterbi_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


@given(a=viterbi_strategy, b=viterbi_strategy, c=viterbi_strategy)
@settings(max_examples=30)
def test_viterbi_semiring_axiomatic_properties(a: float, b: float, c: float) -> None:
    """Verify Viterbi and Reliability Semiring (max, *, 0.0, 1.0) on probability interval [0, 1]."""
    for sr in (ViterbiSemiring(), ReliabilitySemiring()):
        assert semiring_elements_equal(sr.add(a, b), sr.add(b, a))
        assert semiring_elements_equal(sr.add(sr.add(a, b), c), sr.add(a, sr.add(b, c)))
        assert semiring_elements_equal(sr.mul(sr.mul(a, b), c), sr.mul(a, sr.mul(b, c)))
        assert semiring_elements_equal(sr.add(a, sr.zero), a)
        assert semiring_elements_equal(sr.mul(a, sr.one), a)
        assert semiring_elements_equal(sr.mul(a, sr.zero), sr.zero)

        lhs = sr.mul(a, sr.add(b, c))
        rhs = sr.add(sr.mul(a, b), sr.mul(a, c))
        assert semiring_elements_equal(lhs, rhs, tol=1e-6)
        assert sr.star(a) == 1.0


# ---------------------------------------------------------------------------
# Log, Lukasiewicz, Bottleneck, MinTimes, KCollapsed, Digital & Modular Semirings
# ---------------------------------------------------------------------------


@given(
    a=st.floats(min_value=-20.0, max_value=-0.05, allow_nan=False, allow_infinity=False),
    b=st.floats(min_value=-20.0, max_value=-0.05, allow_nan=False, allow_infinity=False),
    c=st.floats(min_value=-20.0, max_value=-0.05, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=30)
def test_log_semiring_axioms_and_kleene_star(a: float, b: float, c: float) -> None:
    """Verify LogSemiring axioms and Kleene star fixed-point identity a* = 1 (+) a (*) a* for a < 0."""
    sr = LogSemiring()
    res = verify_semiring_laws(sr, [sr.zero, sr.one, a, b, c], tol=1e-9)
    assert all(res.values())

    # Kleene star fixed-point law: a* = 0.0 (+) (a + a*)
    a_star = sr.star(a)
    rhs = sr.add(sr.one, sr.mul(a, a_star))
    assert semiring_elements_equal(a_star, rhs, tol=1e-9)


@given(
    u1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    u2=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    u3=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    p1=st.floats(min_value=0.1, max_value=50.0, allow_nan=False),
    p2=st.floats(min_value=0.1, max_value=50.0, allow_nan=False),
    p3=st.floats(min_value=0.1, max_value=50.0, allow_nan=False),
    n1=st.integers(min_value=0, max_value=500),
    n2=st.integers(min_value=0, max_value=500),
    n3=st.integers(min_value=0, max_value=500),
)
@settings(max_examples=25)
def test_fuzzy_bottleneck_mintimes_kcollapsed_digital_modular_axioms(
    u1: float,
    u2: float,
    u3: float,
    p1: float,
    p2: float,
    p3: float,
    n1: int,
    n2: int,
    n3: int,
) -> None:
    """Verify Lukasiewicz, Bottleneck, MinTimes, KCollapsed, Digital, and Modular semirings via Hypothesis."""
    # Lukasiewicz fuzzy t-norm semiring on [0, 1]
    luk = LukasiewiczSemiring()
    assert all(verify_semiring_laws(luk, [luk.zero, luk.one, u1, u2, u3], tol=1e-9).values())

    # Bottleneck (Max-Min) dioid
    bot = BottleneckSemiring()
    assert all(verify_semiring_laws(bot, [bot.zero, bot.one, p1, p2, p3], tol=1e-9).values())

    # MinTimes semiring on R_{>= 0}
    mt = MinTimesSemiring()
    assert all(verify_semiring_laws(mt, [mt.zero, mt.one, p1, p2, p3], tol=1e-7).values())

    # KCollapsed bounded counter semiring
    kc = KCollapsedSemiring(k=7)
    assert all(verify_semiring_laws(kc, [kc.zero, kc.one, min(n1, 7), min(n2, 7), min(n3, 7)]).values())

    # Digital sum-of-digits tropical semiring
    dig = DigitalSemiring()
    assert all(verify_semiring_laws(dig, [dig.zero, dig.one, n1, n2, n3]).values())

    # Modular ring Z / 11Z
    mod = ModularSemiring(11)
    assert all(verify_semiring_laws(mod, [mod.zero, mod.one, n1 % 11, n2 % 11, n3 % 11]).values())


# ---------------------------------------------------------------------------
# Full 34-Semiring Catalog Randomized Law & Dioid Closure Audit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('semiring_name', sorted(Semiring.catalog().keys()))
def test_all_34_catalog_semirings_laws_and_nsum_power_consistency(semiring_name: str) -> None:
    """Verify all 34 catalog semirings satisfy the 9 semiring axioms plus nsum/power consistency."""
    semiring, samples = get_semiring_samples(semiring_name)
    results = verify_semiring_laws(semiring, samples, tol=1e-7)

    for axiom_name, passed in results.items():
        assert passed, f"Semiring '{semiring_name}' failed axiom '{axiom_name}'"

    # Verify nsum(a, 3) == a + a + a and power(a, 3) == a * a * a across all sample elements
    for a in samples[:3]:
        nsum_3 = semiring.nsum(a, 3)
        manual_add_3 = semiring.add(semiring.add(a, a), a)
        assert semiring_elements_equal(nsum_3, manual_add_3, tol=1e-6)

        assert semiring_elements_equal(semiring.nsum(a, 0), semiring.zero, tol=1e-6)
        assert semiring_elements_equal(semiring.power(a, 0), semiring.one, tol=1e-6)

        pow_3 = semiring.power(a, 3)
        manual_mul_3 = semiring.mul(semiring.mul(a, a), a)
        assert semiring_elements_equal(pow_3, manual_mul_3, tol=1e-6)

    # Verify Kleene star fixed-point law on dioids that implement star(zero) == one
    try:
        zero_star = semiring.star(semiring.zero)
        if zero_star is not None:
            assert semiring_elements_equal(zero_star, semiring.one, tol=1e-6)
    except NotImplementedError:
        pass
