import pytest

from algebrax.matrix.academic import (
    PerformanceWarning,
    adjoint,
    cofactor,
    determinant,
    eigen_centrality,
    inverse,
)


def test_determinant_2x2():
    # |1 2| = 1*4 - 2*3 = -2
    # |3 4|
    m = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == pytest.approx(-2)


def test_determinant_3x3():
    # Identity
    m = {0: {0: 1}, 1: {1: 1}, 2: {2: 1}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == pytest.approx(1)


def test_determinant_singular():
    # Row 0 is zero
    m = {0: {}, 1: {1: 1}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == pytest.approx(0)


def test_determinant_row_swap():
    # Matrix requiring row swap
    # | 0 1 |  (pivot at 0,0 is 0)
    # | 1 0 |
    # Swap -> - | 1 0 | -> det = -(-1) = 1? No.
    #           | 0 1 |
    # Det = -1.
    m = {0: {0: 0, 1: 1}, 1: {0: 1, 1: 0}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == pytest.approx(-1)


def test_determinant_empty():
    with pytest.warns(PerformanceWarning):
        assert determinant({}) == pytest.approx(1)


def test_inverse():
    # [4 7]^-1 = 1/(4*6 - 7*2) * [6 -7] = 1/10 * [6 -7]
    # [2 6]                      [-2 4]          [-2 4]
    m = {0: {0: 4, 1: 7}, 1: {0: 2, 1: 6}}
    with pytest.warns(PerformanceWarning):
        inv = inverse(m)

    assert inv[0][0] == pytest.approx(0.6)
    assert inv[0][1] == pytest.approx(-0.7)
    assert inv[1][0] == pytest.approx(-0.2)
    assert inv[1][1] == pytest.approx(0.4)


def test_inverse_singular_raises():
    m = {0: {0: 1, 1: 2}, 1: {0: 2, 1: 4}}  # Det = 0
    with pytest.warns(PerformanceWarning), pytest.raises(ValueError, match='singular'):
        inverse(m)


def test_cofactor():
    m = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
    # C00 = +4, C01 = -3
    # C10 = -2, C11 = +1
    with pytest.warns(PerformanceWarning):
        c = cofactor(m)
    assert c == {0: {0: 4, 1: -3}, 1: {0: -2, 1: 1}}


def test_cofactor_empty():
    with pytest.warns(PerformanceWarning):
        assert cofactor({}) == {}


def test_cofactor_1x1():
    with pytest.warns(PerformanceWarning):
        assert cofactor({0: {0: 5}}) == {0: {0: 1}}


def test_adjoint():
    m = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
    # Adj = C.T = [4 -2]
    #             [-3 1]
    with pytest.warns(PerformanceWarning):
        adj = adjoint(m)
    assert adj == {0: {0: 4, 1: -2}, 1: {0: -3, 1: 1}}


def test_eigen_centrality():
    # 0 <-> 1
    adj = {0: {1: 1}, 1: {0: 1}}
    # Should be equal
    ec = eigen_centrality(adj)
    assert ec[0] == pytest.approx(0.707, 0.01)
    assert ec[1] == pytest.approx(0.707, 0.01)


def test_eigen_centrality_empty():
    assert eigen_centrality({}) == {}


def test_eigen_centrality_zero_matrix():
    # Disconnected nodes with no self-loops -> Matrix is all zeros?
    # No, adjacency usually implies edges.
    # If matrix is zero, vector should remain uniform (or become zero if not normalized?)
    # Our implementation normalizes.
    m = {0: {}, 1: {}}
    ec = eigen_centrality(m)
    assert ec[0] == pytest.approx(0.5)
    assert ec[1] == pytest.approx(0.5)


def test_determinant_pivot_swap():
    m = {0: {1: 1}, 1: {0: 1}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == -1


def test_determinant_already_triangular():
    m = {0: {0: 1, 1: 1}, 1: {1: 1}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == 1


def test_determinant_dense():
    m = {0: {0: 1, 1: 1, 2: 1}, 1: {0: 1, 1: 2, 2: 2}, 2: {0: 1, 1: 2, 2: 3}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == 1


def test_determinant_singular_after_elimination():
    m = {0: {0: 1, 1: 1}, 1: {0: 1, 1: 1}}
    with pytest.warns(PerformanceWarning):
        assert determinant(m) == 0


def test_inverse_scalar_loop():
    m = {0: {0: 2}}
    with pytest.warns(PerformanceWarning):
        inv = inverse(m)
    assert inv == {0: {0: 0.5}}


def test_eigen_centrality_zero_iterations():
    m = {0: {1: 1}, 1: {0: 1}}
    ec = eigen_centrality(m, iterations=0)
    assert ec[0] == pytest.approx(0.5)
    assert ec[1] == pytest.approx(0.5)


def test_cofactor_with_zero_minors():
    m = {0: {0: 1}, 1: {1: 1}, 2: {2: 1}}
    with pytest.warns(PerformanceWarning):
        c = cofactor(m)
    assert c == {0: {0: 1}, 1: {1: 1}, 2: {2: 1}}


def test_determinant_1x1_branch():
    with pytest.warns(PerformanceWarning):
        assert determinant({0: {0: 5.0}}) == 5.0


def test_determinant_n_out_of_bounds():
    with pytest.warns(PerformanceWarning):
        assert determinant({10: {0: 1}}, n=2) == 0
    with pytest.warns(PerformanceWarning):
        assert determinant({0: {10: 1}}, n=2) == 0
