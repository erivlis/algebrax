---
title: "EP-0254: Ergonomics, State Safety, Ecosystem Bridges & Codebase Hygiene"
description: "Fix defensive boundary and state-aliasing bugs across display, converters, probability, transforms, lattice, and group, and refactor god modules, public exports, and lint hygiene."
icon: lucide/sparkles
status: accepted
---

# EP-0254: Ergonomics, State Safety, Ecosystem Bridges & Codebase Hygiene

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0254                                                                       |
| **Title**         | Ergonomics, State Safety, Ecosystem Bridges & Codebase Hygiene             |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | 💡 Feynman (Clarity), 🌿 Steward (Harmony) & 🛡️ Golem (Safety)              |
| **Status**        | Accepted                                                                   |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-27                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

**Prerequisites**: Runs fifth in Phase 8.5 (`EP-0250` → `EP-0251` → `EP-0252` → `EP-0253` → `EP-0254` → `EP-0255`), consuming `canonical_sort_keys` from `EP-0251` and `make_zero_predicate` from `EP-0252`, splitting `verification/_{algebra,rep}.py` and `tests/verifications/` after `EP-0253` lands, and providing the hardened `display.py` & `RichDisplayable` foundation consumed by `EP-0255`.

---

## Abstract

This proposal addresses codebase-wide safety, ergonomics, ecosystem bridge, and maintainability findings from the Second Grand Council Audit. It fixes HTML-escaping and sentinel bugs in `display.py` (plus a minimal `RichDisplayable` protocol unblocking `EP-0222`), negative-index wraparound and format bugs in `converters.py`, defensive boundary crashes (`ZeroDivisionError`, aliased mutable state on `ExplicitGroupRep`/`ExplicitLieRep` and `markov_step`, non-bijective permutation signatures) in core utilities, and cleans up structural debt: decomposing oversized `verification/` and `tests/verifications/` modules (with automated `docs/verification.md` traceability checks), consolidating duplicated sparse helpers in Layer-1/2 `converters.py`, fixing leaked/incomplete `__all__` exports, cleanly removing redundant `verify_padic_ultrametric`, re-enabling Ruff `F401`, and eliminating all internal `EP-XXXX` references from `src/`. *(Command-line interface hardening in `algebrax.__main__` is owned by [`EP-0255`](EP-0255-unified-algebraic-structure-registry-and-cli.md) alongside the unified structure registry.)*

---

## Motivation

While AlgebraX's mathematical breadth has grown to 111 modules and 36.6k LOC, peripheral ergonomics, defensive boundaries, and structural hygiene have accumulated friction that hurts both newcomers (the Freshman Test) and long-term maintainers:

1. **Rich Display Escaping, Sentinel & Protocol Gaps**:
   - `display.py` interpolates titles, keys, and values into raw HTML without `html.escape` (broken rendering / XSS in Jupyter), uses `''` as a missing-cell sentinel (hiding genuine empty-string `''` entries in string-valued matrices), and lacks a formal `RichDisplayable` protocol needed by Phase 9 (`EP-0222`). *(CLI catalog/verify/inspect gaps in `algebrax.__main__` are addressed holistically in [`EP-0255`](EP-0255-unified-algebraic-structure-registry-and-cli.md) on top of the unified structure registry.)*
2. **Ecosystem Bridge & Defensive Boundary Bugs**:
   - `converters.to_numpy` omits `r >= 0 and c >= 0` (silently wrapping negative keys via NumPy indexing), calls `max(matrix.keys())` even when `shape` is provided, and silently drops non-`int` keys with no index-map option; `from_numpy` raises `ValueError` instead of `TypeError` for non-`np.ndarray` inputs; `to_scipy` ignores `format` on empty matrices and lacks symmetric non-int/negative key validation; `from_scipy` has an unused `import scipy.sparse as sp`, and `_get_shape` has a dead `current_depth` parameter.
   - `analysis.calculus.laplacian_smoothing` uses an implicit `any(w < 0 ...)` heuristic to guess whether `graph` is already a Laplacian—silently corrupting signed adjacency matrices.
   - Aliased mutable state leaks from `probability.markov_step(steps=0)`, `ExplicitGroupRep.__call__`, and `ExplicitLieRep`.
   - Unhandled `ZeroDivisionError` / silent corruption in `group.permutation.signature` (non-bijection `{0: 1, 1: 1}` returns `-1` and formats `"broken cycle at None"`), `lattice.harmonic_mean` (`a == -b`), `lattice.join` (wiping negative values via `max(v, 0)`), `lattice.product` (union scan when `default == 0`), `transforms.dft`/`idft` (`n <= 0` / negative keys), `transforms.lorentz_boost(axis=0)`, and `probability.bayes_update` (`evidence <= 0`) / `entropy`/`cross_entropy`/`kl_divergence`/`mutual_information` (`base == 1` or negative probabilities).
3. **Maintainability, Export & Lint Hygiene**:
   - `verification/_algebra.py` (1,767 lines) and `verification/_rep.py` (1,107 lines) are monolithic; 3 identical sparse-matrix equality helpers sit in `verification/_rep.py` (plus duplicates in `rep/lie.py` and `rep/quiver.py`); 5 ad-hoc sparse zero-pruning helpers use 5 different tolerances (`1e-9` to `1e-15`).
   - `tests/verifications/` has grown to 6,708 lines across 12 flat files, with 60.5% (4,059 lines) concentrated in oracle-grouped `test_differential_*.py` monoliths—most acutely `test_differential_sympy.py` (1,569 lines across 7 unrelated domains), `test_differential_topology_prob.py` (809 lines), `test_differential_numpy.py` (768 lines), and `test_differential_graphs.py` (672 lines)—plus `test_mms_sheaves_and_categories.py` (646 lines), while hard top-level imports of `numpy`/`scipy`/`sympy` bypass `conftest.py`'s optional-dependency skip guards.
   - `analysis/__init__.py` leaks private `_get_common_neighbors` and `_is_graph_weighted` in `__all__`; `analysis/calculus.py` re-exports `topology` helpers; `matrix/__init__.py` omits `block`, `hstack`, `vstack`, `slice_matrix`, `element_wise_binary_op`; `converters.py` docstring omits 10 of 18 exported functions.
   - `pyproject.toml:165` globally suppresses `F401`, hiding unused imports across `semiring/algebraic.py`, `converters.py`, and `verification/_algebra.py`; `verify_padic_ultrametric` duplicates `verify_padic_ultrametric_inequality`.
   - 14 internal `EP-XXXX` references leak into `src/` docstrings across 13 files, violating EP non-leakage rules.

---

## Rationale

- **💡 Richard Feynman (Clarity & Freshman Test)**: Error messages, Jupyter HTML tables, and exception types fail loudly, clearly, and predictably—with clean cuts and zero dead aliases.
- **🛡️ The Golem (Safety & State Gravity)**: Freeze internal matrix dicts once at construction via `types.MappingProxyType` (zero per-call copy overhead, protecting `EP-0230`'s inner loops) and eliminate implicit negative-weight heuristics and negative-index wraparound.
- **🌿 The Steward (Harmony & Layering)**: Consolidating shared sparse-equality and zero-pruning utilities inside Layer-1/2 `converters.py` (never `verification/_common.py`) preserves clean downward dependencies across `rep/`, `matrix/`, and `verification/`.

---

## Specification

### 1. Rich Display Hardening & Protocol (`display.py`)
- **`src/algebrax/display.py`**:
  - Escape all rendered text via `html.escape` across `display_matrix`, `display_vector`, `display_trie`, and `semiring_card`.
  - Replace the `''` missing-cell sentinel with a private `_MISSING = object()` sentinel so genuine empty-string `''` entries render accurately.
  - Define and export a minimal 2-method protocol in `algebrax.display.__all__` (unblocking Phase 9 `EP-0222` without importing `display` from Layer-2 `algebra/` or retrofitting legacy classes):
    ```python
    @runtime_checkable
    class RichDisplayable(Protocol):
        """Structural protocol for objects supporting Jupyter HTML and LaTeX display."""
        def _repr_html_(self) -> str: ...
        def _repr_latex_(self) -> str: ...
    ```
- *(CLI hardening for `src/algebrax/__main__.py` — including parameterized `--semiring` errors, dynamic catalog domains, version unification, and full `verify --all` coverage — has been moved to [`EP-0255`](EP-0255-unified-algebraic-structure-registry-and-cli.md) so `__main__.py` is rewritten once against the unified structure registry.)*

### 2. Converters & Defensive Utility Boundaries
- **`src/algebrax/converters.py`**:
  - In `to_numpy`: enforce `not isinstance(r, bool) and isinstance(r, int) and 0 <= r < h` (and same for `c`), skip `max(matrix.keys())` when `shape` is explicitly supplied, and add optional `return_keys: bool = False` for key-polymorphic sparse matrices (`str`, simplex tuples, `StalkCoord`).
  - In `from_numpy`: raise `TypeError` strictly when `not isinstance(arr, np.ndarray)` (preserving `ValueError` for `arr.ndim != 2`).
  - In `to_scipy`: honor the requested `format` (`csr`, `csc`, `coo`, etc.) even when `matrix` is empty, and add symmetric non-int/negative key validation and `return_keys: bool = False` parity with `to_numpy`.
  - Remove unused `import scipy.sparse as sp` in `from_scipy`, remove dead `current_depth` parameter in `_get_shape`, and document all 18 exported converter functions in `converters.py`'s module docstring.
- **`src/algebrax/analysis/calculus.py`**:
  - Replace `laplacian_smoothing`'s negative-weight heuristic (`any(w < 0 ...)`) with an explicit `is_laplacian: bool = False` keyword argument.
- **State Gravity / Immutability**:
  - Return a fresh shallow copy `dict(state)` on 0-step calls in `probability.markov_step` and validate `steps >= 0` (`ValueError` for negative `steps`). *(Zero-step `automata.simulate_nfa` copy and `SparseChainComplex.__init__` copy land in `EP-0252`.)*
  - Freeze internal matrix dicts once in `__post_init__` via nested `types.MappingProxyType` on **both** `ExplicitGroupRep` (`rep/group.py`) and `ExplicitLieRep` (`rep/lie.py`) for $O(1)$ zero-copy immutability (`EP-0253` widens `verification/_common.py:45` to `Mapping`).
- **Boundary Guards & Regression Tests** *(owning the boundary tests relocated from `EP-0253`)*:
  - `group/permutation.py`: validate bijectivity (`set(mapping.keys()) == set(mapping.values())`, raising `ValueError`) and capture `prev = curr` before `mapping.get(curr)` in `signature`.
  - `lattice.py`: guard `a + b == 0` (`ValueError`) in `harmonic_mean`; preserve single-side negative values in `join`; use `set.intersection` when `default == 0` in `product`, `geometric_mean`, and `harmonic_mean`; raise `ValueError` for opposite-sign real inputs in `geometric_mean`.
  - `transforms.py`: validate `n > 0` and non-negative integer signal indices in `dft`/`idft`/`deconvolve`; validate `isinstance(axis, int) and not isinstance(axis, bool) and axis >= 1` in `lorentz_boost` (preserving $D$-vector boosts for `axis >= 4` while rejecting `axis == 0` and `bool`).
  - `probability.py`: validate `base > 0 and base != 1` and non-negative probabilities in `entropy`, `cross_entropy`, `kl_divergence`, and `mutual_information`; in `bayes_update`, raise `ValueError` when explicit `evidence <= 0` while returning `{}` for disjoint support when `evidence is None`.

### 3. Module Decomposition, Shared Utilities & Public Hygiene
- **Canonical Layer-1/2 Sparse Utilities (`src/algebrax/converters.py`)**:
  - Consolidate the 5 ad-hoc zero-pruning helpers (`prune_sparse`, `vec_clean`, `_prune_matrix`, `_is_non_zero`, `_prune_vector`) behind one shared helper in `converters.py` using hoisted `make_zero_predicate` (`EP-0252`)—never calling `isinstance(..., HasZeroPred)` inside inner loops.
  - Consolidate the duplicated sparse-matrix equality helpers (`verification/_rep.py`, `rep/lie.py`, `rep/quiver.py`) into `converters.py` (`sparse_matrices_equal`) so `rep/` and `verification/` both depend downward on Layer-1/2 `converters.py` with zero circular imports.
- **Firm God-Module Decomposition Decisions (Zero Breaking Public Imports)**:
  - Split `verification/_algebra.py` into focused internal submodules (`_magma_group.py`, `_ring_field.py`, `_hopf_normed.py`, `_groebner.py`) re-exported identically via `verification/__init__.py`.
  - Split `verification/_rep.py` into `_rep_group_lie.py` and `_rep_quantum_quiver.py` re-exported via `verification/__init__.py`.
  - Remove `topology` re-exports from `analysis/calculus.py` cleanly (shrinking `calculus.py` without breaking `analysis/__init__.py`).
  - **Defer** splitting `matrix/core.py` (high cross-function coupling, no user benefit in Phase 8.5).
- **`tests/verifications/` Namespace Decomposition & Traceability Hygiene** *(lands after `EP-0253`)*:
  - Reorganize the 5 oracle-grouped `test_differential_*.py` files into a domain-scoped `tests/verifications/differential/` sub-package with shared `differential/_helpers.py` (consolidating sparse/dense and SymPy polynomial adapters) and standardized module-level `pytest.importorskip(...)` guards:
    - `differential/test_linalg_and_tensors.py` (from `test_differential_numpy.py`: core matrix algebra, solvers, decompositions, tensors, converters, norms & RKHS)
    - `differential/test_transforms.py` (from `test_differential_numpy.py`: DFT/IDFT, Hilbert, convolution, Walsh–Hadamard, Z-transform, Gelfand/Legendre–Fenchel, Lorentz boost)
    - `differential/test_path_semirings.py` (from `test_differential_graphs.py`: Tropical, Boolean, Arctic, Bottleneck, Viterbi/Reliability, Log DAG closures & Hypothesis APSP)
    - `differential/test_spectral_graphs.py` (from `test_differential_graphs.py`: Laplacians, spectrum, Fiedler/algebraic connectivity, bipartition, PageRank, eigen-centrality, discrete calculus, Forman–Ricci)
    - `differential/test_statistical_semirings.py` (relocated from `test_differential_statistical_semirings.py`)
    - `differential/test_lie_galois_and_clifford.py` (from `test_differential_sympy.py`: exact `Fraction` matrices, Lie/RootSystems/BCH/Killing, Galois fields, Clifford/octonions/Jordan, finite groups & permutations)
    - `differential/test_representations.py` (from `test_differential_sympy.py`: group representations/character tables, Clebsch–Gordan/Lie `expm`, Molien/Casimir, quantum $U_q(\mathfrak{sl}_2)$/Jones, quivers/Gabriel ADE)
    - `differential/test_polynomials_and_varieties.py` (from `test_differential_sympy.py`: univariate polynomials, autodiff semirings, Gröbner bases, affine varieties)
    - `differential/test_topology.py` (from `test_differential_topology_prob.py`: simplicial homology, Discrete Hodge, DEC/Stokes, Helmholtz–Hodge, persistent homology, cohomology cup/cap)
    - `differential/test_probability_and_discrete.py` (from `test_differential_topology_prob.py`: information theory, moments, Bayes/Markov, automata, fractal metrics)
  - Split `test_mms_sheaves_and_categories.py` (646 lines) into a `tests/verifications/mms/` sub-package:
    - `mms/test_sheaves_and_geometry.py` (cellular sheaves, harmonic extensions, connections/holonomy, Alexander–Whitney, K-theory/Chern, Langlands/$p$-adic)
    - `mms/test_categories_and_algebra.py` (Kleisli/Kan, distributive lattices, algebraic tries, matrix category/Lawvere, quotient ring isomorphism, path groupoids/CCC)
  - Keep cohesive `< 470`-line methodology modules intact at top level (`test_axiomatic_properties.py`, `test_metamorphic_invariants.py`, `test_pit_symbolic.py`, `test_certificates.py`, `test_smt_z3_proofs.py`) alongside recursive `tests/verifications/conftest.py`.
  - Synchronize all 138 `*.py::test_*` traceability references in [`docs/verification.md`](../verification.md) and the directory tree in [`EP-0003`](EP-0003-axiomatic-verification-and-property-based-testing.md), and add a fast CI test asserting every `*.py::test_*` entry in `docs/verification.md` resolves to an existing test function under `tests/verifications/`.
- **Public Exports & Exception Consistency**:
  - Remove `_get_common_neighbors` and `_is_graph_weighted` from `analysis/__init__.__all__`.
  - Align `matrix/__init__.__all__` with `matrix/core.py:__all__` (adding `block`, `hstack`, `vstack`, `slice_matrix`, `element_wise_binary_op`, adding `cg_solve` to `core.__all__`).
  - **Keep `KeyError`** on `Semiring.normalize('bad')` (catalog lookup semantics); normalize `rep/quiver.py` invalid vertex/edge validation on `ValueError`.
- **Lint, Clean Removal & EP Non-Leakage Hygiene**:
  - Remove global `F401` from `pyproject.toml:165`, scoping `per-file-ignores = {"**/__init__.py" = ["F401"]}`, and prune all dead imports (`semiring/algebraic.py`, `converters.py`, `verification/_algebra.py`).
  - **Clean Cut**: Remove redundant alias `verify_padic_ultrametric` from `verification/__init__.py` and update `tests/algebrax/test_langlands_and_padic.py:253` to `verify_padic_ultrametric_inequality`.
  - Strip all 14 `EP-XXXX` references from `src/` docstrings across 13 files (verifying AMDS `_SIG_RE` extraction stays green in `test_docstrings.py`) and add a CI test asserting zero `EP-\d{4}` matches anywhere in `src/`.

---

## Acceptance Criteria

1. `display_matrix` escapes `<script>` HTML payloads and distinguishes `''` entries from `_MISSING` cells; `isinstance(obj, RichDisplayable)` works for objects implementing `_repr_html_` and `_repr_latex_`.
2. `to_numpy` and `to_scipy` reject negative/`bool` keys, support `return_keys=True` for string/tuple keys, and honor `format` on empty matrices; `from_numpy(non_ndarray)` raises `TypeError` while `from_numpy(np.array([1, 2]))` raises `ValueError`.
3. `ExplicitGroupRep` and `ExplicitLieRep` raise `TypeError` on external mutation of returned matrices without per-call deep copies; `markov_step(state, P, steps=0)` returns a non-aliased copy and rejects `steps < 0`.
4. Boundary regression tests pass for `transforms` (`n <= 0`, `lorentz_boost(axis=0)` raises `ValueError`, `lorentz_boost(axis=4)` succeeds), `probability` (`base=1`, negative probabilities, `mutual_information`, `bayes_update(..., evidence=0)`), `lattice` (`harmonic_mean(1, -1)`, negative `join`, `default=0` `product`), and `group.permutation.signature` (non-bijections).
5. `rep/` contains zero imports from `verification/`; `verification/_algebra.py` and `verification/_rep.py` are cleanly decomposed while all existing `algebrax.verification` public exports (minus cleanly removed `verify_padic_ultrametric`) remain intact.
6. `tests/verifications/` is cleanly organized into `differential/` (10 domain modules + `_helpers.py`) and `mms/` (2 modules) with module-level `pytest.importorskip(...)` guards; `uv run pytest tests/verifications/ -m differential` and `-m mms` collect and pass all existing verification tests with zero test loss; `docs/verification.md` and `EP-0003` are synchronized, and the CI traceability test confirms 100% of `*.py::test_*` references in `docs/verification.md` resolve to live test functions.
7. `ruff check .` passes with `F401` enabled globally (except `**/__init__.py`), `tests/algebrax/test_docstrings.py` passes, and the new CI test confirms zero `EP-\d{4}` occurrences in `src/`.

---

## Backwards Compatibility

- **Module splits are non-breaking**: All public symbols remain importable from `algebrax.verification`, `algebrax.matrix`, and `algebrax.analysis`.
- **Verification suite commands remain unchanged**: `pytest tests/verifications/` and marker selections (`-m differential`, `-m mms`, etc.) behave identically; only direct file-path invocations referencing legacy monoliths (e.g., `tests/verifications/test_differential_sympy.py`) move to their new domain paths under `tests/verifications/{differential,mms}/`.
- **Intentional clean cuts & bug fixes**:
  - `verify_padic_ultrametric` is cleanly removed; use `verify_padic_ultrametric_inequality`.
  - `analysis.__all__` no longer exports private `_get_common_neighbors` and `_is_graph_weighted`.
  - `laplacian_smoothing` requires explicit `is_laplacian=True` when passing a precomputed Laplacian.
  - `from_numpy(non_ndarray)` raises `TypeError` instead of `ValueError`.
  - `group.permutation.signature` raises `ValueError` on non-bijective mappings; `bayes_update(..., evidence=0)` raises `ValueError`; `lorentz_boost(axis=0)` raises `ValueError`.
  - `ExplicitGroupRep` and `ExplicitLieRep` return read-only `MappingProxyType` matrix views.

---

## How to Teach This / Documentation Plan

- Ensure `RichDisplayable` and updated converter/display utilities pass `tests/algebrax/test_docstrings.py` (with zero `EP-XXXX` leaks in `src/`).
- Update [`docs/guide/matrix/core.md`](../guide/matrix/core.md) (converter & `to_numpy`/`to_scipy` `return_keys` docs) and [`docs/guide/analysis/discrete_calculus.md`](../guide/analysis/discrete_calculus.md) (`laplacian_smoothing(..., is_laplacian=...)`).
- Update [`docs/guide/probability/information.md`](../guide/probability/information.md), [`docs/guide/transforms/spectral.md`](../guide/transforms/spectral.md), and [`docs/guide/algebra/lattices_and_order.md`](../guide/algebra/lattices_and_order.md) with boundary precondition notes.
- Synchronize all 138 traceability paths in [`docs/verification.md`](../verification.md) and the suite layout tree in [`EP-0003`](EP-0003-axiomatic-verification-and-property-based-testing.md) to reflect `tests/verifications/differential/` and `tests/verifications/mms/`.

---

## Reference Implementation

Target files verified in the Second Grand Council Audit & Review:
- `src/algebrax/{display.py,converters.py,lattice.py,transforms.py,probability.py}`
- `src/algebrax/group/permutation.py`, `src/algebrax/rep/{group.py,lie.py,quiver.py}`
- `src/algebrax/analysis/{__init__.py,calculus.py}`, `src/algebrax/matrix/{__init__.py,core.py}`
- `src/algebrax/verification/{_common.py,_algebra.py,_rep.py,_topology.py,__init__.py}`
- `tests/verifications/` (`differential/`, `mms/`, `conftest.py`), `docs/verification.md`, and `docs/proposals/EP-0003-axiomatic-verification-and-property-based-testing.md`
- `pyproject.toml` and the 13 `src/` files containing `EP-\d{4}` references.

---

## Rejected Ideas

1. **Consolidating `rep/` Sparse Equality Into `verification/_common.py`**:
   - *Rejected*: Creates a circular dependency because `verification/` imports `rep/`. Layer-1/2 `converters.py` is the proper home.
2. **Deep-Copying `ExplicitGroupRep` Matrices on Every `__call__`**:
   - *Rejected*: Allocates $O(|G|^2)$ dict copies in representation/Fourier hot loops (`EP-0230`). Construction-time `MappingProxyType` provides zero-overhead immutability.
3. **Changing `Semiring.normalize('bad')` From `KeyError` to `ValueError`**:
   - *Rejected*: `Semiring.normalize` is a catalog mapping lookup; `KeyError` already obeys Pythonic exception semantics.
4. **Splitting `matrix/core.py` in Phase 8.5**:
   - *Rejected*: High cross-function coupling with negligible user benefit during a hardening phase.
5. **Over-Splitting Cohesive `< 470`-Line Verification Files or Grouping All Verification Tests Strictly by Domain**:
   - *Rejected*: Splitting `test_axiomatic_properties.py`, `test_metamorphic_invariants.py`, `test_pit_symbolic.py`, `test_certificates.py`, or `test_smt_z3_proofs.py` adds boilerplate without reducing cognitive load, while replacing methodology-level grouping with pure domain directories mixes Z3/Hypothesis/SymPy imports and obscures the 8-layer verification architecture (`EP-0003`).

---

## Open Questions

None. All Council review items (`bayes_update`, `Semiring.normalize`, `RichDisplayable`, god-module split scope, `tests/verifications/` decomposition, `verify_padic_ultrametric` clean removal, and `converters.py` utility placement) are resolved.

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Feynman, Steward, Golem, Shannon, Popper, Explorer).
* **2026-11-27:**
  * Incorporated Grand Council Pre-Implementation Review revisions: declared Phase 8.5 sequencing prerequisites, moved sparse-equality/zero-pruning consolidation to `converters.py` (preventing circular `rep/`→`verification/` imports), formalized minimal `RichDisplayable` protocol for `EP-0222`, specified `MappingProxyType` immutability on `ExplicitGroupRep` & `ExplicitLieRep`, fixed `lorentz_boost` (`axis >= 1`), added `mutual_information` and `markov_step(steps < 0)` guards, added `to_scipy` parity, fixed CLI/display/`from_scipy`/doc-link inaccuracies, kept `KeyError` on `Semiring.normalize`, cleanly removed `verify_padic_ultrametric`, finalized god-module split scope, absorbed boundary regression tests from `EP-0253`, added Acceptance Criteria, and promoted status to `Accepted`.
  * Added `tests/verifications/` namespace refactoring to `§3`: decompose oracle-grouped differential monoliths into `tests/verifications/differential/` (10 domain modules + `_helpers.py` with `pytest.importorskip` guards) and `test_mms_sheaves_and_categories.py` into `tests/verifications/mms/` (2 modules), synchronize `docs/verification.md` & `EP-0003`, and add a CI traceability verification test.
  * Cleanly handed off `src/algebrax/__main__.py` CLI hardening and `_registry` consumption to [`EP-0255`](EP-0255-unified-algebraic-structure-registry-and-cli.md) per Grand Council review, sequencing `EP-0254` → `EP-0255`.
