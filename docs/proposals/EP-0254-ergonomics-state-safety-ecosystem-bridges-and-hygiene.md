---
title: "EP-0254: Ergonomics, State Safety, Ecosystem Bridges & Codebase Hygiene"
description: "Fix defensive boundary and state-aliasing bugs across CLI, display, converters, probability, transforms, lattice, and group, and refactor god modules, public exports, and lint hygiene."
icon: lucide/sparkles
status: draft
---

# EP-0254: Ergonomics, State Safety, Ecosystem Bridges & Codebase Hygiene

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0254                                                                       |
| **Title**         | Ergonomics, State Safety, Ecosystem Bridges & Codebase Hygiene             |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | 💡 Feynman (Clarity), 🌿 Steward (Harmony) & 🛡️ Golem (Safety)              |
| **Status**        | Draft                                                                      |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-26                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal addresses codebase-wide safety, ergonomics, ecosystem bridge, and maintainability findings from the Second Grand Council Audit. It fixes silent CLI fallbacks, HTML-escaping and sentinel bugs in `display.py`, negative-index wraparound and format bugs in `converters.py`, defensive boundary crashes (`ZeroDivisionError`, aliased mutable returns, non-bijective permutation signatures) in core utilities, and cleans up structural debt: decomposing 1,000+ line god modules, unifying duplicated sparse helpers, fixing leaked/incomplete `__all__` exports, removing global `F401` lint suppression, and eliminating all internal `EP-XXXX` references from `src/`.

---

## Motivation

While AlgebraX's mathematical breadth has grown to 111 modules and 36.6k LOC, peripheral ergonomics, defensive boundaries, and structural hygiene have accumulated friction that hurts both newcomers (the Freshman Test) and long-term maintainers:

1. **Silent CLI & Display Failures**:
   - `algebrax.__main__` silently catches exceptions when instantiating parameterized `--semiring` flags (`Modular`, `GaloisField`, `Clifford`, `Polynomial`), silently falling back to `StandardSemiring`; carries a stale `'0.8.0'` fallback version; misclassifies `String`/`KCollapsed` under `'logic'`; and only verifies 12 of 33 semirings in `cmd_verify --all`.
   - `display.py` interpolates titles, keys, and values into raw HTML without `html.escape` (broken rendering / XSS in Jupyter), uses `''` as a missing-cell sentinel (hiding genuine `''` entries like `StringSemiring.one`), and covers only matrices/vectors/tries/semirings.
2. **Ecosystem Bridge & Defensive Boundary Bugs**:
   - `converters.to_numpy` omits `r >= 0 and c >= 0` (silently wrapping negative keys via NumPy indexing) and silently drops non-`int` keys with no index-map option; `from_numpy` raises `ValueError` instead of `TypeError`; `to_scipy` ignores `format` on empty matrices.
   - `analysis.calculus.laplacian_smoothing` uses an implicit `any(w < 0 ...)` heuristic to guess whether `graph` is already a Laplacian—silently corrupting signed adjacency matrices.
   - Aliased mutable state leaks from `probability.markov_step(steps=0)`, `automata.simulate_nfa([])`, `SparseChainComplex.__init__`, and `ExplicitGroupRep.__call__`.
   - Unhandled `ZeroDivisionError` / silent corruption in `group.permutation.signature` (non-bijection `{0: 1, 1: 1}` returns `-1` and formats `"broken cycle at None"`), `lattice.harmonic_mean` (`a == -b`), `lattice.join` (wiping negative values via `max(v, 0)`), `lattice.product` (union scan when `default == 0`), `transforms.dft`/`idft` (`n <= 0` / negative keys), `transforms.lorentz_boost(axis=0)`, and `probability.bayes_update` (`evidence == 0`) / `entropy` (`base == 1`).
3. **Maintainability, Export & Lint Hygiene**:
   - Four god modules exceed 1,000 lines (`verification/_algebra.py` 1,767 lines, `verification/_rep.py` 1,107 lines, `matrix/core.py` 1,095 lines, `analysis/calculus.py` 1,029 lines), with 3 identical sparse-matrix equality helpers in `verification/_rep.py`, 5 ad-hoc sparse zero-pruning helpers with 5 different tolerances (`1e-9` to `1e-15`), and 12 cross-package private `_` imports.
   - `analysis/__init__.py` leaks private `_get_common_neighbors` and `_is_graph_weighted` in `__all__`; `matrix/__init__.py` omits `block`, `hstack`, `vstack`, `slice_matrix`, `element_wise_binary_op`; `converters.py` docstring omits 10 of 18 exported functions.
   - `pyproject.toml:165` globally suppresses `F401`, hiding unused imports and dead parameters across `semiring/algebraic.py`, `converters.py`, and `verification/_algebra.py`.
   - 14 internal `EP-XXXX` references leak into `src/` docstrings across 13 files, violating EP non-leakage rules.

---

## Rationale

- **💡 Richard Feynman (Clarity & Freshman Test)**: Error messages, CLI commands, Jupyter HTML tables, and exception types (`TypeError` vs `ValueError` vs `KeyError`) should fail loudly, clearly, and predictably—never silently falling back or rendering broken HTML.
- **🛡️ The Golem (Safety & State Gravity)**: Never return aliased caller dicts or expose mutable internal state on `frozen=True` dataclasses; never rely on implicit negative-weight heuristics or negative-index wraparound.
- **🌿 The Steward (Harmony & Maintainability)**: Splitting monolithic files along natural domain seams, consolidating duplicated helpers, and re-enabling Ruff `F401` keeps the codebase clean and refactorable before Phase 10–11 expansion.

---

## Specification

### 1. CLI & Rich Display Hardening (`__main__.py`, `display.py`)
- **`src/algebrax/__main__.py`**:
  - On `--semiring` instantiation failure (e.g., required constructor parameters), print a clear message to `stderr` explaining the required parameters and return exit code `1` (never silently fall back to `StandardSemiring`).
  - Reuse `algebrax.__version__` directly (remove stale `'0.8.0'` fallback).
  - Derive catalog domain tags and `cmd_verify --all` coverage dynamically from the semiring registry instead of hardcoded partial lists.
- **`src/algebrax/display.py`**:
  - Escape all rendered text via `html.escape` across `display_matrix`, `display_vector`, `display_trie`, and `semiring_card`.
  - Replace the `''` missing-cell sentinel with a private `_MISSING = object()` sentinel so genuine empty strings (e.g., `StringSemiring.one`) render accurately.
  - Introduce a lightweight `RichDisplayable` protocol (`_repr_html_` / `_repr_latex_`) to extend rich Jupyter inspection cleanly to newer domain carriers (`CharacterTable`, `PersistenceInterval`, `AffineVariety`, `FiniteGroup`, `Quiver`, `RootSystem`).

### 2. Converters & Defensive Utility Boundaries
- **`src/algebrax/converters.py`**:
  - In `to_numpy`: enforce `not isinstance(r, bool) and isinstance(r, int) and 0 <= r < h` (and same for `c`), fix string-key `max()` crash, and add an optional `return_keys: bool = False` (or key-index-map helper) for key-polymorphic sparse matrices (`str`, simplex tuples, `StalkCoord`).
  - In `from_numpy`: raise `TypeError` when input is not an `np.ndarray`.
  - In `to_scipy`: honor the requested `format` (`csr`, `csc`, `coo`, etc.) even when `matrix` is empty; remove unused `sp` import and dead `current_depth` parameter in `_get_shape`.
- **`src/algebrax/analysis/calculus.py`**:
  - Replace `laplacian_smoothing`'s negative-weight heuristic (`any(w < 0 ...)`) with an explicit `is_laplacian: bool = False` keyword argument.
- **State Gravity / Immutability**:
  - Return fresh shallow copies (`dict(state)` / `dict(start_states)`) on 0-step calls in `probability.markov_step` and `automata.simulate_nfa`; copy `boundary_matrices` in `SparseChainComplex.__init__`; protect internal matrix dicts in `ExplicitGroupRep`.
- **Boundary Guards**:
  - `group/permutation.py`: validate bijectivity (`set(mapping.keys()) == set(mapping.values())`) and capture `prev = curr` before `mapping.get(curr)` in `signature`.
  - `lattice.py`: guard `a + b == 0` in `harmonic_mean`; preserve single-side negative values in `join`; use `set.intersection` when `default == 0` in `product`, `geometric_mean`, and `harmonic_mean`; reject opposite-sign real inputs cleanly in `geometric_mean` (or document complex promotion).
  - `transforms.py`: validate `n > 0` and non-negative signal indices in `dft`/`idft`/`deconvolve`; validate `axis in (1, 2, 3)` in `lorentz_boost`.
  - `probability.py`: validate `base > 0 and base != 1` and non-negative probabilities in `entropy`/`cross_entropy`/`kl_divergence`; guard `evidence == 0` in `bayes_update` with a clear `ValueError` (or empty posterior per contract).

### 3. Module Decomposition, Shared Utilities & Public Hygiene
- **Canonical Sparse Utilities**:
  - Consolidate the 5 ad-hoc zero-pruning helpers (`prune_sparse`, `vec_clean`, `_prune_matrix`, `_is_non_zero`, `_prune_vector`) behind one `is_zero`-aware utility honoring `HasZeroPred` when a `Field`/`Semiring` is provided.
  - Consolidate the 3 identical sparse-matrix equality helpers in `verification/_rep.py` (plus duplicates in `rep/lie.py` and `rep/quiver.py`) into `verification/_common.py`.
- **God-Module Decomposition (Zero Breaking Public Imports)**:
  - Split `verification/_algebra.py` into focused internal submodules (`_magma_group.py`, `_ring_field.py`, `_hopf_normed.py`, `_groebner.py`) re-exported identically via `verification/__init__.py`.
  - Split `verification/_rep.py` into `_rep_group_lie.py` and `_rep_quantum_quiver.py`.
  - Consider splitting `matrix/core.py` into `_ops.py`, `_vector.py`, and `_solvers.py` (re-exported via `matrix/core.py` and `matrix/__init__.py`), and `analysis/calculus.py` into discrete calculus vs. spectral graph helpers.
- **Public Exports & Exception Consistency**:
  - Remove `_get_common_neighbors` and `_is_graph_weighted` from `analysis/__init__.__all__`; move `topology` re-exports out of `analysis/calculus.py` into `analysis/__init__.py` (or deprecate redundant re-exports).
  - Align `matrix/__init__.__all__` with `matrix/core.py:__all__` (adding `block`, `hstack`, `vstack`, `slice_matrix`, `element_wise_binary_op` and adding `cg_solve` to `core.__all__`).
  - Standardize invalid-name/value errors on `ValueError` (e.g., `Semiring.normalize('bad')` and `rep/quiver.py` vertex/edge validation) while reserving `KeyError` for mapping lookups and `TypeError` for wrong types.
- **Lint & EP Non-Leakage Hygiene**:
  - Remove global `F401` from `pyproject.toml:165` (use `per-file-ignores` only for `__init__.py` re-exports) and prune all dead imports (`semiring/algebraic.py`, `converters.py`, `verification/_algebra.py`) and redundant aliases (`verify_padic_ultrametric`).
  - Strip all 14 `EP-XXXX` references from `src/` docstrings across 13 files and add a CI/test check enforcing zero `EP-\d{4}` matches in `src/`.

---

## Backwards Compatibility

- **Module splits are strictly non-breaking**: All public symbols remain importable from their existing public packages (`algebrax.verification`, `algebrax.matrix`, `algebrax.analysis`).
- **Minor behavior changes (bug fixes)**:
  - `analysis.__all__` no longer exports private `_get_common_neighbors` and `_is_graph_weighted`.
  - `python -m algebrax inspect --semiring Modular` exits with code `1` instead of silently computing with `StandardSemiring`.
  - `laplacian_smoothing` requires explicit `is_laplacian=True` when passing a precomputed Laplacian rather than relying on negative edge weights.
  - `from_numpy(non_ndarray)` raises `TypeError` instead of `ValueError`.
  - `group.permutation.signature` raises `ValueError` on non-bijective mappings.

---

## How to Teach This / Documentation Plan

- Update [`docs/guide/matrix/core.md`](../guide/matrix/core.md) and [`docs/guide/analysis/discrete_calculus.md`](../guide/analysis/discrete_calculus.md) for `laplacian_smoothing(..., is_laplacian=...)` and key-preserving `to_numpy`.
- Update [`docs/converters.md`](../guide/matrix/core.md) / converter docstrings so all 18 exported converter functions are documented accurately.

---

## Reference Implementation

Target files verified in the Second Grand Council Audit:
- `src/algebrax/{__main__.py,display.py,converters.py,lattice.py,transforms.py,probability.py,automata.py}`
- `src/algebrax/group/permutation.py`, `src/algebrax/analysis/{__init__.py,calculus.py}`, `src/algebrax/matrix/{__init__.py,core.py}`
- `src/algebrax/verification/{_common.py,_algebra.py,_rep.py,_topology.py,__init__.py}`
- `pyproject.toml` and the 13 `src/` files containing `EP-\d{4}` references.

---

## Rejected Ideas

1. **Auto-Parsing Arbitrary Constructor Args in CLI `--semiring "Modular(7)"` via `eval()`**:
   - *Rejected*: Severe security hazard (arbitrary code execution) violating Golem's Safety pillar. Explicit safe parsing (or clear error message for parameterized semirings) is strictly safer.
2. **Keeping Global `F401` Disabled to Avoid Updating `__init__.py`**:
   - *Rejected*: Ruff's `per-file-ignores = {"**/__init__.py" = ["F401"]}` cleanly supports package re-exports while catching real dead imports in every implementation file.

---

## Open Questions

- [ ] Should `probability.bayes_update` return `{}` or raise `ValueError` when total `evidence == 0` (disjoint prior and likelihood)?
- [ ] Should `Semiring.normalize('unknown')` change from `KeyError` to `ValueError` in this EP (check existing tests expecting `KeyError`)?

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Feynman, Steward, Golem, Shannon, Popper, Explorer).
