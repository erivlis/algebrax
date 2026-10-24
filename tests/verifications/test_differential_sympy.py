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
from algebrax.matrix.academic import PerformanceWarning
from algebrax.semiring import (
    BinomialConvolutionSemiring,
    CliffordSemiring,
    DualNumberSemiring,
    GaloisFieldSemiring,
    GeneralizedCliffordSemiring,
    MultivariateBinomialConvolutionSemiring,
    PolynomialSemiring,
    QuantumCliffordSemiring,
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
    """Verify GaloisFieldSemiring GF(2^8) and GF(3^3) against SymPy Poly mod irreducible polynomial."""
    x = sp.Symbol('x')

    # 1. AES Field GF(2^8) modulo P(x) = x^8 + x^4 + x^3 + x + 1
    aes_poly_tuple = (1, 1, 0, 1, 1, 0, 0, 0, 1)
    gf_aes = GaloisFieldSemiring(p=2, irreduc_poly=aes_poly_tuple)
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
    gf_27 = GaloisFieldSemiring(p=3, irreduc_poly=gf_27_tuple)
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
    cl_spacetime = CliffordSemiring(p=1, q=3, r=0)
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
    gca = GeneralizedCliffordSemiring(n_order=3, num_generators=2)
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
    q_sr = QuantumCliffordSemiring(q=q_param, num_generators=2)
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


# =============================================================================
# 6. Symbolic Polynomials & Divided-Power Autodiff vs. SymPy Poly & diff
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_polynomial_semiring_over_fraction_vs_sympy_poly() -> None:
    """Verify PolynomialSemiring over exact Fraction matches sympy.Poly over Q[x] with zero error."""
    x = sp.Symbol('x')
    poly_sr = PolynomialSemiring(StandardSemiring(Fraction))

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
    """Verify DualNumberSemiring, BinomialConvolutionSemiring, and MultivariateBinomialConvolution vs sympy.diff."""
    x, y = sp.symbols('x y')

    # 1. 1D Higher-Order Autodiff via BinomialConvolutionSemiring(order=4) and DualNumberSemiring
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

    # Also verify DualNumberSemiring matches 0th and 1st derivatives
    dual_sr = DualNumberSemiring()
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
