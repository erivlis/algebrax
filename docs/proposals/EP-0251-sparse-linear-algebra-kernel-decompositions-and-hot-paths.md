---
title: "EP-0251: Sparse Linear Algebra Kernel, Decomposition Correctness & Hot-Path Performance"
description: "Fix critical correctness and complexity bugs in matrix decompositions and sparse hot paths, and promote a shared Field-polymorphic sparse elimination kernel across matrix, topology, and analysis."
icon: lucide/cpu
status: draft
---

# EP-0251: Sparse Linear Algebra Kernel, Decomposition Correctness & Hot-Path Performance

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0251                                                                       |
| **Title**         | Sparse Linear Algebra Kernel, Decomposition Correctness & Hot-Path Performance |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | ⚡ Shannon (Efficiency) & 🛡️ Golem (Safety)                                 |
| **Status**        | Draft                                                                      |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-26                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal fixes critical correctness and algorithmic-complexity bugs in `algebrax.matrix`, `algebrax.topology`, and `algebrax.analysis`, and consolidates three duplicated Gaussian elimination implementations into a single `Field[V]`-polymorphic sparse elimination kernel (`rank`, `nullspace`, `rref`). It fixes broken LU key alignment, $n \ge 11$ integer-key sorting corruption in `solve_triangular` and `cholesky`, accidental $O(N^4)$ `inv()`, $O(N^2)$ `mat_vec` set allocation, quadratic/exponential `SimplicialComplex` rebuilds, and sparse zero-omission bugs in graph calculus.

---

## Motivation

The Second Grand Council Audit exposed critical silent-wrong-result and asymptotic blowup bugs across the numerical and sparse linear algebra backbone:

1. **Silent Decomposition Failures (`matrix/decompose.py`)**:
   - `_lu_decompose_float` and `_extract_field_lu` label `L`'s columns with `cols[:min_dim]` and `U`'s rows with `rows[:min_dim]`, breaking `P @ A == L @ U` whenever `rows != cols` (rectangular or disjoint-label matrices).
   - `det()` and `solve()` extract `rows` and `cols` independently via `get_matrix_keys`, causing sparse singular matrices with omitted zero rows/columns such as `{0: {1: 1.0}, 1: {2: 1.0}}` to return `det == 1.0` instead of `0.0`.
   - `solve_triangular` and `cholesky` sort keys with `key=str`, placing `'10'` before `'2'` for integer indices $n \ge 11$ and silently corrupting solutions ($Lx \ne b$). `cholesky` also never validates symmetry, silently succeeding on asymmetric matrices with $LL^T \ne A$.
   - `inv()` claims $O(N^3)$ via precomputed LU in its docstring, yet calls `solve(matrix, e_r)` inside the column loop—recomputing `lu_decompose` $N$ times ($O(N^4)$). Meanwhile `matrix` co-exports two conflicting inverses (`matrix.inverse` vs. `matrix.inv`).
2. **Fragmented Elimination Kernels**:
   - Three separate elimination routines exist: dense-grid LU in `matrix/decompose.py`, float-only `_matrix_rank` in `topology/_core.py` (ignoring caller `tol` in `CellularSheaf` and locking homology out of $\mathbb{Q}$/$\mathbb{F}_p$ torsion), and true sparse `Field[V]` pivot elimination buried as a private helper in `variety/affine.py`.
3. **Hot-Path Asymptotic Blowups**:
   - `matrix.core.mat_vec` calls `inner()`, which allocates `set(row.keys()) & set(vector.keys())` on every row—turning sparse matrix-vector multiply into $O(\text{rows}(M) \cdot \text{nnz}(v))$ ($O(N^2)$) inside `cg_solve`, `fiedler_vector`, `laplacian_smoothing`, and `sheaf_diffusion`.
   - `SimplicialComplex.add_simplex` rebuilds **all** boundary matrices at every recursive sub-face insertion (up to $2^{k+1}-1$ rebuilds per $k$-simplex) and accepts degenerate repeated-vertex simplices like `(0, 0)`, breaking $\partial^2 = 0$.
   - `topology/persistence.py` scans all $\binom{N}{2}$ pairs in `_extract_vr_edges` (defeating sparsity) and uses unguarded recursive Hopcroft–Karp DFS (`RecursionError` risk for $\ge 1000$ features).
4. **Graph Calculus & Spectral Correctness Bugs (`analysis/`)**:
   - `gradient` and `laplacian` skip omitted sparse zero keys, returning `{}` on unit impulse `{0: 1.0}` and contradicting `mat_vec(laplacian_matrix(graph), field)`.
   - `fiedler_vector` performs an $O(N \cdot E)$ list membership scan (`neighbor in nodes`) with `queue.pop(0)` and directed-only BFS (misclassifying upper-triangular connected graphs as disconnected).
   - `is_ramanujan_graph` strips *all* eigenvalues with $|\lambda| = d$, falsely certifying disconnected $d$-regular graphs (e.g., $K_4 \sqcup K_4$) as Ramanujan expanders.

---

## Rationale

- **⚡ Claude Shannon (Efficiency)**: Eliminating $O(N^4)$ `inv()`, $O(N^2)$ `mat_vec`, $O(2^k)$ simplex rebuilds, and $O(N^2)$ VR scans restores true sparse output-sensitive complexity without adding a single external dependency.
- **🛡️ The Golem (Safety & Containment)**: Converting Hopcroft–Karp DFS to an explicit iterative stack eliminates `RecursionError` cliffs; enforcing natural key ordering, Cholesky symmetry checks, and degenerate-simplex rejection prevents silent data corruption.
- **⚖️ Emmy Noether (Symmetry)**: Promoting one sparse `Field[V]` elimination kernel (`rank`, `nullspace`, `rref`) eliminates three inconsistent implementations and lets `matrix`, `topology`, `rep`, and `variety` share one exact foundation.

---

## Specification

### 1. Canonical Key Ordering & Unified Square Domains (`matrix/decompose.py`)
- Add a helper `_canonical_sort_keys(keys: Iterable[K]) -> list[K]` that sorts homogeneous comparable keys (such as `int`, `tuple[int, ...]`, `str`) natively (`sorted(keys)`) and falls back to `key=str` **only** when `TypeError` occurs on mixed-type keys.
- In `_lu_decompose_float` and `_extract_field_lu`, bind both `L`'s column keys and `U`'s row keys to a **shared inner pivot domain** (`rows[:min_dim]`) so `P @ A == L @ U` holds identically for rectangular and disjoint-label matrices.
- For square-operator APIs (`det`, `solve`, `inv`), compute the unified operator key space `domain = _canonical_sort_keys(set(rows) | set(cols))` when `rows` and `cols` share a domain (or detect rank deficiency immediately when a row/column index is absent, returning `det = 0` / raising `SingularMatrixError`).
- In `cholesky`: validate symmetry (`abs(A[i][j] - A[j][i]) <= tol`) over all present entries and use `_canonical_sort_keys`.
- In `solve_triangular`: use `_canonical_sort_keys` so integer keys `0..N-1` sort numerically for arbitrary $N$.
- In `inv`: compute `lu_decompose(matrix, field=field, tol=tol)` **once** outside the column loop and reuse the factored `P, L, U` via forward/backward substitution ($O(N^3)$ total).
- Unify `matrix.inverse` and `matrix.inv`: delegate `matrix.core.inverse` to `matrix.decompose.inv` (preserving compatibility or deprecating the redundant name with clear documentation).

### 2. Shared Sparse `Field[V]` Elimination Kernel (`src/algebrax/matrix/eliminate.py`)
Promote `variety/affine.py:_sparse_jacobian_pivot_rows` into a first-class sparse elimination module exported from `algebrax.matrix`:

```python
def sparse_rref(
    matrix: SparseMatrix[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> tuple[SparseMatrix[K, V], list[K]]:
    """Compute exact sparse Reduced Row Echelon Form and pivot column list over any Field[V]."""

def rank(
    matrix: SparseMatrix[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> int:
    """Compute exact matrix rank via sparse Field-polymorphic Gaussian elimination."""

def nullspace(
    matrix: SparseMatrix[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> list[SparseVector[K, V]]:
    """Compute an exact basis of ker(A) via sparse RREF over any Field[V]."""
```

- Replace `variety/affine.py:_sparse_jacobian_pivot_rows`, `topology/_core.py:_matrix_rank`, `rep/invariant.py:_rref_row_basis`, and `rep/lie.py:_rref_nullspace` with calls to this shared kernel.
- Thread `tol` (and optional `field: Field[V] | None`) through `CellularSheaf.global_sections_dimension`, `first_cohomology_dimension`, and `SimplicialComplex.betti_numbers` (enabling exact $\mathbb{Q}$ and $\mathbb{F}_p$ homology and torsion detection).

### 3. Core Hot-Path & Topology Performance Fixes
- **`src/algebrax/matrix/core.py`**:
  - Rewrite `inner(v1, v2, semiring)` to iterate directly over the smaller mapping (`if len(v1) > len(v2): v1, v2 = v2, v1`) with $O(\min(\text{nnz}(v_1), \text{nnz}(v_2)))$ lookups and zero set allocations.
  - Pre-normalize `sr` once in `mat_vec` before the row loop.
  - Avoid the extra trailing `dot(base, base, sr)` in `power(matrix, n)` when `n == 1` (`while exp > 0: ... if exp > 0: base = dot(...)`).
  - Use `collections.deque` in `_find_matrix_components`.
- **`src/algebrax/topology/homology.py`**:
  - Reject degenerate simplices with repeated vertices (`len(set(simplex)) != len(simplex)`) in `SimplicialComplex.add_simplex`.
  - Split `_insert_simplex_no_rebuild(s_tuple)` from `add_simplex`, invoking `_rebuild_boundary_matrices()` **once** per top-level `add_simplex` call and **once** at the end of `__init__` (or lazily on access).
- **`src/algebrax/topology/persistence.py`**:
  - Rewrite `_extract_vr_edges` to iterate only over present entries in `distance_matrix` ($O(\text{nnz})$ instead of $O(N^2)$).
  - Replace recursive Hopcroft–Karp `dfs(u)` in `_has_perfect_bipartite_matching` with an explicit iterative DFS stack.

### 4. Graph Calculus & Spectral Correctness (`src/algebrax/analysis/`)
- **`src/algebrax/analysis/calculus.py`**:
  - Fix `gradient` and `laplacian` to respect sparse zero omission (`val_u = field.get(u, 0)`, `val_v = field.get(v, 0)`) over all edges incident to the support of `field`, guaranteeing `laplacian(f, G) == mat_vec(laplacian_matrix(G), f)`.
  - In `fiedler_vector`, replace `queue.pop(0)` + `neighbor in nodes` with `collections.deque`, a `set` of nodes, and an undirected adjacency map built once so BFS matches `laplacian_matrix`'s symmetrization.
- **`src/algebrax/analysis/spectral.py`**:
  - Fix `is_ramanujan_graph` to remove at most **one** trivial $+d$ eigenvalue (and at most one $-d$ eigenvalue if bipartite), so disconnected $d$-regular graphs with repeated $\lambda = d$ correctly return `is_ramanujan = False`.

---

## Backwards Compatibility

- **Additive**: New `matrix.rank`, `matrix.nullspace`, `matrix.sparse_rref` public APIs; optional `field` parameter on topological Betti/cohomology rank helpers.
- **Behavior fixes**:
  - `cholesky` now raises `ValueError` on asymmetric matrices.
  - `SimplicialComplex.add_simplex` raises `ValueError` on degenerate repeated-vertex simplices.
  - `gradient` / `laplacian` now include boundary edges between nonzero and omitted-zero vertices (correct sparse semantics).
  - `is_ramanujan_graph` now returns `False` for disconnected $d$-regular graphs.

---

## How to Teach This / Documentation Plan

- Update [`docs/guide/matrix/decompositions.md`](../guide/matrix/decompositions.md) and [`docs/guide/algebra/exact_matrix_solvers.md`](../guide/algebra/exact_matrix_solvers.md) to showcase `rank`, `nullspace`, `sparse_rref`, and exact $\mathbb{Q}$/$\mathbb{F}_p$ homology.
- Update [`docs/guide/matrix/benchmarks.md`](../guide/matrix/benchmarks.md) with before/after benchmarks for `mat_vec`, `inv`, and `SimplicialComplex` construction.
- Update [`docs/guide/analysis/discrete_calculus.md`](../guide/analysis/discrete_calculus.md) with impulse-response examples verifying `laplacian(f, G) == mat_vec(laplacian_matrix(G), f)`.

---

## Reference Implementation

Existing sparse elimination prototype already proven in production at `src/algebrax/variety/affine.py:57-89` (`_sparse_jacobian_pivot_rows`). Target files:
- `src/algebrax/matrix/{core.py,decompose.py,eliminate.py,__init__.py}`
- `src/algebrax/topology/{_core.py,homology.py,persistence.py,sheaf.py}`
- `src/algebrax/analysis/{calculus.py,spectral.py}`

---

## Rejected Ideas

1. **Always Converting Keys to `int` Internally in `decompose.py`**:
   - *Rejected*: Breaks AlgebraX's key-polymorphic design where matrices may be indexed by strings, simplex tuples `(0, 1)`, or `StalkCoord` tuples. Native `sorted()` with `TypeError` fallback preserves arbitrary hashable keys while fixing integer order for $n \ge 11$.
2. **Rewriting All Decompositions (`qr`, `svd`) to Sparse-Only Format Immediately**:
   - *Rejected*: Householder QR and Jacobi SVD inherently fill in dense orthogonal factors; keeping dense working grids for QR/SVD while providing sparse `Field`-polymorphic `sparse_rref`/`rank`/`nullspace` and $O(N^3)$ LU `inv` gives the highest leverage with minimal complexity.

---

## Open Questions

- [ ] Should `matrix.core.inverse` remain as a deprecated wrapper around `matrix.decompose.inv` for one release cycle or be unified immediately?
- [ ] Should `SimplicialComplex` rebuild boundary matrices lazily via a `_dirty` flag instead of eagerly at the end of top-level `add_simplex`?

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Shannon, Golem, Popper, Explorer, Feynman).
