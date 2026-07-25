import math

import pytest

from algebrax.probability import (
    bayes_update,
    cross_entropy,
    entropy,
    expected_value,
    kl_divergence,
    kurtosis,
    marginalize,
    markov_steady_state,
    markov_step,
    mode,
    mutual_information,
    normalize,
    skewness,
    variance,
)


def test_normalize():
    d = {'a': 2, 'b': 8}
    n = normalize(d)
    assert n['a'] == pytest.approx(0.2)
    assert n['b'] == pytest.approx(0.8)


def test_normalize_zero_raises():
    with pytest.raises(ValueError):
        normalize({'a': 0})


def test_marginalize():
    # P(X, Y)
    # X=0: Y=0(0.1), Y=1(0.2) -> Sum=0.3
    # X=1: Y=0(0.3), Y=1(0.4) -> Sum=0.7
    joint = {0: {0: 0.1, 1: 0.2}, 1: {0: 0.3, 1: 0.4}}

    # Axis 1 (sum columns -> P(X))
    px = marginalize(joint, axis=1)
    assert px[0] == pytest.approx(0.3)
    assert px[1] == pytest.approx(0.7)

    # Axis 0 (sum rows -> P(Y))
    py = marginalize(joint, axis=0)
    assert py[0] == pytest.approx(0.4)
    assert py[1] == pytest.approx(0.6)


def test_marginalize_invalid_axis():
    with pytest.raises(ValueError):
        marginalize({}, axis=2)


def test_bayes_update():
    prior = {'H1': 0.5, 'H2': 0.5}
    likelihood = {'H1': 0.8, 'H2': 0.1}  # P(E|H)

    # P(E) = 0.5*0.8 + 0.5*0.1 = 0.45
    # P(H1|E) = 0.4 / 0.45 = 8/9 approx 0.888
    # P(H2|E) = 0.05 / 0.45 = 1/9 approx 0.111

    post = bayes_update(prior, likelihood)
    assert post['H1'] == pytest.approx(8 / 9)
    assert post['H2'] == pytest.approx(1 / 9)


def test_bayes_update_empty():
    assert bayes_update({}, {}) == {}


def test_bayes_update_with_evidence():
    prior = {'H1': 0.5}
    likelihood = {'H1': 0.8}
    # Unnormalized = 0.4. Evidence = 0.4. Result = 1.0
    post = bayes_update(prior, likelihood, evidence=0.4)
    assert post['H1'] == pytest.approx(1.0)


def test_entropy():
    # Uniform: -log2(0.5) = 1 bit
    d = {'a': 0.5, 'b': 0.5}
    assert entropy(d) == pytest.approx(1.0)

    # Certainty: 0 bits
    d2 = {'a': 1.0, 'b': 0.0}
    assert entropy(d2) == pytest.approx(0.0)


def test_cross_entropy():
    p = {'a': 0.5, 'b': 0.5}
    q = {'a': 0.5, 'b': 0.5}
    assert cross_entropy(p, q) == pytest.approx(1.0)

    # Infinite
    p2 = {'a': 1.0}
    q2 = {'a': 0.0}  # log(0)
    assert cross_entropy(p2, q2) == float('inf')


def test_cross_entropy_inf():
    p = {0: 0.5}
    q = {0: 0.0}  # q(x) is 0 where p(x) > 0
    assert cross_entropy(p, q) == float('inf')


def test_kl_divergence():
    p = {'a': 0.5, 'b': 0.5}
    q = {'a': 0.25, 'b': 0.75}
    # 0.5 * log2(0.5/0.25) + 0.5 * log2(0.5/0.75)
    # 0.5 * 1 + 0.5 * log2(2/3)
    # 0.5 + 0.5 * (1 - 1.58) = 0.5 - 0.29 = 0.2075
    val = 0.5 * math.log2(2) + 0.5 * math.log2(2 / 3)
    assert kl_divergence(p, q) == pytest.approx(val)


def test_kl_divergence_infinite():
    p = {'a': 0.5}
    q = {'a': 0.0}
    assert kl_divergence(p, q) == float('inf')


def test_kl_divergence_inf_coverage():
    # Duplicate of above but ensures explicit coverage if slightly different paths exist
    p = {0: 0.5}
    q = {0: 0.0}
    assert kl_divergence(p, q) == float('inf')


def test_mutual_information():
    # Independent X, Y -> MI = 0
    # P(X) = 0.5, 0.5. P(Y) = 0.5, 0.5
    # P(X,Y) = 0.25 for all
    joint = {0: {0: 0.25, 1: 0.25}, 1: {0: 0.25, 1: 0.25}}
    assert mutual_information(joint) == pytest.approx(0.0)

    # Perfectly dependent X=Y
    # P(0,0)=0.5, P(1,1)=0.5
    joint_dep = {0: {0: 0.5}, 1: {1: 0.5}}
    # H(X)=1, H(Y)=1, H(X,Y)=1. MI = 1+1-1 = 1.
    assert mutual_information(joint_dep) == pytest.approx(1.0)


def test_markov():
    # 0 -> 1 (1.0)
    # 1 -> 0 (1.0)
    transition = {0: {1: 1.0}, 1: {0: 1.0}}
    state = {0: 1.0}

    # Step 1: {1: 1.0}
    s1 = markov_step(state, transition, 1)
    assert s1[1] == pytest.approx(1.0)

    # Steady state: {0: 0.5, 1: 0.5}
    ss = markov_steady_state(transition)
    assert ss[0] == pytest.approx(0.5)
    assert ss[1] == pytest.approx(0.5)


def test_markov_steady_state_convergence():
    # Simple case that converges quickly
    # 0 -> 1, 1 -> 0
    P = {0: {1: 1.0}, 1: {0: 1.0}}  # noqa: N806
    # Steady state is 0.5, 0.5
    # This should hit the tolerance break
    steady = markov_steady_state(P, iterations=100, tolerance=1e-5)
    assert steady[0] == pytest.approx(0.5)
    assert steady[1] == pytest.approx(0.5)


def test_markov_steady_state_empty():
    assert markov_steady_state({}) == {}


def test_expected_value():
    # Uniform: 1, 2, 3, 4. Mean = 2.5
    dist = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}
    assert expected_value(dist) == pytest.approx(2.5)

    # Skewed: 1 (0.8), 10 (0.2). Mean = 0.8 + 2.0 = 2.8
    dist2 = {1: 0.8, 10: 0.2}
    assert expected_value(dist2) == pytest.approx(2.8)


def test_expected_value_type_error():
    # String keys should fail
    with pytest.raises(TypeError):
        expected_value({'a': 0.5, 'b': 0.5})


def test_variance():
    # Uniform: 1, 2, 3, 4. Mean=2.5
    # Var = E[X^2] - (E[X])^2
    # E[X^2] = 0.25*(1+4+9+16) = 0.25*30 = 7.5
    # Var = 7.5 - 2.5^2 = 7.5 - 6.25 = 1.25
    dist = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}
    assert variance(dist) == pytest.approx(1.25)

    # Constant: Var = 0
    dist2 = {5: 1.0}
    assert variance(dist2) == pytest.approx(0.0)


def test_variance_precomputed():
    # Test with precomputed mean
    dist = {1: 0.25, 2: 0.25, 3: 0.25, 4: 0.25}
    # Mean is 2.5
    var = variance(dist, mu=2.5)
    assert var == pytest.approx(1.25)


def test_skewness():
    # Symmetric: Skewness = 0
    dist = {-1: 0.25, 1: 0.25, -2: 0.25, 2: 0.25}
    assert skewness(dist) == pytest.approx(0.0)

    # Right skewed (tail on right)
    # 1 (0.9), 10 (0.1)
    # Mean = 0.9 + 1 = 1.9
    # Var = 0.9*(1-1.9)^2 + 0.1*(10-1.9)^2 = 0.9*0.81 + 0.1*65.61 = 0.729 + 6.561 = 7.29
    # Sigma = sqrt(7.29) = 2.7
    # M3 = 0.9*(1-1.9)^3 + 0.1*(10-1.9)^3 = 0.9*(-0.729) + 0.1*(531.441) = -0.6561 + 53.1441 = 52.488
    # Skew = 52.488 / (2.7^3) = 52.488 / 19.683 = 2.666...
    dist2 = {1: 0.9, 10: 0.1}
    assert skewness(dist2) > 0


def test_skewness_precomputed():
    # Test with precomputed mu and sigma
    dist = {-1: 0.25, 1: 0.25, -2: 0.25, 2: 0.25}
    # Mean = 0
    # Var = 0.25*(1+1+4+4) = 2.5. Sigma = sqrt(2.5)
    skew = skewness(dist, mu=0.0, sigma=math.sqrt(2.5))
    assert skew == pytest.approx(0.0)


def test_skewness_zero_variance():
    # Constant distribution -> Sigma = 0
    dist = {5: 1.0}
    assert skewness(dist) == pytest.approx(0.0)


def test_kurtosis():
    # Normal-ish (Binomial n=4, p=0.5) -> 0, 1, 2, 3, 4
    # 1, 4, 6, 4, 1 / 16
    dist = {0: 1 / 16, 1: 4 / 16, 2: 6 / 16, 3: 4 / 16, 4: 1 / 16}
    # Kurtosis of Normal is 3. Excess is 0.
    # This implementation returns raw Kurtosis (so approx 3).
    # Binomial Kurtosis = 3 + (1-6p(1-p))/(np(1-p))
    # p=0.5 -> 1-6(0.25) = -0.5. np(1-p) = 4*0.25 = 1.
    # Kurt = 3 - 0.5 = 2.5
    assert kurtosis(dist) == pytest.approx(2.5)


def test_kurtosis_precomputed():
    # Test with precomputed mu and sigma
    dist = {0: 1 / 16, 1: 4 / 16, 2: 6 / 16, 3: 4 / 16, 4: 1 / 16}
    # Mean = 2
    # Var = 1. Sigma = 1
    kurt = kurtosis(dist, mu=2.0, sigma=1.0)
    assert kurt == pytest.approx(2.5)


def test_kurtosis_zero_variance():
    # Constant distribution -> Sigma = 0
    dist = {5: 1.0}
    assert kurtosis(dist) == pytest.approx(0.0)


def test_mode():
    dist = {'a': 0.1, 'b': 0.6, 'c': 0.3}
    assert mode(dist) == 'b'

    # Numeric
    dist2 = {1: 0.2, 2: 0.5, 3: 0.3}
    assert mode(dist2) == 2


def test_mode_empty():
    with pytest.raises(ValueError):
        mode({})
