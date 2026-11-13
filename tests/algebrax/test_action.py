"""
Tests for EP-0198: Generalized Closure Operators — Kleene Plus, Matrix Star Closure & Action Algebras.
"""

import pytest

from algebrax.algebra import (
    ActionAlgebra,
    HasPlus,
    HasResiduals,
    KleeneAlgebra,
    RelationActionAlgebra,
    StarSemiring,
)
from algebrax.matrix import matrix_plus, matrix_star, plus, star
from algebrax.semiring import BooleanSemiring, StandardSemiring, TropicalSemiring
from algebrax.verification import (
    verify_action_algebra_laws,
    verify_matrix_conway_laws,
    verify_residuation_laws,
    verify_star_plus_consistency,
)


def test_has_plus_and_residuals_protocols():
    """Verify HasPlus and HasResiduals protocols."""
    assert issubclass(HasPlus, object)
    assert issubclass(HasResiduals, object)

    b = BooleanSemiring()
    assert isinstance(b, HasPlus)
    assert isinstance(b, HasResiduals)
    assert isinstance(b, ActionAlgebra)

    t = TropicalSemiring()
    assert isinstance(t, HasPlus)


def test_scalar_star_and_plus():
    """Verify scalar star and plus consistency on Boolean and Tropical semirings."""
    b = BooleanSemiring()
    assert b.star(False) is True
    assert b.plus(False) is False
    assert b.star(True) is True
    assert b.plus(True) is True

    res_b = verify_star_plus_consistency(b, [False, True])
    assert all(res_b.values()), f'Boolean star-plus consistency failed: {res_b}'

    t = TropicalSemiring()
    assert t.star(5.0) == 0.0
    assert t.plus(5.0) == 5.0
    assert t.star(0.0) == 0.0
    assert t.plus(0.0) == 0.0

    res_t = verify_star_plus_consistency(t, [0.0, 1.0, 2.5, 10.0])
    assert all(res_t.values()), f'Tropical star-plus consistency failed: {res_t}'


def test_boolean_action_algebra():
    """Verify BooleanSemiring satisfies all Action Algebra axioms."""
    b = BooleanSemiring()
    assert isinstance(b, ActionAlgebra)

    # Truth table for ldiv and rdiv: a \ b <=> not a or b
    assert b.ldiv(True, True) is True
    assert b.ldiv(True, False) is False
    assert b.ldiv(False, True) is True
    assert b.ldiv(False, False) is True

    # rdiv(b, a) = b / a <=> not a or b
    assert b.rdiv(True, True) is True
    assert b.rdiv(False, True) is False
    assert b.rdiv(True, False) is True
    assert b.rdiv(False, False) is True

    res = verify_action_algebra_laws(b, [False, True])
    assert all(res.values()), f'Boolean action algebra verification failed: {res}'


def test_relation_action_algebra():
    """Verify RelationActionAlgebra satisfies all Action Algebra axioms."""
    domain = (0, 1, 2)
    rel_alg = RelationActionAlgebra(domain)
    assert isinstance(rel_alg, ActionAlgebra)

    zero = rel_alg.zero
    one = rel_alg.one
    assert len(zero) == 0
    assert len(one) == 3
    assert (0, 0) in one
    assert (1, 1) in one
    assert (2, 2) in one

    # Relations: edge 0->1, 1->2
    r1 = frozenset({(0, 1)})
    r2 = frozenset({(1, 2)})

    # Composition: r1 · r2 = 0->2
    prod = rel_alg.mul(r1, r2)
    assert prod == frozenset({(0, 2)})

    # Star of r1: I U {(0, 1)}
    r1_star = rel_alg.star(r1)
    assert (0, 0) in r1_star
    assert (1, 1) in r1_star
    assert (2, 2) in r1_star
    assert (0, 1) in r1_star

    # Plus of r1: {(0, 1)}
    r1_plus = rel_alg.plus(r1)
    assert r1_plus == r1

    # Cycle: 0->1, 1->0
    cycle = frozenset({(0, 1), (1, 0)})
    cycle_star = rel_alg.star(cycle)
    assert (0, 0) in cycle_star
    assert (1, 1) in cycle_star
    assert (0, 1) in cycle_star
    assert (1, 0) in cycle_star
    cycle_plus = rel_alg.plus(cycle)
    assert (0, 0) in cycle_plus
    assert (1, 1) in cycle_plus

    # Sample relations for verification
    samples = [
        zero,
        one,
        frozenset({(0, 1)}),
        frozenset({(1, 2)}),
        frozenset({(0, 1), (1, 2)}),
        frozenset({(0, 1), (1, 0)}),
    ]

    res_res = verify_residuation_laws(rel_alg, samples)
    assert all(res_res.values()), f'Relation residuation failed: {res_res}'

    res_act = verify_action_algebra_laws(rel_alg, samples)
    assert all(res_act.values()), f'Relation action algebra verification failed: {res_act}'


def test_matrix_conway_base_cases():
    """Verify matrix_star and matrix_plus on 0x0 and 1x1 base cases."""
    b = BooleanSemiring()

    # 0x0
    assert matrix_star({}, b) == {}
    assert matrix_plus({}, b) == {}

    # 1x1 zero entry
    m_zero = {0: {0: False}}
    # [False]* = [True]
    assert matrix_star(m_zero, b) == {0: {0: True}}
    # [False]+ = [False]
    assert matrix_plus(m_zero, b) == {}

    # 1x1 one entry
    m_one = {0: {0: True}}
    assert matrix_star(m_one, b) == {0: {0: True}}
    assert matrix_plus(m_one, b) == {0: {0: True}}


def test_matrix_conway_boolean_dag():
    """Verify matrix_star vs matrix_plus on a Directed Acyclic Graph (DAG)."""
    b = BooleanSemiring()
    # Graph: 0 -> 1 -> 2
    dag = {
        0: {1: True},
        1: {2: True},
    }

    # Star includes reflexive identity on all nodes {0, 1, 2}
    dag_star = matrix_star(dag, b)
    assert dag_star[0][0] is True
    assert dag_star[1][1] is True
    assert dag_star[2][2] is True
    assert dag_star[0][1] is True
    assert dag_star[1][2] is True
    assert dag_star[0][2] is True

    # Plus gives strict transitive paths: no reflexive loops on DAG!
    dag_plus = matrix_plus(dag, b)
    assert 0 not in dag_plus.get(0, {})  # No self-loop!
    assert 1 not in dag_plus.get(1, {})  # No self-loop!
    assert 2 not in dag_plus.get(2, {})  # No self-loop!
    assert dag_plus[0][1] is True
    assert dag_plus[1][2] is True
    assert dag_plus[0][2] is True

    # Conway laws verification
    res = verify_matrix_conway_laws(dag, b)
    assert all(res.values()), f'Matrix Conway laws failed on Boolean DAG: {res}'


def test_matrix_conway_tropical_apsp():
    """Verify matrix_star computes All-Pairs Shortest Paths (APSP) on TropicalSemiring."""
    t = TropicalSemiring()
    # 3-node graph with edge weights:
    # 0 -> 1 (weight 2.0)
    # 1 -> 2 (weight 3.0)
    # 0 -> 2 (weight 10.0)
    graph = {
        0: {1: 2.0, 2: 10.0},
        1: {2: 3.0},
    }

    apsp = matrix_star(graph, t)
    # Shortest paths:
    # 0->0: 0.0, 1->1: 0.0, 2->2: 0.0
    assert apsp[0][0] == 0.0
    assert apsp[1][1] == 0.0
    assert apsp[2][2] == 0.0
    # 0->1: 2.0
    assert apsp[0][1] == 2.0
    # 1->2: 3.0
    assert apsp[1][2] == 3.0
    # 0->2: min(10.0, 2.0 + 3.0) = 5.0
    assert apsp[0][2] == 5.0

    # Conway laws verification
    res = verify_matrix_conway_laws(graph, t)
    assert all(res.values()), f'Matrix Conway laws failed on Tropical graph: {res}'


def test_matrix_conway_standard_neumann():
    """Verify matrix_star on StandardSemiring computes (I - A)^(-1)."""
    s = StandardSemiring()
    # Nilpotent matrix:
    # A = [[0, 0.5], [0, 0]]
    # (I - A)^(-1) = [[1, 0.5], [0, 1]]
    a = {
        0: {1: 0.5},
    }
    a_star = matrix_star(a, s)
    assert a_star[0][0] == 1.0
    assert a_star[1][1] == 1.0
    assert a_star[0][1] == 0.5

    a_plus = matrix_plus(a, s)
    assert 0 not in a_plus.get(0, {})
    assert 1 not in a_plus.get(1, {})
    assert a_plus[0][1] == 0.5

    res = verify_matrix_conway_laws(a, s)
    assert all(res.values()), f'Matrix Conway laws failed on Standard matrix: {res}'


def test_aliases_and_submodule_exports():
    """Verify star, plus, matrix_star, and matrix_plus exports."""
    from algebrax.matrix import matrix_plus as mp
    from algebrax.matrix import matrix_star as ms
    from algebrax.matrix import plus as p
    from algebrax.matrix import star as s

    assert ms is s
    assert mp is p
