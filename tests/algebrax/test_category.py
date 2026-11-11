"""
Tests for Categorical Abstractions, MatrixCategory Mat(S), LawvereMetricCategory,
Functors, Kleisli Composition, and Category/Functor Axiom Verification (EP-0200).
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from algebrax.category import (
    Category,
    Functor,
    LawvereMetricCategory,
    MatrixCategory,
    OppositeCategory,
    SemiringChangeOfBaseFunctor,
    TransposeFunctor,
    kan_extension_left,
    kleisli_compose,
)
from algebrax.semiring import (
    BooleanSemiring,
    Semiring,
    StandardSemiring,
    TropicalSemiring,
    ViterbiSemiring,
)
from algebrax.verification import verify_category_laws, verify_functor_laws


def test_kleisli_probabilistic_composition():
    """Test Kleisli composition of probabilistic transition morphisms over ViterbiSemiring."""
    f = {'A': {'B': 0.8, 'C': 0.2}}
    g = {'B': {'D': 0.9}, 'C': {'D': 0.5}}

    res = kleisli_compose(f, g, semiring=ViterbiSemiring())
    # Expected max path to D: max(0.8*0.9=0.72, 0.2*0.5=0.10) = 0.72
    assert abs(res['A']['D'] - 0.72) < 1e-6


def test_kleisli_cost_lawvere_composition():
    """Test Kleisli composition in Lawvere Metric Category over TropicalSemiring."""
    f = {'A': {'B': 3.0, 'C': 7.0}}
    g = {'B': {'D': 2.0}, 'C': {'D': 1.0}}

    res = kleisli_compose(f, g, semiring=TropicalSemiring())
    # Expected min cost to D: min(3+2, 7+1) = 5.0
    assert abs(res['A']['D'] - 5.0) < 1e-6

    p = {0: {1: 1.0}}
    fn = {0: {0: 2.0}}
    assert kan_extension_left(p, fn) == {0: {1: 2.0}}


def test_matrix_category_protocols_and_axioms():
    """Verify MatrixCategory satisfies Category protocol and passes verify_category_laws across semirings."""
    for sr in (StandardSemiring(Fraction), StandardSemiring(float), TropicalSemiring(), BooleanSemiring()):
        cat = MatrixCategory(sr)
        assert isinstance(cat, Category)
        assert cat.semiring is sr

    # Exact verification over Q
    cat_q = MatrixCategory(StandardSemiring(Fraction))
    obj = frozenset({0, 1, 2})
    id_mat = cat_q.id(obj)
    assert id_mat == {0: {0: Fraction(1)}, 1: {1: Fraction(1)}, 2: {2: Fraction(1)}}

    m1 = {0: {0: Fraction(1), 1: Fraction(2)}, 1: {2: Fraction(3)}, 2: {0: Fraction(-1)}}
    m2 = {0: {1: Fraction(1, 2)}, 1: {1: Fraction(2), 2: Fraction(-1)}, 2: {0: Fraction(4), 2: Fraction(1)}}
    m3 = {0: {0: Fraction(2), 2: Fraction(1)}, 1: {0: Fraction(-3)}, 2: {1: Fraction(1, 3), 2: Fraction(2)}}

    assert cat_q.source(m1) == frozenset({0, 1, 2})
    assert cat_q.target(m1) == frozenset({0, 1, 2})

    laws = verify_category_laws(cat_q, [obj], [m1, m2, m3])
    assert laws == {'left_identity': True, 'right_identity': True, 'associativity': True}

    # Trivial zero-ring edge case where one == zero
    class ZeroRing(Semiring[int]):
        zero = 0
        one = 0

        def add(self, a: int, b: int) -> int:
            return 0

        def mul(self, a: int, b: int) -> int:
            return 0

    zcat = MatrixCategory(ZeroRing())
    assert zcat.id(obj) == {}


def test_opposite_category_and_transpose_duality_functor():
    """Verify OppositeCategory involution and TransposeFunctor isomorphism Mat(S)^op -> Mat(S)."""
    cat = MatrixCategory(StandardSemiring(Fraction))
    op_cat = cat.opposite()

    assert isinstance(op_cat, OppositeCategory)
    assert isinstance(op_cat, Category)
    assert op_cat.base is cat
    assert op_cat.opposite() is cat

    obj = frozenset({0, 1, 2})
    m1 = {0: {0: Fraction(1), 1: Fraction(2)}, 1: {2: Fraction(3)}, 2: {0: Fraction(-1), 1: Fraction(4)}}
    m2 = {0: {1: Fraction(2), 2: Fraction(1)}, 1: {0: Fraction(-1), 1: Fraction(3)}, 2: {2: Fraction(5)}}
    m3 = {0: {0: Fraction(3)}, 1: {1: Fraction(2), 2: Fraction(-2)}, 2: {0: Fraction(1), 2: Fraction(1)}}

    # OppositeCategory satisfies Category laws
    op_laws = verify_category_laws(op_cat, [obj], [m1, m2, m3])
    assert op_laws == {'left_identity': True, 'right_identity': True, 'associativity': True}

    # TransposeFunctor F: Mat(S)^op -> Mat(S) satisfies Functor laws: (f o_op g)^T = (g . f)^T = f^T . g^T
    tf = TransposeFunctor()
    assert isinstance(tf, Functor)
    f_laws = verify_functor_laws(tf, op_cat, cat, [obj], [m1, m2, m3])
    assert f_laws == {'identity_preservation': True, 'composition_preservation': True}


def test_semiring_change_of_base_functor():
    """Verify SemiringChangeOfBaseFunctor preserves identity and matrix composition."""
    # Support homomorphism phi: StandardSemiring(int) (on non-negative ints) -> BooleanSemiring (x != 0)
    cat_int = MatrixCategory(StandardSemiring(int))
    cat_bool = MatrixCategory(BooleanSemiring())

    support_functor = SemiringChangeOfBaseFunctor(lambda v: v > 0, BooleanSemiring())
    assert isinstance(support_functor, Functor)

    obj = frozenset({0, 1, 2})
    a = {0: {0: 1, 1: 2}, 1: {2: 3}, 2: {0: 4}}
    b = {0: {1: 1}, 1: {1: 5, 2: 1}, 2: {0: 2, 2: 1}}
    c = {0: {0: 2, 2: 1}, 1: {0: 3}, 2: {1: 1, 2: 4}}

    res = verify_functor_laws(support_functor, cat_int, cat_bool, [obj], [a, b, c])
    assert res == {'identity_preservation': True, 'composition_preservation': True}

    # Also test entry pruning when phi maps a non-zero value to target zero (e.g. mod 2 projection)
    mod2_functor = SemiringChangeOfBaseFunctor(lambda v: (v % 2) == 1, BooleanSemiring())
    mapped = mod2_functor.map_mor({0: {0: 2, 1: 3}, 1: {0: 4}})
    assert mapped == {0: {1: True}}


def test_lawvere_metric_category_and_metric_closure():
    """Verify LawvereMetricCategory shortest-path composition, metric closure, and triangle inequality."""
    # Directed graph where direct edge 0 -> 2 has weight 10.0, but path 0 -> 1 -> 2 has weight 2.0 + 3.0 = 5.0
    raw_dist = {
        'A': {'B': 2.0, 'C': 10.0},
        'B': {'C': 3.0},
    }
    lawvere = LawvereMetricCategory(raw_dist)
    assert isinstance(lawvere, Category)
    assert lawvere.distance_matrix == raw_dist
    assert lawvere.objects() == frozenset({'A', 'B', 'C'})

    # Diagonal defaults to 0.0; missing edge defaults to +inf
    assert lawvere.distance('A', 'A') == 0.0
    assert lawvere.distance('A', 'B') == 2.0
    assert lawvere.distance('A', 'C') == 10.0
    assert lawvere.distance('C', 'A') == float('inf')

    # Raw distance violates triangle inequality because d(A, C) = 10 > d(A, B) + d(B, C) = 5
    assert lawvere.satisfies_triangle_inequality() is False

    # 2-step composition via compose_paths
    two_hop = lawvere.compose_paths(raw_dist, raw_dist)
    assert two_hop['A']['C'] == pytest.approx(5.0)

    # Metric closure (Kleene star) enforces Lawvere enriched axioms (identity 0 and triangle inequality)
    closed_mat = lawvere.metric_closure()
    closed_lawvere = LawvereMetricCategory(closed_mat)
    assert closed_lawvere.distance('A', 'C') == pytest.approx(5.0)
    assert closed_lawvere.distance('A', 'A') == pytest.approx(0.0)
    assert closed_lawvere.satisfies_triangle_inequality() is True

    # Verify Category laws on the closed metric space
    pts = frozenset({'A', 'B', 'C'})
    m_id = closed_lawvere.id(pts)
    assert verify_category_laws(closed_lawvere, [pts], [closed_mat, two_hop, m_id]) == {
        'left_identity': True,
        'right_identity': True,
        'associativity': True,
    }

    # Negative self-loop violates d(x, x) == 0
    bad_diag = LawvereMetricCategory({'A': {'A': -1.0}})
    assert bad_diag.satisfies_triangle_inequality() is False

    # Empty Lawvere category
    empty_lawvere: LawvereMetricCategory[str] = LawvereMetricCategory()
    assert empty_lawvere.objects() == frozenset()
    assert empty_lawvere.metric_closure() == {}
    assert empty_lawvere.satisfies_triangle_inequality() is True


def test_category_and_functor_verifiers_falsify_broken_implementations():
    """Verify that verify_category_laws and verify_functor_laws detect broken category/functor axioms."""

    class BrokenCategory:
        def id(self, x: int) -> int:
            return 99  # Wrong identity

        def compose(self, f: int, g: int) -> int:
            return f - 2 * g + 1  # Non-associative

        def source(self, f: int) -> int:
            return 0

        def target(self, f: int) -> int:
            return 0

    bcat = BrokenCategory()
    cat_res = verify_category_laws(bcat, [0], [1, 2, 3])
    assert cat_res == {'left_identity': False, 'right_identity': False, 'associativity': False}

    class BrokenFunctor:
        def map_obj(self, x: frozenset[int]) -> frozenset[int]:
            return x

        def map_mor(self, f: dict[int, dict[int, float]]) -> dict[int, dict[int, float]]:
            # Constant non-identity output breaks both identity_preservation and composition_preservation
            return {0: {0: 42.0}}

    std_cat = MatrixCategory(StandardSemiring(float))
    obj = frozenset({0, 1})
    m1 = {0: {0: 1.0, 1: 2.0}, 1: {1: 1.0}}
    m2 = {0: {0: 2.0}, 1: {0: 1.0, 1: 3.0}}
    m3 = {0: {1: 1.0}, 1: {0: 1.0}}

    bfunc = BrokenFunctor()
    func_res = verify_functor_laws(bfunc, std_cat, std_cat, [obj], [m1, m2, m3])
    assert func_res == {'identity_preservation': False, 'composition_preservation': False}

    with pytest.raises(ValueError, match='at least 1 test object'):
        verify_functor_laws(bfunc, std_cat, std_cat, [], [m1, m2, m3])
