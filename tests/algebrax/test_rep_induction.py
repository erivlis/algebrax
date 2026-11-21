"""Unit, integration, and falsification tests for induced representations, Frobenius reciprocity, and Mackey theory."""

from __future__ import annotations

import cmath
import math

import pytest

from algebrax.group import (
    FiniteGroup,
    dihedral_group,
    quaternion_group,
    symmetric_group,
)
from algebrax.rep import (
    Character,
    ExplicitGroupRep,
    character_inner_product,
    conjugate_representation,
    dihedral_rep,
    direct_sum_rep,
    frobenius_adjoint_inverse,
    frobenius_adjoint_transpose,
    induced_character,
    induced_representation,
    is_intertwiner,
    mackey_decomposition,
    mackey_intertwining_number,
    quaternion_rep,
    regular_rep,
    restrict_character,
    restrict_representation,
    reynolds_average,
    s3_character_table,
    symmetric_defining_rep,
    symmetric_sign_rep,
    symmetric_standard_rep,
    trivial_rep,
)
from algebrax.verification import (
    verify_frobenius_reciprocity,
    verify_mackey_intertwining,
    verify_representation_homomorphism,
    verify_transitivity_of_induction,
)


def _c3_omega_rep(c3: FiniteGroup[tuple[int, ...]]) -> ExplicitGroupRep[complex, tuple[int, ...]]:
    """Build the 1D faithful complex character omega = exp(2*pi*i/3) on C_3 <= S_3."""
    omega = cmath.exp(2j * math.pi / 3.0)
    mats = {
        (0, 1, 2): {0: {0: 1.0 + 0.0j}},
        (1, 2, 0): {0: {0: omega}},
        (2, 0, 1): {0: {0: omega**2}},
    }
    return ExplicitGroupRep(matrices={g: mats[g] for g in c3.elements}, dimension=1)


def _embed_s3_std_in_s4(
    s3_in_s4: FiniteGroup[tuple[int, ...]],
) -> ExplicitGroupRep[float, tuple[int, ...]]:
    """Embed the 2D standard representation of S_3 onto the stabilizer of 3 inside S_4."""
    std3 = symmetric_standard_rep(3)
    mats = {g: std3(g[:3]) for g in s3_in_s4.elements}
    return ExplicitGroupRep(matrices=mats, dimension=2)


# ---------------------------------------------------------------------------
# 1. Restriction Functor (Res_H^G)
# ---------------------------------------------------------------------------


def test_restrict_representation_and_character_on_s3_subgroups() -> None:
    s3 = symmetric_group(3)
    c3 = s3.subgroup([(1, 2, 0)], generate=True)
    c2 = s3.subgroup([(1, 0, 2)], generate=True)
    std = symmetric_standard_rep(3)

    res_c3 = restrict_representation(std, c3)
    assert res_c3.dimension == 2
    assert set(res_c3.matrices.keys()) == set(c3.elements)
    assert all(verify_representation_homomorphism(res_c3, c3).values())

    # Raw element sequence input also accepted
    res_c2 = restrict_representation(std, list(c2.elements))
    assert res_c2.dimension == 2
    assert all(verify_representation_homomorphism(res_c2, c2).values())

    # Character restriction matches Character.from_group(Res(rep), H)
    chi_std = Character.from_group(std, s3)
    chi_res = restrict_character(chi_std, s3, c3)
    chi_direct = Character.from_group(res_c3, c3)
    assert chi_res.degree == 2
    for c_class in c3.conjugacy_classes():
        assert abs(chi_res(c_class) - chi_direct(c_class)) < 1e-12


def test_restrict_representation_empty_subgroup_raises() -> None:
    std = symmetric_standard_rep(3)
    with pytest.raises(ValueError, match='at least one element'):
        restrict_representation(std, [])


# ---------------------------------------------------------------------------
# 2. Induced Representation Functor (Ind_H^G) & Character Formula
# ---------------------------------------------------------------------------


def test_induce_c3_omega_to_s3_yields_standard_2d_rep() -> None:
    s3 = symmetric_group(3)
    c3 = s3.subgroup([(1, 2, 0)], generate=True)
    omega_rep = _c3_omega_rep(c3)

    ind_rep = induced_representation(omega_rep, s3, c3)
    assert ind_rep.dimension == 2
    assert all(verify_representation_homomorphism(ind_rep, s3).values())

    std = symmetric_standard_rep(3)
    for g in s3.elements:
        assert abs(complex(ind_rep.trace(g)) - complex(std.trace(g))) < 1e-12

    # Induced character via Frobenius formula matches trace of induced representation
    chi_omega = Character.from_group(omega_rep, c3)
    chi_ind = induced_character(chi_omega, s3, c3)
    chi_std = Character.from_group(std, s3)
    assert chi_ind.degree == 2
    for c_class in s3.conjugacy_classes():
        assert abs(chi_ind(c_class) - chi_std(c_class)) < 1e-12


def test_induce_trivial_subgroups_recovers_regular_and_permutation_reps() -> None:
    s3 = symmetric_group(3)
    triv_sub = s3.subgroup([s3.identity])
    c2 = s3.subgroup([(1, 0, 2)], generate=True)
    c3 = s3.subgroup([(1, 2, 0)], generate=True)

    # Ind_{e}^G(1) == regular representation
    ind_reg = induced_representation(trivial_rep(triv_sub), s3, triv_sub)
    reg_s3 = regular_rep(s3)
    assert ind_reg.dimension == s3.order
    assert all(verify_representation_homomorphism(ind_reg, s3).values())
    for g in s3.elements:
        assert abs(complex(ind_reg.trace(g)) - complex(reg_s3.trace(g))) < 1e-12

    # Ind_{C_2}^{S_3}(1) has character equal to 3D defining permutation rep (A1 + E)
    ind_perm = induced_representation(trivial_rep(c2), s3, c2)
    def_s3 = symmetric_defining_rep(3)
    assert ind_perm.dimension == 3
    assert all(verify_representation_homomorphism(ind_perm, s3).values())
    for g in s3.elements:
        assert abs(complex(ind_perm.trace(g)) - complex(def_s3.trace(g))) < 1e-12

    # Ind_{C_3}^{S_3}(1) decomposes as Trivial (A1) + Sign (A2)
    ind_c3_triv = induced_representation(trivial_rep(c3), s3, c3)
    tbl = s3_character_table()
    class_reps = [(0, 1, 2), (1, 0, 2), (1, 2, 0)]
    chi_vec = [complex(ind_c3_triv.trace(g)) for g in class_reps]
    assert tbl.decompose(chi_vec) == {'Trivial (A1)': 1, 'Sign (A2)': 1}


def test_induced_representation_sparse_block_footprint_on_s4() -> None:
    s4 = symmetric_group(4)
    c3 = s4.subgroup([(1, 2, 0, 3)], generate=True)
    ind_rep = induced_representation(trivial_rep(c3), s4, c3)
    assert ind_rep.dimension == 8
    assert all(verify_representation_homomorphism(ind_rep, s4).values())

    # Each matrix must have strictly [S_4 : C_3] = 8 non-zero entries (sparse block permutation)
    for g in s4.elements:
        nnz = sum(len(row) for row in ind_rep(g).values())
        assert nnz == 8


def test_induce_higher_dim_rep_and_character_agreement_on_s4() -> None:
    s4 = symmetric_group(4)
    s3_in_s4 = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)
    assert s3_in_s4.order == 6

    w_rep = _embed_s3_std_in_s4(s3_in_s4)
    ind_rep = induced_representation(w_rep, s4, s3_in_s4)
    assert ind_rep.dimension == 8  # [S_4 : S_3] * 2 = 4 * 2
    assert all(verify_representation_homomorphism(ind_rep, s4).values())

    chi_w = Character.from_group(w_rep, s3_in_s4)
    chi_ind_formula = induced_character(chi_w, s4, s3_in_s4)
    chi_ind_rep = Character.from_group(ind_rep, s4)
    for c_class in s4.conjugacy_classes():
        assert abs(chi_ind_formula(c_class) - chi_ind_rep(c_class)) < 1e-11


def test_induce_validation_errors() -> None:
    s3 = symmetric_group(3)
    bad_sub = [(0, 1, 2), (1, 2, 0)]  # Missing inverse (2, 0, 1)
    triv = trivial_rep(s3)
    with pytest.raises(ValueError, match='not closed under inversion'):
        induced_representation(triv, s3, bad_sub)

    zero_dim_rep = ExplicitGroupRep(matrices={s3.identity: {}}, dimension=0)
    triv_sub = s3.subgroup([s3.identity])
    with pytest.raises(ValueError, match='positive dimension'):
        induced_representation(zero_dim_rep, s3, triv_sub)

    # String-labeled Character from CharacterTable cannot cover group elements
    c3 = s3.subgroup([(1, 2, 0)], generate=True)
    str_char = s3_character_table().irrep_character('Standard (E)')
    with pytest.raises(ValueError, match='does not cover all elements'):
        induced_character(str_char, s3, c3)


# ---------------------------------------------------------------------------
# 3. Frobenius Reciprocity Adjunction (Intertwiners & Inverse)
# ---------------------------------------------------------------------------


def test_frobenius_adjoint_transpose_and_inverse_on_s3() -> None:
    s3 = symmetric_group(3)
    c3 = s3.subgroup([(1, 2, 0)], generate=True)
    w_rep = _c3_omega_rep(c3)
    v_rep = symmetric_standard_rep(3)
    ind_w = induced_representation(w_rep, s3, c3)
    res_v = restrict_representation(v_rep, c3)

    # Project a generic 2x1 seed map into Hom_{C_3}(W, Res(V))
    seed = {0: {0: 1.0 + 0.0j}, 1: {0: 0.5 - 0.5j}}
    hom_h = reynolds_average(seed, w_rep, res_v, c3)
    assert hom_h != {}
    assert is_intertwiner(hom_h, w_rep, res_v, c3)

    # Natural isomorphism Hom_H(W, Res V) -> Hom_G(Ind W, V)
    hom_g = frobenius_adjoint_transpose(hom_h, v_rep, s3, c3, dim_w=w_rep.dimension)
    assert hom_g != {}
    assert is_intertwiner(hom_g, ind_w, v_rep, s3)

    # Round-trip inverse: Phi^{-1}(Phi(T)) == T and Phi(Phi^{-1}(T_tilde)) == T_tilde
    recovered_h = frobenius_adjoint_inverse(hom_g, dim_w=w_rep.dimension)
    assert set(recovered_h.keys()) == set(hom_h.keys())
    for r, row in hom_h.items():
        for c, val in row.items():
            assert abs(complex(recovered_h[r][c]) - complex(val)) < 1e-11

    retransposed_g = frobenius_adjoint_transpose(recovered_h, v_rep, s3, c3, dim_w=w_rep.dimension)
    for r in set(hom_g) | set(retransposed_g):
        for c in set(hom_g.get(r, {})) | set(retransposed_g.get(r, {})):
            assert abs(complex(hom_g.get(r, {}).get(c, 0)) - complex(retransposed_g.get(r, {}).get(c, 0))) < 1e-11


def test_frobenius_adjoint_transpose_higher_dimension_on_s4() -> None:
    s4 = symmetric_group(4)
    s3_in_s4 = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)
    w_rep = _embed_s3_std_in_s4(s3_in_s4)  # dim 2
    v_rep = symmetric_standard_rep(4)  # dim 3
    ind_w = induced_representation(w_rep, s4, s3_in_s4)  # dim 8
    res_v = restrict_representation(v_rep, s3_in_s4)  # dim 3

    seed = {0: {0: 1.0, 1: 0.2}, 1: {0: -0.3, 1: 1.0}, 2: {0: 0.4, 1: -0.5}}
    hom_h = reynolds_average(seed, w_rep, res_v, s3_in_s4)
    assert hom_h != {}
    assert is_intertwiner(hom_h, w_rep, res_v, s3_in_s4)

    hom_g = frobenius_adjoint_transpose(hom_h, v_rep, s4, s3_in_s4, dim_w=w_rep.dimension)
    assert hom_g != {}
    assert is_intertwiner(hom_g, ind_w, v_rep, s4)

    # Zero intertwiner maps cleanly to zero intertwiner
    assert frobenius_adjoint_transpose({}, v_rep, s4, s3_in_s4) == {}
    assert frobenius_adjoint_transpose({}, v_rep, s4, s3_in_s4, dim_w=2) == {}


def test_frobenius_adjoint_invalid_dim_w_raises() -> None:
    s3 = symmetric_group(3)
    c3 = s3.subgroup([(1, 2, 0)], generate=True)
    v_rep = symmetric_standard_rep(3)

    with pytest.raises(ValueError, match='positive integer'):
        frobenius_adjoint_transpose({0: {0: 1.0}}, v_rep, s3, c3, dim_w=0)

    with pytest.raises(ValueError, match='column index'):
        frobenius_adjoint_transpose({0: {2: 1.0}}, v_rep, s3, c3, dim_w=2)

    with pytest.raises(ValueError, match='positive integer'):
        frobenius_adjoint_inverse({0: {0: 1.0}}, dim_w=0)


# ---------------------------------------------------------------------------
# 4. Mackey Double Coset Decomposition & Intertwining Number
# ---------------------------------------------------------------------------


def test_mackey_decomposition_non_normal_subgroups_in_s4() -> None:
    s4 = symmetric_group(4)
    # Non-normal H = S_3 (stabilizer of 3, order 6) and non-normal K = D_4 (order 8)
    h_sub = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)
    k_sub = s4.subgroup([(1, 2, 3, 0), (0, 3, 2, 1)], generate=True)
    assert h_sub.order == 6
    assert not s4.is_normal(h_sub)
    assert k_sub.order == 8
    assert not s4.is_normal(k_sub)

    w_rep = _embed_s3_std_in_s4(h_sub)
    lhs_rep = restrict_representation(induced_representation(w_rep, s4, h_sub), k_sub)

    summands = mackey_decomposition(w_rep, s4, h_sub, k_sub)
    assert len(summands) == len(s4.double_cosets(k_sub, h_sub))
    for _, rep_piece in summands:
        assert all(verify_representation_homomorphism(rep_piece, k_sub).values())

    rhs_rep = direct_sum_rep([rep_piece for _, rep_piece in summands], k_sub)
    assert rhs_rep.dimension == lhs_rep.dimension

    chi_lhs = Character.from_group(lhs_rep, k_sub)
    chi_rhs = Character.from_group(rhs_rep, k_sub)
    for c_class in k_sub.conjugacy_classes():
        assert abs(chi_lhs(c_class) - chi_rhs(c_class)) < 1e-11


def test_mackey_intertwining_and_irreducibility_criterion() -> None:
    # 1. S_3: Ind_{C_3}^{S_3}(omega) is irreducible (intertwining == 1); Ind(1) is reducible (== 2)
    s3 = symmetric_group(3)
    c3 = s3.subgroup([(1, 2, 0)], generate=True)
    c2 = s3.subgroup([(1, 0, 2)], generate=True)
    chi_omega = Character.from_group(_c3_omega_rep(c3), c3)
    chi_c3_triv = Character.from_group(trivial_rep(c3), c3)
    chi_c2_triv = Character.from_group(trivial_rep(c2), c2)

    assert mackey_intertwining_number(chi_omega, chi_omega, s3, c3, c3) == 1
    assert mackey_intertwining_number(chi_c3_triv, chi_c3_triv, s3, c3, c3) == 2
    # <Ind_{C_3}^{S_3}(omega), Ind_{C_2}^{S_3}(1)> = <E, A1 + E> = 1
    assert mackey_intertwining_number(chi_omega, chi_c2_triv, s3, c3, c2) == 1
    # <Ind_{C_3}^{S_3}(1), Ind_{C_2}^{S_3}(1)> = <A1 + A2, A1 + E> = 1
    assert mackey_intertwining_number(chi_c3_triv, chi_c2_triv, s3, c3, c2) == 1

    # 2. Q_8: Ind_{<i>}^{Q_8}(chi_i) is irreducible (dim 2 spin rep)
    q8 = quaternion_group()
    c4_i = q8.subgroup(['i'], generate=True)
    chi_i_vals = {('1',): 1.0 + 0j, ('i',): 1.0j, ('-1',): -1.0 + 0j, ('-i',): -1.0j}
    chi_i = Character(values=chi_i_vals, degree=1)
    assert mackey_intertwining_number(chi_i, chi_i, q8, c4_i, c4_i) == 1
    chi_ind_q8 = induced_character(chi_i, q8, c4_i)
    chi_spin = Character.from_group(quaternion_rep(), q8)
    for c_class in q8.conjugacy_classes():
        assert abs(chi_ind_q8(c_class) - chi_spin(c_class)) < 1e-12

    # 3. D_4: Ind_{<r>}^{D_4}(chi_r) is irreducible (dim 2 dihedral rep)
    d4 = dihedral_group(4)
    c4_r = d4.subgroup(['r1'], generate=True)
    chi_r = Character(
        values={'r0': 1.0, 'r1': 1.0j, 'r2': -1.0, 'r3': -1.0j},
        degree=1,
    )
    assert mackey_intertwining_number(chi_r, chi_r, d4, c4_r, c4_r) == 1
    chi_ind_d4 = induced_character(chi_r, d4, c4_r)
    chi_d4 = Character.from_group(dihedral_rep(4, k=1), d4)
    for c_class in d4.conjugacy_classes():
        assert abs(chi_ind_d4(c_class) - chi_d4(c_class)) < 1e-12


def test_conjugate_representation_homomorphism() -> None:
    s4 = symmetric_group(4)
    h_sub = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)
    s = (0, 3, 2, 1)  # swaps 1 and 3 -> conjugates S_3(0,1,2) to S_3(0,3,2)
    s_inv = s4.inv(s)
    conj_sub = s4.subgroup([s4.mul(s4.mul(s, h), s_inv) for h in h_sub.elements])
    w_rep = _embed_s3_std_in_s4(h_sub)
    conj_rep = conjugate_representation(w_rep, s4, s, conj_sub)
    assert conj_rep.dimension == 2
    assert all(verify_representation_homomorphism(conj_rep, conj_sub).values())


# ---------------------------------------------------------------------------
# 5. Verification Predicates & Popper Falsification
# ---------------------------------------------------------------------------


def test_verify_frobenius_reciprocity_transitivity_and_mackey() -> None:
    s3 = symmetric_group(3)
    c3 = s3.subgroup([(1, 2, 0)], generate=True)
    chi_omega = Character.from_group(_c3_omega_rep(c3), c3)
    chi_std = Character.from_group(symmetric_standard_rep(3), s3)
    chi_sgn = Character.from_group(symmetric_sign_rep(3), s3)

    assert all(verify_frobenius_reciprocity(chi_omega, chi_std, s3, c3).values())
    assert all(verify_frobenius_reciprocity(chi_omega, chi_sgn, s3, c3).values())

    # Subgroup chain K <= H <= G in S_4: C_2 <= D_4 <= S_4
    s4 = symmetric_group(4)
    d4_sub = s4.subgroup([(1, 2, 3, 0), (0, 3, 2, 1)], generate=True)
    c2_sub = d4_sub.subgroup([(2, 3, 0, 1)], generate=True)
    chi_k_sgn = Character(values={(0, 1, 2, 3): 1.0, (2, 3, 0, 1): -1.0}, degree=1)
    assert all(verify_transitivity_of_induction(chi_k_sgn, s4, d4_sub, c2_sub).values())

    # Mackey verification on non-normal pair H = S_3, K = D_4 inside S_4
    s3_sub = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)
    chi_s3_std = Character.from_group(_embed_s3_std_in_s4(s3_sub), s3_sub)
    chi_d4_triv = Character.from_group(trivial_rep(d4_sub), d4_sub)
    assert all(verify_mackey_intertwining(chi_s3_std, chi_d4_triv, s4, s3_sub, d4_sub).values())
    # Exact character inner product equals Mackey intertwining integer
    direct_ip = character_inner_product(
        induced_character(chi_s3_std, s4, s3_sub),
        induced_character(chi_d4_triv, s4, d4_sub),
        s4,
    )
    assert abs(direct_ip - mackey_intertwining_number(chi_s3_std, chi_d4_triv, s4, s3_sub, d4_sub)) < 1e-11


def test_falsification_broken_class_functions_and_non_integer_mackey() -> None:
    s3 = symmetric_group(3)
    c2 = s3.subgroup([(1, 0, 2)], generate=True)
    chi_c2 = Character(values={(0, 1, 2): 1.0, (1, 0, 2): 1.0}, degree=1)

    # Break conjugation invariance of chi_V on S_3: assign different values to transpositions
    broken_v = Character(
        values={
            (0, 1, 2): 2.0,
            (1, 0, 2): 5.0,  # transposition in C_2
            (0, 2, 1): -1.0,  # conjugate transposition outside C_2
            (2, 1, 0): -1.0,
            (1, 2, 0): 0.0,
            (2, 0, 1): 0.0,
        },
        degree=2,
    )
    frob_res = verify_frobenius_reciprocity(chi_c2, broken_v, s3, c2)
    assert frob_res['frobenius_reciprocity'] is False
    assert frob_res['class_function_invariance'] is False

    # Break integrality for Mackey intertwining
    fractional_h = Character(values={(0, 1, 2): 0.3, (1, 0, 2): 0.3}, degree=1)
    mackey_res = verify_mackey_intertwining(fractional_h, chi_c2, s3, c2, c2)
    assert mackey_res['nonnegative_integer_intertwining'] is False
    with pytest.raises(ValueError, match='not an integer'):
        mackey_intertwining_number(fractional_h, chi_c2, s3, c2, c2)

    # Complex non-real Mackey intertwining raises ValueError
    non_real_h = Character(values={(0, 1, 2): 1.0 + 0.5j, (1, 0, 2): 1.0 + 0.5j}, degree=1)
    with pytest.raises(ValueError, match='non-real residual'):
        mackey_intertwining_number(non_real_h, chi_c2, s3, c2, c2)

    # Break class invariance in transitivity check (on non-abelian H = S_3 <= S_4)
    s4 = symmetric_group(4)
    s3_sub = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)
    broken_k = Character(
        values={
            (0, 1, 2, 3): 1.0,
            (1, 0, 2, 3): 2.0,
            (0, 2, 1, 3): 0.0,
            (2, 1, 0, 3): 0.0,
            (1, 2, 0, 3): 0.0,
            (2, 0, 1, 3): 0.0,
        },
        degree=1,
    )
    trans_res = verify_transitivity_of_induction(broken_k, s4, s3_sub, s3_sub)
    assert trans_res['class_function_invariance'] is False
