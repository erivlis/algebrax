---
title: "EP-0251: Sparse Linear Algebra Kernel, Decomposition Correctness & Hot-Path Performance"
description: "Fix critical correctness and complexity bugs in matrix decompositions and sparse hot paths, and promote a shared Field-polymorphic sparse elimination kernel across matrix, topology, and analysis."
icon: lucide/cpu
status: final
---

# EP-0251: Sparse Linear Algebra Kernel, Decomposition Correctness & Hot-Path Performance

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0251                                                                       |
| **Title**         | Sparse Linear Algebra Kernel, Decomposition Correctness & Hot-Path Performance |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | ⚡ Shannon (Efficiency) & 🛡️ Golem (Safety)                                 |
| **Status**        | Final                                                                      |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-28                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal fixes critical correctness and algorithmic-complexity bugs in `algebrax.matrix`, `algebrax.converters`, `algebrax.topology`, and `algebrax.analysis`, promotes a single `Field[V]`-polymorphic sparse elimination kernel (`sparse_rref`, `rank`, `nullspace`) with `RectSparseMatrix[R, C, V]` and `Fraction` typing support, and cleanly removes the redundant `matrix.core.inverse` implementation in favor of $O(N^3)$ `matrix.inv`. It fixes broken LU key alignment across `lu_decompose` and `_solve_*`, universal `key=str` integer-key corruption ($n \ge 11$), accidental $O(N^4)$ `inv()`, $O(N^2)$ `mat_vec` set allocation, exponential `SimplicialComplex` rebuilds, float boundary signs breaking exact finite-field homology, and sparse zero-omission bugs in graph calculus.

---

## Motivation

The Second Grand Council Audit exposed critical silent-wrong-result and asymptotic blowup bugs across the numerical and sparse linear algebra backbone:

1. **Silent Decomposition & Key-Ordering Failures (`matrix/decompose.py`, `converters.py`)**:
   - `_lu_decompose_float` and `_extract_field_lu` label `L`'s columns with `cols[:min_dim]` and `U`'s rows with `rows[:min_dim]`, breaking `P @ A == L @ U` whenever `rows != cols` (and `_solve_float`/`_solve_field` index `L` columns via `cols[j]`).
   - `det()` and `solve()` extract `rows` and `cols` independently via `get_matrix_keys`, causing sparse singular square-cardinality matrices with omitted zero rows/columns such as `{0: {1: 1.0}, 1: {2: 1.0}}` to return `det == 1.0` instead of `0.0`.
   - `converters.get_matrix_keys`, `solve_triangular`, `cholesky`, `cg_solve`, `analysis/calculus.py`, `display.py`, and `__main__.py` sort keys with `key=str`, placing `'10'` before `'2'` for integer indices $n \ge 11$ and silently corrupting solutions ($Lx \ne b$). `cholesky` also iterates `matrix.keys()` (rows only, ignoring column-only keys) and never validates symmetry.
   - `inv()` claims $O(N^3)$ via precomputed LU, yet calls `solve(matrix, e_r)` inside the column loop—recomputing `lu_decompose` $N$ times ($O(N^4)$). Meanwhile `matrix` co-exports two conflicting inverses (`matrix.core.inverse` vs. `matrix.decompose.inv`), and `grid_to_sparse`/`prune_sparse` fail to prune complex floating-point noise (`1e-17j`).
2. **Fragmented Elimination Kernels & Missing Rectangular Typing**:
   - Three separate elimination routines exist: dense-grid LU in `matrix/decompose.py`, float-only `_matrix_rank` in `topology/_core.py` (ignoring caller `tol` in `CellularSheaf` and locking homology out of $\mathbb{Q}$/$\mathbb{F}_p$ torsion), and sparse `Field[V]` pivot elimination buried privately in `variety/affine.py`.
   - `SimplicialComplex` stores boundary signs as `float` (`1.0`/`-1.0`), which crashes `ModularField.inv` (`pow()` requires `int`) and downgrades exact `Fraction` homology to `float`.
   - `typing.py` lacks `Fraction` in `N` and `RectSparseMatrix[R, C, V]` for rectangular boundary/incidence maps.
3. **Hot-Path Asymptotic Blowups**:
   - `matrix.core.mat_vec` delegates per row to `inner()`, which re-normalizes `sr`, re-binds methods, and allocates `set(row.keys()) & set(vector.keys())` on every row—turning sparse matrix-vector multiply into $O(\text{rows}(M) \cdot \text{nnz}(v))$ ($O(N^2)$) inside `cg_solve`, `fiedler_vector`, `laplacian_smoothing`, and `sheaf_diffusion`.
   - `SimplicialComplex.add_simplex` rebuilds **all** boundary matrices at every recursive sub-face insertion (up to $2^{k+1}-1$ rebuilds per $k$-simplex) and accepts degenerate repeated-vertex simplices like `(0, 0)`, breaking $\partial^2 = 0$.
   - `topology/persistence.py` scans all $\binom{N}{2}$ pairs in `_extract_vr_edges` (defeating sparsity) and uses unguarded recursive Hopcroft–Karp DFS (`RecursionError` risk for $\ge 1000$ features).
4. **Graph Calculus & Spectral Correctness Bugs (`analysis/`)**:
   - `gradient` and `laplacian` skip omitted sparse zero keys, returning `{}` on unit impulse `{0: 1.0}` and contradicting `mat_vec(laplacian_matrix(graph), field)`.
   - `fiedler_vector` performs an $O(N \cdot E)$ list scan (`neighbor in nodes`) with `queue.pop(0)`, directed-only BFS, and unsymmetrized degree computation (`calculus.py:740`).
   - `is_ramanujan_graph` strips *all* eigenvalues with $|\lambda| = d$, falsely certifying disconnected $d$-regular graphs (e.g., $K_4 \sqcup K_4$) as Ramanujan expanders.

---

## Rationale

- **⚡ Claude Shannon (Efficiency)**: Eliminating $O(N^4)$ `inv()`, $O(N^2)$ `mat_vec`, $O(2^k)$ simplex rebuilds, and $O(N^2)$ VR scans restores true sparse output-sensitive complexity without adding a single external dependency.
- **🛡️ The Golem (Safety & Containment)**: Explicit iterative Hopcroft–Karp DFS eliminates `RecursionError` cliffs; partial pivoting for float/complex sparse elimination prevents catastrophic cancellation; natural key ordering, Cholesky symmetry checks, and degenerate-simplex rejection prevent silent data corruption.
- **⚖️ Emmy Noether (Symmetry)**: One shared `Field[V]`-polymorphic elimination kernel (`sparse_rref`, `rank`, `nullspace`), one canonical `inv` (cleanly removing `matrix.core.inverse`), and operand-order-preserving `inner()` respect non-commutative semirings and exact finite fields alike.

---

## Specification

### 1. Core Typing Extensions & Canonical Key Ordering (`typing.py`, `converters.py`, `matrix/decompose.py`)
- **`src/algebrax/typing.py`**:
  - Add `Fraction` to `N = TypeVar('N', int, float, complex, Decimal, Fraction)`.
  - Add `RectSparseMatrix = Mapping[R, Mapping[C, V]]` for rectangular boundary, incidence, and restriction maps (preserving 2-parameter `SparseMatrix[K, V]` for square matrices).
- **`src/algebrax/converters.py`**:
  - Add public `canonical_sort_keys(keys: Iterable[K]) -> list[K]` that sorts homogeneous comparable keys (`int`, `tuple[int, ...]`, `str`) natively via `sorted(keys)` and falls back to `key=str` **only** on `TypeError` for mixed-type keys.
  - Update `get_matrix_keys`, `matrix/decompose.py` (`cholesky`, `solve_triangular`), `matrix/core.py` (`cg_solve`), `analysis/calculus.py`, `display.py`, and `__main__.py` to use `canonical_sort_keys`.
  - Fix `grid_to_sparse` and `prune_sparse` to prune complex floating-point noise (`abs(val) <= tol` for `isinstance(val, (int, float, complex))`).
- **`src/algebrax/matrix/decompose.py` & `core.py`**:
  - In `_lu_decompose_float` and `_extract_field_lu`, bind both `L`'s column keys and `U`'s row keys to a **shared inner pivot domain** (`rows[:min_dim]`) so `P @ A == L @ U` holds identically for rectangular and disjoint-label matrices. Update `_solve_float` and `_solve_field` to index `L` columns by `rows[j]`.
  - For square-operator APIs (`det`, `solve`, `inv`): check `len(rows) != len(cols)` **first** (raising `ValueError("Matrix must be square")`, preserving rectangular rejection), then check `set(rows) != set(cols)` for disjoint-domain square-cardinality endomorphisms with omitted zero rows/columns, returning `det = 0` / raising `SingularMatrixError` immediately.
  - In `cholesky`: collect the full key domain `canonical_sort_keys(set(rows) | set(cols))` (not `matrix.keys()` alone) and validate symmetry (`abs(A[i][j] - A[j][i]) <= tol`) over all present entries.
  - In `inv`: compute `lu_decompose(matrix, field=field, tol=tol)` **once** outside the column loop and reuse the factored `P, L, U` via forward/backward substitution ($O(N^3)$ total).
  - **Clean Cut**: Remove redundant `matrix.core.inverse` completely (`matrix.inv` in `matrix/decompose.py` is the single canonical inverse); update `rep/group.py`, `rep/lie.py`, `matrix/__init__.py`, docs, and tests to call `inv`.

### 2. Shared Sparse `Field[V]` Elimination Kernel (`src/algebrax/matrix/eliminate.py`)
Promote and generalize `variety/affine.py:_sparse_jacobian_pivot_rows` into a first-class sparse elimination module exported from `algebrax.matrix`:

```python
def sparse_rref(
    matrix: RectSparseMatrix[R, C, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> tuple[RectSparseMatrix[int, C, V], list[C]]:
    """Compute exact sparse Reduced Row Echelon Form and pivot column list over any Field[V]."""

def rank(
    matrix: RectSparseMatrix[R, C, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> int:
    """Compute exact matrix rank via forward-only sparse Field-polymorphic Gaussian elimination."""

def nullspace(
    matrix: RectSparseMatrix[R, C, V],
    *,
    cols: Iterable[C] | None = None,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> list[SparseVector[C, V]]:
    """Compute an exact basis of ker(A) via sparse RREF over any Field[V] (honoring omitted zero columns via cols)."""
```

- **Key Pre-Mapping & Two Pivot Regimes**:
  - Map row and column keys via `canonical_sort_keys` to dense integer indices `0..m-1`, `0..n-1` once up front (safe on mixed-type keys, fast integer hashing in inner loops).
  - **Exact regime** (`field is not None` and not float/complex): sparse pivot selection using `field.is_zero` and `field.inv`.
  - **Floating-point regime** (`field is None` or float/complex `StandardField`): **sparse partial pivoting** (selecting maximum `abs(val) > tol` in the active pivot column) for numerical stability matching `rep/lie.py` and `rep/invariant.py`.
  - `rank(...)` executes **forward elimination only** (skipping RREF back-substitution fill-in).
- Replace `variety/affine.py:_sparse_jacobian_pivot_rows`, `topology/_core.py:_matrix_rank`, `rep/invariant.py:_rref_row_basis`, and `rep/lie.py:_rref_nullspace` with calls to `algebrax.matrix.eliminate`.
- Thread `tol` (and optional `field: Field[V] | None`) through `CellularSheaf.global_sections_dimension`, `first_cohomology_dimension`, and `SimplicialComplex.betti_numbers`. Convert `SimplicialComplex` boundary signs to exact `(field.one, field.neg(field.one))` when `field` is supplied (and store integer `1`/`-1` signs on `SimplicialComplex` boundary matrices) so `ModularField(p)` and `Fraction` homology work with zero `float` coercion.

### 3. Core Hot-Path & Topology Performance Fixes
- **`src/algebrax/matrix/core.py`**:
  - Rewrite `inner(v1, v2, semiring)` to iterate directly over the smaller mapping **while preserving `(v1[k], v2[k])` operand order** (critical for non-commutative semirings like `StringSemiring`, `CliffordAlgebra`, `PathAlgebra`) with $O(\min(\text{nnz}(v_1), \text{nnz}(v_2)))$ lookups and zero set allocations.
  - Inline the inner-product loop directly inside `mat_vec` with a dedicated `if semiring is None:` native Python fast path (avoiding per-row `Semiring.normalize` and method re-binding).
  - Avoid the extra trailing `dot(base, base, sr)` in `power(matrix, n)` when `exp == 0`.
  - Use `collections.deque` in `_find_matrix_components`.
- **`src/algebrax/topology/homology.py` & `persistence.py`**:
  - Reject degenerate simplices with repeated vertices (`len(set(simplex)) != len(simplex)`) with `ValueError` in both `SimplicialComplex.add_simplex` and `FilteredSimplicialComplex.add_simplex`.
  - Split `_insert_simplex_no_rebuild(s_tuple)` from `add_simplex`, make `SimplicialComplex.boundary_matrices` a **lazy `@property`** backed by a `_dirty: bool` flag (preserving direct attribute reads with $O(1)$ amortized `add_simplex` and rebuilding once on first read), and store exact integer `1`/`-1` incidence signs.
  - Rewrite `_extract_vr_edges` in `topology/persistence.py` to iterate only over present entries in `distance_matrix` ($O(\text{nnz})$), canonicalizing `(min(u, v), max(u, v))`, skipping `u == v`, and taking `max(d_uv, d_vu)` **before** filtering `<= max_edge_length`.
  - Replace recursive Hopcroft–Karp `dfs(u)` in `_has_perfect_bipartite_matching` with an explicit iterative DFS stack.

### 4. Graph Calculus & Spectral Correctness (`src/algebrax/analysis/`)
- **`src/algebrax/analysis/calculus.py`**:
  - Fix `gradient` (with zero-pruning) and `laplacian` (matching `laplacian_matrix` symmetrization/self-loop parity) to respect sparse zero omission over all edges incident to the support of `field`, guaranteeing `laplacian(f, G) == mat_vec(laplacian_matrix(G), f)`.
  - In `fiedler_vector`, replace `queue.pop(0)` + `neighbor in nodes` with `collections.deque`, a `set` of nodes, an undirected adjacency map built once, and symmetrized `degrees` (fixing line `740` for `normalized=True` on upper-triangular graphs).
- **`src/algebrax/analysis/spectral.py`**:
  - Fix `is_ramanujan_graph` to remove at most **one** trivial $+d$ eigenvalue (and at most one $-d$ eigenvalue if bipartite), so disconnected $d$-regular graphs with repeated $\lambda = d$ return `is_ramanujan = False`.

---

## Acceptance Criteria

1. `P @ A == L @ U` holds for rectangular and disjoint-key matrices; `solve(A, b)` passes for disjoint-key systems; `det({0: {1: 1.0}, 1: {2: 1.0}}) == 0.0`; rectangular `{0: {0: 1.0, 1: 2.0}}` still raises `ValueError("square")` in `det`/`solve`/`inv`.
2. `solve_triangular` and `cholesky` produce exact solutions for $n \ge 12$ integer-indexed matrices; `cholesky` rejects asymmetric matrices and column-only keys with `ValueError`.
3. `inv()` invokes `lu_decompose` **exactly once** (verified via spy/monkeypatch count `== 1`); `matrix.core.inverse` is cleanly removed and all complex-matrix callers (`rep/group.py`, `rep/lie.py`) pass using `inv()`.
4. `sparse_rref`, `rank`, and `nullspace` match exact reference solutions over `StandardField(float)`, `StandardField(complex)`, `StandardField(Fraction)`, and `ModularField(p)` on rectangular matrices with omitted zero columns; `SimplicialComplex.betti_numbers(field=ModularField(2))` detects $\mathbb{RP}^2$ $\mathbb{Z}/2\mathbb{Z}$ torsion ($\beta_1(\mathbb{RP}^2; \mathbb{F}_2) = 1$ vs. $\beta_1(\mathbb{RP}^2; \mathbb{Q}) = 0$).
5. `inner(v1, v2, sr)` preserves non-commutative order on `StringSemiring` and `CliffordAlgebra` when `len(v1) != len(v2)`.
6. Inserting a 5-simplex into `SimplicialComplex` triggers `_rebuild_boundary_matrices()` **at most once** upon reading `boundary_matrices`; degenerate `(0, 0)` raises `ValueError` in both `SimplicialComplex` and `FilteredSimplicialComplex`.
7. Iterative Hopcroft–Karp handles bipartite matchings of size $N \ge 1500$ without `RecursionError`.
8. `laplacian({0: 1.0}, G) == mat_vec(laplacian_matrix(G), {0: 1.0})` on unweighted, weighted, and upper-triangular graphs; `is_ramanujan_graph` returns `False` on disconnected $K_4 \sqcup K_4$.
9. New public exports (`canonical_sort_keys`, `sparse_rref`, `rank`, `nullspace`, `RectSparseMatrix`) comply with `EP-0002` (AMDS) and pass `tests/algebrax/test_docstrings.py`.

---

## Backwards Compatibility

- **Additive**: `matrix.rank`, `matrix.nullspace`, `matrix.sparse_rref`, `converters.canonical_sort_keys`, `typing.RectSparseMatrix`, `Fraction` in `typing.N`, and optional `field` parameter on topological Betti/cohomology rank helpers.
- **Intentional clean cuts & behavior fixes**:
  - `matrix.core.inverse` is cleanly removed; use `matrix.inv` (single canonical $O(N^3)$ inverse).
  - `cholesky` raises `ValueError` on asymmetric matrices.
  - `SimplicialComplex.add_simplex` and `FilteredSimplicialComplex.add_simplex` raise `ValueError` on degenerate repeated-vertex simplices.
  - `gradient` / `laplacian` include boundary edges between nonzero and omitted-zero vertices.
  - `is_ramanujan_graph` returns `False` for disconnected $d$-regular graphs.

---

## How to Teach This / Documentation Plan

- Ensure `algebrax.matrix.eliminate` and `converters.canonical_sort_keys` conform to `EP-0002` (AMDS) and `tests/algebrax/test_docstrings.py`.
- Update [`docs/guide/matrix/core.md`](../guide/matrix/core.md) (replacing `inverse` Gauss-Jordan notes with `inv`), [`docs/guide/matrix/decompositions.md`](../guide/matrix/decompositions.md), and [`docs/guide/algebra/exact_matrix_solvers.md`](../guide/algebra/exact_matrix_solvers.md) for `rank`, `nullspace`, `sparse_rref`, and exact $\mathbb{Q}$/$\mathbb{F}_p$ homology.
- Update [`docs/guide/topology/homology.md`](../guide/topology/homology.md), [`docs/guide/topology/sheaf.md`](../guide/topology/sheaf.md), [`docs/guide/matrix/benchmarks.md`](../guide/matrix/benchmarks.md), and [`docs/guide/analysis/discrete_calculus.md`](../guide/analysis/discrete_calculus.md).

---

## Reference Implementation

Target files verified in the Second Grand Council Audit & Review:
- `src/algebrax/typing.py`, `src/algebrax/converters.py`
- `src/algebrax/matrix/{core.py,decompose.py,eliminate.py,__init__.py}`
- `src/algebrax/topology/{_core.py,homology.py,persistence.py,sheaf.py}`
- `src/algebrax/analysis/{calculus.py,spectral.py}`
- `src/algebrax/variety/affine.py`, `src/algebrax/rep/{group.py,lie.py,invariant.py}`

---

## Rejected Ideas

1. **Keeping `matrix.core.inverse` as a Deprecated Wrapper Around `matrix.inv`**:
   - *Rejected*: Co-exporting two identical matrix inverses violates Shannon's minimalism and Feynman's Freshman Test. Cleanly unifying on `matrix.inv` leaves one canonical entry point.
2. **Always Converting Keys to `int` Internally in `decompose.py`**:
   - *Rejected*: Breaks AlgebraX's key-polymorphic design (`str`, simplex tuples, `StalkCoord`). `canonical_sort_keys` preserves arbitrary hashable keys while fixing numeric order for $n \ge 11$.
3. **Swapping `(v1, v2)` Directly in `inner()`**:
   - *Rejected*: Breaks non-commutative semirings (`StringSemiring`, `CliffordAlgebra`, `PathAlgebra`). Iterate over the smaller mapping while always evaluating `sr.mul(v1[k], v2[k])`.
4. **Using Unpivoted Exact Elimination for Float/Complex Matrices in `eliminate.py`**:
   - *Rejected*: Causes catastrophic cancellation on ill-conditioned real/complex inputs; two pivot regimes (exact sparse vs. float/complex sparse partial pivoting) keep both regimes exact and stable.

---

## Open Questions

None. Both `matrix.core.inverse` removal and lazy `_dirty` `SimplicialComplex.boundary_matrices` are decided.

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Shannon, Golem, Popper, Explorer, Feynman).
* **2026-11-27:**
  * Incorporated Grand Council Pre-Implementation Review revisions: centralized `canonical_sort_keys` in `converters.py`, moved `RectSparseMatrix`/`typing.N` (`Fraction`) from `EP-0252`, added `_solve_float`/`_solve_field` `L`-index fix and rectangular `ValueError`-first guard, added two-regime pivoting + `cols` param + forward-only `rank` in `eliminate.py`, fixed `SimplicialComplex` integer signs + lazy `_dirty` `@property` + `FilteredSimplicialComplex` parity, fixed non-commutative `inner()` order and `mat_vec` fast path, fixed `fiedler_vector` symmetrized degrees and complex pruning, cleanly removed `matrix.core.inverse`, added Acceptance Criteria and AMDS/guide checklist, and promoted status to `Accepted`.
* **2026-11-28:**
  * Implemented full specification across `typing.py`, `converters.py`, `matrix/{core,decompose,eliminate}.py`, `topology/{_core,homology,persistence,sheaf}.py`, `analysis/{calculus,spectral}.py`, `variety/affine.py`, and `rep/{group,lie,invariant}.py`; added `tests/algebrax/test_linalg_kernel_and_hotpaths.py`, updated user guides, verified all 1,040 tests + Ruff + Pyrefly, and promoted status to `Final`.
