"""Unit, integration, and Popper falsification tests for invariant theory, Molien series,
polynomial Reynolds operators, and cubic Lie Casimir invariants.
"""

from __future__ import annotations

import math

import pytest

import algebrax.lie as lie_pkg
import algebrax.rep as rep_pkg
from algebrax.group import (
    FiniteGroup,
    cyclic_group,
    dihedral_group,
    quaternion_group,
    symmetric_group,
)
from algebrax.lie.classical import se_n, sl_n, so_n, sp_n, su_n
from algebrax.matrix.core import dot, subtract
from algebrax.matrix.decompose import inv
from algebrax.rep.canonical import (
    cyclic_rep,
    dihedral_rep,
    quaternion_rep,
    symmetric_defining_rep,
    symmetric_standard_rep,
)
from algebrax.rep.group import ExplicitGroupRep
from algebrax.rep.invariant import (
    MolienSeries,
    compute_molien_series,
    evaluate_sparse_polynomial,
    invariant_basis_at_degree,
    reynolds_monomial_projection,
    reynolds_polynomial_operator,
)
from algebrax.rep.lie import (
    adjoint_representation,
    cubic_casimir_operator,
    cubic_casimir_tensor,
    defining_representation,
    quadratic_casimir,
)
from algebrax.verification import (
    verify_cubic_casimir_invariance,
    verify_molien_expansion,
    verify_polynomial_invariance,
    verify_reynolds_idempotency,
)


def _make_c4_real_2d_rep() -> tuple[FiniteGroup[int], ExplicitGroupRep[float, int]]:
    group = cyclic_group(4)
    mats = {}
    for k in range(4):
        angle = 2.0 * math.pi * k / 4.0
        c = round(math.cos(angle), 12)
        s = round(math.sin(angle), 12)
        row0 = {}
        row1 = {}
        if c != 0.0:
            row0[0] = c
            row1[1] = c
        if s != 0.0:
            row0[1] = -s
            row1[0] = s
        mats[k] = {0: row0, 1: row1}
    return group, ExplicitGroupRep(mats, dimension=2)


def _make_icosahedral_a5_3d_rep() -> tuple[list[int], ExplicitGroupRep[float, int]]:
    """Generate the 60-element chiral icosahedral rotation group A_5 subset SO(3)."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    # Unit axis u = (1/(2*phi), phi/2, 1/2); 180-degree rotation R_u = 2 u u^T - I in SO(3)
    u = (1.0 / (2.0 * phi), phi / 2.0, 0.5)
    r_u = tuple(
        tuple(2.0 * u[i] * u[j] - (1.0 if i == j else 0.0) for j in range(3))
        for i in range(3)
    )
    g2 = (
        (-1.0, 0.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    g3 = (
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0),
    )

    def mat_mul(
        a: tuple[tuple[float, ...], ...],
        b: tuple[tuple[float, ...], ...],
    ) -> tuple[tuple[float, ...], ...]:
        return tuple(
            tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
            for i in range(3)
        )

    def key_of(m: tuple[tuple[float, ...], ...]) -> tuple[int, ...]:
        return tuple(round(m[i][j] * 1e6) for i in range(3) for j in range(3))

    ident = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    seen: dict[tuple[int, ...], tuple[tuple[float, ...], ...]] = {key_of(ident): ident}
    queue = [ident]
    while queue:
        cur = queue.pop()
        for gen in (r_u, g2, g3):
            nxt = mat_mul(cur, gen)
            k = key_of(nxt)
            if k not in seen:
                seen[k] = nxt
                queue.append(nxt)

    mats_list = list(seen.values())
    sparse_map: dict[int, dict[int, dict[int, float]]] = {}
    for idx, m in enumerate(mats_list):
        s_mat: dict[int, dict[int, float]] = {}
        for i in range(3):
            row = {j: m[i][j] for j in range(3) if abs(m[i][j]) > 1e-12}
            if row:
                s_mat[i] = row
        sparse_map[idx] = s_mat

    return list(range(len(mats_list))), ExplicitGroupRep(sparse_map, dimension=3)


def _sparse_is_zero(mat: dict[int, dict[int, float | complex]], tol: float = 1e-9) -> bool:
    return all(abs(complex(v)) <= tol for row in mat.values() for v in row.values())


def _sparse_commutator(
    a: dict[int, dict[int, float | complex]],
    b: dict[int, dict[int, float | complex]],
) -> dict[int, dict[int, float | complex]]:
    return subtract(dot(a, b), dot(b, a))


# =============================================================================
# 1. MolienSeries Data Model & Exact Expansion
# =============================================================================


class TestMolienSeries:
    def test_manual_series_expansion_and_evaluation(self) -> None:
        # 1 / ((1 - t^2)(1 - t^3))
        m = MolienSeries(numerator_coeffs=(1,), denominator_factors=(2, 3))
        assert m.series(10) == [1, 0, 1, 1, 1, 1, 2, 1, 2, 2, 2]
        assert m.coefficient(6) == 2
        assert m.coefficient(0) == 1
        assert m.denominator_coeffs() == (1, 0, -1, -1, 0, 1)
        t = 0.5
        expected_val = 1.0 / ((1.0 - t**2) * (1.0 - t**3))
        assert math.isclose(m.evaluate(t), expected_val, rel_tol=1e-12, abs_tol=1e-12)

    def test_molien_series_validation_errors(self) -> None:
        with pytest.raises(ValueError, match='numerator_coeffs'):
            MolienSeries(numerator_coeffs=(), denominator_factors=(2,))
        with pytest.raises(ValueError, match='positive'):
            MolienSeries(numerator_coeffs=(1,), denominator_factors=(2, 0))
        m = MolienSeries(numerator_coeffs=(1,), denominator_factors=(2,))
        with pytest.raises(ValueError, match='non-negative'):
            m.series(-1)
        with pytest.raises(ZeroDivisionError, match='pole'):
            m.evaluate(1.0)


# =============================================================================
# 2. Molien's Theorem Benchmarks
# =============================================================================


class TestComputeMolienSeries:
    def test_klein_four_group_v4_on_r2(self) -> None:
        # D_4 = V_4 = {+-I, +-diag(1,-1)} on R^2 -> 1 / (1 - t^2)^2
        group = dihedral_group(2)
        rep = dihedral_rep(2)
        m = compute_molien_series(rep, group)
        assert m.numerator_coeffs == (1,)
        assert m.denominator_factors == (2, 2)
        assert m.series(8) == [1, 0, 2, 0, 3, 0, 4, 0, 5]

    def test_c4_real_2d_rotation_rep(self) -> None:
        # C_4 on R^2 -> (1 + t^4) / ((1 - t^2)(1 - t^4))
        group, rep = _make_c4_real_2d_rep()
        m = compute_molien_series(rep, group)
        assert m.series(10) == [1, 0, 1, 0, 3, 0, 3, 0, 5, 0, 5]
        t = 0.4
        expected = (1.0 + t**4) / ((1.0 - t**2) * (1.0 - t**4))
        assert math.isclose(m.evaluate(t), expected, rel_tol=1e-12)

    @pytest.mark.parametrize('n', [3, 5])
    def test_cyclic_complex_1d_rep(self, n: int) -> None:
        group = cyclic_group(n)
        rep = cyclic_rep(n, k=1)
        m = compute_molien_series(rep, group)
        assert m.numerator_coeffs == (1,)
        assert m.denominator_factors == (n,)
        expected = [1 if d % n == 0 else 0 for d in range(2 * n + 1)]
        assert m.series(2 * n) == expected

    def test_dihedral_d8_on_r2(self) -> None:
        # D_8 reflection group -> polynomial ring 1 / ((1 - t^2)(1 - t^4))
        group = dihedral_group(4)
        rep = dihedral_rep(4)
        m = compute_molien_series(rep, group)
        assert m.numerator_coeffs == (1,)
        assert m.denominator_factors == (2, 4)
        assert m.series(8) == [1, 0, 1, 0, 2, 0, 2, 0, 3]

    def test_symmetric_s3_defining_and_standard(self) -> None:
        group = symmetric_group(3)
        rep_def = symmetric_defining_rep(3)
        m_def = compute_molien_series(rep_def, group)
        assert m_def.numerator_coeffs == (1,)
        assert m_def.denominator_factors == (1, 2, 3)
        assert m_def.series(6) == [1, 1, 2, 3, 4, 5, 7]

        rep_std = symmetric_standard_rep(3)
        m_std = compute_molien_series(rep_std, group)
        assert m_std.numerator_coeffs == (1,)
        assert m_std.denominator_factors == (2, 3)
        assert m_std.series(6) == [1, 0, 1, 1, 1, 1, 2]

    def test_quaternion_q8_kleinian_d4_singularity(self) -> None:
        # Q_8 subset SU(2) -> (1 + t^6) / (1 - t^4)^2
        group = quaternion_group()
        rep = quaternion_rep()
        m = compute_molien_series(rep, group)
        assert m.numerator_coeffs == (1, 0, 0, 0, 0, 0, 1)
        assert m.denominator_factors == (4, 4)
        assert m.series(12) == [1, 0, 0, 0, 2, 0, 1, 0, 3, 0, 2, 0, 4]

    def test_icosahedral_a5_3d_rotation_group(self) -> None:
        # A_5 subset SO(3), order 60 -> (1 + t^15) / ((1 - t^2)(1 - t^6)(1 - t^10))
        elements, rep = _make_icosahedral_a5_3d_rep()
        assert len(elements) == 60
        m = compute_molien_series(rep, elements)
        assert m.denominator_factors == (2, 6, 10)
        expected_num = (1,) + (0,) * 14 + (1,)
        assert m.numerator_coeffs == expected_num
        assert m.series(16) == [1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 3, 0, 4, 0, 4, 1, 5]

    def test_similarity_conjugation_invariance_non_orthogonal(self) -> None:
        # Non-orthogonal change of basis S * rho(g) * S^{-1} must yield identical Molien series
        group = dihedral_group(4)
        base_rep = dihedral_rep(4)
        s_mat = {0: {0: 2.0, 1: 1.0}, 1: {0: 0.5, 1: 1.5}}
        s_inv = inv(s_mat)
        conj_mats = {g: dot(dot(s_mat, base_rep(g)), s_inv) for g in group.elements}
        conj_rep = ExplicitGroupRep(conj_mats, dimension=2)

        m_base = compute_molien_series(base_rep, group)
        m_conj = compute_molien_series(conj_rep, group)
        assert m_conj == m_base

    def test_compute_molien_series_errors(self) -> None:
        rep = dihedral_rep(4)
        with pytest.raises(ValueError, match='non-empty'):
            compute_molien_series(rep, [])
        # Incomplete non-group subset produces non-integer Taylor coefficient
        with pytest.raises(ValueError, match='Non-integer Molien coefficient'):
            compute_molien_series(rep, ['r0', 'r1', 'r2'])


# =============================================================================
# 3. Reynolds Polynomial Symmetrization & Homogeneous Invariant Bases
# =============================================================================


class TestReynoldsAndInvariantBases:
    @pytest.mark.parametrize(
        ('name', 'max_deg'),
        [
            ('V4', 6),
            ('C4_2D', 6),
            ('D8', 6),
            ('S3_def', 5),
            ('S3_std', 6),
            ('Q8', 8),
        ],
    )
    def test_basis_dimensions_match_molien_and_invariance(self, name: str, max_deg: int) -> None:
        if name == 'V4':
            group: FiniteGroup[object] = dihedral_group(2)  # type: ignore[assignment]
            rep = dihedral_rep(2)
        elif name == 'C4_2D':
            group, rep = _make_c4_real_2d_rep()  # type: ignore[assignment]
        elif name == 'D8':
            group = dihedral_group(4)  # type: ignore[assignment]
            rep = dihedral_rep(4)
        elif name == 'S3_def':
            group = symmetric_group(3)  # type: ignore[assignment]
            rep = symmetric_defining_rep(3)
        elif name == 'S3_std':
            group = symmetric_group(3)  # type: ignore[assignment]
            rep = symmetric_standard_rep(3)
        else:
            group = quaternion_group()  # type: ignore[assignment]
            rep = quaternion_rep()

        molien = compute_molien_series(rep, group)
        actual_dims: list[int] = []
        for deg in range(max_deg + 1):
            basis = invariant_basis_at_degree(rep, group, deg)
            actual_dims.append(len(basis))
            for poly in basis:
                ver = verify_polynomial_invariance(poly, rep, group, num_probes=20, seed=7 + deg)
                assert all(ver.values()), f'{name} degree {deg} basis failed invariance: {ver}'

        mol_ver = verify_molien_expansion(molien, actual_dims)
        assert all(mol_ver.values()), f'{name} Molien mismatch: {actual_dims} vs {molien.series(max_deg)}'

    def test_reynolds_polynomial_operator_idempotency_and_non_orthogonal_rep(self) -> None:
        group = dihedral_group(4)
        base_rep = dihedral_rep(4)
        # Non-orthogonal basis change S * rho(g) * S^{-1}
        s_mat = {0: {0: 2.0, 1: 0.7}, 1: {0: -0.4, 1: 1.3}}
        s_inv = inv(s_mat)
        conj_rep = ExplicitGroupRep(
            {g: dot(dot(s_mat, base_rep(g)), s_inv) for g in group.elements},
            dimension=2,
        )

        def raw_poly(x: list[float]) -> float:
            return x[0] ** 4 + 2.0 * x[0] ** 3 * x[1] - x[0] * x[1] ** 2 + 3.0 * x[1] ** 2

        inv_poly = reynolds_polynomial_operator(raw_poly, conj_rep, group)
        idem = verify_reynolds_idempotency(
            lambda f: reynolds_polynomial_operator(f, conj_rep, group),
            raw_poly,
            [1.3, -0.7],
        )
        assert all(idem.values())

        inv_check = verify_polynomial_invariance(inv_poly, conj_rep, group, num_probes=30, seed=99)
        assert all(inv_check.values())

        # Also test with raw element sequence (no FiniteGroup wrapper)
        inv_poly_seq = reynolds_polynomial_operator(raw_poly, conj_rep, list(group.elements))
        inv_check_seq = verify_polynomial_invariance(
            inv_poly_seq, conj_rep, list(group.elements), num_probes=25, seed=101
        )
        assert all(inv_check_seq.values())

    def test_reynolds_monomial_projection_exact_polynomials(self) -> None:
        group_s3 = symmetric_group(3)
        rep_s3 = symmetric_defining_rep(3)
        proj_lin = reynolds_monomial_projection((1, 0, 0), rep_s3, group_s3)
        assert len(proj_lin) == 3
        for exp in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            assert math.isclose(float(proj_lin[exp].real), 1.0 / 3.0, rel_tol=1e-12)
        assert math.isclose(float(evaluate_sparse_polynomial(proj_lin, [1.0, 2.0, 6.0]).real), 3.0, rel_tol=1e-12)

        # Odd-degree monomial under V_4 vanishes identically
        group_v4 = dihedral_group(2)
        rep_v4 = dihedral_rep(2)
        assert reynolds_monomial_projection((2, 1), rep_v4, group_v4) == {}

    def test_reynolds_and_basis_validation_errors(self) -> None:
        group = dihedral_group(2)
        rep = dihedral_rep(2)
        with pytest.raises(ValueError, match='length 2'):
            reynolds_monomial_projection((1, 0, 0), rep, group)
        with pytest.raises(ValueError, match='non-negative'):
            reynolds_monomial_projection((-1, 2), rep, group)
        with pytest.raises(ValueError, match='non-negative'):
            invariant_basis_at_degree(rep, group, -1)


# =============================================================================
# 4. Higher-Order Lie Casimir Invariants (Cubic Casimir C_3 & d_{ijk})
# =============================================================================


class TestCubicCasimirInvariants:
    @pytest.mark.parametrize('factory', [sl_n, su_n])
    def test_rank_two_a2_cubic_casimir_separates_fundamental_and_dual(self, factory: object) -> None:
        alg = factory(3)  # type: ignore[operator]
        d_tensor = cubic_casimir_tensor(alg)
        assert len(d_tensor) > 0

        ver = verify_cubic_casimir_invariance(alg, d_tensor=d_tensor)
        assert ver['total_symmetry']
        assert ver['ad_invariance']

        fund = defining_representation(alg)
        dual = fund.dual()
        adj = adjoint_representation(alg)

        # Quadratic Casimir gives IDENTICAL scalar eigenvalues on 3 and 3-bar
        c2_fund = quadratic_casimir(fund)
        c2_dual = quadratic_casimir(dual)
        lam2_fund = complex(c2_fund[0][0])
        lam2_dual = complex(c2_dual[0][0])
        assert abs(lam2_fund - lam2_dual) <= 1e-9

        # Cubic Casimir gives OPPOSITE non-zero scalar eigenvalues (+lam3 vs -lam3) on 3 vs 3-bar!
        c3_fund = cubic_casimir_operator(fund, d_tensor=d_tensor)
        c3_dual = cubic_casimir_operator(dual, d_tensor=d_tensor)
        c3_adj = cubic_casimir_operator(adj, d_tensor=d_tensor)

        # Commutativity [C_3, rho(X_a)] = 0 on fundamental and dual
        for a in range(alg.dim):
            assert _sparse_is_zero(_sparse_commutator(c3_fund, fund.generator_matrix(a)), tol=1e-9)
            assert _sparse_is_zero(_sparse_commutator(c3_dual, dual.generator_matrix(a)), tol=1e-9)

        # Scalar multiple of identity by Schur's lemma
        lam3_fund = complex(c3_fund[0][0])
        lam3_dual = complex(c3_dual[0][0])
        assert abs(lam3_fund) > 1e-6
        for i in range(3):
            assert abs(complex(c3_fund[i][i]) - lam3_fund) <= 1e-9
            assert abs(complex(c3_dual[i][i]) - lam3_dual) <= 1e-9
        assert abs(lam3_fund + lam3_dual) <= 1e-9

        # Self-dual adjoint representation 8 has identically zero cubic Casimir!
        assert _sparse_is_zero(c3_adj, tol=1e-9)
        assert cubic_casimir_tensor(alg, rep=adj) == {}

    def test_self_dual_rank_one_algebras_have_zero_cubic_casimir(self) -> None:
        for alg in (su_n(2), so_n(3), sp_n(1)):
            d_tensor = cubic_casimir_tensor(alg)
            assert d_tensor == {}
            fund = defining_representation(alg)
            assert cubic_casimir_operator(fund) == {}
            ver = verify_cubic_casimir_invariance(alg, d_tensor=d_tensor)
            assert ver['total_symmetry']
            assert ver['ad_invariance']

    def test_non_semisimple_algebra_raises_in_cubic_casimir_operator(self) -> None:
        alg = se_n(3)
        rep = adjoint_representation(alg)
        with pytest.raises(ValueError, match='semisimple'):
            cubic_casimir_operator(rep, algebra=alg)

    def test_public_and_lazy_package_reexports(self) -> None:
        assert rep_pkg.MolienSeries is MolienSeries
        assert rep_pkg.compute_molien_series is compute_molien_series
        assert rep_pkg.reynolds_polynomial_operator is reynolds_polynomial_operator
        assert rep_pkg.cubic_casimir_tensor is cubic_casimir_tensor
        assert rep_pkg.cubic_casimir_operator is cubic_casimir_operator
        assert lie_pkg.cubic_casimir_tensor is cubic_casimir_tensor
        assert lie_pkg.cubic_casimir_operator is cubic_casimir_operator


# =============================================================================
# 5. Popper Falsification Tests
# =============================================================================


class TestPopperFalsification:
    def test_non_invariant_polynomial_fails_verification(self) -> None:
        group = dihedral_group(4)
        rep = dihedral_rep(4)
        res = verify_polynomial_invariance(lambda x: x[0], rep, group, num_probes=20, seed=42)
        assert not res['polynomial_invariance']
        assert not res['probe_coverage']

    def test_non_idempotent_operator_fails_reynolds_idempotency(self) -> None:
        res = verify_reynolds_idempotency(
            lambda f: (lambda x: 2.0 * f(x)),
            lambda x: x[0] ** 2 + 1.0,
            [1.5, -0.5],
        )
        assert res['finite_values']
        assert not res['reynolds_idempotency']

    def test_wrong_dimensions_fail_molien_expansion(self) -> None:
        m = MolienSeries(numerator_coeffs=(1,), denominator_factors=(2, 2))
        res = verify_molien_expansion(m, [1, 0, 99, 0, 3])
        assert not res['expansion_matches']
        assert res['degree_zero_unit']

    def test_corrupted_cubic_tensor_fails_symmetry_and_ad_invariance(self) -> None:
        alg = sl_n(3)
        d_tensor = dict(cubic_casimir_tensor(alg))
        # Break permutation symmetry on a non-diagonal entry
        asym_key = next(k for k in d_tensor if len(set(k)) > 1)
        broken_sym = dict(d_tensor)
        broken_sym[asym_key] = complex(broken_sym[asym_key]) + 1.0
        res_sym = verify_cubic_casimir_invariance(alg, d_tensor=broken_sym)
        assert not res_sym['total_symmetry']
        assert not res_sym['ad_invariance']

        # Symmetric tensor that is NOT ad-invariant: d_{0,0,0} = 1
        non_inv = {(0, 0, 0): 1.0}
        res_ad = verify_cubic_casimir_invariance(alg, d_tensor=non_inv)
        assert res_ad['total_symmetry']
        assert not res_ad['ad_invariance']
