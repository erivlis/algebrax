---
title: "EP-0214: Invariant Theory, Molien Series & Casimir Polynomials"
description: "Formalize classical invariant rings, the Reynolds projection operator, Molien's generating series, and polynomial Casimir invariants over sparse matrix actions."
icon: lucide/shield-check
status: final
---

# EP-0214: Invariant Theory, Molien Series & Casimir Polynomials

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0214                                                                              |
| **Title**         | Invariant Theory, Molien Series & Casimir Polynomials                             |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | ⚖️ Noether (Invariant Rings) & ⚡ Shannon (Sparse Monomial Actions)               |
| **Status**        | Final                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-11-22                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational framework for **Classical Invariant Theory** in AlgebraX, formalizing polynomial functions and algebraic tensors that remain invariant under linear group actions and Lie symmetries atop [`algebrax.group`](EP-0210-group-representations-character-tables-schurs-lemma.md), [`algebrax.rep`](EP-0210-group-representations-character-tables-schurs-lemma.md), and [`algebrax.lie`](EP-0211-lie-algebra-representations-clebsch-gordan.md). EP-0214 introduces:

1. **The Polynomial Reynolds Symmetrization Operator & Homogeneous Bases (`algebrax.rep.invariant`)**:
   An idempotent projection operator $\mathcal{R} : K[V] \to K[V]^G$ complementing linear operator averaging (`reynolds_average` in `algebrax.rep.group`), alongside symbolic monomial projection (`reynolds_monomial_projection`), unboxed polynomial evaluation (`evaluate_sparse_polynomial`), and canonical RREF homogeneous invariant bases (`invariant_basis_at_degree`):
   $$\mathcal{R}(f)(\mathbf{x}) = \frac{1}{|G|} \sum_{g \in G} f(\rho(g^{-1}) \mathbf{x}), \quad \mathcal{R}^2 = \mathcal{R}$$
2. **Molien's Generating Series (`algebrax.rep.invariant`)**:
   Exact computation of the Hilbert series of the graded invariant ring $K[V]^G = \bigoplus_{d=0}^\infty K[V]_d^G$ using Theodor Molien's 1897 determinant formula over `FiniteGroup[G]` or raw element sequences:
   $$M(t) = \sum_{d=0}^\infty \dim(K[V]_d^G) t^d = \frac{1}{|G|} \sum_{g \in G} \frac{1}{\det(\mathbf{I}_n - t \rho(g))} = \frac{P(t)}{\prod_{i=1}^n (1 - t^{d_i})}$$
   evaluated via pure-Python sparse Faddeev–LeVerrier characteristic polynomials, exact cyclotomic cancellation in $\mathbb{Z}[t]$, Krull-dimension-preserving Cohen–Macaulay factor packing, and arbitrary-precision integer DP series expansion.
3. **Primary & Secondary Invariants (Cohen–Macaulay Decomposition)**:
   Decomposing the invariant ring as a free module over a polynomial subring (Hochster–Eagon theorem):
   $$K[V]^G = \bigoplus_{j=1}^m \eta_j \cdot K[\theta_1, \dots, \theta_n]$$
   where $\theta_i$ are algebraically independent primary invariants (denominator degrees $d_i$), and $\eta_j$ are secondary invariants (non-negative numerator coefficients $P(t)$).
4. **High-Order Lie Casimir Invariants (`algebrax.rep.lie`, re-exported in `algebrax.rep` and lazily in `algebrax.lie`)**:
   Extending [`EP-0211`](EP-0211-lie-algebra-representations-clebsch-gordan.md) quadratic Casimirs to higher-order polynomial invariants in the symmetric algebra $S(\mathfrak{g})^\mathfrak{g} \cong \mathcal{Z}(U(\mathfrak{g}))$, via `cubic_casimir_tensor` ($d_{ijk}$) and `cubic_casimir_operator` ($C_3 = \sum_{i,j,k} d^{ijk} \rho(X_i)\rho(X_j)\rho(X_k)$).
5. **Property-Based Verification (`src/algebrax/verification.py`)**:
   Automated verification of Reynolds idempotency (`verify_reynolds_idempotency`), polynomial invariance $f(\rho(g) \mathbf{x}) = f(\mathbf{x})$ (`verify_polynomial_invariance`), Molien series expansion matching monomial counting (`verify_molien_expansion`), and cubic Casimir total symmetry and $\mathrm{ad}$-invariance (`verify_cubic_casimir_invariance`), returning `dict[str, bool]`.

---

## Motivation

Invariant theory—founded by Cayley, Sylvester, Gordan, and Hilbert—is the historical birthplace of modern abstract algebra. In modern science:

1. **Feature Engineering & Machine Learning**: Symmetries in data (rotations, reflections, permutations) require invariant features. Machine learning architectures (SE(3)-equivariant networks, Graph Neural Networks) rely on polynomial invariants of groups to guarantee invariance.
2. **Physics & Conserved Quantities**: By Emmy Noether’s theorem, every continuous symmetry produces an invariant conservation law. Casimir polynomials in Lie algebras classify quantum charges, particle mass formulas, and distinguish conjugate representations such as $\mathbf{3}$ vs $\bar{\mathbf{3}}$ of $\mathfrak{su}(3)/\mathfrak{sl}(3)$.
3. **Counting Symmetries via Molien’s Formula**: Knowing *a priori* how many independent invariants exist at degree $d$ (via Molien series) prevents redundant search and verifies complete invariant generating sets.

---

## Rationale & Council Alignment

- **⚖️ Noether (Foundational Invariant Theory)**:
  Emmy Noether proved in 1915 (*Der Endlichkeitssatz der Invarianten endlicher Gruppen*) that the invariant ring of a finite group is always finitely generated by polynomials of degree at most $|G|$. This EP is dedicated directly to her mathematical legacy.
- **⚡ Shannon (Zero Bloat & Sparse Determinant Evaluation)**:
  Molien’s formula evaluates $\det(\mathbf{I} - t \rho(g))$ via sparse Faddeev–LeVerrier characteristic polynomials grouped by identical charpolys, avoiding explosive $O(n^d)$ monomial generation. Consolidating polynomial Reynolds and Molien helpers into `src/algebrax/rep/invariant.py` while routing Lie Casimir tensors alongside `quadratic_casimir` in `src/algebrax/rep/lie.py` avoids fragmenting cohesive invariants across tiny modules.
- **🔬 Popper (Falsifiable Invariants)**:
  Every generated invariant $f(\mathbf{x})$ is subjected to empirical falsification: evaluating $|f(\rho(g) \mathbf{x}) - f(\mathbf{x})| \le 10^{-11}$ across deterministic Gaussian probe vectors and all $g \in G$, while cubic tensors $d_{ijk}$ are verified for $S_3$ total symmetry and $\mathrm{ad}$-invariance.
- **🧩 Russell (Graded Algebra Taxonomy & Dennis Point)**:
  1. *Default representation for `cubic_casimir_tensor`*: Because the adjoint representation of any semisimple Lie algebra is self-dual (real), $\operatorname{Tr}(\mathrm{ad}_i \{\mathrm{ad}_j, \mathrm{ad}_k\}) \equiv 0$ identically even for $\mathfrak{sl}_3/\mathfrak{su}_3$. Therefore `cubic_casimir_tensor` defaults to `defining_representation(algebra)` when `algebra.matrix_basis is not None` (falling back to `adjoint_representation(algebra)` only if no matrix basis is attached).
  2. *Non-orthogonal Reynolds projection*: Averaging over `{rep(group.inv(g))}` when a `FiniteGroup` is supplied — or `{rep(g)}` over a closed finite sequence since $\{g^{-1} : g \in G\} = G$ — preserves exactness for arbitrary similarity-conjugated non-orthogonal representations $S\rho(g)S^{-1}$ without assuming unitarity or falling back to `transpose(rep(g))`.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"If you spin a square on a table, $x^2 + y^2$ doesn't change, and $x^4 + y^4$ doesn't change. Molien's series is a magic cash register that tells you exactly how many such unbreakable formulas exist at each power!"*

---

## Specification

### 1. Polynomial Reynolds Symmetrizer, Bases & Molien Series (`src/algebrax/rep/invariant.py`)

```python
@dataclass(frozen=True)
class MolienSeries:
    """Rational generating function M(t) = P(t) / prod_i (1 - t^{d_i}) for invariant dimensions."""

    numerator_coeffs: tuple[int, ...]
    denominator_factors: tuple[int, ...]

    def series(self, max_degree: int) -> list[int]: ...
    def coefficient(self, degree: int) -> int: ...
    def denominator_coeffs(self) -> tuple[int, ...]: ...
    def evaluate(self, t: float | complex) -> float | complex: ...


def compute_molien_series(
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    tol: float = 1e-7,
) -> MolienSeries: ...


def reynolds_polynomial_operator(
    poly_eval: Callable[[Sequence[Any]], Any],
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
) -> Callable[[Sequence[Any]], Any]: ...


def evaluate_sparse_polynomial(
    poly: dict[tuple[int, ...], float | complex],
    x: Sequence[float | complex],
) -> float | complex: ...


def reynolds_monomial_projection(
    exponents: tuple[int, ...],
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    tol: float = 1e-12,
) -> dict[tuple[int, ...], float | complex]: ...


def invariant_basis_at_degree(
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    degree: int,
    tol: float = 1e-9,
) -> list[dict[tuple[int, ...], float | complex]]: ...
```

### 2. High-Order Lie Casimir Invariants (`src/algebrax/rep/lie.py`, re-exported in `algebrax.rep` & `algebrax.lie`)

```python
def cubic_casimir_tensor(
    algebra: LieAlgebra,
    rep: LieRepresentation[Any] | None = None,
    tol: float = 1e-12,
) -> dict[tuple[int, int, int], float | complex]:
    """Compute totally symmetric cubic invariant tensor d_{ijk} = Tr(rho(X_i){rho(X_j), rho(X_k)}).

    Defaults to defining_representation(algebra) when algebra.matrix_basis is present
    (since adjoint representations are self-dual and have d_{ijk} == 0 identically).
    Non-zero for sl_n / su_n (n >= 3); empty {} for self-dual algebras (su_2, so_3, sp_1).
    """
    ...


def cubic_casimir_operator(
    rep: LieRepresentation[Any],
    algebra: LieAlgebra | None = None,
    d_tensor: dict[tuple[int, int, int], float | complex] | None = None,
    killing_metric_inv: SparseMatrix[int, Any] | None = None,
    tol: float = 1e-12,
) -> SparseMatrix[int, Any]:
    """Construct the cubic Casimir operator C_3 = sum_{i,j,k} d^{ijk} rho(X_i) rho(X_j) rho(X_k)."""
    ...
```

### 3. Verification Suite (`src/algebrax/verification.py`)

```python
def verify_reynolds_idempotency(
    reynolds_fn: Callable[[Callable[[Sequence[Any]], Any]], Callable[[Sequence[Any]], Any]],
    test_poly: Callable[[Sequence[Any]], Any],
    test_point: Sequence[float | complex],
    tol: float = 1e-11,
) -> dict[str, bool]: ...


def verify_polynomial_invariance(
    poly: Callable[[Sequence[Any]], Any] | dict[tuple[int, ...], float | complex],
    rep: Any,
    elements_or_group: Any,
    dimension: int | None = None,
    num_probes: int = 50,
    seed: int = 42,
    tol: float = 1e-11,
) -> dict[str, bool]: ...


def verify_molien_expansion(
    series: Any,
    actual_dimensions: Sequence[int],
) -> dict[str, bool]: ...


def verify_cubic_casimir_invariance(
    algebra: Any,
    d_tensor: dict[tuple[int, int, int], float | complex] | None = None,
    rep: Any = None,
    tol: float = 1e-9,
) -> dict[str, bool]: ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. Group invariant tools live in `algebrax.rep.invariant` (re-exported in `algebrax.rep`), high-order Casimirs extend `algebrax.rep.lie` (re-exported in `algebrax.rep` and lazily in `algebrax.lie`), and all four verifiers reside in `src/algebrax/verification.py`, integrating seamlessly with `algebrax.group.FiniteGroup`.

---

## How to Teach This / Documentation Plan

- **Guide**: `docs/guide/algebra/invariant_theory.md` (registered in `zensical.toml`, cross-linked from `representations.md` and `lie_representations.md`):
  - Exact Molien series for $V_4$, $D_8$, $S_3$, $Q_8$ (Kleinian $D_4$ singularity), and $A_5$ (icosahedral rotation group).
  - Polynomial Reynolds symmetrization, symbolic monomial projection, and homogeneous invariant bases verified against Molien's theorem.
  - Separating $\mathbf{3}$ vs $\bar{\mathbf{3}}$ of $\mathfrak{sl}_3/\mathfrak{su}_3$ via the cubic Casimir $C_3$ and $d_{ijk}$.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for Molien's determinant formula, Reynolds projection, and cubic Casimir contractions.

---

## Reference Implementation

- **Polynomial Invariant Theory & Molien Series**: `src/algebrax/rep/invariant.py`
- **Cubic Lie Casimir Tensor & Operator**: `src/algebrax/rep/lie.py`
- **Public & Lazy Package Re-exports**: `src/algebrax/rep/__init__.py`, `src/algebrax/lie/__init__.py`
- **Verification Predicates**: `src/algebrax/verification.py`
- **Unit, Integration & Falsification Tests**: `tests/algebrax/test_rep_invariant.py`
- **SymPy Differential Oracle Tests & Traceability**: `tests/verifications/test_differential_sympy.py`, `docs/verification.md`
- **User Guide**: `docs/guide/algebra/invariant_theory.md`

---

## Rejected Ideas

1. **Pure Monomial Gröbner Basis Engines for Dimension Counting**:
   - *Rejected*: Computing invariant Hilbert dimensions exclusively via general Gröbner bases (Buchberger’s algorithm) is doubly exponential, whereas Molien’s formula provides the dimensions in polynomial time using linear algebra determinants. (Once invariant generators $\pi_1, \dots, \pi_m$ are found, their algebraic syzygies and GIT quotient variety $V // G$ are computed via [`EP-0220`](EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md) and `syzygy_variety` in [`EP-0221`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md)).
2. **Dense Multidimensional Arrays for High-Order Casimirs**:
   - *Rejected*: High-order invariant tensors $d_{i_1 \dots i_k}$ have $n^k$ entries but are highly symmetric and sparse. They are stored as unboxed sparse dictionaries `dict[tuple[int, int, int], float | complex]`.
3. **Adjoint Default for `cubic_casimir_tensor` and Transpose Fallback for Reynolds**:
   - *Rejected (Dennis Point)*: The adjoint representation of every semisimple Lie algebra is self-dual, making $\operatorname{Tr}(\mathrm{ad}_i \{\mathrm{ad}_j, \mathrm{ad}_k\}) \equiv 0$; defaulting to `defining_representation` produces the non-trivial $A_n$ ($n \ge 3$) cubic invariant out of the box. Likewise, replacing the `transpose(rep(g))` fallback with exact closed-group summation preserves accuracy on non-orthogonal representations.

---

## Open Questions

- [ ] Algorithm for automated primary invariant generation via King's algorithm.
- [ ] Invariant theory for continuous compact Lie groups via Weyl integration formula.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
* **2026-11-15:**
  * Aligned specification to consolidate Reynolds polynomial invariants and Molien series into `src/algebrax/rep/invariant.py` accepting `FiniteGroup[G]`, route `cubic_casimir_tensor` into `src/algebrax/rep/lie.py` (re-exported in `algebrax.lie`), and place verifiers returning `dict[str, bool]` in `src/algebrax/verification.py`.
* **2026-11-22:**
  * Implemented full specification (`src/algebrax/rep/invariant.py`, `src/algebrax/rep/lie.py`, `src/algebrax/verification.py`), SymPy differential verification (`tests/verifications/test_differential_sympy.py`), unit/falsification tests (`tests/algebrax/test_rep_invariant.py`), and user guide (`docs/guide/algebra/invariant_theory.md`).
  * Recorded Dennis Point refinements (`defining_representation` default for `cubic_casimir_tensor` and exact closed-group non-orthogonal Reynolds averaging) and transitioned status to Final.
