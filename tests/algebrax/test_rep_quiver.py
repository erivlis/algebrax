"""Tests for Quiver Representations, Path Algebras, Tits Form, Gabriel's ADE Theorem & CellularSheaf Bridge."""

from __future__ import annotations

from fractions import Fraction

import pytest

from algebrax.algebra import Algebra, PathAlgebra, Ring, path_algebra
from algebrax.category import Quiver as CategoryQuiver
from algebrax.matrix.core import dot
from algebrax.rep import (
    FiniteQuiver,
    QuiverRepresentation,
    bgp_reflect_dimension,
    classify_dynkin_type,
    classify_representation_type,
    cycle_quiver,
    direct_sum_quiver_rep,
    dynkin_quiver,
    euler_form,
    from_cellular_sheaf,
    gabriel_positive_roots,
    interval_representation,
    kronecker_quiver,
    simple_representation,
    tits_quadratic_form,
    to_cellular_sheaf,
)
from algebrax.semiring.arithmetic import StandardSemiring
from algebrax.topology.sheaf import CellularSheaf
from algebrax.verification import (
    verify_algebra_laws,
    verify_quiver_direct_sum,
    verify_quiver_morphism_commutation,
    verify_ring_laws,
    verify_tits_positive_definiteness,
)


def _extended_d4_quiver() -> FiniteQuiver[int, str]:
    """4-subspace star quiver ~D4 (one central hub with 4 leaves)."""
    return FiniteQuiver.from_edges((0, 1, 2, 3, 4), [('e0', 1, 0), ('e1', 2, 0), ('e2', 3, 0), ('e3', 4, 0)])


def _extended_d5_quiver() -> FiniteQuiver[int, str]:
    """Extended ~D5 quiver: two degree-3 hubs (0, 1) each with two leaves."""
    return FiniteQuiver.from_edges(
        (0, 1, 2, 3, 4, 5),
        [('mid', 0, 1), ('a', 2, 0), ('b', 3, 0), ('c', 1, 4), ('d', 1, 5)],
    )


def _tree_with_arms(arms: tuple[int, int, int]) -> FiniteQuiver[int, str]:
    """Build a rooted tree with one degree-3 hub (vertex 0) and three arms of given lengths."""
    verts = [0]
    edges: list[tuple[str, int, int]] = []
    next_v = 1
    e_idx = 0
    for arm_len in arms:
        prev = 0
        for _ in range(arm_len):
            verts.append(next_v)
            edges.append((f'e{e_idx}', prev, next_v))
            prev = next_v
            next_v += 1
            e_idx += 1
    return FiniteQuiver.from_edges(verts, edges)


# =============================================================================
# 1. Quiver Structure, Representations, Direct Sums & Morphisms
# =============================================================================


class TestQuiverRepresentations:
    """Verify FiniteQuiver construction, representations, morphisms, and direct sums."""

    def test_quiver_construction_and_queries(self) -> None:
        q = dynkin_quiver('A', 3, orientation='linear')
        assert isinstance(q, CategoryQuiver)
        assert q.source('e0') == 0
        assert q.target('e0') == 1
        assert q.num_vertices == 3
        assert q.num_edges == 2
        assert q.is_acyclic()
        assert len(q.outgoing(0)) == 1
        assert len(q.incoming(0)) == 0
        assert len(q.all_paths()) == 6  # 3 length-0 + 2 length-1 + 1 length-2

    def test_quiver_validation_errors(self) -> None:
        with pytest.raises(ValueError, match='unique'):
            FiniteQuiver((0, 0), (), {}, {})
        with pytest.raises(ValueError, match='unique'):
            FiniteQuiver((0, 1), ('a', 'a'), {'a': 0}, {'a': 1})
        with pytest.raises(KeyError, match='present'):
            FiniteQuiver((0, 1), ('a',), {'a': 0}, {})
        with pytest.raises(ValueError, match='Source vertex'):
            FiniteQuiver((0, 1), ('a',), {'a': 99}, {'a': 1})
        with pytest.raises(ValueError, match='Target vertex'):
            FiniteQuiver((0, 1), ('a',), {'a': 0}, {'a': 99})

    def test_representation_direct_sum_and_morphisms(self) -> None:
        # A3 persistence-module quiver: 0 -> 1 -> 2
        q = dynkin_quiver('A', 3)
        rep_full = interval_representation(q, (0, 1, 2))
        rep_tail = interval_representation(q, (1, 2))
        rep_s0 = simple_representation(q, 0)

        assert rep_full.dimension_vector == (1, 1, 1)
        assert rep_tail.dimension_vector == (0, 1, 1)
        assert rep_s0.dimension_vector == (1, 0, 0)

        dsum = rep_full.direct_sum(rep_tail)
        assert dsum.dimension_vector == (1, 2, 2)
        assert dsum.total_dimension == 5
        assert all(verify_quiver_direct_sum(rep_full, rep_tail, dsum).values())

        # Canonical surjection rep_full -> simple_representation(q, 0) (head projection)
        proj_head = {0: {0: {0: 1.0}}, 1: {}, 2: {}}
        assert all(verify_quiver_morphism_commutation(rep_full, rep_s0, proj_head).values())

        # Canonical inclusion rep_tail -> rep_full (submodule)
        inc_tail = {0: {}, 1: {0: {0: 1.0}}, 2: {0: {0: 1.0}}}
        assert all(verify_quiver_morphism_commutation(rep_tail, rep_full, inc_tail).values())

    def test_representation_validation_errors(self) -> None:
        q = dynkin_quiver('A', 2)
        with pytest.raises(KeyError, match='Missing dimension'):
            QuiverRepresentation(q, {0: 1}, {'e0': {}})
        with pytest.raises(ValueError, match='non-negative'):
            QuiverRepresentation(q, {0: -1, 1: 1}, {'e0': {}})
        with pytest.raises(ValueError, match='Row index'):
            QuiverRepresentation(q, {0: 1, 1: 1}, {'e0': {2: {0: 1.0}}})
        with pytest.raises(ValueError, match='Col index'):
            QuiverRepresentation(q, {0: 1, 1: 1}, {'e0': {0: {3: 1.0}}})


# =============================================================================
# 2. Tits Form, Gabriel's ADE Theorem & Weyl/BGP Reflections
# =============================================================================


class TestGabrielADETheorem:
    """Verify Tits quadratic form, ADE / Euclidean / Wild classification, and root bijection."""

    @pytest.mark.parametrize(
        ('family', 'rank', 'expected_label', 'expected_pos_roots'),
        [
            ('A', 1, 'A1', 1),
            ('A', 2, 'A2', 3),
            ('A', 3, 'A3', 6),
            ('A', 4, 'A4', 10),
            ('D', 4, 'D4', 12),
            ('D', 5, 'D5', 20),
            ('E6', None, 'E6', 36),
            ('E7', None, 'E7', 63),
            ('E8', None, 'E8', 120),
        ],
    )
    def test_ade_quivers_finite_type_and_root_bijection(
        self,
        family: str,
        rank: int | None,
        expected_label: str,
        expected_pos_roots: int,
    ) -> None:
        for orient in ('linear', 'alternating'):
            q = dynkin_quiver(family, rank, orientation=orient)
            assert classify_representation_type(q) == 'finite'
            assert classify_dynkin_type(q) == expected_label

            checks = verify_tits_positive_definiteness(q)
            assert all(checks.values()), f'Failed Tits positive definiteness on {expected_label}: {checks}'

            roots = gabriel_positive_roots(q)
            assert len(roots) == expected_pos_roots
            for r in roots:
                assert tits_quadratic_form(q, r) == 1

    def test_tame_euclidean_quivers_classified_and_radical_zero(self) -> None:
        # ~A0 (Jordan loop), ~A1 (Kronecker 2-arrow), ~A2 (3-cycle), ~D4, ~D5, ~E6, ~E7, ~E8
        tame_cases: list[tuple[FiniteQuiver[int, str], str, list[int]]] = [
            (cycle_quiver(1), '~A0', [1]),
            (kronecker_quiver(2), '~A1', [1, 1]),
            (cycle_quiver(3), '~A2', [1, 1, 1]),
            (_extended_d4_quiver(), '~D4', [2, 1, 1, 1, 1]),
            (_extended_d5_quiver(), '~D5', [2, 2, 1, 1, 1, 1]),
            (_tree_with_arms((2, 2, 2)), '~E6', [3, 2, 1, 2, 1, 2, 1]),
            (_tree_with_arms((1, 3, 3)), '~E7', [4, 2, 3, 2, 1, 3, 2, 1]),
            (_tree_with_arms((1, 2, 5)), '~E8', [6, 3, 4, 2, 5, 4, 3, 2, 1]),
        ]
        for q, expected_label, radical_delta in tame_cases:
            assert classify_representation_type(q) == 'tame'
            assert classify_dynkin_type(q) == expected_label
            assert tits_quadratic_form(q, radical_delta) == 0
            checks = verify_tits_positive_definiteness(q)
            assert not checks['positive_definite']
            assert not checks['ade_classification']
            assert not checks['samples_positive']

    def test_wild_quivers_have_negative_tits_witness(self) -> None:
        # 3-arrow Kronecker, 2-loop bouquet, 5-star, and (1, 2, 6) wild tree
        wild_cases = [
            kronecker_quiver(3),
            FiniteQuiver.from_edges((0,), [('l1', 0, 0), ('l2', 0, 0)]),
            FiniteQuiver.from_edges((0, 1, 2, 3, 4, 5), [(f'e{i}', i, 0) for i in range(1, 6)]),
            _tree_with_arms((1, 2, 6)),
        ]
        for q in wild_cases:
            assert classify_representation_type(q) == 'wild'
            assert classify_dynkin_type(q) == 'Wild'
            checks = verify_tits_positive_definiteness(q)
            assert not checks['positive_definite']
            assert not checks['ade_classification']
            assert not checks['samples_positive']
            with pytest.raises(ValueError, match='finite-type ADE'):
                gabriel_positive_roots(q)

    def test_disconnected_quiver_classification(self) -> None:
        # Disjoint union A2 + D4 is still finite
        q = FiniteQuiver.from_edges(
            (0, 1, 2, 3, 4, 5),
            [('a', 0, 1), ('d1', 2, 3), ('d2', 2, 4), ('d3', 2, 5)],
        )
        assert classify_representation_type(q) == 'finite'
        assert classify_dynkin_type(q) == 'A2 + D4'
        assert len(gabriel_positive_roots(q)) == 3 + 12

    def test_bgp_reflection_preserves_tits_form(self) -> None:
        q = dynkin_quiver('D', 4)
        d = {0: 1, 1: 2, 2: 1, 3: 1}
        base_q = tits_quadratic_form(q, d)
        assert base_q == 1
        for v in q.vertices:
            reflected = bgp_reflect_dimension(q, d, v)
            assert tits_quadratic_form(q, reflected) == base_q
            # Reflection is an involution: s_v(s_v(d)) == d
            assert bgp_reflect_dimension(q, reflected, v) == d

    def test_euler_form_non_symmetry_and_cartan_relation(self) -> None:
        q = dynkin_quiver('A', 3)
        u = {0: 1, 1: 2, 2: 1}
        v = {0: 2, 1: 1, 2: 3}
        # Euler form is non-symmetric: <u, v> != <v, u> in general
        assert euler_form(q, u, v) != euler_form(q, v, u)
        # Symmetrized Euler form equals u^T C_Q v
        c_mat = q.symmetric_cartan_matrix()
        u_list = [u[i] for i in range(3)]
        v_list = [v[i] for i in range(3)]
        bilinear_c = sum(u_list[i] * c_mat[i][j] * v_list[j] for i in range(3) for j in range(3))
        assert euler_form(q, u, v) + euler_form(q, v, u) == bilinear_c


# =============================================================================
# 3. Path Algebra KQ & Module Action
# =============================================================================


class TestPathAlgebra:
    """Verify PathAlgebra axioms, orthogonal idempotents, concatenation, and module evaluation."""

    def test_path_algebra_protocol_and_laws(self) -> None:
        q = dynkin_quiver('A', 3)
        coeff_ring = StandardSemiring(Fraction)
        kq = path_algebra(q, coeff_semiring=coeff_ring)
        assert isinstance(kq, PathAlgebra)
        assert isinstance(kq, Ring)
        assert isinstance(kq, Algebra)

        e0 = kq.vertex_idempotent(0)
        e1 = kq.vertex_idempotent(1)
        e2 = kq.vertex_idempotent(2)
        a0 = kq.arrow('e0')
        a1 = kq.arrow('e1')
        a01 = kq.path_element(('e0', 'e1'))

        # Orthogonal idempotents summing to 1
        assert kq.add(kq.add(e0, e1), e2) == kq.one
        assert kq.mul(e0, e0) == e0
        assert kq.mul(e0, e1) == kq.zero
        assert kq.mul(a0, a1) == a01
        assert kq.mul(a1, a0) == kq.zero  # non-commutative!

        # Verify full Ring & Algebra axioms via algebrax.verification
        r_samples = [Fraction(0), Fraction(1), Fraction(-2), Fraction(3, 2)]
        a_samples = [kq.zero, kq.one, e0, a0, a1, a01, kq.add(e0, a0)]
        assert all(verify_ring_laws(kq, a_samples).values())
        assert all(verify_algebra_laws(kq, coeff_ring, r_samples, a_samples).values())

    def test_path_algebra_truncation_on_cyclic_quiver(self) -> None:
        q = cycle_quiver(2)
        kq = path_algebra(q, max_path_length=2)
        a0 = kq.arrow('e0')
        a1 = kq.arrow('e1')
        p01 = kq.mul(a0, a1)
        assert p01 == {(0, ('e0', 'e1')): 1.0}
        # Length 3 path truncated to 0
        assert kq.mul(p01, a0) == kq.zero
        assert len(kq.basis()) == 6  # 2 len-0 + 2 len-1 + 2 len-2

    def test_path_algebra_evaluate_in_rep_right_module_homomorphism(self) -> None:
        q = dynkin_quiver('A', 3)
        rep = QuiverRepresentation(
            quiver=q,
            dimensions={0: 2, 1: 2, 2: 1},
            edge_maps={
                'e0': {0: {0: 1.0, 1: 2.0}, 1: {1: -1.0}},
                'e1': {0: {0: 3.0, 1: 4.0}},
            },
        )
        kq = path_algebra(q)
        x = kq.add(kq.smul(2.0, kq.arrow('e0')), kq.vertex_idempotent(0))
        y = kq.add(kq.arrow('e1'), kq.smul(-1.0, kq.vertex_idempotent(1)))

        # Right-module action: Phi(x * y) == Phi(y) @ Phi(x)
        lhs = kq.evaluate_in_rep(kq.mul(x, y), rep)
        rhs = dot(kq.evaluate_in_rep(y, rep), kq.evaluate_in_rep(x, rep))
        assert lhs == rhs

        # Identity evaluates to full 5x5 identity matrix
        phi_one = kq.evaluate_in_rep(kq.one, rep)
        assert phi_one == {i: {i: 1.0} for i in range(5)}


# =============================================================================
# 4. CellularSheaf <-> QuiverRepresentation Equivalence
# =============================================================================


class TestCellularSheafBridge:
    """Verify structural equivalence between QuiverRepresentation and CellularSheaf."""

    def test_round_trip_direct_mode_and_global_sections(self) -> None:
        q = dynkin_quiver('A', 3)
        m0 = {0: {0: 2.0}, 1: {0: -1.0}}  # R^1 -> R^2
        m1 = {0: {0: 1.0, 1: 3.0}}  # R^2 -> R^1
        rep = QuiverRepresentation(quiver=q, dimensions={0: 1, 1: 2, 2: 1}, edge_maps={'e0': m0, 'e1': m1})

        sheaf = to_cellular_sheaf(rep)
        assert isinstance(sheaf, CellularSheaf)
        # Global section x0 = [1], x1 = M0 x0 = [2, -1], x2 = M1 x1 = [-1] has zero Dirichlet energy
        section = {(0, 0): 1.0, (1, 0): 2.0, (1, 1): -1.0, (2, 0): -1.0}
        assert sheaf.dirichlet_energy(section) < 1e-12
        assert sheaf.global_sections_dimension() == 1

        # Round-trip back to QuiverRepresentation in direct mode
        recovered = from_cellular_sheaf(sheaf, mode='direct')
        assert recovered.dimensions == rep.dimensions
        assert recovered.edge_maps[(0, 1)] == m0
        assert recovered.edge_maps[(1, 2)] == m1

    def test_general_cellular_sheaf_incidence_quiver_conversion(self) -> None:
        sheaf: CellularSheaf[str] = CellularSheaf()
        sheaf.add_vertex('u', 2)
        sheaf.add_vertex('v', 2)
        sheaf.add_edge('u', 'v', dim=1, rho_u=[[1.0, -1.0]], rho_v=[[2.0, 0.5]])

        with pytest.raises(ValueError, match='direct mode'):
            from_cellular_sheaf(sheaf, mode='direct')

        q_rep = from_cellular_sheaf(sheaf, mode='auto')
        assert q_rep.quiver.num_vertices == 3  # ('v', 'u'), ('v', 'v'), ('e', ('u', 'v'))
        assert q_rep.quiver.num_edges == 2
        assert q_rep.dimensions[('e', ('u', 'v'))] == 1

    def test_to_cellular_sheaf_rejects_loops_parallel_edges_and_zero_stalks(self) -> None:
        with pytest.raises(ValueError, match='positive stalk'):
            to_cellular_sheaf(simple_representation(dynkin_quiver('A', 2), 0))
        with pytest.raises(ValueError, match='self-loop'):
            to_cellular_sheaf(QuiverRepresentation(cycle_quiver(1), {0: 1}, {'e0': {0: {0: 1.0}}}))
        with pytest.raises(ValueError, match='parallel'):
            to_cellular_sheaf(
                QuiverRepresentation(kronecker_quiver(2), {0: 1, 1: 1}, {'a0': {0: {0: 1.0}}, 'a1': {0: {0: 2.0}}})
            )


# =============================================================================
# 5. Popper Falsification Tests
# =============================================================================


class TestQuiverFalsification:
    """Verify every quiver verifier rejects broken morphisms, direct sums, and non-ADE quivers."""

    def test_broken_morphism_rejected(self) -> None:
        q = dynkin_quiver('A', 2)
        rep1 = QuiverRepresentation(q, {0: 1, 1: 1}, {'e0': {0: {0: 2.0}}})
        rep2 = QuiverRepresentation(q, {0: 1, 1: 1}, {'e0': {0: {0: 5.0}}})
        # f1 @ M0 = 1*2 = 2 != 5*1 = N0 @ f0
        bad_mor = {0: {0: {0: 1.0}}, 1: {0: {0: 1.0}}}
        res = verify_quiver_morphism_commutation(rep1, rep2, bad_mor)
        assert res['same_quiver']
        assert res['vertex_coverage']
        assert res['dimension_compatibility']
        assert not res['edge_commutation']

    def test_broken_direct_sum_rejected(self) -> None:
        q = dynkin_quiver('A', 2)
        rep1 = interval_representation(q, (0, 1))
        rep2 = interval_representation(q, (0, 1))
        # Corrupt off-diagonal coupling so blocks do not split
        corrupted = QuiverRepresentation(
            q,
            {0: 2, 1: 2},
            {'e0': {0: {0: 1.0, 1: 1.0}, 1: {1: 1.0}}},
        )
        res = verify_quiver_direct_sum(rep1, rep2, corrupted)
        assert res['dimension_additivity']
        assert not res['inclusion_2_morphism']
        assert not res['projection_1_morphism']

    def test_non_ade_fails_tits_positive_definiteness(self) -> None:
        for non_ade in (kronecker_quiver(2), kronecker_quiver(3), cycle_quiver(4)):
            res = verify_tits_positive_definiteness(non_ade)
            assert not res['positive_definite']
            assert not res['samples_positive']
            assert not res['ade_classification']
            assert not res['roots_unit_tits']
