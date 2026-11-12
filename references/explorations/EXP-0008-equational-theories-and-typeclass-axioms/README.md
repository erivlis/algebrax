# EXP-0008: Equational Theories, Law Witness Mixins & Characteristic Mathematical Operations

| Field           | Value                                                                                                 |
|:----------------|:------------------------------------------------------------------------------------------------------|
| **EXP**         | 0008                                                                                                  |
| **Title**       | Equational Theories, Law Witness Mixins & Characteristic Mathematical Operations                      |
| **Author**      | Eran Rivlis, Antigravity AI, Grand Council                                                            |
| **Status**      | Concluded                                                                                             |
| **Type**        | Architectural & Research Exploration                                                                  |
| **Created**     | 2026-11-12                                                                                            |
| **Updated**     | 2026-11-12                                                                                            |
| **Related EPs** | [EP-0194](../../docs/proposals/EP-0194-atomic-algebraic-mixins-and-protocol-composition.md), [EP-0204](../../docs/proposals/EP-0204-non-associative-quantum-algebras-jordan-octonions-poisson.md), [EP-0216](../../docs/proposals/EP-0216-law-witness-mixins-and-equational-differentiation.md) |

---

## 1. Abstract & Context

### 1.1 The Problem Statement
In Phase 6 and Phase 7, AlgebraX established a granular algebraic hierarchy (EP-0190 through EP-0194, EP-0204) strictly governed by the **Law of Flat Protocol Composition** (EP-0194): Layer 2 Named Protocols may only inherit from Layer 1 Atomic Mixins (`Has*` in `algebrax.algebra._mixins`) and `typing.Protocol`.

However, an acute architectural gap arises when distinguishing structures that share identical operational signatures ($\Sigma$) but belong to fundamentally different mathematical varieties defined by distinct equational theories ($E$):

```python
# In src/algebrax/algebra/_non_assoc.py
class JordanAlgebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M]): ...
class AlternativeAlgebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M]): ...
class MalcevAlgebra(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M]): ...
```

Because Python's `typing.Protocol` and `@runtime_checkable` inspect only attribute names and method signatures:
1. **Zero Type-Level Distinction**: Static type checkers (`mypy`, `pyright`) treat `JordanAlgebra`, `AlternativeAlgebra`, and `MalcevAlgebra` as structurally interchangeable.
2. **False-Positive Runtime Collisions**: At runtime, `isinstance(so_n(3), JordanAlgebra)` evaluates to **`True`**, even though a Lie algebra is anticommutative and violates the Jordan identity $(xy)x^2 = x(y x^2)$!
3. **Ecosystem-Wide Blindness**: The exact same signature collision exists across single-sorted structures:
   - `Ring` vs. `CommRing` vs. `NonAssocRing`
   - `AddGroup` vs. `AddCommGroup`
   - `Module[R, M]` vs. `VectorSpace[R, M]`

### 1.2 The Core Question
> *How can an algebraic library express equational laws ($E$) explicitly in Python's type system and runtime protocol checks, while preserving zero-overhead unboxed carriers and the Law of Flat Protocol Composition?*

---

## 2. Global Literature & Comparative Analysis

We conducted an exhaustive survey of how modern proof assistants, computer algebra systems, and typed programming languages solve the tension between Signature ($\Sigma$) and Equational Laws ($E$):

### 2.1 Lean 4 / Mathlib: Semi-Bundled Mixins & `Prop`-Valued Typeclasses
- **Source**: Anne Baanen, *"Use and Abuse of Instance Parameters in the Lean Mathematical Library"* (ITP 2022, [PDF](./papers/Baanen_2022_Lean_Instance_Parameters.pdf)); Eric Wieser, *"Multiple-inheritance hazards in dependently-typed algebraic hierarchies"* (2023, [PDF](./papers/Wieser_2023_Multiple_Inheritance_Hazards.pdf)).
- **Mechanism**: Lean 4 bundles computational data into typeclasses, but isolates equational axioms and cross-cutting properties into **`Prop`-valued mixin typeclasses** (e.g. `[MulCommClass M]`, `[IsDomain R]`, `[IsOrderedMonoid M]`).
- **Core Lesson for AlgebraX**: Axioms do not carry runtime data. In Python terms, an axiom witness is a zero-runtime-cost marker property (returning `Literal[True]`) that participates in protocol subtyping without requiring wrapper objects or memory allocations.

### 2.2 Coq / Mathematical Components: Hierarchy Builder
- **Source**: Cyril Cohen, Kazuhiko Sakaguchi, Enrico Tassi, *"Hierarchy Builder: Algebraic Hierarchies Made Easy in Coq with Elpi"* (FSCD 2020, LIPIcs Vol. 167, [PDF](./papers/Cohen_2020_Hierarchy_Builder.pdf)).
- **Mechanism**: Separates atomic components (`HB.mixin`) from interfaces (`HB.structure`) and provides **factories** (`HB.factory`) with automatic builders that derive canonical properties from minimal user input.
- **Core Lesson for AlgebraX**: Protocols should provide automatic default derivations of canonical operations (e.g., deriving `associator` or `jordan_triple` from `add`, `sub`, and `mul`), eliminating boilerplate for library consumers.

### 2.3 SageMath: Categories with Axioms
- **Source**: Nicolas M. Thiéry et al., *"Infrastructure for generic code in SageMath: categories, axioms, constructions"* (CICM 2016); Dehaye & Thiéry et al., *"Interoperability in the OpenDreamKit Project"* (2016, [PDF](./papers/Dehaye_Thiery_2016_OpenDreamKit_Math_in_the_Middle.pdf)).
- **Mechanism**: Sage builds categories dynamically by attaching axioms (`Commutative`, `Associative`, `Unital`) as subcategories that inject generic algorithms and law verifications directly into the parent's MRO.

### 2.4 GAP 4: Filters, Categories & Properties
- **Source**: Thomas Breuer & Steve Linton, *"The GAP 4 Type System: Organising Algebraic Algorithms"*.
- **Mechanism**: Distinguishes **Categories** (operational capabilities) from **Properties** (boolean mathematical truths like `IsAbelian`, `IsAssociative`). Method dispatch checks both.

### 2.5 Scala Spire / Typelevel Algebra
- **Source**: Spire Algebraic Hierarchy & Typelevel Algebra design.
- **Mechanism**: Solves the multiple-inheritance collision between additive and multiplicative monoids via parallel traits (`AdditiveMonoid`, `MultiplicativeMonoid`) and distinguishes `Ring` from `CommutativeRing` (`CRing`) via explicit commutative traits.

---

## 3. Empirical Verification: The Prototype Benchmark

To validate the failure mode and test the proposed solution, we authored [`sources/prototype_axioms.py`](./sources/prototype_axioms.py) and executed it:

```text
=== EXP-0008 Empirical Demonstration ===

1. Baseline Structural Subtyping (Status Quo):
   isinstance(so3, BaselineMalcevAlgebra):     True (Expected True)
   isinstance(so3, BaselineJordanAlgebra):     True (ERROR: False Positive! Lie != Jordan)
   isinstance(so3, BaselineAlternativeAlgebra):True (ERROR: False Positive! Lie != Alternative)

2. Proposed Axiom-Witness Subtyping (Pillars 2 & 3):
   isinstance(so3, ProposedMalcevAlgebra):     True (True)
   isinstance(so3, ProposedJordanAlgebra):     False (Correctly False!)
   isinstance(so3, ProposedAlternativeAlgebra):False (Correctly False!)
   isinstance(so3, LawAnticommutative):        True (True)
   isinstance(so3, LawCommutative):            False (Correctly False!)

3. Canonical Derived Operation in Action:
   so3.jacobian(e1, e2, e3): {} (Jacobi identity holds -> equals zero!)
```

The experiment confirmed:
1. Pure signature subtyping leads to blatant mathematical falsehoods at runtime (`isinstance(so3, JordanAlgebra) == True`).
2. Law witness mixins with `Literal[True]` completely eliminate false-positive collisions.
3. Concrete classes inherit these witnesses and canonical derived operations from their Layer 2 protocol with **zero boilerplate**.

---

## 4. The 3-Pillar Unified Architecture for AlgebraX

We propose formalizing the relationship between Signature ($\Sigma$) and Equational Theory ($E$) via a **Three-Pillar Synthesis**:

```text
                       Layer 2 Named Protocol
                    (e.g., JordanAlgebra[R, M])
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
   [Pillar 1]            [Pillar 2]            [Pillar 3]
Atomic Operational    Layer 1 Law Witness   Canonical Derived
   Capabilities             Mixins              Operations
(HasScale, HasZero,   (LawCommutative,      (jordan_triple,
 HasAdd, HasNeg,      LawJordan)            quadratic_repr)
 HasMul)
```

### Pillar 1: Layer 1 Operational Capabilities ($\Sigma$)
Retains all existing atomic operational mixins in `algebrax.algebra._mixins`:
- `HasZero[V]`, `HasOne[V]`, `HasAdd[V]`, `HasNeg[V]`, `HasMul[V]`, `HasInv[V]`, `HasScale[R, M]`, `HasBracket[V]`.

### Pillar 2: Layer 1 Law Witness Mixins ($E$)
Introduces formal, lightweight law witness protocols in `algebrax.algebra._mixins`:
- `LawCommutative`: `@property def is_commutative(self) -> Literal[True]: ...`
- `LawAnticommutative`: `@property def is_anticommutative(self) -> Literal[True]: ...`
- `LawAssociative`: `@property def is_associative(self) -> Literal[True]: ...`
- `LawJordan`: `@property def is_jordan(self) -> Literal[True]: ...`
- `LawAlternative`: `@property def is_alternative(self) -> Literal[True]: ...`
- `LawMalcev`: `@property def is_malcev(self) -> Literal[True]: ...`
- `LawLie`: `@property def is_lie(self) -> Literal[True]: ...`

**Zero Boilerplate Rule**:
Every Layer 2 Named Protocol provides the default concrete property implementation:
```python
@runtime_checkable
class JordanAlgebra(
    HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M],
    LawCommutative, LawJordan,
    Protocol[R, M],
):
    @property
    def is_commutative(self) -> Literal[True]:
        return True

    @property
    def is_jordan(self) -> Literal[True]:
        return True
```
Because EP-0194 mandates that concrete Layer 3 classes nominally inherit from their Layer 2 protocol (`class SymmetricMatrixJordanAlgebra(JordanAlgebra[...]):`), all concrete classes satisfy these law witnesses automatically with **zero lines of extra code**.

### Pillar 3: Canonical Characteristic Operations
Structures that possess unique canonical operations derived from their equational theory must expose them directly on the protocol with default implementations:
- `AlternativeAlgebra`: Exposes `associator(x, y, z) -> M = (xy)z - x(yz)`.
- `JordanAlgebra`: Exposes `jordan_triple(x, y, z) -> M = (xy)z + x(yz) - y(xz)` and `quadratic_repr(x, y) -> M = 2x(xy) - x^2 y`.
- `MalcevAlgebra`: Exposes `jacobian(x, y, z) -> M = [[x, y], z] + [[y, z], x] + [[z, x], y]`.

---

## 5. Architectural Alignment & Constraints

1. **EP-0194 Compliance (Law of Flat Protocol Composition)**:
   - Layer 1 Law Mixins are pure Layer 1 mixins (they inherit only from `Protocol`).
   - Layer 2 Named Protocols inherit *only* from Layer 1 Operational Mixins, Layer 1 Law Mixins, and `Protocol`.
   - **No Layer 2 diamond inheritance is introduced**.
2. **Shannon Efficiency & Unboxed Carriers**:
   - Zero wrapper objects, zero heap boxing.
   - Law witnesses are purely virtual properties or class attributes resolved in nanoseconds.
3. **Russell Deductive Order**:
   - Eliminates ambiguity. A Lie algebra can never masquerade as a Jordan algebra, neither statically in IDEs nor dynamically in runtime dispatch.
4. **Popper Falsifiability**:
   - Directly links to `algebrax.verification`: property-based test suites can inspect `isinstance(obj, LawJordan)` to automatically dispatch the exact right verification suite (`verify_jordan_laws`).

---

## 6. Actionable Verdict & Standards Track Roadmap

1. **Compendium Concluded**: The architectural design is verified, prototyped, and archived with primary literature in `references/explorations/EXP-0008-equational-theories-and-typeclass-axioms/`.
2. **Proposed Standards Track EP**:
   - Author **EP-0216: Law Witness Mixins & Equational Protocol Differentiation**.
   - Scope: Update `_mixins.py`, `_ring.py`, `_group.py`, and `_non_assoc.py` with Pillar 2 and Pillar 3, while preserving 100% backward compatibility for all existing algorithms and carrier data.
