---
title: "EP-0006: Morphisms, Homomorphisms & Structural Mappings"
description: "Establishes universal structure-preserving mappings across AlgebraX: algebraic homomorphisms (groups, rings, modules, Lie), categorical arrows and functors, and natural dualities."
icon: lucide/arrow-right-left
status: draft
---

# EP-0006: Morphisms, Homomorphisms & Structural Mappings

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0006                                                                              |
| **Title**         | Morphisms, Homomorphisms & Structural Mappings                                     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | The Grand Council                                                                 |
| **Delegate**      | ⚖️ Emmy Noether (Invariants & Duality) & 🧭 The Explorer (Categorical Arrows)      |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-11-12                                                                        |
| **Updated**       | 2026-11-12                                                                        |
| **Replaces**      | [EP-0201](EP-0201-algebraic-homomorphisms-ideals-quotients.md) (Morphisms Spec)   |
| **Superseded-By** | —                                                                                 |

---

## Abstract

In modern mathematics, objects alone do not define a theory; **arrows (morphisms) between objects govern the structure**. As mandated by [EP-0001](EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md), AlgebraX treats structure-preserving mappings as first-class mathematical entities alongside objects.

This proposal establishes the universal **Morphism & Homomorphism Architecture** of AlgebraX:
1. **Algebraic Homomorphisms (`algebrax.algebra._homomorphisms`)**:
   - `Homomorphism[Dom, Cod]`: Base callable protocol for maps between carriers $\phi: \mathrm{Dom} \to \mathrm{Cod}$.
   - `GroupHom[Dom, Cod]`: Group homomorphisms preserving binary product and identity ($\phi(a \cdot b) = \phi(a) \cdot \phi(b)$).
   - `RingHom[Dom, Cod]`: Unital ring homomorphisms preserving addition, multiplication, zero, and one.
   - `LinearMap[R, Dom, Cod]`: Module and vector space homomorphisms preserving linear combinations ($\phi(r \cdot u + v) = r \cdot \phi(u) + \phi(v)$).
   - `LieAlgebraHom[Dom, Cod]`: Commutator-preserving maps ($\phi([x, y]) = [\phi(x), \phi(y)]$).
   - `CallableHomomorphism[Dom, Cod]`: Composable arrow abstraction providing $(\phi_2 \circ \phi_1)(x)$.
2. **Categorical Morphisms & Functors (`algebrax.category`)**:
   - `Category[Obj, Mor]`: Small categories with identities and associative composition.
   - `Functor[C, D]`: Structure-preserving maps between categories assigning objects to objects and arrows to arrows.
   - `OppositeCategory`: Dualization functor $\mathbf{C}^\mathrm{op}$.
   - Matrix categories $\mathbf{Mat}(S)$, Kleisli monadic arrows $f: A \to T(B)$, and Kan extensions.
3. **Morphism Verification Oracles (`algebrax.verification`)**:
   - Automated testing oracles: `verify_ring_homomorphism_laws`, `verify_category_laws`, `verify_functor_laws`.

---

## Motivation

Earlier phases of AlgebraX treated mathematical operations primarily within isolated structures (e.g. multiplying elements within a single group or ring). However, computational mathematics frequently demands **translating between structures**:

1. **Change of Base & Embeddings**: Embedding integers into rationals ($\mathbb{Z} \hookrightarrow \mathbb{Q}$), modular reductions ($\mathbb{Z} \twoheadrightarrow \mathbb{Z}/n\mathbb{Z}$), or complex embeddings into real $2 \times 2$ matrices.
2. **Linear Representations**: Mapping abstract group or Lie elements into matrix linear transformations ($\rho: G \to \mathrm{GL}(V)$).
3. **Dualities & Adjunctions**: Mapping cochain complexes to chain complexes via matrix transposes, and composing effectful probabilistic pipelines via Kleisli monads.

Without a unified morphism protocol standard, functions mapping between algebras were implemented as arbitrary Python callables without type-checked preservation laws or composition operators.

---

## Rationale & Council Alignment

- **⚖️ Emmy Noether (Symmetry, Morphisms & Conserved Quantities)**:
  The first isomorphism theorem ($\mathrm{Dom}/\ker(\phi) \cong \mathrm{im}(\phi)$) is the cornerstone of modern algebra. Structure is conserved under homomorphism.
- **🧭 The Explorer (Arrows, Categories & Compositionality)**:
  Category theory teaches that an object is entirely characterized by its incoming and outgoing arrows (the Yoneda lemma). Providing first-class morphisms unlocks functorial constructions across all domains.
- **🧩 Bertrand Russell (Type Safety & Variance)**:
  `Homomorphism[Dom, Cod]` uses strict variance annotations: contravariant domain `Dom` and covariant codomain `Cod`, matching mathematical function space typing $\mathrm{Hom}(A, B)$.
- **⚡ Claude Shannon (Zero Boxing Overhead)**:
  Homomorphisms are callable protocols. Any plain Python function or lambda `lambda x: ...` satisfies `Homomorphism[Dom, Cod]` without needing to be wrapped in a container class.

---

## Specification

### 1. Algebraic Homomorphisms (`src/algebrax/algebra/_homomorphisms.py`)

```python
from collections.abc import Callable
from typing import Generic, Protocol, TypeVar, runtime_checkable

Dom = TypeVar('Dom', contravariant=True)
Cod = TypeVar('Cod', covariant=True)
R = TypeVar('R')
V = TypeVar('V')
W = TypeVar('W')
K = TypeVar('K')


@runtime_checkable
class Homomorphism(Protocol[Dom, Cod]):
    r"""Base protocol for a mathematical mapping $\phi: \mathrm{Dom} \to \mathrm{Cod}$."""
    def __call__(self, x: Dom) -> Cod: ...


@runtime_checkable
class GroupHom(Protocol[Dom, Cod]):
    r"""Group homomorphism $\phi: G_1 \to G_2$ preserving group multiplication and identity."""
    def __call__(self, x: Dom) -> Cod: ...


@runtime_checkable
class RingHom(Protocol[Dom, Cod]):
    r"""Unital ring homomorphism $\phi: R_1 \to R_2$ preserving addition, multiplication, 0, and 1."""
    def __call__(self, x: Dom) -> Cod: ...


@runtime_checkable
class LinearMap(Protocol[R, Dom, Cod]):
    r"""Linear map $\phi: V \to W$ over scalar ring/field $R$ preserving addition and scalar multiplication."""
    def __call__(self, x: Dom) -> Cod: ...


@runtime_checkable
class LieAlgebraHom(Protocol[Dom, Cod]):
    r"""Lie algebra homomorphism $\phi: \mathfrak{g}_1 \to \mathfrak{g}_2$ preserving Lie brackets."""
    def __call__(self, x: Dom) -> Cod: ...


class CallableHomomorphism(Homomorphism[V, W], Generic[V, W]):
    r"""Composable homomorphism wrapper supporting arrow composition $\phi_2 \circ \phi_1$."""
    def __init__(self, fn: Callable[[V], W]) -> None:
        self._fn = fn

    def __call__(self, x: V) -> W:
        return self._fn(x)

    def compose(self, other: Homomorphism[K, V]) -> CallableHomomorphism[K, W]:
        return CallableHomomorphism(lambda x: self._fn(other(x)))
```

---

### 2. Categorical Morphisms & Functors (`src/algebrax/category/`)

```python
@runtime_checkable
class Category(Protocol[Obj, Mor]):
    r"""A small category $\mathbf{C}$ consisting of objects and arrows."""
    def identity(self, x: Obj) -> Mor: ...
    def compose(self, f: Mor, g: Mor) -> Mor: ...
    def src(self, f: Mor) -> Obj: ...
    def dst(self, f: Mor) -> Obj: ...


@runtime_checkable
class Functor(Protocol[C_Obj, C_Mor, D_Obj, D_Mor]):
    r"""A covariant functor $F: \mathbf{C} \to \mathbf{D}$."""
    def map_obj(self, x: C_Obj) -> D_Obj: ...
    def map_mor(self, f: C_Mor) -> D_Mor: ...
```

---

### 3. Falsifiability & Verification Oracles (`src/algebrax/verification.py`)

Morphisms are verified against their preservation laws:

```python
from algebrax.verification import verify_ring_homomorphism_laws

# Verify modular reduction phi: Z -> Z/5Z is a valid RingHom
phi = lambda x: x % 5
res = verify_ring_homomorphism_laws(
    domain_ring=IntegerField(),
    codomain_ring=ModularField(5),
    hom=phi,
    samples=[0, 1, 2, 7, -3, 14]
)
assert all(res.values())
```

---

## Backwards Compatibility

1. **Non-Breaking**: Extends the existing `algebrax.algebra._homomorphisms` and `algebrax.category` APIs without breaking any call signatures.
2. **Elevates EP-0201**: The morphism specifications from `EP-0201` are elevated and canonized as `EP-0006`.

---

## How to Teach This / Documentation Plan

- **Guide**: `docs/guide/category/` and `docs/guide/algebra/` document homomorphisms, change of base, and representation maps.
- **Notebooks**: Interactive examples in `recipes/categorical_kleisli_monads.ipynb` demonstrate morphism composition and string diagrams.

---

## Reference Implementation

- **Homomorphism Modules**: [`src/algebrax/algebra/_homomorphisms.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/algebra/_homomorphisms.py).
- **Category Modules**: [`src/algebrax/category/core.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/category/core.py).
- **Verification Engine**: [`src/algebrax/verification.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/verification.py).

---

## Rejected Ideas

1. **Requiring Every Function to Subclass a Heavy Morphism Base Class**:
   *Rejected*: Violates Pythonic duck-typing and the Shannon Invariant. Pure lambdas and callables satisfy `Homomorphism[Dom, Cod]` naturally.

---

## Open Questions

None. The morphism and category protocols have been verified across algebra, topology, and enriched matrices.

---

## Change Log

- **2026-10-27**: Morphisms introduced in EP-0201.
- **2026-11-12**: Unified and elevated to single-digit foundational canon as EP-0006.
