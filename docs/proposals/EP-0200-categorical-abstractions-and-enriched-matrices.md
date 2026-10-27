---
title: "EP-0200: Categorical Abstractions & Enriched Matrix Mechanics"
description: "Formalize mathematical Category and Functor protocols in algebrax.category, establish the Matrix Category Mat(S), and realize Lawvere metric spaces over tropical semirings."
icon: lucide/network
status: draft
---

# EP-0200: Categorical Abstractions & Enriched Matrix Mechanics

| Field        | Value                                                              |
|:-------------|:-------------------------------------------------------------------|
| **EP**       | 0200                                                               |
| **Title**    | Categorical Abstractions & Enriched Matrix Mechanics               |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Antigravity                        |
| **Sponsor**  | Core Maintainers                                                   |
| **Delegate** | 🧩 Russell (Taxonomy & Consistency) & ⚡ Shannon (Zero Bloat & Efficiency) |
| **Status**   | Draft                                                              |
| **Type**     | Standards Track                                                    |
| **Created**  | 2026-10-27                                                         |
| **Updated**  | 2026-10-27                                                         |
| **Replaces** | —                                                                  |
| **Superseded-By** | —                                                             |

---

## Abstract

This proposal establishes a rigorous, Lean 4 Mathlib-aligned category-theoretic substrate within `algebrax.category`, upgrading the module from a pair of thin helper functions into a first-class mathematical suite. EP-0200 introduces: (1) core protocols for `Category[Obj, Mor]` and `Functor[C, D]`; (2) the **Matrix Category** $\mathbf{Mat}(S)$, where objects are finite index sets, morphisms are sparse dict-matrices, and composition is sparse matrix multiplication (`dot`); (3) **Lawvere Metric Spaces**, realizing metric spaces and graph shortest-path networks as enriched categories over the tropical cost semiring $\langle [0, \infty], \ge, +, 0 \rangle$; and (4) automated property-based verification (`verify_category_laws`, `verify_functor_laws`) in `algebrax.verification`. All abstractions adhere strictly to AlgebraX's canonical carrier constraint: **zero-overhead, unboxed sparse dictionary matrices**.

---

## Motivation

AlgebraX introduced `algebrax.category` in Phase 2 ([EP-0113](EP-0113-categorical-morphisms-and-kleisli.md)) to support Kleisli composition and Kan extensions. However, the implementation remained skeletal:
- `kleisli_compose(f, g, semiring)` is a 1-line wrapper around `dot(f, g, semiring)`.
- `kan_extension_left(p, f, semiring)` is a 1-line wrapper around `dot(f, p, semiring)`.

Neither function exposes or verifies actual categorical structures. There is no `Category` protocol, no `Functor` abstraction, and no way to inspect objects, domains, codomains, or identity morphisms.

Meanwhile, seminal computer science and mathematics literature demonstrates that **Category Theory is the natural unifying language of linear algebra and graph algorithms**:
1. **Stephen Dolan (2013)** demonstrated in *Fun with Semirings* that for any semiring $S$, matrices form a category $\mathbf{Mat}(S)$ whose composition is matrix multiplication and whose Kleene star $\mathbf{A}^*$ unifies shortest paths, transitive closure, and regular languages.
2. **F. William Lawvere (1973)** demonstrated in *Metric spaces, generalized logic, and closed categories* that an extended metric space $(X, d)$ is strictly a category enriched over the tropical cost semiring $\mathcal{V} = \langle [0, \infty], \ge, +, 0 \rangle$, where the triangle inequality $d(x, z) \le d(x, y) + d(y, z)$ is nothing more than morphism composition $g \circ f$.
3. **Lean 4 Mathlib** organizes modern computational algebra around `CategoryTheory.Category` and `CategoryTheory.ConcreteCategory`.

By elevating `algebrax.category` into a first-class protocol suite, AlgebraX bridges abstract category theory with high-performance sparse matrix computation without introducing heavy boxed wrappers.

---

## Rationale & Council Alignment

- **🧩 Russell (Taxonomy, Ontological Coherence & Deductive Order)**:
  Directly aligns the category hierarchy with Lean 4 Mathlib. Separates object classification from morphism composition, eliminating ad-hoc function signatures.
- **⚡ Shannon (Zero Bloat & Unboxed Efficiency)**:
  Rejects heavy object-oriented wrapper hierarchies (e.g. `class Morphism`, `class Object`). Morphisms in $\mathbf{Mat}(S)$ remain **raw Python dictionaries** `dict[K, dict[V, S]]`. `MatrixCategory` acts as a stateless, zero-cost operator.
- **🔬 Popper (Falsifiability & Empirical Invariants)**:
  Specifies executable property-based testing in `algebrax.verification`: `verify_category_laws` (left/right identities, associativity) and `verify_functor_laws` (identity and composition preservation).
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  Demystifies category theory through concrete computational realities: showing that *"a category is just a typed graph of compatible matrices where matrix multiplication is composition."*
- **⚖️ Noether (Structural Conservation)**:
  Guarantees that algebraic conservation laws (e.g. semiring distributivity and associativity) map directly to the functorial preservation of paths across matrix pipelines.

---

## Specification

### 1. The Core Category Protocols (`src/algebrax/category/core.py`)

```python
from typing import Generic, Protocol, TypeVar, runtime_checkable
from collections.abc import Iterable

Obj = TypeVar("Obj")
Mor = TypeVar("Mor")
Obj_co = TypeVar("Obj_co", covariant=True)
Mor_co = TypeVar("Mor_co", covariant=True)


@runtime_checkable
class Category(Protocol[Obj, Mor]):
    r"""A mathematical category $\mathcal{C} = \langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{id}, \circ \rangle$."""

    def id(self, x: Obj) -> Mor:
        r"""Identity morphism $\mathrm{id}_x : x \to x$."""
        ...

    def compose(self, f: Mor, g: Mor) -> Mor:
        r"""Composition of morphisms: $g \circ f$ (f followed by g)."""
        ...

    def source(self, f: Mor) -> Obj:
        r"""Source object $\mathrm{dom}(f)$."""
        ...

    def target(self, f: Mor) -> Obj:
        r"""Target object $\mathrm{cod}(f)$."""
        ...


@runtime_checkable
class Functor(Protocol[Obj, Mor, Obj_co, Mor_co]):
    r"""A functor $F : \mathcal{C} \to \mathcal{D}$ between categories."""

    def map_obj(self, x: Obj) -> Obj_co:
        r"""Object mapping: $F(x)$."""
        ...

    def map_mor(self, f: Mor) -> Mor_co:
        r"""Morphism mapping: $F(f)$."""
        ...
```

---

### 2. The Matrix Category $\mathbf{Mat}(S)$ (`src/algebrax/category/matrix.py`)

A concrete category whose morphisms are unboxed sparse dict-matrices over a semiring or ring $S$:

```python
from typing import Generic, TypeVar
from algebrax.algebra import Semiring
from algebrax.matrix import dot
from algebrax.typing import SparseMatrix

K = TypeVar("K")
V = TypeVar("V")


class MatrixCategory(Generic[K, V]):
    r"""The Category $\mathbf{Mat}(S)$ of sparse matrices over a Semiring $S$.

    - Objects: Frozensets of row/column index keys.
    - Morphisms: Sparse matrices $M \in S^{A \times B}$.
    - Composition: $g \circ f = \mathrm{dot}(f, g, \mathrm{semiring}=S)$.
    - Identity: $\mathrm{id}_A = \{k: \{k: 1_S\} \mid k \in A\}$.
    """

    def __init__(self, semiring: Semiring[V]):
        self._semiring = semiring

    def id(self, x: frozenset[K]) -> SparseMatrix[K, V]:
        one = self._semiring.one
        return {k: {k: one} for k in x}

    def compose(self, f: SparseMatrix[K, V], g: SparseMatrix[K, V]) -> SparseMatrix[K, V]:
        return dot(f, g, semiring=self._semiring)

    def source(self, f: SparseMatrix[K, V]) -> frozenset[K]:
        return frozenset(f.keys())

    def target(self, f: SparseMatrix[K, V]) -> frozenset[K]:
        targets = set()
        for row in f.values():
            targets.update(row.keys())
        return frozenset(targets)
```

---

### 3. Lawvere Enriched Metric Category (`src/algebrax/category/enriched.py`)

Realizes F. William Lawvere's theorem that generalized metric spaces are categories enriched over the tropical cost semiring $\langle [0, \infty], \ge, +, 0 \rangle$:

```python
from algebrax.semiring.optimization import MinPlusSemiring


class LawvereMetricCategory:
    r"""A Lawvere metric space $(X, d)$ as a category enriched over $\langle [0, \infty], \ge, +, 0 \rangle$.

    - Objects: Points $x \in X$.
    - Enriched Morphism: Distance $d(x, y) \in [0, \infty]$.
    - Enriched Composition: Triangle inequality $d(x, y) + d(y, z) \ge d(x, z)$.
    - Enriched Identity: $d(x, x) = 0$.
    """

    def __init__(self, distance_matrix: SparseMatrix[K, float]):
        self._d = distance_matrix
        self._semiring = MinPlusSemiring()

    def distance(self, x: K, y: K) -> float:
        return self._d.get(x, {}).get(y, float("inf"))

    def compose_paths(self, f: SparseMatrix[K, float], g: SparseMatrix[K, float]) -> SparseMatrix[K, float]:
        """Compute all-pairs shortest paths via min-plus matrix composition."""
        return dot(f, g, semiring=self._semiring)
```

---

### 4. Falsifiable Category Axiom Verification (`src/algebrax/verification.py`)

```python
def verify_category_laws(
    cat: Category[Obj, Mor],
    objects: Iterable[Obj],
    morphisms: Iterable[Mor],
    eq_fn: Callable[[Mor, Mor], bool],
) -> dict[str, bool]:
    r"""Test Category axioms:
    - Left Identity: id(cod(f)) \circ f == f
    - Right Identity: f \circ id(dom(f)) == f
    - Associativity: (h \circ g) \circ f == h \circ (g \circ f)
    """
    ...


def verify_functor_laws(
    functor: Functor[Obj, Mor, Obj2, Mor2],
    cat_src: Category[Obj, Mor],
    cat_dst: Category[Obj2, Mor2],
    test_objects: Iterable[Obj],
    test_morphisms: Iterable[Mor],
    eq_fn: Callable[[Mor2, Mor2], bool],
) -> dict[str, bool]:
    r"""Test Functor axioms:
    - Identity preservation: F(id_x) == id_{F(x)}
    - Composition preservation: F(g \circ f) == F(g) \circ F(f)
    """
    ...
```

---

## Backwards Compatibility

1. **Existing Functions Unbroken**:
   `kleisli_compose` and `kan_extension_left` in `algebrax.category` remain fully functional and backwards-compatible. They are re-exported from `algebrax.category`.
2. **Zero Overhead Carrier Invariant**:
   Morphisms remain unboxed dictionaries `dict[K, dict[V, S]]`. No boxing into `class Morphism` is required.

---

## How to Teach This / Documentation Plan

- Add `guide/discrete/category.md` to Tier 6 of the User Guide (per EP-0193), showcasing:
  1. The 30-second snippet composing matrices via `MatrixCategory(StandardSemiring(float))`.
  2. The Lawvere metric interpretation of shortest path networks.
  3. Interactive verification using `verify_category_laws`.

---

## Reference Implementation

A prototype test in `tests/algebrax/test_category.py` confirms that `MatrixCategory(StandardSemiring(float))` satisfies all category axioms under `verify_category_laws`.

---

## Rejected Ideas

1. **Boxing Matrices into `Morphism` Classes**:
   - *Rejected*: Violates Shannon efficiency and core carrier constraints. Morphisms must remain raw dictionaries.
2. **Infinite Category Formalization**:
   - *Rejected*: Out of scope for a computational sparse matrix library. Focus remains on finite, computable categories.

---

## Open Questions

- [ ] Should `MatrixCategory` provide automatic matrix transposition as the categorical dual (opposite category $\mathcal{C}^{\mathrm{op}}$)? (**Recommended: Yes, via `cat.opposite()`**).

---

## Change Log

* **2026-10-27:**
    * Initial Draft authored by Eran Rivlis & Antigravity derived from EXP-0005.
