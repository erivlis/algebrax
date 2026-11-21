"""Comprehensive tests for Lie algebra representations, weight spaces, Casimir operators,
Freudenthal eigenvalues, matrix-exponential bridge, and sparse Clebsch-Gordan coupling tensors.
"""

from __future__ import annotations

import math

import pytest

from algebrax import lie, rep, tensor
from algebrax.algebra._homomorphisms import LieAlgebraHom
from algebrax.lie import (
    RootSystem,
    chevalley_lie_algebra,
    g2,
    se_n,
    sl_n,
    so_n,
    sp_n,
    su_n,
)
from algebrax.matrix.core import dot, transpose
from algebrax.rep.lie import (
    ExplicitLieRep,
    LieRepresentation,
    adjoint_representation,
    clebsch_gordan_coefficient,
    clebsch_gordan_matrix,
    clebsch_gordan_tensor,
    defining_representation,
    direct_sum_lie_rep,
    freudenthal_casimir_eigenvalue,
    highest_weight_vectors,
    is_lie_intertwiner,
    quadratic_casimir,
    spin_representation,
    tensor_product_lie_rep,
    trivial_lie_rep,
    weight_space_decomposition,
)
from algebrax.verification import (
    verify_casimir_commutativity,
    verify_clebsch_gordan_coupling,
    verify_lie_representation_homomorphism,
)


def _mat_allclose(
    a: dict[int, dict[int, complex | float]],
    b: dict[int, dict[int, complex | float]],
    tol: float = 1e-9,
) -> bool:
    rows = set(a.keys()) | set(b.keys())
    for r in rows:
        ra = a.get(r, {})
        rb = b.get(r, {})
        for c in set(ra.keys()) | set(rb.keys()):
            if abs(complex(ra.get(c, 0.0)) - complex(rb.get(c, 0.0))) > tol:
                return False
    return True


def _mat_conj_transpose(a: dict[int, dict[int, complex | float]]) -> dict[int, dict[int, complex]]:
    out: dict[int, dict[int, complex]] = {}
    for r, row in a.items():
        for c, val in row.items():
            out.setdefault(c, {})[r] = complex(val).conjugate()
    return out


class TestProtocolsAndExports:
    """Verify LieRepresentation / LieAlgebraHom protocols and package re-exports."""

    def test_explicit_lie_rep_protocols(self) -> None:
        spin_half = spin_representation(1, form='su2')
        assert isinstance(spin_half, LieRepresentation)
        assert isinstance(spin_half, LieAlgebraHom)
        assert spin_half.dimension == 2
        assert spin_half.algebra.dim == 3

    def test_lazy_lie_package_reexports(self) -> None:
        assert lie.adjoint_representation is adjoint_representation
        assert lie.defining_representation is defining_representation
        assert lie.quadratic_casimir is quadratic_casimir
        assert lie.spin_representation is spin_representation

    def test_rep_and_tensor_package_reexports(self) -> None:
        assert rep.ExplicitLieRep is ExplicitLieRep
        assert rep.spin_representation is spin_representation
        assert rep.quadratic_casimir is quadratic_casimir
        assert rep.clebsch_gordan_tensor is clebsch_gordan_tensor
        assert tensor.clebsch_gordan_coefficient is clebsch_gordan_coefficient
        assert tensor.clebsch_gordan_tensor is clebsch_gordan_tensor
        assert tensor.clebsch_gordan_matrix is clebsch_gordan_matrix
        assert hasattr(tensor, 'einsum')
        assert hasattr(tensor, 'outer_product')

    def test_explicit_lie_rep_validation(self) -> None:
        alg = su_n(2)
        with pytest.raises(ValueError, match='dimension'):
            ExplicitLieRep(algebra=alg, generator_matrices=({}, {}, {}), dimension=0)
        with pytest.raises(ValueError, match='Expected 3'):
            ExplicitLieRep(algebra=alg, generator_matrices=({}, {}), dimension=2)
        rep_su2 = spin_representation(1, form='su2')
        with pytest.raises(IndexError):
            rep_su2(3)
        with pytest.raises(IndexError):
            rep_su2(-1)


class TestSpinAndStandardRepresentations:
    """Verify spin_representation, adjoint, defining, and trivial representations."""

    @pytest.mark.parametrize('j_halves', [0, 1, 2, 3, 4])
    @pytest.mark.parametrize('form', ['su2', 'sl2'])
    def test_spin_representation_homomorphism(self, j_halves: int, form: str) -> None:
        rep_j = spin_representation(j_halves, form=form)  # type: ignore[arg-type]
        assert rep_j.dimension == j_halves + 1
        res = verify_lie_representation_homomorphism(rep_j)
        assert res['bracket_preservation']
        assert res['antisymmetry']
        assert res['jacobi_identity']

    def test_spin_half_matches_classical_defining_bases(self) -> None:
        su2_alg = su_n(2)
        sl2_alg = sl_n(2)
        spin_su2 = spin_representation(1, form='su2')
        def_su2 = defining_representation(su2_alg)
        spin_sl2 = spin_representation(1, form='sl2')
        def_sl2 = defining_representation(sl2_alg)

        for idx in range(3):
            assert _mat_allclose(spin_su2(idx), def_su2(idx))
            assert _mat_allclose(spin_sl2(idx), def_sl2(idx))

    def test_spin_representation_invalid_inputs(self) -> None:
        with pytest.raises(ValueError, match='j_halves'):
            spin_representation(-1)
        with pytest.raises(ValueError, match='j_halves'):
            spin_representation(True)
        with pytest.raises(ValueError, match='form'):
            spin_representation(1, form='so3')  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        'alg_factory',
        [
            lambda: so_n(3),
            lambda: su_n(2),
            lambda: su_n(3),
            lambda: sl_n(3),
            lambda: sp_n(1),
            lambda: se_n(3),
            lambda: chevalley_lie_algebra(RootSystem.from_dynkin('A', 2)),
            g2,
        ],
    )
    def test_adjoint_representation_laws(self, alg_factory: object) -> None:
        alg = alg_factory()  # type: ignore[operator]
        ad_rep = adjoint_representation(alg)
        assert ad_rep.dimension == alg.dim
        res = verify_lie_representation_homomorphism(ad_rep)
        assert res['bracket_preservation']
        assert res['antisymmetry']
        assert res['jacobi_identity']

    @pytest.mark.parametrize(
        ('alg_factory', 'expected_dim'),
        [
            (lambda: su_n(2), 2),
            (lambda: su_n(3), 3),
            (lambda: sl_n(3), 3),
            (lambda: so_n(3), 3),
            (lambda: sp_n(1), 2),
            (lambda: se_n(3), 4),
        ],
    )
    def test_defining_representation_laws(self, alg_factory: object, expected_dim: int) -> None:
        alg = alg_factory()  # type: ignore[operator]
        def_rep = defining_representation(alg)
        assert def_rep.dimension == expected_dim
        res = verify_lie_representation_homomorphism(def_rep)
        assert res['bracket_preservation']
        assert res['antisymmetry']
        assert res['jacobi_identity']

    def test_defining_representation_g2_fundamental_casimir(self) -> None:
        g2_alg = g2()
        def_g2 = defining_representation(g2_alg)
        assert def_g2.dimension == 7
        assert all(verify_lie_representation_homomorphism(def_g2).values())
        rs_g2 = RootSystem.from_dynkin('G', 2)
        lam_7 = freudenthal_casimir_eigenvalue(rs_g2, [1, 0])
        assert math.isclose(lam_7, 0.5, rel_tol=1e-12)
        res = verify_casimir_commutativity(def_g2, expected_eigenvalue=lam_7)
        assert res['casimir_commutes']
        assert res['eigenvalue_matches']

    def test_defining_representation_requires_matrix_basis(self) -> None:
        from algebrax.lie import LieAlgebra

        abstract_alg = LieAlgebra(
            dim=3,
            structure_constants=su_n(2).structure_constants,
        )
        with pytest.raises(ValueError, match='matrix_basis'):
            defining_representation(abstract_alg)

    def test_trivial_lie_rep(self) -> None:
        triv = trivial_lie_rep(su_n(2), dimension=3)
        assert triv.dimension == 3
        res = verify_lie_representation_homomorphism(triv)
        assert all(res.values())
        for idx in range(3):
            assert triv(idx) == {}


class TestFunctorialConstructionsAndExpMap:
    """Verify direct_sum, tensor_product, dual, intertwiners, and exp_map."""

    def test_direct_sum_and_tensor_product(self) -> None:
        r_half = spin_representation(1, form='su2')
        r_one = spin_representation(2, form='su2')

        r_sum = r_half.direct_sum(r_one)
        assert r_sum.dimension == 5
        assert all(verify_lie_representation_homomorphism(r_sum).values())

        r_tensor = r_half.tensor_product(r_half)
        assert r_tensor.dimension == 4
        assert all(verify_lie_representation_homomorphism(r_tensor).values())

    def test_contragredient_dual_and_intertwiners(self) -> None:
        r_half = spin_representation(1, form='su2')
        r_half_dual = r_half.dual()
        assert all(verify_lie_representation_homomorphism(r_half_dual).values())

        # Spin-1/2 of su(2) is pseudoreal (self-dual via antisymmetric epsilon tensor)
        eps: dict[int, dict[int, float]] = {0: {1: 1.0}, 1: {0: -1.0}}
        assert is_lie_intertwiner(eps, r_half, r_half_dual)

        # Fundamental 3 and antifundamental 3-bar of sl(3) are NOT intertwined by I_3
        def_sl3 = defining_representation(sl_n(3))
        dual_sl3 = def_sl3.dual()
        assert all(verify_lie_representation_homomorphism(dual_sl3).values())
        ident3: dict[int, dict[int, float]] = {0: {0: 1.0}, 1: {1: 1.0}, 2: {2: 1.0}}
        assert not is_lie_intertwiner(ident3, def_sl3, dual_sl3)

    def test_mismatched_algebras_raise(self) -> None:
        r_su2 = spin_representation(1, form='su2')
        r_sl2 = spin_representation(1, form='sl2')
        with pytest.raises(ValueError, match='same LieAlgebra'):
            direct_sum_lie_rep([r_su2, r_sl2])
        with pytest.raises(ValueError, match='same LieAlgebra'):
            tensor_product_lie_rep(r_su2, r_sl2)
        with pytest.raises(ValueError, match='same LieAlgebra'):
            is_lie_intertwiner({}, r_su2, r_sl2)

    def test_exp_map_double_cover_and_unitarity(self) -> None:
        r_half = spin_representation(1, form='su2')
        r_one = spin_representation(2, form='su2')

        # 2*pi rotation around z: T_2 = -i J_z => exp(2*pi * T_2) = -I for spin-1/2, +I for spin-1
        rot_half_2pi = r_half.exp_map({2: 2.0 * math.pi})
        rot_half_4pi = r_half.exp_map({2: 4.0 * math.pi})
        rot_one_2pi = r_one.exp_map({2: 2.0 * math.pi})

        neg_i2: dict[int, dict[int, complex]] = {0: {0: -1.0}, 1: {1: -1.0}}
        pos_i2: dict[int, dict[int, complex]] = {0: {0: 1.0}, 1: {1: 1.0}}
        pos_i3: dict[int, dict[int, complex]] = {0: {0: 1.0}, 1: {1: 1.0}, 2: {2: 1.0}}

        assert _mat_allclose(rot_half_2pi, neg_i2, tol=1e-9)
        assert _mat_allclose(rot_half_4pi, pos_i2, tol=1e-9)
        assert _mat_allclose(rot_one_2pi, pos_i3, tol=1e-9)

        # Unitarity check: U^dagger U = I
        u = r_half.exp_map({0: 0.7, 1: -0.4, 2: 1.1})
        assert _mat_allclose(dot(_mat_conj_transpose(u), u), pos_i2, tol=1e-9)

    def test_exp_map_bch_compatibility(self) -> None:
        alg = su_n(2)
        r_one = spin_representation(2, form='su2')
        x = {0: 0.12, 1: -0.08, 2: 0.05}
        y = {0: -0.07, 1: 0.11, 2: -0.09}

        lhs = dot(r_one.exp_map(x), r_one.exp_map(y))
        z_bch = alg.bch(x, y, order=4)
        rhs = r_one.exp_map(z_bch)
        assert _mat_allclose(lhs, rhs, tol=1e-6)


class TestWeightSpacesAndHighestWeights:
    """Verify weight_space_decomposition and highest_weight_vectors."""

    @pytest.mark.parametrize('j_halves', [1, 2, 3, 4])
    def test_sl2_irreducible_weights_and_highest_weight(self, j_halves: int) -> None:
        rep_j = spin_representation(j_halves, form='sl2')
        weights = weight_space_decomposition(rep_j, cartan_indices=(2,))
        expected_weights = {(float(m_h),) for m_h in range(j_halves, -j_halves - 1, -2)}
        assert set(weights.keys()) == expected_weights
        for basis in weights.values():
            assert len(basis) == 1

        hw = highest_weight_vectors(rep_j, cartan_indices=(2,), raising_indices=(0,))
        assert len(hw) == 1
        assert hw[0][0] == (float(j_halves),)

    def test_sl2_tensor_product_highest_weights(self) -> None:
        # V_{1/2} (x) V_{1/2} = V_1 (+) V_0 => highest weights (2,) and (0,)
        r_half = spin_representation(1, form='sl2')
        t_hh = r_half.tensor_product(r_half)
        weights_hh = weight_space_decomposition(t_hh, cartan_indices=(2,))
        assert len(weights_hh[(2.0,)]) == 1
        assert len(weights_hh[(0.0,)]) == 2
        assert len(weights_hh[(-2.0,)]) == 1

        hw_hh = highest_weight_vectors(t_hh, cartan_indices=(2,), raising_indices=(0,))
        hw_weights_hh = sorted((w[0] for w, _ in hw_hh), reverse=True)
        assert hw_weights_hh == [2.0, 0.0]

        # V_1 (x) V_{1/2} = V_{3/2} (+) V_{1/2} => highest weights (3,) and (1,)
        r_one = spin_representation(2, form='sl2')
        t_oh = r_one.tensor_product(r_half)
        hw_oh = highest_weight_vectors(t_oh, cartan_indices=(2,), raising_indices=(0,))
        assert sorted((w[0] for w, _ in hw_oh), reverse=True) == [3.0, 1.0]

        # V_1 (x) V_1 = V_2 (+) V_1 (+) V_0 => highest weights (4,), (2,), (0,)
        t_oo = r_one.tensor_product(r_one)
        hw_oo = highest_weight_vectors(t_oo, cartan_indices=(2,), raising_indices=(0,))
        assert sorted((w[0] for w, _ in hw_oo), reverse=True) == [4.0, 2.0, 0.0]

    def test_sl3_defining_weights_and_highest_weight(self) -> None:
        # sl_n(3) basis: ['E_{01}', 'E_{02}', 'E_{10}', 'E_{12}', 'E_{20}', 'E_{21}', 'H_0', 'H_1']
        def_sl3 = defining_representation(sl_n(3))
        weights = weight_space_decomposition(def_sl3, cartan_indices=(6, 7))
        assert set(weights.keys()) == {(1.0, 0.0), (-1.0, 1.0), (0.0, -1.0)}

        hw = highest_weight_vectors(def_sl3, cartan_indices=(6, 7), raising_indices=(0, 1, 3))
        assert len(hw) == 1
        assert hw[0][0] == (1.0, 0.0)


class TestCasimirAndFreudenthal:
    """Verify quadratic_casimir, freudenthal_casimir_eigenvalue, and verify_casimir_commutativity."""

    @pytest.mark.parametrize('j_halves', [0, 1, 2, 3, 4])
    @pytest.mark.parametrize('form', ['su2', 'sl2'])
    def test_su2_sl2_casimir_matches_freudenthal(self, j_halves: int, form: str) -> None:
        rep_j = spin_representation(j_halves, form=form)  # type: ignore[arg-type]
        j_val = j_halves / 2.0
        expected_killing = 0.5 * j_val * (j_val + 1.0)

        rs_a1 = RootSystem.from_dynkin('A', 1)
        freud = freudenthal_casimir_eigenvalue(rs_a1, [j_halves])
        assert math.isclose(freud, expected_killing, rel_tol=1e-12, abs_tol=1e-12)

        res = verify_casimir_commutativity(rep_j, expected_eigenvalue=freud)
        assert res['casimir_commutes']
        assert res['eigenvalue_matches']

    def test_physics_j_squared_custom_metric(self) -> None:
        # With g^{ij} = -delta^{ij} on skew-Hermitian su(2) generators T_k = -i J_k,
        # sum_k (-1) T_k^2 = sum_k J_k^2 = j(j+1) I
        phys_metric_inv: dict[int, dict[int, float]] = {0: {0: -1.0}, 1: {1: -1.0}, 2: {2: -1.0}}
        for j_halves in (1, 2, 3):
            j_val = j_halves / 2.0
            rep_j = spin_representation(j_halves, form='su2')
            res = verify_casimir_commutativity(
                rep_j,
                killing_metric_inv=phys_metric_inv,
                expected_eigenvalue=j_val * (j_val + 1.0),
            )
            assert res['casimir_commutes']
            assert res['eigenvalue_matches']

    def test_sl3_fundamental_and_dual_casimir(self) -> None:
        rs_a2 = RootSystem.from_dynkin('A', 2)
        def_sl3 = defining_representation(sl_n(3))
        dual_sl3 = def_sl3.dual()

        lam_fund = freudenthal_casimir_eigenvalue(rs_a2, [1, 0])
        lam_dual = freudenthal_casimir_eigenvalue(rs_a2, [0, 1])
        assert math.isclose(lam_fund, 4.0 / 9.0, rel_tol=1e-12)
        assert math.isclose(lam_dual, 4.0 / 9.0, rel_tol=1e-12)

        res_def = verify_casimir_commutativity(def_sl3, expected_eigenvalue=lam_fund)
        res_dual = verify_casimir_commutativity(dual_sl3, expected_eigenvalue=lam_dual)
        assert all(res_def.values())
        assert all(res_dual.values())

    @pytest.mark.parametrize(
        ('alg_factory', 'dynkin_type', 'rank', 'highest_root_dynkin'),
        [
            (lambda: su_n(2), 'A', 1, [2]),
            (lambda: so_n(3), 'A', 1, [2]),
            (lambda: sl_n(3), 'A', 2, [1, 1]),
            (lambda: su_n(3), 'A', 2, [1, 1]),
            (lambda: sp_n(1), 'A', 1, [2]),
            (g2, 'G', 2, [0, 1]),
        ],
    )
    def test_adjoint_casimir_is_identity_for_simple_algebras(
        self,
        alg_factory: object,
        dynkin_type: str,
        rank: int,
        highest_root_dynkin: list[int],
    ) -> None:
        alg = alg_factory()  # type: ignore[operator]
        ad_rep = adjoint_representation(alg)
        rs = RootSystem.from_dynkin(dynkin_type, rank)
        freud = freudenthal_casimir_eigenvalue(rs, highest_root_dynkin)
        assert math.isclose(freud, 1.0, rel_tol=1e-11, abs_tol=1e-11)

        res = verify_casimir_commutativity(ad_rep, expected_eigenvalue=1.0)
        assert res['casimir_commutes']
        assert res['eigenvalue_matches']


class TestClebschGordanTensors:
    """Verify sparse Clebsch-Gordan coefficients, 3-tensors, and orthogonal coupling matrices."""

    def test_exact_known_coefficients(self) -> None:
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        assert math.isclose(clebsch_gordan_coefficient(1, 1, 1, 1, 2, 2), 1.0, rel_tol=1e-14)
        assert math.isclose(clebsch_gordan_coefficient(1, 1, 1, -1, 2, 0), inv_sqrt2, rel_tol=1e-14)
        assert math.isclose(clebsch_gordan_coefficient(1, -1, 1, 1, 2, 0), inv_sqrt2, rel_tol=1e-14)
        assert math.isclose(clebsch_gordan_coefficient(1, 1, 1, -1, 0, 0), inv_sqrt2, rel_tol=1e-14)
        assert math.isclose(clebsch_gordan_coefficient(1, -1, 1, 1, 0, 0), -inv_sqrt2, rel_tol=1e-14)
        # Spin 1 x 1 -> j=1, m=0 has vanishing <1,0; 1,0 | 1,0> = 0
        assert clebsch_gordan_coefficient(2, 0, 2, 0, 2, 0) == 0.0

    def test_selection_rule_zeros(self) -> None:
        assert clebsch_gordan_coefficient(1, 1, 1, 1, 2, 0) == 0.0  # m != m1 + m2
        assert clebsch_gordan_coefficient(2, 0, 2, 0, 6, 0) == 0.0  # triangle violated
        assert clebsch_gordan_coefficient(1, 1, 1, -1, 1, 0) == 0.0  # parity violated
        assert clebsch_gordan_coefficient(1, 3, 1, -1, 2, 2) == 0.0  # |m1| > j1

    @pytest.mark.parametrize(
        ('j1_halves', 'j2_halves'),
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2), (4, 2)],
    )
    def test_verify_clebsch_gordan_coupling(self, j1_halves: int, j2_halves: int) -> None:
        res = verify_clebsch_gordan_coupling(j1_halves, j2_halves)
        assert res['orthogonality']
        assert res['selection_rules']
        assert res['intertwiner_equivariance']

    def test_cg_matrix_intertwines_sl2_as_well(self) -> None:
        u_mat, _ = clebsch_gordan_matrix(2, 1)
        tensor_rep = spin_representation(2, form='sl2').tensor_product(spin_representation(1, form='sl2'))
        coupled_rep = direct_sum_lie_rep([
            spin_representation(3, form='sl2'),
            spin_representation(1, form='sl2'),
        ])
        assert is_lie_intertwiner(u_mat, coupled_rep, tensor_rep)
        assert is_lie_intertwiner(transpose(u_mat), tensor_rep, coupled_rep)

    def test_cg_tensor_sparsity(self) -> None:
        # 1 x 1 has dense dimension 9 x 9 = 81 entries, but only 18 non-zero CG coefficients
        cg_1_1 = clebsch_gordan_tensor(2, 2)
        assert len(cg_1_1) < 81
        assert len(cg_1_1) == 18


class TestPopperFalsification:
    """Deliberate falsification tests ensuring invalid structures fail cleanly."""

    def test_broken_lie_rep_fails_homomorphism_check(self) -> None:
        alg = su_n(2)
        r_half = spin_representation(1, form='su2')
        # Perturb generator 0 by scaling it by 2.0 (breaks [T0, T1] = T2)
        scaled_t0 = {r: {c: 2.0 * v for c, v in row.items()} for r, row in r_half(0).items()}
        broken = ExplicitLieRep(
            algebra=alg,
            generator_matrices=(scaled_t0, r_half(1), r_half(2)),
            dimension=2,
        )
        res = verify_lie_representation_homomorphism(broken)
        assert not res['bracket_preservation']

    def test_non_semisimple_se3_raises_in_casimir(self) -> None:
        se3 = se_n(3)
        ad_se3 = adjoint_representation(se3)
        with pytest.raises(ValueError, match='singular'):
            quadratic_casimir(ad_se3)

    def test_wrong_expected_casimir_eigenvalue_fails(self) -> None:
        r_one = spin_representation(2, form='su2')
        res = verify_casimir_commutativity(r_one, expected_eigenvalue=99.0)
        assert res['casimir_commutes']
        assert not res['eigenvalue_matches']

    def test_non_diagonal_cartan_raises_in_weight_decomposition(self) -> None:
        r_half = spin_representation(1, form='su2')
        # Generator 0 of su_n(2) is off-diagonal!
        with pytest.raises(ValueError, match='diagonal'):
            weight_space_decomposition(r_half, cartan_indices=(0,))

    def test_freudenthal_validation(self) -> None:
        rs_a2 = RootSystem.from_dynkin('A', 2)
        with pytest.raises(ValueError, match='Dynkin labels'):
            freudenthal_casimir_eigenvalue(rs_a2, [1])
        with pytest.raises(ValueError, match='non-negative'):
            freudenthal_casimir_eigenvalue(rs_a2, [1, -1])
