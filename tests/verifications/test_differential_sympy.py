"""Comparative (Differential) Verification — Symbolic Algebra, Lie, Galois, Clifford & Group Theory (EP-0183).

Pits AlgebraX's exact rational linear algebra, Lie algebras, Root systems, Baker-Campbell-Hausdorff (BCH)
dynamics, Galois finite fields GF(p^m), Clifford geometric algebra rotors, permutation groups, and
automatic differentiation semirings against SymPy (`sympy.Matrix`, `sympy.liealgebras`, `sympy.Poly`,
`sympy.combinatorics.Permutation`, `sympy.diff`) and SciPy (`scipy.linalg.expm`, `scipy.spatial.transform.Rotation`).
"""

from __future__ import annotations

import math
import warnings
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
import scipy.linalg
import sympy as sp
from hypothesis import given, settings
from hypothesis import strategies as st
from scipy.spatial.transform import Rotation
from sympy.combinatorics.permutations import Permutation as SymPyPermutation
from sympy.liealgebras.root_system import RootSystem as SymPyRootSystem

import algebrax as ax
from algebrax.algebra import GaloisField
from algebrax.matrix.academic import PerformanceWarning
from algebrax.semiring import (
    BinomialConvolutionSemiring,
    CliffordAlgebra,
    DualNumberAlgebra,
    GeneralizedCliffordAlgebra,
    MultivariateBinomialConvolutionSemiring,
    PolynomialAlgebra,
    QuantumCliffordAlgebra,
    StandardSemiring,
)
from algebrax.typing import SparseMatrix


def _sympy_rational_to_fraction(val: sp.Basic) -> Fraction:
    """Convert an exact SymPy Rational/Integer to Python's fractions.Fraction."""
    rat = sp.Rational(val)
    return Fraction(int(rat.p), int(rat.q))


# =============================================================================
# 1. Exact Rational Linear Algebra (Fraction) vs. SymPy Matrix over Q
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_exact_fraction_matrix_determinant_adjoint_and_inverse_vs_sympy() -> None:
    """Verify exact zero-rounding determinant, cofactor, adjoint, and inverse over Fraction vs SymPy Matrix."""
    # Exact 3x3 rational matrix with non-trivial fractions
    entries = [
        [Fraction(2, 3), Fraction(-1, 4), Fraction(3, 5)],
        [Fraction(1, 2), Fraction(5, 6), Fraction(-2, 3)],
        [Fraction(-3, 4), Fraction(1, 3), Fraction(7, 8)],
    ]
    n = 3
    mat_ax: SparseMatrix[int, Fraction] = {
        r: {c: entries[r][c] for c in range(n) if entries[r][c] != 0} for r in range(n)
    }
    mat_sp = sp.Matrix(
        [[sp.Rational(entries[r][c].numerator, entries[r][c].denominator) for c in range(n)] for r in range(n)]
    )

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', PerformanceWarning)
        det_ax = ax.matrix.academic.determinant(mat_ax)
        cof_ax = ax.matrix.academic.cofactor(mat_ax)
        adj_ax = ax.matrix.academic.adjoint(mat_ax)
        inv_ax = ax.matrix.academic.inverse(mat_ax)

    det_sp = _sympy_rational_to_fraction(mat_sp.det())
    assert det_ax == det_sp

    cof_sp = mat_sp.cofactor_matrix()
    adj_sp = mat_sp.adjugate()
    inv_sp = mat_sp.inv()

    for r in range(n):
        for c in range(n):
            assert cof_ax.get(r, {}).get(c, Fraction(0)) == _sympy_rational_to_fraction(cof_sp[r, c])
            assert adj_ax.get(r, {}).get(c, Fraction(0)) == _sympy_rational_to_fraction(adj_sp[r, c])
            assert inv_ax.get(r, {}).get(c, Fraction(0)) == _sympy_rational_to_fraction(inv_sp[r, c])

    # Verify exact multiplicative identity A * A^(-1) == I over StandardSemiring(Fraction)
    sr_frac = StandardSemiring(Fraction)
    prod_ax = ax.matrix.dot(mat_ax, inv_ax, semiring=sr_frac)
    identity_ax = {i: {i: Fraction(1)} for i in range(n)}
    assert prod_ax == identity_ax


@pytest.mark.verification
@pytest.mark.differential
@settings(max_examples=20, deadline=None)
@given(
    numerators=st.lists(st.integers(min_value=-5, max_value=5), min_size=9, max_size=9),
    denominators=st.lists(st.integers(min_value=1, max_value=4), min_size=9, max_size=9),
)
def test_hypothesis_exact_fraction_determinant_and_inverse_vs_sympy(
    numerators: list[int],
    denominators: list[int],
) -> None:
    """Property-based exact Q verification: determinant & inverse over Fraction match SymPy with zero error."""
    n = 3
    mat_ax: SparseMatrix[int, Fraction] = {}
    rows_sp: list[list[sp.Rational]] = []

    for r in range(n):
        row_sp: list[sp.Rational] = []
        for c in range(n):
            idx = r * n + c
            val = Fraction(numerators[idx], denominators[idx])
            if r == c and val == 0:
                val = Fraction(1)
            if val != 0:
                mat_ax.setdefault(r, {})[c] = val
            row_sp.append(sp.Rational(val.numerator, val.denominator))
        rows_sp.append(row_sp)

    mat_sp = sp.Matrix(rows_sp)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', PerformanceWarning)
        det_ax = ax.matrix.academic.determinant(mat_ax, n=n)

    det_sp = _sympy_rational_to_fraction(mat_sp.det())
    assert det_ax == det_sp

    if det_sp != 0:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', PerformanceWarning)
            inv_ax = ax.matrix.academic.inverse(mat_ax)
        inv_sp = mat_sp.inv()
        for r in range(n):
            for c in range(n):
                assert inv_ax.get(r, {}).get(c, Fraction(0)) == _sympy_rational_to_fraction(inv_sp[r, c])


# =============================================================================
# 2. Lie Algebras, Root Systems & BCH Dynamics vs. SymPy & SciPy.linalg.expm
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_root_systems_and_cartan_matrices_vs_sympy() -> None:
    """Verify RootSystem Cartan matrices, determinants, and root counts against sympy.liealgebras.RootSystem."""
    # Expected total root counts |Phi| = 2 |Phi^+| for crystallographic Dynkin types
    cases: list[tuple[str, int, int]] = [
        ('A', 1, 2),
        ('A', 2, 6),
        ('A', 3, 12),
        ('B', 2, 8),
        ('B', 3, 18),
        ('C', 2, 8),
        ('C', 3, 18),
        ('D', 4, 24),
        ('G2', 2, 12),
        ('F4', 4, 48),
        ('E6', 6, 72),
        ('E7', 7, 126),
        ('E8', 8, 240),
    ]

    for fam, rank, expected_num_roots in cases:
        rs_ax = ax.lie.RootSystem.from_dynkin(fam, rank)
        cartan_ax = sp.Matrix(rs_ax.cartan_matrix)

        if (fam, rank) == ('A', 1):
            # SymPy's TypeA(1).cartan_matrix() has an upstream IndexError (m[0, 1] = -1 on a 1x1 matrix)
            cartan_sp = sp.Matrix([[2]])
        elif (fam, rank) == ('C', 2):
            # SymPy's TypeC requires n >= 3 (since C_2 is dual to B_2)
            cartan_sp = SymPyRootSystem(['B', 2]).cartan_matrix().T
        else:
            rs_sp = SymPyRootSystem([fam[0], rank])
            cartan_sp = rs_sp.cartan_matrix()

        # Rank and Cartan matrix determinant (isomorphism invariant independent of node relabeling)
        assert rs_ax.rank == rank
        assert cartan_ax.shape == cartan_sp.shape
        assert cartan_ax.det() == cartan_sp.det()

        # For A_n, D_n, G_2 Cartan matrices match SymPy entrywise; B_n, C_n, F_4 match up to dual transpose
        if fam in ('A', 'D', 'G2'):
            assert rs_ax.cartan_matrix == cartan_sp.tolist()
        elif fam in ('B', 'C', 'F4'):
            assert rs_ax.cartan_matrix in (cartan_sp.tolist(), cartan_sp.T.tolist())

        # Verify positive/negative root partition and total root cardinality
        assert len(rs_ax.roots) == expected_num_roots
        assert len(rs_ax.positive_roots) == expected_num_roots // 2
        assert len(rs_ax.negative_roots) == expected_num_roots // 2
        assert len(rs_ax.simple_roots) == rank

        # Verify Symmetrizing factors d_i satisfy d_i A_{ij} == d_j A_{ji}
        d = rs_ax.symmetrizing_factors
        for i in range(rank):
            for j in range(rank):
                assert d[i] * rs_ax.cartan_matrix[i][j] == d[j] * rs_ax.cartan_matrix[j][i]


@pytest.mark.verification
@pytest.mark.differential
def test_differential_lie_bch_series_vs_scipy_expm() -> None:
    """Verify Baker-Campbell-Hausdorff series exp(X)exp(Y) = exp(BCH(X, Y)) against scipy.linalg.expm."""
    rng = np.random.default_rng(18301)

    for g, mat_dim in [
        (ax.lie.so_n(3), 3),
        (ax.lie.sl_n(2), 2),
        (ax.lie.su_n(2), 2),
        (ax.lie.se_n(3), 4),
    ]:
        # Sample small elements X, Y well inside the BCH convergence radius ||X|| + ||Y|| < ln(2)
        x_coords = [float(v) for v in rng.uniform(-0.08, 0.08, size=g.dim)]
        y_coords = [float(v) for v in rng.uniform(-0.08, 0.08, size=g.dim)]

        x_mat = np.asarray(
            ax.converters.to_numpy(g.element_to_matrix(x_coords), shape=(mat_dim, mat_dim)), dtype=np.complex128
        )
        y_mat = np.asarray(
            ax.converters.to_numpy(g.element_to_matrix(y_coords), shape=(mat_dim, mat_dim)), dtype=np.complex128
        )

        # Exact matrix group product via SciPy Padé matrix exponential
        target_group_prod = scipy.linalg.expm(x_mat) @ scipy.linalg.expm(y_mat)

        errors: list[float] = []
        for order in (1, 2, 3, 4):
            z_bch = g.bch(x_coords, y_coords, order=order)
            z_mat = np.asarray(
                ax.converters.to_numpy(g.element_to_matrix(z_bch), shape=(mat_dim, mat_dim)),
                dtype=np.complex128,
            )
            approx_prod = scipy.linalg.expm(z_mat)
            errors.append(float(np.linalg.norm(target_group_prod - approx_prod, ord='fro')))

        # Higher BCH orders must strictly improve approximation accuracy, with order-4 residual < 1e-6
        assert errors[3] < errors[1] < errors[0]
        assert errors[3] < 1e-6


@pytest.mark.verification
@pytest.mark.differential
def test_differential_lie_adjoint_homomorphism_and_killing_form() -> None:
    """Verify [ad_X, ad_Y] = ad_{[X, Y]}, Killing form trace identity, and Cartan semisimplicity."""
    rng = np.random.default_rng(18302)

    semisimple_algebras = [ax.lie.so_n(3), ax.lie.sl_n(3), ax.lie.su_n(2), ax.lie.sp_n(1), ax.lie.g2()]
    for g in semisimple_algebras:
        assert g.is_semisimple()
        assert g.structure_constants.verify_antisymmetry()
        assert g.structure_constants.verify_jacobi()

        x = [float(v) for v in rng.normal(0.0, 1.0, size=g.dim)]
        y = [float(v) for v in rng.normal(0.0, 1.0, size=g.dim)]
        z = [float(v) for v in rng.normal(0.0, 1.0, size=g.dim)]

        ad_x = ax.converters.to_numpy(g.adjoint_matrix(x), shape=(g.dim, g.dim))
        ad_y = ax.converters.to_numpy(g.adjoint_matrix(y), shape=(g.dim, g.dim))
        xy = g.bracket(x, y)
        ad_xy = ax.converters.to_numpy(g.adjoint_matrix(xy), shape=(g.dim, g.dim))

        # 1. Adjoint representation is a Lie algebra homomorphism: [ad_X, ad_Y] == ad_{[X, Y]}
        np.testing.assert_allclose(ad_x @ ad_y - ad_y @ ad_x, ad_xy, rtol=1e-11, atol=1e-11)

        # 2. Killing form matches matrix trace Tr(ad_X @ ad_Y)
        b_xy_ax = float(np.real(g.killing_form(x, y)))
        b_xy_np = float(np.trace(ad_x @ ad_y))
        assert math.isclose(b_xy_ax, b_xy_np, rel_tol=1e-11, abs_tol=1e-11)

        # 3. Ad-invariance of Killing form: B([X, Y], Z) + B(Y, [X, Z]) == 0
        xz = g.bracket(x, z)
        invariance_sum = float(np.real(g.killing_form(xy, z) + g.killing_form(y, xz)))
        assert math.isclose(invariance_sum, 0.0, abs_tol=1e-10)

    # Non-semisimple Lie algebras (reductive u(2) with abelian center, and Euclidean se(2), se(3))
    for non_ss in [ax.lie.u_n(2), ax.lie.se_n(2), ax.lie.se_n(3)]:
        assert not non_ss.is_semisimple()


# =============================================================================
# 3. Galois Finite Fields GF(p^m) vs. SymPy Polynomial Quotient Arithmetic
# =============================================================================


def _dict_to_sympy_poly(elem: dict[int, int], x_sym: sp.Symbol, p: int) -> sp.Poly:
    """Convert an AlgebraX GF(p^m) sparse dict {deg: coeff} into a SymPy Poly over GF(p)."""
    expr = sum((coeff * (x_sym**deg) for deg, coeff in elem.items()), sp.Integer(0))
    return sp.Poly(expr, x_sym, domain=sp.GF(p, symmetric=False))


def _sympy_poly_to_dict(poly: sp.Poly, p: int) -> dict[int, int]:
    """Convert a SymPy Poly over GF(p) back to an AlgebraX canonical sparse dict {deg: coeff}."""
    res: dict[int, int] = {}
    for (deg,), coeff in poly.terms():
        c_mod = int(coeff) % p
        if c_mod != 0:
            res[int(deg)] = c_mod
    return res


@pytest.mark.verification
@pytest.mark.differential
def test_differential_galois_field_arithmetic_and_fermat_little_theorem_vs_sympy() -> None:
    """Verify GaloisField GF(2^8) and GF(3^3) against SymPy Poly mod irreducible polynomial."""
    x = sp.Symbol('x')

    # 1. AES Field GF(2^8) modulo P(x) = x^8 + x^4 + x^3 + x + 1
    aes_poly_tuple = (1, 1, 0, 1, 1, 0, 0, 0, 1)
    gf_aes = GaloisField(p=2, irreduc_poly=aes_poly_tuple)
    mod_poly_aes = _dict_to_sympy_poly({i: c for i, c in enumerate(aes_poly_tuple) if c}, x, p=2)

    a = {0: 1, 1: 1, 4: 1, 6: 1}  # 1 + x + x^4 + x^6
    b = {1: 1, 2: 1, 5: 1, 7: 1}  # x + x^2 + x^5 + x^7

    add_ax = gf_aes.add(a, b)
    mul_ax = gf_aes.mul(a, b)

    a_sp = _dict_to_sympy_poly(a, x, p=2)
    b_sp = _dict_to_sympy_poly(b, x, p=2)
    add_sp = _sympy_poly_to_dict(a_sp + b_sp, p=2)
    mul_sp = _sympy_poly_to_dict((a_sp * b_sp) % mod_poly_aes, p=2)

    assert add_ax == add_sp
    assert mul_ax == mul_sp

    # Fermat's Little Theorem in GF(2^8)^*: a^(255) == 1 and multiplicative inverse a * a^(254) == 1
    assert gf_aes.power(a, 255) == gf_aes.one
    a_inv = gf_aes.power(a, 254)
    assert gf_aes.mul(a, a_inv) == gf_aes.one

    # Freshman's Dream / Frobenius endomorphism in characteristic 2: (a + b)^2 == a^2 + b^2
    assert gf_aes.power(gf_aes.add(a, b), 2) == gf_aes.add(gf_aes.power(a, 2), gf_aes.power(b, 2))

    # 2. Odd-characteristic extension field GF(3^3) modulo P(x) = x^3 + 2x + 1 (irreducible over F_3)
    gf_27_tuple = (1, 2, 0, 1)
    gf_27 = GaloisField(p=3, irreduc_poly=gf_27_tuple)
    mod_poly_27 = _dict_to_sympy_poly({i: c for i, c in enumerate(gf_27_tuple) if c}, x, p=3)

    u = {0: 2, 1: 1, 2: 2}
    v = {0: 1, 2: 1}
    assert gf_27.mul(u, v) == _sympy_poly_to_dict(
        (_dict_to_sympy_poly(u, x, p=3) * _dict_to_sympy_poly(v, x, p=3)) % mod_poly_27,
        p=3,
    )
    # Order of multiplicative group GF(3^3)^* is 3^3 - 1 = 26
    assert gf_27.power(u, 26) == gf_27.one
    assert gf_27.power(gf_27.add(u, v), 3) == gf_27.add(gf_27.power(u, 3), gf_27.power(v, 3))


@pytest.mark.verification
@pytest.mark.differential
def test_differential_gf_matrix_mul_vs_sympy() -> None:
    """Verify galois.gf_matrix_mul over GF(2^8) against SymPy matrix multiplication over GF(2)[x]/P(x)."""
    x = sp.Symbol('x')
    aes_poly_tuple = (1, 1, 0, 1, 1, 0, 0, 0, 1)
    mod_poly = _dict_to_sympy_poly({i: c for i, c in enumerate(aes_poly_tuple) if c}, x, p=2)

    m1 = {
        0: {0: {0: 1, 1: 1}, 1: {1: 1, 3: 1}},
        1: {0: {2: 1}, 1: {0: 1, 4: 1, 7: 1}},
    }
    m2 = {
        0: {0: {1: 1, 5: 1}, 1: {0: 1}},
        1: {0: {3: 1, 6: 1}, 1: {2: 1, 7: 1}},
    }

    prod_ax = ax.galois.gf_matrix_mul(m1, m2, p=2, irreduc_poly=aes_poly_tuple)

    for r in range(2):
        for c in range(2):
            acc_sp = sp.Poly(0, x, domain=sp.GF(2, symmetric=False))
            for k in range(2):
                p1 = _dict_to_sympy_poly(m1[r][k], x, p=2)
                p2 = _dict_to_sympy_poly(m2[k][c], x, p=2)
                acc_sp = (acc_sp + (p1 * p2) % mod_poly) % mod_poly
            assert prod_ax.get(r, {}).get(c, {}) == _sympy_poly_to_dict(acc_sp, p=2)


# =============================================================================
# 4. Clifford Geometric Algebra & Rotors vs. SciPy Spatial Rotation
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_clifford_rotor_rotation_vs_scipy_rotation() -> None:
    """Verify clifford.rotor_rotation in 3D coordinate planes against scipy.spatial.transform.Rotation."""
    rng = np.random.default_rng(18304)

    for _ in range(10):
        vec_np = rng.normal(0.0, 5.0, size=3)
        vec_ax = {(0,): float(vec_np[0]), (1,): float(vec_np[1]), (2,): float(vec_np[2])}
        angle = float(rng.uniform(-math.pi, math.pi))

        # Plane (0, 1) -> rotation around +z axis by angle
        rot_xy_ax = ax.clifford.rotor_rotation(vec_ax, bivector=(0, 1), angle_rad=angle, p=3)
        rot_xy_sp = Rotation.from_rotvec([0.0, 0.0, angle]).apply(vec_np)
        np.testing.assert_allclose(
            [rot_xy_ax.get((0,), 0.0), rot_xy_ax.get((1,), 0.0), rot_xy_ax.get((2,), 0.0)],
            rot_xy_sp,
            rtol=1e-11,
            atol=1e-11,
        )

        # Plane (1, 2) -> rotation around +x axis by angle
        rot_yz_ax = ax.clifford.rotor_rotation(vec_ax, bivector=(1, 2), angle_rad=angle, p=3)
        rot_yz_sp = Rotation.from_rotvec([angle, 0.0, 0.0]).apply(vec_np)
        np.testing.assert_allclose(
            [rot_yz_ax.get((0,), 0.0), rot_yz_ax.get((1,), 0.0), rot_yz_ax.get((2,), 0.0)],
            rot_yz_sp,
            rtol=1e-11,
            atol=1e-11,
        )

        # Plane (0, 2) -> e_0 ^ e_2 = - e_2 ^ e_0 -> rotation around -y axis by angle
        rot_xz_ax = ax.clifford.rotor_rotation(vec_ax, bivector=(0, 2), angle_rad=angle, p=3)
        rot_xz_sp = Rotation.from_rotvec([0.0, -angle, 0.0]).apply(vec_np)
        np.testing.assert_allclose(
            [rot_xz_ax.get((0,), 0.0), rot_xz_ax.get((1,), 0.0), rot_xz_ax.get((2,), 0.0)],
            rot_xz_sp,
            rtol=1e-11,
            atol=1e-11,
        )


@pytest.mark.verification
@pytest.mark.differential
def test_differential_clifford_algebras_and_bivector_lie_isomorphism() -> None:
    """Verify Clifford Cl(p,q,r), GeneralizedClifford, QuantumClifford, and Spin(3) ~= so(3) isomorphism."""
    # 1. Minkowski Spacetime Algebra Cl(1, 3, 0) with 1-indexed generators:
    # e_1^2 = +1, e_2^2 = e_3^2 = e_4^2 = -1, and e_i e_j + e_j e_i = 0 for i != j
    cl_spacetime = CliffordAlgebra(p=1, q=3, r=0)
    expected_sq = {1: 1.0, 2: -1.0, 3: -1.0, 4: -1.0}
    for i in range(1, 5):
        ei = {(i,): 1.0}
        assert cl_spacetime.mul(ei, ei) == {(): expected_sq[i]}
        for j in range(i + 1, 5):
            ej = {(j,): 1.0}
            anticomm = cl_spacetime.add(cl_spacetime.mul(ei, ej), cl_spacetime.mul(ej, ei))
            assert anticomm == {}

    # 2. Bivector Lie algebra of Cl(3, 0, 0) is isomorphic to so(3): dim = 3, Killing form = -2 * I_3
    spin3 = ax.lie.clifford_lie_algebra(3)
    assert spin3.dim == 3
    assert spin3.is_semisimple()
    assert spin3.structure_constants.verify_jacobi()

    # 3. Generalized Clifford Algebra C_3^(2): e_0^3 = 1, e_1^3 = 1, e_0 e_1 = omega e_1 e_0
    gca = GeneralizedCliffordAlgebra(n_order=3, num_generators=2)
    g0 = {(1, 0): 1.0 + 0j}
    g1 = {(0, 1): 1.0 + 0j}
    assert gca.power(g0, 3) == gca.one
    assert gca.power(g1, 3) == gca.one
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    prod_01 = ax.clifford.gca_product(g0, g1, n_order=3, num_generators=2)
    prod_10 = ax.clifford.gca_product(g1, g0, n_order=3, num_generators=2)
    assert cmath_isclose(prod_01[(1, 1)], omega * prod_10[(1, 1)])

    # 4. Quantum Clifford Algebra Cl_q(2): e_1 * e_0 = -q * (e_0 * e_1)
    q_param = 0.6 + 0.8j
    q_sr = QuantumCliffordAlgebra(q=q_param, num_generators=2)
    q_01 = ax.clifford.quantum_clifford_product(g0, g1, q=q_param, num_generators=2)
    q_10 = ax.clifford.quantum_clifford_product(g1, g0, q=q_param, num_generators=2)
    assert cmath_isclose(q_10[(1, 1)], -q_param * q_01[(1, 1)])
    assert q_sr.mul(g0, g0) == q_sr.one


def cmath_isclose(a: complex, b: complex, tol: float = 1e-12) -> bool:
    """Check closeness of two complex numbers."""
    return abs(a - b) <= tol


# =============================================================================
# 5. Permutation Groups vs. SymPy Combinatorics
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
@settings(max_examples=30, deadline=None)
@given(
    perm1=st.permutations(range(7)),
    perm2=st.permutations(range(7)),
)
def test_hypothesis_differential_permutation_group_vs_sympy(
    perm1: list[int],
    perm2: list[int],
) -> None:
    """Property-based differential check: group.compose, invert, and signature match SymPy Permutation."""
    n = len(perm1)
    p1_ax = {i: perm1[i] for i in range(n)}
    p2_ax = {i: perm2[i] for i in range(n)}

    p1_sp = SymPyPermutation(perm1)
    p2_sp = SymPyPermutation(perm2)

    # 1. Parity / signature matches SymPy (-1 for odd, +1 for even)
    sgn1_ax = ax.group.signature(p1_ax)
    sgn2_ax = ax.group.signature(p2_ax)
    assert sgn1_ax == (1 if p1_sp.is_even else -1)
    assert sgn2_ax == (1 if p2_sp.is_even else -1)

    # 2. Composition: ax.group.compose(p1, p2)[k] = p2[p1[k]], which in SymPy is p1_sp * p2_sp
    comp_ax = ax.group.compose(p1_ax, p2_ax)
    comp_sp = p1_sp * p2_sp
    assert [comp_ax[i] for i in range(n)] == list(comp_sp.array_form)

    # 3. Sign homomorphism: sgn(p1 o p2) == sgn(p1) * sgn(p2)
    assert ax.group.signature(comp_ax) == sgn1_ax * sgn2_ax

    # 4. Inverse: invert(p1) matches ~p1_sp and compose(p1, invert(p1)) == identity
    inv1_ax = ax.group.invert(p1_ax)
    inv1_sp = ~p1_sp
    assert [inv1_ax[i] for i in range(n)] == list(inv1_sp.array_form)
    assert ax.group.compose(p1_ax, inv1_ax) == {i: i for i in range(n)}


@pytest.mark.verification
@pytest.mark.differential
def test_differential_finite_groups_and_conjugacy_classes_vs_sympy() -> None:
    """Verify FiniteGroup, FiniteCommGroup, conjugacy classes, and centers vs sympy.combinatorics.named_groups."""
    from sympy.combinatorics.named_groups import AlternatingGroup as SymPyAlternatingGroup
    from sympy.combinatorics.named_groups import CyclicGroup as SymPyCyclicGroup
    from sympy.combinatorics.named_groups import DihedralGroup as SymPyDihedralGroup
    from sympy.combinatorics.named_groups import SymmetricGroup as SymPySymmetricGroup

    from algebrax.algebra import CommGroup, Group
    from algebrax.group import (
        FiniteCommGroup,
        alternating_group,
        cyclic_group,
        dihedral_group,
        symmetric_group,
    )
    from algebrax.verification import verify_comm_group_laws, verify_group_laws

    cases = [
        (cyclic_group(5), SymPyCyclicGroup(5)),
        (cyclic_group(6), SymPyCyclicGroup(6)),
        (dihedral_group(2), SymPyDihedralGroup(2)),
        (dihedral_group(3), SymPyDihedralGroup(3)),
        (dihedral_group(4), SymPyDihedralGroup(4)),
        (symmetric_group(2), SymPySymmetricGroup(2)),
        (symmetric_group(3), SymPySymmetricGroup(3)),
        (symmetric_group(4), SymPySymmetricGroup(4)),
        (alternating_group(3), SymPyAlternatingGroup(3)),
        (alternating_group(4), SymPyAlternatingGroup(4)),
    ]

    for grp_ax, grp_sp in cases:
        assert grp_ax.order == int(grp_sp.order())
        assert grp_ax.is_abelian() == bool(grp_sp.is_abelian)
        assert isinstance(grp_ax, Group)
        assert isinstance(grp_ax, FiniteCommGroup) is bool(grp_sp.is_abelian)
        assert isinstance(grp_ax, CommGroup) is bool(grp_sp.is_abelian)

        # Conjugacy class size multisets must match SymPy exactly
        sizes_ax = sorted(len(c) for c in grp_ax.conjugacy_classes())
        sizes_sp = sorted(len(c) for c in grp_sp.conjugacy_classes())
        assert sizes_ax == sizes_sp

        # Center order and abelian witness
        center_ax = grp_ax.center()
        assert isinstance(center_ax, FiniteCommGroup)
        assert center_ax.order == int(grp_sp.center().order())

        # Exhaustive group law checks (with CommGroup axioms on abelian groups)
        samples = grp_ax.elements if grp_ax.order >= 3 else (*grp_ax.elements, grp_ax.identity)
        if isinstance(grp_ax, CommGroup):
            assert all(verify_comm_group_laws(grp_ax, samples).values())
        else:
            assert all(verify_group_laws(grp_ax, samples).values())


@pytest.mark.verification
@pytest.mark.differential
def test_differential_group_representations_and_character_tables_vs_numpy_sympy() -> None:  #noqa: C901
    """Verify CharacterTable class invariants vs SymPy and Maschke isotypic projectors via NumPy."""
    from sympy.combinatorics.named_groups import AlternatingGroup as SymPyAlternatingGroup
    from sympy.combinatorics.named_groups import CyclicGroup as SymPyCyclicGroup
    from sympy.combinatorics.named_groups import DihedralGroup as SymPyDihedralGroup
    from sympy.combinatorics.named_groups import SymmetricGroup as SymPySymmetricGroup

    from algebrax.group import (
        FiniteGroup,
        alternating_group,
        cyclic_group,
        dihedral_group,
        quaternion_group,
        symmetric_group,
    )
    from algebrax.rep import (
        CharacterTable,
        a4_character_table,
        cyclic_character_table,
        dihedral_character_table,
        is_intertwiner,
        isotypic_projector,
        q8_character_table,
        regular_rep,
        reynolds_average,
        s3_character_table,
        s4_character_table,
    )
    from algebrax.verification import (
        verify_burnside_dimension_formula,
        verify_representation_homomorphism,
        verify_schur_orthogonality,
    )

    def _class_index_map(grp: FiniteGroup[Any], tbl: CharacterTable, name: str) -> dict[Any, int]:
        if name == 'C5':
            return {g: int(g) for g in grp.elements}
        if name == 'S3':
            return {g: tbl.classes.index({1: '1^3', 2: '2^1 1^1', 3: '3^1'}[grp.order_of(g)]) for g in grp.elements}
        if name == 'S4':
            size_of = {g: len(cls) for cls in grp.conjugacy_classes() for g in cls}
            mapping: dict[Any, int] = {}
            for g in grp.elements:
                ord_g, sz_g = grp.order_of(g), size_of[g]
                if ord_g == 1:
                    col = '1^4'
                elif ord_g == 2:
                    col = '2 1^2' if sz_g == 6 else '2^2'
                elif ord_g == 3:
                    col = '3 1'
                else:
                    col = '4'
                mapping[g] = tbl.classes.index(col)
            return mapping
        if name == 'A4':
            classes = grp.conjugacy_classes()
            c_123 = next(c for c in classes if (1, 2, 0, 3) in c)
            c_132 = next(c for c in classes if (2, 0, 1, 3) in c)
            mapping = {}
            for g in grp.elements:
                if g == grp.identity:
                    col = 'e'
                elif grp.order_of(g) == 2:
                    col = '(12)(34)'
                elif g in c_123:
                    col = '(123)'
                else:
                    assert g in c_132
                    col = '(132)'
                mapping[g] = tbl.classes.index(col)
            return mapping
        if name == 'D4':
            label_for = {
                'r0': 'e',
                'r1': 'r^1',
                'r3': 'r^1',
                'r2': 'r^2',
                's0': 's_even',
                's2': 's_even',
                's1': 's_odd',
                's3': 's_odd',
            }
            return {g: tbl.classes.index(label_for[str(g)]) for g in grp.elements}
        label_for_q8 = {
            '1': '{1}',
            '-1': '{-1}',
            'i': '{+-i}',
            '-i': '{+-i}',
            'j': '{+-j}',
            '-j': '{+-j}',
            'k': '{+-k}',
            '-k': '{+-k}',
        }
        return {g: tbl.classes.index(label_for_q8[str(g)]) for g in grp.elements}

    table_pairs: list[tuple[str, CharacterTable, FiniteGroup[Any], Any]] = [
        ('C5', cyclic_character_table(5), cyclic_group(5), SymPyCyclicGroup(5)),
        ('S3', s3_character_table(), symmetric_group(3), SymPySymmetricGroup(3)),
        ('S4', s4_character_table(), symmetric_group(4), SymPySymmetricGroup(4)),
        ('A4', a4_character_table(), alternating_group(4), SymPyAlternatingGroup(4)),
        ('D4', dihedral_character_table(4), dihedral_group(4), SymPyDihedralGroup(4)),
        ('Q8', q8_character_table(), quaternion_group(), None),
    ]

    for tag, tbl, grp, sym_g in table_pairs:
        assert tbl.group_order == grp.order
        assert all(verify_schur_orthogonality(tbl).values())
        assert all(verify_burnside_dimension_formula(tbl).values())
        if sym_g is not None:
            assert sorted(tbl.class_sizes) == sorted(len(c) for c in sym_g.conjugacy_classes())

        # Regular representation: complete orthogonal idempotent projector decomposition in NumPy
        reg = regular_rep(grp)
        assert all(verify_representation_homomorphism(reg, grp).values())

        d = reg.dimension
        assert d == grp.order
        class_map = _class_index_map(grp, tbl, tag)

        projectors_np: list[np.ndarray] = []
        for irrep_idx, _irrep_name in enumerate(tbl.irreps):
            row = tbl.table[irrep_idx]
            dim_chi = round(complex(row[0]).real)
            chi_map = {g: complex(row[class_map[g]]) for g in grp.elements}
            p_sparse = isotypic_projector(reg, grp, chi_map, irrep_dim=dim_chi)
            p_np = np.asarray(ax.converters.to_numpy(p_sparse, shape=(d, d)), dtype=np.complex128)

            # Idempotence P^2 == P and Burnside multiplicity Tr(P) == d_chi^2 in regular rep
            np.testing.assert_allclose(p_np @ p_np, p_np, rtol=1e-9, atol=1e-9)
            assert math.isclose(float(np.real(np.trace(p_np))), float(dim_chi**2), rel_tol=1e-9, abs_tol=1e-9)
            assert is_intertwiner(p_sparse, reg, reg, grp)
            projectors_np.append(p_np)

        # Completeness sum_i P_i == I_d and pairwise orthogonality P_i P_j == 0
        np.testing.assert_allclose(sum(projectors_np), np.eye(d, dtype=np.complex128), rtol=1e-9, atol=1e-9)
        for i, pi in enumerate(projectors_np):
            for j, pj in enumerate(projectors_np):
                if i != j:
                    np.testing.assert_allclose(pi @ pj, np.zeros((d, d), dtype=np.complex128), atol=1e-9)

        # Reynolds average of an arbitrary seed matrix must intertwine reg with itself
        seed_mat = {r: {c: float((r + 2 * c) % 5 - 2) for c in range(d)} for r in range(d)}
        avg_op = reynolds_average(seed_mat, reg, reg, grp)
        assert is_intertwiner(avg_op, reg, reg, grp)


# =============================================================================
# 6. Symbolic Polynomials & Divided-Power Autodiff vs. SymPy Poly & diff
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_polynomial_semiring_over_fraction_vs_sympy_poly() -> None:
    """Verify PolynomialAlgebra over exact Fraction matches sympy.Poly over Q[x] with zero error."""
    x = sp.Symbol('x')
    poly_sr = PolynomialAlgebra(StandardSemiring(Fraction))

    p = {0: Fraction(1, 2), 2: Fraction(-3, 4), 4: Fraction(5, 3)}
    q = {1: Fraction(2, 5), 2: Fraction(3, 4), 3: Fraction(-1, 2)}

    p_sp = sp.Poly(
        sum(sp.Rational(c.numerator, c.denominator) * (x**deg) for deg, c in p.items()),
        x,
        domain='QQ',
    )
    q_sp = sp.Poly(
        sum(sp.Rational(c.numerator, c.denominator) * (x**deg) for deg, c in q.items()),
        x,
        domain='QQ',
    )

    add_ax = poly_sr.add(p, q)
    mul_ax = poly_sr.mul(p, q)
    pow_ax = poly_sr.power(p, 3)

    for res_ax, res_sp in [(add_ax, p_sp + q_sp), (mul_ax, p_sp * q_sp), (pow_ax, p_sp**3)]:
        expected = {int(deg): _sympy_rational_to_fraction(coeff) for (deg,), coeff in res_sp.terms() if coeff != 0}
        assert res_ax == expected


@pytest.mark.verification
@pytest.mark.differential
def test_differential_autodiff_semirings_vs_sympy_derivatives() -> None:
    """Verify DualNumberAlgebra, BinomialConvolutionSemiring, and MultivariateBinomialConvolution vs sympy.diff."""
    x, y = sp.symbols('x y')

    # 1. 1D Higher-Order Autodiff via BinomialConvolutionSemiring(order=4) and DualNumberAlgebra
    # Evaluate f(x) = (2 + x)^3 * (1 - 2x)^2 + 3 * (2 + x)^2 at x0 = 1.25
    f_sym = (2 + x) ** 3 * (1 - 2 * x) ** 2 + 3 * (2 + x) ** 2
    x0 = 1.25

    # In BinomialConvolutionSemiring, multiplication already includes the binomial coefficients (k choose j),
    # which is the Divided Power Algebra where element k stores the k-th derivative d^k f / dx^k directly!
    # Variable seed for x at x0 has value x0 and 1st derivative 1.0: (x0, 1.0, 0.0, 0.0, 0.0).
    order = 4
    binom_sr = BinomialConvolutionSemiring(order=order)
    x_var = (x0, 1.0, 0.0, 0.0, 0.0)
    c_two = (2.0, 0.0, 0.0, 0.0, 0.0)
    c_one = (1.0, 0.0, 0.0, 0.0, 0.0)
    c_neg2 = (-2.0, 0.0, 0.0, 0.0, 0.0)
    c_three = (3.0, 0.0, 0.0, 0.0, 0.0)

    two_plus_x = binom_sr.add(c_two, x_var)
    one_minus_2x = binom_sr.add(c_one, binom_sr.mul(c_neg2, x_var))
    term1 = binom_sr.mul(binom_sr.power(two_plus_x, 3), binom_sr.power(one_minus_2x, 2))
    term2 = binom_sr.mul(c_three, binom_sr.power(two_plus_x, 2))
    f_jets = binom_sr.add(term1, term2)

    for k in range(order + 1):
        deriv_sp = float(sp.diff(f_sym, x, k).subs(x, x0))
        assert math.isclose(f_jets[k], deriv_sp, rel_tol=1e-11, abs_tol=1e-11)

    # Also verify DualNumberAlgebra matches 0th and 1st derivatives
    dual_sr = DualNumberAlgebra()
    x_dual = (x0, 1.0)
    d_two_plus_x = dual_sr.add((2.0, 0.0), x_dual)
    d_one_minus_2x = dual_sr.add((1.0, 0.0), dual_sr.mul((-2.0, 0.0), x_dual))
    f_dual = dual_sr.add(
        dual_sr.mul(dual_sr.power(d_two_plus_x, 3), dual_sr.power(d_one_minus_2x, 2)),
        dual_sr.mul((3.0, 0.0), dual_sr.power(d_two_plus_x, 2)),
    )
    assert math.isclose(f_dual[0], f_jets[0], rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(f_dual[1], f_jets[1], rel_tol=1e-12, abs_tol=1e-12)

    # 2. 2D Partial Derivatives via MultivariateBinomialConvolutionSemiring(num_vars=2, order=3)
    # Evaluate g(x, y) = (x + 2y)^2 * (3x - y) at (x0, y0) = (1.5, -0.75)
    g_sym = (x + 2 * y) ** 2 * (3 * x - y)
    x0_2d, y0_2d = 1.5, -0.75
    mv_sr = MultivariateBinomialConvolutionSemiring(num_vars=2, order=3)
    x_mv = {(0, 0): x0_2d, (1, 0): 1.0}
    y_mv = {(0, 0): y0_2d, (0, 1): 1.0}

    x_plus_2y = mv_sr.add(x_mv, mv_sr.mul({(0, 0): 2.0}, y_mv))
    three_x_minus_y = mv_sr.add(mv_sr.mul({(0, 0): 3.0}, x_mv), mv_sr.mul({(0, 0): -1.0}, y_mv))
    g_jets = mv_sr.mul(mv_sr.power(x_plus_2y, 2), three_x_minus_y)

    for a1 in range(4):
        for a2 in range(4 - a1):
            partial_sp = float(sp.diff(g_sym, (x, a1), (y, a2)).subs({x: x0_2d, y: y0_2d}))
            assert math.isclose(g_jets.get((a1, a2), 0.0), partial_sp, rel_tol=1e-11, abs_tol=1e-11)


# =============================================================================
# 10. EP-0204: Non-Associative & Quantum Algebras vs SymPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_octonion_quaternion_subalgebra_vs_sympy_quaternion() -> None:
    """Verify OctonionAlgebra restricted to quaternion subalgebra (e0, e1, e2, e3) matches sympy.algebras.quaternion."""
    from sympy.algebras.quaternion import Quaternion as SymPyQuaternion

    from algebrax.algebra._non_assoc import OctonionAlgebra

    oct_alg = OctonionAlgebra()

    # Quaternion sub-elements (e0, e1, e2, e3)
    # in Octonion: basis indices 0..7
    q1_vals = [2.0, -1.5, 3.0, 0.5]
    q2_vals = [1.0, 2.0, -0.5, 4.0]

    o1 = {i: q1_vals[i] for i in range(4)}
    o2 = {i: q2_vals[i] for i in range(4)}

    o_prod = oct_alg.mul(o1, o2)

    # SymPy Quaternion (w, x, y, z)
    sq1 = SymPyQuaternion(*q1_vals)
    sq2 = SymPyQuaternion(*q2_vals)
    sq_prod = sq1 * sq2

    assert math.isclose(o_prod.get(0, 0.0), float(sq_prod.a), rel_tol=1e-12)
    assert math.isclose(o_prod.get(1, 0.0), float(sq_prod.b), rel_tol=1e-12)
    assert math.isclose(o_prod.get(2, 0.0), float(sq_prod.c), rel_tol=1e-12)
    assert math.isclose(o_prod.get(3, 0.0), float(sq_prod.d), rel_tol=1e-12)
    for i in range(4, 8):
        assert math.isclose(o_prod.get(i, 0.0), 0.0, abs_tol=1e-12)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_symmetric_matrix_jordan_product_vs_sympy_matrix() -> None:
    """Verify SymmetricMatrixJordanAlgebra Jordan product (A B + B A) / 2 against SymPy Matrix."""
    from algebrax.algebra._non_assoc import SymmetricMatrixJordanAlgebra

    jordan_alg = SymmetricMatrixJordanAlgebra()

    # Symmetric 3x3 matrices
    a_dense = [
        [2.0, 1.0, -1.0],
        [1.0, 3.0, 0.5],
        [-1.0, 0.5, 4.0],
    ]
    b_dense = [
        [1.5, -0.5, 2.0],
        [-0.5, 2.0, 1.0],
        [2.0, 1.0, -1.0],
    ]

    a_sp = {i: {j: a_dense[i][j] for j in range(3)} for i in range(3)}
    b_sp = {i: {j: b_dense[i][j] for j in range(3)} for i in range(3)}

    prod_ax = jordan_alg.mul(a_sp, b_sp)

    # SymPy Matrix computation
    sp_a = sp.Matrix(a_dense)
    sp_b = sp.Matrix(b_dense)
    sp_jordan = (sp_a * sp_b + sp_b * sp_a) / 2

    for i in range(3):
        for j in range(3):
            val_ax = prod_ax.get(i, {}).get(j, 0.0)
            val_sp = float(sp_jordan[i, j])
            assert math.isclose(val_ax, val_sp, rel_tol=1e-12, abs_tol=1e-12)


# =============================================================================
# 10. Lie Algebra Representations, Exp Map & Clebsch-Gordan vs. SymPy / SciPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_clebsch_gordan_and_lie_expm_vs_sympy_scipy() -> None:
    """Verify sparse Clebsch-Gordan tensors vs. sympy.physics.quantum.cg.CG and exp_map vs. scipy.linalg.expm."""
    from scipy.linalg import expm as scipy_expm
    from sympy.physics.quantum.cg import CG

    from algebrax.rep.lie import (
        clebsch_gordan_coefficient,
        clebsch_gordan_tensor,
        spin_representation,
    )

    # 1. Exhaustive differential comparison of CG coefficients against SymPy CG oracle
    for j1_h, j2_h in [(1, 1), (2, 1), (2, 2), (3, 2)]:
        cg_tensor = clebsch_gordan_tensor(j1_h, j2_h)
        sympy_nonzero: set[tuple[tuple[int, int], int, int]] = set()
        for j_h in range(abs(j1_h - j2_h), j1_h + j2_h + 1, 2):
            for m_h in range(-j_h, j_h + 1, 2):
                for m1_h in range(-j1_h, j1_h + 1, 2):
                    m2_h = m_h - m1_h
                    if abs(m2_h) > j2_h:
                        continue
                    sp_val = float(
                        CG(
                            sp.Rational(j1_h, 2),
                            sp.Rational(m1_h, 2),
                            sp.Rational(j2_h, 2),
                            sp.Rational(m2_h, 2),
                            sp.Rational(j_h, 2),
                            sp.Rational(m_h, 2),
                        )
                        .doit()
                        .evalf()
                    )
                    ax_val = clebsch_gordan_coefficient(j1_h, m1_h, j2_h, m2_h, j_h, m_h)
                    assert math.isclose(ax_val, sp_val, rel_tol=1e-12, abs_tol=1e-12)
                    if abs(sp_val) > 1e-14:
                        sympy_nonzero.add(((j_h, m_h), m1_h, m2_h))
                        assert math.isclose(
                            cg_tensor[((j_h, m_h), m1_h, m2_h)],
                            sp_val,
                            rel_tol=1e-12,
                            abs_tol=1e-12,
                        )
        assert set(cg_tensor.keys()) == sympy_nonzero

    # 2. Differential comparison of ExplicitLieRep.exp_map against scipy.linalg.expm
    rng = np.random.default_rng(21101)
    for j_h in (1, 2, 3):
        rep_j = spin_representation(j_h, form='su2')
        dim = rep_j.dimension
        coeffs = {k: float(v) for k, v in enumerate(rng.normal(0.0, 1.5, size=3))}
        rho_x_np = ax.converters.to_numpy(rep_j.evaluate(coeffs), shape=(dim, dim))
        exp_ax_np = ax.converters.to_numpy(rep_j.exp_map(coeffs), shape=(dim, dim))
        exp_sp_np = scipy_expm(rho_x_np)
        np.testing.assert_allclose(exp_ax_np, exp_sp_np, rtol=1e-11, atol=1e-11)


# =============================================================================
# 11. Invariant Theory (Molien Series) & Cubic Casimir Invariants vs. SymPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_molien_series_and_cubic_casimir_vs_sympy() -> None:
    """Verify compute_molien_series and cubic_casimir_tensor/operator against exact SymPy oracles."""
    from algebrax.group import dihedral_group, quaternion_group, symmetric_group
    from algebrax.lie.classical import sl_n
    from algebrax.rep import (
        compute_molien_series,
        cubic_casimir_operator,
        cubic_casimir_tensor,
        defining_representation,
        dihedral_rep,
        quaternion_rep,
        symmetric_defining_rep,
    )

    t = sp.Symbol('t')
    max_deg = 12

    def _to_sympy_mat(sparse_mat: dict[int, dict[int, Any]], n: int) -> sp.Matrix:
        rows: list[list[Any]] = []
        for i in range(n):
            row_dict = sparse_mat.get(i, {})
            row: list[Any] = []
            for j in range(n):
                val = complex(row_dict.get(j, 0.0))
                re = sp.nsimplify(val.real, tolerance=1e-10, rational=False)
                im = sp.nsimplify(val.imag, tolerance=1e-10, rational=False)
                row.append(re + sp.I * im)
            rows.append(row)
        return sp.Matrix(rows)

    # 1. Molien series vs exact SymPy Taylor expansion of (1/|G|) sum_g 1 / det(I - t * rho(g))
    cases: list[tuple[Any, Any]] = [
        (dihedral_group(2), dihedral_rep(2)),
        (dihedral_group(4), dihedral_rep(4)),
        (symmetric_group(3), symmetric_defining_rep(3)),
        (quaternion_group(), quaternion_rep()),
    ]
    for grp, rep in cases:
        molien = compute_molien_series(rep, grp)
        dim = rep.dimension
        eye_n = sp.eye(dim)
        sym_sum = sp.Integer(0)
        for g in grp.elements:
            m_sp = _to_sympy_mat(rep(g), dim)
            sym_sum += sp.Integer(1) / (eye_n - t * m_sp).det()
        sym_molien = sp.simplify(sym_sum / sp.Integer(grp.order))
        sym_poly = sp.series(sym_molien, t, 0, max_deg + 1).removeO().as_poly(t)
        expected_dims = [int(sym_poly.nth(d)) for d in range(max_deg + 1)]
        assert molien.series(max_deg) == expected_dims

    # 2. Cubic symmetric invariant tensor d_{ijk} and operator C_3 on sl(3) vs exact SymPy Matrix trace
    alg = sl_n(3)
    fund = defining_representation(alg)
    dual = fund.dual()
    d_ax = cubic_casimir_tensor(alg)

    sp_gens = [_to_sympy_mat(fund(i), 3) for i in range(alg.dim)]
    sp_d: dict[tuple[int, int, int], sp.Expr] = {}
    for i in range(alg.dim):
        for j in range(alg.dim):
            for k in range(alg.dim):
                val_sp = (sp_gens[i] * (sp_gens[j] * sp_gens[k] + sp_gens[k] * sp_gens[j])).trace()
                if val_sp != 0:
                    sp_d[(i, j, k)] = val_sp
                    assert math.isclose(
                        float(complex(d_ax[(i, j, k)]).real),
                        float(val_sp),
                        rel_tol=1e-11,
                        abs_tol=1e-11,
                    )
    assert set(d_ax.keys()) == set(sp_d.keys())

    # Exact SymPy C_3 on fundamental 3 and dual 3-bar via inverse Killing metric
    killing_sp = _to_sympy_mat(alg.killing_matrix(), alg.dim)
    killing_inv_sp = killing_sp.inv()
    # Raise indices d^{ijk} = sum_{a,b,c} g^{ia} g^{jb} g^{kc} d_{abc}
    c3_fund_sp = sp.zeros(3, 3)
    for (a, b, c), d_abc in sp_d.items():
        # Contract g^{ia} T_i = sum_i g^{ia} T_i
        ta = sum((killing_inv_sp[i, a] * sp_gens[i] for i in range(alg.dim)), sp.zeros(3, 3))
        tb = sum((killing_inv_sp[j, b] * sp_gens[j] for j in range(alg.dim)), sp.zeros(3, 3))
        tc = sum((killing_inv_sp[k, c] * sp_gens[k] for k in range(alg.dim)), sp.zeros(3, 3))
        c3_fund_sp += d_abc * (ta * tb * tc)

    c3_fund_ax = cubic_casimir_operator(fund, d_tensor=d_ax)
    c3_dual_ax = cubic_casimir_operator(dual, d_tensor=d_ax)
    for r in range(3):
        for c in range(3):
            expected_val = float(c3_fund_sp[r, c])
            got_fund = float(complex(c3_fund_ax.get(r, {}).get(c, 0.0)).real)
            got_dual = float(complex(c3_dual_ax.get(r, {}).get(c, 0.0)).real)
            assert math.isclose(got_fund, expected_val, rel_tol=1e-10, abs_tol=1e-10)
            assert math.isclose(got_dual, -expected_val, rel_tol=1e-10, abs_tol=1e-10)


# =============================================================================
# 12. Quantum Groups U_q(sl_2), Yang-Baxter Equation & Jones Polynomial vs. SymPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_quantum_groups_yang_baxter_and_jones_vs_sympy() -> None:
    """Verify QuantumSL2 spin-j reps, universal R-matrix QYBE, and Jones polynomial against SymPy."""
    import cmath

    from algebrax.rep import (
        QuantumSL2,
        jones_polynomial_eval,
        universal_r_matrix_sl2_fundamental,
    )

    q = sp.Symbol('q')
    t = q ** (-2)

    def _q_int(n: int) -> sp.Expr:
        return sp.simplify((q**n - q ** (-n)) / (q - 1 / q))

    # 1. Symbolic SymPy verification of the 4x4 fundamental R-matrix QYBE
    r_sp = sp.Matrix(
        [
            [q, 0, 0, 0],
            [0, 1, 0, 0],
            [0, q - 1 / q, 1, 0],
            [0, 0, 0, q],
        ]
    )
    eye2 = sp.eye(2)
    r12_sp = sp.kronecker_product(r_sp, eye2)
    r23_sp = sp.kronecker_product(eye2, r_sp)
    r13_sp = sp.zeros(8, 8)
    for r_op in range(4):
        i, k = divmod(r_op, 2)
        for c_op in range(4):
            val = r_sp[r_op, c_op]
            if val != 0:
                ip, kp = divmod(c_op, 2)
                for j in range(2):
                    r13_sp[(i * 2 + j) * 2 + k, (ip * 2 + j) * 2 + kp] = val

    qybe_diff = sp.simplify(r12_sp * r13_sp * r23_sp - r23_sp * r13_sp * r12_sp)
    assert qybe_diff == sp.zeros(8, 8)

    # Compare numerical evaluation against AlgebraX sparse R-matrix and spin-j modules
    q_probes = [1.35 + 0.0j, cmath.exp(0.37j), 1.12 * cmath.exp(-0.55j)]
    for q_val in q_probes:
        r_ax = universal_r_matrix_sl2_fundamental(q_val)
        r_eval = r_sp.subs(q, complex(q_val))
        for r_idx in range(4):
            for c_idx in range(4):
                got = complex(r_ax.get(r_idx, {}).get(c_idx, 0.0))
                exp = complex(r_eval[r_idx, c_idx].evalf())
                assert abs(got - exp) < 1e-12

    # 2. Symbolic SymPy U_q(sl_2) spin-j matrices (j = 1/2, 1, 3/2) & exact Drinfeld-Jimbo identities
    for j_halves in (1, 2, 3):
        dim = j_halves + 1
        e_sp = sp.zeros(dim, dim)
        f_sp = sp.zeros(dim, dim)
        k_sp = sp.zeros(dim, dim)
        for idx in range(dim):
            k_sp[idx, idx] = q ** (j_halves - 2 * idx)
        for p in range(1, dim):
            entry = sp.sqrt(_q_int(p) * _q_int(dim - p))
            e_sp[p - 1, p] = entry
            f_sp[p, p - 1] = entry

        assert sp.simplify(k_sp * e_sp * k_sp.inv() - (q**2) * e_sp) == sp.zeros(dim, dim)
        assert sp.simplify(k_sp * f_sp * k_sp.inv() - (q ** (-2)) * f_sp) == sp.zeros(dim, dim)
        assert sp.simplify(e_sp * f_sp - f_sp * e_sp - (k_sp - k_sp.inv()) / (q - 1 / q)) == sp.zeros(dim, dim)

        for q_val in q_probes:
            rep_ax = QuantumSL2(q_val).spin_representation(j_halves)
            for name, mat_sp in (('E', e_sp), ('F', f_sp), ('K', k_sp)):
                mat_eval = mat_sp.subs(q, complex(q_val))
                for r_idx in range(dim):
                    for c_idx in range(dim):
                        got = complex(rep_ax[name].get(r_idx, {}).get(c_idx, 0.0))
                        exp = complex(mat_eval[r_idx, c_idx].evalf())
                        assert abs(got - exp) < 1e-11

    # 3. Exact SymPy Laurent polynomial Jones invariants at t = q^{-2} vs jones_polynomial_eval
    knot_oracles: list[tuple[list[int], int, sp.Expr]] = [
        ([], 1, sp.Integer(1)),
        ([1], 2, sp.Integer(1)),
        ([], 2, -(q + 1 / q)),
        ([1, 1], 2, -(1 / q + q ** (-5))),
        ([1, 1, 1], 2, t + t**3 - t**4),
        ([-1, -1, -1], 2, t ** (-1) + t ** (-3) - t ** (-4)),
        ([1, -2, 1, -2], 3, t ** (-2) - t ** (-1) + 1 - t + t**2),
    ]
    for q_val in q_probes:
        for braid_word, strands, sym_expr in knot_oracles:
            got_v = jones_polynomial_eval(braid_word, strands, q_val)
            exp_v = complex(sym_expr.subs(q, complex(q_val)).evalf())
            assert abs(got_v - exp_v) < 1e-10


# =============================================================================
# 13. Quiver Representations, Tits Form & Gabriel's ADE Theorem vs. SymPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_quiver_tits_form_and_gabriel_ade_vs_sympy() -> None:
    """Verify Tits quadratic form, Gabriel ADE/tame/wild classification, and PathAlgebra against SymPy."""
    from algebrax.algebra import path_algebra
    from algebrax.rep import (
        Quiver,
        QuiverRepresentation,
        classify_representation_type,
        cycle_quiver,
        dynkin_quiver,
        gabriel_positive_roots,
        kronecker_quiver,
        tits_quadratic_form,
    )

    def _tree_arms(arms: tuple[int, int, int]) -> Quiver[int, str]:
        verts = [0]
        edges: list[tuple[str, int, int]] = []
        nxt = 1
        e_idx = 0
        for arm_len in arms:
            prev = 0
            for _ in range(arm_len):
                verts.append(nxt)
                edges.append((f'e{e_idx}', prev, nxt))
                prev = nxt
                nxt += 1
                e_idx += 1
        return Quiver.from_edges(verts, edges)

    # 1. Exact SymPy positive-definite / semidefinite / indefinite oracle vs Gabriel classification
    ade_quivers = [
        (dynkin_quiver('A', 2), 3),
        (dynkin_quiver('A', 4), 10),
        (dynkin_quiver('D', 4), 12),
        (dynkin_quiver('D', 5), 20),
        (dynkin_quiver('E6'), 36),
        (dynkin_quiver('E7'), 63),
        (dynkin_quiver('E8'), 120),
    ]
    for q_ade, expected_root_count in ade_quivers:
        c_sp = sp.Matrix(q_ade.symmetric_cartan_matrix())
        assert c_sp.is_positive_definite is True
        assert classify_representation_type(q_ade) == 'finite'
        roots = gabriel_positive_roots(q_ade)
        assert len(roots) == expected_root_count
        for r in roots:
            d_vec = sp.Matrix([r[v] for v in q_ade.vertices])
            q_sym = sp.Rational(1, 2) * (d_vec.T * c_sp * d_vec)[0, 0]
            assert q_sym == sp.Integer(1)
            assert tits_quadratic_form(q_ade, r) == 1

    # 2. Tame Euclidean quivers: exact SymPy positive semidefinite & singular (det == 0)
    tame_quivers = [
        cycle_quiver(1),
        kronecker_quiver(2),
        cycle_quiver(4),
        _tree_arms((2, 2, 2)),  # ~E6
        _tree_arms((1, 3, 3)),  # ~E7
        _tree_arms((1, 2, 5)),  # ~E8
    ]
    for q_tame in tame_quivers:
        c_sp = sp.Matrix(q_tame.symmetric_cartan_matrix())
        assert c_sp.is_positive_definite is False
        assert c_sp.is_positive_semidefinite is True
        assert c_sp.det() == 0
        assert classify_representation_type(q_tame) == 'tame'
        null_basis = c_sp.nullspace()
        assert len(null_basis) == 1
        delta_sp = null_basis[0]
        # Clear denominators to obtain exact integer radical vector
        lcm_den = sp.ilcm(1, *(sp.Rational(x).q for x in delta_sp))
        delta_int = [int(x * lcm_den) for x in delta_sp]
        assert tits_quadratic_form(q_tame, delta_int) == 0

    # 3. Wild quivers: exact SymPy indefinite (not positive semidefinite)
    wild_quivers = [
        kronecker_quiver(3),
        _tree_arms((1, 2, 6)),
        Quiver.from_edges((0, 1, 2, 3, 4, 5), [(f'e{i}', i, 0) for i in range(1, 6)]),
    ]
    for q_wild in wild_quivers:
        c_sp = sp.Matrix(q_wild.symmetric_cartan_matrix())
        assert c_sp.is_positive_semidefinite is False
        assert classify_representation_type(q_wild) == 'wild'

    # 4. PathAlgebra right-module representation action vs exact SymPy block matrices
    q_a3 = dynkin_quiver('A', 3)
    m0_sp = sp.Matrix([[1, 2], [0, -1]])
    m1_sp = sp.Matrix([[3, 4]])
    rep = QuiverRepresentation(
        quiver=q_a3,
        dimensions={0: 2, 1: 2, 2: 1},
        edge_maps={
            'e0': {0: {0: 1.0, 1: 2.0}, 1: {1: -1.0}},
            'e1': {0: {0: 3.0, 1: 4.0}},
        },
    )
    kq = path_algebra(q_a3)
    p01 = kq.mul(kq.arrow('e0'), kq.arrow('e1'))
    phi_p01 = kq.evaluate_in_rep(p01, rep)
    expected_block = m1_sp * m0_sp  # 1x2 matrix at rows [4], cols [0, 1]
    for col in range(2):
        assert math.isclose(
            float(phi_p01.get(4, {}).get(col, 0.0)),
            float(expected_block[0, col]),
            rel_tol=1e-12,
            abs_tol=1e-12,
        )


# =============================================================================
# 12. Multivariate Polynomial Algebras & Exact Gröbner Bases vs. SymPy
# =============================================================================


def _mpoly_to_sympy(poly: dict[tuple[int, ...], Any], syms: tuple[sp.Symbol, ...]) -> sp.Expr:
    """Convert an AlgebraX SparseMPoly over Fraction or int into a SymPy expression."""
    expr: sp.Expr = sp.Integer(0)
    for mon, coeff in poly.items():
        sp_c = (
            sp.Rational(coeff.numerator, coeff.denominator)
            if isinstance(coeff, Fraction)
            else sp.Integer(int(coeff))
        )
        term: sp.Expr = sp_c
        for sym, exp in zip(syms, mon, strict=True):
            if exp:
                term *= sym**exp
        expr += term
    return sp.expand(expr)


def _sympy_poly_to_mpoly_q(poly_sp: sp.Poly) -> dict[tuple[int, ...], Fraction]:
    """Convert a monic SymPy Poly over QQ to an AlgebraX SparseMPoly[Fraction]."""
    out: dict[tuple[int, ...], Fraction] = {}
    for mon, coeff in poly_sp.terms():
        rat = sp.Rational(coeff)
        if rat != 0:
            out[tuple(int(e) for e in mon)] = Fraction(int(rat.p), int(rat.q))
    return out


def _sympy_poly_to_mpoly_fp(poly_sp: sp.Poly, p: int) -> dict[tuple[int, ...], int]:
    """Convert a monic SymPy Poly over GF(p) to an AlgebraX SparseMPoly[int]."""
    out: dict[tuple[int, ...], int] = {}
    for mon, coeff in poly_sp.terms():
        val = int(coeff) % p
        if val != 0:
            out[tuple(int(e) for e in mon)] = val
    return out


@pytest.mark.verification
@pytest.mark.differential
@pytest.mark.parametrize('order', ['grevlex', 'grlex', 'lex'])
@pytest.mark.parametrize('method', ['f4', 'buchberger'])
def test_differential_groebner_basis_over_rationals_vs_sympy(order: Any, method: Any) -> None:
    """Verify exact 1-to-1 reduced monic Groebner basis agreement vs sympy.groebner over QQ."""
    q_field = ax.algebra.StandardField(Fraction)

    # 3-variable systems: TwistedCubic & Cyclic-3
    r3 = ax.algebra.MultivariatePolynomialAlgebra(q_field, n_vars=3, order=order)
    x, y, z = r3.gen(0), r3.gen(1), r3.gen(2)
    s3 = sp.symbols('x y z')

    systems_3 = [
        [r3.sub(r3.mul(x, x), y), r3.sub(r3.mul(x, y), z)],
        [
            r3.add(r3.add(x, y), z),
            r3.add(r3.add(r3.mul(x, y), r3.mul(y, z)), r3.mul(z, x)),
            r3.sub(r3.mul(r3.mul(x, y), z), r3.one),
        ],
    ]
    for gens in systems_3:
        gb_ax = ax.algebra.groebner_basis(r3, gens, method=method)
        gb_sp = sp.groebner([_mpoly_to_sympy(g, s3) for g in gens], *s3, order=order, domain=sp.QQ)
        expected = [_sympy_poly_to_mpoly_q(p) for p in gb_sp.polys]
        assert gb_ax == expected

    # 4-variable systems: Cyclic-4 & 2R-Robot-IK
    r4 = ax.algebra.MultivariatePolynomialAlgebra(q_field, n_vars=4, order=order)
    x4, y4, z4, w4 = (r4.gen(i) for i in range(4))
    s4 = sp.symbols('x y z w')

    cyclic4 = [
        r4.add(r4.add(x4, y4), r4.add(z4, w4)),
        r4.add(r4.add(r4.mul(x4, y4), r4.mul(y4, z4)), r4.add(r4.mul(z4, w4), r4.mul(w4, x4))),
        r4.add(
            r4.add(r4.mul(r4.mul(x4, y4), z4), r4.mul(r4.mul(y4, z4), w4)),
            r4.add(r4.mul(r4.mul(z4, w4), x4), r4.mul(r4.mul(w4, x4), y4)),
        ),
        r4.sub(r4.mul(r4.mul(x4, y4), r4.mul(z4, w4)), r4.one),
    ]
    robot_ik = [
        r4.sub(r4.add(r4.smul(Fraction(3), x4), r4.smul(Fraction(2), z4)), r4.const(Fraction(3))),
        r4.sub(r4.add(r4.smul(Fraction(3), y4), r4.smul(Fraction(2), w4)), r4.const(Fraction(2))),
        r4.sub(r4.add(r4.mul(x4, x4), r4.mul(y4, y4)), r4.one),
        r4.sub(r4.add(r4.mul(z4, z4), r4.mul(w4, w4)), r4.one),
    ]
    for gens in (cyclic4, robot_ik):
        gb_ax = ax.algebra.groebner_basis(r4, gens, method=method)
        gb_sp = sp.groebner([_mpoly_to_sympy(g, s4) for g in gens], *s4, order=order, domain=sp.QQ)
        expected = [_sympy_poly_to_mpoly_q(p) for p in gb_sp.polys]
        assert gb_ax == expected


@pytest.mark.verification
@pytest.mark.differential
@pytest.mark.parametrize('p', [7, 101])
@pytest.mark.parametrize('order', ['grevlex', 'lex'])
def test_differential_groebner_basis_over_finite_field_vs_sympy(p: int, order: Any) -> None:
    """Verify exact 1-to-1 reduced monic Groebner basis agreement vs sympy.groebner over GF(p)."""
    fp = ax.algebra.ModularField(p)
    r3 = ax.algebra.MultivariatePolynomialAlgebra(fp, n_vars=3, order=order)
    x, y, z = r3.gen(0), r3.gen(1), r3.gen(2)
    s3 = sp.symbols('x y z')

    cyclic3 = [
        r3.add(r3.add(x, y), z),
        r3.add(r3.add(r3.mul(x, y), r3.mul(y, z)), r3.mul(z, x)),
        r3.sub(r3.mul(r3.mul(x, y), z), r3.one),
    ]
    ideal = ax.algebra.GroebnerIdeal(r3, cyclic3)
    gb_sp = sp.groebner([_mpoly_to_sympy(g, s3) for g in cyclic3], *s3, order=order, domain=sp.GF(p))
    expected = [_sympy_poly_to_mpoly_fp(poly, p) for poly in gb_sp.polys]
    assert list(ideal.basis) == expected


@pytest.mark.verification
@pytest.mark.differential
def test_differential_multivariate_diff_gcd_sqf_and_poisson_vs_sympy() -> None:
    """Verify formal diff, univariate_gcd, square_free_part, and poisson_bracket against SymPy."""
    q_field = ax.algebra.StandardField(Fraction)
    ring = ax.algebra.MultivariatePolynomialAlgebra(q_field, n_vars=2)
    q_sym, p_sym = sp.symbols('q p')
    syms = (q_sym, p_sym)

    f = {
        (3, 1): Fraction(2, 3),
        (1, 2): Fraction(-5, 4),
        (0, 3): Fraction(7, 2),
        (0, 0): Fraction(-1),
    }
    g = {
        (2, 2): Fraction(3, 5),
        (1, 0): Fraction(-2),
        (0, 1): Fraction(4, 3),
    }
    f_sp = _mpoly_to_sympy(f, syms)
    g_sp = _mpoly_to_sympy(g, syms)

    # Partial derivatives
    assert _mpoly_to_sympy(ring.diff(f, 0), syms) == sp.expand(sp.diff(f_sp, q_sym))
    assert _mpoly_to_sympy(ring.diff(f, 1), syms) == sp.expand(sp.diff(f_sp, p_sym))

    # Symplectic Poisson bracket {f, g} = df/dq * dg/dp - df/dp * dg/dq
    pb_sp = sp.expand(sp.diff(f_sp, q_sym) * sp.diff(g_sp, p_sym) - sp.diff(f_sp, p_sym) * sp.diff(g_sp, q_sym))
    assert _mpoly_to_sympy(ring.poisson_bracket(f, g), syms) == pb_sp

    # Univariate GCD & square-free part
    x = ring.gen(0)
    u1 = ring.mul(ring.mul(ring.sub(x, ring.one), ring.sub(x, ring.one)), ring.add(x, ring.const(Fraction(2))))
    u2 = ring.mul(ring.sub(x, ring.one), ring.sub(x, ring.const(Fraction(3))))
    u1_sp = _mpoly_to_sympy(u1, syms)
    u2_sp = _mpoly_to_sympy(u2, syms)

    gcd_ax = _mpoly_to_sympy(ring.univariate_gcd(u1, u2, var_index=0), syms)
    assert gcd_ax == sp.expand(sp.Poly(sp.gcd(u1_sp, u2_sp), q_sym, domain=sp.QQ).monic().as_expr())

    sqf_ax = _mpoly_to_sympy(ring.square_free_part(u1, var_index=0), syms)
    assert sqf_ax == sp.expand(sp.Poly(sp.sqf_part(u1_sp), q_sym, domain=sp.QQ).monic().as_expr())


# =============================================================================
# 16. Affine Algebraic Varieties, Stickelberger Solvers & Morphisms vs. SymPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_variety_stickelberger_and_rational_solver_vs_sympy() -> None:
    """Verify Stickelberger & exact rational variety solvers against sympy.solve."""
    q_field = ax.algebra.StandardField(Fraction)
    r2 = ax.algebra.MultivariatePolynomialAlgebra(q_field, n_vars=2, order='grevlex')
    x, y = r2.gen(0), r2.gen(1)
    xs, ys = sp.symbols('x y')

    # 4-point intersection: x^2 + y^2 - 5 = 0, x*y - 2 = 0
    g1 = r2.sub(r2.add(r2.mul(x, x), r2.mul(y, y)), r2.const(Fraction(5)))
    g2 = r2.sub(r2.mul(x, y), r2.const(Fraction(2)))
    var = ax.variety.AffineVariety(r2, [g1, g2])

    sp_sols = sorted(
        (float(sol[xs]), float(sol[ys]))
        for sol in sp.solve([xs**2 + ys**2 - 5, xs * ys - 2], [xs, ys], dict=True)
    )
    ax_sols = ax.variety.solve_zero_dimensional(var)
    ax_rat = ax.variety.solve_exact_rational(var)

    assert len(ax_sols) == len(sp_sols)
    for (ax_x, ax_y), (sp_x, sp_y) in zip(ax_sols, sp_sols, strict=True):
        assert math.isclose(float(ax_x.real), sp_x, abs_tol=1e-7)
        assert math.isclose(float(ax_y.real), sp_y, abs_tol=1e-7)
    assert [(float(p[0]), float(p[1])) for p in ax_rat] == sp_sols


@pytest.mark.verification
@pytest.mark.differential
def test_differential_variety_jacobian_elimination_and_syzygy_vs_sympy() -> None:
    """Verify Jacobian evaluation, elimination ideals, and GIT syzygy variety against SymPy."""
    q_field = ax.algebra.StandardField(Fraction)
    r3 = ax.algebra.MultivariatePolynomialAlgebra(q_field, n_vars=3, order='grevlex')
    x, y, z = r3.gen(0), r3.gen(1), r3.gen(2)
    xs, ys, zs = sp.symbols('x y z')

    # Twisted cubic V(x^2 - y, x^3 - z)
    tc_gens = [r3.sub(r3.mul(x, x), y), r3.sub(r3.mul(r3.mul(x, x), x), z)]
    tc = ax.variety.AffineVariety(r3, tc_gens)

    # 1. Jacobian at (2, 4, 8) matches sympy.Matrix.jacobian on the reduced basis
    pt_q = (Fraction(2), Fraction(4), Fraction(8))
    jac_ax = tc.jacobian_at(pt_q)
    basis_sp = sp.Matrix([_mpoly_to_sympy(g, (xs, ys, zs)) for g in tc.ideal.basis])
    jac_sp = basis_sp.jacobian([xs, ys, zs]).subs({xs: 2, ys: 4, zs: 8})
    for r_idx in range(jac_sp.rows):
        for c_idx in range(jac_sp.cols):
            got = jac_ax.get(r_idx, {}).get(c_idx, Fraction(0))
            assert sp.Rational(got.numerator, got.denominator) == jac_sp[r_idx, c_idx]

    # 2. Elimination of x matches SymPy lex Groebner elimination
    proj = tc.eliminate(1)
    sp_lex = sp.groebner([xs**2 - ys, xs**3 - zs], xs, ys, zs, order='lex', domain=sp.QQ)
    sp_elim = [p for p in sp_lex.polys if p.degree(xs) == 0]
    assert len(proj.ideal.basis) == len(sp_elim) == 1
    assert _mpoly_to_sympy(proj.ideal.basis[0], (ys, zs)) == sp.expand(sp_elim[0].as_expr())

    # 3. Syzygy variety for Z_2 invariants (x^2, y^2, x*y) vs SymPy implicitization
    r2 = ax.algebra.MultivariatePolynomialAlgebra(q_field, n_vars=2, order='grevlex')
    x2, y2 = r2.gen(0), r2.gen(1)
    syz = ax.variety.syzygy_variety(r2, [r2.mul(x2, x2), r2.mul(y2, y2), r2.mul(x2, y2)])
    u1, u2, u3 = sp.symbols('u1 u2 u3')
    sp_syz_gb = sp.groebner([u1 - xs**2, u2 - ys**2, u3 - xs * ys], xs, ys, u1, u2, u3, order='lex', domain=sp.QQ)
    sp_syz = [p for p in sp_syz_gb.polys if p.degree(xs) == 0 and p.degree(ys) == 0]
    assert len(syz.ideal.basis) == len(sp_syz) == 1
    assert _mpoly_to_sympy(syz.ideal.basis[0], (u1, u2, u3)) == sp.expand(sp_syz[0].as_expr())
