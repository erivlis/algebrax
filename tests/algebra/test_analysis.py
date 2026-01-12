import pytest

from algebrax.analysis import (
    divergence,
    gaussian_kernel,
    gradient,
    laplacian,
    ollivier_ricci_curvature,
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
    graph = {0: {1: 1}, 1: {0: 1}} # Weighted

    lap = laplacian(field, graph)
    assert lap[0] == -10
    assert lap[1] == 10

def test_gaussian_kernel():
    # d(0,1) = 0 (self) -> 1.0
    # d(0,1) = 1 -> exp(-0.5) approx 0.606
    dist = {0: {1: 1.0}}
    sim = gaussian_kernel(dist, sigma=1.0)
    assert sim[0][1] == pytest.approx(0.60653, 0.001)

def test_curvature():
    # Triangle (Clique)
    # 0-1, 1-2, 2-0
    # deg=2 for all
    # F(e) = 4 - 2 - 2 = 0
    graph = {
        0: {1: 1, 2: 1},
        1: {0: 1, 2: 1},
        2: {0: 1, 1: 1}
    }
    ric = ollivier_ricci_curvature(graph)
    assert ric[(0, 1)] == 0

    # Line 0-1-2-3
    # 1-2: deg(1)=2, deg(2)=2 -> 0
    # 0-1: deg(0)=1, deg(1)=2 -> 4-1-2 = 1
    line = {
        0: {1: 1},
        1: {0: 1, 2: 1},
        2: {1: 1, 3: 1},
        3: {2: 1}
    }
    ric_line = ollivier_ricci_curvature(line)
    assert ric_line[(0, 1)] == 1
    assert ric_line[(1, 2)] == 0
