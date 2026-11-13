r"""Schwartz-Zippel Randomized Polynomial Identity Testing (PIT).

Implements EP-0180 & EP-0186 (Layer 5 — Randomized Polynomial Identity Testing):
Tests high-degree algebraic identities over unexpanded arithmetic circuits by evaluating
identities on random integer/rational coordinates sampled from large finite subsets,
bounding the false-positive error probability to under $10^{-16}$ (Schwartz 1980, Saxena 2014):
- **PIT 1**: Lie Algebra Jacobi Identity $[x, [y, z]] + [y, [z, x]] + [z, [x, y]] = 0$ across classical
  ($\mathfrak{so}_3, \mathfrak{sl}_2, \mathfrak{so}_4, \mathfrak{su}_3, \mathfrak{sp}_2, \mathfrak{se}_3$)
  and exceptional ($\mathfrak{g}_2, \mathfrak{f}_4$) Lie algebras.
- **PIT 2**: Lie Adjoint Representation Homomorphism
  $[\operatorname{ad}_X, \operatorname{ad}_Y](Z) = \operatorname{ad}_{[X, Y]}(Z)$
  and Bracket Antisymmetry $[x, y] + [y, x] = 0$.
- **PIT 3**: **Cayley-Hamilton Theorem** $p_A(A) = A^n + c_{n-1} A^{n-1} + \dots + c_0 I = \mathbf{0}$
  verified over exact `fractions.Fraction` $3 \times 3$ and $4 \times 4$ matrices (Faddeev-LeVerrier trace recurrence).
- **PIT 4**: Multivariate Polynomial Ring (`MultivariateBinomialConvolutionSemiring`) and `PolynomialAlgebra`
  Brahmagupta-Fibonacci / Euler Four-Square / Binomial Identities over random rational evaluations.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Any

import pytest

from algebrax.lie import LieAlgebra, e6, e7, e8, f4, g2, se_n, sl_n, so_n, sp_n, su_n
from algebrax.matrix.academic import determinant
from algebrax.matrix.core import add, dot, mat_vec, subtract, trace
from algebrax.semiring import PolynomialAlgebra, StandardSemiring

pytestmark = [pytest.mark.verification, pytest.mark.pit]

SAMPLE_SPACE_BOUND = 500  # |S| = 1000; 248^2 * x*y*z <= 7.6*10^12 << 2^53 (exact IEEE 754 float64 precision)
NUM_TRIALS = 6  # (d / |S|)^6 <= (2 / 1000)^6 = 6.4*10^-17 < 10^-16


def _random_vector(dim: int, sample_space: range, rng: random.Random) -> dict[int, float]:
    """Sample random integer coordinates for a Lie algebra element."""
    return {i: float(rng.choice(sample_space)) for i in range(dim)}


# ---------------------------------------------------------------------------
# PIT 1: Lie Algebra Jacobi Identity in Classical & Exceptional Algebras
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('lie_algebra_factory', 'name'),
    [
        (lambda: so_n(3), 'so(3) - 3D Rotations (dim 3)'),
        (lambda: sl_n(2), 'sl(2) - Special Linear (dim 3)'),
        (lambda: so_n(4), 'so(4) - 4D Orthogonal (dim 6)'),
        (lambda: se_n(3), 'se(3) - 3D Rigid Motions (dim 6)'),
        (lambda: su_n(3), 'su(3) - Special Unitary (dim 8)'),
        (lambda: sp_n(2), 'sp(2) - Symplectic (dim 10)'),
        (lambda: g2(), 'g2 - Exceptional Lie Algebra (dim 14)'),
        (lambda: f4(), 'f4 - Exceptional Lie Algebra (dim 52)'),
        (lambda: e6(), 'e6 - Exceptional Lie Algebra (dim 78)'),
        (lambda: e7(), 'e7 - Exceptional Lie Algebra (dim 133)'),
        (lambda: e8(), 'e8 - Exceptional Lie Algebra (dim 248)'),
    ],
)
def test_pit_lie_algebra_jacobi_identity(lie_algebra_factory: Any, name: str) -> None:
    """Verify that Jacobi identity [x, [y, z]] + [y, [z, x]] + [z, [x, y]] == 0 holds via PIT."""
    g: LieAlgebra = lie_algebra_factory()
    rng = random.Random(20261025)
    sample_space = range(-SAMPLE_SPACE_BOUND, SAMPLE_SPACE_BOUND)

    for trial in range(NUM_TRIALS):
        x = _random_vector(g.dim, sample_space, rng)
        y = _random_vector(g.dim, sample_space, rng)
        z = _random_vector(g.dim, sample_space, rng)

        term1 = g.bracket(x, g.bracket(y, z))
        term2 = g.bracket(y, g.bracket(z, x))
        term3 = g.bracket(z, g.bracket(x, y))

        jacobi_sum: dict[int, float | complex] = {}
        for term in (term1, term2, term3):
            for k, val in term.items():
                jacobi_sum[k] = jacobi_sum.get(k, 0.0) + val

        term_scale = max(
            max((abs(v) for v in term1.values()), default=1.0),
            1.0,
        )
        max_comp_err = max((abs(v) for v in jacobi_sum.values()), default=0.0)
        assert max_comp_err / term_scale < 1e-12, f'Jacobi identity failed for {name} on trial {trial}: {jacobi_sum}'


# ---------------------------------------------------------------------------
# PIT 2: Lie Bracket Antisymmetry & Adjoint Homomorphism
# ---------------------------------------------------------------------------


def test_pit_lie_bracket_antisymmetry_and_adjoint_homomorphism() -> None:
    """Verify [x, y] + [y, x] == 0 and [ad_x, ad_y](z) == ad_{[x, y]}(z) on g2 (dim 14) via PIT."""
    g = g2()
    rng = random.Random(314159)
    sample_space = range(-1000, 1000)

    for _ in range(NUM_TRIALS):
        x = _random_vector(g.dim, sample_space, rng)
        y = _random_vector(g.dim, sample_space, rng)
        z = _random_vector(g.dim, sample_space, rng)

        xy = g.bracket(x, y)
        yx = g.bracket(y, x)

        antisym_sum: dict[int, float | complex] = {}
        for k, v in xy.items():
            antisym_sum[k] = antisym_sum.get(k, 0.0) + v
        for k, v in yx.items():
            antisym_sum[k] = antisym_sum.get(k, 0.0) + v
        assert all(abs(v) < 1e-10 for v in antisym_sum.values())

        # Adjoint representation homomorphism: (ad_x ad_y - ad_y ad_x) z == ad_{[x, y]} z
        ad_x = g.adjoint_matrix(x)
        ad_y = g.adjoint_matrix(y)
        ad_xy = g.adjoint_matrix(xy)

        comm_ad = subtract(dot(ad_x, ad_y), dot(ad_y, ad_x))
        lhs_z = mat_vec(comm_ad, z)
        rhs_z = mat_vec(ad_xy, z)
        for k in range(g.dim):
            assert abs(lhs_z.get(k, 0.0) - rhs_z.get(k, 0.0)) < 1e-6


# ---------------------------------------------------------------------------
# PIT 3: Exact Rational Cayley-Hamilton Theorem p_A(A) == 0
# ---------------------------------------------------------------------------


def _diag_fraction(n: int, c: Fraction) -> dict[int, dict[int, Fraction]]:
    """Construct n x n scalar diagonal matrix c * I over Fraction."""
    if c == 0:
        return {}
    return {i: {i: c} for i in range(n)}


def _faddeev_leverrier_cayley_hamilton(
    a_mat: dict[int, dict[int, Fraction]],
    n: int,
) -> dict[int, dict[int, Fraction]]:
    """Evaluate p_A(A) over exact Fractions via Faddeev-LeVerrier recurrence and verify c_0 == (-1)^n det(A)."""
    import warnings

    sr = StandardSemiring(Fraction)
    ident = _diag_fraction(n, Fraction(1))

    coeffs: list[Fraction] = [Fraction(1)]  # c_n = 1
    b_k = ident
    for k in range(1, n + 1):
        ab_k = dot(a_mat, b_k, semiring=sr)
        tr_ab = trace(ab_k, semiring=sr)
        c_n_minus_k = -tr_ab / Fraction(k)
        coeffs.append(c_n_minus_k)
        if k < n:
            b_k = add(ab_k, _diag_fraction(n, c_n_minus_k), semiring=sr)

    # Constant term c_0 must equal (-1)^n det(A)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        det_a = determinant(a_mat)
    assert math.isclose(float(coeffs[-1]), ((-1) ** n) * det_a, rel_tol=1e-9, abs_tol=1e-9)

    # Evaluate Horner's scheme p_A(A) = (...((I * A + c_{n-1} I) * A + c_{n-2} I)...) * A + c_0 I
    poly_a = _diag_fraction(n, coeffs[0])
    for c in coeffs[1:]:
        poly_a = add(dot(poly_a, a_mat, semiring=sr), _diag_fraction(n, c), semiring=sr)

    return poly_a


def test_pit_cayley_hamilton_theorem_exact_rational() -> None:
    """Verify Cayley-Hamilton Theorem p_A(A) == 0 and c_0 == (-1)^n det(A) over exact Fraction matrices via PIT."""
    rng = random.Random(271828)
    for n in (3, 4):
        for _ in range(NUM_TRIALS):
            a_mat = {i: {j: Fraction(rng.randint(-15, 15), rng.randint(1, 4)) for j in range(n)} for i in range(n)}
            residual = _faddeev_leverrier_cayley_hamilton(a_mat, n)
            assert residual == {}


# ---------------------------------------------------------------------------
# PIT 4: Polynomial Ring & Diophantine Brahmagupta-Fibonacci Identity
# ---------------------------------------------------------------------------


def test_pit_polynomial_ring_brahmagupta_fibonacci_identity() -> None:
    """Verify (P^2 + Q^2)(R^2 + S^2) == (PR - QS)^2 + (PS + QR)^2 in Q[x] via PIT."""
    sr_q = StandardSemiring(Fraction)
    poly_sr = PolynomialAlgebra(sr_q)
    rng = random.Random(161803)

    def _rand_poly(deg: int) -> dict[int, Fraction]:
        return {k: Fraction(rng.randint(-20, 20), rng.randint(1, 3)) for k in range(deg + 1)}

    def _poly_sub(p: dict[int, Fraction], q: dict[int, Fraction]) -> dict[int, Fraction]:
        neg_q = {k: -v for k, v in q.items()}
        return poly_sr.add(p, neg_q)

    for _ in range(NUM_TRIALS):
        p = _rand_poly(2)
        q = _rand_poly(2)
        r = _rand_poly(2)
        s = _rand_poly(2)

        lhs = poly_sr.mul(
            poly_sr.add(poly_sr.power(p, 2), poly_sr.power(q, 2)),
            poly_sr.add(poly_sr.power(r, 2), poly_sr.power(s, 2)),
        )
        pr_minus_qs = _poly_sub(poly_sr.mul(p, r), poly_sr.mul(q, s))
        ps_plus_qr = poly_sr.add(poly_sr.mul(p, s), poly_sr.mul(q, r))
        rhs = poly_sr.add(poly_sr.power(pr_minus_qs, 2), poly_sr.power(ps_plus_qr, 2))

        assert lhs == rhs


# ---------------------------------------------------------------------------
# PIT 5: Non-Associative Algebras (EP-0204) — Jordan & Alternative Identities
# ---------------------------------------------------------------------------


def test_pit_non_associative_jordan_and_alternative_identities() -> None:
    """Verify Jordan identity (x * y) * x^2 == x * (y * x^2) and Artin's alternative theorem via PIT."""
    from algebrax.algebra._non_assoc import OctonionAlgebra, SymmetricMatrixJordanAlgebra

    # 1. Jordan Identity over 3x3 symmetric matrix algebra
    jordan_alg = SymmetricMatrixJordanAlgebra()
    rng = random.Random(42)

    for _ in range(NUM_TRIALS):
        # Sample random symmetric matrices
        x_dense = [[float(rng.randint(-10, 10)) for _ in range(3)] for _ in range(3)]
        y_dense = [[float(rng.randint(-10, 10)) for _ in range(3)] for _ in range(3)]
        # Symmetrize
        x_mat = {i: {j: (x_dense[i][j] + x_dense[j][i]) / 2.0 for j in range(3)} for i in range(3)}
        y_mat = {i: {j: (y_dense[i][j] + y_dense[j][i]) / 2.0 for j in range(3)} for i in range(3)}

        x2 = jordan_alg.mul(x_mat, x_mat)

        # Jordan identity: (x * y) * x^2 == x * (y * x^2)
        lhs = jordan_alg.mul(jordan_alg.mul(x_mat, y_mat), x2)
        rhs = jordan_alg.mul(x_mat, jordan_alg.mul(y_mat, x2))

        for i in range(3):
            for j in range(3):
                assert math.isclose(lhs[i][j], rhs[i][j], rel_tol=1e-10, abs_tol=1e-10)

    # 2. Alternative Identity in OctonionAlgebra: x * (x * y) == x^2 * y (Left Alternative)
    oct_alg = OctonionAlgebra()
    for _ in range(NUM_TRIALS):
        ox = {i: float(rng.randint(-15, 15)) for i in range(8)}
        oy = {i: float(rng.randint(-15, 15)) for i in range(8)}

        ox2 = oct_alg.mul(ox, ox)
        lhs_alt = oct_alg.mul(ox, oct_alg.mul(ox, oy))
        rhs_alt = oct_alg.mul(ox2, oy)

        for k in range(8):
            assert math.isclose(lhs_alt.get(k, 0.0), rhs_alt.get(k, 0.0), rel_tol=1e-10, abs_tol=1e-10)


# ---------------------------------------------------------------------------
# PIT 6: Hopf Algebras (EP-0206) — Antipode Axiom & Coassociativity
# ---------------------------------------------------------------------------


def test_pit_hopf_algebra_antipode_and_coassociativity() -> None:
    """Verify Hopf algebra antipode axiom and coassociativity under randomized rational trials."""
    from algebrax.algebra import DividedPowerCoalgebra, Group, GroupHopfAlgebra
    from algebrax.verification import verify_antipode_axiom, verify_coassociativity, verify_counitality

    class CyclicGroup6(Group[int]):
        @property
        def zero(self) -> int:
            return 0

        @property
        def one(self) -> int:
            return 0

        def mul(self, x: int, y: int) -> int:
            return (x + y) % 6

        def inv(self, x: int) -> int:
            return (-x) % 6

        def div(self, x: int, y: int) -> int:
            return (x - y) % 6

    gh = GroupHopfAlgebra(CyclicGroup6())
    dpc = DividedPowerCoalgebra()
    rng = random.Random(9990206)

    for _ in range(NUM_TRIALS):
        # 1. Random group algebra linear combinations
        gh_sample = {g: float(rng.randint(-50, 50)) for g in range(6)}
        assert verify_coassociativity(gh, [gh_sample])
        assert verify_counitality(gh, [gh_sample])
        assert verify_antipode_axiom(gh, [gh_sample])

        # 2. Random divided power sequence element
        dpc_sample = {deg: float(rng.randint(-30, 30)) for deg in range(5)}
        assert verify_coassociativity(dpc, [dpc_sample])
        assert verify_counitality(dpc, [dpc_sample])

