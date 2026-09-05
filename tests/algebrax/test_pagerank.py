"""
Unit test suite for algebraic PageRank and Random Walk with Restart (EP-0151).

Verifies:
1. Analytical stationary distribution for symmetric cycles and cliques.
2. Directed star graphs and flow accumulation.
3. Dangling sink nodes and exact mass conservation (sum == 1.0).
4. Personalized PageRank (topic-sensitive / seed-biased random walks).
5. Custom dangling redistribution vectors.
6. Boundary conditions (damping = 0.0, single-node, empty graph).
7. Weighted transition normalization.
8. Disconnected components and reachability.
9. Semiring parameter normalization (class vs instance).
10. Error validation and exception handling.
11. Public cross-exports across algebrax.analysis and algebrax.probability.
"""

import pytest

import algebrax as ax
from algebrax.analysis import pagerank
from algebrax.probability import pagerank as prob_pagerank
from algebrax.semiring import StandardSemiring


def test_pagerank_empty_and_trivial():
    """Empty graphs and single-node graphs return proper base cases."""
    assert pagerank({}) == {}
    assert pagerank({1: {}}) == {1: 1.0}
    assert pagerank({'a': {'a': 10.0}}) == {'a': 1.0}


def test_pagerank_symmetric_cycle():
    """Directed cycle graphs have uniform stationary distribution by symmetry."""
    # 2-cycle
    g2 = {'a': {'b': 1.0}, 'b': {'a': 1.0}}
    pr2 = pagerank(g2)
    assert pytest.approx(pr2['a'], rel=1e-5) == 0.5
    assert pytest.approx(pr2['b'], rel=1e-5) == 0.5
    assert pytest.approx(sum(pr2.values()), rel=1e-6) == 1.0

    # 3-cycle
    g3 = {0: {1: 1.0}, 1: {2: 1.0}, 2: {0: 1.0}}
    pr3 = pagerank(g3)
    for i in range(3):
        assert pytest.approx(pr3[i], rel=1e-5) == 1.0 / 3.0
    assert pytest.approx(sum(pr3.values()), rel=1e-6) == 1.0


def test_pagerank_star_graph():
    """Center of a star graph accumulates higher centrality than leaves."""
    g = {
        'center': {'l1': 1.0, 'l2': 1.0, 'l3': 1.0},
        'l1': {'center': 1.0},
        'l2': {'center': 1.0},
        'l3': {'center': 1.0},
    }
    pr = pagerank(g, damping=0.85)
    assert pr['center'] > pr['l1']
    assert pytest.approx(pr['l1'], rel=1e-5) == pr['l2']
    assert pytest.approx(pr['l2'], rel=1e-5) == pr['l3']
    assert pytest.approx(sum(pr.values()), rel=1e-6) == 1.0


def test_pagerank_dangling_sinks_and_mass_conservation():
    """Graphs with dangling nodes (sinks) conserve total mass and match analytical solution."""
    # Line a -> b -> c (c has no outgoing edges)
    line = {
        'a': {'b': 1.0},
        'b': {'c': 1.0},
        'c': {},
    }
    alpha = 0.85
    pr = pagerank(line, damping=alpha, tol=1e-10, max_iter=200)

    # Unit probability mass conservation
    assert pytest.approx(sum(pr.values()), abs=1e-7) == 1.0

    # In a -> b -> c, c is downstream of all flow, so p(c) > p(b) > p(a)
    assert pr['c'] > pr['b'] > pr['a']

    # Analytical derivation for line a -> b -> c with uniform teleportation and sink redistribution:
    # Let v = 1/3, m_c = p_c
    # p_a = (1-alpha)/3 + alpha * p_c / 3
    # p_b = (1-alpha)/3 + alpha * p_a + alpha * p_c / 3
    # p_c = (1-alpha)/3 + alpha * p_b + alpha * p_c / 3
    # With alpha = 0.85:
    # p_a = 0.05 + (0.85/3) * p_c
    # p_b - p_a = 0.85 * p_a => p_b = 1.85 * p_a
    # p_c - p_b = 0.85 * (p_b - p_a) = 0.85 * 0.85 * p_a => p_c = p_b + 0.7225 * p_a = 2.5725 * p_a
    # Sum: p_a * (1 + 1.85 + 2.5725) = 5.4225 * p_a = 1.0 => p_a = 1 / 5.4225 ≈ 0.184417
    expected_pa = 1.0 / (1.0 + (1.0 + alpha) + (1.0 + alpha + alpha**2))
    expected_pb = (1.0 + alpha) * expected_pa
    expected_pc = (1.0 + alpha + alpha**2) * expected_pa

    assert pytest.approx(pr['a'], rel=1e-4) == expected_pa
    assert pytest.approx(pr['b'], rel=1e-4) == expected_pb
    assert pytest.approx(pr['c'], rel=1e-4) == expected_pc


def test_pagerank_personalized():
    """Personalized PageRank biases random walk toward specified seed nodes."""
    line = {
        'a': {'b': 1.0},
        'b': {'c': 1.0},
        'c': {'a': 1.0},
    }
    # Unpersonalized: uniform 1/3 each
    pr_uniform = pagerank(line)
    assert pytest.approx(pr_uniform['a'], rel=1e-5) == 1.0 / 3.0

    # Personalized entirely to 'a'
    pr_a = pagerank(line, personalization={'a': 1.0, 'b': 0.0, 'c': 0.0})
    assert pr_a['a'] > pr_uniform['a']
    assert pr_a['b'] < pr_a['a']
    assert pytest.approx(sum(pr_a.values()), rel=1e-6) == 1.0

    # Personalized to 'b'
    pr_b = pagerank(line, personalization={'b': 1.0})
    assert pr_b['b'] > pr_b['a']
    assert pr_b['b'] > pr_b['c']


def test_pagerank_custom_dangling():
    """Custom dangling vector routes dead-end mass back to specific nodes."""
    line = {
        'a': {'b': 1.0},
        'b': {'c': 1.0},
    }
    # When c is a sink, redirecting c back to a boosts a
    pr_default = pagerank(line)
    pr_custom_sink = pagerank(line, dangling={'a': 1.0, 'b': 0.0, 'c': 0.0})

    assert pr_custom_sink['a'] > pr_default['a']
    assert pytest.approx(sum(pr_custom_sink.values()), rel=1e-6) == 1.0


def test_pagerank_damping_extremes():
    """At damping=0, output is exactly the personalization vector."""
    g = {'a': {'b': 1.0}, 'b': {'a': 1.0}}
    pers = {'a': 0.75, 'b': 0.25}

    pr_zero = pagerank(g, damping=0.0, personalization=pers)
    assert pytest.approx(pr_zero['a'], rel=1e-6) == 0.75
    assert pytest.approx(pr_zero['b'], rel=1e-6) == 0.25

    # Near 1.0 damping converges stably
    pr_high = pagerank(g, damping=0.99, max_iter=300)
    assert pytest.approx(pr_high['a'], rel=1e-4) == 0.5
    assert pytest.approx(pr_high['b'], rel=1e-4) == 0.5


def test_pagerank_weighted_transitions():
    """Transition probabilities reflect relative edge weights."""
    g = {
        'src': {'dst1': 3.0, 'dst2': 1.0},
        'dst1': {'src': 1.0},
        'dst2': {'src': 1.0},
    }
    pr = pagerank(g, damping=0.85)
    # dst1 received 3x the transition probability of dst2
    assert pr['dst1'] > pr['dst2']
    assert pytest.approx(sum(pr.values()), rel=1e-6) == 1.0


def test_pagerank_disconnected_components():
    """Teleportation connects disconnected graph components."""
    g = {
        1: {2: 1.0},
        2: {1: 1.0},
        3: {4: 1.0},
        4: {3: 1.0},
    }
    pr = pagerank(g)
    for k in [1, 2, 3, 4]:
        assert pytest.approx(pr[k], rel=1e-5) == 0.25
    assert pytest.approx(sum(pr.values()), rel=1e-6) == 1.0


def test_pagerank_semiring_classes_and_instances():
    """Accepts semiring as instance or class factory."""
    g = {'a': {'b': 1.0}, 'b': {'a': 1.0}}
    pr_inst = pagerank(g, semiring=StandardSemiring())
    pr_cls = pagerank(g, semiring=StandardSemiring)
    assert pr_inst == pr_cls


def test_pagerank_validation_errors():
    """Validates parameters and raises ValueError on malformed inputs."""
    g = {'a': {'b': 1.0}}

    with pytest.raises(ValueError, match=r'damping must be between 0\.0 and 1\.0'):
        pagerank(g, damping=-0.1)

    with pytest.raises(ValueError, match=r'damping must be between 0\.0 and 1\.0'):
        pagerank(g, damping=1.05)

    with pytest.raises(ValueError, match='max_iter must be a positive integer'):
        pagerank(g, max_iter=0)

    with pytest.raises(ValueError, match='tol must be non-negative'):
        pagerank(g, tol=-1e-4)

    with pytest.raises(ValueError, match='Personalization values must be non-negative'):
        pagerank(g, personalization={'a': -0.5, 'b': 1.5})

    with pytest.raises(ValueError, match='Personalization vector must have a positive sum'):
        pagerank(g, personalization={'a': 0.0, 'b': 0.0})

    with pytest.raises(ValueError, match='Dangling values must be non-negative'):
        pagerank(g, dangling={'a': -1.0})

    with pytest.raises(ValueError, match='Dangling vector must have a positive sum'):
        pagerank(g, dangling={'a': 0.0})


def test_pagerank_cross_exports():
    """Cross-exports are identical across analysis and probability."""
    assert prob_pagerank is pagerank
    assert ax.analysis.pagerank is pagerank
    assert ax.probability.pagerank is pagerank
