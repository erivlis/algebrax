import pytest

from algebrax.analysis import (
    divergence,
    forman_ricci_curvature,
    gaussian_kernel,
    gradient,
    laplacian,
)


def test_gradient():
    # 0 -- 1
    # f(0)=0, f(1)=10
    field = {0: 0, 1: 10}
    graph = {0: [1], 1: [0]}

    grad = gradient(field, graph)
    # 0->1: 10 - 0 = 10
    # 1->0: 0 - 10 = -10
    assert grad[0][1] == 10
    assert grad[1][0] == -10


def test_divergence():
    # Flow 0->1 (10)
    flow = {0: {1: 10}}
    div = divergence(flow)
    # 0: +10 (out)
    # 1: -10 (in)
    assert div[0] == 10
    assert div[1] == -10


def test_laplacian():
    # 0 -- 1
    # f(0)=0, f(1)=10
    # L(0) = sum(f(0)-f(1)) = 0-10 = -10
    # L(1) = sum(f(1)-f(0)) = 10-0 = 10
    field = {0: 0, 1: 10}
    graph = {0: {1: 1}, 1: {0: 1}}  # Weighted

    lap = laplacian(field, graph)
    assert lap[0] == -10
    assert lap[1] == 10


def test_gaussian_kernel():
    # d(0,1) = 0 (self) -> 1.0
    # d(0,1) = 1 -> exp(-0.5) approx 0.606
    dist = {0: {1: 1.0}}
    sim = gaussian_kernel(dist, sigma=1.0)
    assert sim[0][1] == pytest.approx(0.60653, 0.001)


def test_forman_ricci_curvature():
    # 1. Unweighted Triangle (Clique)
    # 0-1, 1-2, 2-0
    # For e=(0, 1):
    # deg(0)=2, deg(1)=2. Triangles containing (0, 1) = 1.
    # Unaugmented: 4 - 2 - 2 = 0
    # Augmented: 4 - 2 - 2 + 3*1 = 3
    graph = {0: {1: 1, 2: 1}, 1: {0: 1, 2: 1}, 2: {0: 1, 1: 1}}

    f_1d = forman_ricci_curvature(graph, augmented=False)
    assert f_1d[(0, 1)] == pytest.approx(0.0)

    f_aug = forman_ricci_curvature(graph, augmented=True)
    assert f_aug[(0, 1)] == pytest.approx(3.0)

    # 2. Unweighted Line 0-1-2-3
    # 1-2: deg(1)=2, deg(2)=2 -> 4 - 2 - 2 = 0
    # 0-1: deg(0)=1, deg(1)=2 -> 4 - 1 - 2 = 1
    line = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1}}
    f_line = forman_ricci_curvature(line, augmented=True)
    assert f_line[(0, 1)] == pytest.approx(1.0)
    assert f_line[(1, 2)] == pytest.approx(0.0)

    # 3. Weighted Graph (with and without triangles)
    # 0-1: 2.0, 1-2: 2.0, 2-0: 2.0
    # All edge weights are 2.0.
    # Node strengths: s(0) = 4.0, s(1) = 4.0, s(2) = 4.0.
    # For edge (0, 1):
    # w_e = 2.0, w_u = 4.0, w_v = 4.0.
    # Adjacent sums:
    # sharing 0: adjacent is (0, 2) weight 2.0. Sum_u = 4.0 / sqrt(2 * 2) = 2.0
    # sharing 1: adjacent is (1, 2) weight 2.0. Sum_v = 4.0 / sqrt(2 * 2) = 2.0
    # 1D FRC: 2.0 * (4.0/2.0 + 4.0/2.0 - 2.0 - 2.0) = 0.0
    # Augmented FRC:
    # common neighbor is 2. Tri weight w_f = (2.0 * 2.0 * 2.0) ** (1/3) = 2.0.
    # tri_contrib = 2.0 / 2.0 = 1.0.
    # FRC_aug = 0.0 + 3.0 * tri_contrib = 3.0.
    weighted_graph = {0: {1: 2.0, 2: 2.0}, 1: {0: 2.0, 2: 2.0}, 2: {0: 2.0, 1: 2.0}}
    f_weighted_1d = forman_ricci_curvature(weighted_graph, augmented=False)
    assert f_weighted_1d[(0, 1)] == pytest.approx(0.0)

    f_weighted_aug = forman_ricci_curvature(weighted_graph, augmented=True)
    assert f_weighted_aug[(0, 1)] == pytest.approx(3.0)


def test_gaussian_kernel_empty():
    assert gaussian_kernel({}) == {}


def test_gaussian_kernel_threshold():
    dist = {0: {1: 10.0}}
    sim = gaussian_kernel(dist, sigma=1.0, threshold=0.1)
    assert sim == {}


def test_gradient_missing_keys():
    field = {0: 0, 1: 10}
    graph = {0: [1], 2: [0]}
    grad = gradient(field, graph)
    assert 2 not in grad
    assert grad[0][1] == 10


def test_gradient_neighbor_missing():
    field = {0: 0}
    graph = {0: [2]}
    grad = gradient(field, graph)
    assert grad == {}


def test_laplacian_missing_keys():
    field = {0: 0}
    graph = {0: {1: 1}, 2: {0: 1}}
    lap = laplacian(field, graph)
    assert lap == {}


def test_laplacian_zero_sum():
    field = {0: 10, 1: 10}
    graph = {0: {1: 1}}
    lap = laplacian(field, graph)
    assert lap == {}


def test_forman_ricci_weighted_and_uncomparable_nodes():
    g_weighted = {
        0: {1: 2.0, 2: 4.0},
        1: {0: 2.0, 2: 3.0},
        2: {0: 4.0, 1: 3.0},
    }
    frc_explicit = forman_ricci_curvature(g_weighted, weighted=True, augmented=True)
    frc_auto = forman_ricci_curvature(g_weighted, weighted=None, augmented=True)
    assert frc_explicit == frc_auto
    assert len(frc_explicit) == 3

    g_zero = {0: {1: 0.0}, 1: {0: 0.0}}
    frc_zero = forman_ricci_curvature(g_zero, weighted=True)
    assert frc_zero[(0, 1)] == 0.0

    class CustomNode:
        def __init__(self, val):
            self.val = val

    n1 = CustomNode(1)
    n2 = CustomNode(2)
    g_custom = {n1: {n2: 1.0}, n2: {n1: 1.0}}
    frc_custom = forman_ricci_curvature(g_custom, weighted=False)
    assert len(frc_custom) == 1


def test_analysis_edge_branches():
    from algebrax.analysis import _get_common_neighbors, _is_graph_weighted

    assert _get_common_neighbors({0: {1: 1.0}}, 0, 999) == set()
    assert not _is_graph_weighted({0: {1: 1.0}})
    assert _is_graph_weighted({0: {1: 2.0}})

    class CustomNode:
        pass

    c1, c2 = CustomNode(), CustomNode()
    g_custom_weighted = {c1: {c2: 2.0}, c2: {c1: 2.0}}
    assert len(forman_ricci_curvature(g_custom_weighted, weighted=True)) == 1


def test_analysis_branch_coverage():
    g = {
        0: {1: 1.0, 2: 0.0},
        1: {0: 1.0, 2: 1.0},
        2: {0: 0.0, 1: 1.0},
    }
    frc = forman_ricci_curvature(g, weighted=True, augmented=True)
    assert len(frc) == 3
