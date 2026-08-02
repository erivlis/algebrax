---
title: "EP-0145: Type Safety & Contract Hardening"
description: "Strengthens type annotations, normalizes semiring contracts, and fixes structural edge cases."
icon: lucide/shield-check
status: draft
---

# EP-0145: Type Safety & Contract Hardening

| Field       | Value                              |
|:------------|:-----------------------------------|
| **EP**      | 0145                               |
| **Title**   | Type Safety & Contract Hardening   |
| **Author**  | Eran Rivlis & Antigravity          |
| **Status**  | Draft                              |
| **Type**    | Standards Track                    |
| **Created** | 2026-08-02                         |
| **Updated** | 2026-08-02                         |

## Abstract

The Grand Council Assessment (Golem) identified type annotation compatibility risks across Python
3.10–3.14, inconsistent semiring parameter contracts (instance vs. class factory), and a flawed
collision branch in `flat_to_nested`. This proposal hardens type safety and explicit contracts.

## Motivation

`algebrax` achieves pristine functional purity and zero mutable state — a rare quality. However,
three contract-level issues create subtle correctness risks: recursive `TypeAlias` forward references
may fail runtime introspection on Python 3.10–3.11, semiring parameters accept either instances or
class types inconsistently across modules, and `flat_to_nested` silently corrupts on mixed-depth
key collisions.

## Specification

### 1. Forward-Compatible Type Annotations (`algebrax/typing.py`)

Add `from __future__ import annotations` to ensure the recursive `SparseTensor` TypeAlias:

```python
SparseTensor: TypeAlias = Mapping[K, 'SparseTensor[K, V] | V']
```

evaluates correctly under `typing.get_type_hints()` across Python 3.10–3.14.

### 2. Semiring Parameter Normalization

Create a private helper and apply across modules:

```python
def _normalize_semiring(s: Semiring[V] | type[Semiring[V]] | None) -> Semiring[V]:
    """Normalize semiring argument to an instance, handling class factories."""
    if s is None:
        return StandardSemiring()
    return s() if isinstance(s, type) else s
```

Apply in:
- `analysis.py`: `verify_nilpotency`, `hodge_laplacian`, `SparseChainComplex.__init__`
- `category.py`: `kleisli_compose`, `kan_extension_left`
- `transforms.py`: functions accepting `semiring` parameters

### 3. Fix `flat_to_nested` Collision Handling (`converters.py`)

Replace the flawed fallback branch (~line 480) with explicit validation:

```python
if not isinstance(current, dict):
    raise ValueError(
        f"Key collision: cannot nest dict under existing non-dict leaf at {keys[:i+1]}"
    )
```

### 4. Enforce Parameterized Generic Types

Audit and update all unparameterized usages of `SparseMatrix` and `SparseVector` across:
- `homology.py`, `analysis.py`, `converters.py`, `matrix/core.py`

Standardize return type annotations (e.g., `transpose()` returns `dict[K, dict[K, V]]` consistently
typed as the concrete return rather than the `Mapping`-based `SparseMatrix`).

## Falsifiable Invariants

- `typing.get_type_hints(algebrax.typing)` resolves without errors on Python 3.10–3.14.
- `_normalize_semiring(TropicalSemiring)` and `_normalize_semiring(TropicalSemiring())` both
  return a valid `TropicalSemiring` instance.
- `flat_to_nested({(1,): 'a', (1, 2): 'b'})` raises `ValueError` instead of silent corruption.
- `mypy` type checking passes on all modified modules.

## Backwards Compatibility

- `_normalize_semiring` is private (no public API change).
- `flat_to_nested` now raises `ValueError` on previously-undefined collision behavior — this is a
  correctness fix, not a breaking change (prior behavior was silently incorrect).
- Type annotation changes are non-behavioral.

## Change Log

* **2026-08-02:** Initial Draft from Grand Council Assessment (Golem).
