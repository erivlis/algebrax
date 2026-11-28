"""Comprehensive tests for EP-0252: Universal Semiring Propagation, Parameterized Tries & Domain Unification.

Covers all 8 Acceptance Criteria:
1. Live parameterized semirings in AlgebraicTrie, tensor.einsum/outer_product/dot, pickle roundtrips,
   and O(1) len(trie) consistency across insert, overwrite, delete, and zero-cancelling add().
2. tensor.dot empty-tensor safety and O(N) hash-join scaling in tensor.einsum.
3. SparseChainComplex.hodge_laplacian semiring propagation and defensive boundary_matrices copy.
4. Cochain/CochainAlgebra finite fields (ModularField, GaloisField) and Tropical cup_product 0.0 preservation.
5. GroupHopfAlgebra exact arithmetic over ModularField(5) and StandardField(Fraction), plus Ring validation.
6. pagerank propagation across Standard, Viterbi, Bottleneck semirings and TypeError on StringSemiring.
7. Weighted automata (simulate_nfa, nfa_step), non-aliasing empty run, and nfa_closure Kleene reachability.
8. TopologicalKTheoryRing composition on CommGrothendieckRing over VectorBundleSemiring and verify_comm_ring_laws.
"""

from __future__ import annotations

import math
import pickle
import time
from fractions import Fraction
from typing import Any

import pytest

from algebrax.algebra import (
    CommGrothendieckRing,
    CommSemiring,
    Group,
    GroupHopfAlgebra,
    ModularField,
    StandardField,
)
from algebrax.analysis import pagerank
from algebrax.automata import nfa_closure, nfa_step, simulate_nfa
from algebrax.clifford import CliffordAlgebra
from algebrax.converters import is_algebraic_zero, make_zero_predicate
from algebrax.display import extract_algebraic_signature
from algebrax.matrix import add as mat_add
from algebrax.semiring import (
    BooleanSemiring,
    BottleneckSemiring,
    GaloisField,
    ModularSemiring,
    StandardSemiring,
    StringSemiring,
    TropicalSemiring,
    ViterbiSemiring,
)
from algebrax.tensor import dot as tensor_dot
from algebrax.tensor import einsum, outer_product
from algebrax.topology import (
    Cochain,
    CochainAlgebra,
    DiscreteOrthogonalConnection,
    SimplicialComplex,
    SparseChainComplex,
    TopologicalKTheoryRing,
    VectorBundleSemiring,
    apply_gauge_transformation,
    cup_product,
    trivial_bundle,
)
from algebrax.trie import AlgebraicTrie
from algebrax.verification import (
    verify_comm_ring_laws,
    verify_hopf_algebra_laws,
    verify_ring_laws,
)

# =============================================================================
# Helpers
# =============================================================================


class SymmetricGroupS3(Group[tuple[int, int, int]]):
    """Symmetric group S_3 represented as permutations of (0, 1, 2)."""

    @property
    def one(self) -> tuple[int, int, int]:
        return (0, 1, 2)

    def mul(self, a: tuple[int, int, int], b: tuple[int, int, int]) -> tuple[int, int, int]:
        return (a[b[0]], a[b[1]], a[b[2]])

    def inv(self, a: tuple[int, int, int]) -> tuple[int, int, int]:
        out = [0, 0, 0]
        for idx, val in enumerate(a):
            out[val] = idx
        return (out[0], out[1], out[2])


def _rot2d(theta: float) -> dict[int, dict[int, float]]:
    c = math.cos(theta)
    s = math.sin(theta)
    return {0: {0: c, 1: -s}, 1: {0: s, 1: c}}


def _make_bundle(
    fiber_dim: int,
    transports: dict[tuple[Any, Any], dict[int, dict[int, float]]],
) -> DiscreteOrthogonalConnection:
    conn = DiscreteOrthogonalConnection(fiber_dim)
    for (u, v), mat in transports.items():
        conn.set_transport(u, v, mat)
    return conn


# =============================================================================
# 0. Shared Zero-Predicate Helper
# =============================================================================


def test_make_zero_predicate_and_is_algebraic_zero() -> None:
    """Verify hoisted make_zero_predicate preserves Tropical 0.0 and honors HasZeroPred."""
    trop = TropicalSemiring()
    is_z_trop = make_zero_predicate(trop, tol=1e-9)
    assert is_z_trop(float('inf')) is True
    assert is_z_trop(0.0) is False  # TropicalSemiring.one == 0.0 must NEVER be pruned!
    assert is_algebraic_zero(trop, float('inf')) is True
    assert is_algebraic_zero(trop, 0.0) is False

    f7 = ModularField(7)
    is_z_f7 = make_zero_predicate(f7)
    assert is_z_f7(f7.zero) is True
    assert is_z_f7(f7.one) is False
    assert is_algebraic_zero(f7, f7.zero) is True

    gf = GaloisField(3, [1, 0, 1])  # x^2 + 1 is irreducible over F_3
    is_z_gf = make_zero_predicate(gf)
    assert is_z_gf(gf.zero) is True
    assert is_z_gf(gf.one) is False

    std = StandardSemiring(float)
    is_z_std = make_zero_predicate(std, tol=1e-12)
    assert is_z_std(1e-15) is True
    assert is_z_std(1e-6) is False


# =============================================================================
# AC1: Parameterized AlgebraicTrie, Pickle Roundtrip & O(1) len()
# =============================================================================


def test_ac1_parameterized_trie_modular_galois_clifford_and_pickle() -> None:
    """Verify live parameterized semirings survive einsum, outer_product, dot, and pickle."""
    # 1. ModularField(7)
    f7 = ModularField(7)
    a_mod = AlgebraicTrie(f7)
    a_mod[(0, 0)] = 3
    a_mod[(0, 1)] = 5
    b_mod = AlgebraicTrie(f7)
    b_mod[(0, 0)] = 4
    b_mod[(1, 0)] = 6

    prod_mod = einsum('ij,jk->ik', a_mod, b_mod, semiring=f7)
    assert isinstance(prod_mod.semiring, ModularField)
    assert prod_mod.semiring.p == 7
    # 3*4 + 5*6 = 12 + 30 = 42 = 0 mod 7 -> cancelled & pruned!
    assert len(prod_mod) == 0
    assert (0, 0) not in prod_mod

    a_mod2 = AlgebraicTrie(f7)
    a_mod2[(0,)] = 3
    a_mod2[(1,)] = 4
    out_mod = outer_product(a_mod2, a_mod2, semiring=f7)
    assert isinstance(out_mod.semiring, ModularField)
    assert out_mod.semiring.p == 7
    assert out_mod[(0, 0)] == 2  # 9 mod 7
    assert out_mod[(0, 1)] == 5  # 12 mod 7

    dot_mod = tensor_dot(a_mod2, a_mod2, axes=([0], [0]), semiring=f7)
    assert isinstance(dot_mod.semiring, ModularField)
    assert dot_mod.semiring.p == 7
    assert dot_mod[()] == 4  # (9 + 16) mod 7 = 25 mod 7 = 4

    restored_mod = pickle.loads(pickle.dumps(out_mod))
    assert isinstance(restored_mod.semiring, ModularField)
    assert restored_mod.semiring.p == 7
    assert restored_mod[(0, 1)] == 5
    assert len(restored_mod) == len(out_mod)

    # 2. GaloisField(3, [1, 0, 1]) (GF(3^2) = F_3[x]/(x^2 + 1))
    gf9 = GaloisField(3, [1, 0, 1])
    x = {1: 1}  # generator x
    t_gf = AlgebraicTrie(gf9)
    t_gf[(0,)] = x
    t_gf[(1,)] = gf9.one

    out_gf = outer_product(t_gf, t_gf, semiring=gf9)
    assert isinstance(out_gf.semiring, GaloisField)
    assert (out_gf.semiring.p, out_gf.semiring.irreduc_poly) == (3, (1, 0, 1))
    assert out_gf[(0, 0)] == gf9.mul(x, x)  # x^2 = -1 = 2 mod 3 -> {0: 2}

    ein_gf = einsum('i,i->', t_gf, t_gf, semiring=gf9)
    assert isinstance(ein_gf.semiring, GaloisField)
    # x^2 + 1 = 0 in F_3[x]/(x^2 + 1) -> cancelled & pruned!
    assert len(ein_gf) == 0
    assert () not in ein_gf

    t_gf2 = AlgebraicTrie(gf9)
    t_gf2[(0,)] = x
    t_gf2[(1,)] = {0: 2}
    dot_gf = tensor_dot(t_gf, t_gf2, axes=([0], [0]), semiring=gf9)
    assert isinstance(dot_gf.semiring, GaloisField)
    assert dot_gf[()] == gf9.add(gf9.mul(x, x), {0: 2})

    restored_gf = pickle.loads(pickle.dumps(out_gf))
    assert isinstance(restored_gf.semiring, GaloisField)
    assert (restored_gf.semiring.p, restored_gf.semiring.irreduc_poly) == (3, (1, 0, 1))
    assert restored_gf[(0, 0)] == gf9.mul(x, x)

    # 3. CliffordAlgebra(2, 0, 0)
    cl2 = CliffordAlgebra(2, 0, 0)
    e1 = {(1,): 1.0}
    e2 = {(2,): 1.0}
    t_cl = AlgebraicTrie(cl2)
    t_cl[(0,)] = e1
    t_cl[(1,)] = e2

    out_cl = outer_product(t_cl, t_cl, semiring=cl2)
    assert isinstance(out_cl.semiring, CliffordAlgebra)
    assert (out_cl.semiring.p, out_cl.semiring.q, out_cl.semiring.r) == (2, 0, 0)
    assert out_cl[(0, 1)] == cl2.mul(e1, e2)

    ein_cl = einsum('i,i->', t_cl, t_cl, semiring=cl2)
    assert ein_cl[()] == cl2.add(cl2.mul(e1, e1), cl2.mul(e2, e2))

    dot_cl = tensor_dot(t_cl, t_cl, axes=([0], [0]), semiring=cl2)
    assert dot_cl[()] == cl2.add(cl2.mul(e1, e1), cl2.mul(e2, e2))

    restored_cl = pickle.loads(pickle.dumps(out_cl))
    assert isinstance(restored_cl.semiring, CliffordAlgebra)
    assert (restored_cl.semiring.p, restored_cl.semiring.q, restored_cl.semiring.r) == (2, 0, 0)
    assert restored_cl[(0, 1)] == cl2.mul(e1, e2)
    assert len(restored_cl) == len(out_cl)


def test_ac1_trie_o1_len_and_zero_cancellation_branch_pruning() -> None:
    """Verify O(1) len(trie) matches exact iteration across inserts, overwrites, deletes, and add() cancellation."""
    f5 = ModularField(5)
    t = AlgebraicTrie(f5)
    assert len(t) == 0

    # Insert
    t[(0, 1)] = 2
    t[(0, 2)] = 3
    t[(1, 0)] = 4
    assert len(t) == 3 == sum(1 for _ in t)

    # Overwrite with non-zero -> size unchanged
    t[(0, 1)] = 4
    assert len(t) == 3 == sum(1 for _ in t)

    # Zero-cancelling add() on (0, 2): 3 + 2 = 0 mod 5 -> removed & size decremented
    t.add((0, 2), 2)
    assert len(t) == 2 == sum(1 for _ in t)
    assert (0, 2) not in t

    # Zero-cancelling add() on (0, 1): 4 + 1 = 0 mod 5 -> last child under 0 removed & branch pruned
    t.add((0, 1), 1)
    assert len(t) == 1 == sum(1 for _ in t)
    assert 0 not in t._data  # Emptied intermediate branch pruned

    # Explicit delete
    del t[(1, 0)]
    assert len(t) == 0 == sum(1 for _ in t)
    assert t._data == {}


# =============================================================================
# AC2: tensor.dot Empty Safety & O(N) Hash-Join tensor.einsum
# =============================================================================


def test_ac2_tensor_dot_empty_safety_and_einsum_linear_scaling() -> None:
    """Verify tensor.dot handles empty operands and 3-way diagonal einsum scales linearly."""
    f7 = ModularField(7)
    empty = AlgebraicTrie(f7)
    non_empty = AlgebraicTrie(f7)
    non_empty[(0, 0)] = 3

    res_empty_l = tensor_dot(empty, non_empty, axes=([1], [0]), semiring=f7)
    assert len(res_empty_l) == 0
    assert isinstance(res_empty_l.semiring, ModularField)
    assert res_empty_l.semiring.p == 7

    res_empty_r = tensor_dot(non_empty, empty, axes=([1], [0]), semiring=f7)
    assert len(res_empty_r) == 0
    assert isinstance(res_empty_r.semiring, ModularField)
    assert res_empty_r.semiring.p == 7

    res_both = tensor_dot(empty, empty, axes=([0], [0]), semiring=f7)
    assert len(res_both) == 0

    # Linear O(N) hash-join scaling: N = 2000 diagonal entries (O(N^3) would be 8e9 ops!)
    n = 2000
    diag = AlgebraicTrie(StandardSemiring(float))
    for i in range(n):
        diag[(i, i)] = 2.0

    t0 = time.perf_counter()
    cubed = einsum('ii,ii,ii->i', diag, diag, diag)
    elapsed = time.perf_counter() - t0

    assert elapsed < 3.0, f'Hash-join einsum took too long ({elapsed:.2f}s); expected O(N)'
    assert len(cubed) == n
    assert cubed[(0,)] == 8.0
    assert cubed[(n - 1,)] == 8.0


# =============================================================================
# AC3: SparseChainComplex Hodge Laplacian Propagation & Defensive Copy
# =============================================================================


def test_ac3_hodge_laplacian_semiring_propagation_and_defensive_copy() -> None:
    """Verify hodge_laplacian uses semiring in final add(l_down, l_up) and __init__ copies matrices."""
    mod5 = ModularSemiring(5)
    sc = SimplicialComplex([(0, 1, 2)])
    b1 = sc.boundary_matrices[1]
    b2 = sc.boundary_matrices[2]
    caller_boundaries = {
        1: {r: dict(row) for r, row in b1.items()},
        2: {r: dict(row) for r, row in b2.items()},
    }

    cc = SparseChainComplex(caller_boundaries)

    # Mutate caller dict after construction -> must NOT affect cc
    caller_boundaries[1].clear()
    caller_boundaries[2].clear()
    assert len(cc.boundary_matrices[1]) == len(b1)
    assert len(cc.boundary_matrices[2]) == len(b2)

    # Compare hodge_laplacian(1, semiring=mod5) with explicit add(l_down, l_up, semiring=mod5)
    # Build integer boundary matrices modulo 5 so ModularSemiring(5) entries are ints in 0..4
    b1_mod = {r: {c: int(v) % 5 for c, v in row.items() if int(v) % 5 != 0} for r, row in b1.items()}
    b2_mod = {r: {c: int(v) % 5 for c, v in row.items() if int(v) % 5 != 0} for r, row in b2.items()}
    cc_mod = SparseChainComplex({1: b1_mod, 2: b2_mod})

    lap = cc_mod.hodge_laplacian(1, semiring=mod5)
    from algebrax.matrix import dot as mat_dot
    from algebrax.matrix import transpose

    l_down = mat_dot(transpose(b1_mod), b1_mod, semiring=mod5)
    l_up = mat_dot(b2_mod, transpose(b2_mod), semiring=mod5)
    expected = mat_add(l_down, l_up, semiring=mod5)
    assert lap == expected
    # Every entry in lap must lie in Z/5Z (0..4) — would be >= 5 without semiring in add()!
    for row in lap.values():
        for val in row.values():
            assert 0 <= val < 5


# =============================================================================
# AC4: Cochain / CochainAlgebra Finite Fields & Tropical cup_product
# =============================================================================


def test_ac4_cochain_algebra_finite_fields_and_tropical_cup_product() -> None:
    """Verify CochainAlgebra over ModularField(5) and GF(2^2), orientation negation, and Tropical 0.0."""
    sc = SimplicialComplex([(0, 1, 2)])

    # 1. ModularField(5)
    f5 = ModularField(5)
    ca_f5 = CochainAlgebra(sc, f5)
    # Orientation negation over ModularField(5): reversing (0, 1) -> (1, 0) negates 2 -> 3 mod 5
    omega_f5 = Cochain({(0, 1): 2, (1, 2): 4}, degree=1, ring=f5)
    assert omega_f5[(1, 0)] == 3
    assert omega_f5.get((2, 1)) == 1

    samples_f5 = [
        ca_f5.zero,
        ca_f5.one,
        Cochain({(0,): 2, (1,): 3}, degree=0, ring=f5),
        omega_f5,
        Cochain({(0, 1): 1, (0, 2): 4}, degree=1, ring=f5),
    ]
    laws_f5 = verify_ring_laws(ca_f5, samples_f5)
    assert all(laws_f5.values()), f'CochainAlgebra(ModularField(5)) failed ring laws: {laws_f5}'

    # 2. GaloisField(2, [1, 1, 1]) (GF(4), characteristic 2)
    gf4 = GaloisField(2, [1, 1, 1])
    alpha = {1: 1}
    beta = {0: 1, 1: 1}
    ca_gf4 = CochainAlgebra(sc, gf4)
    omega_gf4 = Cochain({(0, 1): alpha, (1, 2): beta}, degree=1, ring=gf4)
    # In char 2, -alpha == alpha
    assert omega_gf4[(1, 0)] == alpha

    samples_gf4 = [
        ca_gf4.zero,
        ca_gf4.one,
        Cochain({(0,): alpha, (2,): gf4.one}, degree=0, ring=gf4),
        omega_gf4,
        Cochain({(1, 2): alpha, (0, 2): gf4.one}, degree=1, ring=gf4),
    ]
    laws_gf4 = verify_ring_laws(ca_gf4, samples_gf4)
    assert all(laws_gf4.values()), f'CochainAlgebra(GF(4)) failed ring laws: {laws_gf4}'

    # 3. TropicalSemiring cup_product must preserve 0.0 (TropicalSemiring.one)!
    trop = TropicalSemiring()
    c1_trop = Cochain({(0, 1): 0.0}, degree=1, oriented=False, ring=trop)
    c2_trop = Cochain({(1, 2): 0.0}, degree=1, oriented=False, ring=trop)
    cup_trop = cup_product(c1_trop, c2_trop, semiring=trop)
    assert (0, 1, 2) in cup_trop
    assert cup_trop[(0, 1, 2)] == 0.0


# =============================================================================
# AC5: GroupHopfAlgebra Exact ModularField(5) & StandardField(Fraction)
# =============================================================================


def test_ac5_group_hopf_algebra_exact_rings_and_validation() -> None:
    """Verify GroupHopfAlgebra(S3) passes verify_hopf_algebra_laws over ModularField(5) and Fraction."""
    s3 = SymmetricGroupS3()
    e = (0, 1, 2)
    s12 = (1, 0, 2)
    r3 = (1, 2, 0)
    r3_inv = (2, 0, 1)

    # 1. ModularField(5)
    f5 = ModularField(5)
    gh_f5 = GroupHopfAlgebra(s3, coeff_semiring=f5)
    r_f5 = [f5.zero, f5.one, 2, 4]
    c_f5 = [
        gh_f5.zero,
        gh_f5.one,
        {s12: 2, r3: 3},
        {e: 1, r3_inv: 4},
        {s12: 4, r3: 1, r3_inv: 2},
    ]
    laws_f5 = verify_hopf_algebra_laws(gh_f5, r_f5, c_f5)
    assert all(laws_f5.values()), f'GroupHopfAlgebra(S3, GF(5)) failed: {laws_f5}'

    # 2. StandardField(Fraction)
    qf = StandardField(Fraction)
    gh_q = GroupHopfAlgebra(s3, coeff_semiring=qf)
    r_q = [Fraction(0), Fraction(1), Fraction(-1, 2), Fraction(3, 5)]
    c_q = [
        gh_q.zero,
        gh_q.one,
        {s12: Fraction(1, 3), r3: Fraction(-2, 5)},
        {e: Fraction(1, 2), r3_inv: Fraction(5, 7)},
        {s12: Fraction(-1, 4), r3: Fraction(3, 4)},
    ]
    laws_q = verify_hopf_algebra_laws(gh_q, r_q, c_q)
    assert all(laws_q.values()), f'GroupHopfAlgebra(S3, Q) failed: {laws_q}'

    # 3. Non-Ring semiring must raise TypeError upfront
    with pytest.raises(TypeError, match='Ring'):
        GroupHopfAlgebra(s3, coeff_semiring=BooleanSemiring())  # type: ignore[arg-type]


# =============================================================================
# AC6: PageRank Semiring Propagation & Carrier Validation
# =============================================================================


def test_ac6_pagerank_semiring_propagation_and_validation() -> None:
    """Verify pagerank propagates Standard, Viterbi, Bottleneck semirings and rejects StringSemiring."""
    graph = {
        'A': {'B': 1.0, 'C': 1.0},
        'B': {'C': 1.0},
        'C': {'A': 1.0},
    }

    pr_std = pagerank(graph, semiring=StandardSemiring(float))
    assert math.isclose(sum(pr_std.values()), 1.0, rel_tol=1e-5)
    assert pr_std['C'] > pr_std['B']

    pr_vit = pagerank(graph, semiring=ViterbiSemiring())
    assert set(pr_vit.keys()) == {'A', 'B', 'C'}
    assert all(v > 0.0 for v in pr_vit.values())

    pr_bot = pagerank(graph, semiring=BottleneckSemiring())
    assert set(pr_bot.keys()) == {'A', 'B', 'C'}
    assert all(v > 0.0 for v in pr_bot.values())

    # String catalog name support
    pr_str_name = pagerank(graph, semiring='Standard')
    assert all(math.isclose(pr_std[k], pr_str_name[k], rel_tol=1e-6) for k in pr_std)

    # Non-numeric carriers fail upfront with TypeError
    with pytest.raises(TypeError, match='numeric'):
        pagerank(graph, semiring=StringSemiring())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match='numeric'):
        pagerank(graph, semiring=BooleanSemiring())  # type: ignore[arg-type]


# =============================================================================
# AC7: Weighted Automata & Kleene Reachability Closure
# =============================================================================


def test_ac7_weighted_automata_and_nfa_closure() -> None:
    """Verify simulate_nfa across semirings, non-aliasing empty runs, and nfa_closure."""
    # Non-aliasing on empty sequence
    start = {'q0': 1.0}
    res_empty = simulate_nfa(start, [], {})
    assert res_empty == {'q0': 1.0}
    res_empty['q0'] = 99.0
    assert start['q0'] == 1.0

    # 1. BooleanSemiring reachability
    bool_trans = {
        'q0': {'a': {'q1': True, 'q2': True}},
        'q1': {'b': {'q3': True}},
        'q2': {'b': {'q3': True}},
    }
    res_bool = simulate_nfa({'q0': True}, ['a', 'b'], bool_trans, semiring=BooleanSemiring)
    assert res_bool == {'q3': True}

    # 2. TropicalSemiring shortest path cost
    trop_trans = {
        'q0': {'a': {'q1': 2.0, 'q2': 5.0}},
        'q1': {'b': {'q3': 10.0}},
        'q2': {'b': {'q3': 1.0}},
    }
    # q0 -> q1 -> q3 costs 12.0; q0 -> q2 -> q3 costs 6.0 -> min is 6.0
    res_trop = simulate_nfa({'q0': 0.0}, ['a', 'b'], trop_trans, semiring=TropicalSemiring)
    assert res_trop == {'q3': 6.0}

    # 3. ViterbiSemiring max-probability path
    vit_trans = {
        'q0': {'a': {'q1': 0.6, 'q2': 0.4}},
        'q1': {'b': {'q3': 0.2}},
        'q2': {'b': {'q3': 0.9}},
    }
    # q0->q1->q3: 0.12; q0->q2->q3: 0.36 -> max is 0.36
    res_vit = simulate_nfa({'q0': 1.0}, ['a', 'b'], vit_trans, semiring=ViterbiSemiring)
    assert math.isclose(res_vit['q3'], 0.36, rel_tol=1e-9)

    # 4. StringSemiring formal language transduction
    str_trans = {
        'q0': {'a': {'q1': {'x'}, 'q2': {'y'}}},
        'q1': {'b': {'q3': {'1'}}},
        'q2': {'b': {'q3': {'2'}}},
    }
    res_str = simulate_nfa({'q0': {''}}, ['a', 'b'], str_trans, semiring=StringSemiring)
    assert res_str == {'q3': {'x1', 'y2'}}

    # Direct nfa_step check with catalog string name
    step_bool = nfa_step({'q0': True}, 'a', bool_trans, semiring='Boolean')
    assert step_bool == {'q1': True, 'q2': True}

    # 5. nfa_closure: all-symbol & single-symbol (epsilon) over Boolean & Tropical
    closure_bool = nfa_closure(bool_trans, semiring=BooleanSemiring)
    assert closure_bool['q0']['q0'] is True
    assert closure_bool['q0']['q3'] is True
    assert 'q0' not in closure_bool.get('q3', {})

    eps_trans = {
        'q0': {'eps': {'q1': True}, 'a': {'q2': True}},
        'q1': {'eps': {'q3': True}},
    }
    eps_closure = nfa_closure(eps_trans, symbol='eps', semiring=BooleanSemiring)
    assert eps_closure['q0']['q3'] is True
    assert 'q2' not in eps_closure['q0']

    closure_trop = nfa_closure(trop_trans, semiring=TropicalSemiring)
    assert closure_trop['q0']['q0'] == 0.0
    assert closure_trop['q0']['q3'] == 6.0

    # 6. nfa_closure rejects non-StarSemiring (StringSemiring) with TypeError
    with pytest.raises(TypeError, match='StarSemiring'):
        nfa_closure(str_trans, semiring=StringSemiring)  # type: ignore[arg-type]


# =============================================================================
# AC8: TopologicalKTheoryRing on CommGrothendieckRing & VectorBundleSemiring
# =============================================================================


def test_ac8_topological_k_theory_grothendieck_and_comm_ring_laws() -> None:
    """Verify TopologicalKTheoryRing composes CommGrothendieckRing over VectorBundleSemiring."""
    edges = [(0, 1), (1, 2), (0, 2)]
    k_ring = TopologicalKTheoryRing(edges)

    assert isinstance(k_ring, CommGrothendieckRing)
    assert isinstance(k_ring.semiring, VectorBundleSemiring)
    assert isinstance(k_ring.semiring, CommSemiring)

    # AMDS compliance on VectorBundleSemiring
    sig = extract_algebraic_signature(VectorBundleSemiring)
    assert sig is not None
    assert r'\mathrm{Vect}_{\mathbb{R}}(K)' in sig

    # Verify CommRing laws (using orthogonal-similarity equivalence on bundles)
    e1 = _make_bundle(2, {(0, 1): _rot2d(0.4), (1, 2): _rot2d(0.2), (0, 2): _rot2d(-0.1)})
    e2 = _make_bundle(2, {(0, 1): _rot2d(-0.3), (1, 2): _rot2d(0.5), (0, 2): _rot2d(0.2)})
    triv1 = trivial_bundle(1, edges)

    samples = [
        k_ring.zero,
        k_ring.one,
        k_ring.embed(e1),
        (e2, triv1),
    ]
    laws = verify_comm_ring_laws(k_ring, samples)
    assert all(laws.values()), f'TopologicalKTheoryRing failed CommRing laws: {laws}'

    # Popperian falsification check: distinct bundles must NOT be reported equivalent
    assert not k_ring.equiv(k_ring.embed(e1), k_ring.embed(e2))
    assert not k_ring.equiv(k_ring.embed(e1), k_ring.zero)


# =============================================================================
# Council Post-Implementation Review Regression Tests
# =============================================================================


def test_council_k_theory_axial_gauge_holonomy_and_dim5_spectrum() -> None:
    """Verify K-theory equivalence catches opposite holonomy, multi-cycle mismatch, and d=5 spectra."""
    edges = [(0, 1), (1, 2), (0, 2)]
    k_ring = TopologicalKTheoryRing(edges)

    # 1. Opposite-holonomy triangle: identical per-edge O(2) traces (R(+0.5) ~ R(-0.5)),
    #    different cycle holonomy angles (+1.5 vs +0.5) -> must NOT be equivalent.
    b_pos = _make_bundle(2, {(0, 1): _rot2d(0.5), (1, 2): _rot2d(0.5), (2, 0): _rot2d(0.5)})
    b_mix = _make_bundle(2, {(0, 1): _rot2d(0.5), (1, 2): _rot2d(0.5), (2, 0): _rot2d(-0.5)})
    assert not k_ring.equiv(k_ring.embed(b_pos), k_ring.embed(b_mix))

    # 2. Genuine vertex gauge transformation preserves bundle equivalence.
    b_gauged = apply_gauge_transformation(
        b_pos,
        {0: _rot2d(0.7), 1: _rot2d(-1.1), 2: _rot2d(0.3)},
    )
    assert k_ring.equiv(k_ring.embed(b_pos), k_ring.embed(b_gauged))

    # 3. Dimension d = 5 Newton spectrum test:
    #    M_plus has eigenvalues e^{2*pi*i*m/5} (tr(M^k)=0 for k=1..4, tr(M^5)=+5),
    #    M_minus has eigenvalues e^{pi*i*(2m+1)/5} (tr(M^k)=0 for k=1..4, tr(M^5)=-5).
    def _block5(theta1: float, theta2: float, last: float) -> dict[int, dict[int, float]]:
        r1 = _rot2d(theta1)
        r2 = _rot2d(theta2)
        return {
            0: r1[0],
            1: r1[1],
            2: {2: r2[0][0], 3: r2[0][1]},
            3: {2: r2[1][0], 3: r2[1][1]},
            4: {4: last},
        }

    ident5 = {i: {i: 1.0} for i in range(5)}
    m_plus = _block5(2.0 * math.pi / 5.0, 4.0 * math.pi / 5.0, 1.0)
    m_minus = _block5(math.pi / 5.0, 3.0 * math.pi / 5.0, -1.0)
    b5_plus = _make_bundle(5, {(0, 1): ident5, (1, 2): ident5, (0, 2): m_plus})
    b5_minus = _make_bundle(5, {(0, 1): ident5, (1, 2): ident5, (0, 2): m_minus})
    assert not k_ring.equiv(k_ring.embed(b5_plus), k_ring.embed(b5_minus))

    # 4. Multi-cycle simultaneous conjugacy (figure-8 with two triangles sharing vertex 0):
    #    Individual cycle holonomies (R(0.4), R(0.6)) vs (R(0.4), R(-0.6)) have identical
    #    per-cycle traces, but tr(H1 H2) = 2*cos(1.0) != 2*cos(-0.2).
    fig8_edges = [(0, 1), (1, 2), (0, 2), (0, 3), (3, 4), (0, 4)]
    k_fig8 = TopologicalKTheoryRing(fig8_edges)
    ident2 = _rot2d(0.0)
    f8_same = _make_bundle(
        2,
        {
            (0, 1): ident2,
            (1, 2): ident2,
            (0, 2): _rot2d(0.4),
            (0, 3): ident2,
            (3, 4): ident2,
            (0, 4): _rot2d(0.6),
        },
    )
    f8_opp = _make_bundle(
        2,
        {
            (0, 1): ident2,
            (1, 2): ident2,
            (0, 2): _rot2d(0.4),
            (0, 3): ident2,
            (3, 4): ident2,
            (0, 4): _rot2d(-0.6),
        },
    )
    assert not k_fig8.equiv(k_fig8.embed(f8_same), k_fig8.embed(f8_opp))


def test_council_nfa_step_zero_pruning_parity() -> None:
    """Verify nfa_step(semiring=None) prunes zero weights and cancellations like StandardSemiring(float)."""
    transitions = {
        'q0': {'a': {'q3': 2.0, 'q4': 0.0}},
        'q1': {'a': {'q5': 1.0, 'q6': 0.5}},
        'q2': {'a': {'q5': 1.0}},
    }
    current = {'q0': 0.0, 'q1': 1.0, 'q2': -1.0}
    res_default = nfa_step(current, 'a', transitions)
    res_std = nfa_step(current, 'a', transitions, semiring=StandardSemiring(float))
    assert res_default == res_std == {'q6': 0.5}


def test_council_trie_setitem_zero_pruning() -> None:
    """Verify AlgebraicTrie.__setitem__ prunes algebraic zero assignments and emptied branches."""
    f5 = ModularField(5)
    t: AlgebraicTrie[int, int] = AlgebraicTrie(f5)

    # Assigning zero to missing path is a clean no-op
    t[(0, 2)] = f5.zero
    assert len(t) == 0
    assert t._data == {}

    # Assigning zero to existing path deletes it, decrements len, and prunes emptied branches
    t[(0, 2)] = 3
    assert len(t) == 1
    t[(0, 2)] = f5.zero
    assert len(t) == 0 == sum(1 for _ in t)
    assert (0, 2) not in t
    assert t._data == {}


def test_council_cochain_algebra_rejects_non_negatable_semirings() -> None:
    """Verify CochainAlgebra rejects non-Ring/non-StandardSemiring structures upfront."""
    sc = SimplicialComplex([(0, 1, 2)])
    with pytest.raises(TypeError, match='Ring'):
        CochainAlgebra(sc, BooleanSemiring())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match='Ring'):
        CochainAlgebra(sc, TropicalSemiring())  # type: ignore[arg-type]


def test_council_tensor_conflicting_semiring_guard() -> None:
    """Verify tensor ops reject mismatched AlgebraicTrie semirings unless overridden explicitly."""
    f5 = ModularField(5)
    f7 = ModularField(7)
    a = AlgebraicTrie(f5)
    a[(0, 0)] = 2
    b = AlgebraicTrie(f7)
    b[(0, 0)] = 3

    with pytest.raises(ValueError, match='Conflicting semirings'):
        einsum('ij,jk->ik', a, b)
    with pytest.raises(ValueError, match='Conflicting semirings'):
        outer_product(a, b)
    with pytest.raises(ValueError, match='Conflicting semirings'):
        tensor_dot(a, b, axes=([1], [0]))

    # Explicit override succeeds
    overridden = einsum('ij,jk->ik', a, b, semiring=f5)
    assert overridden[(0, 0)] == 1

    # Distinct but equivalent parameterized instances succeed without error
    a2 = AlgebraicTrie(ModularField(5))
    a2[(0, 0)] = 4
    res_eq = einsum('ij,jk->ik', a, a2)
    assert res_eq[(0, 0)] == 3

    cl1 = AlgebraicTrie(CliffordAlgebra(2, 0, 0))
    cl2 = AlgebraicTrie(CliffordAlgebra(2, 0, 0))
    cl1[(0, 0)] = {(1,): 1.0}
    cl2[(0, 0)] = {(2,): 2.0}
    res_cl = einsum('ij,jk->ik', cl1, cl2)
    assert res_cl[(0, 0)] == {(1, 2): 2.0}

