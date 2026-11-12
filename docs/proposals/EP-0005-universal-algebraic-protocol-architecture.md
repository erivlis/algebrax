---
title: "EP-0005: Universal Algebraic Protocol Architecture — Capabilities, Law Witnesses & Canonical Operations"
description: "Establishes the 3-pillar algebraic protocol architecture in AlgebraX: Layer 1 Operational Mixins (Has*), Layer 1 Law Witness Mixins (Law*), Layer 2 Flat Protocols, and Characteristic Derived Methods, resolving signature vs. equational theory blindness."
icon: lucide/layers
status: draft
---

# EP-0005: Universal Algebraic Protocol Architecture — Capabilities, Law Witnesses & Canonical Operations

| Field             | Value                                                                                                                     |
|:------------------|:--------------------------------------------------------------------------------------------------------------------------|
| **EP**            | 0005                                                                                                                      |
| **Title**         | Universal Algebraic Protocol Architecture — Capabilities, Law Witnesses & Canonical Operations                             |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                                               |
| **Sponsor**       | The Grand Council                                                                                                         |
| **Delegate**      | 🧩 Bertrand Russell (Type Theory & Deductive Order) & ⚖️ Emmy Noether (Symmetries & Invariants)                            |
| **Status**        | Draft                                                                                                                     |
| **Type**          | Standards Track                                                                                                           |
| **Created**       | 2026-11-12                                                                                                                |
| **Updated**       | 2026-11-12                                                                                                                |
| **Replaces**      | [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md)                                                    |
| **Superseded-By** | —                                                                                                                         |

---

## Abstract

This proposal establishes the permanent, constitutional **Universal Algebraic Protocol Architecture** across `algebrax.algebra`. It reconciles abstract algebra's classical dual nature—the **Signature** $\Sigma$ (operations and arities) versus the **Equational Theory** $E$ (axioms and laws)—within Python's structural typing system (`typing.Protocol` and `@runtime_checkable`).

Synthesizing [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md) and the empirical findings of EXP-0008 (`references/explorations/EXP-0008-equational-theories-and-typeclass-axioms/`), this architecture formalizes three interconnected pillars:

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

1. **Pillar 1: Layer 1 Operational Capabilities ($\Sigma$)**: Diamond-free atomic mixins (`HasZero`, `HasAdd`, `HasNeg`, `HasMul`, `HasScale`, `HasBracket`) defining syntactic operations and derived generators (`sub`, `div`, `is_zero`).
2. **Pillar 2: Layer 1 Law Witness Mixins ($E$)**: Zero-runtime-cost marker protocols (`LawCommutative`, `LawAnticommutative`, `LawAssociative`, `LawJordan`, `LawAlternative`, `LawMalcev`) with `@property def is_...() -> Literal[True]: return True` default implementations on Layer 2 protocols. This resolves the long-standing "algebraic isomer" blindness where `isinstance(so3, JordanAlgebra)` falsely evaluated to `True`.
3. **Pillar 3: Canonical Characteristic Operations**: Equipping specialized algebras with intrinsic mathematical operators derived directly from their axioms (`associator` on `AlternativeAlgebra`, `jordan_triple` and `quadratic_repr` on `JordanAlgebra`, `jacobian` on `MalcevAlgebra`).

This proposal formally supersedes and canonizes [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md) into the single-digit foundational canon.

---

## Motivation

In Universal Algebra (Birkhoff's variety theorem), an algebraic variety $\mathcal{V} = (\Sigma, E)$ requires both its operations $\Sigma$ and its identities $E$.

In [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md), AlgebraX established the **Law of Flat Protocol Composition**, eliminating deep inheritance diamonds by composing Layer 2 protocols from Layer 1 mixins. While this solved operational MRO diamonds, it left the **Equational Theory ($E$)** unrepresented in the type system:

1. **The Algebraic Isomer Dilemma**:
   `JordanAlgebra`, `AlternativeAlgebra`, and `MalcevAlgebra` all inherited identical bases:
   `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M])`.
   Similarly, `Ring`, `CommRing`, and `NonAssocRing` shared identical operational signatures.
2. **False-Positive Runtime Collisions**:
   Because `@runtime_checkable` inspects only method names, `isinstance(so_n(3), JordanAlgebra)` evaluated to **`True`** at runtime, conflating an anticommutative Lie algebra $[x, y] = -[y, x]$ with a commutative quantum observable algebra $x \circ y = y \circ x$ satisfying $(x \circ y) \circ x^2 = x \circ (y \circ x^2)$.
3. **Static Type Indistinguishability**:
   Type checkers (`mypy`, `pyright`) treated these distinct mathematical varieties as interchangeable structural types.
4. **Missing Canonical Computational Operators**:
   A user working with an alternative algebra had no direct `associator(x, y, z)` method on the protocol, and a user working with a Jordan algebra had no `jordan_triple(x, y, z)` or quadratic representation $U_x(y)$ operator.

---

## Rationale & Council Alignment

- **🧩 Bertrand Russell (Deductive Soundness & The Theory of Types)**:
  Aligns with Lean 4 Mathlib's `Prop`-valued typeclasses (Baanen 2022) and Axiom's category attributes. Preserves the **Law of Flat Protocol Composition**: Layer 1 Law Mixins inherit only from `Protocol`. Layer 2 Named Protocols inherit only from Layer 1 Mixins and `Protocol`. **Zero diamond inheritance is introduced**.
- **⚖️ Emmy Noether (Symmetry & Invariants)**:
  Restores the algebraic symmetries that govern physical conservation laws. Anticommutativity ($[x, y] = -[y, x]$) and commutativity ($x \circ y = y \circ x$) are now formally distinguishable in the type system.
- **⚡ Claude Shannon (Zero Overhead & Native Carrier Invariance)**:
  Law witnesses are pure virtual properties returning `Literal[True]`. They introduce **zero memory allocations, zero boxing of scalars, and zero wrapper classes**. Concrete Layer 3 classes inherit them statically with **zero extra lines of code**.
- **🔬 Karl Popper (Falsifiability & Automated Oracles)**:
  Bridges directly to `algebrax.verification`: a generic verification runner can inspect `isinstance(struct, LawJordan)` to automatically dispatch `verify_jordan_laws`.
- **💡 Richard Feynman (The Freshman Test & Educational Clarity)**:
  Canonical derived operations (`associator`, `jordan_triple`, `jacobian`) provide immediate pedagogical and practical utility: students and scientists can compute the associator or Jordan triple product directly without manual parenthesis tracking.

---

## Specification

### 1. Pillar 1: Layer 1 Atomic Operational Mixins (`src/algebrax/algebra/_mixins.py`)

Retains all orthogonal single-principle capabilities:
- `HasZero[V]`: `@property def zero(self) -> V: ...`
- `HasZeroPred[V]`: `def is_zero(self, a: V) -> bool: ...` (derived generator from `zero`)
- `HasOne[V]`: `@property def one(self) -> V: ...`
- `HasAdd[V]`: `def add(self, a: V, b: V) -> V: ...`
- `HasNeg[V]`: `def neg(self, a: V) -> V: ...` (with derived generator `def sub(self, a: V, b: V) -> V: return self.add(a, self.neg(b))`)
- `HasMul[V]`: `def mul(self, a: V, b: V) -> V: ...`
- `HasInv[V]`: `def inv(self, a: V) -> V: ...` (with derived generator `def div(self, a: V, b: V) -> V: return self.mul(a, self.inv(b))`)
- `HasScale[R, M]`: `def smul(self, r: R, m: M) -> M: ...` (aliased as `HasSMul`)
- `HasStar[V]`: `def star(self, a: V) -> V: ...`
- `HasBracket[V]`: `def bracket(self, a: V, b: V) -> V: ...`
- `HasJoin[V]`, `HasMeet[V]`, `HasBounds[V]`, `HasComplement[V]`, `HasOp[V]`, `HasIdentity[V]`.

---

### 2. Pillar 2: Layer 1 Law Witness Mixins (`src/algebrax/algebra/_mixins.py`)

Equational laws are modeled as lightweight, runtime-checkable protocols:

```python
from typing import Literal, Protocol, runtime_checkable

@runtime_checkable
class LawCommutative(Protocol):
    r"""Equational axiom witness: binary multiplication is commutative ($a \cdot b = b \cdot a$)."""
    @property
    def is_commutative(self) -> Literal[True]: ...

@runtime_checkable
class LawAnticommutative(Protocol):
    r"""Equational axiom witness: binary operation is skew-symmetric ($[a, b] = -[b, a]$)."""
    @property
    def is_anticommutative(self) -> Literal[True]: ...

@runtime_checkable
class LawAssociative(Protocol):
    r"""Equational axiom witness: binary multiplication is associative ($(a \cdot b) \cdot c = a \cdot (b \cdot c)$)."""
    @property
    def is_associative(self) -> Literal[True]: ...

@runtime_checkable
class LawJordan(Protocol):
    r"""Equational axiom witness: satisfies Jordan identity ($(a \circ b) \circ a^2 = a \circ (b \circ a^2)$)."""
    @property
    def is_jordan(self) -> Literal[True]: ...

@runtime_checkable
class LawAlternative(Protocol):
    r"""Equational axiom witness: satisfies Artin alternativity ($(a \cdot a) \cdot b = a \cdot (a \cdot b)$ and $(b \cdot a) \cdot a = b \cdot (a \cdot a)$)."""
    @property
    def is_alternative(self) -> Literal[True]: ...

@runtime_checkable
class LawMalcev(Protocol):
    r"""Equational axiom witness: satisfies Malcev identity ($J(x, y, [x, z]) = [J(x, y, z), x]$)."""
    @property
    def is_malcev(self) -> Literal[True]: ...

@runtime_checkable
class LawLie(Protocol):
    r"""Equational axiom witness: satisfies Jacobi identity ($[[x, y], z] + [[y, z], x] + [[z, x], y] = \mathbf{0}$)."""
    @property
    def is_lie(self) -> Literal[True]: ...
```

---

### 3. Pillar 3: Flat Layer 2 Protocol Composition with Canonical Derived Operations

Layer 2 Named Protocols compose Layer 1 Operational Mixins and Layer 1 Law Witness Mixins, providing default property witnesses and canonical derived operators:

#### 3.1 Non-Associative & Quantum Algebras (`_non_assoc.py`)
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

    def jordan_triple(self, x: M, y: M, z: M) -> M:
        r"""Jordan triple product $\{x, y, z\} = (x \circ y) \circ z + x \circ (y \circ z) - y \circ (x \circ z)$."""
        xy_z = self.mul(self.mul(x, y), z)
        x_yz = self.mul(x, self.mul(y, z))
        y_xz = self.mul(y, self.mul(x, z))
        return self.add(self.add(xy_z, x_yz), self.neg(y_xz))

    def quadratic_repr(self, x: M, y: M) -> M:
        r"""Quadratic representation operator $U_x(y) = 2 x \circ (x \circ y) - x^2 \circ y$."""
        x_xy = self.mul(x, self.mul(x, y))
        two_x_xy = self.add(x_xy, x_xy)
        x2_y = self.mul(self.mul(x, x), y)
        return self.add(two_x_xy, self.neg(x2_y))


@runtime_checkable
class AlternativeAlgebra(
    HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M],
    LawAlternative,
    Protocol[R, M],
):
    @property
    def is_alternative(self) -> Literal[True]:
        return True

    def associator(self, x: M, y: M, z: M) -> M:
        r"""Associator $[x, y, z] = (x \cdot y) \cdot z - x \cdot (y \cdot z)$."""
        xy_z = self.mul(self.mul(x, y), z)
        x_yz = self.mul(x, self.mul(y, z))
        return self.add(xy_z, self.neg(x_yz))


@runtime_checkable
class MalcevAlgebra(
    HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M],
    LawAnticommutative, LawMalcev,
    Protocol[R, M],
):
    @property
    def is_anticommutative(self) -> Literal[True]:
        return True

    @property
    def is_malcev(self) -> Literal[True]:
        return True

    def jacobian(self, x: M, y: M, z: M) -> M:
        r"""Jacobian operator $J(x, y, z) = [[x, y], z] + [[y, z], x] + [[z, x], y]$."""
        xy_z = self.mul(self.mul(x, y), z)
        yz_x = self.mul(self.mul(y, z), x)
        zx_y = self.mul(self.mul(z, x), y)
        return self.add(self.add(xy_z, yz_x), zx_y)
```

#### 3.2 Rings & Commutative Rings (`_ring.py`)
```python
@runtime_checkable
class Ring(
    HasZero[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V],
    LawAssociative,
    Protocol[V],
):
    @property
    def is_associative(self) -> Literal[True]:
        return True


@runtime_checkable
class CommRing(
    HasZero[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V],
    LawAssociative, LawCommutative,
    Protocol[V],
):
    @property
    def is_associative(self) -> Literal[True]:
        return True

    @property
    def is_commutative(self) -> Literal[True]:
        return True
```

---

### 4. Zero Boilerplate for Layer 3 Concrete Implementations

Because concrete Layer 3 classes nominally inherit from their primary Layer 2 protocol (as required by EP-0194):
```python
class SymmetricMatrixJordanAlgebra(JordanAlgebra[float, SparseMatrix[Any, float]]):
    ...
```
`SymmetricMatrixJordanAlgebra` automatically inherits `is_commutative = True`, `is_jordan = True`, `jordan_triple(...)`, and `quadratic_repr(...)` **with zero lines of extra code**.

At runtime:
```python
jordan = SymmetricMatrixJordanAlgebra()
assert isinstance(jordan, JordanAlgebra)
assert isinstance(jordan, LawJordan)
assert isinstance(jordan, LawCommutative)

lie_so3 = so_n(3)
assert isinstance(lie_so3, MalcevAlgebra)
assert not isinstance(lie_so3, JordanAlgebra)  # Correctly False!
assert not isinstance(lie_so3, LawCommutative) # Correctly False!
```

---

### 5. Multi-Sorted Parameter Ordering Constraint

All two-sorted protocols (`Semimodule`, `Module`, `VectorSpace`, `NonAssocAlgebra`, `JordanAlgebra`, `AlternativeAlgebra`, `MalcevAlgebra`, `PoissonAlgebra`, `Algebra`) must place `HasScale[R, M]` first in their base tuple alongside explicit `Protocol[R, M]`. This guarantees that `cls.__parameters__` evaluates strictly to `(R, M)`:

```python
assert JordanAlgebra.__parameters__ == (R, M)
```

---

## Backwards Compatibility

1. **Non-Breaking Runtime Behavior**: Existing code calling `.zero`, `.add`, `.mul`, `.smul`, etc., continues to operate with identical semantics and performance.
2. **Replaces EP-0194**: All specifications from `EP-0194` (the Law of Flat Protocol Composition, atomic mixin definitions, and generic parameter ordering) are preserved and elevated to foundational canon status in `EP-0005`.

---

## How to Teach This / Documentation Plan

- **Guide Update**: `docs/guide/algebra/modules_and_vector_spaces.md` is updated to highlight the 3-pillar model (Capabilities, Law Witnesses, and Canonical Operations).
- **Interactive Verification**: Property tests and notebook tutorials demonstrate how `isinstance(obj, LawJordan)` enables automated verification dispatch.

---

## Reference Implementation

- **Research Compendium & Prototype**: `references/explorations/EXP-0008-equational-theories-and-typeclass-axioms/README.md` and `references/explorations/EXP-0008-equational-theories-and-typeclass-axioms/sources/prototype_axioms.py`.
- **Core Modules**: `src/algebrax/algebra/_mixins.py`, `_non_assoc.py`, `_ring.py`, `_group.py`.
- **Precedent Proposal**: [`docs/proposals/EP-0194-atomic-algebraic-mixins-and-protocol-composition.md`](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md).

---

## Rejected Ideas

1. **Relying Exclusively on Docstrings for Mathematical Axioms**:
   *Rejected*: Leaves static type checkers and `@runtime_checkable` blind to equational identities, leading to false-positive collisions (`isinstance(so3, JordanAlgebra) == True`).
2. **Deep Chained Nominal Protocol Inheritance**:
   *Rejected*: Introduces exponential MRO diamonds and inter-module coupling. The Law of Flat Protocol Composition is non-negotiable.
3. **Heavy Runtime Proof Objects**:
   *Rejected*: Storing proof instances or AST objects at runtime violates the Shannon Zero-Overhead Carrier Invariant. Marker properties returning `Literal[True]` resolve in nanoseconds with zero heap allocation.

---

## Open Questions

None. The prototype has been verified, benchmarked, and reviewed by the Grand Council in EXP-0008.

---

## Change Log

- **2026-11-01**: Authored initial flat mixin composition proposal as EP-0194.
- **2026-11-12**: Unified with EXP-0008 findings (Law Witnesses & Canonical Operations) and elevated to foundational canon as EP-0005.
