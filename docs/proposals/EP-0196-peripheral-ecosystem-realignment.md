---
title: "EP-0196: Peripheral Ecosystem Realignment (Benchmarks, Recipes, GUI Lab & User Guides)"
description: "Align benchmarks, recipe notebooks, GUI lab, and user documentation with canonical alias-free interfaces established in EP-0195."
icon: lucide/refresh-cw
status: final
---

# EP-0196: Peripheral Ecosystem Realignment (Benchmarks, Recipes, GUI Lab & User Guides)

| Field             | Value                                                                         |
|:------------------|:------------------------------------------------------------------------------|
| **EP**            | 0196                                                                          |
| **Title**         | Peripheral Ecosystem Realignment (Benchmarks, Recipes, GUI Lab & User Guides) |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                   |
| **Sponsor**       | Council Framework                                                             |
| **Delegate**      | 🎨 Feynman (Pedagogy & Didactic Clarity), ⏱️ Shannon (Efficiency)              |
| **Status**        | Final                                                                         |
| **Type**          | Standards Track                                                               |
| **Created**       | 2026-11-04                                                                    |
| **Updated**       | 2026-11-04                                                                    |
| **Replaces**      | —                                                                             |
| **Superseded-By** | —                                                                             |

## Abstract

Following the core engine and verification purge in [EP-0195](EP-0195-canonical-core-consolidation.md), this proposal
updates the surrounding ecosystem of `algebrax`: performance benchmarks (`benchmarks/`), interactive recipe notebooks
(`recipes/*.ipynb`, `recipes/*.py`), the DearPyGui graphical laboratory (`recipes/lab.py`), and documentation pages
(`docs/`). It ensures that every demonstration and benchmark measures and showcases pure canonical syntax without
relying on deprecated imports or aliases.

## Motivation

While EP-0195 cleanses `src/algebrax/` and `tests/`, peripheral assets must be updated to maintain ecosystem integrity:

1. **Benchmarks (`benchmarks/`)**: `test_benchmarks.py` and `test_linalg_benchmarks.py` currently invoke `ax.homology`
   and `ax.matrix.decompose.lu`. Measuring benchmark timings through legacy shims adds noise and inaccurate performance
   profiles.
2. **Recipes (`recipes/`)**: 12 recipes (including `clifford_rotor_kinematics`, `topological_data_analysis`, and
   `topological_homology_betti`) import `CliffordSemiring` and `algebrax.homology`. As the primary entry points for
   practitioners and researchers, recipes must model canonical, idiomatic usage.
3. **Interactive Lab (`recipes/lab.py`)**: The 5,100-line graphical lab must be validated against the alias-free API to
   ensure all 32 interactive visualizer views execute without regressions.
4. **Static Documentation & Navigation**: Validate `zensical build --clean` to confirm zero broken links or unresolved
   references across the documentation compendium.

## Rationale & Council Alignment

- **Richard Feynman (Honesty & Clarity)**: Tutorials and recipes must never teach deprecated habits. If a recipe
  demonstrates multivector physics, it must teach `CliffordAlgebra`, not a legacy semiring wrapper.
- **Claude Shannon (Efficiency & Direct Measurement)**: Benchmarks must benchmark direct implementations, eliminating
  indirection overhead.
- **Karl Popper (Empirical Demonstration)**: Every Jupyter notebook must execute head-to-tail without import errors or
  warnings.

## Specification

### 1. Benchmarks Realignment (`benchmarks/`)

- Update `benchmarks/test_benchmarks.py`: replace `ax.homology` with `ax.topology`.
- Update `benchmarks/test_linalg_benchmarks.py`: replace `ax.matrix.decompose.lu` with
  `ax.matrix.decompose.lu_decompose`.
- Run `uv run pytest benchmarks/` to confirm all benchmark suites execute cleanly.

### 2. Recipes Realignment (`recipes/`)

Update both `.py` scripts and paired `.ipynb` notebooks:

- `recipes/clifford_rotor_kinematics.py` & `.ipynb`: Update `CliffordSemiring` $\to$ `CliffordAlgebra`.
- `recipes/topological_data_analysis.py` & `.ipynb`: Update `algebrax.homology` $\to$ `algebrax.topology`.
- `recipes/topological_homology_betti.py` & `.ipynb`: Update `algebrax.homology` $\to$ `algebrax.topology`.
- `recipes/topological_neural_network.py` & `.ipynb`: Update `algebrax.homology` $\to$ `algebrax.topology`.
- Verify all recipes run cleanly via `pytest --nbmake` or direct Python execution.

### 3. Graphical Laboratory (`recipes/lab.py`)

- Audit `recipes/lab.py` imports and runtime accessors.
- Verify that `ax.topology`, `ax.analysis`, `ax.transforms`, and `ax.matrix` integrate seamlessly across all 7 domain
  categories and 32 views.

### 4. Documentation Build & Link Integrity

- Run `uv run zensical build --clean` to ensure the entire site builds with 0 errors and 0 warnings.
- Confirm that no deleted symbols (`homology`, `CliffordSemiring`, `DualNumberSemiring`, `PolynomialSemiring`,
  `AbelianGroup`) are mentioned in documentation examples.

## Backwards Compatibility

Non-breaking for modern canonical users. All recipes and benchmarks become strictly conforming reference
implementations.

## How to Teach This / Documentation Plan

- Recipe notebooks serve as living documentation. Updating them directly trains users on the canonical idioms.

## Reference Implementation

1. Update imports in `benchmarks/`.
2. Update scripts and notebooks in `recipes/`.
3. Test `recipes/lab.py` headless startup.
4. Run `uv run zensical build --clean`.

## Rejected Ideas

- **Leaving Notebooks Untouched**: Rejected because broken notebooks in `recipes/` destroy developer trust and fail
  automated CI notebook checks (`nbmake`).

## Open Questions

- None.

## Change Log

- **2026-11-04**: Draft authored following EXP-0007 Council consensus.
- **2026-11-04**: Implemented and verified: all benchmarks, recipes, notebooks, and user guides updated to pure canonical names; clean test, benchmark, and Zensical builds. Marked as Final.
