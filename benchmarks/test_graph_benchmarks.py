"""Benchmarks for graph calculus, probability, automata, lattice operations and metrics."""

import operator
import sys

import pytest

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from _generators import distribution, graph, rng, sparse_matrix, sparse_signal, stochastic_matrix

import algebrax as ax

# region Vector Calculus on Graphs


@pytest.mark.benchmark(group="analysis-laplacian")
@pytest.mark.parametrize("density", [0.05, 0.25])
def test_benchmark_analysis_laplacian(benchmark, density: float):
    g = graph(120, density, seed=1)
    field = {node: float(node % 17) for node in g}

    result = benchmark(ax.analysis.laplacian, field, g)
    assert result is not None


@pytest.mark.benchmark(group="analysis-gradient")
def test_benchmark_analysis_gradient(benchmark):
    g = graph(120, 0.15, seed=1)
    field = {node: float(node % 17) for node in g}

    result = benchmark(ax.analysis.gradient, field, g)
    assert result is not None


@pytest.mark.benchmark(group="analysis-divergence")
def test_benchmark_analysis_divergence(benchmark):
    g = graph(120, 0.15, seed=1)
    field = {node: float(node % 17) for node in g}
    flow = ax.analysis.gradient(field, g)

    result = benchmark(ax.analysis.divergence, flow)
    assert result is not None


@pytest.mark.benchmark(group="analysis-forman-ricci")
@pytest.mark.parametrize("weighted", [False, True])
def test_benchmark_analysis_forman_ricci(benchmark, weighted: bool):
    g = graph(60, 0.15, seed=1, weighted=weighted)

    result = benchmark(ax.analysis.forman_ricci_curvature, g, weighted)
    assert result is not None


@pytest.mark.benchmark(group="analysis-gaussian-kernel")
def test_benchmark_analysis_gaussian_kernel(benchmark):
    distances = sparse_matrix(80, 80, 0.25, seed=1)

    result = benchmark(ax.analysis.gaussian_kernel, distances, 2.0)
    assert result is not None


# endregion


# region Probability & Information Theory


@pytest.mark.benchmark(group="probability-information")
@pytest.mark.parametrize("measure", ["entropy", "kl_divergence", "cross_entropy"])
def test_benchmark_probability_information(benchmark, measure: str):
    p = distribution(500, seed=1)
    q = distribution(500, seed=2)

    if measure == "entropy":
        result = benchmark(ax.probability.entropy, p)
    elif measure == "kl_divergence":
        result = benchmark(ax.probability.kl_divergence, p, q)
    else:
        result = benchmark(ax.probability.cross_entropy, p, q)

    assert result is not None


@pytest.mark.benchmark(group="probability-mutual-information")
def test_benchmark_probability_mutual_information(benchmark):
    joint = stochastic_matrix(60, 0.3, seed=1)
    total = sum(sum(row.values()) for row in joint.values())
    joint = {k: {j: v / total for j, v in row.items()} for k, row in joint.items()}

    result = benchmark(ax.probability.mutual_information, joint)
    assert result is not None


@pytest.mark.benchmark(group="probability-markov")
@pytest.mark.parametrize("steps", [1, 25])
def test_benchmark_probability_markov_step(benchmark, steps: int):
    transitions = stochastic_matrix(80, 0.2, seed=1)
    state = distribution(80, seed=2)

    result = benchmark(ax.probability.markov_step, state, transitions, steps)
    assert result is not None


@pytest.mark.benchmark(group="probability-markov")
def test_benchmark_probability_markov_steady_state(benchmark):
    transitions = stochastic_matrix(80, 0.2, seed=1)

    result = benchmark(ax.probability.markov_steady_state, transitions)
    assert result is not None


@pytest.mark.benchmark(group="probability-moments")
@pytest.mark.parametrize("moment", ["variance", "skewness", "kurtosis"])
def test_benchmark_probability_moments(benchmark, moment: str):
    dist = distribution(1000, seed=1)
    func = getattr(ax.probability, moment)

    result = benchmark(func, dist)
    assert result is not None


# endregion


# region Automata


@pytest.mark.benchmark(group="automata-dfa")
def test_benchmark_automata_simulate_dfa(benchmark):
    rand = rng(3)
    states = list(range(20))
    alphabet = "abcd"
    transitions = {s: {a: rand.choice(states) for a in alphabet} for s in states}
    sequence = {i: rand.choice(alphabet) for i in range(2_000)}

    result = benchmark(ax.automata.simulate_dfa, 0, sequence, transitions)
    assert result is not None


@pytest.mark.benchmark(group="automata-nfa")
def test_benchmark_automata_simulate_nfa(benchmark):
    rand = rng(4)
    states = list(range(12))
    alphabet = "abc"
    transitions = {
        s: {a: {rand.choice(states): rand.uniform(0.1, 1.0) for _ in range(3)} for a in alphabet} for s in states
    }
    sequence = {i: rand.choice(alphabet) for i in range(200)}

    result = benchmark(ax.automata.simulate_nfa, {0: 1.0}, sequence, transitions)
    assert result is not None


# endregion


# region Lattice Operations


@pytest.mark.benchmark(group="lattice-set-ops")
@pytest.mark.parametrize("op", ["join", "meet", "difference", "symmetric_difference"])
def test_benchmark_lattice_set_ops(benchmark, op: str):
    m_a = sparse_signal(2_000, 0.6, seed=1)
    m_b = sparse_signal(2_000, 0.6, seed=2)
    func = getattr(ax.lattice, op)

    result = benchmark(func, m_a, m_b)
    assert result is not None


@pytest.mark.benchmark(group="lattice-combine")
@pytest.mark.parametrize("domain", ["union", "intersection"])
def test_benchmark_lattice_combine(benchmark, domain: str):
    m_a = sparse_signal(2_000, 0.6, seed=1)
    m_b = sparse_signal(2_000, 0.6, seed=2)
    key_domain = set.union if domain == "union" else set.intersection

    result = benchmark(ax.lattice.combine, m_a, m_b, operator.add, 0, key_domain)
    assert result is not None


@pytest.mark.benchmark(group="lattice-means")
@pytest.mark.parametrize("mean", ["average", "geometric_mean", "harmonic_mean"])
def test_benchmark_lattice_means(benchmark, mean: str):
    m_a = sparse_signal(2_000, 0.6, seed=1)
    m_b = sparse_signal(2_000, 0.6, seed=2)
    func = getattr(ax.lattice, mean)

    result = benchmark(func, m_a, m_b)
    assert result is not None


# endregion


# region Metrics


@pytest.mark.benchmark(group="metrics-fractal")
def test_benchmark_metrics_box_counting_dimension(benchmark):
    rand = rng(5)
    points = {(rand.randint(0, 255), rand.randint(0, 255)): 1.0 for _ in range(2_000)}

    result = benchmark(ax.metrics.box_counting_dimension, points)
    assert result is not None


@pytest.mark.benchmark(group="metrics-shape")
@pytest.mark.parametrize("metric", ["deepness", "wideness", "count_elements"])
def test_benchmark_metrics_shape(benchmark, metric: str):
    tree = sparse_matrix(120, 120, 0.3, seed=1)
    func = getattr(ax.metrics, metric)

    result = benchmark(func, tree)
    assert result is not None


@pytest.mark.benchmark(group="metrics-uniformness")
def test_benchmark_metrics_uniformness(benchmark):
    tree = sparse_matrix(120, 120, 0.3, seed=1)

    result = benchmark(ax.metrics.uniformness, tree)
    assert result is not None


# endregion
