---
title: "EP-0146: Developer Ergonomics & Ecosystem Bridges"
description: "Namespace organization, optional NumPy/SciPy interop, and Jupyter rich display support."
icon: lucide/plug
status: final
---

# EP-0146: Developer Ergonomics & Ecosystem Bridges

| Field       | Value                                        |
|:------------|:---------------------------------------------|
| **EP**      | 0146                                         |
| **Title**   | Developer Ergonomics & Ecosystem Bridges     |
| **Author**  | Eran Rivlis & Antigravity                    |
| **Status**  | Final                                        |
| **Type**    | Standards Track                              |
| **Created** | 2026-08-02                                   |
| **Updated** | 2026-08-05                                   |

## Abstract

The Grand Council Assessment (Steward) identified three ergonomic friction points: top-level namespace
overcrowding (100+ symbols), missing ecosystem interoperability bridges (NumPy, SciPy), and
absence of Jupyter rich display. This proposal addresses all three while preserving the zero-dependency core.

## Motivation

`algebrax` works directly on native Python dicts — a powerful design choice. However, the current
developer experience suffers from: generic function names (`add`, `product`, `power`) shadowing
builtins when star-imported, no bridge to the PyData ecosystem for users working in mixed pipelines,
and raw dict output in Jupyter notebooks being unreadable for inspection.

## Specification

### 1. Namespace Organization (`algebrax/__init__.py`)

Re-exported submodules as namespace objects for clean qualified access:

```python
import algebrax as ax

result = ax.matrix.dot(A, B, semiring=ax.semiring.TropicalSemiring())
betti = ax.homology.cohomology_rank(complex, 1)
```

Enables idiomatic usage patterns while retaining flat imports for backward compatibility.

### 2. Optional Ecosystem Converters (`algebrax.converters`)

Added soft-dependency helpers that raise `ImportError` with a helpful message if NumPy/SciPy is not
installed. These are **optional** — the core library remains zero-dependency.

```python
def to_numpy(matrix: SparseMatrix, shape: tuple[int, int] | None = None) -> 'numpy.ndarray':
    """Convert sparse dict matrix to NumPy 2D array."""

def from_numpy(arr: 'numpy.ndarray') -> SparseMatrix:
    """Convert NumPy 2D array to sparse dict matrix (zero entries pruned)."""

def to_scipy(matrix: SparseMatrix, format: str = 'csr') -> 'scipy.sparse.spmatrix':
    """Convert sparse dict matrix to SciPy sparse matrix."""

def from_scipy(sp_matrix: 'scipy.sparse.spmatrix') -> SparseMatrix:
    """Convert SciPy sparse matrix to sparse dict matrix."""
```

### 3. Jupyter Rich Display (`algebrax.display`)

Added `algebrax.display` module:

```python
def display_matrix(matrix: SparseMatrix, title: str = '') -> str:
    """Return HTML table representation for Jupyter Notebooks."""

def display_vector(vector: SparseVector, title: str = '') -> str:
    """Return HTML representation of a sparse vector."""

def display_trie(trie: AlgebraicTrie, max_depth: int = 4) -> str:
    """Return HTML tree representation of an AlgebraicTrie."""
```

## Falsifiable Invariants

- `import algebrax as ax; ax.matrix.dot({0:{0:1}}, {0:{0:2}})` works.
- `from_numpy(to_numpy(M)) == M` round-trip identity for integer-keyed matrices.
- `from_scipy(to_scipy(M)) == M` round-trip identity.
- `display_matrix(M)` returns a valid HTML string containing `<table>` elements.
- All ecosystem converters raise `ImportError` with clear install instructions when optional deps are missing.
- Core `algebrax` remains installable and fully functional without NumPy/SciPy.

## Backwards Compatibility

Purely additive. Namespace re-exports are non-breaking. Ecosystem converters use soft dependencies. `algebrax.display` is a new optional module.

## Change Log

* **2026-08-02:** Initial Draft from Grand Council Assessment (Steward).
* **2026-08-05:** Fully implemented submodule namespace re-exports in `__init__.py`, `to_numpy`/`from_numpy`/`to_scipy`/`from_scipy` in `converters.py`, `display_matrix`/`display_vector`/`display_trie` in `display.py`, and added test suite `test_ergonomics.py`. Status → Final.

