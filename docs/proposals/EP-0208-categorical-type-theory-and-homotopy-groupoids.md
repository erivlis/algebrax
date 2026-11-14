---
title: "EP-0208: Categorical Type Theory, Semiring Coeffects & Homotopy Groupoids"
description: "Formalize Cartesian Closed Categories, the Curry-Howard-Lambek correspondence, semiring-graded coeffects for resource bounds, and simplicial homotopy path groupoids."
icon: lucide/binary
status: final
---

# EP-0208: Categorical Type Theory, Semiring Coeffects & Homotopy Groupoids

| Field             | Value                                                               |
|:------------------|:--------------------------------------------------------------------|
| **EP**            | 0208                                                                |
| **Title**         | Categorical Type Theory, Semiring Coeffects & Homotopy Groupoids    |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                         |
| **Sponsor**       | Core Maintainers                                                    |
| **Delegate**      | 🧩 Russell (Type Stratification) & 🛡️ Golem (Type Safety Contracts) |
| **Status**        | Final                                                               |
| **Type**          | Standards Track                                                     |
| **Created**       | 2026-10-28                                                          |
| **Updated**       | 2026-11-14                                                          |
| **Replaces**      | —                                                                   |
| **Superseded-By** | —                                                                   |

---

## Abstract

This proposal formalizes the profound unity between Logic, Category Theory, and Type Systems—the **Curry–Howard–Lambek
correspondence**—within AlgebraX. EP-0208 establishes:

1. **Cartesian Closed Categories (CCC)**: Extending `algebrax.category` with categorical products $A \times B$,
   coproducts $A \amalg B$, and exponential objects $B^A$, providing the categorical model of the simply typed lambda
   calculus.
2. **Semiring-Graded Coeffects**: Applying AlgebraX's semirings to type-theoretic resource tracking:
    - Variable reuse tracking via the natural number semiring $\langle \mathbb{N}, +, \times \rangle$.
    - Dead-code and reachability analysis via the Boolean semiring $\langle \mathbb{B}, \lor, \land \rangle$.
    - Latency and privacy cost bounds via the tropical
      semiring $\langle \mathbb{R}_{\ge 0} \cup \{\infty\}, \min, + \rangle$.
3. **Simplicial Homotopy Path Groupoids ($\Pi_1 (K)$)**: Grounding Homotopy Type Theory (HoTT) in `algebrax.topology`:
   1-chains modulo 2-face homotopies form a groupoid where terms are points, proofs are continuous paths, and higher
   proofs are 2D homotopies.
4. **Synthetic Univalence**: Establishing that isomorphic structures in AlgebraX categories have equivalent categorical
   behavior without requiring manual transport lemmas ($A \cong B \implies F (A) \cong F (B)$).
5. **Property-Based Verification**: Executable testing in `algebrax.verification`: `verify_exponential_adjunction`,
   `verify_coeffect_grading`, and `verify_path_groupoid_laws`.

All abstractions preserve AlgebraX's unboxed sparse carriers, with zero runtime wrapping.

---

## Motivation

AlgebraX’s architectural principles are anchored by **Council Delegate 🧩 Russell (Taxonomy, Ontological Coherence &
Deductive Order)**, named after Bertrand Russell who invented Type Theory in 1908.

Today, modern mathematics and computational foundations are governed by three deep insights:

1. **Curry–Howard–Lambek**: Writing a program, proving a theorem, and composing morphisms in a Cartesian Closed Category
   are identical mathematical activities.
2. **Homotopy Type Theory (HoTT)**: Vladimir Voevodsky demonstrated that types are topological spaces, identity proofs
   are paths, and isomorphisms are equalities (the Univalence Axiom).
3. **Coeffects & Semirings**: In modern compiler theory (Orchard & Petricek), semirings provide the universal algebraic
   language for tracking computational resource bounds, sensitivity, and execution costs.

By formalizing these structures, AlgebraX connects its sparse matrix engine and semiring taxonomy to the forefront of
modern theoretical computer science.

---

## Rationale & Council Alignment

- **🧩 Russell (Taxonomy, Type Stratification & Deductive Order)**:
  Directly honors Russell's type theory, ensuring clear ontological stratification between objects, morphisms, types,
  and coeffects.
- **🛡️ Golem (Type Safety & Defensive Contracts)**:
  Guarantees type-checked composition in categories and formal static contracts on resource consumption via semiring
  coeffects.
- **⚡ Shannon (Zero Bloat & Discrete Groupoids)**:
  Rejects heavy AST wrappers. Paths are simple tuples of vertex indices, and path homotopies are sparse triangulated
  moves.
- **🔬 Popper (Falsifiability & Groupoid Invariants)**:
  Tests path groupoid associativity, left/right path inversion ($p \cdot p^{-1} \sim \mathrm{id}$ modulo 2-faces), and
  exponential adjunction laws.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"A type system is just a set of rules that prevents you from feeding diesel into an electric car. A coeffect system
  tells you exactly how much electricity that car will burn before you drive it."*

---

## Specification

### 1. Atomic Categorical Mixins & Flat Protocol Composition (`src/algebrax/category/_mixins.py`, `core.py`, `ccc.py`)

In strict compliance with [EP-0005](EP-0005-universal-algebraic-protocol-architecture.md) and [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md) (**Law of Flat Protocol Composition**), `algebrax.category` decomposes categorical capabilities into **9 orthogonal Layer-1 operational mixins (`Has*`)** in `src/algebrax/category/_mixins.py`:

| Atomic Mixin | Type Parameters | Required Member(s) | Mathematical Signature |
| :--- | :--- | :--- | :--- |
| `HasQuiver[Obj, Mor]` | `(Obj, Mor)` | `source(f) -> Obj`, `target(f) -> Obj` | $\langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{source}, \mathrm{target} \rangle$ |
| `HasCatId[Obj, Mor]` | `(Obj, Mor)` | `id(x) -> Mor` | $\langle \mathrm{Obj}, \mathrm{Hom}, \mathrm{id} \rangle$ |
| `HasCompose[Mor]` | `(Mor,)` | `compose(f, g) -> Mor` | $\langle \mathrm{Hom}, \circ \rangle$ |
| `HasMorInv[Mor]` | `(Mor,)` | `invert_path(f) -> Mor` | $\langle \mathrm{Hom}, ()^{-1} \rangle$ |
| `HasTerminal[Obj]` | `(Obj,)` | `terminal -> Obj` | $\langle \mathrm{Obj}, \mathbf{1} \rangle$ |
| `HasProducts[Obj, Mor]` | `(Obj, Mor)` | `product(a, b)`, `proj1(a, b)`, `proj2(a, b)`, `pair(f, g)` | $\langle \mathrm{Obj}, \mathrm{Hom}, \times, \pi_1, \pi_2, \langle -,- \rangle \rangle$ |
| `HasExponentials[Obj, Mor]` | `(Obj, Mor)` | `exponential(base, exp)`, `eval_mor(base, exp)`, `curry(...)`, `uncurry(...)` | $\langle \mathrm{Obj}, \mathrm{Hom}, B^A, \mathrm{eval}, \mathrm{curry}, \mathrm{uncurry} \rangle$ |
| `HasMapObj[Obj, Obj_co]` | `(Obj, Obj_co)` | `map_obj(x) -> Obj_co` | $\langle \mathrm{Obj}_{\mathcal{C}}, \mathrm{Obj}_{\mathcal{D}}, F_{\mathrm{Obj}} \rangle$ |
| `HasMapMor[Mor, Mor_co]` | `(Mor, Mor_co)` | `map_mor(f) -> Mor_co` | $\langle \mathrm{Hom}_{\mathcal{C}}, \mathrm{Hom}_{\mathcal{D}}, F_{\mathrm{Mor}} \rangle$ |

All Layer-2 categorical protocols inherit **exclusively** from Layer-1 `Has*` mixins and `typing.Protocol` with zero diamond inheritance:

```python
@runtime_checkable
class Quiver(HasQuiver[Obj, Mor], Protocol[Obj, Mor]): ...

@runtime_checkable
class Category(HasQuiver[Obj, Mor], HasCatId[Obj, Mor], HasCompose[Mor], Protocol[Obj, Mor]): ...

@runtime_checkable
class Groupoid(
    HasQuiver[Obj, Mor], HasCatId[Obj, Mor], HasCompose[Mor], HasMorInv[Mor], Protocol[Obj, Mor]
): ...

@runtime_checkable
class CartesianCategory(
    HasQuiver[Obj, Mor], HasCatId[Obj, Mor], HasCompose[Mor],
    HasTerminal[Obj], HasProducts[Obj, Mor], Protocol[Obj, Mor]
): ...

@runtime_checkable
class CartesianClosedCategory(
    HasQuiver[Obj, Mor], HasCatId[Obj, Mor], HasCompose[Mor],
    HasTerminal[Obj], HasProducts[Obj, Mor], HasExponentials[Obj, Mor], Protocol[Obj, Mor]
): ...

@runtime_checkable
class Functor(
    HasMapObj[Obj, Obj_co], HasMapMor[Mor, Mor_co], Protocol[Obj, Mor, Obj_co, Mor_co]
): ...
```

### 2. Semiring-Graded Coeffects (`src/algebrax/category/coeffect.py`)

```python
from algebrax.algebra import Semiring


class SemiringCoeffectTracker(Generic[Obj]):
    r"""Tracks computational resource bounds graded by a Semiring $S$."""

    def __init__(self, semiring: Semiring[Any]) -> None:
        self.semiring = semiring
        self._costs: dict[Obj, Any] = {}

    def record_cost(self, operation: Obj, cost: Any) -> None:
        if operation in self._costs:
            self._costs[operation] = self.semiring.add(self._costs[operation], cost)
        else:
            self._costs[operation] = cost

    def compose_sequence(self, op1: Obj, op2: Obj) -> Any:
        r"""Compose execution costs via semiring multiplication: $c_1 \times c_2$."""
        c1 = self._costs.get(op1, self.semiring.one)
        c2 = self._costs.get(op2, self.semiring.one)
        return self.semiring.mul(c1, c2)
```

### 3. Simplicial Homotopy Path Groupoid (`src/algebrax/topology/groupoid.py`)

```python
class SimplicialPathGroupoid(Groupoid[Any, tuple[Any, ...]]):
    r"""Fundamental groupoid $\Pi_1(K)$ over simplicial complex $K$.

    Objects: Vertices $v \in K_0$.
    Morphisms: Paths of edges modulo 2-face homotopies.
    Composition: Path concatenation.
    Inversion: Path reversal.
    """

    def __init__(self, vertices: set[Any], edges: set[tuple[Any, Any]], triangles: set[tuple[Any, ...]]) -> None:
        self.vertices = vertices
        self.edges = edges
        self.triangles = triangles

    def invert_path(self, path: tuple[Any, ...]) -> tuple[Any, ...]:
        """Invert path by reversing vertex sequence."""
        return path[::-1]

    def are_homotopic(self, path1: tuple[Any, ...], path2: tuple[Any, ...]) -> bool:
        r"""Test if two paths are homotopic modulo 2-face boundary moves."""
        ...
```

---

## Backwards Compatibility

Strictly additive. Extends `algebrax.category` and `algebrax.topology`.

---

## How to Teach This / Documentation Plan

1. **User Guide (`docs/guide/discrete/category.md`)**:
    - The Curry-Howard-Lambek triangle: logic, programs, categories.
    - Resource bound estimation using semiring coeffects.
    - Synthetic topology: paths as proofs in simplicial complexes.

---

## Reference Implementation

Implemented across `src/algebrax/category/ccc.py`, `src/algebrax/category/coeffect.py`, `src/algebrax/topology/groupoid.py`, and `src/algebrax/verification.py`, with unit and MMS tests in `tests/algebrax/test_type_theory_and_groupoids.py` and `tests/verifications/test_mms_sheaves_and_categories.py`.

---

## Rejected Ideas

1. **Building an Entire Lambda Calculus Interpreter in Python**:
   *Rejected*: AlgebraX is a numerical and algebraic framework. We model the categorical semantics and coeffects, not a
   language runtime.

---

## Open Questions

1. **Higher Groupoids ($\Pi_\infty (K)$)**:
   Should we model 2-groupoids with explicit 2-morphisms? *Recommendation*: Keep $\Pi_1 (K)$ as the baseline, with
   higher homotopies represented via persistent homology.

---

## Change Log

- **2026-10-28**: Initial draft authored following Council consensus.
- **2026-11-14**: Implemented `CartesianClosedCategory`, `FiniteSetCCC`, `CoeffectContext`, `SemiringCoeffectTracker`, `SimplicialPathGroupoid`, and axiomatic verifiers; promoted status to Final.

