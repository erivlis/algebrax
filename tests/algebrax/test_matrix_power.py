import pytest

from algebrax.matrix import power


def test_matrix_power_identity():
    """Test that M^0 is the identity matrix."""
    m = {0: {0: 2, 1: 3}, 1: {0: 4, 1: 5}}
    identity = power(m, 0)

    assert identity == {0: {0: 1}, 1: {1: 1}}

def test_matrix_power_one():
    """Test that M^1 is M."""
    m = {0: {0: 2, 1: 3}, 1: {0: 4, 1: 5}}
    m1 = power(m, 1)

    # power might return sparse structure (missing zeros), but input is dense-ish
    # Let's check equality. power() implementation constructs new dicts.
    assert m1 == m

def test_matrix_power_fibonacci():
    """
    Test matrix exponentiation using Fibonacci sequence.
    [1 1] ^ n  =  [F(n+1) F(n)  ]
    [1 0]         [F(n)   F(n-1)]
    """
    # Q matrix for Fibonacci
    q_matrix = {0: {0: 1, 1: 1}, 1: {0: 1}}  # 1: {1: 0} is implicit sparse

    # F(0)=0, F(1)=1, F(2)=1, F(3)=2, F(4)=3, F(5)=5, F(6)=8

    # n=5
    q5 = power(q_matrix, 5)
    # Expected: [[8, 5], [5, 3]]
    assert q5[0][0] == 8  # F(6)
    assert q5[0][1] == 5  # F(5)
    assert q5[1][0] == 5  # F(5)
    assert q5[1][1] == 3  # F(4)

    # n=10
    # F(10) = 55, F(11) = 89
    q10 = power(q_matrix, 10)
    assert q10[0][1] == 55

def test_matrix_power_graph_paths():
    """
    Test that (Adj)^k[i][j] counts paths of length k from i to j.
    Graph: 0 -> 1 -> 2
           ^         |
           |_________|
    Cycle: 0->1->2->0 (Length 3)
    """
    # Adjacency matrix
    adj = {
        0: {1: 1},
        1: {2: 1},
        2: {0: 1}
    }

    # 3 steps: Should be identity (paths of length 3 are loops)
    adj3 = power(adj, 3)
    assert adj3[0][0] == 1
    assert adj3[1][1] == 1
    assert adj3[2][2] == 1

    # 0->1 is 1 step. In 3 steps 0->1->2->0.
    # In 4 steps: 0->1->2->0->1. So adj4[0][1] should be 1.
    adj4 = power(adj, 4)
    assert adj4[0][1] == 1

def test_matrix_power_negative_raises():
    """Test that negative exponent raises ValueError."""
    m = {0: {0: 1}}
    with pytest.raises(ValueError):
        power(m, -1)
