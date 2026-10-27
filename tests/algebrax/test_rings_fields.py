"""
Tests for Rings, Fields, Modules, and Exact Matrix Solvers (EP-0191).

Tests NonAssocRing, Ring, CommRing, DivisionRing, Field, StandardField,
ModularField, Semimodule, Module, VectorSpace, Algebra, and exact polymorphic
matrix solvers (lu_decompose, solve_triangular, solve, det, inv).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from algebrax.algebra import (
    Algebra,
    CommRing,
    CommutativeRing,
    DivisionRing,
    Field,
    ModularField,
    Module,
    NonAssocAlgebra,
    NonAssocRing,
    Ring,
    Semimodule,
    StandardField,
    VectorSpace,
)
from algebrax.matrix import (
    SingularMatrixError,
    det,
    dot,
    inv,
    lu,
    lu_decompose,
    recompose_lu,
    solve,
    solve_triangular,
)
from algebrax.verification import (
    verify_algebra_laws,
    verify_comm_ring_laws,
    verify_division_ring_laws,
    verify_field_laws,
    verify_module_laws,
    verify_non_assoc_ring_laws,
    verify_ring_laws,
    verify_semimodule_laws,
)

# =============================================================================
# 1. Structural Subtyping & Protocol Conformance
# =============================================================================


class IntegerRing:
    """Standard integer ring Z (unboxed ints)."""

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, a: int, b: int) -> int:
        return a + b

    def sub(self, a: int, b: int) -> int:
        return a - b

    def neg(self, a: int) -> int:
        return -a

    def mul(self, a: int, b: int) -> int:
        return a * b


class LieAlgebra3D:
    """3D Lie algebra (e.g. so(3)) with cross product as non-associative bracket."""

    @property
    def zero(self) -> tuple[float, float, float]:
        return (0.0, 0.0, 0.0)

    def add(self, a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    def neg(self, a: tuple[float, float, float]) -> tuple[float, float, float]:
        return (-a[0], -a[1], -a[2])

    def sub(self, a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    def mul(self, a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
        # Cross product [a, b] = a x b
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )


class SparseVectorModule:
    """Module of sparse vectors dict[str, int] over integer ring Z."""

    @property
    def zero(self) -> dict[str, int]:
        return {}

    def add(self, u: dict[str, int], v: dict[str, int]) -> dict[str, int]:
        res = {k: u.get(k, 0) + v.get(k, 0) for k in set(u) | set(v)}
        return {k: val for k, val in res.items() if val != 0}

    def neg(self, u: dict[str, int]) -> dict[str, int]:
        return {k: -val for k, val in u.items() if val != 0}

    def sub(self, u: dict[str, int], v: dict[str, int]) -> dict[str, int]:
        return self.add(u, self.neg(v))

    def smul(self, r: int, u: dict[str, int]) -> dict[str, int]:
        if r == 0:
            return {}
        return {k: r * val for k, val in u.items() if r * val != 0}


def test_structural_protocols():
    """Verify runtime_checkable protocol conformance across rings, fields, and modules."""
    z_ring = IntegerRing()
    assert isinstance(z_ring, NonAssocRing)
    assert isinstance(z_ring, Ring)
    assert isinstance(z_ring, CommRing)
    assert isinstance(z_ring, CommutativeRing)

    lie = LieAlgebra3D()
    assert isinstance(lie, NonAssocRing)
    # Lie algebra is not associative and has no identity 1, so not Ring
    assert not isinstance(lie, Ring)

    f_field = StandardField(Fraction)
    assert isinstance(f_field, NonAssocRing)
    assert isinstance(f_field, Ring)
    assert isinstance(f_field, CommRing)
    assert isinstance(f_field, DivisionRing)
    assert isinstance(f_field, Field)

    mod7 = ModularField(7)
    assert isinstance(mod7, DivisionRing)
    assert isinstance(mod7, Field)

    mod_vec = SparseVectorModule()
    assert isinstance(mod_vec, Semimodule)
    assert isinstance(mod_vec, Module)
    assert isinstance(mod_vec, VectorSpace)


# =============================================================================
# 2. Law Verification Engine
# =============================================================================


def test_ring_and_field_law_verifiers():
    """Verify axiomatic law verifiers for NonAssocRing, Ring, CommRing, DivisionRing, and Field."""
    z_ring = IntegerRing()
    samples_z = [-3, -1, 0, 1, 2, 5]
    res_z = verify_comm_ring_laws(z_ring, samples_z)
    assert all(res_z.values())

    q_field = StandardField(Fraction)
    samples_q = [Fraction(-3, 2), Fraction(0, 1), Fraction(1, 1), Fraction(2, 3), Fraction(5, 7)]
    res_q = verify_field_laws(q_field, samples_q)
    assert all(res_q.values())
    assert res_q['zero_division_guard'] is True

    f7 = ModularField(7)
    samples_f7 = [0, 1, 2, 3, 4, 5, 6]
    res_f7 = verify_field_laws(f7, samples_f7)
    assert all(res_f7.values())
    assert res_f7['zero_division_guard'] is True


def test_module_and_algebra_law_verifiers():
    """Verify Module, Semimodule, and Algebra law verifiers."""
    z_ring = IntegerRing()
    v_mod = SparseVectorModule()

    r_samples = [-2, 0, 1, 3]
    m_samples = [
        {},
        {'x': 1},
        {'x': -2, 'y': 3},
        {'y': 1, 'z': -1},
    ]

    res_smod = verify_semimodule_laws(v_mod, z_ring, r_samples, m_samples)
    assert all(res_smod.values())

    res_mod = verify_module_laws(v_mod, z_ring, r_samples, m_samples)
    assert all(res_mod.values())


def test_law_falsification_on_broken_structures():
    """Verify that verifiers properly catch broken rings and fields."""

    class BrokenDistributivityRing(IntegerRing):
        def mul(self, a: int, b: int) -> int:
            return a + b  # Fails distributivity and monoid identity

    br = BrokenDistributivityRing()
    res = verify_ring_laws(br, [1, 2, 3])
    assert res['left_distributivity'] is False

    class BrokenDivisionField(StandardField[Fraction]):
        def inv(self, a: Fraction) -> Fraction:
            return a  # Broken inverse

    bf = BrokenDivisionField(Fraction)
    res_f = verify_field_laws(bf, [Fraction(1, 1), Fraction(2, 1), Fraction(3, 1)])
    assert res_f['left_inverse'] is False


def test_zero_division_error_contracts():
    """Verify Golem contract invariant: division by zero raises ZeroDivisionError."""
    f = StandardField(Fraction)
    with pytest.raises(ZeroDivisionError):
        f.inv(Fraction(0, 1))
    with pytest.raises(ZeroDivisionError):
        f.div(Fraction(1, 2), Fraction(0, 1))

    mod5 = ModularField(5)
    with pytest.raises(ZeroDivisionError):
        mod5.inv(0)
    with pytest.raises(ZeroDivisionError):
        mod5.div(3, 0)
    with pytest.raises(ValueError, match='prime >= 2'):
        ModularField(1)


# =============================================================================
# 3. Exact Rational Linear Algebra & Hilbert Matrices (EP-0191 Showcase)
# =============================================================================


def test_exact_rational_lu_hilbert():
    """Verify exact LU decomposition on ill-conditioned Hilbert matrices over Fraction."""
    # 2x2 Hilbert matrix:
    # [ 1/1  1/2 ]
    # [ 1/2  1/3 ]
    h2 = {
        0: {0: Fraction(1, 1), 1: Fraction(1, 2)},
        1: {0: Fraction(1, 2), 1: Fraction(1, 3)},
    }
    field_q = StandardField(Fraction)

    p, l_mat, u_mat = lu_decompose(h2, field=field_q)

    # U[1][1] = 1/3 - (1/2)*(1/2) = 1/3 - 1/4 = 1/12
    assert u_mat[1][1] == Fraction(1, 12)
    # L[1][0] = 1/2
    assert l_mat[1][0] == Fraction(1, 2)

    # Exact reconstruction: P^T @ L @ U == A
    reconstructed = recompose_lu(p, l_mat, u_mat, field=field_q)
    assert reconstructed == h2

    # Exact determinant: det(H_2) = (1) * (1/12) = 1/12
    d = det(h2, field=field_q)
    assert d == Fraction(1, 12)

    # Exact inverse:
    # H_2^-1 = [  4  -6 ]
    #          [ -6  12 ]
    inv_h2 = inv(h2, field=field_q)
    expected_inv = {
        0: {0: Fraction(4, 1), 1: Fraction(-6, 1)},
        1: {0: Fraction(-6, 1), 1: Fraction(12, 1)},
    }
    assert inv_h2 == expected_inv

    # Verify dot(H_2, H_2^-1) == Identity exactly
    identity_2 = {
        0: {0: Fraction(1, 1)},
        1: {1: Fraction(1, 1)},
    }
    prod = dot(h2, inv_h2, semiring=field_q)
    assert prod == identity_2


def test_exact_rational_solve_system():
    """Solve linear system A x = b exactly with fractions."""
    # [ 2   1 ] [ x ] = [ 5 ]  => x = 2
    # [ 1  -1 ] [ y ] = [ 1 ]  => y = 1
    a = {
        'row1': {'x': Fraction(2, 1), 'y': Fraction(1, 1)},
        'row2': {'x': Fraction(1, 1), 'y': Fraction(-1, 1)},
    }
    b = {'row1': Fraction(5, 1), 'row2': Fraction(1, 1)}

    sol = solve(a, b, field=StandardField(Fraction))
    assert sol == {'x': Fraction(2, 1), 'y': Fraction(1, 1)}


def test_solve_triangular():
    """Verify solve_triangular for lower and upper systems."""
    # Lower triangular:
    # [ 2  0 ] [ x0 ] = [ 4 ] => x0 = 2
    # [ 3  1 ] [ x1 ] = [ 9 ] => 3(2) + x1 = 9 => x1 = 3
    l_mat = {
        0: {0: 2.0},
        1: {0: 3.0, 1: 1.0},
    }
    rhs = {0: 4.0, 1: 9.0}
    sol_l = solve_triangular(l_mat, rhs, lower=True)
    assert sol_l == {0: 2.0, 1: 3.0}

    # Upper triangular:
    # [ 2  1 ] [ x0 ] = [ 5 ] => 2(2) + 1 = 5
    # [ 0  3 ] [ x1 ] = [ 3 ] => x1 = 1
    u_mat = {
        0: {0: 2.0, 1: 1.0},
        1: {1: 3.0},
    }
    rhs_u = {0: 5.0, 1: 3.0}
    sol_u = solve_triangular(u_mat, rhs_u, lower=False)
    assert sol_u == {0: 2.0, 1: 1.0}


# =============================================================================
# 4. Finite Field Linear Algebra (F_p)
# =============================================================================


def test_finite_field_gaussian_elimination():
    """Verify exact linear algebra over finite Galois field F_7."""
    # Matrix over F_7:
    # [ 1  2 ]
    # [ 3  4 ]
    # det = 1*4 - 2*3 = 4 - 6 = -2 = 5 (mod 7)
    a_f7 = {
        0: {0: 1, 1: 2},
        1: {0: 3, 1: 4},
    }
    f7 = ModularField(7)

    d = det(a_f7, field=f7)
    assert d == 5

    # Inverse over F_7:
    # det^-1 = 5^-1 = 3 (mod 7) (since 5*3 = 15 = 1 mod 7)
    # adj(A) = [ 4  -2 ] = [ 4  5 ]
    #          [ -3  1 ] = [ 4  1 ]
    # A^-1 = 3 * adj(A) = [ 12  15 ] = [ 5  1 ]
    #                     [ 12   3 ] = [ 5  3 ] (mod 7)
    inv_f7 = inv(a_f7, field=f7)
    assert inv_f7 == {
        0: {0: 5, 1: 1},
        1: {0: 5, 1: 3},
    }

    # Verify A @ A^-1 = I (mod 7)
    identity_f7 = {
        0: {0: 1},
        1: {1: 1},
    }
    prod = dot(a_f7, inv_f7, semiring=f7)
    assert prod == identity_f7


# =============================================================================
# 5. Singularity & Error Detection
# =============================================================================


def test_singular_matrix_errors():
    """Verify SingularMatrixError is raised on singular systems."""
    # Collinear rows:
    singular_mat = {
        0: {0: 1.0, 1: 2.0},
        1: {0: 2.0, 1: 4.0},
    }
    with pytest.raises(SingularMatrixError):
        solve(singular_mat, {0: 1.0, 1: 2.0})

    with pytest.raises(SingularMatrixError):
        inv(singular_mat)

    # Triangular with zero on diagonal
    zero_diag_l = {
        0: {0: 0.0},
        1: {0: 1.0, 1: 1.0},
    }
    with pytest.raises(SingularMatrixError):
        solve_triangular(zero_diag_l, {0: 1.0, 1: 1.0}, lower=True)


def test_matrix_dimensions_errors():
    """Verify ValueError for non-square matrices in solve, det, inv."""
    non_square = {
        0: {0: 1.0, 1: 2.0, 2: 3.0},
        1: {0: 4.0, 1: 5.0, 2: 6.0},
    }
    with pytest.raises(ValueError, match='square matrix'):
        solve(non_square, {0: 1.0, 1: 2.0})

    with pytest.raises(ValueError, match='square matrices'):
        det(non_square)

    with pytest.raises(ValueError, match='square matrix'):
        inv(non_square)


def test_empty_matrices():
    """Verify empty matrix edge cases."""
    assert lu_decompose({}) == ({}, {}, {})
    assert solve_triangular({}, {}) == {}
    assert solve({}, {}) == {}
    assert det({}) == 1.0
    assert det({}, field=StandardField(Fraction)) == Fraction(1, 1)
    assert inv({}) == {}
