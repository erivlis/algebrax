---
title: "EP-0133: Jupyter Rich Display & CLI Inspector"
description: "Rich _repr_html_() for sparse matrices in Jupyter and a CLI tool for inspecting algebraic structures."
icon: lucide/terminal
status: draft
---

# EP-0133: Jupyter Rich Display & CLI Inspector

| Field       | Value                                |
|:------------|:-------------------------------------|
| **EP**      | 0133                                 |
| **Title**   | Jupyter Rich Display & CLI Inspector |
| **Author**  | Eran Rivlis & Antigravity            |
| **Status**  | Draft                                |
| **Type**    | Standards Track                      |
| **Created** | 2026-08-02                           |
| **Updated** | 2026-08-02                           |

## Abstract

This proposal adds two integration surfaces that reduce friction for users exploring `algebrax`:

1. **Jupyter `_repr_html_()`**: Rich HTML rendering of sparse matrices, semirings, and algebraic structures directly in
   Jupyter notebooks with color-coded heatmaps and formatted LaTeX.
2. **CLI Inspector**: A `python -m algebrax inspect` command that loads a JSON graph/matrix, applies a semiring power
   operation, and prints the result.

## Motivation

**The Steward (Harmony):** *"Move forward with the least friction."* Users currently must write boilerplate to visualize
results. Jupyter's `_repr_html_()` protocol and a CLI tool eliminate this friction.

## Specification

### 1. `_repr_html_()` Protocol

Add `_repr_html_()` methods to:

- `SparseMatrix` wrapper class (or a display helper function `algebrax.display.matrix_html()`)
- `Semiring` base class (showing the semiring name, zero, one, and operator symbols)
- `SimplicialComplex` (showing simplex counts and Betti numbers)
- `AlgebraicTrie` (showing a tree structure)

### 2. CLI Inspector

```bash
# Apply tropical matrix power and display result
python -m algebrax inspect graph.json --semiring tropical --power 5

# Show semiring catalog
python -m algebrax catalog

# Verify algebraic laws for a semiring
python -m algebrax verify --semiring viterbi
```

### 3. Display Helper Module: `algebrax.display`

```python
def matrix_html(matrix: SparseMatrix, title: str = '') -> str:
    """Generate an HTML table with heatmap coloring for a sparse matrix."""

def semiring_card(semiring: Semiring) -> str:
    """Generate an HTML card summarizing a semiring's properties."""
```

## Backwards Compatibility

Purely additive. No existing behavior changes.

## Change Log

* **2026-08-02:** Initial Draft.
