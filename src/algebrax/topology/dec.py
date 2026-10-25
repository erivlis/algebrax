"""Discrete Exterior Calculus (DEC) operators, Hodge star, and Helmholtz-Hodge flow decomposition."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple

from algebrax.semiring import Semiring
from algebrax.topology.cohomology import Cochain, coboundary
from algebrax.topology.homology import SimplicialComplex, SparseChainComplex
from algebrax.typing import K, SparseMatrix, V

__all__ = [
    'HodgeDecomposition',
    'codifferential',
    'exterior_derivative',
    'helmholtz_hodge_decomposition',
    'hodge_laplacian',
    'hodge_star',
]


class HodgeDecomposition(NamedTuple):
    r"""Orthogonal Helmholtz-Hodge decomposition of a discrete 1-form $\omega = d\alpha + \delta\beta + \gamma$.

    Attributes:
        exact: Curl-free gradient flow $d_0 \alpha \in \operatorname{im}(d_0)$.
        coexact: Divergence-free solenoidal circulation $\delta_2 \beta \in \operatorname{im}(\delta_2)$.
        harmonic: Topological harmonic circulation $\gamma \in \ker(\Delta_1) \cong H^1(K; \mathbb{R})$.
        potential: Node scalar potential 0-cochain $\alpha \in C^0(K; \mathbb{R})$ such that `exact = d_0(alpha)`.
        stream: Triangle curl stream 2-cochain $\beta \in C^2(K; \mathbb{R})$ such that `coexact = delta_2(beta)`.
    """

    exact: Cochain[int, float]
    coexact: Cochain[int, float]
    harmonic: Cochain[int, float]
    potential: Cochain[int, float]
    stream: Cochain[int, float]


def exterior_derivative(complex: SparseChainComplex, k: int) -> SparseMatrix:
    r"""Construct the discrete exterior derivative operator $d_k: \Omega^k(K) \to \Omega^{k+1}(K)$.

    Algebraic Signature:
        $\langle d_k \omega, \sigma_{k+1} \rangle = \langle \omega, \partial_{k+1} \sigma_{k+1} \rangle
        \implies d_k = \partial_{k+1}^T$

    Carrier:
        `SparseMatrix[Simplex, float]` (Incidence matrix mapping $k$-simplices to $(k+1)$-simplices).

    Operations:
        - Boundary Transpose: Transposes the $(k+1)$-th boundary operator $D_{k+1}$.

    Properties:
        Satisfies exact cochain nilpotency $d_{k+1} \circ d_k = 0$.

    Applications:
        - Discrete gradient ($d_0$), discrete curl ($d_1$), and higher exterior derivatives.
        - Simplicial cohomology and Helmholtz-Hodge decomposition.

    Args:
        complex: `SimplicialComplex` or `SparseChainComplex` instance.
        k: Cochain degree $k \ge 0$.

    Returns:
        Sparse matrix representation of $d_k$.
    """
    return coboundary(complex, k)


def codifferential(
    complex: SparseChainComplex,
    k: int,
    dual_weights_k: Mapping[tuple[int, ...], float] | None = None,
    dual_weights_km1: Mapping[tuple[int, ...], float] | None = None,
) -> SparseMatrix:
    r"""Construct the discrete codifferential operator $\delta_k = d_{k-1}^*: \Omega^k(K) \to \Omega^{k-1}(K)$.

    Algebraic Signature:
        $\delta_k = \star_{k-1}^{-1} \circ \partial_k \circ \star_k$
        (reduces to $\partial_k$ under combinatorial unit Hodge star weights).

    Carrier:
        `SparseMatrix[Simplex, float]` (Matrix mapping $k$-simplices to $(k-1)$-simplices).

    Operations:
        - Adjoint Projection: Scales columns by $\star_k$ and rows by $\star_{k-1}^{-1}$ on $D_k$.

    Properties:
        Satisfies nilpotency $\delta_{k-1} \circ \delta_k = 0$ and formal adjointness
        $\langle d_{k-1} \alpha, \beta \rangle = \langle \alpha, \delta_k \beta \rangle$.

    Applications:
        - Discrete divergence ($\delta_1$) of edge flows and rotational coexact flux ($\delta_2$) from 2-simplices.

    Args:
        complex: `SimplicialComplex` or `SparseChainComplex` instance.
        k: Cochain degree $k \ge 1$.
        dual_weights_k: Optional positive Hodge star weights on $k$-simplices.
        dual_weights_km1: Optional positive Hodge star weights on $(k-1)$-simplices.

    Returns:
        Sparse matrix representation of $\delta_k$.
    """
    d_k = complex.boundary_matrices.get(k, {})
    if not d_k:
        return {}
    if dual_weights_k is None and dual_weights_km1 is None:
        return {r: dict(row) for r, row in d_k.items()}

    res = {}
    for face, row in d_k.items():
        w_km1 = float(dual_weights_km1.get(face, 1.0)) if dual_weights_km1 is not None else 1.0
        if w_km1 == 0.0:  # NOSONAR - exact zero singularity guard
            continue
        scaled_row = {}
        for simplex, val in row.items():
            w_k = float(dual_weights_k.get(simplex, 1.0)) if dual_weights_k is not None else 1.0
            scaled = float(val) * (w_k / w_km1)
            if scaled != 0.0:  # NOSONAR - structural sparse zero pruning
                scaled_row[simplex] = scaled
        if scaled_row:
            res[face] = scaled_row
    return res


def hodge_star(
    form: Cochain[K, float] | Mapping[tuple[K, ...], float],
    dual_weights: Mapping[tuple[K, ...], float] | None = None,
    *,
    inverse: bool = False,
    tol: float = 1e-14,
) -> Cochain[K, float]:
    r"""Apply the diagonal discrete Hodge star operator $\star_k$ (or $\star_k^{-1}$) to a $k$-cochain.

    Algebraic Signature:
        $(\star_k \omega)(\sigma) = \frac{|\sigma^\star|}{|\sigma|} \omega(\sigma) = w_\sigma \omega(\sigma)$

    Carrier:
        `Cochain[K, float]` (Metric-weighted dual cochain indexed by primal simplices).

    Operations:
        - Diagonal Volume Scaling: Multiplies (or divides when `inverse=True`) each simplex coefficient
          by its dual-to-primal volume ratio $w_\sigma$ (defaulting to combinatorial identity $w_\sigma = 1$).

    Properties:
        Defines the discrete $L^2$ inner product
        $\langle \alpha, \beta \rangle_\star = \langle \alpha, \star \beta \rangle$.

    Applications:
        - Geometric weighting of circumcentric Voronoi dual meshes in Discrete Exterior Calculus.

    Args:
        form: Input `Cochain` or simplex-keyed dictionary.
        dual_weights: Optional mapping from canonical simplices to positive metric weights $w_\sigma > 0$.
        inverse: If True, divides by $w_\sigma$ to apply $\star_k^{-1}$.
        tol: Numerical pruning threshold.

    Returns:
        Weighted `Cochain[K, float]`.
    """
    c = form if isinstance(form, Cochain) else Cochain(form, tol=tol)
    if dual_weights is None:
        return c

    weights_c = Cochain(dual_weights, oriented=False, tol=0.0)
    scaled: dict[tuple[K, ...], float] = {}
    for s, val in c.items():
        w = float(weights_c.get(s, 1.0))
        if w <= 0.0:
            raise ValueError(f'Hodge star dual weight for simplex {s} must be positive, got {w}.')
        scaled[s] = (float(val) / w) if inverse else (float(val) * w)
    return Cochain(scaled, degree=c.degree, oriented=c.oriented, tol=tol)


def hodge_laplacian(
    complex: SparseChainComplex,
    k: int,
    semiring: Semiring[V] | type[Semiring[V]] | None = None,
) -> SparseMatrix:
    r"""Construct the $k$-th discrete Hodge Laplacian operator $\Delta_k = d_{k-1} \delta_k + \delta_{k+1} d_k$.

    Algebraic Signature:
        $\Delta_k = \partial_k^T \partial_k + \partial_{k+1} \partial_{k+1}^T : \Omega^k(K) \to \Omega^k(K)$

    Carrier:
        `SparseMatrix[Simplex, float]` (Symmetric positive semi-definite operator on $k$-cochains).

    Operations:
        - Down-Laplacian Assembly: Computes $\Delta_k^{\text{down}} = \partial_k^T \partial_k$.
        - Up-Laplacian Assembly: Computes $\Delta_k^{\text{up}} = \partial_{k+1} \partial_{k+1}^T$.

    Properties:
        $\ker(\Delta_k) = \ker(d_k) \cap \ker(\delta_k) \cong H^k(K; \mathbb{R})$ (Discrete Hodge Theorem).

    Applications:
        - Harmonic form extraction, edge flow diffusion, and higher-order spectral clustering.

    Args:
        complex: `SimplicialComplex` or `SparseChainComplex` instance.
        k: Cochain dimension $k \ge 0$.
        semiring: Optional semiring for generalized algebraic Laplacians.

    Returns:
        Sparse matrix representation of $\Delta_k$.
    """
    return complex.hodge_laplacian(k, semiring=semiring)


def _normalize_hodge_input(
    flow: Cochain[int, float] | Mapping[tuple[int, ...], float] | SparseMatrix[int, float],
    tol: float,
) -> Cochain[int, float]:
    if isinstance(flow, Cochain):
        return flow
    if not flow:
        return Cochain(degree=1, tol=tol)
    first_key = next(iter(flow))
    if isinstance(first_key, tuple):
        return Cochain(flow, degree=1, tol=tol)  # type: ignore[arg-type]
    return Cochain.from_flow(flow, tol=tol)  # type: ignore[arg-type]


def helmholtz_hodge_decomposition(
    complex: SimplicialComplex,
    flow: Cochain[int, float] | Mapping[tuple[int, ...], float] | SparseMatrix[int, float],
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> HodgeDecomposition:
    r"""Decompose a discrete 1-form (edge flow) into orthogonal exact, coexact, and harmonic components.

    Algebraic Signature:
        $\omega = d_0 \alpha + \delta_2 \beta + \gamma \in
        \operatorname{im}(d_0) \oplus \operatorname{im}(\delta_2) \oplus \ker(\Delta_1)$

    Carrier:
        `HodgeDecomposition(exact, coexact, harmonic, potential, stream)` where each component is a `Cochain`.

    Operations:
        - Exact Potential Projection: Solves $\Delta_0 \alpha = \partial_1 \omega$ via deflated `cg_solve`
          and evaluates $\omega_{\text{exact}} = d_0 \alpha = \partial_1^T \alpha$.
        - Coexact Curl Projection: Solves $\Delta_2^{\text{down}} \beta = d_1 \omega = \partial_2^T \omega$
          via `cg_solve` and evaluates $\omega_{\text{coexact}} = \delta_2 \beta = \partial_2 \beta$.
        - Harmonic Residual Extraction: Computes $\gamma = \omega - \omega_{\text{exact}} - \omega_{\text{coexact}}$.

    Properties:
        Mutually $L^2$-orthogonal decomposition satisfying
        $\langle d_0 \alpha, \delta_2 \beta \rangle = \langle d_0 \alpha, \gamma \rangle =
        \langle \delta_2 \beta, \gamma \rangle = 0$, with $d_1(d_0 \alpha) = 0$, $\delta_1(\delta_2 \beta) = 0$,
        and $\Delta_1 \gamma = 0$.

    Applications:
        - HodgeRank global ranking and cyclic inconsistency detection in pairwise comparisons.
        - Financial currency and DeFi triangular vs. global cycle arbitrage isolation.
        - Traffic engineering and fluid vortex separation on meshes.

    Args:
        complex: `SimplicialComplex` defining vertices (0-simplices), edges (1-simplices), and triangles (2-simplices).
        flow: Input 1-form supplied either as a `Cochain`, a tuple-keyed dict `{(u, v): val}`,
            or a nested adjacency matrix `{u: {v: val}}`.
        tol: Conjugate gradient convergence tolerance (default `1e-9`).
        max_iter: Maximum conjugate gradient iterations (default `1000`).

    Returns:
        `HodgeDecomposition` containing `(exact, coexact, harmonic, potential, stream)`.
    """
    from algebrax.matrix.core import cg_solve, dot, mat_vec, transpose

    clean_tol = max(tol * 10.0, 1e-11)
    omega = _normalize_hodge_input(flow, tol=clean_tol)

    # 1. Exact component: Delta_0 alpha = partial_1 omega, exact = d_0 alpha
    b1 = complex.boundary_matrices.get(1, {})
    d0 = transpose(b1)
    delta0 = dot(b1, d0)

    div_flow = mat_vec(b1, omega)
    alpha_raw = cg_solve(delta0, div_flow, tol=tol, max_iter=max_iter, project_nullspace=True)
    potential = Cochain(alpha_raw, degree=0, tol=clean_tol)
    exact = Cochain(mat_vec(d0, potential), degree=1, tol=clean_tol)

    # 2. Coexact component: (partial_2^T partial_2) beta = partial_2^T omega, coexact = partial_2 beta
    coexact: Cochain[int, float] = Cochain(degree=1, tol=clean_tol)
    stream: Cochain[int, float] = Cochain(degree=2, tol=clean_tol)
    b2 = complex.boundary_matrices.get(2)
    if b2:
        d1 = transpose(b2)
        delta2 = dot(d1, b2)
        curl_flow = mat_vec(d1, omega)
        beta_raw = cg_solve(delta2, curl_flow, tol=tol, max_iter=max_iter, project_nullspace=False)
        stream = Cochain(beta_raw, degree=2, tol=clean_tol)
        coexact = Cochain(mat_vec(b2, stream), degree=1, tol=clean_tol)

    # 3. Harmonic component: gamma = omega - exact - coexact
    harmonic_raw = omega - exact - coexact
    harmonic = Cochain(dict(harmonic_raw), degree=1, tol=clean_tol)

    return HodgeDecomposition(
        exact=exact,
        coexact=coexact,
        harmonic=harmonic,
        potential=potential,
        stream=stream,
    )
