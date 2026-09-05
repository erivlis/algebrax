import math

import pytest

import algebrax as ax
from algebrax.analysis import (
    algebraic_connectivity,
    fiedler_vector,
    laplacian_matrix,
    laplacian_smoothing,
    laplacian_spectrum,
    spectral_bipartition,
)
from algebrax.matrix.academic import PerformanceWarning


def _dirichlet_energy(lap, u):
    lu = ax.matrix.mat_vec(lap, u)
    return 0.5 * sum(u[k] * lu.get(k, 0.0) for k in u)


# ---------------------------------------------------------------------------
# 1. Laplacian Matrix Assembly
# ---------------------------------------------------------------------------


def test_laplacian_matrix_empty():
    assert laplacian_matrix({}) == {}


def test_laplacian_matrix_single_node():
    assert laplacian_matrix({0: {}}) == {}


def test_laplacian_matrix_combinatorial_p3():
    # 0 - 1 - 2
    p3 = {0: {1: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {1: 1.0}}
    lap = laplacian_matrix(p3)
    # L = [[1, -1, 0], [-1, 2, -1], [0, -1, 1]]
    assert lap[0][0] == 1.0
    assert lap[0][1] == -1.0
    assert lap[1][1] == 2.0
    assert lap[1][0] == -1.0
    assert lap[1][2] == -1.0
    assert lap[2][2] == 1.0
    assert lap[2][1] == -1.0


def test_laplacian_matrix_symmetric_normalized():
    # 0 - 1
    edge = {0: {1: 2.0}, 1: {0: 2.0}}
    lap_sym = laplacian_matrix(edge, normalized='sym')
    # L_sym = [[1, -1], [-1, 1]]
    assert pytest.approx(lap_sym[0][0]) == 1.0
    assert pytest.approx(lap_sym[1][1]) == 1.0
    assert pytest.approx(lap_sym[0][1]) == -1.0
    assert pytest.approx(lap_sym[1][0]) == -1.0


def test_laplacian_matrix_random_walk():
    # Star S3: center 0, leaves 1, 2
    s3 = {0: {1: 1.0, 2: 1.0}, 1: {0: 1.0}, 2: {0: 1.0}}
    lap_rw = laplacian_matrix(s3, normalized='rw')
    # d_0 = 2, so row 0 has diag 1, off-diagonals -0.5
    assert pytest.approx(lap_rw[0][0]) == 1.0
    assert pytest.approx(lap_rw[0][1]) == -0.5
    assert pytest.approx(lap_rw[0][2]) == -0.5
    # d_1 = 1, so row 1 has diag 1, off-diagonal -1.0
    assert pytest.approx(lap_rw[1][0]) == -1.0


def test_laplacian_matrix_symmetrize():
    # Directed graph: 0 -> 1 with weight 2.0
    digraph = {0: {1: 2.0}}
    lap_sym = laplacian_matrix(digraph, symmetrize=True)
    # Average weight is 1.0 each way
    assert lap_sym[0][0] == 1.0
    assert lap_sym[1][1] == 1.0
    assert lap_sym[0][1] == -1.0
    assert lap_sym[1][0] == -1.0

    lap_nosym = laplacian_matrix(digraph, symmetrize=False)
    assert lap_nosym[0][0] == 2.0
    assert lap_nosym[0][1] == -2.0
    assert 1 not in lap_nosym  # Node 1 has out-degree 0


def test_laplacian_matrix_self_loops():
    # Self-loops should cancel out in L = D - W
    graph_with_loops = {0: {0: 5.0, 1: 1.0}, 1: {0: 1.0, 1: 3.0}}
    lap = laplacian_matrix(graph_with_loops)
    assert lap[0][0] == 1.0
    assert lap[1][1] == 1.0
    assert lap[0][1] == -1.0


def test_laplacian_matrix_invalid_mode():
    with pytest.raises(ValueError, match="Unknown normalization mode: 'invalid'"):
        laplacian_matrix({0: {1: 1.0}}, normalized='invalid')  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 2. Analytical Eigenspectrum & Fiedler Vector Oracles
# ---------------------------------------------------------------------------


def test_fiedler_path_p4():
    # P4: 0 - 1 - 2 - 3
    # Analytical: lambda_2 = 2 - 2*cos(pi/4) = 2 - sqrt(2) ≈ 0.58578644
    p4 = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1}}
    expected_lam2 = 2.0 - math.sqrt(2.0)
    lam2, f_vec = fiedler_vector(p4)
    assert pytest.approx(lam2, abs=1e-6) == expected_lam2
    assert algebraic_connectivity(p4) == pytest.approx(expected_lam2, abs=1e-6)

    # Unit norm and orthogonal to 1
    assert pytest.approx(sum(v * v for v in f_vec.values()), abs=1e-6) == 1.0
    assert pytest.approx(sum(f_vec.values()), abs=1e-6) == 0.0


def test_fiedler_cycle_c6():
    # C6: lambda_2 = 2 - 2*cos(2*pi/6) = 2 - 2*(0.5) = 1.0
    c6 = {0: {1: 1, 5: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1, 4: 1}, 4: {3: 1, 5: 1}, 5: {4: 1, 0: 1}}
    lam2 = algebraic_connectivity(c6)
    assert pytest.approx(lam2, abs=1e-6) == 1.0


def test_fiedler_clique_k5():
    # K5: lambda_2 = ... = lambda_5 = 5.0
    k5 = {i: {j: 1 for j in range(5) if j != i} for i in range(5)}
    lam2 = algebraic_connectivity(k5)
    assert pytest.approx(lam2, abs=1e-6) == 5.0


def test_fiedler_star_s4():
    # S4 (1 center, 3 leaves): lambda_2 = 1.0
    s4 = {0: {1: 1, 2: 1, 3: 1}, 1: {0: 1}, 2: {0: 1}, 3: {0: 1}}
    lam2 = algebraic_connectivity(s4)
    assert pytest.approx(lam2, abs=1e-6) == 1.0


def test_fiedler_small_graphs():
    assert fiedler_vector({}) == (0.0, {})
    assert fiedler_vector({0: {}}) == (0.0, {0: 0.0})

    # N=2 graph
    n2 = {0: {1: 3.0}, 1: {0: 3.0}}
    lam2, vec = fiedler_vector(n2)
    assert pytest.approx(lam2) == 6.0
    assert pytest.approx(abs(vec[0])) == 1.0 / math.sqrt(2.0)
    assert pytest.approx(abs(vec[1])) == 1.0 / math.sqrt(2.0)


def test_fiedler_disconnected_graph():
    # Two disconnected edges: {0 - 1} and {2 - 3}
    g = {0: {1: 1.0}, 1: {0: 1.0}, 2: {3: 1.0}, 3: {2: 1.0}}
    lam2, f_vec = fiedler_vector(g)
    assert lam2 == 0.0
    # Should partition the two components
    assert f_vec[0] == f_vec[1]
    assert f_vec[2] == f_vec[3]
    assert f_vec[0] != f_vec[2]


def test_fiedler_normalized():
    # Normalized Laplacian on P4
    p4 = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1}}
    lam2, f_vec = fiedler_vector(p4, normalized=True)
    assert lam2 > 0.0
    assert pytest.approx(sum(v * v for v in f_vec.values()), abs=1e-6) == 1.0


# ---------------------------------------------------------------------------
# 3. Spectral Bipartitioning & Cheeger Cuts
# ---------------------------------------------------------------------------


def test_spectral_bipartition_barbell():
    # Barbell graph: K3 on {0, 1, 2} connected to K3 on {3, 4, 5} via edge (2, 3)
    barbell = {
        0: {1: 1.0, 2: 1.0},
        1: {0: 1.0, 2: 1.0},
        2: {0: 1.0, 1: 1.0, 3: 1.0},
        3: {2: 1.0, 4: 1.0, 5: 1.0},
        4: {3: 1.0, 5: 1.0},
        5: {3: 1.0, 4: 1.0},
    }
    v1, v2, metrics = spectral_bipartition(barbell)

    # Should separate the two cliques
    clique1 = {0, 1, 2}
    clique2 = {3, 4, 5}
    assert (v1 == clique1 and v2 == clique2) or (v1 == clique2 and v2 == clique1)

    # Bridge edge cut_size is exactly 1.0
    assert pytest.approx(metrics['cut_size']) == 1.0
    assert metrics['conductance'] > 0.0
    assert metrics['ratio_cut'] > 0.0
    assert metrics['normalized_cut'] > 0.0


def test_spectral_bipartition_median():
    # P4: 0 - 1 - 2 - 3
    p4 = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1}}
    v1, v2, metrics = spectral_bipartition(p4, method='median')
    assert len(v1) == 2
    assert len(v2) == 2
    assert pytest.approx(metrics['cut_size']) == 1.0


def test_spectral_bipartition_edge_cases():
    expected_empty = (
        set(),
        set(),
        {'cut_size': 0.0, 'ratio_cut': 0.0, 'normalized_cut': 0.0, 'conductance': 0.0},
    )
    assert spectral_bipartition({}) == expected_empty
    v1, v2, _ = spectral_bipartition({0: {}})
    assert v1 == {0}
    assert v2 == set()

    with pytest.raises(ValueError, match="method must be 'sign' or 'median'"):
        spectral_bipartition({0: {1: 1}}, method='other')  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 4. Laplacian Smoothing & Heat Diffusion
# ---------------------------------------------------------------------------


def test_laplacian_smoothing_dirichlet_energy_decrease():
    # P4 graph with noisy scalar field
    p4 = {0: {1: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {1: 1.0, 3: 1.0}, 3: {2: 1.0}}
    lap = laplacian_matrix(p4)
    f0 = {0: 10.0, 1: 0.0, 2: 0.0, 3: 10.0}

    e_prev = _dirichlet_energy(lap, f0)
    for s in [1, 3, 5, 10]:
        f_smoothed = laplacian_smoothing(f0, p4, steps=s, tau=0.1)
        e_curr = _dirichlet_energy(lap, f_smoothed)
        assert e_curr <= e_prev + 1e-12
        e_prev = e_curr


def test_laplacian_smoothing_with_precomputed_laplacian():
    p3 = {0: {1: 1.0}, 1: {0: 1.0, 2: 1.0}, 2: {1: 1.0}}
    lap = laplacian_matrix(p3)
    f0 = {0: 1.0, 1: 0.0, 2: 1.0}

    # Pass laplacian operator directly
    f_smooth = laplacian_smoothing(f0, lap, steps=5, tau=0.1)
    assert 0 in f_smooth
    assert 1 in f_smooth
    assert 2 in f_smooth


def test_laplacian_smoothing_invalid_args():
    p2 = {0: {1: 1.0}, 1: {0: 1.0}}
    f0 = {0: 1.0, 1: 0.0}
    with pytest.raises(ValueError, match='steps must be a positive integer'):
        laplacian_smoothing(f0, p2, steps=0)
    with pytest.raises(ValueError, match='tau must be positive'):
        laplacian_smoothing(f0, p2, steps=5, tau=0.0)


# ---------------------------------------------------------------------------
# 5. Full Eigenspectrum & Performance Warnings
# ---------------------------------------------------------------------------


def test_laplacian_spectrum_p4():
    p4 = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1}}
    vals, vecs = laplacian_spectrum(p4)
    expected_p4 = [0.0, 2.0 - math.sqrt(2.0), 2.0, 2.0 + math.sqrt(2.0)]
    assert len(vals) == 4
    assert len(vecs) == 4
    for v_actual, v_exp in zip(vals, expected_p4, strict=True):
        assert pytest.approx(v_actual, abs=1e-8) == v_exp


def test_laplacian_spectrum_truncated():
    p4 = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1}}
    vals, vecs = laplacian_spectrum(p4, k=2)
    assert len(vals) == 2
    assert len(vecs) == 2
    assert pytest.approx(vals[0], abs=1e-8) == 0.0
    assert pytest.approx(vals[1], abs=1e-8) == 2.0 - math.sqrt(2.0)


def test_laplacian_spectrum_empty():
    vals, vecs = laplacian_spectrum({})
    assert vals == []
    assert vecs == []


def test_laplacian_spectrum_warning_on_large_graph():
    # Construct a cycle graph with 151 vertices to trigger PerformanceWarning
    n = 151
    large_graph = {i: {(i + 1) % n: 1.0, (i - 1) % n: 1.0} for i in range(n)}
    with pytest.warns(PerformanceWarning, match='Computing full laplacian_spectrum for N=151 > 150'):
        laplacian_spectrum(large_graph, k=1)
