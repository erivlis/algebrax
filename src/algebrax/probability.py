import math
from collections import defaultdict

from algebrax.lattice import product
from algebrax.matrix.core import vec_mat
from algebrax.typing import K, N, SparseMatrix, SparseVector

__all__ = [
    'bayes_update',
    'cross_entropy',
    'entropy',
    'expected_value',
    'kl_divergence',
    'kurtosis',
    'marginalize',
    'markov_steady_state',
    'markov_step',
    'mode',
    'mutual_information',
    'normalize',
    'skewness',
    'variance',
]


def bayes_update(
    prior: SparseVector[K, float],
    likelihood: SparseVector[K, float],
    evidence: float | None = None,
) -> SparseVector[K, float]:
    """
    Perform a Bayesian update of a probability distribution.
    Posterior(H) = Likelihood(D|H) * Prior(H) / Evidence(D)

    Args:
        prior: The prior probability distribution P(H).
        likelihood: The likelihood of the data given the hypothesis P(D|H).
        evidence: The total probability of the data P(D).
                  If None, it is computed by normalizing the result.

    Returns:
        The posterior probability distribution P(H|D).
    """
    # Unnormalized posterior = Prior * Likelihood (Hadamard product)
    posterior = product(prior, likelihood)

    if not posterior:
        return {}

    if evidence is None:
        return normalize(posterior)

    return {k: v / evidence for k, v in posterior.items()}


def cross_entropy(
    p: SparseVector[K, float],
    q: SparseVector[K, float],
    base: float = 2.0,
) -> float:
    """
    Compute the Cross-Entropy between two probability distributions.
    H(P, Q) = - sum(P(x) * log(Q(x)))

    Args:
        p: The true distribution.
        q: The predicted distribution.
        base: Logarithm base (default 2 for bits).

    Returns:
        The cross-entropy value.
    """
    result = 0.0
    for k, prob_p in p.items():
        if prob_p > 0:
            prob_q = q.get(k, 0.0)
            if prob_q > 0:
                result -= prob_p * math.log(prob_q, base)
            else:
                return float('inf')
    return result


def entropy(
    distribution: SparseVector[K, float],
    base: float = 2.0,
) -> float:
    """
    Compute the Shannon Entropy of a probability distribution.
    H(X) = - sum(P(x) * log(P(x)))

    Args:
        distribution: A mapping representing probabilities.
        base: Logarithm base (default 2 for bits).

    Returns:
        The entropy value.
    """
    result = 0.0
    for prob in distribution.values():
        if prob > 0:
            result -= prob * math.log(prob, base)
    return result


def expected_value(distribution: SparseVector[N, float]) -> float:
    """
    Compute the Expected Value (Mean) of a probability distribution.
    E[X] = sum(x * P(x))

    Args:
        distribution: A mapping where keys are numeric outcomes and values are probabilities.

    Returns:
        The expected value.

    Raises:
        TypeError: If keys are not numeric.
    """
    return sum(k * v for k, v in distribution.items())


def kl_divergence(
    p: SparseVector[K, float],
    q: SparseVector[K, float],
    base: float = 2.0,
) -> float:
    """
    Compute the Kullback-Leibler (KL) Divergence.
    D_KL(P || Q) = sum(P(x) * log(P(x) / Q(x)))

    Args:
        p: The true distribution.
        q: The reference distribution.
        base: Logarithm base (default 2 for bits).

    Returns:
        The KL divergence value.
    """
    result = 0.0
    for k, prob_p in p.items():
        if prob_p > 0:
            prob_q = q.get(k, 0.0)
            if prob_q > 0:
                result += prob_p * math.log(prob_p / prob_q, base)
            else:
                return float('inf')
    return result


def kurtosis(distribution: SparseVector[N, float], mu: float | None = None, sigma: float | None = None) -> float:
    """
    Compute the Kurtosis (4th standardized moment) of a probability distribution.
    Kurt[X] = E[(X - mu)^4] / sigma^4

    Args:
        distribution: A mapping where keys are numeric outcomes and values are probabilities.
        mu: Precomputed mean (optional).
        sigma: Precomputed standard deviation (optional).

    Returns:
        The kurtosis value.
    """
    if mu is None:
        mu = expected_value(distribution)

    # Calculate 4th central moment
    m4 = sum(((k - mu) ** 4) * v for k, v in distribution.items())

    if sigma is None:
        var = sum(((k - mu) ** 2) * v for k, v in distribution.items())
        sigma = var**0.5

    if sigma == 0:
        return 0.0

    return m4 / (sigma**4)


def marginalize(matrix: SparseMatrix[K, N], axis: int = 0) -> SparseVector[K, N]:
    """
    Marginalize a matrix by summing over an axis.

    Args:
        matrix: The input matrix.
        axis: 0 to sum over columns (produce row sums), 1 to sum over rows (produce column sums).
              Note: This follows numpy convention.
              axis=0 -> collapses rows, returns sums of columns.
              axis=1 -> collapses columns, returns sums of rows.

    Returns:
        A dictionary representing the marginal distribution.
    """
    if axis == 1:
        return {r: sum(row.values()) for r, row in matrix.items()}
    elif axis == 0:
        result = defaultdict(int)
        for row in matrix.values():
            for c, val in row.items():
                result[c] += val
        return dict(result)
    else:
        raise ValueError('Axis must be 0 or 1')


def markov_steady_state(
    transition_matrix: SparseMatrix[K, float],
    iterations: int = 100,
    tolerance: float = 1e-6,
) -> SparseVector[K, float]:
    """
    Compute the steady-state distribution of a Markov chain using Power Iteration.
    pi = pi * P

    Args:
        transition_matrix: Row-stochastic matrix (rows sum to 1).
                           P_ij = Prob(i -> j).
        iterations: Maximum number of iterations.
        tolerance: Convergence tolerance.

    Returns:
        The steady-state probability distribution.
    """
    # Initialize uniform distribution
    nodes = set(transition_matrix.keys()) | {k for row in transition_matrix.values() for k in row}
    n = len(nodes)
    if n == 0:
        return {}

    # Initial state vector (row vector)
    state = dict.fromkeys(nodes, 1.0 / n)

    for _ in range(iterations):
        # pi_new = pi_old * P
        new_state = vec_mat(state, transition_matrix)

        # Check convergence (L1 norm of difference)
        diff = sum(abs(new_state.get(k, 0) - state.get(k, 0)) for k in nodes)
        state = new_state

        if diff < tolerance:
            break

    return state


def markov_step(
    state: SparseVector[K, float],
    transition_matrix: SparseMatrix[K, float],
    steps: int = 1,
) -> SparseVector[K, float]:
    """
    Advance a probability distribution by n steps in a Markov chain.
    state_new = state * P^n

    Args:
        state: Initial probability distribution (row vector).
        transition_matrix: Transition matrix P.
        steps: Number of steps to advance.

    Returns:
        The new probability distribution.
    """
    current = state
    for _ in range(steps):
        # Vector-Matrix multiplication: v_new = v * M
        current = vec_mat(current, transition_matrix)

    return current


def mode(distribution: SparseVector[K, float]) -> K:
    """
    Find the mode (key with the highest probability) of a distribution.

    Args:
        distribution: A mapping representing probabilities.

    Returns:
        The key with the maximum value.
    """
    if not distribution:
        raise ValueError('Cannot find mode of empty distribution')
    return max(distribution, key=distribution.get)


def mutual_information(
    joint: SparseMatrix[K, float],
    base: float = 2.0,
) -> float:
    """
    Compute the Mutual Information of a joint probability distribution.
    I(X; Y) = sum(P(x,y) * log(P(x,y) / (P(x)P(y))))
    I(X; Y) = H(X) + H(Y) - H(X, Y)

    Args:
        joint: A matrix representing the joint distribution P(X, Y).
               Rows are X, columns are Y.
        base: Logarithm base (default 2 for bits).

    Returns:
        The mutual information value.
    """
    # Compute marginals
    p_x = marginalize(joint, axis=1)
    p_y = marginalize(joint, axis=0)

    result = 0.0
    for x, row in joint.items():
        for y, p_xy in row.items():
            if p_xy > 0:
                px = p_x.get(x, 0.0)
                py = p_y.get(y, 0.0)
                # px and py must be > 0 if p_xy > 0, so we can skip the check
                result += p_xy * math.log(p_xy / (px * py), base)

    return result


def normalize(mapping: SparseVector[K, N]) -> SparseVector[K, float]:
    """
    Normalize a mapping (probability distribution) so values sum to 1.

    Args:
        mapping: A mapping of keys to numeric values.

    Returns:
        A new dictionary with normalized values.

    Raises:
        ValueError: If the sum of values is zero.
    """
    total = sum(mapping.values())
    if total == 0:
        raise ValueError('Cannot normalize a mapping with zero sum.')
    return {k: v / total for k, v in mapping.items()}


def skewness(distribution: SparseVector[N, float], mu: float | None = None, sigma: float | None = None) -> float:
    """
    Compute the Skewness (3rd standardized moment) of a probability distribution.
    Skew[X] = E[(X - mu)^3] / sigma^3

    Args:
        distribution: A mapping where keys are numeric outcomes and values are probabilities.
        mu: Precomputed mean (optional).
        sigma: Precomputed standard deviation (optional).

    Returns:
        The skewness value.
    """
    if mu is None:
        mu = expected_value(distribution)

    # Calculate 3th central moment
    m3 = sum(((k - mu) ** 3) * v for k, v in distribution.items())

    if sigma is None:
        var = sum(((k - mu) ** 2) * v for k, v in distribution.items())
        sigma = var**0.5

    if sigma == 0:
        return 0.0

    return m3 / (sigma**3)


def variance(distribution: SparseVector[N, float], mu: float | None = None) -> float:
    """
    Compute the Variance (2nd central moment) of a probability distribution.
    Var(X) = E[(X - mu)^2]

    Args:
        distribution: A mapping where keys are numeric outcomes and values are probabilities.
        mu: Precomputed mean (optional).

    Returns:
        The variance value.
    """
    if mu is None:
        mu = expected_value(distribution)

    return sum(((k - mu) ** 2) * v for k, v in distribution.items())
