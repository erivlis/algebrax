"""Comparative (Differential) Verification — Graph Calculus, Spectral Theory & Path Semirings (EP-0182).

Pits AlgebraX's polymorphic path-semiring closures, graph Laplacians, spectral solvers,
PageRank, and discrete graph calculus operators against NetworkX and SciPy (`scipy.sparse.csgraph`,
`scipy.linalg`) reference implementations.
"""

from __future__ import annotations

import math

import networkx as nx
import numpy as np
import pytest
import scipy.linalg
import scipy.sparse.csgraph as csgraph
from hypothesis import given, settings
from hypothesis import strategies as st

import algebrax as ax
from algebrax.semiring import (
    ArcticSemiring,
    BooleanSemiring,
    BottleneckSemiring,
    LogSemiring,
    ReliabilitySemiring,
    Semiring,
    TropicalSemiring,
    ViterbiSemiring,
)
from algebrax.typing import SparseMatrix


def _semiring_kleene_closure(
    adj: SparseMatrix[int, float | bool],
    n: int,
    semiring: Semiring,
) -> SparseMatrix[int, float | bool]:
    """Compute Kleene star closure A* = (I (+) A)^(n-1) for an idempotent path semiring."""
    identity: SparseMatrix[int, float | bool] = {i: {i: semiring.one} for i in range(n)}
    step = ax.matrix.add(identity, adj, semiring=semiring)
    if n <= 1:
        return step
    return ax.matrix.power(step, n - 1, semiring=semiring)


# =============================================================================
# 1. Path Semiring Kleene Closures vs. SciPy.csgraph & NetworkX
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_tropical_shortest_paths_vs_csgraph_and_networkx() -> None:
    """Verify TropicalSemiring (min, +) Kleene closure matches Floyd-Warshall in csgraph & NetworkX."""
    rng = np.random.default_rng(18201)
    n = 10
    # Random directed weighted graph with ~40% edge density and disconnected pairs
    mask = rng.random((n, n)) < 0.40
    np.fill_diagonal(mask, False)
    weights = np.round(rng.uniform(0.5, 15.0, size=(n, n)), 3)

    adj_ax: SparseMatrix[int, float] = {}
    g_nx = nx.DiGraph()
    g_nx.add_nodes_from(range(n))
    dense_cs = np.full((n, n), np.inf, dtype=np.float64)
    np.fill_diagonal(dense_cs, 0.0)

    for i in range(n):
        for j in range(n):
            if mask[i, j]:
                w = float(weights[i, j])
                adj_ax.setdefault(i, {})[j] = w
                g_nx.add_edge(i, j, weight=w)
                dense_cs[i, j] = w

    sr = TropicalSemiring()
    closure_ax = _semiring_kleene_closure(adj_ax, n, sr)

    dist_cs = csgraph.floyd_warshall(dense_cs, directed=True)
    dist_nx = nx.floyd_warshall_numpy(g_nx, nodelist=list(range(n)), weight='weight')

    for i in range(n):
        for j in range(n):
            val_ax = closure_ax.get(i, {}).get(j, sr.zero)
            assert math.isclose(val_ax, dist_cs[i, j], rel_tol=1e-12, abs_tol=1e-12) or (
                math.isinf(val_ax) and math.isinf(dist_cs[i, j])
            )
            assert math.isclose(val_ax, dist_nx[i, j], rel_tol=1e-12, abs_tol=1e-12) or (
                math.isinf(val_ax) and math.isinf(dist_nx[i, j])
            )


@pytest.mark.verification
@pytest.mark.differential
def test_differential_boolean_transitive_closure_vs_networkx_and_csgraph() -> None:
    """Verify BooleanSemiring (or, and) Kleene closure matches NetworkX reflexive transitive closure."""
    rng = np.random.default_rng(18202)
    n = 12
    mask = rng.random((n, n)) < 0.25

    adj_ax: SparseMatrix[int, bool] = {}
    g_nx = nx.DiGraph()
    g_nx.add_nodes_from(range(n))
    adj_dense = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        for j in range(n):
            if mask[i, j]:
                adj_ax.setdefault(i, {})[j] = True
                g_nx.add_edge(i, j)
                adj_dense[i, j] = 1.0

    sr = BooleanSemiring()
    closure_ax = _semiring_kleene_closure(adj_ax, n, sr)

    tc_nx = nx.transitive_closure(g_nx, reflexive=True)
    dist_cs = csgraph.floyd_warshall(adj_dense, directed=True, unweighted=True)
    reach_cs = dist_cs < np.inf

    for i in range(n):
        for j in range(n):
            val_ax = bool(closure_ax.get(i, {}).get(j, False))
            val_nx = tc_nx.has_edge(i, j)
            val_cs = bool(reach_cs[i, j])
            assert val_ax == val_nx == val_cs


@pytest.mark.verification
@pytest.mark.differential
def test_differential_arctic_longest_path_on_dag_vs_networkx() -> None:
    """Verify ArcticSemiring (max, +) Kleene closure on DAGs matches NetworkX longest path and negated csgraph."""
    rng = np.random.default_rng(18203)
    n = 10
    # Strictly upper triangular -> guaranteed Directed Acyclic Graph (DAG)
    adj_ax: SparseMatrix[int, float] = {}
    g_nx = nx.DiGraph()
    g_nx.add_nodes_from(range(n))
    neg_dense = np.full((n, n), np.inf, dtype=np.float64)
    np.fill_diagonal(neg_dense, 0.0)

    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < 0.55:
                w = float(np.round(rng.uniform(1.0, 20.0), 3))
                adj_ax.setdefault(i, {})[j] = w
                g_nx.add_edge(i, j, weight=w)
                neg_dense[i, j] = -w

    sr = ArcticSemiring()
    closure_ax = _semiring_kleene_closure(adj_ax, n, sr)

    # On a DAG, longest path with weights W equals -shortest_path with weights -W
    neg_shortest = csgraph.floyd_warshall(neg_dense, directed=True)

    max_ax = float('-inf')
    for i in range(n):
        for j in range(n):
            val_ax = closure_ax.get(i, {}).get(j, sr.zero)
            expected = -neg_shortest[i, j] if not math.isinf(neg_shortest[i, j]) else float('-inf')
            if math.isinf(expected):
                assert val_ax == float('-inf')
            else:
                assert math.isclose(val_ax, expected, rel_tol=1e-12, abs_tol=1e-12)
                max_ax = max(max_ax, val_ax)

    nx_longest = nx.dag_longest_path_length(g_nx, weight='weight')
    assert math.isclose(max_ax, nx_longest, rel_tol=1e-12, abs_tol=1e-12)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_bottleneck_widest_path_vs_maximum_spanning_tree() -> None:
    """Verify BottleneckSemiring (max, min) Kleene closure matches minimax widest-path and MST bottleneck."""
    rng = np.random.default_rng(18204)
    n = 9
    # Construct connected undirected weighted capacity graph
    g_nx = nx.Graph()
    adj_ax: SparseMatrix[int, float] = {}
    for i in range(n - 1):
        cap = float(np.round(rng.uniform(2.0, 50.0), 3))
        adj_ax.setdefault(i, {})[i + 1] = cap
        adj_ax.setdefault(i + 1, {})[i] = cap
        g_nx.add_edge(i, i + 1, weight=cap)

    for i in range(n):
        for j in range(i + 2, n):
            if rng.random() < 0.4:
                cap = float(np.round(rng.uniform(1.0, 50.0), 3))
                adj_ax.setdefault(i, {})[j] = cap
                adj_ax.setdefault(j, {})[i] = cap
                g_nx.add_edge(i, j, weight=cap)

    sr = BottleneckSemiring()
    closure_ax = _semiring_kleene_closure(adj_ax, n, sr)

    # On an undirected graph, the widest path between u and v is the unique path in the Maximum Spanning Tree
    mst = nx.maximum_spanning_tree(g_nx, weight='weight')
    for u in range(n):
        for v in range(n):
            val_ax = closure_ax.get(u, {}).get(v, sr.zero)
            if u == v:
                assert val_ax == float('inf')
            else:
                path = nx.shortest_path(mst, source=u, target=v)
                mst_bottleneck = min(mst[path[k]][path[k + 1]]['weight'] for k in range(len(path) - 1))
                assert math.isclose(val_ax, mst_bottleneck, rel_tol=1e-12, abs_tol=1e-12)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_viterbi_and_reliability_vs_log_csgraph() -> None:
    """Verify ViterbiSemiring and ReliabilitySemiring (max, *) via log-domain isomorphism to csgraph."""
    rng = np.random.default_rng(18205)
    n = 8
    adj_ax: SparseMatrix[int, float] = {}
    neg_log_dense = np.full((n, n), np.inf, dtype=np.float64)
    np.fill_diagonal(neg_log_dense, 0.0)

    for i in range(n):
        for j in range(n):
            if i != j and rng.random() < 0.45:
                prob = float(rng.uniform(0.05, 0.95))
                adj_ax.setdefault(i, {})[j] = prob
                neg_log_dense[i, j] = -math.log(prob)

    for sr in (ViterbiSemiring(), ReliabilitySemiring()):
        closure_ax = _semiring_kleene_closure(adj_ax, n, sr)
        dist_cs = csgraph.floyd_warshall(neg_log_dense, directed=True)

        for i in range(n):
            for j in range(n):
                val_ax = closure_ax.get(i, {}).get(j, 0.0)
                expected_prob = 0.0 if math.isinf(dist_cs[i, j]) else math.exp(-dist_cs[i, j])
                assert math.isclose(val_ax, expected_prob, rel_tol=1e-11, abs_tol=1e-11)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_log_semiring_dag_partition_function_vs_scipy_inv() -> None:
    """Verify LogSemiring path sum on a DAG matches log((I - P)^(-1)) via scipy.linalg.inv."""
    rng = np.random.default_rng(18206)
    n = 7
    p_dense = np.zeros((n, n), dtype=np.float64)
    log_adj: SparseMatrix[int, float] = {}

    # Strictly upper-triangular sub-stochastic transition matrix on a DAG
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < 0.6:
                p_ij = float(rng.uniform(0.05, 0.35))
                p_dense[i, j] = p_ij
                log_adj.setdefault(i, {})[j] = math.log(p_ij)

    sr = LogSemiring()
    # Accumulate I (+) L (+) L^2 (+) ... (+) L^(n-1) in LogSemiring
    acc: SparseMatrix[int, float] = {i: {i: sr.one} for i in range(n)}
    curr: SparseMatrix[int, float] = {i: {i: sr.one} for i in range(n)}
    for _ in range(1, n):
        curr = ax.matrix.dot(curr, log_adj, semiring=sr)
        acc = ax.matrix.add(acc, curr, semiring=sr)

    resolvent = scipy.linalg.inv(np.eye(n) - p_dense)
    for i in range(n):
        for j in range(n):
            val_ax = acc.get(i, {}).get(j, sr.zero)
            if resolvent[i, j] <= 1e-15:
                assert val_ax == float('-inf')
            else:
                assert math.isclose(math.exp(val_ax), resolvent[i, j], rel_tol=1e-11, abs_tol=1e-11)


# =============================================================================
# 2. Graph Laplacians & Spectral Theory vs. NetworkX & SciPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_laplacian_matrices_vs_networkx_and_csgraph() -> None:
    """Verify combinatorial, symmetric normalized, and random-walk Laplacians against NetworkX & csgraph."""
    rng = np.random.default_rng(18207)
    n = 10
    g_nx = nx.erdos_renyi_graph(n, p=0.45, seed=18207)
    while not nx.is_connected(g_nx):
        g_nx = nx.erdos_renyi_graph(n, p=0.45, seed=int(rng.integers(1, 10000)))

    adj_ax: SparseMatrix[int, float] = {}
    w_dense = np.zeros((n, n), dtype=np.float64)
    for u, v in g_nx.edges():
        w = float(np.round(rng.uniform(0.5, 5.0), 3))
        g_nx[u][v]['weight'] = w
        adj_ax.setdefault(u, {})[v] = w
        adj_ax.setdefault(v, {})[u] = w
        w_dense[u, v] = w
        w_dense[v, u] = w

    nodelist = list(range(n))

    # 1. Unnormalized combinatorial Laplacian L = D - W
    lap_unnorm_ax = ax.converters.to_numpy(ax.matrix.laplacian_matrix(adj_ax, normalized=None), shape=(n, n))
    lap_unnorm_nx = nx.laplacian_matrix(g_nx, nodelist=nodelist, weight='weight').toarray()
    lap_unnorm_cs = csgraph.laplacian(w_dense, normed=False)
    np.testing.assert_allclose(lap_unnorm_ax, lap_unnorm_nx, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(lap_unnorm_ax, lap_unnorm_cs, rtol=1e-12, atol=1e-12)

    # 2. Symmetric normalized Laplacian L_sym = I - D^(-1/2) W D^(-1/2)
    lap_sym_ax = ax.converters.to_numpy(ax.matrix.laplacian_matrix(adj_ax, normalized='sym'), shape=(n, n))
    lap_sym_nx = nx.normalized_laplacian_matrix(g_nx, nodelist=nodelist, weight='weight').toarray()
    lap_sym_cs = csgraph.laplacian(w_dense, normed=True)
    np.testing.assert_allclose(lap_sym_ax, lap_sym_nx, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(lap_sym_ax, lap_sym_cs, rtol=1e-12, atol=1e-12)

    # 3. Random-walk normalized Laplacian L_rw = I - D^(-1) W
    lap_rw_ax = ax.converters.to_numpy(ax.matrix.laplacian_matrix(adj_ax, normalized='rw'), shape=(n, n))
    deg = w_dense.sum(axis=1)
    lap_rw_expected = np.eye(n) - np.diag(1.0 / deg) @ w_dense
    np.testing.assert_allclose(lap_rw_ax, lap_rw_expected, rtol=1e-12, atol=1e-12)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_laplacian_spectrum_vs_scipy_eigh() -> None:
    """Verify analysis.laplacian_spectrum against scipy.linalg.eigh for unnormalized and normalized Laplacians."""
    rng = np.random.default_rng(18208)
    n = 9
    g_nx = nx.barabasi_albert_graph(n, m=2, seed=18208)
    adj_ax: SparseMatrix[int, float] = {}
    for u, v in g_nx.edges():
        w = float(np.round(rng.uniform(0.8, 4.0), 3))
        adj_ax.setdefault(u, {})[v] = w
        adj_ax.setdefault(v, {})[u] = w

    for norm_flag, norm_mode in [(False, None), (True, 'sym')]:
        evals_ax, evecs_ax = ax.analysis.laplacian_spectrum(adj_ax, normalized=norm_flag)
        lap_dense = ax.converters.to_numpy(ax.matrix.laplacian_matrix(adj_ax, normalized=norm_mode), shape=(n, n))
        evals_sp, _ = scipy.linalg.eigh(lap_dense)

        np.testing.assert_allclose(evals_ax, evals_sp, rtol=1e-6, atol=1e-7)

        # Verify eigenpair residual ||L v_i - lambda_i v_i||_2 and eigenvector orthonormality
        v_mat = np.column_stack([[vec.get(i, 0.0) for i in range(n)] for vec in evecs_ax])
        np.testing.assert_allclose(v_mat.T @ v_mat, np.eye(n), rtol=1e-6, atol=1e-6)
        for idx, lam in enumerate(evals_ax):
            residual = np.linalg.norm(lap_dense @ v_mat[:, idx] - lam * v_mat[:, idx])
            assert residual < 1e-6


@pytest.mark.verification
@pytest.mark.differential
def test_differential_fiedler_vector_and_algebraic_connectivity_vs_networkx() -> None:
    """Verify analysis.fiedler_vector and algebraic_connectivity against NetworkX and SciPy."""
    # Weighted barbell-like graph with clear spectral gap
    g_nx = nx.barbell_graph(4, 1)
    rng = np.random.default_rng(18209)
    adj_ax: SparseMatrix[int, float] = {}
    for u, v in g_nx.edges():
        w = float(np.round(rng.uniform(1.0, 2.5), 3))
        g_nx[u][v]['weight'] = w
        adj_ax.setdefault(u, {})[v] = w
        adj_ax.setdefault(v, {})[u] = w

    n = g_nx.number_of_nodes()
    for norm_flag, norm_mode in [(False, None), (True, 'sym')]:
        lam2_ax, fvec_ax = ax.analysis.fiedler_vector(adj_ax, normalized=norm_flag, tol=1e-10, max_iter=800)
        conn_ax = ax.analysis.algebraic_connectivity(adj_ax, normalized=norm_flag, tol=1e-10)
        assert math.isclose(lam2_ax, conn_ax, rel_tol=1e-9, abs_tol=1e-9)

        lam2_nx = nx.algebraic_connectivity(g_nx, normalized=norm_flag, weight='weight', tol=1e-10)
        assert math.isclose(lam2_ax, lam2_nx, rel_tol=1e-5, abs_tol=1e-5)

        lap_dense = ax.converters.to_numpy(ax.matrix.laplacian_matrix(adj_ax, normalized=norm_mode), shape=(n, n))
        evals_sp, evecs_sp = scipy.linalg.eigh(lap_dense)
        assert math.isclose(lam2_ax, float(evals_sp[1]), rel_tol=1e-5, abs_tol=1e-5)

        vec_ax_np = np.array([fvec_ax.get(i, 0.0) for i in range(n)], dtype=np.float64)
        vec_sp_np = evecs_sp[:, 1]
        alignment_sp = abs(float(np.dot(vec_ax_np, vec_sp_np)))
        assert math.isclose(alignment_sp, 1.0, rel_tol=1e-4, abs_tol=1e-4)

        if not norm_flag:
            fvec_nx = nx.fiedler_vector(g_nx, normalized=False, weight='weight', tol=1e-10)
            vec_ax_nx_order = np.array([fvec_ax[u] for u in g_nx.nodes()], dtype=np.float64)
            vec_nx_np = np.asarray(fvec_nx, dtype=np.float64)
            vec_nx_np /= np.linalg.norm(vec_nx_np)
            alignment_nx = abs(float(np.dot(vec_ax_nx_order, vec_nx_np)))
            assert math.isclose(alignment_nx, 1.0, rel_tol=1e-4, abs_tol=1e-4)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_spectral_bipartition_metrics_vs_networkx_cuts() -> None:
    """Verify analysis.spectral_bipartition cut metrics match NetworkX cut_size, conductance, and normalized_cut."""
    g_nx = nx.barbell_graph(5, 0)
    adj_ax: SparseMatrix[int, float] = {}
    for u, v in g_nx.edges():
        g_nx[u][v]['weight'] = 1.5
        adj_ax.setdefault(u, {})[v] = 1.5
        adj_ax.setdefault(v, {})[u] = 1.5

    for method in ('sign', 'median'):
        v1, v2, metrics = ax.analysis.spectral_bipartition(adj_ax, method=method)
        assert v1 | v2 == set(g_nx.nodes())
        assert not (v1 & v2)

        nx_cut = nx.cut_size(g_nx, v1, v2, weight='weight')
        nx_cond = nx.conductance(g_nx, v1, v2, weight='weight')
        nx_ncut = nx.normalized_cut_size(g_nx, v1, v2, weight='weight')
        nx_rcut = nx_cut * (1.0 / len(v1) + 1.0 / len(v2))

        assert math.isclose(metrics['cut_size'], nx_cut, rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(metrics['conductance'], nx_cond, rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(metrics['normalized_cut'], nx_ncut, rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(metrics['ratio_cut'], nx_rcut, rel_tol=1e-12, abs_tol=1e-12)


# =============================================================================
# 3. Centrality & Algebraic PageRank vs. NetworkX
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_pagerank_vs_networkx() -> None:
    """Verify analysis.pagerank against networkx.pagerank across weighted, dangling, and personalized graphs."""
    rng = np.random.default_rng(18210)
    n = 12
    g_nx = nx.DiGraph()
    g_nx.add_nodes_from(range(n))
    adj_ax: SparseMatrix[int, float] = {}

    # Create directed edges, leaving node (n - 1) as a dangling sink node
    for u in range(n - 1):
        targets = rng.choice([v for v in range(n) if v != u], size=3, replace=False)
        for v in targets:
            w = float(np.round(rng.uniform(0.5, 5.0), 3))
            g_nx.add_edge(u, int(v), weight=w)
            adj_ax.setdefault(u, {})[int(v)] = w

    # 1. Standard uniform PageRank with dangling node
    pr_ax = ax.analysis.pagerank(adj_ax, damping=0.85, max_iter=500, tol=1e-10)
    pr_nx = nx.pagerank(g_nx, alpha=0.85, max_iter=500, tol=1e-10, weight='weight')
    assert math.isclose(sum(pr_ax.values()), 1.0, rel_tol=1e-9, abs_tol=1e-9)
    for u in range(n):
        assert math.isclose(pr_ax[u], pr_nx[u], rel_tol=1e-6, abs_tol=1e-6)

    # 2. Personalized PageRank with custom dangling distribution
    personalization = {i: float(i + 1) for i in range(n)}
    dangling = {i: float(n - i) for i in range(n)}
    pr_pers_ax = ax.analysis.pagerank(
        adj_ax,
        damping=0.75,
        personalization=personalization,
        dangling=dangling,
        max_iter=500,
        tol=1e-10,
    )
    pr_pers_nx = nx.pagerank(
        g_nx,
        alpha=0.75,
        personalization=personalization,
        dangling=dangling,
        max_iter=500,
        tol=1e-10,
        weight='weight',
    )
    for u in range(n):
        assert math.isclose(pr_pers_ax[u], pr_pers_nx[u], rel_tol=1e-6, abs_tol=1e-6)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_eigen_centrality_vs_networkx() -> None:
    """Verify analysis.eigen_centrality matches NetworkX eigenvector_centrality_numpy."""
    rng = np.random.default_rng(18211)
    n = 10
    g_nx = nx.watts_strogatz_graph(n, k=4, p=0.3, seed=18211)
    adj_ax: SparseMatrix[int, float] = {}
    for u, v in g_nx.edges():
        w = float(np.round(rng.uniform(0.5, 3.0), 3))
        g_nx[u][v]['weight'] = w
        adj_ax.setdefault(u, {})[v] = w
        adj_ax.setdefault(v, {})[u] = w

    ec_ax = ax.analysis.eigen_centrality(adj_ax, iterations=500, tolerance=1e-10)
    ec_nx = nx.eigenvector_centrality_numpy(g_nx, weight='weight')

    vec_ax = np.array([ec_ax[i] for i in range(n)], dtype=np.float64)
    vec_nx = np.array([ec_nx[i] for i in range(n)], dtype=np.float64)
    vec_nx /= np.linalg.norm(vec_nx)

    np.testing.assert_allclose(vec_ax, vec_nx, rtol=1e-5, atol=1e-5)


# =============================================================================
# 4. Discrete Vector Calculus, Diffusion & Curvature vs. NetworkX & SciPy
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
def test_differential_gradient_divergence_laplacian_and_greens_identity() -> None:
    """Verify discrete gradient, divergence, and Laplacian operators against NetworkX incidence & Laplacian."""
    rng = np.random.default_rng(18212)
    n = 8
    g_nx = nx.erdos_renyi_graph(n, p=0.5, seed=18212)
    while not nx.is_connected(g_nx):
        g_nx = nx.erdos_renyi_graph(n, p=0.5, seed=int(rng.integers(1, 10000)))

    adj_unweighted: SparseMatrix[int, float] = {}
    adj_weighted: SparseMatrix[int, float] = {}
    for u, v in g_nx.edges():
        w = float(np.round(rng.uniform(0.5, 4.0), 3))
        g_nx[u][v]['weight'] = w
        adj_unweighted.setdefault(u, {})[v] = 1.0
        adj_unweighted.setdefault(v, {})[u] = 1.0
        adj_weighted.setdefault(u, {})[v] = w
        adj_weighted.setdefault(v, {})[u] = w

    field = {i: float(np.round(rng.uniform(-5.0, 5.0), 3)) for i in range(n)}
    f_np = np.array([field[i] for i in range(n)], dtype=np.float64)

    # 1. Weighted Laplacian operator action matches nx.laplacian_matrix(G) @ f
    lap_f_ax = ax.analysis.laplacian(field, adj_weighted)
    lap_nx = nx.laplacian_matrix(g_nx, nodelist=list(range(n)), weight='weight').toarray()
    lap_f_nx = lap_nx @ f_np
    for i in range(n):
        assert math.isclose(lap_f_ax.get(i, 0.0), lap_f_nx[i], rel_tol=1e-11, abs_tol=1e-11)

    # 2. On unweighted undirected graphs, div(grad(f)) = -2 * L * f
    grad_f = ax.analysis.gradient(field, adj_unweighted)
    div_grad_f = ax.analysis.divergence(grad_f)
    lap_unw_f = ax.analysis.laplacian(field, adj_unweighted)
    for i in range(n):
        assert math.isclose(div_grad_f.get(i, 0.0), -2.0 * lap_unw_f.get(i, 0.0), rel_tol=1e-11, abs_tol=1e-11)

    # 3. Discrete Green's Identity (Integration by Parts):
    # sum_{u, v} (grad f)_{uv} * F_{uv} = - sum_u f_u * (div F)_u
    flow: SparseMatrix[int, float] = {}
    for u, neighbors in adj_unweighted.items():
        for v in neighbors:
            flow.setdefault(u, {})[v] = float(rng.uniform(-3.0, 3.0))

    div_flow = ax.analysis.divergence(flow)
    edge_inner = sum(grad_f.get(u, {}).get(v, 0.0) * flow_val for u, row in flow.items() for v, flow_val in row.items())
    vertex_inner = -sum(field[u] * div_flow.get(u, 0.0) for u in range(n))
    assert math.isclose(edge_inner, vertex_inner, rel_tol=1e-11, abs_tol=1e-11)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_laplacian_smoothing_and_gaussian_kernel_vs_numpy() -> None:
    """Verify analysis.laplacian_smoothing and gaussian_kernel against NumPy matrix powers and RBF formula."""
    rng = np.random.default_rng(18213)
    n = 7
    g_nx = nx.cycle_graph(n)
    adj_ax: SparseMatrix[int, float] = {}
    for u, v in g_nx.edges():
        adj_ax.setdefault(u, {})[v] = 1.0
        adj_ax.setdefault(v, {})[u] = 1.0

    field = {i: float(rng.normal(0.0, 2.0)) for i in range(n)}
    f_np = np.array([field[i] for i in range(n)], dtype=np.float64)

    steps = 8
    tau = 0.08
    smoothed_ax = ax.analysis.laplacian_smoothing(field, adj_ax, steps=steps, tau=tau, normalized='sym')
    lap_sym = nx.normalized_laplacian_matrix(g_nx, nodelist=list(range(n))).toarray()
    smoothed_np = np.linalg.matrix_power(np.eye(n) - tau * lap_sym, steps) @ f_np

    for i in range(n):
        assert math.isclose(smoothed_ax.get(i, 0.0), smoothed_np[i], rel_tol=1e-11, abs_tol=1e-11)

    # Gaussian RBF kernel verification
    dist_dense = rng.uniform(0.1, 3.0, size=(n, n))
    dist_ax = ax.converters.from_numpy(dist_dense)
    sigma = 1.25
    threshold = 1e-4
    kernel_ax = ax.converters.to_numpy(
        ax.analysis.gaussian_kernel(dist_ax, sigma=sigma, threshold=threshold),
        shape=(n, n),
    )
    kernel_np = np.exp(-(dist_dense**2) / (2.0 * sigma**2))
    kernel_np[kernel_np <= threshold] = 0.0
    np.testing.assert_allclose(kernel_ax, kernel_np, rtol=1e-12, atol=1e-12)


@pytest.mark.verification
@pytest.mark.differential
def test_differential_forman_ricci_curvature_vs_combinatorial_invariants() -> None:
    """Verify Forman-Ricci curvature on canonical graphs (cycle C_n, complete K_n) and weighted networks."""
    # 1. Cycle graph C_n (triangle-free 2-regular): F(e) = 4 - 2 - 2 + 0 = 0 everywhere
    n_cycle = 6
    c_nx = nx.cycle_graph(n_cycle)
    c_ax: SparseMatrix[int, float] = {}
    for u, v in c_nx.edges():
        c_ax.setdefault(u, {})[v] = 1.0
        c_ax.setdefault(v, {})[u] = 1.0

    curv_cycle = ax.analysis.forman_ricci_curvature(c_ax, augmented=True)
    assert len(curv_cycle) == n_cycle
    for val in curv_cycle.values():
        assert math.isclose(val, 0.0, abs_tol=1e-12)

    # 2. Complete graph K_n: deg(u) = n - 1, common neighbors = n - 2
    # Unaugmented: 4 - 2(n - 1) = 6 - 2n
    # Augmented: (6 - 2n) + 3(n - 2) = n
    n_complete = 5
    k_nx = nx.complete_graph(n_complete)
    k_ax: SparseMatrix[int, float] = {}
    for u, v in k_nx.edges():
        k_ax.setdefault(u, {})[v] = 1.0
        k_ax.setdefault(v, {})[u] = 1.0

    curv_k_unaug = ax.analysis.forman_ricci_curvature(k_ax, augmented=False)
    curv_k_aug = ax.analysis.forman_ricci_curvature(k_ax, augmented=True)
    for val in curv_k_unaug.values():
        assert math.isclose(val, 6.0 - 2.0 * n_complete, abs_tol=1e-12)
    for val in curv_k_aug.values():
        assert math.isclose(val, float(n_complete), abs_tol=1e-12)


# =============================================================================
# 5. Hypothesis Property-Based Differential Sweeps
# =============================================================================


@pytest.mark.verification
@pytest.mark.differential
@settings(max_examples=25, deadline=None)
@given(
    weights=st.lists(
        st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False),
        min_size=25,
        max_size=25,
    ),
)
def test_hypothesis_differential_tropical_apsp_and_laplacian(weights: list[float]) -> None:
    """Property-based differential sweep: Tropical Kleene star & Laplacian match csgraph across random 5x5 graphs."""
    n = 5
    w_mat = np.array(weights, dtype=np.float64).reshape((n, n))
    np.fill_diagonal(w_mat, 0.0)

    adj_ax: SparseMatrix[int, float] = {}
    dense_cs = np.full((n, n), np.inf, dtype=np.float64)
    np.fill_diagonal(dense_cs, 0.0)

    for i in range(n):
        for j in range(n):
            if i != j and w_mat[i, j] > 2.0:
                val = float(w_mat[i, j])
                adj_ax.setdefault(i, {})[j] = val
                dense_cs[i, j] = val

    sr = TropicalSemiring()
    closure_ax = _semiring_kleene_closure(adj_ax, n, sr)
    dist_cs = csgraph.floyd_warshall(dense_cs, directed=True)

    for i in range(n):
        for j in range(n):
            val_ax = closure_ax.get(i, {}).get(j, sr.zero)
            if math.isinf(dist_cs[i, j]):
                assert math.isinf(val_ax)
            else:
                assert math.isclose(val_ax, dist_cs[i, j], rel_tol=1e-11, abs_tol=1e-11)

    # Also verify symmetrized combinatorial Laplacian against csgraph.laplacian
    sym_w = 0.5 * (np.where(np.isinf(dense_cs), 0.0, dense_cs) + np.where(np.isinf(dense_cs), 0.0, dense_cs).T)
    np.fill_diagonal(sym_w, 0.0)
    lap_ax = ax.converters.to_numpy(ax.matrix.laplacian_matrix(adj_ax, normalized=None, symmetrize=True), shape=(n, n))
    lap_cs = csgraph.laplacian(sym_w, normed=False)
    np.testing.assert_allclose(lap_ax, lap_cs, rtol=1e-11, atol=1e-11)
