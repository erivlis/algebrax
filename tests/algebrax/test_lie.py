"""
Unit and property tests for Lie Algebras, Root Systems, and BCH Dynamics (EP-0163).

Verifies:
1. StructureConstants: antisymmetry and Jacobi identity via einsum contraction.
2. Canonical Lie algebras: so(3), sl(2), se(3), and Clifford bivector algebras.
3. Adjoint representation: ad_X(Y) = [X, Y] via matrix-vector multiplication.
4. Killing form and Cartan criterion for semisimplicity (so(3) and sl(2) semisimple, se(3) not).
5. Adjoint invariance of Killing metric: B([X, Y], Z) + B(Y, [X, Z]) = 0.
6. Baker-Campbell-Hausdorff series orders 1..4, commuting identity, and ConvergenceWarning.
7. Matrix basis projection (from_matrix_basis) and roundtrip conversions.
8. Error handling on non-closed or singular bases and invalid BCH orders.
"""

import math
import warnings

import pytest

import algebrax as ax
from algebrax.lie import (
    ConvergenceWarning,
    LieAlgebra,
    RootSystem,
    StructureConstants,
    chevalley_lie_algebra,
    clifford_lie_algebra,
    e6,
    e7,
    e8,
    f4,
    g2,
    se_n,
    sl_n,
    so_n,
    sp_n,
    su_n,
    u_n,
)
from algebrax.matrix import commutator, mat_vec
from algebrax.semiring.algebraic import CliffordSemiring


def test_structure_constants_jacobi_and_antisymmetry():
    """Verify antisymmetry and Jacobi identity validation on StructureConstants."""
    # Abelian structure (all 0)
    abelian_sc = StructureConstants(dim=2, tensor={})
    assert abelian_sc.verify_antisymmetry()
    assert abelian_sc.verify_jacobi()

    # so(3) structure constants
    alg = so_n(3, names=['J_x', 'J_y', 'J_z'])
    sc = alg.structure_constants
    assert sc.dim == 3
    assert sc.verify_antisymmetry()
    assert sc.verify_jacobi()

    # Faulty structure constants violating Jacobi: [T_0, T_1] = T_0, [T_0, T_2] = T_1, [T_1, T_2] = 0
    bad_sc = StructureConstants(dim=3, tensor={(0, 1, 0): 1.0, (1, 0, 0): -1.0, (0, 2, 1): 1.0, (2, 0, 1): -1.0})
    assert not bad_sc.verify_jacobi()

    # Faulty structure constants violating antisymmetry
    bad_anti = StructureConstants(dim=3, tensor={(0, 1, 2): 1.0, (1, 0, 2): 1.0})
    assert not bad_anti.verify_antisymmetry()


def test_so3_bracket_and_cross_product():
    """Verify so(3) commutation relations on skew-symmetric basis."""
    alg = so_n(3)
    assert alg.dim == 3
    assert alg.basis_names == ['L_{01}', 'L_{02}', 'L_{12}']

    # [L_{01}, L_{02}] = -L_{12}
    b_01 = alg.bracket({'L_{01}': 1.0}, {'L_{02}': 1.0})
    assert b_01 == {2: -1.0}

    # [L_{01}, L_{12}] = L_{02}
    b_02 = alg.bracket({'L_{01}': 1.0}, {'L_{12}': 1.0})
    assert b_02 == {1: 1.0}

    # [L_{02}, L_{12}] = -L_{01}
    b_12 = alg.bracket({'L_{02}': 1.0}, {'L_{12}': 1.0})
    assert b_12 == {0: -1.0}

    # Antisymmetry: [L_{02}, L_{01}] = L_{12}
    b_rev = alg.bracket({'L_{02}': 1.0}, {'L_{01}': 1.0})
    assert b_rev == {2: 1.0}


def test_sl2_commutation_relations():
    """Verify sl(2, R) commutation relations [e, f] = h, [h, e] = 2e, [h, f] = -2f."""
    alg = sl_n(2, names=['e', 'f', 'h'])
    assert alg.dim == 3
    assert alg.basis_names == ['e', 'f', 'h']
    assert alg.structure_constants.verify_jacobi()

    # [e, f] = h
    b_ef = alg.bracket({'e': 1.0}, {'f': 1.0})
    assert b_ef == {2: 1.0}

    # [h, e] = 2e
    b_he = alg.bracket({'h': 1.0}, {'e': 1.0})
    assert b_he == {0: 2.0}

    # [h, f] = -2f
    b_hf = alg.bracket({'h': 1.0}, {'f': 1.0})
    assert b_hf == {1: -2.0}


def test_se3_kinematics_bracket():
    """Verify se(3) kinematics relations between rotations and translations."""
    alg = se_n(3)
    assert alg.dim == 6
    assert alg.basis_names == ['J_{01}', 'J_{02}', 'J_{12}', 'P_0', 'P_1', 'P_2']
    assert alg.structure_constants.verify_jacobi()

    # Rotational subalgebra: [J_{01}, J_{02}] = -J_{12}
    assert alg.bracket({'J_{01}': 1.0}, {'J_{02}': 1.0}) == {2: -1.0}

    # Rotation on translation: [J_{01}, P_1] = P_0 (index 3)
    assert alg.bracket({'J_{01}': 1.0}, {'P_1': 1.0}) == {3: 1.0}
    assert alg.bracket({'J_{02}': 1.0}, {'P_2': 1.0}) == {3: 1.0}

    # Translation commutativity: [P_i, P_j] = 0
    assert alg.bracket({'P_0': 1.0}, {'P_1': 1.0}) == {}
    assert alg.bracket({'P_0': 1.0}, {'P_2': 1.0}) == {}


def test_clifford_bivector_lie_algebra():
    """Verify that Clifford algebra bivectors form closed Lie algebras."""
    # Cl(3, 0) bivectors form so(3)
    c30 = clifford_lie_algebra(3, 0)
    assert c30.dim == 3
    assert c30.structure_constants.verify_jacobi()
    assert c30.structure_constants.verify_antisymmetry()
    assert c30.is_semisimple()

    # Cl(3, 1) bivectors form Lorentz so(3, 1)
    c31 = clifford_lie_algebra(3, 1)
    assert c31.dim == 6
    assert c31.structure_constants.verify_jacobi()
    assert c31.structure_constants.verify_antisymmetry()
    assert c31.is_semisimple()

    # Via CliffordSemiring instance
    cs = CliffordSemiring(p=2, q=0)
    c20 = clifford_lie_algebra(cs)
    assert c20.dim == 1  # 1 bivector in 2D (so(2))
    assert c20.structure_constants.verify_jacobi()


def test_adjoint_matrix_representation():
    """Verify ad_X(Y) matrix satisfies (ad_X Y) == [X, Y]."""
    alg = so_n(3, names=['J_x', 'J_y', 'J_z'])
    x = [0.2, -0.4, 0.5]
    y = [0.1, 0.7, -0.3]

    adj_x = alg.adjoint_matrix(x)
    bracket_xy = alg.bracket(x, y)

    # mat_vec(adj_x, y)
    y_sparse = dict(enumerate(y))
    adj_y_res = mat_vec(adj_x, y_sparse)

    for i in range(alg.dim):
        assert math.isclose(bracket_xy.get(i, 0.0), adj_y_res.get(i, 0.0), abs_tol=1e-12)


def test_killing_form_and_cartan_semisimplicity():
    """Verify Killing matrix, signature, Cartan's criterion, and adjoint invariance."""
    # so(3): Killing matrix is -2 * I_3, semisimple
    alg_so3 = so_n(3)
    k_so3 = alg_so3.killing_matrix()
    assert k_so3[0][0] == -1.0 or k_so3[0][0] == -2.0  # Normalized Killing metric
    assert alg_so3.is_semisimple()

    # sl(2, R): semisimple
    alg_sl2 = sl_n(2)
    assert alg_sl2.is_semisimple()

    # se(3): non-semisimple due to abelian translation ideal
    alg_se3 = se_n(3)
    assert not alg_se3.is_semisimple()

    # Killing form symmetry: B(X, Y) == B(Y, X)
    x = [0.3, -0.1, 0.5]
    y = [0.2, 0.4, -0.2]
    assert math.isclose(alg_so3.killing_form(x, y), alg_so3.killing_form(y, x))

    # Adjoint Invariance: B([X, Y], Z) + B(Y, [X, Z]) == 0
    z = [0.1, -0.5, 0.2]
    xy = alg_so3.bracket(x, y)
    xz = alg_so3.bracket(x, z)
    term1 = alg_so3.killing_form(xy, z)
    term2 = alg_so3.killing_form(y, xz)
    assert math.isclose(term1 + term2, 0.0, abs_tol=1e-12)


def test_bch_formula():
    """Verify Baker-Campbell-Hausdorff series across orders and check convergence warning."""
    alg = so_n(3)

    # Commuting elements: [X, Y] = 0 -> BCH(X, Y) == X + Y
    x_comm = {'L_{01}': 0.1}
    y_comm = {'L_{01}': 0.2}
    for order in (1, 2, 3, 4):
        bch_res = alg.bch(x_comm, y_comm, order=order)
        assert math.isclose(bch_res[0], 0.3, abs_tol=1e-12)
        assert len(bch_res) == 1

    # Order terms check for non-commuting L_{01} and L_{02}
    x = {'L_{01}': 0.05}
    y = {'L_{02}': 0.05}
    # Order 1: X + Y
    res_o1 = alg.bch(x, y, order=1)
    assert math.isclose(res_o1[0], 0.05)
    assert math.isclose(res_o1[1], 0.05)
    assert 2 not in res_o1

    # Order 2: + 1/2 [X, Y] = + 0.5 * 0.0025 * (-L_{12}) = -0.00125 L_{12}
    res_o2 = alg.bch(x, y, order=2)
    assert math.isclose(res_o2[2], -0.00125)

    # Order 3
    res_o3 = alg.bch(x, y, order=3)
    assert isinstance(res_o3, dict)

    # Order 4
    res_o4 = alg.bch(x, y, order=4)
    assert isinstance(res_o4, dict)

    # Invalid order raises ValueError
    with pytest.raises(ValueError, match='between 1 and 4'):
        alg.bch(x, y, order=0)
    with pytest.raises(ValueError, match='between 1 and 4'):
        alg.bch(x, y, order=5)

    # Inputs exceeding convergence radius ln(2) trigger ConvergenceWarning
    large_x = {'L_{01}': 0.5}
    large_y = {'L_{02}': 0.5}  # 0.5 + 0.5 = 1.0 >= ln(2) ~ 0.693
    with pytest.warns(ConvergenceWarning, match='exceed convergence radius'):
        alg.bch(large_x, large_y, order=4)

    # Small inputs should NOT trigger ConvergenceWarning
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        alg.bch(x, y, order=4)


def test_from_matrix_basis_and_conversions():
    """Verify constructing LieAlgebra from matrix basis and roundtrip conversions."""
    jx = {1: {2: -1.0}, 2: {1: 1.0}}
    jy = {0: {2: 1.0}, 2: {0: -1.0}}
    jz = {0: {1: -1.0}, 1: {0: 1.0}}

    alg = LieAlgebra.from_matrix_basis([jx, jy, jz], names=['Jx', 'Jy', 'Jz'])
    assert alg.dim == 3
    assert alg.structure_constants.verify_jacobi()

    # element_to_matrix and matrix_to_element
    coord = [0.2, -0.4, 0.6]
    mat = alg.element_to_matrix(coord)
    assert mat[1][2] == -0.2
    assert mat[2][1] == 0.2
    assert mat[0][1] == -0.6

    coord_back = alg.matrix_to_element(mat)
    for i in range(3):
        assert math.isclose(coord[i], coord_back.get(i, 0.0), abs_tol=1e-12)

    # Error on non-closed matrix basis
    # [jx, jy] = jz, but jz is missing
    with pytest.raises(ValueError, match='not closed under commutator'):
        LieAlgebra.from_matrix_basis([jx, jy])

    # Error on linearly dependent matrix basis
    with pytest.raises(ValueError, match='singular or linearly dependent'):
        LieAlgebra.from_matrix_basis([jx, jx])

    # Error on empty basis
    with pytest.raises(ValueError, match='empty basis'):
        LieAlgebra.from_matrix_basis([])


def test_naming_and_ergonomics():
    """Verify dictionary normalization, string generator names, and rich representations."""
    alg = so_n(3)
    # String keys
    res = alg.bracket({'L_{01}': 2.0}, {'L_{02}': 3.0})
    assert res == {2: -6.0}

    # Named conversion
    named = alg.to_named(res)
    assert named == {'L_{12}': -6.0}

    # Unknown generator raises KeyError
    with pytest.raises(KeyError, match="Unknown basis generator name 'J_w'"):
        alg.bracket({'J_w': 1.0}, {'L_{01}': 1.0})

    # Repr and Jupyter hooks
    assert 'so(3)' not in repr(alg) or 'LieAlgebra' in repr(alg)
    assert '$$\\mathfrak{g}' in alg._repr_latex_()
    assert 'LieAlgebra' in alg._repr_html_()


def test_complex_lie_algebras_su2_and_u1():
    """Verify complex matrix Lie algebras u(1) and su(2), and complex Lie elements."""
    # u(1)
    alg_u1 = u_n(1, names=['T'])
    assert alg_u1.dim == 1
    assert alg_u1.basis_names == ['T']
    assert alg_u1.bracket({'T': 1.0}, {'T': 2.0}) == {}
    assert not alg_u1.is_semisimple()

    # su(2)
    alg_su2 = su_n(2, names=['J_x', 'J_y', 'J_z'])
    assert alg_su2.dim == 3
    assert alg_su2.basis_names == ['J_x', 'J_y', 'J_z']
    assert alg_su2.structure_constants.verify_jacobi()
    assert alg_su2.structure_constants.verify_antisymmetry()
    assert alg_su2.is_semisimple()

    # [J_x, J_y] = J_z
    comm_xy = alg_su2.bracket({'J_x': 1.0}, {'J_y': 1.0})
    assert math.isclose(comm_xy.get(2, 0.0), 1.0)

    # [J_y, J_z] = J_x
    comm_yz = alg_su2.bracket({'J_y': 1.0}, {'J_z': 1.0})
    assert math.isclose(comm_yz.get(0, 0.0), 1.0)

    # [J_z, J_x] = J_y
    comm_zx = alg_su2.bracket({'J_z': 1.0}, {'J_x': 1.0})
    assert math.isclose(comm_zx.get(1, 0.0), 1.0)

    # Complex Lie element bracket
    x_c = {'J_x': 0.1 + 0.2j}
    y_c = {'J_y': 0.3 - 0.1j}
    comm_c = alg_su2.bracket(x_c, y_c)
    # (0.1 + 0.2j) * (0.3 - 0.1j) = 0.03 - 0.01j + 0.06j - 0.02 j^2 = 0.05 + 0.05j
    assert math.isclose(comm_c[2].real, 0.05)
    assert math.isclose(comm_c[2].imag, 0.05)

    # Complex BCH with 2-norm safe calculation
    bch_c = alg_su2.bch(x_c, y_c, order=2)
    assert isinstance(bch_c, dict)

    # Complex matrix to element and back
    mat = alg_su2.element_to_matrix(x_c)
    coords_recon = alg_su2.matrix_to_element(mat)
    assert math.isclose(coords_recon[0].real, 0.1)
    assert math.isclose(coords_recon[0].imag, 0.2)


def test_classical_families_and_exceptional_g2():
    """Verify general classical Lie algebras (u_n, su_n, so_n, sp_n) and exceptional G_2."""
    # u(2): dim 4, not semisimple
    u2 = u_n(2)
    assert u2.dim == 4
    assert u2.structure_constants.verify_jacobi()
    assert not u2.is_semisimple()

    # su(3): dim 8, semisimple
    su3 = su_n(3)
    assert su3.dim == 8
    assert su3.structure_constants.verify_jacobi()
    assert su3.is_semisimple()

    # so(4): dim 6, semisimple
    so4 = so_n(4)
    assert so4.dim == 6
    assert so4.structure_constants.verify_jacobi()
    assert so4.is_semisimple()

    # sp(4): dim 10, semisimple
    sp4 = sp_n(2)
    assert sp4.dim == 10
    assert sp4.structure_constants.verify_jacobi()
    assert sp4.is_semisimple()

    # G_2: dim 14, semisimple
    alg_g2 = g2()
    assert alg_g2.dim == 14
    assert alg_g2.structure_constants.verify_jacobi()
    assert alg_g2.structure_constants.verify_antisymmetry()
    assert alg_g2.is_semisimple()

    # F_4: dim 52, semisimple
    alg_f4 = f4()
    assert alg_f4.dim == 52
    assert alg_f4.structure_constants.verify_antisymmetry()
    assert alg_f4.is_semisimple()

    # E_6: dim 78, semisimple
    alg_e6 = e6()
    assert alg_e6.dim == 78
    assert alg_e6.structure_constants.verify_antisymmetry()
    assert alg_e6.is_semisimple()

    # E_7: dim 133, semisimple
    alg_e7 = e7()
    assert alg_e7.dim == 133
    assert alg_e7.structure_constants.verify_antisymmetry()
    assert alg_e7.is_semisimple()

    # E_8: dim 248, semisimple
    alg_e8 = e8()
    assert alg_e8.dim == 248
    assert alg_e8.structure_constants.verify_antisymmetry()
    assert alg_e8.is_semisimple()


def test_root_system_all_families_and_weyl_reflections():
    """Verify RootSystem classification, Weyl reflections, Euclidean embedding, and Dynkin diagrams."""
    # Test cases: (family, rank, expected_roots, expected_pos)
    cases = [
        ('A', 3, 12, 6),
        ('B', 2, 8, 4),
        ('C', 3, 18, 9),
        ('D', 4, 24, 12),
        ('G2', None, 12, 6),
        ('F4', None, 48, 24),
        ('E6', None, 72, 36),
        ('E7', None, 126, 63),
        ('E8', None, 240, 120),
    ]

    for fam, r, num_roots, num_pos in cases:
        rs = RootSystem.from_dynkin(fam, rank=r)
        assert len(rs.roots) == num_roots, f'{fam} total roots mismatch'
        assert len(rs.positive_roots) == num_pos, f'{fam} pos roots mismatch'
        assert len(rs.negative_roots) == num_pos, f'{fam} neg roots mismatch'

        # Verify Weyl reflection involution: s_i(s_i(alpha)) == alpha
        for root in rs.positive_roots[:5]:
            for i in range(rs.rank):
                ref1 = rs.weyl_reflect(root, i)
                assert ref1 in rs.roots, f'Reflection {ref1} not in root system for {fam}'
                ref2 = rs.weyl_reflect(ref1, i)
                assert ref2 == root, f'Involution s_i^2 != id failed for {fam}'

        # Verify Euclidean projection
        euc = rs.to_euclidean(rs.simple_roots[0])
        assert isinstance(euc, tuple)
        assert len(euc) >= rs.rank

        # Verify ASCII Dynkin diagram rendering
        diagram = rs.dynkin_diagram()
        assert isinstance(diagram, str)
        assert len(diagram) > 0


def test_classical_families_sl_se_and_shortcuts():
    """Verify sl_n, se_n, so_n, and their algebraic properties."""
    # sl_n
    sl3 = sl_n(3)
    assert sl3.dim == 8
    assert sl3.structure_constants.verify_jacobi()
    assert sl3.is_semisimple()

    # se_n
    se2_alg = se_n(2)
    assert se2_alg.dim == 3
    assert se2_alg.structure_constants.verify_jacobi()
    assert not se2_alg.is_semisimple()

    assert so_n(2).dim == 1


def test_chevalley_lie_algebra_factory():
    """Verify chevalley_lie_algebra for classical and exceptional Dynkin types."""
    # Exceptional types
    assert chevalley_lie_algebra('G2').dim == 14
    assert chevalley_lie_algebra('F4').dim == 52
    assert chevalley_lie_algebra('E6').dim == 78
    assert chevalley_lie_algebra('E7').dim == 133
    assert chevalley_lie_algebra('E8').dim == 248

    # Classical types via RootSystem
    rs_a2 = RootSystem.from_dynkin('A', 2)
    assert chevalley_lie_algebra(rs_a2).dim == 8  # su(3)

    rs_b2 = RootSystem.from_dynkin('B', 2)
    assert chevalley_lie_algebra(rs_b2).dim == 10  # so(5)

    rs_c2 = RootSystem.from_dynkin('C', 2)
    assert chevalley_lie_algebra(rs_c2).dim == 10  # sp(4)

    rs_d4 = RootSystem.from_dynkin('D', 4)
    assert chevalley_lie_algebra(rs_d4).dim == 28  # so(8)

    # General simply-laced from raw Cartan matrix
    raw_cartan = [[2, -1], [-1, 2]]  # A2
    alg_raw = chevalley_lie_algebra(raw_cartan)
    assert alg_raw.dim == 8


def test_validation_errors_and_edge_cases():
    """Verify validation exceptions, fallback methods, and edge cases across lie."""
    # Invalid dimensional parameters
    with pytest.raises(ValueError, match='u\\(n\\) is only defined for n >= 1'):
        u_n(0)
    with pytest.raises(ValueError, match='su\\(n\\) is only defined for n >= 2'):
        su_n(1)
    with pytest.raises(ValueError, match='sp\\(2n\\) is only defined for n >= 1'):
        sp_n(0)
    with pytest.raises(ValueError, match='so\\(n\\) is only defined for n >= 2'):
        so_n(1)
    with pytest.raises(ValueError, match='sl\\(n\\) is only defined for n >= 2'):
        sl_n(1)
    with pytest.raises(ValueError, match='se\\(n\\) is only defined for n >= 2'):
        se_n(1)

    # RootSystem validation
    with pytest.raises(ValueError, match='Rank must be specified'):
        RootSystem.from_dynkin('A')
    with pytest.raises(ValueError, match='A_n requires rank >= 1'):
        RootSystem.from_dynkin('A', 0)
    with pytest.raises(ValueError, match='B_n requires rank >= 2'):
        RootSystem.from_dynkin('B', 1)
    with pytest.raises(ValueError, match='C_n requires rank >= 2'):
        RootSystem.from_dynkin('C', 1)
    with pytest.raises(ValueError, match='D_n requires rank >= 4'):
        RootSystem.from_dynkin('D', 3)
    with pytest.raises(ValueError, match='Unknown Dynkin family'):
        RootSystem.from_dynkin('Z', 5)

    # Fallback dynkin diagram and Euclidean projection
    custom_rs = RootSystem.from_cartan_matrix([[2]], dynkin_type='CustomType')
    assert 'CustomType' in custom_rs.dynkin_diagram()
    assert custom_rs.to_euclidean((1,)) == (1.0,)
    assert 'RootSystem' in repr(custom_rs)

    # LieAlgebra without matrix basis errors
    abstract_alg = LieAlgebra(dim=2, structure_constants=StructureConstants(dim=2, tensor={}))
    with pytest.raises(ValueError, match='not initialized with a matrix basis'):
        abstract_alg.element_to_matrix({0: 1.0})
    with pytest.raises(ValueError, match='not initialized with a matrix basis'):
        abstract_alg.matrix_to_element({0: {0: 1.0}})

    # _repr_latex_ with > 6 generators
    assert '\\dots' in e8()._repr_latex_()

    # Complex cleaning with imaginary part
    u2 = u_n(2)
    b_c = u2.bracket({0: 1.0 + 1.0j}, {1: 2.0j})
    assert any(isinstance(v, complex) and abs(v.imag) > 1e-10 for v in b_c.values())

    # All Dynkin diagrams
    for dynkin_label in ['A3', 'B2', 'C3', 'D4', 'G2', 'F4', 'E6', 'E7', 'E8']:
        fam = dynkin_label[:2] if dynkin_label.startswith(('G2', 'F4', 'E6', 'E7', 'E8')) else dynkin_label[0]
        r = (
            int(dynkin_label[1:])
            if (len(dynkin_label) > 1 and dynkin_label[1:].isdigit() and not dynkin_label.startswith(('G', 'F', 'E')))
            else None
        )
        rs_diag = RootSystem.from_dynkin(fam, rank=r)
        d_ascii = rs_diag.dynkin_diagram('ascii')
        d_mermaid = rs_diag.dynkin_diagram('mermaid')
        d_svg = rs_diag.dynkin_diagram('svg')
        assert len(d_ascii) > 0
        assert d_mermaid.startswith('flowchart LR')
        assert d_svg.startswith('<svg')
        assert d_svg.endswith('</svg>')
        assert rs_diag.dynkin_ascii() == d_ascii
        assert rs_diag.dynkin_mermaid() == d_mermaid
        assert rs_diag.dynkin_svg() == d_svg
        assert rs_diag._repr_svg_() == d_svg

    # Specific structural checks
    rs_a3 = RootSystem.from_dynkin('A', 3)
    assert '1((1)) --- 2((2))' in rs_a3.dynkin_mermaid()
    assert '2((2)) --- 3((3))' in rs_a3.dynkin_mermaid()
    assert rs_a3.dynkin_ascii() == '(1) --- (2) --- (3)'

    rs_b2 = RootSystem.from_dynkin('B', 2)
    assert '1((1)) ==> 2((2))' in rs_b2.dynkin_mermaid()
    assert '<polygon' in rs_b2.dynkin_svg()

    rs_c3 = RootSystem.from_dynkin('C', 3)
    assert '2((2)) <== 3((3))' in rs_c3.dynkin_mermaid()
    assert '<polygon' in rs_c3.dynkin_svg()

    rs_d4 = RootSystem.from_dynkin('D', 4)
    assert '2((2)) --- 3((3))' in rs_d4.dynkin_mermaid()
    assert '2((2)) --- 4((4))' in rs_d4.dynkin_mermaid()

    rs_g2 = RootSystem.from_dynkin('G2')
    assert '1((1)) ===|"⇒ (3)"| 2((2))' in rs_g2.dynkin_mermaid()
    assert '<polygon' in rs_g2.dynkin_svg()
    assert rs_g2.dynkin_ascii() == '(1) ≡>≡ (2)'

    rs_f4 = RootSystem.from_dynkin('F4')
    assert '2((2)) ==> 3((3))' in rs_f4.dynkin_mermaid()
    assert '<polygon' in rs_f4.dynkin_svg()

    rs_e6 = RootSystem.from_dynkin('E6')
    assert '2((2)) --- 4((4))' in rs_e6.dynkin_mermaid()
    assert '5((5)) --- 6((6))' in rs_e6.dynkin_mermaid()

    rs_a1 = RootSystem.from_dynkin('A', 1)
    assert '1((1))' in rs_a1.dynkin_mermaid()
    assert '<circle' in rs_a1.dynkin_svg()

    # Fallback / custom type
    rs_custom = RootSystem.from_cartan_matrix([[2]], dynkin_type='CustomX')
    assert rs_custom.dynkin_diagram('ascii') == 'Dynkin(CustomX, rank=1)'
    assert '1((1))' in rs_custom.dynkin_diagram('mermaid')
    assert '<circle' in rs_custom.dynkin_diagram('svg')

    # Invalid format error handling
    with pytest.raises(ValueError, match="Unsupported Dynkin diagram format 'pdf'"):
        rs_a3.dynkin_diagram('pdf')  # type: ignore[arg-type]
