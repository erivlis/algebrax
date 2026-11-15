"""
Unit & Falsification Tests for Group Representations, Character Tables & Schur's Lemma.
"""

from __future__ import annotations

import pytest

from algebrax import rep
from algebrax.matrix.core import add, dot, trace
from algebrax.rep import (
    Character,
    CharacterTable,
    ExplicitGroupRep,
    GroupRepresentation,
    a4_character_table,
    alternating_defining_rep,
    alternating_elements,
    alternating_standard_rep,
    conjugacy_classes,
    cyclic_character_table,
    cyclic_rep,
    dihedral_character_table,
    dihedral_elements,
    dihedral_mul,
    dihedral_rep,
    direct_sum_rep,
    is_intertwiner,
    isotypic_projector,
    q8_character_table,
    quaternion_elements,
    quaternion_mul,
    quaternion_rep,
    regular_rep,
    reynolds_average,
    s3_character_table,
    s4_character_table,
    symmetric_defining_rep,
    symmetric_elements,
    symmetric_inv,
    symmetric_mul,
    symmetric_sign_rep,
    symmetric_standard_rep,
    tensor_product_rep,
    trivial_rep,
)
from algebrax.verification import (
    verify_burnside_dimension_formula,
    verify_representation_homomorphism,
    verify_schur_orthogonality,
    verify_schurs_lemma,
)


def _assert_sparse_close(
    a: dict[int, dict[int, float | complex]],
    b: dict[int, dict[int, float | complex]],
    tol: float = 1e-8,
) -> None:
    for r in set(a.keys()) | set(b.keys()):
        ra = a.get(r, {})
        rb = b.get(r, {})
        for c in set(ra.keys()) | set(rb.keys()):
            assert abs(complex(ra.get(c, 0)) - complex(rb.get(c, 0))) <= tol


def test_top_level_export_and_protocol_conformance() -> None:
    """Verify algebrax.rep exports and runtime_checkable GroupRepresentation protocol."""
    assert rep.CharacterTable is CharacterTable
    c4 = cyclic_rep(4, k=1)
    assert isinstance(c4, GroupRepresentation)
    assert isinstance(c4, ExplicitGroupRep)
    assert c4.dimension == 1
    assert abs(c4.trace(1) - 1.0j) < 1e-12


def test_cyclic_representations_and_fourier_character_table() -> None:
    """Verify cyclic group representations C_n, tensor products, duals, and character tables."""
    for n in (1, 3, 4, 5, 6):
        elems = list(range(n))
        table = cyclic_character_table(n)
        assert all(verify_schur_orthogonality(table).values())
        assert all(verify_burnside_dimension_formula(table).values())

        rho1 = cyclic_rep(n, k=1)
        hom_res = verify_representation_homomorphism(rho1, elems, lambda a, b, mod=n: (a + b) % mod, identity=0)
        assert all(hom_res.values())

        # Tensor product rho_1 (x) rho_1 ~= rho_2
        rho2_expected = cyclic_rep(n, k=2)
        rho1_sq = rho1.tensor_product(rho1)
        for g in elems:
            assert abs(complex(rho1_sq.trace(g)) - complex(rho2_expected.trace(g))) < 1e-9

        # Dual (contragredient) rep rho^*(g) = rho(g^-1)^T
        rho_dual = rho1.dual(inv_fn=lambda g, mod=n: (-g) % mod)
        rho_dual_auto = rho1.dual()
        for g in elems:
            _assert_sparse_close(rho_dual(g), rho_dual_auto(g))
            assert abs(complex(rho_dual.trace(g)) - complex(rho1.trace(g)).conjugate()) < 1e-9


def test_dihedral_representations_and_character_tables() -> None:
    """Verify dihedral D_2n geometric representations and character tables for odd and even n."""
    for n in (1, 2, 3, 4, 5, 6):
        elems = dihedral_elements(n)
        mul = dihedral_mul(n)
        rho = dihedral_rep(n, k=1)
        assert isinstance(rho, GroupRepresentation)
        assert rho.dimension == 2
        res = verify_representation_homomorphism(rho, elems, mul, identity='r0')
        assert all(res.values()), f'Failed D_{2 * n} homomorphism laws: {res}'

        tbl = dihedral_character_table(n)
        orth = verify_schur_orthogonality(tbl)
        burn = verify_burnside_dimension_formula(tbl)
        assert all(orth.values()), f'Failed D_{2 * n} Schur orthogonality: {orth}'
        assert all(burn.values()), f'Failed D_{2 * n} Burnside formula: {burn}'


def test_quaternion_q8_pauli_representation_and_character_table() -> None:
    """Verify faithful 2D Q_8 spin representation, Q_8 character table, and Schur decomposition."""
    elems = quaternion_elements()
    rho_q8 = quaternion_rep()
    assert rho_q8.dimension == 2
    res = verify_representation_homomorphism(rho_q8, elems, quaternion_mul, identity='1')
    assert all(res.values()), f'Failed Q_8 laws: {res}'

    # Verify i^2 = j^2 = k^2 = i*j*k = -I
    minus_i = {0: {0: -1.0 + 0j}, 1: {1: -1.0 + 0j}}
    _assert_sparse_close(dot(rho_q8('i'), rho_q8('i')), minus_i)
    _assert_sparse_close(dot(rho_q8('j'), rho_q8('j')), minus_i)
    _assert_sparse_close(dot(rho_q8('k'), rho_q8('k')), minus_i)
    _assert_sparse_close(dot(dot(rho_q8('i'), rho_q8('j')), rho_q8('k')), minus_i)

    q8_tbl = q8_character_table()
    assert all(verify_schur_orthogonality(q8_tbl).values())
    assert all(verify_burnside_dimension_formula(q8_tbl).values())

    # Evaluate Character.from_representation on Q_8 class representatives
    reps_map = {'{1}': '1', '{-1}': '-1', '{+-i}': 'i', '{+-j}': 'j', '{+-k}': 'k'}
    sizes_map = dict(zip(q8_tbl.classes, q8_tbl.class_sizes))
    chi_e = Character.from_representation(rho_q8, reps_map)
    assert chi_e.degree == 2
    assert chi_e.is_irreducible(8, sizes_map)
    assert q8_tbl.decompose(chi_e) == {'E': 1}

    # Decompose tensor product E (x) E = A1 + A2 + B1 + B2
    chi_e_sq = q8_tbl.tensor_product_character(chi_e, chi_e)
    assert q8_tbl.decompose(chi_e_sq) == {'A1': 1, 'A2': 1, 'B1': 1, 'B2': 1}


def test_symmetric_and_alternating_decompositions() -> None:
    """Verify S_3, S_4, and A_4 representations, Maschke decompositions, and conjugacy classes."""
    # 1. S_3: defining rep (3D) = Trivial (A1) + Standard (E)
    s3_tbl = s3_character_table()
    assert all(verify_schur_orthogonality(s3_tbl).values())
    assert all(verify_burnside_dimension_formula(s3_tbl).values())

    s3_elems = symmetric_elements(3)
    classes_s3 = conjugacy_classes(s3_elems, symmetric_mul, symmetric_inv)
    assert sorted(len(c) for c in classes_s3) == [1, 2, 3]

    def_s3 = symmetric_defining_rep(3)
    sgn_s3 = symmetric_sign_rep(3)
    std_s3 = symmetric_standard_rep(3)
    assert all(verify_representation_homomorphism(def_s3, s3_elems, symmetric_mul).values())
    assert all(verify_representation_homomorphism(sgn_s3, s3_elems, symmetric_mul).values())
    assert all(verify_representation_homomorphism(std_s3, s3_elems, symmetric_mul).values())

    s3_class_reps = {'1^3': (0, 1, 2), '2^1 1^1': (1, 0, 2), '3^1': (1, 2, 0)}
    chi_def_s3 = [complex(def_s3.trace(s3_class_reps[c])) for c in s3_tbl.classes]
    chi_std_s3 = [complex(std_s3.trace(s3_class_reps[c])) for c in s3_tbl.classes]
    assert s3_tbl.is_irreducible(chi_std_s3)
    assert not s3_tbl.is_irreducible(chi_def_s3)
    assert s3_tbl.decompose(chi_def_s3) == {'Trivial (A1)': 1, 'Standard (E)': 1}
    assert s3_tbl.decompose(chi_std_s3) == {'Standard (E)': 1}

    # Clebsch-Gordan / Kronecker product E (x) E = A1 + A2 + E
    e_row = s3_tbl.irrep_row('Standard (E)')
    assert s3_tbl.decompose(s3_tbl.tensor_product_character(e_row, e_row)) == {
        'Trivial (A1)': 1,
        'Sign (A2)': 1,
        'Standard (E)': 1,
    }

    # 2. S_4: defining rep (4D) = A1 + T2; T2 (x) A2 = T1
    s4_tbl = s4_character_table()
    assert all(verify_schur_orthogonality(s4_tbl).values())
    assert all(verify_burnside_dimension_formula(s4_tbl).values())

    s4_elems = symmetric_elements(4)
    std_s4 = symmetric_standard_rep(4)
    def_s4 = symmetric_defining_rep(4)
    assert all(verify_representation_homomorphism(std_s4, s4_elems, symmetric_mul).values())

    s4_class_reps = {
        '1^4': (0, 1, 2, 3),
        '2 1^2': (1, 0, 2, 3),
        '2^2': (1, 0, 3, 2),
        '3 1': (1, 2, 0, 3),
        '4': (1, 2, 3, 0),
    }
    chi_def_s4 = [complex(def_s4.trace(s4_class_reps[c])) for c in s4_tbl.classes]
    chi_std_s4 = [complex(std_s4.trace(s4_class_reps[c])) for c in s4_tbl.classes]
    assert s4_tbl.decompose(chi_def_s4) == {'Trivial (A1)': 1, 'Standard (T2)': 1}
    assert s4_tbl.decompose(chi_std_s4) == {'Standard (T2)': 1}
    assert s4_tbl.decompose(
        s4_tbl.tensor_product_character(s4_tbl.irrep_row('Standard (T2)'), s4_tbl.irrep_row('Sign (A2)'))
    ) == {'T1': 1}

    # 3. A_4 complex character table and defining/standard reps
    a4_tbl = a4_character_table()
    assert all(verify_schur_orthogonality(a4_tbl).values())
    assert all(verify_burnside_dimension_formula(a4_tbl).values())

    a4_elems = alternating_elements(4)
    assert len(a4_elems) == 12
    def_a4 = alternating_defining_rep(4)
    std_a4 = alternating_standard_rep(4)
    assert all(verify_representation_homomorphism(std_a4, a4_elems, symmetric_mul).values())
    a4_class_reps = {'e': (0, 1, 2, 3), '(12)(34)': (1, 0, 3, 2), '(123)': (1, 2, 0, 3), '(132)': (2, 0, 1, 3)}
    chi_def_a4 = [complex(def_a4.trace(a4_class_reps[c])) for c in a4_tbl.classes]
    assert a4_tbl.decompose(chi_def_a4) == {'1': 1, 'T': 1}


def test_regular_rep_and_maschke_isotypic_projectors() -> None:
    """Verify regular representation decomposes with multiplicity d_i and isotypic projectors partition I."""
    s3_elems = symmetric_elements(3)
    s3_table = {(g, h): symmetric_mul(g, h) for g in s3_elems for h in s3_elems}
    reg = regular_rep(s3_table)
    assert reg.dimension == 6
    assert all(verify_representation_homomorphism(reg, s3_elems, symmetric_mul).values())

    # Trace of regular rep is |G| at e, 0 elsewhere
    assert reg.trace((0, 1, 2)) == 6.0
    for g in s3_elems:
        if g != (0, 1, 2):
            assert reg.trace(g) == 0.0

    # Construct character functions on all elements of S_3
    triv_chi = dict.fromkeys(s3_elems, 1.0 + 0j)
    sgn_rep = symmetric_sign_rep(3)
    sgn_chi = {g: complex(sgn_rep.trace(g)) for g in s3_elems}
    std_rep = symmetric_standard_rep(3)
    std_chi = {g: complex(std_rep.trace(g)) for g in s3_elems}

    p_triv = isotypic_projector(reg, s3_elems, triv_chi, irrep_dim=1)
    p_sgn = isotypic_projector(reg, s3_elems, sgn_chi, irrep_dim=1)
    p_std = isotypic_projector(reg, s3_elems, std_chi, irrep_dim=2)

    # Verify traces equal d_i^2 (1, 1, 4)
    assert abs(complex(trace(p_triv)) - 1.0) < 1e-9
    assert abs(complex(trace(p_sgn)) - 1.0) < 1e-9
    assert abs(complex(trace(p_std)) - 4.0) < 1e-9

    # Verify idempotence (P^2 = P), orthogonality (P_i P_j = 0), and completeness (sum P_i = I_6)
    projectors = [p_triv, p_sgn, p_std]
    for i, pi in enumerate(projectors):
        _assert_sparse_close(dot(pi, pi), pi)
        for j, pj in enumerate(projectors):
            if i != j:
                _assert_sparse_close(dot(pi, pj), {})

    total_p = add(add(p_triv, p_sgn), p_std)
    identity_6 = {i: {i: 1.0} for i in range(6)}
    _assert_sparse_close(total_p, identity_6)


def test_schurs_lemma_intertwiners_and_reynolds_average() -> None:
    """Verify Schur's Lemma via Reynolds averaging for equal and inequivalent irreps."""
    s3_elems = symmetric_elements(3)
    sgn_s3 = symmetric_sign_rep(3)
    std_s3 = symmetric_standard_rep(3)

    # Case 1: Inequivalent irreps (1D Sign -> 2D Standard of S_3): only intertwiner is 0
    arbitrary_rect = {0: {0: 3.5}, 1: {0: -2.25}}
    avg_ineq = reynolds_average(arbitrary_rect, sgn_s3, std_s3, s3_elems, inv_fn=symmetric_inv)
    res_ineq = verify_schurs_lemma(avg_ineq, sgn_s3, std_s3, s3_elems, is_equivalent=False)
    assert all(res_ineq.values())

    # Case 2: Identical complex irrep (2D irrep of Q_8): intertwiner is (tr(T)/2) * I_2
    q8_elems = quaternion_elements()
    rho_q8 = quaternion_rep()
    arbitrary_2x2 = {0: {0: 4.0 + 1.0j, 1: -3.0}, 1: {0: 2.5j, 1: 6.0 - 1.0j}}
    avg_eq = reynolds_average(arbitrary_2x2, rho_q8, rho_q8, q8_elems)
    res_eq = verify_schurs_lemma(avg_eq, rho_q8, rho_q8, q8_elems, is_equivalent=True)
    assert all(res_eq.values())
    assert abs(avg_eq[0][0] - (5.0 + 0.0j)) < 1e-9

    # Direct is_intertwiner and direct_sum_rep check
    ds = direct_sum_rep([trivial_rep(s3_elems), std_s3], s3_elems)
    assert ds.dimension == 3
    proj_first = {0: {0: 1.0}}
    assert is_intertwiner(proj_first, ds, ds, s3_elems)


def test_falsification_and_validation_errors() -> None:
    """Falsify broken representations/tables and verify defensive validation exceptions."""
    # Broken representation: negate one element so homomorphism fails
    s3_elems = symmetric_elements(3)
    broken_mats = dict(symmetric_sign_rep(3).matrices)
    swap = (1, 0, 2)
    broken_mats[swap] = {0: {0: 1.0}}  # True sign is -1
    broken_rep = ExplicitGroupRep(matrices=broken_mats, dimension=1)
    hom_res = verify_representation_homomorphism(broken_rep, s3_elems, symmetric_mul)
    assert not hom_res['multiplicativity']

    # Corrupted character table fails Schur orthogonality & Burnside formula
    bad_tbl = CharacterTable(
        classes=['1^3', '2^1 1^1', '3^1'],
        class_sizes=[1, 3, 2],
        irreps=['A1', 'A2', 'E'],
        table=[[1, 1, 1], [1, -1, 1], [3, 0, -1]],
        group_order=6,
    )
    assert not all(verify_schur_orthogonality(bad_tbl).values())
    assert not all(verify_burnside_dimension_formula(bad_tbl).values())

    # Non-intertwiner fails Schur's Lemma
    q8_elems = quaternion_elements()
    rho_q8 = quaternion_rep()
    non_scalar = {0: {0: 1.0, 1: 2.0}, 1: {1: 3.0}}
    schur_bad = verify_schurs_lemma(non_scalar, rho_q8, rho_q8, q8_elems, is_equivalent=True)
    assert not schur_bad['intertwining']
    assert not schur_bad['schur_consequence']

    # Decompose guards against non-integer and virtual characters
    s3_tbl = s3_character_table()
    with pytest.raises(ValueError, match='Non-integer multiplicity'):
        s3_tbl.decompose([1.5, 0.0, 0.0])
    with pytest.raises(ValueError, match='Negative multiplicity'):
        s3_tbl.decompose([-1.0, -1.0, -1.0])
    a4_tbl = a4_character_table()
    with pytest.raises(ValueError, match='Non-real multiplicity'):
        a4_tbl.decompose([0.0, 0.0, 1.0j, 0.0])

    # Input validation errors
    with pytest.raises(ValueError):
        trivial_rep([])
    with pytest.raises(ValueError):
        regular_rep({})
    with pytest.raises(ValueError):
        cyclic_rep(0)
    with pytest.raises(ValueError):
        dihedral_rep(0)
    with pytest.raises(ValueError):
        symmetric_standard_rep(1)
    ds_tp = tensor_product_rep(rho_q8, rho_q8, q8_elems).direct_sum(rho_q8)
    assert ds_tp.dimension == 6
    with pytest.raises(ValueError):
        s3_tbl.inner_product([1.0], [1.0, 1.0, 1.0])


def test_finite_group_and_homomorphism_integration() -> None:
    """Verify GroupHom refinement and seamless FiniteGroup support across algebrax.rep & verification."""
    from algebrax.algebra import GroupHom
    from algebrax.group import quaternion_group, symmetric_group

    s3 = symmetric_group(3)
    q8 = quaternion_group()

    std_s3 = symmetric_standard_rep(3)
    rho_q8 = quaternion_rep()
    assert isinstance(std_s3, GroupHom)
    assert isinstance(std_s3, GroupRepresentation)

    assert all(verify_representation_homomorphism(std_s3, s3).values())
    assert all(verify_representation_homomorphism(rho_q8, q8).values())

    reg_s3 = regular_rep(s3)
    assert reg_s3.dimension == 6
    p_std = isotypic_projector(reg_s3, s3, {g: complex(std_s3.trace(g)) for g in s3}, irrep_dim=2)
    assert abs(complex(trace(p_std)) - 4.0) < 1e-9

    chi_std = Character.from_group(std_s3, s3)
    sizes = {c: len(c) for c in s3.conjugacy_classes()}
    assert chi_std.is_irreducible(s3.order, sizes)

    arbitrary = {0: {0: 2.0 + 1.0j, 1: -1.0}, 1: {0: 3.0j, 1: 4.0 - 1.0j}}
    intertwiner = reynolds_average(arbitrary, rho_q8, rho_q8, q8)
    assert all(verify_schurs_lemma(intertwiner, rho_q8, rho_q8, q8, is_equivalent=True).values())

    dual_q8 = rho_q8.dual(elements=q8)
    assert all(verify_representation_homomorphism(dual_q8, q8).values())

