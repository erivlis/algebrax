import math

import pytest

from algebrax.matrix.core import dot, power
from algebrax.semiring import (
    BooleanSemiring,
    BottleneckSemiring,
    LogSemiring,
    ReliabilitySemiring,
    StringSemiring,
    TropicalSemiring,
)


def test_tropical_shortest_path():
    # Graph: 0 -> 1 (weight 1), 1 -> 2 (weight 2), 0 -> 2 (weight 10)
    # Shortest path 0->2 is 0->1->2 (cost 1+2=3). Direct is 10.

    # Adjacency matrix (weights)
    # Missing edge = infinity
    adj = {0: {1: 1.0, 2: 10.0}, 1: {2: 2.0}, 2: {}}

    # Tropical Semiring: (min, +)
    # A^2 gives shortest path of length exactly 2 (or <= 2 if we add I?)
    # Standard power gives length exactly k.

    semiring = TropicalSemiring()

    # Step 1: A^1 = adj

    # Step 2: A^2 = A . A
    # (0, 2) = min( (0,0)+(0,2), (0,1)+(1,2), (0,2)+(2,2) )
    #        = min( inf+10, 1+2, 10+inf ) = 3.

    adj2 = dot(adj, adj, semiring=semiring)
    assert adj2[0][2] == pytest.approx(3.0)

    # Step 3: Power
    # Shortest path with exactly 2 edges
    adj_pow2 = power(adj, 2, semiring=semiring)
    assert adj_pow2[0][2] == pytest.approx(3.0)


def test_boolean_reachability():
    # Graph: 0 -> 1 -> 2
    # 0 can reach 2?

    adj = {0: {1: True}, 1: {2: True}, 2: {}}

    semiring = BooleanSemiring()

    # Reachability in exactly 2 steps
    reach2 = power(adj, 2, semiring=semiring)
    assert reach2[0][2] is True

    # Can't reach 1 in exactly 2 steps (unless loop)
    # Sparse matrix: missing key means False (zero)
    assert reach2[0].get(1, False) is False

    # Transitive closure usually involves (I + A)^N
    # Let's manually add I
    identity_matrix = {0: {0: True}, 1: {1: True}, 2: {2: True}}

    # Manual union of A and I (element-wise OR)
    adj_plus_identity = {}
    keys = set(adj.keys()) | set(identity_matrix.keys())
    for k in keys:
        row_a = adj.get(k, {})
        row_i = identity_matrix.get(k, {})
        # Union of rows
        new_row = row_a.copy()
        new_row.update(row_i)
        adj_plus_identity[k] = new_row

    # (I+A)^2 covers paths of length 0, 1, 2
    reach_all = power(adj_plus_identity, 2, semiring=semiring)
    assert reach_all[0][2] is True
    assert reach_all[0][1] is True
    assert reach_all[0][0] is True


def test_bottleneck_capacity():
    # Graph: 0 -> 1 (cap 10), 1 -> 2 (cap 5)
    # Path capacity = min(10, 5) = 5.
    # Max capacity path = max over all paths.

    adj = {0: {1: 10.0}, 1: {2: 5.0}, 2: {}}

    semiring = BottleneckSemiring()

    # Capacity of path length 2
    # (0, 2) = max( min(10, 5) ) = 5
    res = power(adj, 2, semiring=semiring)
    assert res[0][2] == pytest.approx(5.0)


def test_log_semiring():
    # Probabilities: 0->1 (0.5), 1->2 (0.5)
    # Path prob = 0.25.
    # Log probs: log(0.5) approx -0.693
    # Path log prob = -0.693 + -0.693 = -1.386

    lp = math.log(0.5)
    adj = {0: {1: lp}, 1: {2: lp}, 2: {}}

    semiring = LogSemiring()

    res = power(adj, 2, semiring=semiring)
    assert res[0][2] == pytest.approx(2 * lp)

    # Addition in LogSemiring is logaddexp
    # log(exp(a) + exp(b))
    # If we have two paths 0->2 with log probs a and b
    # Total prob = exp(a) + exp(b)
    # Total log prob = log(exp(a) + exp(b))

    # Graph: 0->1 (p=0.5), 0->2 (p=0.1)
    #        1->3 (p=0.5), 2->3 (p=0.5)
    # Path 1: 0->1->3 (p=0.25)
    # Path 2: 0->2->3 (p=0.05)
    # Total p = 0.30. Log(0.30) approx -1.204

    lp1 = math.log(0.5)
    lp2 = math.log(0.1)

    adj_multi = {0: {1: lp1, 2: lp2}, 1: {3: lp1}, 2: {3: lp1}, 3: {}}

    res_multi = power(adj_multi, 2, semiring=semiring)
    expected = math.log(0.25 + 0.05)
    assert res_multi[0][3] == pytest.approx(expected)


def test_log_semiring_edge_cases():
    semiring = LogSemiring()
    neg_inf = float('-inf')

    # add(-inf, x) = x
    assert semiring.add(neg_inf, 5.0) == pytest.approx(5.0)
    assert semiring.add(5.0, neg_inf) == pytest.approx(5.0)
    assert semiring.add(neg_inf, neg_inf) == neg_inf


def test_string_semiring():
    # Graph: 0 -a-> 1 -b-> 2
    #        0 -c-> 1
    # Paths 0->2: "ab", "cb"

    adj = {0: {1: {'a', 'c'}}, 1: {2: {'b'}}, 2: {}}

    semiring = StringSemiring()

    res = power(adj, 2, semiring=semiring)
    assert res[0][2] == {'ab', 'cb'}


def test_string_semiring_empty():
    semiring = StringSemiring()
    # mul(empty, x) = empty
    assert semiring.mul(set(), {'a'}) == set()
    assert semiring.mul({'a'}, set()) == set()


def test_reliability_semiring():
    # Same as Viterbi
    semiring = ReliabilitySemiring()
    assert semiring.add(0.5, 0.8) == pytest.approx(0.8)  # max
    assert semiring.mul(0.5, 0.5) == pytest.approx(0.25)  # mul
    assert semiring.zero == pytest.approx(0.0)
    assert semiring.one == pytest.approx(1.0)
