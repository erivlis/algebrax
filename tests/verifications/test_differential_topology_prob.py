r"""Comparative verification of Topology, Probability, Automata & Metrics vs SciPy.stats & Reference TDA Oracles.

Implements EP-0184:
- Simplicial homology (`SimplicialComplex.betti_numbers`, `cohomology_rank`) vs exact `np.linalg.matrix_rank`
  on dense boundary matrices and canonical manifolds ($S^1, S^2, T^2, \mathbb{R}P^2$, disconnected clusters).
- Euler-Poincare Characteristic Theorem: $\chi(K) = \sum (-1)^k |K_k| = \sum (-1)^k \beta_k$.
- Discrete Stokes' Theorem: $\langle d_k \omega, c_{k+1} \rangle = \langle \omega, \partial_{k+1} c_{k+1} \rangle$
  and Weighted Adjointness $\langle d_{k-1} \alpha, \beta \rangle_{\star_k} =
  \langle \alpha, \delta_k \beta \rangle_{\star_{k-1}}$.
- Discrete Hodge Theorem (`hodge_laplacian`) vs `scipy.linalg.eigvalsh`: $\dim \ker \Delta_k = \beta_k$.
- Helmholtz-Hodge Decomposition (`helmholtz_hodge_decomposition`): $L^2$ orthogonality, zero curl of exact,
  zero divergence of coexact, and harmonic kernel $\Delta_1 \gamma = 0$.
- Information Theory (`entropy`, `cross_entropy`, `kl_divergence`, `mutual_information`) vs `scipy.stats.entropy`
  and `scipy.special.rel_entr`.
- Statistical Moments (`expected_value`, `variance`, `skewness`, `kurtosis`) vs `scipy.stats.rv_discrete`
  and `scipy.stats.skew` / `scipy.stats.kurtosis`.
- Bayesian Conditioning (`bayes_update`) and Markov Chains (`markov_step`, `markov_steady_state`) vs
  analytical Bayes' rule, sequential update commutativity, and `scipy.linalg.eig` left Perron-Frobenius eigenvector.
- Formal Languages (`dfa_step`, `nfa_step`, `simulate_dfa`, `simulate_nfa`) vs Rabin-Scott powerset construction,
  probabilistic matrix powers $p_0 P^w$, and Python's `re` regular expression oracle.
- Structural & Fractal Metrics (`density`, `sparsity`, `box_counting_dimension`, `count_elements`, `deepness`,
  `wideness`, `uniformness`) vs NumPy dense nonzeros and analytical Hausdorff dimensions ($\ln 3 / \ln 2$ Sierpinski).
"""

from __future__ import annotations

import math
import re

import numpy as np
import pytest
import scipy.linalg as sla
import scipy.special as sps
import scipy.stats as stats
from hypothesis import given, settings
from hypothesis import strategies as st

from algebrax.automata import dfa_step, nfa_step, simulate_dfa, simulate_nfa
from algebrax.homology import (
    Cochain,
    FilteredSimplicialComplex,
    PersistenceInterval,
    SimplicialComplex,
    betti_curve,
    bottleneck_distance,
    coboundary,
    cochain_to_flow,
    codifferential,
    cohomology_rank,
    exterior_derivative,
    flow_to_cochain,
    helmholtz_hodge_decomposition,
    hodge_laplacian,
    hodge_star,
    persistence_entropy,
    persistent_homology,
)
from algebrax.matrix.core import mat_vec
from algebrax.metrics import (
    box_counting_dimension,
    count_elements,
    deepness,
    density,
    is_sparse,
    sparsity,
    uniformness,
    wideness,
)
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

# ---------------------------------------------------------------------------
# Helpers for Dense Boundary / Operator Conversion
# ---------------------------------------------------------------------------


def _sparse_boundary_to_dense(
    sc: SimplicialComplex,
    k: int,
) -> np.ndarray:
    """Convert the k-th boundary matrix D_k : C_k -> C_{k-1} of a SimplicialComplex to a dense NumPy array."""
    rows = sorted(sc._simplices.get(k - 1, set()))
    cols = sorted(sc._simplices.get(k, set()))
    if not rows or not cols:
        return np.zeros((len(rows), len(cols)), dtype=np.float64)

    row_idx = {r: i for i, r in enumerate(rows)}
    col_idx = {c: j for j, c in enumerate(cols)}
    d_k = sc.boundary_matrices.get(k, {})

    dense = np.zeros((len(rows), len(cols)), dtype=np.float64)
    for r_simp, row_map in d_k.items():
        if r_simp in row_idx:
            i = row_idx[r_simp]
            for c_simp, val in row_map.items():
                if c_simp in col_idx:
                    dense[i, col_idx[c_simp]] = float(val)
    return dense


def _sparse_square_to_dense(
    mat: dict,
    basis: list,
) -> np.ndarray:
    """Convert a square sparse operator over `basis` to a dense NumPy matrix."""
    n = len(basis)
    idx = {b: i for i, b in enumerate(basis)}
    dense = np.zeros((n, n), dtype=np.float64)
    for r, row in mat.items():
        if r in idx:
            i = idx[r]
            for c, val in row.items():
                if c in idx:
                    dense[i, idx[c]] = float(val)
    return dense


# ---------------------------------------------------------------------------
# 1. Simplicial Homology, Canonical Manifolds & Euler-Poincare Characteristic
# ---------------------------------------------------------------------------


def test_simplicial_homology_canonical_manifolds_and_euler_poincare() -> None:
    """Verify Betti numbers, nilpotency, and Euler-Poincare characteristic on canonical manifolds vs NumPy rank."""
    # 1. Circle S^1 (hollow triangle): beta = (1, 1, 0), chi = 3 - 3 = 0
    s1 = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
    assert s1.betti_numbers(max_k=2) == {0: 1, 1: 1, 2: 0}

    # 2. Filled Disk D^2 (2-simplex): beta = (1, 0, 0), chi = 3 - 3 + 1 = 1
    d2 = SimplicialComplex([(0, 1, 2)])
    assert d2.betti_numbers(max_k=2) == {0: 1, 1: 0, 2: 0}

    # 3. Hollow Tetrahedron S^2 (boundary of 3-simplex): beta = (1, 0, 1), chi = 4 - 6 + 4 = 2
    s2 = SimplicialComplex([(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
    assert s2.betti_numbers(max_k=2) == {0: 1, 1: 0, 2: 1}

    # 4. Solid Tetrahedron D^3 (3-simplex): beta = (1, 0, 0, 0), chi = 4 - 6 + 4 - 1 = 1
    d3 = SimplicialComplex([(0, 1, 2, 3)])
    assert d3.betti_numbers(max_k=3) == {0: 1, 1: 0, 2: 0, 3: 0}

    # 5. Minimal 7-vertex Császár / Möbius-Kantor Triangulation of the 2-Torus T^2:
    # 7 vertices, 21 edges, 14 triangles -> chi = 7 - 21 + 14 = 0, beta = (1, 2, 1)
    torus_triangles = [
        (0, 1, 3),
        (1, 2, 4),
        (2, 3, 5),
        (3, 4, 6),
        (0, 4, 5),
        (1, 5, 6),
        (0, 2, 6),
        (0, 2, 3),
        (1, 3, 4),
        (2, 4, 5),
        (3, 5, 6),
        (0, 4, 6),
        (0, 1, 5),
        (1, 2, 6),
    ]
    t2 = SimplicialComplex(torus_triangles)
    assert len(t2._simplices[0]) == 7
    assert len(t2._simplices[1]) == 21
    assert len(t2._simplices[2]) == 14
    assert t2.betti_numbers(max_k=2) == {0: 1, 1: 2, 2: 1}

    # 6. Disconnected Cluster: two disjoint hollow triangles + one isolated edge: beta = (3, 2, 0)
    cluster = SimplicialComplex([(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (6, 7)])
    assert cluster.betti_numbers(max_k=2) == {0: 3, 1: 2, 2: 0}

    # Verify against dense `np.linalg.matrix_rank` and Euler-Poincare theorem across all complexes
    for sc in (s1, d2, s2, d3, t2, cluster):
        max_dim = max(sc._simplices.keys())
        betti = sc.betti_numbers(max_k=max_dim)
        for k in range(max_dim + 1):
            assert sc.verify_nilpotency(k)
            assert cohomology_rank(sc, k) == betti[k]

            num_k = len(sc._simplices.get(k, set()))
            d_k_dense = _sparse_boundary_to_dense(sc, k) if k >= 1 else np.zeros((0, num_k))
            d_k1_dense = _sparse_boundary_to_dense(sc, k + 1) if (k + 1) <= max_dim else np.zeros((num_k, 0))

            rank_dk = int(np.linalg.matrix_rank(d_k_dense)) if d_k_dense.size > 0 else 0
            rank_dk1 = int(np.linalg.matrix_rank(d_k1_dense)) if d_k1_dense.size > 0 else 0
            expected_beta_k = num_k - rank_dk - rank_dk1
            assert betti[k] == expected_beta_k

        # Euler-Poincare Characteristic: sum_{k} (-1)^k |K_k| == sum_{k} (-1)^k beta_k
        chi_simplices = sum(((-1) ** k) * len(sc._simplices.get(k, set())) for k in range(max_dim + 1))
        chi_betti = sum(((-1) ** k) * betti[k] for k in range(max_dim + 1))
        assert chi_simplices == chi_betti


# ---------------------------------------------------------------------------
# 2. Discrete Hodge Theorem: dim(ker Delta_k) == beta_k vs SciPy eigvalsh
# ---------------------------------------------------------------------------


def test_discrete_hodge_theorem_vs_scipy_eigvalsh() -> None:
    """Verify Discrete Hodge Theorem (nullity of Delta_k equals beta_k) and PSD spectrum vs scipy.linalg.eigvalsh."""
    torus_triangles = [
        (0, 1, 3),
        (1, 2, 4),
        (2, 3, 5),
        (3, 4, 6),
        (0, 4, 5),
        (1, 5, 6),
        (0, 2, 6),
        (0, 2, 3),
        (1, 3, 4),
        (2, 4, 5),
        (3, 5, 6),
        (0, 4, 6),
        (0, 1, 5),
        (1, 2, 6),
    ]
    complexes = [
        SimplicialComplex([(0, 1), (1, 2), (0, 2)]),  # S^1
        SimplicialComplex([(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]),  # S^2
        SimplicialComplex(torus_triangles),  # T^2
    ]

    for sc in complexes:
        betti = sc.betti_numbers(max_k=2)
        for k in range(3):
            simplices_k = sorted(sc._simplices.get(k, set()))
            if not simplices_k:
                continue

            delta_k_sparse = hodge_laplacian(sc, k)
            delta_k_dense = _sparse_square_to_dense(delta_k_sparse, simplices_k)

            # Compare against dense D_k^T D_k + D_{k+1} D_{k+1}^T
            d_k = _sparse_boundary_to_dense(sc, k) if k >= 1 else np.zeros((0, len(simplices_k)))
            d_k1 = _sparse_boundary_to_dense(sc, k + 1) if (k + 1) in sc._simplices else np.zeros((len(simplices_k), 0))
            expected_delta = (d_k.T @ d_k if d_k.size else 0.0) + (d_k1 @ d_k1.T if d_k1.size else 0.0)
            np.testing.assert_allclose(delta_k_dense, expected_delta, atol=1e-12)

            # Symmetric Positive Semi-Definite & Nullity == beta_k
            eigvals = sla.eigvalsh(delta_k_dense)
            assert np.all(eigvals >= -1e-12)
            nullity = int(np.sum(np.abs(eigvals) < 1e-9))
            assert nullity == betti[k]


# ---------------------------------------------------------------------------
# 3. Discrete Stokes' Theorem & Hodge Star Adjointness
# ---------------------------------------------------------------------------


def test_discrete_stokes_theorem_and_hodge_star_adjointness() -> None:
    """Verify <d_k omega, c_{k+1}> == <omega, partial_{k+1} c_{k+1}> and weighted codifferential adjointness."""
    sc = SimplicialComplex([(0, 1, 2), (1, 2, 3), (0, 2, 3), (0, 1, 3)])

    # 1. Degree k=0 -> k+1=1: <d_0 f, c_1> == <f, partial_1 c_1>
    f0 = Cochain({(0,): 2.5, (1,): -1.2, (2,): 0.8, (3,): 3.1}, degree=0)
    c1 = {(0, 1): 1.5, (1, 2): -2.0, (0, 2): 0.5, (2, 3): 4.0, (0, 3): -1.0}

    d0 = exterior_derivative(sc, 0)
    b1 = sc.boundary_matrices[1]
    d0_f = Cochain(mat_vec(d0, f0), degree=1)
    partial1_c1 = mat_vec(b1, c1)

    lhs_01 = d0_f.eval(c1)
    rhs_01 = f0.eval(partial1_c1)
    assert math.isclose(lhs_01, rhs_01, rel_tol=1e-12, abs_tol=1e-12)

    # 2. Degree k=1 -> k+1=2: <d_1 omega, c_2> == <omega, partial_2 c_2>
    omega1 = Cochain(
        {(0, 1): 0.7, (1, 2): -1.3, (0, 2): 2.1, (1, 3): 0.4, (2, 3): -0.9, (0, 3): 1.8},
        degree=1,
    )
    c2 = {(0, 1, 2): 2.0, (1, 2, 3): -1.5, (0, 2, 3): 0.8, (0, 1, 3): -0.5}

    d1 = exterior_derivative(sc, 1)
    b2 = sc.boundary_matrices[2]
    d1_omega = Cochain(mat_vec(d1, omega1), degree=2)
    partial2_c2 = mat_vec(b2, c2)

    lhs_12 = d1_omega.eval(c2)
    rhs_12 = omega1.eval(partial2_c2)
    assert math.isclose(lhs_12, rhs_12, rel_tol=1e-12, abs_tol=1e-12)

    # 3. Cochain alternating parity & flow bridge roundtrip
    assert math.isclose(omega1[(1, 0)], -omega1[(0, 1)], rel_tol=1e-12)
    assert omega1.get((1, 1), 0.0) == 0.0
    flow_mat = cochain_to_flow(omega1, skew_symmetric=True)
    omega1_roundtrip = flow_to_cochain(flow_mat)
    assert omega1_roundtrip == omega1

    # 4. Weighted Hodge star & codifferential formal adjointness:
    # <d_0 alpha, star_1 beta> == <alpha, star_0(delta_1 beta)>
    w0 = {(0,): 1.2, (1,): 2.5, (2,): 0.8, (3,): 1.7}
    w1 = {(0, 1): 0.9, (0, 2): 1.4, (0, 3): 2.1, (1, 2): 1.1, (1, 3): 0.6, (2, 3): 1.8}
    delta1_weighted = codifferential(sc, 1, dual_weights_k=w1, dual_weights_km1=w0)

    star1_omega1 = hodge_star(omega1, w1)
    delta1_omega1 = Cochain(mat_vec(delta1_weighted, omega1), degree=0)
    star0_delta1 = hodge_star(delta1_omega1, w0)

    adj_lhs = d0_f.eval(star1_omega1)
    adj_rhs = f0.eval(star0_delta1)
    assert math.isclose(adj_lhs, adj_rhs, rel_tol=1e-12, abs_tol=1e-12)

    # Inverse Hodge star roundtrip
    assert hodge_star(star1_omega1, w1, inverse=True) == omega1


# ---------------------------------------------------------------------------
# 4. Helmholtz-Hodge Decomposition Orthogonality & Harmonic Extraction
# ---------------------------------------------------------------------------


def test_helmholtz_hodge_decomposition_orthogonality_and_invariants() -> None:
    """Verify Helmholtz-Hodge decomposition omega = exact + coexact + harmonic on a complex with a hole & triangle."""
    # Simplicial complex with a filled triangle (0, 1, 2) and an unfilled 4-cycle (1, 2, 3, 4) -> beta_1 = 1
    sc = SimplicialComplex([(0, 1, 2), (1, 3), (3, 4), (2, 4)])
    assert sc.betti_numbers(max_k=2) == {0: 1, 1: 1, 2: 0}

    flow = Cochain(
        {
            (0, 1): 3.0,
            (1, 2): 2.5,
            (0, 2): -1.5,
            (1, 3): 4.0,
            (3, 4): 4.0,
            (2, 4): -4.0,
        },
        degree=1,
    )
    decomp = helmholtz_hodge_decomposition(sc, flow, tol=1e-11, max_iter=2000)

    # 1. Exact reconstruction: exact + coexact + harmonic == flow
    reconstructed = decomp.exact + decomp.coexact + decomp.harmonic
    for edge in sc._simplices[1]:
        assert math.isclose(reconstructed.get(edge, 0.0), flow.get(edge, 0.0), abs_tol=1e-7)

    # 2. Mutual L2 orthogonality: <exact, coexact> == <exact, harmonic> == <coexact, harmonic> == 0
    assert abs(decomp.exact.eval(decomp.coexact)) < 1e-7
    assert abs(decomp.exact.eval(decomp.harmonic)) < 1e-7
    assert abs(decomp.coexact.eval(decomp.harmonic)) < 1e-7

    # 3. Differential invariants:
    # - Exact component is curl-free: d_1(exact) == 0
    d1 = coboundary(sc, 1)
    curl_exact = mat_vec(d1, decomp.exact)
    assert all(abs(v) < 1e-7 for v in curl_exact.values())

    # - Coexact component is divergence-free: partial_1(coexact) == 0
    b1 = sc.boundary_matrices[1]
    div_coexact = mat_vec(b1, decomp.coexact)
    assert all(abs(v) < 1e-7 for v in div_coexact.values())

    # - Harmonic component lies in ker(Delta_1): Delta_1(harmonic) == 0
    delta1 = hodge_laplacian(sc, 1)
    lap_harmonic = mat_vec(delta1, decomp.harmonic)
    assert all(abs(v) < 1e-7 for v in lap_harmonic.values())


# ---------------------------------------------------------------------------
# 5. Information Theory vs SciPy.stats & SciPy.special
# ---------------------------------------------------------------------------


@settings(max_examples=40, deadline=None)
@given(
    raw_p=st.lists(
        st.floats(min_value=1e-4, max_value=10.0, allow_nan=False, allow_infinity=False), min_size=2, max_size=12
    ),
    raw_q=st.lists(
        st.floats(min_value=1e-4, max_value=10.0, allow_nan=False, allow_infinity=False), min_size=2, max_size=12
    ),
)
def test_information_theory_vs_scipy_stats(raw_p: list[float], raw_q: list[float]) -> None:
    """Verify entropy, cross_entropy, and kl_divergence against scipy.stats.entropy and scipy.special.rel_entr."""
    n = min(len(raw_p), len(raw_q))
    p_dict = normalize({i: raw_p[i] for i in range(n)})
    q_dict = normalize({i: raw_q[i] for i in range(n)})

    p_arr = np.array([p_dict[i] for i in range(n)], dtype=np.float64)
    q_arr = np.array([q_dict[i] for i in range(n)], dtype=np.float64)

    # 1. Shannon Entropy (base 2 and base e)
    h_p_bits = entropy(p_dict, base=2.0)
    h_p_nats = entropy(p_dict, base=math.e)
    assert math.isclose(h_p_bits, float(stats.entropy(p_arr, base=2.0)), rel_tol=1e-11, abs_tol=1e-11)
    assert math.isclose(h_p_nats, float(stats.entropy(p_arr)), rel_tol=1e-11, abs_tol=1e-11)
    assert 0.0 <= h_p_bits <= math.log2(n) + 1e-12

    # 2. Kullback-Leibler Divergence vs scipy.stats.entropy(P, Q) and scipy.special.rel_entr
    kl_bits = kl_divergence(p_dict, q_dict, base=2.0)
    kl_nats = kl_divergence(p_dict, q_dict, base=math.e)
    assert math.isclose(kl_bits, float(stats.entropy(p_arr, q_arr, base=2.0)), rel_tol=1e-11, abs_tol=1e-11)
    assert math.isclose(kl_nats, float(np.sum(sps.rel_entr(p_arr, q_arr))), rel_tol=1e-11, abs_tol=1e-11)
    # Gibbs' inequality: D_KL(P || Q) >= 0 and D_KL(P || P) == 0
    assert kl_bits >= -1e-12
    assert abs(kl_divergence(p_dict, p_dict, base=2.0)) < 1e-12

    # 3. Cross-Entropy identity: H(P, Q) == H(P) + D_KL(P || Q)
    ce_bits = cross_entropy(p_dict, q_dict, base=2.0)
    assert math.isclose(ce_bits, h_p_bits + kl_bits, rel_tol=1e-11, abs_tol=1e-11)


def test_mutual_information_and_marginals_vs_scipy() -> None:
    """Verify mutual_information and marginalize against scipy.stats.entropy on joint distributions."""
    raw_joint = {
        0: {0: 0.25, 1: 0.05, 2: 0.10},
        1: {0: 0.05, 1: 0.30, 2: 0.05},
        2: {0: 0.02, 1: 0.03, 2: 0.15},
    }
    p_x = marginalize(raw_joint, axis=1)
    p_y = marginalize(raw_joint, axis=0)

    dense_joint = np.array([[raw_joint[i][j] for j in range(3)] for i in range(3)], dtype=np.float64)
    np.testing.assert_allclose([p_x[i] for i in range(3)], dense_joint.sum(axis=1), atol=1e-12)
    np.testing.assert_allclose([p_y[j] for j in range(3)], dense_joint.sum(axis=0), atol=1e-12)

    # Mutual Information: I(X; Y) = H(X) + H(Y) - H(X, Y) = D_KL(P(X,Y) || P(X)P(Y))
    mi_bits = mutual_information(raw_joint, base=2.0)
    h_x = float(stats.entropy(dense_joint.sum(axis=1), base=2.0))
    h_y = float(stats.entropy(dense_joint.sum(axis=0), base=2.0))
    h_xy = float(stats.entropy(dense_joint.ravel(), base=2.0))
    assert math.isclose(mi_bits, h_x + h_y - h_xy, rel_tol=1e-11, abs_tol=1e-11)
    assert mi_bits >= 0.0


# ---------------------------------------------------------------------------
# 6. Statistical Moments vs SciPy.stats.rv_discrete
# ---------------------------------------------------------------------------


def test_statistical_moments_vs_scipy_rv_discrete() -> None:
    """Verify expected_value, variance, skewness, kurtosis, and mode against scipy.stats.rv_discrete."""
    dist = {-2: 0.10, 0: 0.25, 1: 0.35, 3: 0.20, 7: 0.10}
    xk = np.array(sorted(dist.keys()), dtype=np.float64)
    pk = np.array([dist[k] for k in sorted(dist.keys())], dtype=np.float64)

    rv = stats.rv_discrete(name='custom', values=(xk, pk))
    mean_sp, var_sp, skew_sp, kurt_excess_sp = rv.stats(moments='mvsk')

    mu_ax = expected_value(dist)
    var_ax = variance(dist)
    skew_ax = skewness(dist)
    kurt_ax = kurtosis(dist)  # Pearson kurtosis (non-Fisher, where normal = 3.0)

    assert math.isclose(mu_ax, float(mean_sp), rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(var_ax, float(var_sp), rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(skew_ax, float(skew_sp), rel_tol=1e-11, abs_tol=1e-11)
    # SciPy rv.stats returns Fisher excess kurtosis (Pearson - 3)
    assert math.isclose(kurt_ax, float(kurt_excess_sp) + 3.0, rel_tol=1e-11, abs_tol=1e-11)
    assert mode(dist) == 1


# ---------------------------------------------------------------------------
# 7. Bayesian Conditioning & Markov Chains vs Analytical & SciPy Eigenvectors
# ---------------------------------------------------------------------------


def test_bayes_update_commutativity_and_markov_steady_state() -> None:
    """Verify sequential Bayes updates commute and markov_steady_state matches left Perron-Frobenius eigenvector."""
    prior = {'H0': 0.5, 'H1': 0.3, 'H2': 0.2}
    likelihood_e1 = {'H0': 0.8, 'H1': 0.4, 'H2': 0.1}
    likelihood_e2 = {'H0': 0.2, 'H1': 0.7, 'H2': 0.9}

    # Sequential Bayesian update order invariance: B(B(P, E1), E2) == B(B(P, E2), E1)
    post_12 = bayes_update(bayes_update(prior, likelihood_e1), likelihood_e2)
    post_21 = bayes_update(bayes_update(prior, likelihood_e2), likelihood_e1)
    joint_likelihood = {k: likelihood_e1[k] * likelihood_e2[k] for k in prior}
    post_joint = bayes_update(prior, joint_likelihood)

    for h in prior:
        assert math.isclose(post_12[h], post_21[h], rel_tol=1e-12, abs_tol=1e-12)
        assert math.isclose(post_12[h], post_joint[h], rel_tol=1e-12, abs_tol=1e-12)

    # Markov chain transition steps and steady state vs NumPy matrix power and SciPy eigenvector
    trans = {
        0: {0: 0.7, 1: 0.2, 2: 0.1},
        1: {0: 0.1, 1: 0.6, 2: 0.3},
        2: {0: 0.2, 1: 0.3, 2: 0.5},
    }
    p_mat = np.array([[trans[i][j] for j in range(3)] for i in range(3)], dtype=np.float64)
    init_state = {0: 0.6, 1: 0.3, 2: 0.1}
    init_vec = np.array([0.6, 0.3, 0.1], dtype=np.float64)

    # 5-step advancement: state_5 == init_vec @ P^5
    state_5 = markov_step(init_state, trans, steps=5)
    expected_5 = init_vec @ np.linalg.matrix_power(p_mat, 5)
    np.testing.assert_allclose([state_5[i] for i in range(3)], expected_5, atol=1e-12)

    # Steady state pi = pi P
    steady = markov_steady_state(trans, iterations=500, tolerance=1e-12)
    eigvals, left_eigvecs = sla.eig(p_mat, left=True, right=False)
    idx_unit = int(np.argmin(np.abs(eigvals - 1.0)))
    pi_scipy = np.real(left_eigvecs[:, idx_unit])
    pi_scipy = pi_scipy / np.sum(pi_scipy)

    np.testing.assert_allclose([steady[i] for i in range(3)], pi_scipy, atol=1e-10)


# ---------------------------------------------------------------------------
# 8. Formal Languages: DFA / NFA vs Rabin-Scott Powerset & Python Regex Oracle
# ---------------------------------------------------------------------------


def test_automata_dfa_nfa_vs_rabin_scott_and_regex_oracle() -> None:
    """Verify simulate_dfa and simulate_nfa against Rabin-Scott powerset construction and Python's re engine."""
    # Regular language over {'a', 'b'}: strings ending with 'ab' (regex r'^[ab]*ab$')
    # NFA: q0 --a,b--> q0, q0 --a--> q1, q1 --b--> q2 (accepting: q2)
    nfa_transitions = {
        'q0': {'a': {'q0': 1.0, 'q1': 1.0}, 'b': {'q0': 1.0}},
        'q1': {'b': {'q2': 1.0}},
        'q2': {},
    }
    # Equivalent determinized DFA via Rabin-Scott subset construction:
    # S0 = {q0}, S1 = {q0, q1}, S2 = {q0, q2} (accepting: S2)
    dfa_transitions = {
        'S0': {'a': 'S1', 'b': 'S0'},
        'S1': {'a': 'S1', 'b': 'S2'},
        'S2': {'a': 'S1', 'b': 'S0'},
    }
    regex = re.compile(r'^[ab]*ab$')

    test_words = ['', 'a', 'b', 'ab', 'aba', 'abb', 'aab', 'bab', 'abab', 'bbaab', 'ababa', 'bbbab']
    for word in test_words:
        symbols = list(word)
        dfa_final = simulate_dfa('S0', symbols, dfa_transitions)
        nfa_final = simulate_nfa({'q0': 1.0}, symbols, nfa_transitions)

        dfa_accepts = dfa_final == 'S2'
        nfa_accepts = nfa_final.get('q2', 0.0) > 0.0
        regex_accepts = bool(regex.match(word))

        assert dfa_accepts == regex_accepts
        assert nfa_accepts == regex_accepts

        # Verify sparse time-indexed dict input equivalence
        sparse_seq = dict(enumerate(symbols))
        assert simulate_dfa('S0', sparse_seq, dfa_transitions) == dfa_final
        assert simulate_nfa({'q0': 1.0}, sparse_seq, nfa_transitions) == nfa_final

    # Verify single steps and probabilistic automaton transition matrix equivalence
    assert dfa_step('S0', 'a', dfa_transitions) == 'S1'
    assert dfa_step('S0', 'c', dfa_transitions) is None
    assert nfa_step({'q0': 1.0}, 'a', nfa_transitions) == {'q0': 1.0, 'q1': 1.0}

    prob_transitions = {
        0: {'x': {0: 0.6, 1: 0.4}, 'y': {0: 0.2, 1: 0.8}},
        1: {'x': {0: 0.3, 1: 0.7}, 'y': {0: 0.9, 1: 0.1}},
    }
    tx = np.array([[0.6, 0.4], [0.3, 0.7]], dtype=np.float64)
    ty = np.array([[0.2, 0.8], [0.9, 0.1]], dtype=np.float64)
    p0 = {0: 0.5, 1: 0.5}
    p_final = simulate_nfa(p0, ['x', 'y', 'x'], prob_transitions)
    expected_p = np.array([0.5, 0.5]) @ tx @ ty @ tx
    np.testing.assert_allclose([p_final[0], p_final[1]], expected_p, atol=1e-12)


# ---------------------------------------------------------------------------
# 9. Structural & Fractal Dimension Metrics vs Analytical Hausdorff Oracles
# ---------------------------------------------------------------------------


def test_metrics_density_sparsity_and_fractal_box_counting() -> None:
    """Verify density, sparsity, structural metrics, and box_counting_dimension on self-similar fractals."""
    # 1. Sparse matrix density + sparsity conservation against NumPy count_nonzero
    sparse_mat = {
        0: {0: 1.0, 3: 2.0},
        1: {1: -1.0},
        2: {0: 4.0, 2: 5.0, 3: 6.0},
    }
    dense_mat = np.zeros((4, 4), dtype=np.float64)
    for r, row in sparse_mat.items():
        for c, val in row.items():
            dense_mat[r, c] = val

    cap = dense_mat.size
    dens_ax = density(sparse_mat, capacity=cap)
    spar_ax = sparsity(sparse_mat, capacity=cap)
    expected_dens = float(np.count_nonzero(dense_mat)) / cap

    assert math.isclose(dens_ax, expected_dens, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(dens_ax + spar_ax, 1.0, rel_tol=1e-12, abs_tol=1e-12)
    assert is_sparse(sparse_mat, capacity=cap, threshold=0.5) is True
    assert count_elements(sparse_mat) == 6
    assert deepness(sparse_mat) == 2
    assert wideness(sparse_mat) == 3
    assert math.isclose(uniformness(sparse_mat), 1.0, rel_tol=1e-12)

    # 2. Sierpinski Gasket (Pascal's triangle mod 2 on 2^k x 2^k grid):
    # Analytical Hausdorff / box-counting dimension D = ln(3) / ln(2) ~= 1.5849625
    # With coordinates (x, y) in [0, 63]^2 where (x & y) == 0, every power-of-2 box size s = 2^m
    # divides the 64x64 grid into exact self-similar blocks with N(s) = 3^(6 - m).
    sierpinski_points = {(x, y): 1 for x in range(64) for y in range(64) if (x & y) == 0}
    dim_sierpinski = box_counting_dimension(sierpinski_points, min_box_size=1, max_box_size=32)
    expected_sierpinski = math.log(3.0) / math.log(2.0)
    assert math.isclose(dim_sierpinski, expected_sierpinski, rel_tol=1e-12, abs_tol=1e-12)

    # 3. 1D Line Segment of length 64: D = 1.0
    line_points = {(x, 0): 1 for x in range(64)}
    dim_line = box_counting_dimension(line_points, min_box_size=1, max_box_size=32)
    assert math.isclose(dim_line, 1.0, rel_tol=1e-12, abs_tol=1e-12)

    # 4. 2D Solid Square of size 64 x 64: D = 2.0
    square_points = {(x, y): 1 for x in range(64) for y in range(64)}
    dim_square = box_counting_dimension(square_points, min_box_size=1, max_box_size=32)
    assert math.isclose(dim_square, 2.0, rel_tol=1e-12, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# 10. Persistent Homology, Vietoris-Rips Filtrations & Bottleneck Stability (EP-0162)
# ---------------------------------------------------------------------------


def _gf2_rank_numpy(mat: np.ndarray) -> int:
    """Reference dense F_2 Gaussian elimination rank oracle using NumPy XOR row reduction."""
    if mat.size == 0:
        return 0
    a = (np.abs(np.rint(mat)).astype(np.int64) % 2).copy()
    m, n = a.shape
    rank = 0
    for col in range(n):
        pivot_rows = np.nonzero(a[rank:, col])[0]
        if pivot_rows.size == 0:
            continue
        piv = rank + int(pivot_rows[0])
        if piv != rank:
            a[[rank, piv]] = a[[piv, rank]]
        below = np.nonzero(a[rank + 1 :, col])[0] + (rank + 1)
        if below.size > 0:
            a[below] ^= a[rank]
        rank += 1
        if rank == m:
            break
    return rank


def test_persistent_homology_vietoris_rips_and_bottleneck_stability() -> None:
    """Verify persistent_homology against dense F_2 boundary rank, scipy.stats.entropy, and Cohen-Steiner stability."""
    # Regular hexagon on unit circle: side = 1.0, short chord = sqrt(3) ~= 1.73205, diameter = 2.0
    angles = [k * math.pi / 3.0 for k in range(6)]
    pts = [(math.cos(theta), math.sin(theta)) for theta in angles]
    dist_mat: dict[int, dict[int, float]] = {}
    for i in range(6):
        dist_mat[i] = {}
        for j in range(6):
            if i != j:
                dist_mat[i][j] = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])

    fsc = FilteredSimplicialComplex.from_vietoris_rips(dist_mat, max_dim=2)
    intervals = persistent_homology(fsc, max_k=1)

    # 1. Verify H_1 barcode: 1 dominant loop born at t = 1.0 and killed at t = sqrt(3)
    h1_bars = [iv for iv in intervals if iv.dimension == 1]
    assert len(h1_bars) == 1
    assert math.isclose(h1_bars[0].birth, 1.0, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(h1_bars[0].death, math.sqrt(3.0), rel_tol=1e-12, abs_tol=1e-12)

    # 2. Verify Betti curve against dense F_2 Gaussian elimination rank of sublevel boundary matrices
    thresholds = [0.0, 0.5, 1.0, 1.2, 1.5, 1.8, 2.1]
    b0_curve = betti_curve(intervals, thresholds, dimension=0)
    b1_curve = betti_curve(intervals, thresholds, dimension=1)

    for idx, t in enumerate(thresholds):
        sub_sc = fsc.to_simplicial_complex(t)
        n0 = len(sub_sc._simplices.get(0, set()))
        n1 = len(sub_sc._simplices.get(1, set()))
        r1 = _gf2_rank_numpy(_sparse_boundary_to_dense(sub_sc, 1))
        r2 = _gf2_rank_numpy(_sparse_boundary_to_dense(sub_sc, 2))
        assert b0_curve[idx] == n0 - r1
        assert b1_curve[idx] == n1 - r1 - r2

    # 3. Verify persistence_entropy against scipy.stats.entropy
    synthetic_bars = [
        PersistenceInterval(0, 0.0, 1.5, (0,), (0, 1)),
        PersistenceInterval(0, 0.0, 3.0, (1,), (1, 2)),
        PersistenceInterval(1, 1.0, 5.5, (0, 2), (0, 1, 2)),
    ]
    ent_ax = persistence_entropy(synthetic_bars)
    ent_scipy = float(stats.entropy([1.5, 3.0, 4.5]))
    assert math.isclose(ent_ax, ent_scipy, rel_tol=1e-12, abs_tol=1e-12)

    # 4. Verify bottleneck_distance metric triangle inequality and Cohen-Steiner stability
    dgm_a = [
        PersistenceInterval(1, 1.0, 4.0, (0, 1), (0, 1, 2)),
        PersistenceInterval(1, 2.0, 2.6, (1, 2), (1, 2, 3)),
    ]
    dgm_b = [
        PersistenceInterval(1, 1.2, 3.7, (0, 1), (0, 1, 2)),
        PersistenceInterval(1, 2.1, 2.5, (1, 2), (1, 2, 3)),
    ]
    dgm_c = [
        PersistenceInterval(1, 0.9, 4.2, (0, 1), (0, 1, 2)),
    ]
    d_ab = bottleneck_distance(dgm_a, dgm_b, dimension=1)
    d_bc = bottleneck_distance(dgm_b, dgm_c, dimension=1)
    d_ac = bottleneck_distance(dgm_a, dgm_c, dimension=1)
    assert math.isclose(d_ab, 0.3, rel_tol=1e-12, abs_tol=1e-12)
    assert d_ac <= d_ab + d_bc + 1e-12
