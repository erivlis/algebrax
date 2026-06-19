import pytest

from algebrax.analysis import (
    divergence,
    fenchel_legendre_transform,
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
    assert f_1d[(0, 1)] == 0.0

    f_aug = forman_ricci_curvature(graph, augmented=True)
    assert f_aug[(0, 1)] == 3.0

    # 2. Unweighted Line 0-1-2-3
    # 1-2: deg(1)=2, deg(2)=2 -> 4 - 2 - 2 = 0
    # 0-1: deg(0)=1, deg(1)=2 -> 4 - 1 - 2 = 1
    line = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1, 3: 1}, 3: {2: 1}}
    f_line = forman_ricci_curvature(line, augmented=True)
    assert f_line[(0, 1)] == 1.0
    assert f_line[(1, 2)] == 0.0

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


def test_fenchel_legendre_transform():
    from algebrax.semiring import ArcticSemiring, StandardSemiring, TropicalSemiring

    # f(x) = x^2
    signal = {0: 0.0, 1: 1.0, 2: 4.0, 3: 9.0}

    # Standard / None semiring (fallback)
    # f*(s) = sup_x (s*x - f(x))
    # s = 2: max(2*0-0, 2*1-1, 2*2-4, 2*3-9) = max(0, 1, 0, -3) = 1.0
    val_none = fenchel_legendre_transform(signal, slope=2.0)
    assert val_none == 1.0

    val_std = fenchel_legendre_transform(signal, slope=2.0, semiring=StandardSemiring())
    assert val_std == 1.0

    # Tropical (Min-Plus):
    # f*(s) = min_x (s + x - f(x))
    # s = 2: min(2+0-0, 2+1-1, 2+2-4, 2+3-9) = min(2, 2, 0, -4) = -4.0
    val_trop = fenchel_legendre_transform(signal, slope=2.0, semiring=TropicalSemiring())
    assert val_trop == -4.0

    # Arctic (Max-Plus):
    # f*(s) = max_x (s + x - f(x))
    # s = 2: max(2+0-0, 2+1-1, 2+2-4, 2+3-9) = max(2, 2, 0, -4) = 2.0
    val_arc = fenchel_legendre_transform(signal, slope=2.0, semiring=ArcticSemiring())
    assert val_arc == 2.0
