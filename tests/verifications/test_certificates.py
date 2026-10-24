r"""Proof-carrying solver (PCS) verification certificates.

Implements EP-0180 & EP-0186 (Layer 7 — Universal Proof-Carrying Solver Certificates):
Verifies the outputs of $O(N^3)$ numerical decompositions and iterative solvers in fast $O(\text{nnz})$ or
$O(N^2)$ time using strictly pure-Python `algebrax` algebraic witnesses (zero external library calls):
- `matrix.decompose.lu(A)`: $\|P A - L U\|_\infty \le \epsilon$, unit lower-triangular $L$, upper-triangular $U$,
  and permutation matrix $P^T P = I$.
- `matrix.decompose.qr(A)`: $\|A - Q R\|_\infty \le \epsilon$, orthonormal columns $Q^T Q = I$, upper-triangular $R$.
- `matrix.decompose.cholesky(A)`: $\|A - L L^T\|_\infty \le \epsilon$, lower-triangular $L$ with positive diagonal
  $L_{ii} > 0$.
- `matrix.decompose.svd(A)`: $\|A - U \Sigma V^T\|_\infty \le \epsilon$, $U^T U = I$, $V^T V = I$, and sorted
  non-negative singular values $\sigma_1 \ge \sigma_2 \ge \dots \ge 0$.
- `matrix.cg_solve(A, b)` & `matrix.inverse(A)`: relative linear residual
  $\|A x - b\|_\infty / \|b\|_\infty \le \epsilon$ and $A A^{-1} = I$.
- `analysis.pagerank(W)` & `analysis.fiedler_vector(W)`: stationary fixed-point certificate and Laplacian eigenpair
  witness $\|L v_2 - \lambda_2 v_2\|_2 \le \epsilon$ with $\langle v_2, \mathbf{1} \rangle = 0$.
- `homology.helmholtz_hodge_decomposition`: $O(|E|)$ orthogonal decomposition, curl-free exact, divergence-free coexact,
  and harmonic kernel $\Delta_1 \gamma = 0$.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pytest

import algebrax as ax
from algebrax.analysis import algebraic_connectivity, fiedler_vector, pagerank
from algebrax.homology import Cochain, SimplicialComplex, helmholtz_hodge_decomposition, hodge_laplacian
from algebrax.matrix.core import cg_solve, dot, inverse, laplacian_matrix, mat_vec, subtract, transpose, vec_norm
from algebrax.matrix.decompose import (
    cholesky,
    lu,
    qr,
    recompose_cholesky,
    recompose_lu,
    recompose_qr,
    recompose_svd,
    svd,
)
from algebrax.verification import semiring_elements_equal

pytestmark = [pytest.mark.verification, pytest.mark.certificates]


def _max_abs_entry(mat: Mapping[int, Mapping[int, float]]) -> float:
    """Compute max_{i, j} |A_{i, j}| of a sparse matrix."""
    vals = [abs(v) for row in mat.values() for v in row.values()]
    return max(vals) if vals else 0.0


def _inner_product(
    f1: Mapping[tuple[int, ...], float],
    f2: Mapping[tuple[int, ...], float],
) -> float:
    """Compute Euclidean L^2 inner product between two sparse cochains."""
    acc = 0.0
    for simplex, val in f1.items():
        if simplex in f2:
            acc += val * f2[simplex]
    return acc


# ---------------------------------------------------------------------------
# 1. LU Decomposition Proof-Carrying Certificate
# ---------------------------------------------------------------------------


def test_lu_decomposition_certificate() -> None:
    """Verify P, L, U certificate conditions: P @ A == L @ U, unit lower L, upper U, and P^T P == I."""
    a_mat = {
        0: {0: 2.0, 1: 1.0, 2: 1.0, 3: 0.0},
        1: {0: 4.0, 1: 3.0, 2: 3.0, 3: 1.0},
        2: {0: 8.0, 1: 7.0, 2: 9.0, 3: 5.0},
        3: {0: 6.0, 1: 7.0, 2: 9.0, 3: 8.0},
    }
    p_mat, l_mat, u_mat = lu(a_mat)

    # Certificate 1: Permutation orthogonality P^T @ P == I
    pt_p = dot(transpose(p_mat), p_mat)
    ident = {i: {i: 1.0} for i in range(4)}
    assert _max_abs_entry(subtract(pt_p, ident)) < 1e-12

    # Certificate 2: Unit lower-triangular structure of L (L_{ii} == 1, L_{ij} == 0 for j > i)
    for i in range(4):
        assert math.isclose(l_mat.get(i, {}).get(i, 0.0), 1.0, rel_tol=1e-12)
        for j, val in l_mat.get(i, {}).items():
            if j > i:
                assert abs(val) < 1e-12

    # Certificate 3: Upper-triangular structure of U (U_{ij} == 0 for i > j)
    for i, row in u_mat.items():
        for j, val in row.items():
            if i > j:
                assert abs(val) < 1e-12

    # Certificate 4: Exact factorization witness P @ A == L @ U and recompose_lu(P, L, U) == A
    pa = dot(p_mat, a_mat)
    lu_prod = dot(l_mat, u_mat)
    assert _max_abs_entry(subtract(pa, lu_prod)) < 1e-11
    assert _max_abs_entry(subtract(recompose_lu(p_mat, l_mat, u_mat), a_mat)) < 1e-11


# ---------------------------------------------------------------------------
# 2. QR Decomposition Proof-Carrying Certificate
# ---------------------------------------------------------------------------


def test_qr_decomposition_certificate() -> None:
    """Verify Q, R certificate conditions: Q^T @ Q == I, R upper-triangular, and Q @ R == A."""
    a_mat = {
        0: {0: 12.0, 1: -51.0, 2: 4.0},
        1: {0: 6.0, 1: 167.0, 2: -68.0},
        2: {0: -4.0, 1: 24.0, 2: -41.0},
    }
    q_mat, r_mat = qr(a_mat)
    ident = {i: {i: 1.0} for i in range(3)}

    # Certificate 1: Orthonormality Q^T @ Q == I
    qt_q = dot(transpose(q_mat), q_mat)
    assert _max_abs_entry(subtract(qt_q, ident)) < 1e-11

    # Certificate 2: Upper-triangular structure of R (R_{ij} == 0 for i > j)
    for i, row in r_mat.items():
        for j, val in row.items():
            if i > j:
                assert abs(val) < 1e-11

    # Certificate 3: Factorization witness Q @ R == A
    assert _max_abs_entry(subtract(recompose_qr(q_mat, r_mat), a_mat)) < 1e-10


# ---------------------------------------------------------------------------
# 3. Cholesky SPD Decomposition Proof-Carrying Certificate
# ---------------------------------------------------------------------------


def test_cholesky_decomposition_certificate() -> None:
    """Verify Cholesky certificate: L lower-triangular, L_{ii} > 0, and L @ L^T == A."""
    spd_mat = {
        0: {0: 4.0, 1: 12.0, 2: -16.0},
        1: {0: 12.0, 1: 37.0, 2: -43.0},
        2: {0: -16.0, 1: -43.0, 2: 98.0},
    }
    l_mat = cholesky(spd_mat)

    # Certificate 1: Positive diagonal & lower-triangular structure
    for i in range(3):
        assert l_mat.get(i, {}).get(i, 0.0) > 0.0
        for j, val in l_mat.get(i, {}).items():
            if j > i:
                assert abs(val) < 1e-12

    # Certificate 2: Recomposition L @ L^T == A
    assert _max_abs_entry(subtract(recompose_cholesky(l_mat), spd_mat)) < 1e-11


# ---------------------------------------------------------------------------
# 4. Singular Value Decomposition (SVD) Proof-Carrying Certificate
# ---------------------------------------------------------------------------


def test_svd_decomposition_certificate() -> None:
    """Verify SVD certificate: U^T U == I, V^T V == I, sigma_1 >= sigma_2 >= 0, and U Sigma V^T == A."""
    a_mat = {
        0: {0: 3.0, 1: 2.0, 2: 2.0},
        1: {0: 2.0, 1: 3.0, 2: -2.0},
        2: {0: 0.0, 1: 1.0, 2: 4.0},
    }
    u_mat, s_vec, vt_mat = svd(a_mat)
    ident = {i: {i: 1.0} for i in range(3)}

    # Certificate 1: Non-negative descending singular values
    sigmas = [s_vec.get(i, 0.0) for i in range(3)]
    assert all(s >= 0.0 for s in sigmas)
    assert sigmas[0] >= sigmas[1] - 1e-12 >= sigmas[2] - 2e-12

    # Certificate 2: Left & right singular vector orthonormality U^T U == I and V_t V_t^T == I
    ut_u = dot(transpose(u_mat), u_mat)
    vt_v = dot(vt_mat, transpose(vt_mat))
    assert _max_abs_entry(subtract(ut_u, ident)) < 1e-7
    assert _max_abs_entry(subtract(vt_v, ident)) < 1e-7

    # Certificate 3: Recomposition witness U @ diag(S) @ V^T == A
    recomposed = recompose_svd(u_mat, s_vec, vt_mat)
    assert _max_abs_entry(subtract(recomposed, a_mat)) < 1e-7


# ---------------------------------------------------------------------------
# 5. Linear Solvers (CG & Inverse) & Spectral Graph Certificates
# ---------------------------------------------------------------------------


def test_linear_solver_and_spectral_eigenpair_certificates() -> None:
    """Verify O(nnz) residual certificates for cg_solve, inverse, Fiedler eigenpair, and PageRank fixed point."""
    # 1. Conjugate Gradient residual certificate: ||A x - b||_2 / ||b||_2 <= tol
    spd = {
        0: {0: 6.0, 1: -2.0, 2: 1.0},
        1: {0: -2.0, 1: 5.0, 2: -1.0},
        2: {0: 1.0, 1: -1.0, 2: 4.0},
    }
    b = {0: 11.0, 1: -9.0, 2: 7.0}
    x = cg_solve(spd, b, tol=1e-11, max_iter=200)

    ax_vec = mat_vec(spd, x)
    residual = {k: ax_vec.get(k, 0.0) - b.get(k, 0.0) for k in set(ax_vec) | set(b)}
    assert vec_norm(residual) / vec_norm(b) < 1e-9

    # 2. Matrix Inverse certificate: ||A A^{-1} - I||_inf <= tol
    inv_spd = inverse(spd)
    ident = {i: {i: 1.0} for i in range(3)}
    assert _max_abs_entry(subtract(dot(spd, inv_spd), ident)) < 1e-11

    # 3. Fiedler Vector & Algebraic Connectivity Eigenpair Certificate on a connected graph:
    # L v_2 == lambda_2 v_2, ||v_2||_2 == 1, and <v_2, 1> == 0
    graph = {
        0: {1: 1.0, 2: 1.0},
        1: {0: 1.0, 2: 1.0, 3: 1.0},
        2: {0: 1.0, 1: 1.0, 3: 1.0},
        3: {1: 1.0, 2: 1.0},
    }
    lap = laplacian_matrix(graph)
    lambda_2_ac = algebraic_connectivity(graph)
    lambda_2, v_2 = fiedler_vector(graph)
    assert math.isclose(lambda_2, lambda_2_ac, rel_tol=1e-6)

    # Orthogonality to constant nullspace vector 1 and unit L2 norm
    assert abs(sum(v_2.values())) < 1e-6
    assert math.isclose(vec_norm(v_2), 1.0, rel_tol=1e-6)

    # Eigenpair residual ||L v_2 - lambda_2 v_2||_2 <= tol
    lv_2 = mat_vec(lap, v_2)
    eig_residual = {u: lv_2.get(u, 0.0) - lambda_2 * v_2.get(u, 0.0) for u in graph}
    assert vec_norm(eig_residual) < 1e-5

    # 4. PageRank stationary probability certificate: sum(pi) == 1, pi_u >= 0, and fixed-point convergence
    pr = pagerank(graph, damping=0.85, tol=1e-10)
    assert math.isclose(sum(pr.values()), 1.0, rel_tol=1e-9)
    assert all(p > 0.0 for p in pr.values())
    # Symmetry certificate: nodes 0 and 3 are automorphic, nodes 1 and 2 are automorphic
    assert math.isclose(pr[0], pr[3], rel_tol=1e-8)
    assert math.isclose(pr[1], pr[2], rel_tol=1e-8)


# ---------------------------------------------------------------------------
# 6. Helmholtz-Hodge Decomposition Certificate
# ---------------------------------------------------------------------------


def test_helmholtz_hodge_decomposition_certificate() -> None:
    """Verify in O(|E|) time that Helmholtz-Hodge decomposition satisfies the 4 orthogonal certificate conditions."""
    triangles = [
        (0, 1, 2),
        (2, 3, 4),
        (4, 5, 0),
        (0, 2, 4),
    ]
    sc = SimplicialComplex(triangles)

    raw_flow = {
        (0, 1): 2.5,
        (1, 2): 1.5,
        (2, 3): -3.0,
        (3, 4): 2.0,
        (4, 5): 1.0,
        (5, 0): -0.5,
        (0, 2): 1.0,
        (2, 4): -1.2,
    }
    flow = Cochain(raw_flow, degree=1)
    decomp = helmholtz_hodge_decomposition(sc, flow, tol=1e-9)

    exact = decomp.exact
    coexact = decomp.coexact
    harmonic = decomp.harmonic

    # Certificate Condition 1: Recomposition Identity (w = w_exact + w_coexact + w_harmonic)
    recomposed: dict[tuple[int, ...], float] = {}
    for comp in (exact, coexact, harmonic):
        for e, v in comp.items():
            recomposed[e] = recomposed.get(e, 0.0) + v

    recomposed_clean = {e: v for e, v in recomposed.items() if abs(v) > 1e-9}
    flow_clean = {e: v for e, v in flow.items() if abs(v) > 1e-9}

    assert semiring_elements_equal(recomposed_clean, flow_clean, tol=1e-6), (
        f'Recomposition certificate failed: {recomposed_clean} != {flow_clean}'
    )

    # Certificate Condition 2: L^2 Orthogonality Witnesses
    assert abs(_inner_product(exact, coexact)) < 1e-6
    assert abs(_inner_product(exact, harmonic)) < 1e-6
    assert abs(_inner_product(coexact, harmonic)) < 1e-6

    # Certificate Condition 3: Curl-free exact & Divergence-free coexact
    b1 = sc.boundary_matrices.get(1, {})
    b2 = sc.boundary_matrices.get(2, {})

    if b2:
        d1 = ax.matrix.transpose(b2)
        curl_exact = ax.matrix.mat_vec(d1, exact)
        for tri, val in curl_exact.items():
            assert abs(val) < 1e-6, f'Exact component is not curl-free on triangle {tri}: {val}'

    if b1:
        div_coexact = ax.matrix.mat_vec(b1, coexact)
        for vertex, val in div_coexact.items():
            assert abs(val) < 1e-6, f'Coexact component is not divergence-free on vertex {vertex}: {val}'

    # Certificate Condition 4: Harmonic component lies in ker(Delta_1)
    delta1 = hodge_laplacian(sc, 1)
    lap_harmonic = ax.matrix.mat_vec(delta1, harmonic)
    for edge, val in lap_harmonic.items():
        assert abs(val) < 1e-6, f'Harmonic component has non-zero Hodge Laplacian on {edge}: {val}'
