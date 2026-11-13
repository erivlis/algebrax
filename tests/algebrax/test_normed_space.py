"""
Comprehensive tests for Normed Spaces, Inner Products, RKHS, and Banach Contractions (EP-0205).
"""

import math

import pytest

from algebrax.algebra import InnerProductSpace, NormedSpace
from algebrax.analysis import (
    BanachContractionVerifier,
    EuclideanSpace,
    ReproducingKernelHilbertSpace,
    contractive_fixed_point,
    cosine_kernel,
    cosine_similarity,
    gram_schmidt,
    inner_euclidean,
    linear_kernel,
    norm_frobenius,
    norm_operator_1,
    norm_operator_inf,
    norm_p,
    polynomial_kernel,
    rbf_kernel,
)
from algebrax.verification import (
    verify_cauchy_schwarz,
    verify_contraction_constant,
    verify_inner_product_space_laws,
    verify_normed_space_laws,
    verify_parallelogram_law,
    verify_triangle_inequality,
)

# =============================================================================
# 1. Vector and Matrix p-Norms
# =============================================================================


def test_vector_p_norms():
    """Verify sparse vector L1, L2, L_inf, and Lp norms."""
    vec = {'x': 3.0, 'y': -4.0}

    # Empty vector
    assert norm_p({}) == 0.0
    assert norm_p({}, p=1.0) == 0.0
    assert norm_p({}, p=float('inf')) == 0.0

    # L1: |3| + |-4| = 7
    assert norm_p(vec, p=1.0) == 7.0

    # L2: sqrt(3^2 + (-4)^2) = 5
    assert norm_p(vec, p=2.0) == 5.0

    # L_inf: max(|3|, |-4|) = 4
    assert norm_p(vec, p=float('inf')) == 4.0

    # L3: (3^3 + 4^3)^(1/3) = (27 + 64)^(1/3) = 91^(1/3)
    expected_3 = 91.0 ** (1.0 / 3.0)
    assert math.isclose(norm_p(vec, p=3.0), expected_3, rel_tol=1e-9)

    # Invalid p
    with pytest.raises(ValueError, match=r'Norm order p must be >= 1.0'):
        norm_p(vec, p=0.5)


def test_matrix_norms():
    """Verify matrix Frobenius, operator 1, and operator inf norms."""
    mat = {
        0: {0: 1.0, 1: -2.0},
        1: {0: 3.0, 1: 4.0},
    }

    assert norm_frobenius({}) == 0.0
    assert norm_operator_1({}) == 0.0
    assert norm_operator_inf({}) == 0.0

    # Frobenius: sqrt(1^2 + (-2)^2 + 3^2 + 4^2) = sqrt(1 + 4 + 9 + 16) = sqrt(30)
    assert math.isclose(norm_frobenius(mat), math.sqrt(30.0), rel_tol=1e-9)

    # Operator 1 (max col sum): col 0 = |1| + |3| = 4, col 1 = |-2| + |4| = 6 -> max 6
    assert norm_operator_1(mat) == 6.0

    # Operator inf (max row sum): row 0 = |1| + |-2| = 3, row 1 = |3| + |4| = 7 -> max 7
    assert norm_operator_inf(mat) == 7.0


# =============================================================================
# 2. Inner Products, Angles & Gram-Schmidt
# =============================================================================


def test_inner_product_and_cosine():
    """Verify Euclidean/Hermitian inner products and cosine similarity."""
    u = {'a': 1.0, 'b': 2.0}
    v = {'b': 3.0, 'c': 4.0}

    # Inner product: only overlap at 'b' -> 2.0 * 3.0 = 6.0
    assert inner_euclidean(u, v) == 6.0
    assert inner_euclidean({}, u) == 0.0

    # Orthogonal vectors
    o1 = {'x': 1.0, 'y': 0.0}
    o2 = {'x': 0.0, 'y': 1.0}
    assert inner_euclidean(o1, o2) == 0.0
    assert cosine_similarity(o1, o2) == 0.0

    # Parallel vectors
    p1 = {'x': 2.0, 'y': 4.0}
    p2 = {'x': 1.0, 'y': 2.0}
    assert math.isclose(cosine_similarity(p1, p2), 1.0, rel_tol=1e-9)

    # Opposite vectors
    assert math.isclose(cosine_similarity(p1, {'x': -1.0, 'y': -2.0}), -1.0, rel_tol=1e-9)

    # Zero vector cosine similarity
    assert cosine_similarity({}, p1) == 0.0

    # Complex inner product (Hermitian: u * conj(v))
    cu = {'a': 1.0 + 2.0j}
    cv = {'a': 3.0 + 4.0j}
    # (1 + 2j) * (3 - 4j) = 3 - 4j + 6j - 8j^2 = 11 + 2j
    assert inner_euclidean(cu, cv) == 11.0 + 2.0j


def test_gram_schmidt_orthogonalization():
    """Verify Gram-Schmidt orthogonalization produces an orthonormal basis."""
    v1 = {0: 3.0, 1: 1.0}
    v2 = {0: 2.0, 1: 2.0}

    basis = gram_schmidt([v1, v2], normalize=True)
    assert len(basis) == 2

    # Both must have unit norm
    assert math.isclose(norm_p(basis[0], 2.0), 1.0, rel_tol=1e-9)
    assert math.isclose(norm_p(basis[1], 2.0), 1.0, rel_tol=1e-9)

    # Inner product between basis vectors must be approximately 0
    assert abs(inner_euclidean(basis[0], basis[1])) < 1e-12

    # Linearly dependent vector should be eliminated
    v3 = {0: 6.0, 1: 2.0}  # 2 * v1
    basis_dep = gram_schmidt([v1, v3], normalize=True)
    assert len(basis_dep) == 1


# =============================================================================
# 3. EuclideanSpace Protocol Conformance
# =============================================================================


def test_euclidean_space_protocols():
    """Verify EuclideanSpace satisfies NormedSpace and InnerProductSpace protocols."""
    space = EuclideanSpace()

    assert isinstance(space, NormedSpace)
    assert isinstance(space, InnerProductSpace)

    u = {'x': 1.0, 'y': 2.0}
    v = {'x': 3.0, 'y': -1.0}

    # Addition & Negation
    sum_uv = space.add(u, v)
    assert sum_uv == {'x': 4.0, 'y': 1.0}

    neg_u = space.neg(u)
    assert neg_u == {'x': -1.0, 'y': -2.0}

    diff_uv = space.sub(u, v)
    assert diff_uv == {'x': -2.0, 'y': 3.0}

    # Scaling
    scaled = space.smul(3.0, u)
    assert scaled == {'x': 3.0, 'y': 6.0}
    assert space.smul(0.0, u) == {}

    # Norm & Distance
    assert math.isclose(space.norm(u), math.sqrt(5.0))
    dist = space.distance(u, v)
    assert math.isclose(dist, math.sqrt((-2.0)**2 + 3.0**2))


# =============================================================================
# 4. Reproducing Kernel Hilbert Spaces (RKHS)
# =============================================================================


def test_mercer_kernels():
    """Verify linear, polynomial, RBF, and cosine Mercer kernels."""
    x1 = {'a': 1.0, 'b': 2.0}
    x2 = {'a': 1.0, 'b': 2.0}
    x3 = {'a': -2.0, 'b': 1.0}

    # Linear
    assert linear_kernel(x1, x2) == 5.0
    assert linear_kernel(x1, x3) == 0.0

    # Polynomial: (5 + 1)^2 = 36
    assert polynomial_kernel(x1, x2, degree=2.0, c=1.0) == 36.0

    # RBF: dist(x1, x2) = 0 -> exp(0) = 1.0
    assert rbf_kernel(x1, x2, gamma=1.0) == 1.0
    assert rbf_kernel(x1, x3, gamma=1.0) < 1.0

    # Cosine
    assert math.isclose(cosine_kernel(x1, x2), 1.0)
    assert cosine_kernel(x1, x3) == 0.0


def test_rkhs_gram_matrix_and_regression():
    """Verify RKHS Gram matrix assembly and kernel ridge regression."""
    rkhs = ReproducingKernelHilbertSpace(rbf_kernel)

    samples = [
        {'x': 0.0},
        {'x': 1.0},
        {'x': 2.0},
    ]

    # Gram matrix
    gram = rkhs.build_gram_matrix(samples)
    assert len(gram) == 3

    # Diagonal entries are k(x_i, x_i) = 1.0 for RBF
    for i in range(3):
        assert math.isclose(gram[i][i], 1.0)

    # Symmetry K_ij == K_ji
    for i in range(3):
        for j in range(3):
            assert math.isclose(gram[i][j], gram[j][i])

    # Feature distance: d(x1, x1) = 0
    assert rkhs.distance(samples[0], samples[0]) == 0.0
    assert rkhs.distance(samples[0], samples[1]) > 0.0

    # Kernel Ridge Regression
    targets = [0.0, 1.0, 4.0]  # approximate y = x^2
    predictor = rkhs.kernel_ridge_regression(samples, targets, alpha=1e-3)

    # Predict at training points should be close to targets
    for sample, target in zip(samples, targets):
        assert math.isclose(predictor(sample), target, abs_tol=0.1)


# =============================================================================
# 5. Certified Banach Contractions
# =============================================================================


def test_banach_contraction_solver():
    """Verify Banach contraction verification and geometric fixed-point convergence."""
    space = EuclideanSpace()

    # Contraction operator: T(x) = 0.5 * x + 1.0 (fixed point is x* = 2.0)
    def contractive_op(vec: dict[str, float]) -> dict[str, float]:
        val = vec.get('val', 0.0)
        return {'val': 0.5 * val + 1.0}

    verifier = BanachContractionVerifier(space, gamma=0.6)

    u = {'val': 0.0}
    v = {'val': 10.0}

    # Step verification: |T(0) - T(10)| = |1 - 6| = 5 <= 0.6 * 10 = 6
    assert verifier.verify_step(contractive_op, u, v)

    # Estimate contraction factor
    samples = [{'val': float(k)} for k in range(-5, 6)]
    est_gamma = verifier.estimate_contraction_factor(contractive_op, samples)
    assert math.isclose(est_gamma, 0.5, rel_tol=1e-9)

    # Solve for fixed point
    fixed_point, _iters, converged = contractive_fixed_point(
        space, contractive_op, initial={'val': 100.0}, tol=1e-9
    )
    assert converged
    assert math.isclose(fixed_point['val'], 2.0, abs_tol=1e-7)

    # Invalid gamma
    with pytest.raises(ValueError, match=r'Contraction constant must satisfy'):
        BanachContractionVerifier(space, gamma=1.0)


# =============================================================================
# 6. Axiomatic Verifications (EP-0205)
# =============================================================================


def test_axiomatic_properties():
    """Verify Cauchy-Schwarz, Triangle inequality, Parallelogram law, and space laws."""
    space = EuclideanSpace()

    u = {'a': 1.0, 'b': 2.0, 'c': -1.0}
    v = {'a': 2.0, 'b': -1.0, 'c': 3.0}

    # Cauchy-Schwarz
    assert verify_cauchy_schwarz(space, u, v)

    # Triangle inequality
    assert verify_triangle_inequality(space, u, v)

    # Parallelogram law
    assert verify_parallelogram_law(space, u, v)

    # Contraction verification
    def op(x: dict[str, float]) -> dict[str, float]:
        return {k: 0.3 * val for k, val in x.items()}

    samples = [u, v, space.zero]
    assert verify_contraction_constant(space, op, samples, gamma=0.5)

    # Batch verification of all NormedSpace laws
    r_samples = [0.0, 1.0, -2.5, 3.0]
    v_samples = [
        {'a': 1.0},
        {'b': 2.0},
        {'a': -1.0, 'b': 3.0},
        space.zero,
    ]
    norm_results = verify_normed_space_laws(space, r_samples, v_samples)
    assert all(norm_results.values()), f'NormedSpace laws failed: {norm_results}'

    # Batch verification of all InnerProductSpace laws
    inner_results = verify_inner_product_space_laws(space, r_samples, v_samples)
    assert all(inner_results.values()), f'InnerProductSpace laws failed: {inner_results}'
