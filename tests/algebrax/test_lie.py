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
    StructureConstants,
    clifford_lie_algebra,
    e8,
    f4,
    g2,
    se3,
    sl2,
    so3,
    so_n,
    sp_n,
    su2,
    su_n,
    u1,
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
    alg = so3()
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
    """Verify so(3) commutation relations and vector cross product isomorphism."""
    alg = so3()
    assert alg.dim == 3
    assert alg.basis_names == ['J_x', 'J_y', 'J_z']

    # [J_x, J_y] = J_z
    b_xy = alg.bracket({'J_x': 1.0}, {'J_y': 1.0})
    assert b_xy == {2: 1.0}

    # [J_y, J_z] = J_x
    b_yz = alg.bracket({'J_y': 1.0}, {'J_z': 1.0})
    assert b_yz == {0: 1.0}

    # [J_z, J_x] = J_y
    b_zx = alg.bracket({'J_z': 1.0}, {'J_x': 1.0})
    assert b_zx == {1: 1.0}

    # Antisymmetry: [J_y, J_x] = -J_z
    b_yx = alg.bracket({'J_y': 1.0}, {'J_x': 1.0})
    assert b_yx == {2: -1.0}

    # General cross product u x v
    u = [1.0, 2.0, 3.0]
    v = [4.0, 5.0, 6.0]
    # Expected u x v:
    # cx = 2*6 - 3*5 = 12 - 15 = -3
    # cy = 3*4 - 1*6 = 12 - 6 = 6
    # cz = 1*5 - 2*4 = 5 - 8 = -3
    cross = alg.bracket(u, v)
    assert math.isclose(cross.get(0, 0.0), -3.0)
    assert math.isclose(cross.get(1, 0.0), 6.0)
    assert math.isclose(cross.get(2, 0.0), -3.0)


def test_sl2_commutation_relations():
    """Verify sl(2, R) commutation relations [e, f] = h, [h, e] = 2e, [h, f] = -2f."""
    alg = sl2()
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
    alg = se3()
    assert alg.dim == 6
    assert alg.basis_names == ['J_x', 'J_y', 'J_z', 'P_x', 'P_y', 'P_z']
    assert alg.structure_constants.verify_jacobi()

    # Rotational subalgebra: [J_x, J_y] = J_z
    assert alg.bracket({'J_x': 1.0}, {'J_y': 1.0}) == {2: 1.0}

    # Rotation on translation: [J_x, P_y] = P_z (index 5)
    assert alg.bracket({'J_x': 1.0}, {'P_y': 1.0}) == {5: 1.0}
    assert alg.bracket({'J_y': 1.0}, {'P_z': 1.0}) == {3: 1.0}
    assert alg.bracket({'J_z': 1.0}, {'P_x': 1.0}) == {4: 1.0}

    # Translation commutativity: [P_i, P_j] = 0
    assert alg.bracket({'P_x': 1.0}, {'P_y': 1.0}) == {}
    assert alg.bracket({'P_x': 1.0}, {'P_z': 1.0}) == {}


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
    alg = so3()
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
    alg_so3 = so3()
    k_so3 = alg_so3.killing_matrix()
    assert k_so3[0][0] == -2.0
    assert k_so3[1][1] == -2.0
    assert k_so3[2][2] == -2.0
    assert alg_so3.is_semisimple()

    # sl(2, R): semisimple
    alg_sl2 = sl2()
    assert alg_sl2.is_semisimple()

    # se(3): non-semisimple due to abelian translation ideal
    alg_se3 = se3()
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
    alg = so3()

    # Commuting elements: [X, Y] = 0 -> BCH(X, Y) == X + Y
    x_comm = {'J_z': 0.1}
    y_comm = {'J_z': 0.2}
    for order in (1, 2, 3, 4):
        bch_res = alg.bch(x_comm, y_comm, order=order)
        assert math.isclose(bch_res[2], 0.3, abs_tol=1e-12)
        assert len(bch_res) == 1

    # Order terms check for non-commuting J_x and J_y
    x = {'J_x': 0.05}
    y = {'J_y': 0.05}
    # Order 1: X + Y
    res_o1 = alg.bch(x, y, order=1)
    assert math.isclose(res_o1[0], 0.05)
    assert math.isclose(res_o1[1], 0.05)
    assert 2 not in res_o1

    # Order 2: + 1/2 [X, Y] = + 0.5 * 0.0025 J_z = 0.00125 J_z
    res_o2 = alg.bch(x, y, order=2)
    assert math.isclose(res_o2[2], 0.00125)

    # Order 3: includes + 1/12 [X, [X, Y]] - 1/12 [Y, [X, Y]]
    res_o3 = alg.bch(x, y, order=3)
    assert res_o3[0] < 0.05  # slightly decreased by commutator back-reaction
    assert res_o3[1] < 0.05

    # Order 4
    res_o4 = alg.bch(x, y, order=4)
    assert isinstance(res_o4, dict)

    # Invalid order raises ValueError
    with pytest.raises(ValueError, match='between 1 and 4'):
        alg.bch(x, y, order=0)
    with pytest.raises(ValueError, match='between 1 and 4'):
        alg.bch(x, y, order=5)

    # Inputs exceeding convergence radius ln(2) trigger ConvergenceWarning
    large_x = {'J_x': 0.5}
    large_y = {'J_y': 0.5}  # 0.5 + 0.5 = 1.0 >= ln(2) ~ 0.693
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
    alg = so3()
    # String keys
    res = alg.bracket({'J_x': 2.0}, {'J_y': 3.0})
    assert res == {2: 6.0}

    # Named conversion
    named = alg.to_named(res)
    assert named == {'J_z': 6.0}

    # Unknown generator raises KeyError
    with pytest.raises(KeyError, match="Unknown basis generator name 'J_w'"):
        alg.bracket({'J_w': 1.0}, {'J_x': 1.0})

    # Repr and Jupyter hooks
    assert 'so(3)' not in repr(alg) or 'LieAlgebra' in repr(alg)
    assert '$$\\mathfrak{g}' in alg._repr_latex_()
    assert 'LieAlgebra' in alg._repr_html_()


def test_complex_lie_algebras_su2_and_u1():
    """Verify complex matrix Lie algebras u(1) and su(2), and complex Lie elements."""
    # u(1)
    alg_u1 = u1()
    assert alg_u1.dim == 1
    assert alg_u1.basis_names == ['T']
    assert alg_u1.bracket({'T': 1.0}, {'T': 2.0}) == {}
    assert not alg_u1.is_semisimple()

    # su(2)
    alg_su2 = su2()
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

    # F_4 and E_8 raises NotImplementedError
    with pytest.raises(NotImplementedError, match='F₄'):
        f4()
    with pytest.raises(NotImplementedError, match='E₈'):
        e8()


