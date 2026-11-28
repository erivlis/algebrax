"""Regression and soundness tests for sparse linear algebra kernel, decompositions, and hot paths."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

import algebrax as ax
import algebrax.matrix.core as matrix_core
import algebrax.matrix.decompose as matrix_decompose
from algebrax.algebra import ModularField, StandardField
from algebrax.analysis import fiedler_vector, gradient, is_ramanujan_graph, laplacian
from algebrax.clifford import CliffordAlgebra
from algebrax.converters import canonical_sort_keys, grid_to_sparse, prune_sparse
from algebrax.matrix import (
    SingularMatrixError,
    cholesky,
    det,
    dot,
    inner,
    inv,
    laplacian_matrix,
    lu_decompose,
    mat_vec,
    nullspace,
    power,
    rank,
    recompose_cholesky,
    recompose_lu,
    solve,
    solve_triangular,
    sparse_rref,
)
from algebrax.semiring import StringSemiring, TropicalSemiring
from algebrax.topology import CellularSheaf, FilteredSimplicialComplex, SimplicialComplex
from algebrax.topology.persistence import _extract_vr_edges, _has_perfect_bipartite_matching


def _assert_matrices_close(a: dict[Any, dict[Any, Any]], b: dict[Any, dict[Any, Any]], tol: float = 1e-9) -> None:
    keys = set(a.keys()) | set(b.keys())
    for r in keys:
        ra = a.get(r, {})
        rb = b.get(r, {})
        for c in set(ra.keys()) | set(rb.keys()):
            va = ra.get(c, 0.0)
            vb = rb.get(c, 0.0)
            assert abs(va - vb) <= tol, f'Mismatch at ({r!r}, {c!r}): {va!r} != {vb!r}'


# ---------------------------------------------------------------------------
# 1. LU Decomposition, Disjoint-Key Systems, Rectangular & Zero Row/Col Guards
# ---------------------------------------------------------------------------


def test_lu_decompose_rectangular_and_disjoint_keys():
    """Verify P @ A == L @ U on tall, wide, and disjoint-key matrices (float and exact Fraction)."""
    tall = {0: {'x': 2.0, 'y': 1.0}, 1: {'x': 4.0, 'y': 3.0}, 2: {'x': 6.0, 'y': 7.0}}
    wide = {'r0': {10: 1.0, 2: 2.0, 5: 3.0}, 'r1': {10: 4.0, 2: 5.0, 5: 9.0}}
    disjoint = {0: {1: 2.0, 2: 1.0}, 1: {1: 1.0, 2: 3.0}}

    for mat in (tall, wide, disjoint):
        p_mat, l_mat, u_mat = lu_decompose(mat)
        pa = dot(p_mat, mat)
        lu = dot(l_mat, u_mat)
        _assert_matrices_close(pa, lu)
        _assert_matrices_close(recompose_lu(p_mat, l_mat, u_mat), mat)

    q_field = StandardField(Fraction)
    tall_q = {
        0: {'x': Fraction(2), 'y': Fraction(1)},
        1: {'x': Fraction(4), 'y': Fraction(3)},
        2: {'x': Fraction(6), 'y': Fraction(7)},
    }
    p_q, l_q, u_q = lu_decompose(tall_q, field=q_field)
    assert dot(p_q, tall_q) == dot(l_q, u_q)


def test_solve_disjoint_keys_and_det_omitted_zero_domain():
    """Verify solve() on disjoint row/col domains and det() on shifted/rectangular matrices."""
    mat = {'eq0': {'x': 2.0, 'y': 1.0}, 'eq1': {'x': 1.0, 'y': 3.0}}
    rhs = {'eq0': 5.0, 'eq1': 5.0}
    sol = solve(mat, rhs)
    assert sol['x'] == pytest.approx(2.0)
    assert sol['y'] == pytest.approx(1.0)

    q_field = StandardField(Fraction)
    mat_q = {'eq0': {'x': Fraction(2), 'y': Fraction(1)}, 'eq1': {'x': Fraction(1), 'y': Fraction(3)}}
    rhs_q = {'eq0': Fraction(5), 'eq1': Fraction(5)}
    assert solve(mat_q, rhs_q, field=q_field) == {'x': Fraction(2), 'y': Fraction(1)}

    # Shifted key sets {0, 1} vs {1, 2} imply omitted zero column 0 & zero row 2 in 3x3 square domain
    shifted = {0: {1: 1.0}, 1: {2: 1.0}}
    assert det(shifted) == 0.0
    assert det({0: {1: Fraction(1)}, 1: {2: Fraction(1)}}, field=q_field) == Fraction(0)
    with pytest.raises(SingularMatrixError):
        inv(shifted)

    # Rectangular matrices must raise ValueError before any omitted-domain singularity check
    rect = {0: {0: 1.0, 1: 2.0}}
    with pytest.raises(ValueError, match='square'):
        det(rect)
    with pytest.raises(ValueError, match='square'):
        solve(rect, {0: 1.0})
    with pytest.raises(ValueError, match='square'):
        inv(rect)


# ---------------------------------------------------------------------------
# 2. Canonical Key Ordering, Cholesky Validation, Complex Pruning
# ---------------------------------------------------------------------------


def test_canonical_sort_keys_and_n12_triangular_cholesky():
    """Verify natural integer ordering (2 < 10) for solve_triangular and cholesky at n >= 12."""
    assert canonical_sort_keys([10, 2, 1, 11, 0]) == [0, 1, 2, 10, 11]
    assert canonical_sort_keys([2, 'a', 1]) == sorted([2, 'a', 1], key=str)

    n = 12
    # Lower triangular L with L[i, i] = 2.0 and L[i, i-1] = 0.5
    lower_mat: dict[int, dict[int, float]] = {}
    for i in range(n):
        lower_mat[i] = {i: 2.0}
        if i > 0:
            lower_mat[i][i - 1] = 0.5

    x_true = {i: float(i + 1) for i in range(n)}
    b_vec = mat_vec(lower_mat, x_true)
    x_solved = solve_triangular(lower_mat, b_vec, lower=True)
    for i in range(n):
        assert x_solved[i] == pytest.approx(x_true[i])

    # SPD matrix A = L @ L^T on integer keys 0..11
    spd = recompose_cholesky(lower_mat)
    l_chol = cholesky(spd)
    _assert_matrices_close(recompose_cholesky(l_chol), spd)
    _assert_matrices_close(l_chol, lower_mat)


def test_cholesky_rejects_asymmetric_and_column_only_keys():
    """Verify cholesky validates symmetry and full row/column key domain."""
    asym = {0: {0: 4.0, 1: 1.0}, 1: {0: 2.0, 1: 4.0}}
    with pytest.raises(ValueError, match='symmetric'):
        cholesky(asym)

    col_only = {0: {0: 4.0, 1: 1.0}}
    with pytest.raises(ValueError, match='symmetric'):
        cholesky(col_only)


def test_complex_noise_pruning():
    """Verify prune_sparse and grid_to_sparse prune tiny complex noise while keeping non-trivial entries."""
    noisy = {0: {0: 1e-17j, 1: 1e-17 + 1e-17j, 2: 2.0j}}
    pruned = prune_sparse(noisy, tol=1e-12)
    assert pruned == {0: {2: 2.0j}}

    grid = [[1e-17j, 3.0 - 1.0j], [0.0j, 1e-16 + 0.0j]]
    sparse = grid_to_sparse(grid, [0, 1], [0, 1], tol=1e-12)
    assert sparse == {0: {1: 3.0 - 1.0j}}


# ---------------------------------------------------------------------------
# 3. O(N^3) Single-LU inv() & Clean Removal of matrix.core.inverse
# ---------------------------------------------------------------------------


def test_inv_single_lu_and_complex_and_clean_cut(monkeypatch):
    """Verify inv() calls lu_decompose once, supports complex/Fraction, and matrix.core.inverse is removed."""
    assert not hasattr(ax.matrix, 'inverse')
    assert not hasattr(matrix_core, 'inverse')

    calls = 0
    orig_lu = matrix_decompose.lu_decompose

    def spy_lu(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return orig_lu(*args, **kwargs)

    monkeypatch.setattr(matrix_decompose, 'lu_decompose', spy_lu)

    n = 6
    mat = {i: {i: 4.0} for i in range(n)}
    for i in range(n - 1):
        mat[i][i + 1] = 1.0
        mat[i + 1][i] = 1.0

    mat_inv = inv(mat)
    assert calls == 1
    ident = {i: {i: 1.0} for i in range(n)}
    _assert_matrices_close(dot(mat, mat_inv), ident)

    # Complex matrix inversion
    c_mat = {0: {0: 1.0 + 1.0j, 1: 2.0j}, 1: {0: 0.0 + 0.0j, 1: 1.0 - 1.0j}}
    c_inv = inv(c_mat)
    _assert_matrices_close(dot(c_mat, c_inv), {0: {0: 1.0 + 0.0j}, 1: {1: 1.0 + 0.0j}})

    # Exact rational matrix inversion
    q_field = StandardField(Fraction)
    q_mat = {0: {0: Fraction(2), 1: Fraction(1)}, 1: {0: Fraction(1), 1: Fraction(3)}}
    q_inv = inv(q_mat, field=q_field)
    assert dot(q_mat, q_inv) == {0: {0: Fraction(1)}, 1: {1: Fraction(1)}}


# ---------------------------------------------------------------------------
# 4. Field-Polymorphic Sparse Elimination, RP^2 Torsion & Sheaf Field/Tol
# ---------------------------------------------------------------------------


def test_sparse_rref_rank_nullspace_across_fields():
    """Verify sparse_rref, rank, and nullspace across float, complex, Fraction, and ModularField."""
    # 2x4 matrix with an omitted zero column 'z'
    all_cols = ['a', 'b', 'c', 'z']

    # Float regime
    a_float = {0: {'a': 1.0, 'b': 2.0, 'c': 3.0}, 1: {'a': 2.0, 'b': 4.0, 'c': 6.0}}
    rref_f, pivots_f = sparse_rref(a_float)
    assert pivots_f == ['a']
    assert rref_f == {0: {'a': 1.0, 'b': 2.0, 'c': 3.0}}
    assert rank(a_float) == 1
    ker_f = nullspace(a_float, cols=all_cols)
    assert len(ker_f) == 3
    for vec in ker_f:
        for r, row in a_float.items():
            val = sum(row.get(c, 0.0) * v for c, v in vec.items())
            assert abs(val) <= 1e-12, f'Row {r} nonzero for nullspace vector {vec}'

    # Complex regime
    c_field = StandardField(complex)
    a_cplx = {0: {'a': 1.0j, 'b': 1.0 + 1.0j}, 1: {'a': -1.0, 'b': -1.0 + 1.0j}}
    assert rank(a_cplx, field=c_field) == 1
    ker_c = nullspace(a_cplx, cols=['a', 'b', 'z'], field=c_field)
    assert len(ker_c) == 2
    for vec in ker_c:
        for row in a_cplx.values():
            val = sum(row.get(c, 0j) * v for c, v in vec.items())
            assert abs(val) <= 1e-12

    # Exact Fraction regime
    q_field = StandardField(Fraction)
    a_q = {
        0: {'a': Fraction(2), 'b': Fraction(4), 'c': Fraction(1)},
        1: {'a': Fraction(1), 'b': Fraction(2), 'c': Fraction(3)},
    }
    rref_q, pivots_q = sparse_rref(a_q, field=q_field)
    assert pivots_q == ['a', 'c']
    assert rref_q == {
        0: {'a': Fraction(1), 'b': Fraction(2)},
        1: {'c': Fraction(1)},
    }
    assert rank(a_q, field=q_field) == 2
    ker_q = nullspace(a_q, cols=all_cols, field=q_field)
    assert len(ker_q) == 2
    for vec in ker_q:
        for row in a_q.values():
            acc = Fraction(0)
            for c, v in vec.items():
                if c in row:
                    acc += row[c] * v
            assert acc == Fraction(0)

    # ModularField(5) regime
    f5 = ModularField(5)
    a_f5 = {0: {'a': 2, 'b': 1, 'c': 3}, 1: {'a': 4, 'b': 2, 'c': 1}}
    assert rank(a_f5, field=f5) == 1
    ker_f5 = nullspace(a_f5, cols=all_cols, field=f5)
    assert len(ker_f5) == 3
    for vec in ker_f5:
        for row in a_f5.values():
            acc_mod = 0
            for c, v in vec.items():
                if c in row:
                    acc_mod = f5.add(acc_mod, f5.mul(row[c], v))
            assert acc_mod == 0


def test_rp2_torsion_homology_over_f2_vs_q():
    """Verify exact Z_2 torsion detection on the minimal 6-vertex triangulation of RP^2."""
    rp2_triangles = [
        (0, 1, 2),
        (0, 2, 3),
        (0, 3, 4),
        (0, 4, 5),
        (0, 5, 1),
        (1, 2, 4),
        (2, 3, 5),
        (3, 4, 1),
        (4, 5, 2),
        (5, 1, 3),
    ]
    sc = SimplicialComplex(rp2_triangles)

    # Over F_2: H_0 = F_2, H_1 = F_2 (2-torsion), H_2 = F_2 (mod-2 fundamental class)
    assert sc.betti_numbers(max_k=2, field=ModularField(2)) == {0: 1, 1: 1, 2: 1}
    # Over Q and F_3: torsion vanishes -> H_0 = K, H_1 = 0, H_2 = 0
    assert sc.betti_numbers(max_k=2, field=StandardField(Fraction)) == {0: 1, 1: 0, 2: 0}
    assert sc.betti_numbers(max_k=2, field=ModularField(3)) == {0: 1, 1: 0, 2: 0}


def test_cellular_sheaf_cohomology_honors_tol_and_field():
    """Verify CellularSheaf global_sections_dimension and first_cohomology_dimension honor tol and field."""
    # Mobius 1-sheaf on a 3-cycle: holonomy = -1 (frustrated over Q/R, flat over F_2)
    mobius = CellularSheaf()
    mobius.add_edge(0, 1, dim=1, rho_u=1.0, rho_v=1.0)
    mobius.add_edge(1, 2, dim=1, rho_u=1.0, rho_v=1.0)
    mobius.add_edge(0, 2, dim=1, rho_u=-1.0, rho_v=1.0)

    assert mobius.global_sections_dimension(field=StandardField(Fraction)) == 0
    assert mobius.first_cohomology_dimension(field=StandardField(Fraction)) == 0
    assert mobius.global_sections_dimension(field=ModularField(2)) == 1
    assert mobius.first_cohomology_dimension(field=ModularField(2)) == 1

    # Tolerance sensitivity on near-zero restriction map
    eps_sheaf = CellularSheaf()
    eps_sheaf.add_edge(0, 1, dim=1, rho_u=1e-6, rho_v=0.0)
    assert eps_sheaf.global_sections_dimension(tol=1e-12) == 1
    assert eps_sheaf.first_cohomology_dimension(tol=1e-12) == 0
    assert eps_sheaf.global_sections_dimension(tol=1e-4) == 2
    assert eps_sheaf.first_cohomology_dimension(tol=1e-4) == 1


# ---------------------------------------------------------------------------
# 5. Non-Commutative inner(), Fast mat_vec(), and power() Squaring Skip
# ---------------------------------------------------------------------------


def test_inner_preserves_noncommutative_operand_order():
    """Verify inner(v1, v2, sr) preserves (v1[k], v2[k]) order regardless of len(v1) vs len(v2)."""
    str_sr = StringSemiring()
    v_short = {0: {'A'}}
    v_long = {0: {'B'}, 1: {'C'}, 2: {'D'}}
    assert inner(v_short, v_long, str_sr) == {'AB'}
    assert inner(v_long, v_short, str_sr) == {'BA'}

    cl = CliffordAlgebra(2, 0)
    e1, e2 = {(1,): 1.0}, {(2,): 1.0}
    u_short = {0: e1}
    u_long = {0: e2, 1: e1, 2: e2}
    prod_12 = inner(u_short, u_long, cl)
    prod_21 = inner(u_long, u_short, cl)
    assert prod_12 == cl.mul(e1, e2)
    assert prod_21 == cl.mul(e2, e1)
    assert prod_12 != prod_21


def test_mat_vec_matches_inner_and_power_skips_trailing_squaring(monkeypatch):
    """Verify mat_vec parity with inner and that power(M, n) skips unused final base squaring."""
    mat = {0: {0: 2.0, 1: 3.0}, 1: {0: 1.0, 2: 4.0}}
    vec = {0: 5.0, 1: -1.0, 2: 2.0}
    res = mat_vec(mat, vec)
    for r, row in mat.items():
        assert res[r] == pytest.approx(inner(row, vec))

    trop = TropicalSemiring()
    res_trop = mat_vec(mat, vec, trop)
    for r, row in mat.items():
        assert res_trop[r] == pytest.approx(inner(row, vec, trop))

    str_sr = StringSemiring()
    s_mat = {0: {0: 'a', 1: 'b'}, 1: {1: 'c'}}
    s_vec = {0: 'x', 1: 'y'}
    assert mat_vec(s_mat, s_vec, str_sr) == {r: inner(row, s_vec, str_sr) for r, row in s_mat.items()}

    # Spy on dot inside power(M, 4): binary 100_2 -> M^2, M^4, I*M^4 = 3 calls (no unused M^8 squaring)
    dot_calls = 0
    orig_dot = matrix_core.dot

    def spy_dot(*args: Any, **kwargs: Any) -> Any:
        nonlocal dot_calls
        dot_calls += 1
        return orig_dot(*args, **kwargs)

    monkeypatch.setattr(matrix_core, 'dot', spy_dot)
    base_m = {0: {0: 1.0, 1: 1.0}, 1: {1: 1.0}}
    p4 = power(base_m, 4)
    assert p4 == {0: {0: 1.0, 1: 4.0}, 1: {1: 1.0}}
    assert dot_calls == 3


# ---------------------------------------------------------------------------
# 6. Lazy SimplicialComplex, Exact Int Signs, Degenerate Rejection & O(nnz) VR
# ---------------------------------------------------------------------------


def test_lazy_simplicial_complex_exact_signs_and_degenerate_rejection(monkeypatch):
    """Verify 5-simplex insertion rebuilds boundaries at most once on access with exact int signs."""
    rebuilds = 0
    orig_rebuild = SimplicialComplex._rebuild_boundary_matrices

    def spy_rebuild(self: SimplicialComplex) -> None:
        nonlocal rebuilds
        rebuilds += 1
        orig_rebuild(self)

    monkeypatch.setattr(SimplicialComplex, '_rebuild_boundary_matrices', spy_rebuild)

    sc = SimplicialComplex()
    sc.add_simplex((0, 1, 2, 3, 4, 5))
    assert rebuilds == 0

    bm = sc.boundary_matrices
    assert rebuilds == 1
    _ = sc.boundary_matrices
    assert rebuilds == 1

    # Verify all incidence coefficients are exact int (+1 or -1)
    for mat in bm.values():
        for row in mat.values():
            for val in row.values():
                assert type(val) is int
                assert val in (-1, 1)

    # Degenerate repeated-vertex simplices must raise ValueError
    with pytest.raises(ValueError, match='Degenerate'):
        sc.add_simplex((0, 0))
    with pytest.raises(ValueError, match='Degenerate'):
        sc.add_simplex((0, 1, 0))

    fsc = FilteredSimplicialComplex()
    with pytest.raises(ValueError, match='Degenerate'):
        fsc.add_simplex((2, 2), 1.0)


def test_vr_edges_asymmetric_distance_max_before_threshold():
    """Verify _extract_vr_edges computes max(d_uv, d_vu) before filtering by max_edge_length."""
    dist = {
        0: {1: 0.5, 2: 0.8},
        1: {0: 2.0, 2: 0.6},
        2: {0: 0.7, 1: 0.6},
    }
    _, edges, _ = _extract_vr_edges(dist, max_edge_length=1.0)
    # (0, 1) has max(0.5, 2.0) = 2.0 > 1.0, so it must be excluded
    assert (0, 1) not in edges
    assert edges[(0, 2)] == pytest.approx(0.8)
    assert edges[(1, 2)] == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# 7. Iterative Hopcroft-Karp Matching Depth Safety (N >= 1500)
# ---------------------------------------------------------------------------


def test_iterative_hopcroft_karp_deep_alternating_chain():
    """Verify iterative _has_perfect_bipartite_matching handles depth N >= 1500 without RecursionError."""
    n = 1500
    # Ordering [i + 1, i] forces greedy matching u_i -> v_{i+1}, leaving u_{n-1} to augment across all n steps to v_0
    adj = [[i + 1, i] if i + 1 < n else [i] for i in range(n)]
    assert _has_perfect_bipartite_matching(adj, n, n) is True
    # Violate Hall's condition by restricting both u_{n-2} and u_{n-1} to v_{n-2} (isolating v_{n-1})
    adj_broken = [list(nbrs) for nbrs in adj]
    adj_broken[n - 2] = [n - 2]
    adj_broken[n - 1] = [n - 2]
    assert _has_perfect_bipartite_matching(adj_broken, n, n) is False


# ---------------------------------------------------------------------------
# 8. Graph Calculus Parity, Symmetrized Fiedler & Ramanujan Connectivity
# ---------------------------------------------------------------------------


def test_graph_laplacian_gradient_parity_and_upper_triangular_fiedler():
    """Verify laplacian(f, G) == mat_vec(laplacian_matrix(G), f), gradient pruning, and fiedler_vector."""
    unweighted = {0: {1: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {1: 1.0}}
    weighted = {0: {1: 2.5}, 1: {0: 2.5, 2: 0.5}, 2: {1: 0.5}}
    upper_tri_with_loop = {0: {0: 9.0, 1: 2.0}, 1: {2: 3.0}, 2: {}}

    f_sparse = {0: 1.0}
    for g in (unweighted, weighted, upper_tri_with_loop):
        lap_direct = laplacian(f_sparse, g)
        lap_mat_res = mat_vec(laplacian_matrix(g), f_sparse)
        assert set(lap_direct.keys()) == set(lap_mat_res.keys())
        for k in lap_mat_res:
            assert lap_direct[k] == pytest.approx(lap_mat_res[k])

    # gradient captures boundary edges to zero-valued neighbors and prunes zero-difference edges
    grad = gradient({0: 1.0}, unweighted)
    assert grad == {0: {1: -1.0}, 1: {0: 1.0}}
    assert gradient({0: 2.0, 1: 2.0, 2: 2.0}, unweighted) == {}

    # fiedler_vector on upper-triangular graph: symmetrization (A + A^T)/2 halves edge weights
    upper_path = {0: {1: 1.0}, 1: {2: 1.0}, 2: {3: 1.0}}
    sym_path = {0: {1: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {1: 1.0, 3: 1.0}, 3: {2: 1.0}}
    lam_u, _ = fiedler_vector(upper_path, normalized=False)
    lam_s, _ = fiedler_vector(sym_path, normalized=False)
    assert lam_u == pytest.approx(0.5 * lam_s, rel=1e-4)

    # Normalized Laplacian is scale-invariant under the 0.5 symmetrization factor
    lam_un, _ = fiedler_vector(upper_path, normalized=True)
    lam_sn, _ = fiedler_vector(sym_path, normalized=True)
    assert lam_un == pytest.approx(lam_sn, rel=1e-4)


def test_is_ramanujan_graph_rejects_disconnected_regular_graph():
    """Verify is_ramanujan_graph returns False on disconnected K_4 union K_4."""
    k4 = {i: {j: 1.0 for j in range(4) if j != i} for i in range(4)}
    is_ram_k4, _, _ = is_ramanujan_graph(k4, degree=3)
    assert is_ram_k4 is True

    # Disjoint union K_4 U K_4 has two eigenvalues equal to +3, so second eigenvalue is 3 > 2*sqrt(2)
    k4_union_k4 = {i: {j: 1.0 for j in range(4) if j != i} for i in range(4)}
    for i in range(4, 8):
        k4_union_k4[i] = {j: 1.0 for j in range(4, 8) if j != i}
    is_ram_disc, max_nt, threshold = is_ramanujan_graph(k4_union_k4, degree=3)
    assert is_ram_disc is False
    assert max_nt == pytest.approx(3.0, abs=1e-6)
    assert max_nt > threshold
