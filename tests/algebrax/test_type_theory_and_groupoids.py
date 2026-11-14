"""
Unit & Falsification Tests for Categorical Type Theory, Semiring Coeffects & Homotopy Groupoids.
"""

from __future__ import annotations

import pytest

from algebrax.category import (
    CartesianCategory,
    CartesianClosedCategory,
    Category,
    CoeffectContext,
    FiniteMor,
    FiniteObj,
    FiniteSetCCC,
    Functor,
    Groupoid,
    HasCatId,
    HasCompose,
    HasExponentials,
    HasMapMor,
    HasMapObj,
    HasMorInv,
    HasProducts,
    HasQuiver,
    HasTerminal,
    Quiver,
    SemiringCoeffectTracker,
    TransposeFunctor,
)
from algebrax.semiring import BooleanSemiring, StandardSemiring, TropicalSemiring
from algebrax.topology import SimplicialComplex, SimplicialPathGroupoid
from algebrax.verification import (
    verify_coeffect_grading,
    verify_exponential_adjunction,
    verify_path_groupoid_laws,
)


def test_finite_set_ccc_protocol_and_terminal() -> None:
    """Verify that FiniteSetCCC satisfies atomic mixins, CartesianCategory, and CartesianClosedCategory."""
    from algebrax.algebra import Semimodule
    from algebrax.category import (
        CellPosetCategory,
        LawvereMetricCategory,
        MatrixCategory,
        OppositeCategory,
        SemiringChangeOfBaseFunctor,
    )

    ccc = FiniteSetCCC()
    assert CartesianClosedCategory in FiniteSetCCC.__mro__
    assert Category in OppositeCategory.__mro__
    assert Category in MatrixCategory.__mro__
    assert Category in LawvereMetricCategory.__mro__
    assert Category in CellPosetCategory.__mro__
    assert Functor in TransposeFunctor.__mro__
    assert Functor in SemiringChangeOfBaseFunctor.__mro__
    assert Semimodule in CoeffectContext.__mro__
    assert Groupoid in SimplicialPathGroupoid.__mro__
    assert isinstance(ccc, HasQuiver)
    assert isinstance(ccc, HasCatId)
    assert isinstance(ccc, HasCompose)
    assert isinstance(ccc, HasTerminal)
    assert isinstance(ccc, HasProducts)
    assert isinstance(ccc, HasExponentials)
    assert isinstance(ccc, Quiver)
    assert isinstance(ccc, Category)
    assert isinstance(ccc, CartesianCategory)
    assert isinstance(ccc, CartesianClosedCategory)
    assert not isinstance(ccc, Groupoid)

    tf = TransposeFunctor()
    assert isinstance(tf, HasMapObj)
    assert isinstance(tf, HasMapMor)
    assert isinstance(tf, Functor)

    sc = SimplicialComplex([(0, 1, 2)])
    from algebrax.category import FaceInclusion
    from algebrax.topology import ConstantSheaf

    cs = ConstantSheaf.from_simplicial_complex(sc)
    assert isinstance(cs, HasMapObj)
    assert isinstance(cs, HasMapMor)
    assert isinstance(cs, Functor)
    v0 = cs.poset_category.cells_of_dim(0)[0]
    e01 = cs.poset_category.cells_of_dim(1)[0]
    assert cs.map_obj(v0) == frozenset({0})
    assert cs.map_mor(FaceInclusion(v0, e01)) == cs.restriction_map(v0, e01)

    a: FiniteObj = frozenset({1, 2, 3})
    term = ccc.terminal
    assert len(term) == 1

    bang_a = ccc.to_terminal(a)
    assert ccc.source(bang_a) == a
    assert ccc.target(bang_a) == term

    id_a = ccc.id(a)
    assert ccc.compose(id_a, bang_a) == bang_a


def test_finite_set_ccc_products_and_currying_adjunction() -> None:
    """Verify products, exponentials, currying bijection, and beta/eta laws in FiniteSetCCC."""
    ccc = FiniteSetCCC()
    a: FiniteObj = frozenset({'a0', 'a1'})
    b: FiniteObj = frozenset({0, 1})
    c: FiniteObj = frozenset({'x', 'y'})

    ab = ccc.product(a, b)
    assert len(ab) == 4

    exp_cb = ccc.exponential(c, b)
    # |C|^|B| = 2^2 = 4 functions from B to C
    assert len(exp_cb) == 4

    # Empty exponent C^0 has 1 unique empty function
    assert len(ccc.exponential(c, frozenset())) == 1
    # Empty base 0^B (for non-empty B) has 0 functions
    assert len(ccc.exponential(frozenset(), b)) == 0

    # Define two sample morphisms f1, f2 : A x B -> C
    f1: FiniteMor = (
        ab,
        c,
        {
            ('a0', 0): 'x',
            ('a0', 1): 'y',
            ('a1', 0): 'y',
            ('a1', 1): 'x',
        },
    )
    f2: FiniteMor = (
        ab,
        c,
        {
            ('a0', 0): 'x',
            ('a0', 1): 'x',
            ('a1', 0): 'y',
            ('a1', 1): 'y',
        },
    )

    laws = verify_exponential_adjunction(ccc, a, b, c, [f1, f2])
    assert all(laws.values()), f'CCC adjunction failed: {laws}'


def test_finite_set_ccc_validation_and_falsification() -> None:
    """Verify defensive domain/codomain checks and Popperian falsification of broken currying."""
    ccc = FiniteSetCCC()
    a: FiniteObj = frozenset({0, 1})
    b: FiniteObj = frozenset({2, 3})
    c: FiniteObj = frozenset({'u', 'v'})

    f_a_b: FiniteMor = (a, b, {0: 2, 1: 3})
    g_c_a: FiniteMor = (c, a, {'u': 0, 'v': 1})

    with pytest.raises(ValueError, match='Cannot compose'):
        ccc.compose(f_a_b, f_a_b)

    with pytest.raises(ValueError, match='Cannot pair'):
        ccc.pair(f_a_b, g_c_a)

    with pytest.raises(ValueError, match='does not match A x B'):
        ccc.curry(f_a_b, a, b)

    class _BrokenCurryCCC(FiniteSetCCC):
        def curry(self, mor: FiniteMor, a: FiniteObj, b: FiniteObj) -> FiniteMor:
            dom_a, exp_cb, _curried_map = super().curry(mor, a, b)
            first_func = next(iter(exp_cb))
            return (dom_a, exp_cb, dict.fromkeys(dom_a, first_func))

    broken = _BrokenCurryCCC()
    ab = ccc.product(a, b)
    non_const: FiniteMor = (
        ab,
        c,
        {(0, 2): 'u', (0, 3): 'v', (1, 2): 'v', (1, 3): 'u'},
    )
    res = verify_exponential_adjunction(broken, a, b, c, [non_const])
    assert not res['beta_evaluation']
    assert not res['uncurry_curry_bijection']


def test_coeffect_context_and_tracker_across_semirings() -> None:
    """Verify semiring-graded coeffect contexts across N, Boolean, and Tropical semirings."""
    from algebrax.algebra import HasScale, Semimodule

    # 1. Natural number semiring: linear & bounded variable usage counting
    nat_s = StandardSemiring(int)
    nat_ctx = CoeffectContext[str, int](nat_s)
    assert isinstance(nat_ctx, HasScale)
    assert isinstance(nat_ctx, Semimodule)

    c_x = nat_ctx.singleton('x')
    c_y = nat_ctx.singleton('y', 2)
    assert nat_ctx.singleton('z', 0) == {}
    assert nat_ctx.grade_of(c_x, 'x') == 1
    assert nat_ctx.grade_of(c_x, 'missing') == 0

    combined = nat_ctx.add(c_x, c_y)
    # Scaling by loop bound 3 amplifies variable usages: 3 * (1*x + 2*y) = 3*x + 6*y
    loop_scaled = nat_ctx.scale(3, combined)
    assert loop_scaled == {'x': 3, 'y': 6}
    assert nat_ctx.smul(3, combined) == {'x': 3, 'y': 6}
    assert nat_ctx.scale(0, combined) == {}

    nat_laws = verify_coeffect_grading(
        nat_ctx,
        grade_samples=[0, 1, 2, 3],
        context_samples=[{}, {'x': 1}, {'x': 2, 'y': 1}, {'y': 3, 'z': 4}],
    )
    assert all(nat_laws.values()), f'Nat coeffect grading failed: {nat_laws}'

    # 2. Boolean semiring: liveness / dead-code reachability
    bool_s = BooleanSemiring()
    bool_tracker = SemiringCoeffectTracker[str, bool](bool_s)
    bool_tracker.record_cost('live_branch', True)
    bool_tracker.record_cost('dead_branch', False)
    assert bool_tracker.get_cost('live_branch') is True
    assert bool_tracker.get_cost('unreferenced') is False
    assert bool_tracker.compose_parallel('live_branch', 'dead_branch') is True
    assert bool_tracker.compose_sequence('live_branch', 'dead_branch') is False
    assert bool_tracker.costs == {'live_branch': True, 'dead_branch': False}

    # 3. Tropical min-plus semiring: latency / privacy sensitivity budgets
    trop_s = TropicalSemiring()
    trop_tracker = SemiringCoeffectTracker[str, float](trop_s)
    trop_tracker.record_cost('stage_a', 2.5)
    trop_tracker.record_cost('stage_a', 1.5)  # min(2.5, 1.5) = 1.5
    trop_tracker.record_cost('stage_b', 4.0)
    assert trop_tracker.get_cost('stage_a') == pytest.approx(1.5)
    # Sequential composition in TropicalSemiring is addition: 1.5 + 4.0 = 5.5
    assert trop_tracker.compose_sequence('stage_a', 'stage_b') == pytest.approx(5.5)


def test_coeffect_grading_falsification() -> None:
    """Verify Popperian falsification when context scaling violates semimodule distributivity."""
    nat_s = StandardSemiring(int)

    class _NonDistributiveCoeffect(CoeffectContext[str, int]):
        def scale(self, grade: int, ctx: dict[str, int]) -> dict[str, int]:
            return {k: v + grade for k, v in ctx.items()}

    broken_ctx = _NonDistributiveCoeffect(nat_s)
    res = verify_coeffect_grading(
        broken_ctx,
        grade_samples=[0, 1, 2],
        context_samples=[{}, {'x': 1}, {'x': 2, 'y': 3}],
    )
    assert not all(res.values())


def test_simplicial_path_groupoid_filled_vs_punctured_triangle() -> None:
    """Verify homotopy equivalence on a filled 2-simplex vs obstruction on a punctured 1-cycle."""
    # 1. Filled 2-simplex Delta^2 = {0, 1, 2}: simply connected, (0, 1, 2) ~ (0, 2)
    sc_filled = SimplicialComplex([(0, 1, 2)])
    g_filled = SimplicialPathGroupoid.from_simplicial_complex(sc_filled)
    assert isinstance(g_filled, Quiver)
    assert isinstance(g_filled, Category)
    assert isinstance(g_filled, HasMorInv)
    assert isinstance(g_filled, Groupoid)

    assert g_filled.are_homotopic((0, 1, 2), (0, 2))
    assert g_filled.are_homotopic((0, 1, 2, 0), g_filled.id(0))
    assert g_filled.reduce_backtracking((0, 1, 2, 1, 0)) == (0,)

    laws = verify_path_groupoid_laws(
        g_filled,
        sample_paths=[(0,), (0, 1), (0, 1, 2), (0, 1, 2, 0)],
    )
    assert all(laws.values()), f'Path groupoid laws failed: {laws}'

    # 2. Punctured triangle d(Delta^2) = S^1: no 2-simplex, so (0, 1, 2) is NOT homotopic to (0, 2)
    sc_hole = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
    g_hole = SimplicialPathGroupoid.from_simplicial_complex(sc_hole)

    assert not g_hole.are_homotopic((0, 1, 2), (0, 2))
    # Backtracking spurs still cancel even without 2-simplices!
    assert g_hole.are_homotopic((0, 1, 0), (0,))
    assert g_hole.are_homotopic((0, 1, 2, 1), (0, 1))


def test_simplicial_path_groupoid_validation_and_falsification() -> None:
    """Verify input validation and Popperian falsification of path groupoid laws."""
    with pytest.raises(ValueError, match='2 vertices'):
        SimplicialPathGroupoid(vertices=[0, 1], edges=[(0,)])

    with pytest.raises(ValueError, match='3 distinct vertices'):
        SimplicialPathGroupoid(vertices=[0, 1], edges=[(0, 1)], triangles=[(0, 1, 1)])

    g = SimplicialPathGroupoid(vertices=[0, 1, 2], edges=[(0, 1), (1, 2)], triangles=[])
    with pytest.raises(ValueError, match='not in the simplicial complex'):
        g.id(99)
    with pytest.raises(ValueError, match='empty'):
        g.source(())
    with pytest.raises(ValueError, match='empty'):
        g.target(())
    with pytest.raises(ValueError, match='empty'):
        g.compose((), (0,))
    with pytest.raises(ValueError, match='Path mismatch'):
        g.compose((1, 2), (0, 2))
    with pytest.raises(ValueError, match='empty'):
        g.invert_path(())
    with pytest.raises(ValueError, match='empty'):
        g.reduce_backtracking(())

    assert not g.is_valid_path(())
    assert not g.is_valid_path((0, 99))
    assert not g.is_valid_path((0, 2))  # (0, 2) is not an edge in g
    assert not g.are_homotopic((0, 1), (1, 2))  # distinct endpoints
    assert not g.are_homotopic((0, 2), (0, 1, 2))  # invalid edge (0, 2)

    class _NonInvertingGroupoid(SimplicialPathGroupoid):
        def invert_path(self, path: tuple[int, ...]) -> tuple[int, ...]:
            return path

    broken = _NonInvertingGroupoid(vertices=[0, 1, 2], edges=[(0, 1), (1, 2), (0, 2)], triangles=[(0, 1, 2)])
    with pytest.raises(ValueError, match='Path mismatch'):
        verify_path_groupoid_laws(broken, sample_paths=[(0, 1)])
