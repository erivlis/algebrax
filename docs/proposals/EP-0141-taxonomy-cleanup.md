---
title: "EP-0141: Structural Taxonomy Cleanup"
description: "Resolves module misplacements and import redundancies to enforce clean set-theoretic non-overlap."
icon: lucide/folder-tree
status: final
---

# EP-0141: Structural Taxonomy Cleanup

| Field       | Value                          |
|:------------|:-------------------------------|
| **EP**      | 0141                           |
| **Title**   | Structural Taxonomy Cleanup    |
| **Author**  | Eran Rivlis & Antigravity      |
| **Status**  | Final                          |
| **Type**    | Standards Track                |
| **Created** | 2026-08-02                     |
| **Updated** | 2026-08-05                     |

## Abstract

The Grand Council Assessment (Russell) identified structural misplacements and import graph redundancies
that violate set-theoretic non-overlap principles. This proposal relocates misclassified components to
their canonical homes and cleans up the import graph.

## Motivation

An element should belong to a single canonical category. Currently, `SparseChainComplex` (a homological
algebra object) lives in `analysis.py` (vector calculus), `permute_tensor` (a tensor automorphism) lives in
`transforms.py` (signal processing), and several semiring classes are imported twice in `__init__.py`.

## Specification

### 1. Relocate `SparseChainComplex`

- **From:** `algebrax/analysis.py`
- **To:** `algebrax/homology.py`
- **Rationale:** Chain complexes are foundational homological algebra objects ($\text{ChainComplex} \in \text{Homology}$),
  not vector calculus. The current placement forces an inverted dependency (`homology` → `analysis`).
- **Backward compat:** Re-import in `analysis.py` with deprecation comment.

### 2. Relocate `permute_tensor`

- **From:** `algebrax/transforms.py`
- **To:** `algebrax/tensor.py`
- **Rationale:** Index permutation is a tensor space automorphism ($T: \bigotimes V_i \to \bigotimes V_{\pi(i)}$),
  not a signal transform.
- **Backward compat:** Re-export in `transforms.py`.

### 3. Clean `__init__.py` Import Graph

- Remove duplicate `CliffordSemiring` / `GaloisFieldSemiring` imports (currently imported from both
  `algebrax.clifford` and `algebrax.semiring`, where the latter silently overwrites the former).
- Import `cholesky`, `lu`, `qr`, `svd` from `algebrax.matrix` (which already re-exports them) instead
  of directly from `algebrax.matrix.decompose`.

### 4. Consolidate Redundant Converters

- Delegate `tensor.flatten_tensor` → `converters.nested_to_flat`
- Delegate `tensor.unflatten_tensor` → `converters.flat_to_nested`
- Retain backward-compatible aliases in `tensor.py`.

### 5. Fix `transforms.py` Module Docstring

- Remove claim about "fractal dimension estimation" — `box_counting_dimension` lives in `algebrax.metrics`.

## Falsifiable Invariants

- All existing tests pass unchanged (289/289).
- `from algebrax.homology import SparseChainComplex` works.
- `from algebrax.tensor import permute_tensor` works.
- `from algebrax.analysis import SparseChainComplex` still works (backward compat).
- No duplicate symbol names in `dir(algebrax)` after cleanup.

## Backwards Compatibility

All changes maintain backward-compatible re-exports. No breaking changes.

## Change Log

* **2026-08-02:** Initial Draft from Grand Council Assessment (Russell).
* **2026-08-05:** Fully implemented taxonomy relocations (`SparseChainComplex`, `permute_tensor`), `flatten`/`unflatten` delegation, docstring fix, and `__init__.py` import graph cleanups. Status → Final.

