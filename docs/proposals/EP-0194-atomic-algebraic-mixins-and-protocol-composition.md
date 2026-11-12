---
title: "EP-0194: Atomic Algebraic Mixins & Diamond-Free Protocol Composition"
description: "Refactor the algebraic protocol hierarchy from deep diamond inheritance chains into orthogonal atomic operational mixins composed into flat named algebraic protocols."
icon: lucide/layers
status: final
---

# EP-0194: Atomic Algebraic Mixins & Diamond-Free Protocol Composition

| Field | Value |
| :--- | :--- |
| **EP** | 0194 |
| **Title** | Atomic Algebraic Mixins & Diamond-Free Protocol Composition |
| **Author** | Eran Rivlis <eran@rivlis.info>, Antigravity |
| **Sponsor** | Council Framework |
| **Delegate** | 🧩 Russell (Taxonomy & Type Theory) & ⚖️ Noether (Algebraic Invariants) |
| **Status** | Superseded |
| **Type** | Standards Track |
| **Created** | 2026-11-01 |
| **Updated** | 2026-11-12 |
| **Replaces** | — |
| **Superseded-By** | [EP-0005](EP-0005-universal-algebraic-protocol-architecture.md) |

## Abstract

This proposal refactors the protocol architecture in `algebrax.algebra` (established in [EP-0190](EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md) and [EP-0191](EP-0191-rings-fields-modules-and-exact-solvers.md)) to eliminate deep inheritance chaining and diamond inheritance graphs. By separating **Atomic Operational Mixins** (`HasZero`, `HasZeroPred`, `HasOne`, `HasAdd`, `HasNeg`, `HasMul`, `HasInv`, `HasScale` / `HasSMul`, `HasStar`, `HasJoin`, `HasMeet`, `HasBounds`, `HasComplement`, `HasOp`, `HasIdentity`, `HasBracket`) from **Named Algebraic Protocols** (`Monoid`, `Group`, `Semiring`, `Ring`, `Field`, `Module`, `Algebra`, `Lattice`), every named algebraic protocol becomes a flat, depth-2 composition of orthogonal primitives. Because Python's `@runtime_checkable` `Protocol` evaluates structural subtyping via attribute supersets (`__protocol_attrs__`), both runtime `isinstance()` checks and static type checking (`mypy` / `pyright` / `ty` / `pyrefly`) automatically preserve all mathematical subtyping relationships without diamond Method Resolution Orders (MROs).

Following unanimous Grand Council review (Noether, Russell, Popper, Shannon, The Golem, Feynman, The Explorer), this proposal enforces explicit `(R, M)` generic parameter ordering on two-sorted protocols, preserves zero-divisor predicates via `HasZeroPred`, keeps `__protocol_attrs__` strictly minimal for unboxed duck-typing, eliminates cross-module protocol imports, and establishes the permanent **Law of Flat Protocol Composition** for Phases 7 and 8.

## Motivation

In [EP-0190](EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md) and [EP-0191](EP-0191-rings-fields-modules-and-exact-solvers.md), algebraic protocols were chained nominally on top of one another (`Algebra -> NonAssocAlgebra -> Module -> Semimodule -> AddCommMonoid -> AddMonoid -> AddSemigroup -> AddMagma`). While mathematically intuitive at first glance, this nominal chaining conflated **reusable operational building blocks** with **named mathematical bundles**, producing three structural liabilities:

1. **Pervasive Diamond Inheritance**:
   - `Ring` inherits from `NonAssocRing[V]` and `Monoid[V]`, both of which independently inherit from `Magma[V]`.
   - `Field` inherits from `DivisionRing[V]` and `CommRing[V]`, both of which independently inherit from `Ring[V]`.
   - `Algebra` inherits from `NonAssocAlgebra[R, M]` and `Ring[M]`, both of which independently inherit from `NonAssocRing[M]` and `AddCommGroup[M]`.
   - `CommGroup` inherits from `Group[V]` and `CommMonoid[V]`, both of which inherit from `Monoid[V]`.
   - `BooleanAlgebra` inherits from `BoundedLattice[V]` and `DistributiveLattice[V]`, both of which inherit from `Lattice[V]`.

2. **Duplicated Derived Operations (`sub`, `div`, `is_zero`) & Inter-Module Coupling**:
   - Default derived operations like `div(a, b) = mul(a, inv(b))` were duplicated across `Group` (`_group.py`) and `DivisionRing` (`_ring.py`), while binary exponentiation (`nsum`, `power`) was duplicated verbatim between `Semiring` (`_semiring.py`) and `_helpers.py`.
   - Protocol modules formed a 5-deep import chain (`_module -> _ring -> _group -> _monoid -> _magma`).

3. **Obscured Signatures & Redundant `Protocol[V]` Boilerplate**:
   - Inspecting `class Algebra(NonAssocAlgebra[R, M], Ring[M], Protocol[R, M])` required tracing 8 classes across 4 files to discover the actual required methods (`zero`, `one`, `add`, `neg`, `sub`, `mul`, `smul`).
   - Every intermediate protocol repeated `Protocol[V]` or `Generic[V]` even when type parameters were already bound by parent bases.

### The Mental Model (The Periodic Table of Algebra)

Instead of a tangled family tree where every cousin marries back into the same ancestors, think of algebraic structures like **molecules assembled from atomic elements and functional groups**:

- **Elementary Atoms (Single-Operation Mixins)**: Each `Has*` protocol represents a single mathematical capability:
  - `HasZero` ($\mathbf{0}$), `HasOne` ($\mathbf{1}$), `HasAdd` ($+$), `HasMul` ($\cdot$), `HasScale` / `HasSMul` ($r \cdot m$), `HasStar` (Kleene $a^*$), `HasJoin` ($\vee$), `HasMeet` ($\wedge$), `HasBounds` ($\bot, \top$), `HasComplement` ($\neg$), `HasOp` ($\operatorname{op}$), `HasIdentity` ($\operatorname{id}$), `HasBracket` ($[\cdot, \cdot]$).
- **Bonded Functional Groups (Derived-Generator Mixins)**: Just as a hydroxyl group ($\text{-OH}$) in chemistry is a bonded pair, three mixins bundle an operation with its prerequisite so their derived operation comes for free:
  - `HasNeg(HasAdd[V], Protocol)`: Bundles `add` and `neg` ($-a$) with default subtraction `sub(a, b) = add(a, neg(b))`.
  - `HasInv(HasMul[V], Protocol)`: Bundles `mul` and `inv` ($a^{-1}$) with default division `div(a, b) = mul(a, inv(b))`.
  - `HasZeroPred(HasZero[V], Protocol)`: Bundles `zero` ($\mathbf{0}$) with default zero-test `is_zero(a) = (a == zero)` for division rings and fields.
- **Molecules & Structural Isomers (Named Algebraic Protocols)**:
  Every named protocol (`Monoid`, `Group`, `Semiring`, `Ring`, `Field`, `Module`, `Algebra`) is a flat formula of atoms and functional groups. When two named protocols share the exact same operational formula—such as `Ring[V]` and `CommRing[V]`, or `Magma[V]`, `Semigroup[V]`, and `Band[V]`—they are **algebraic isomers** (like graphite and diamond, both pure carbon): the *mixins* define the operational syntax (checked by `isinstance` and `mypy`), while the *named protocols* declare the mathematical laws (checked by `verify_*_laws`).

## Rationale & Council Alignment

- **🧩 Russell (Taxonomy & Type Theory)**: Aligns directly with Lean 4 Mathlib's unbundled operational typeclasses (`Zero`, `One`, `Add`, `Neg`, `Sub`, `Mul`, `Inv`, `Div`, `SMul`). Eliminates all diamond MRO paths across `algebrax.algebra` while preserving 100% of the named mathematical protocols, including the domain-agnostic `Op*` branch, `Quasigroup`, and `GroupAction`.
- **⚖️ Noether (Algebraic Invariants & Duality)**: Places derived operations (`sub`, `div`, `is_zero`) on their exact algebraic symmetry generators: additive inversion generates subtraction (`HasNeg.sub`), multiplicative inversion generates division (`HasInv.div`), and additive identity generates zero-testing (`HasZeroPred.is_zero`).
- **🔬 Popper (Falsifiability & `__protocol_attrs__` Minimality)**: Protects unboxed duck-typing by keeping `HasZero`, `HasOne`, `HasAdd`, and `HasMul` strictly minimal (`{'zero'}`, `{'one'}`, `{'add'}`, `{'mul'}`). Standalone polymorphic algorithms (`nsum`, `zsmul`, `power`, `zpow`, `fold_*`) remain in `algebrax.algebra._helpers` so duck-typed `Monoid`, `Group`, and `Ring` classes do not need to implement `.power()` or `.nsum()` to satisfy `isinstance()`.
- **⚡ Shannon (Information Density & Dependency Flattening)**: Flattens MRO depth from 8 levels to 2 levels and drops the internal protocol import graph depth from 5 to 1 (every protocol module imports exclusively from `_mixins.py`). Deduplicates `Semiring.nsum` and `Semiring.power` by delegating directly to `_helpers.py`.
- **🛡️ The Golem (Runtime & Static Subtyping Invariants)**: Enforces `HasScale[R, M]` as the first base class alongside explicit `Protocol[R, M]` on all two-sorted protocols (`Semimodule`, `Module`, `VectorSpace`, `NonAssocAlgebra`, `Algebra`) so `cls.__parameters__` is strictly locked to `(R, M)` rather than inverted to `(M, R)`.
- **💡 Feynman (Self-Documenting Clarity)**: Every named protocol declaration reads identically to its formal mathematical tuple $\langle S, +, \cdot, \mathbf{0}, \mathbf{1} \rangle$, and `HasSMul` is provided as an exact alias for `HasScale` to match the `.smul()` method name.
- **🧭 The Explorer (Frontier Synthesis)**: Establishes the **Law of Flat Protocol Composition** and introduces `HasBracket[V]`, preventing multi-diamond explosions in Phase 7 & 8 structures (`PoissonAlgebra`, `Bialgebra`, `HopfAlgebra`, `NormedSpace`).

## Specification

### 1. Layer 1: Atomic Operational Mixins (`src/algebrax/algebra/_mixins.py`)

A new foundational module `_mixins.py` defines all orthogonal single-operation atoms and bonded functional groups:

```python
from typing import Protocol, TypeVar, runtime_checkable

V = TypeVar('V')
R = TypeVar('R')
M = TypeVar('M')


@runtime_checkable
class HasZero(Protocol[V]):
    r"""Additive neutral element $\mathbf{0}$.

    Algebraic Signature:
        $\langle V, \mathbf{0} \rangle$
    """

    @property
    def zero(self) -> V: ...


@runtime_checkable
class HasZeroPred(Protocol[V]):
    r"""Zero-divisor predicate `is_zero(a)` testing whether an element equals $\mathbf{0}$.

    Algebraic Signature:
        $\langle V, \operatorname{is\_zero} \rangle$
    """

    def is_zero(self, a: V) -> bool:
        """Return True if element is the additive zero."""
        return a == self.zero  # type: ignore[attr-defined]


@runtime_checkable
class HasOne(Protocol[V]):
    r"""Multiplicative neutral element $\mathbf{1}$.

    Algebraic Signature:
        $\langle V, \mathbf{1} \rangle$
    """

    @property
    def one(self) -> V: ...


@runtime_checkable
class HasAdd(Protocol[V]):
    r"""Binary addition operation $+: V \times V \to V$.

    Algebraic Signature:
        $\langle V, + \rangle$
    """

    def add(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasNeg(Protocol[V]):
    r"""Additive inverse $-: V \to V$ and derived subtraction $a - b = a + (-b)$.

    Algebraic Signature:
        $\langle V, - \rangle$
    """

    def neg(self, a: V) -> V: ...

    def sub(self, a: V, b: V) -> V:
        """Difference a - b = a + neg(b)."""
        return self.add(a, self.neg(b))  # type: ignore[attr-defined]


@runtime_checkable
class HasMul(Protocol[V]):
    r"""Binary multiplication operation $\cdot: V \times V \to V$.

    Algebraic Signature:
        $\langle V, \cdot \rangle$
    """

    def mul(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasInv(Protocol[V]):
    r"""Multiplicative inverse $^{-1}: V \to V$ and derived quotient $a / b = a \cdot b^{-1}$.

    Algebraic Signature:
        $\langle V, ^{-1} \rangle$
    """

    def inv(self, a: V) -> V: ...

    def div(self, a: V, b: V) -> V:
        """Quotient a / b = a * inv(b)."""
        return self.mul(a, self.inv(b))  # type: ignore[attr-defined]


@runtime_checkable
class HasScale(Protocol[R, M]):
    r"""External scalar multiplication $\cdot: R \times M \to M$.

    Algebraic Signature:
        $\langle M, R, \cdot \rangle$
    """

    def smul(self, r: R, m: M) -> M: ...


HasSMul = HasScale  # Canonical Mathlib-aligned alias matching .smul()


@runtime_checkable
class HasStar(Protocol[V]):
    r"""Kleene closure operation $a^* = \mathbf{1} \oplus a \oplus a^2 \oplus \cdots$.

    Note: Denotes idempotent/convergent Kleene star closure in semirings and automata,
    distinct from involutive conjugate/adjoint operations ($a^\dagger$) in $^*$-algebras.

    Algebraic Signature:
        $\langle V, ^* \rangle$
    """

    def star(self, a: V) -> V: ...


@runtime_checkable
class HasJoin(Protocol[V]):
    r"""Lattice least upper bound (join) $\vee: V \times V \to V$.

    Algebraic Signature:
        $\langle L, \vee \rangle$
    """

    def join(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasMeet(Protocol[V]):
    r"""Lattice greatest lower bound (meet) $\wedge: V \times V \to V$.

    Algebraic Signature:
        $\langle L, \wedge \rangle$
    """

    def meet(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasBounds(Protocol[V]):
    r"""Lattice bottom ($\bot$) and top ($\top$) bounds.

    Algebraic Signature:
        $\langle L, \bot, \top \rangle$
    """

    @property
    def bot(self) -> V: ...

    @property
    def top(self) -> V: ...


@runtime_checkable
class HasComplement(Protocol[V]):
    r"""Unary lattice complement $\neg: V \to V$.

    Algebraic Signature:
        $\langle B, \neg \rangle$
    """

    def complement(self, a: V) -> V: ...


@runtime_checkable
class HasOp(Protocol[V]):
    r"""Domain-agnostic binary operation $\operatorname{op}: V \times V \to V$.

    Algebraic Signature:
        $\langle M, \operatorname{op} \rangle$
    """

    def op(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasIdentity(Protocol[V]):
    r"""Domain-agnostic neutral identity element.

    Algebraic Signature:
        $\langle M, \operatorname{identity} \rangle$
    """

    @property
    def identity(self) -> V: ...


@runtime_checkable
class HasBracket(Protocol[V]):
    r"""Bilinear bracket operation $[\cdot, \cdot]: V \times V \to V$.

    Algebraic Signature:
        $\langle \mathfrak{g}, [\cdot, \cdot] \rangle$
    """

    def bracket(self, a: V, b: V) -> V: ...
```

> [!IMPORTANT]
> **Purely Orthogonal Mixins (Zero Mixin-to-Mixin Inheritance)**:
> Every `Has*` mixin in `_mixins.py` inherits **directly and exclusively** from `Protocol`. Neither `HasNeg`, `HasInv`, nor `HasZeroPred` inherits from `HasAdd`, `HasMul`, or `HasZero`. Consequently, every Named Protocol explicitly lists all of its constituent operational mixins in its class declaration (e.g., `Group(HasOne[V], HasMul[V], HasInv[V], Protocol)`), making every class header 100% self-documenting and mathematically transparent while guaranteeing zero diamond inheritance by construction.

---

### 2. Layer 2: Flat Named Algebraic Protocols

Every named algebraic protocol is composed directly from the orthogonal mixins in `_mixins.py` with **zero imports between named protocol modules**:

| Named Protocol | Flat Mixin Composition | Mixin-Aligned Algebraic Signature |
| :--- | :--- | :--- |
| **`Magma[V]`** / **`Semigroup[V]`** / **`Band[V]`** | `(HasMul[V], Protocol)` | $\langle V, \cdot \rangle$ |
| **`Quasigroup[V]`** | `(HasMul[V], Protocol)` (+ `ldiv`, `rdiv`) | $\langle V, \cdot, \backslash, / \rangle$ |
| **`AddMagma[V]`** / **`AddSemigroup[V]`** | `(HasAdd[V], Protocol)` | $\langle V, + \rangle$ |
| **`OpMagma[V]`** / **`OpSemigroup[V]`** | `(HasOp[V], Protocol)` | $\langle V, \operatorname{op} \rangle$ |
| **`Monoid[V]`** / **`CommMonoid[V]`** | `(HasOne[V], HasMul[V], Protocol)` | $\langle V, \mathbf{1}, \cdot \rangle$ |
| **`AddMonoid[V]`** / **`AddCommMonoid[V]`** | `(HasZero[V], HasAdd[V], Protocol)` | $\langle V, \mathbf{0}, + \rangle$ |
| **`OpMonoid[V]`** / **`OpCommMonoid[V]`** | `(HasIdentity[V], HasOp[V], Protocol)` | $\langle V, \operatorname{identity}, \operatorname{op} \rangle$ |
| **`Group[V]`** / **`CommGroup[V]`** | `(HasOne[V], HasMul[V], HasInv[V], Protocol)` | $\langle V, \mathbf{1}, \cdot, ^{-1} \rangle$ |
| **`AddGroup[V]`** / **`AddCommGroup[V]`** | `(HasZero[V], HasAdd[V], HasNeg[V], Protocol)` | $\langle V, \mathbf{0}, +, - \rangle$ |
| **`GroupAction[G, X]`** | `(Protocol[G, X])` (+ `gact`) | $\langle G, X, \operatorname{gact} \rangle$ |
| **`Semiring[V]`** | `(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], Protocol)` | $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$ |
| **`NonAssocRing[V]`** | `(HasZero[V], HasAdd[V], HasNeg[V], HasMul[V], Protocol)` | $\langle V, \mathbf{0}, +, -, \cdot \rangle$ |
| **`Ring[V]`** / **`CommRing[V]`** | `(HasZero[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], Protocol)` | $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ |
| **`DivisionRing[V]`** / **`Field[V]`** | `(HasZero[V], HasZeroPred[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], HasInv[V], Protocol)` | $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, ^{-1} \rangle$ |
| **`Semimodule[R, M]`** | `(HasScale[R, M], HasZero[M], HasAdd[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, + \rangle$ |
| **`Module[R, M]`** / **`VectorSpace[R, M]`** | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, - \rangle$ |
| **`NonAssocAlgebra[R, M]`** | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$ |
| **`Algebra[R, M]`** | `(HasScale[R, M], HasZero[M], HasAdd[M], HasNeg[M], HasOne[M], HasMul[M], Protocol[R, M])` | $\langle R, M, \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ |
| **`JoinSemilattice[V]`** | `(HasJoin[V], Protocol)` | $\langle V, \vee \rangle$ |
| **`MeetSemilattice[V]`** | `(HasMeet[V], Protocol)` | $\langle V, \wedge \rangle$ |
| **`Lattice[V]`** / **`DistributiveLattice[V]`** | `(HasJoin[V], HasMeet[V], Protocol)` | $\langle V, \vee, \wedge \rangle$ |
| **`BoundedLattice[V]`** | `(HasJoin[V], HasMeet[V], HasBounds[V], Protocol)` | $\langle V, \vee, \wedge, \bot, \top \rangle$ |
| **`BooleanAlgebra[V]`** | `(HasJoin[V], HasMeet[V], HasBounds[V], HasComplement[V], Protocol)` | $\langle V, \vee, \wedge, \bot, \top, \neg \rangle$ |

> [!CAUTION]
> **Two-Sorted Generic Parameter Order (`[R, M]`)**:
> On `Semimodule[R, M]`, `Module[R, M]`, `VectorSpace[R, M]`, `NonAssocAlgebra[R, M]`, and `Algebra[R, M]`, `HasScale[R, M]` **must** appear first in the base list and `Protocol[R, M]` must be explicitly subscripted. Otherwise, if `HasZero[M]` appeared before `HasScale[R, M]` with unsubscripted `Protocol`, Python's `Generic` metaclass would collect `TypeVar` parameters in order of first appearance as `(M, R)`, inverting the scalar ring type `R` and carrier type `M`!

---

### 3. Verification of Diamond-Free MRO & `_helpers.py` Delegation

1. **Zero Duplicate MRO Paths**:
   Every protocol in `algebrax.algebra` has a strictly flat, depth-2 MRO of orthogonal mixins ordered by **Additive cluster $\to$ Multiplicative cluster $\to$ Closure/Bounds**:
   - **`Group.mro()`**:
     `[Group, HasOne, HasMul, HasInv, Protocol, Generic, object]`
   - **`Algebra.mro()`**:
     `[Algebra, HasScale, HasZero, HasAdd, HasNeg, HasOne, HasMul, Protocol, Generic, object]`
   - **`Field.mro()`**:
     `[Field, HasZero, HasZeroPred, HasAdd, HasNeg, HasOne, HasMul, HasInv, Protocol, Generic, object]`
   - **`BooleanAlgebra.mro()`**:
     `[BooleanAlgebra, HasJoin, HasMeet, HasBounds, HasComplement, Protocol, Generic, object]`

2. **Deduplication of `Semiring.nsum` and `Semiring.power`**:
   In `src/algebrax/algebra/_semiring.py`, `Semiring.nsum(self, a: V, n: int) -> V` and `Semiring.power(self, a: V, n: int) -> V` delegate directly to `nsum(self, a, n)` and `power(self, a, n)` in `src/algebrax/algebra/_helpers.py`, eliminating 40 lines of duplicated binary exponentiation loops while keeping `HasZero`, `HasOne`, `HasAdd`, and `HasMul` free of extra `__protocol_attrs__` methods.

---

### 4. Preservation of Structural Subtyping (`isinstance` and Static Typing)

Because Python's `@runtime_checkable` `_ProtocolMeta.__instancecheck__` verifies whether an instance provides all attributes in `cls.__protocol_attrs__`:

- **Fields & Division Rings (`StandardField`, `ModularField`)**:
  Provide `{zero, is_zero, one, add, neg, sub, mul, inv, div}`:
  - `isinstance(field, DivisionRing)` $\to$ `True`
  - `isinstance(field, CommRing)` / `isinstance(field, Ring)` / `isinstance(field, NonAssocRing)` $\to$ `True`
  - `isinstance(field, AddCommGroup)` / `isinstance(field, AddGroup)` / `isinstance(field, AddCommMonoid)` / `isinstance(field, AddMonoid)` $\to$ `True`
  - `isinstance(field, CommGroup)` / `isinstance(field, Group)` / `isinstance(field, CommMonoid)` / `isinstance(field, Monoid)` $\to$ `True` *(reflecting operational subsumption where `inv` and `div` act on the multiplicative group of units $F^\times = F \setminus \{\mathbf{0}\}$ and raise `ZeroDivisionError` at $\mathbf{0}$)*
- **Associative Unital Algebras (`CliffordAlgebra`, `PolynomialAlgebra`, `DualNumberAlgebra`, `CochainAlgebra`)**:
  Provide `{zero, one, add, neg, sub, mul, smul}`:
  - `isinstance(alg, Algebra)` / `isinstance(alg, NonAssocAlgebra)` $\to$ `True`
  - `isinstance(alg, Module)` / `isinstance(alg, Semimodule)` $\to$ `True`
  - `isinstance(alg, Ring)` / `isinstance(alg, NonAssocRing)` $\to$ `True`
- **Non-Associative Algebras (`LieAlgebra`)**:
  Provide `{zero, add, neg, sub, mul, smul, bracket}` (and **not** `one`):
  - `isinstance(lie, NonAssocAlgebra)` / `isinstance(lie, Module)` / `isinstance(lie, NonAssocRing)` $\to$ `True`
  - `isinstance(lie, Ring)` / `isinstance(lie, Algebra)` $\to$ `False` (missing `one`)
- **`Semiring` vs `Ring` / `Field` Boundary**:
  - Every `Semiring` instance structurally satisfies `AddCommMonoid`, `AddMonoid`, `AddSemigroup`, `AddMagma`, `CommMonoid`, `Monoid`, `Semigroup`, and `Magma`.
  - Domain algebras that subclass `Semiring` (`CliffordAlgebra`, `PolynomialAlgebra`, `DualNumberAlgebra`, `StandardSemiring`) satisfy **both** `Semiring` and `Ring` / `Algebra`.
  - General `Ring` and `Field` protocols do not include `HasStar` (`star()`) because arbitrary rings and fields (`StandardField`, `ModularField`, `CochainAlgebra`) do not admit a total Kleene closure $a^* = 1 + a + a^2 + \cdots$.
- **Runtime `isinstance` vs `issubclass` Note (PEP 544)**:
  - Callers must always use `isinstance(instance, Protocol)` at runtime and protocol type annotations for static subtyping; per PEP 544, Python's `issubclass(Cls, Protocol)` raises `TypeError` on protocols with `@property` members (`zero`, `one`, `bot`, `top`, `identity`) when `Protocol` is not in `Cls.__mro__`.

---

### 5. Forward Compatibility: The Law of Flat Protocol Composition (Phases 7 & 8)

To prevent diamond inheritance from ever re-entering the codebase in Phases 7 and 8 (`EP-0200`–`EP-0215`), this proposal establishes a permanent architectural invariant:

> **The Law of Flat Protocol Composition**:
> *No Named Algebraic Protocol (Layer 2) may ever inherit from another Named Algebraic Protocol—only from Layer 1 Atomic Operational Mixins (`Has*`) and `Protocol`. Structural subtyping between Layer 2 protocols is guaranteed automatically by PEP 544 attribute superset inclusion.*

For example, in Phase 7:
- **`PoissonAlgebra[R, M]` (`EP-0204`)**: Composes `(HasScale[R, M], HasZero[M], HasOne[M], HasNeg[M], HasMul[M], HasBracket[M], Protocol[R, M])`—avoiding diamond collisions between `CommAlgebra` and `LieAlgebra` and keeping `.mul()` (commutative associative product) distinct from `.bracket()` (Lie bracket).
- **`Bialgebra[R, M]` & `HopfAlgebra[R, M]` (`EP-0206`)**: Compose `Algebra` mixins with coalgebraic mixins (`HasCoproduct`, `HasCounit`, `HasAntipode`) at depth 2 with zero diamonds.

## Backwards Compatibility

1. **100% Public Symbol Compatibility**:
   - All existing 31 protocol names and aliases (`Magma`, `Semigroup`, `Band`, `Quasigroup`, `Monoid`, `CommMonoid`, `CommutativeMonoid`, `Group`, `CommGroup`, `AbelianGroup`, `GroupAction`, `AddMagma`, `AddSemigroup`, `AddMonoid`, `AddCommMonoid`, `AddGroup`, `AddCommGroup`, `OpMagma`, `OpSemigroup`, `OpMonoid`, `OpCommMonoid`, `Semiring`, `NonAssocRing`, `Ring`, `CommRing`, `CommutativeRing`, `AbelianRing`, `DivisionRing`, `Field`, `Semimodule`, `Module`, `VectorSpace`, `NonAssocAlgebra`, `Algebra`, `JoinSemilattice`, `MeetSemilattice`, `Lattice`, `BoundedLattice`, `DistributiveLattice`, `BooleanAlgebra`) remain exported from `algebrax.algebra`.
   - All atomic mixins (`HasZero`, `HasZeroPred`, `HasOne`, `HasAdd`, `HasNeg`, `HasMul`, `HasInv`, `HasScale`, `HasSMul`, `HasStar`, `HasJoin`, `HasMeet`, `HasBounds`, `HasComplement`, `HasOp`, `HasIdentity`, `HasBracket`) are exported from `algebrax.algebra`.
2. **Concrete Implementations Unchanged**:
   - Concrete classes (`StandardSemiring`, `StandardField`, `ModularField`, `PolynomialAlgebra`, `DualNumberAlgebra`, `CliffordAlgebra`, `LieAlgebra`, `CochainAlgebra`) require zero changes to their public APIs.

## How to Teach This / Documentation Plan

- Update [EP-0193 (Documentation Architecture Realignment)](EP-0193-documentation-architecture-realignment.md) to introduce the **Periodic Table of Algebraic Mixins** (Atoms, Functional Groups, Molecules, and Isomers) in `docs/concepts.md` and `docs/guide/algebra/magmas_and_monoids.md`.
- Show how complex structures (`Ring`, `Field`, `Algebra`) are flat combinations of elementary operational capabilities rather than deep OOP inheritance trees.

## Reference Implementation

Implementation targets `src/algebrax/algebra/` and `tests/algebrax/test_type_safety.py`:
- `src/algebrax/algebra/_mixins.py` (new atomic mixins)
- `src/algebrax/algebra/_magma.py` (imports only from `_mixins.py`)
- `src/algebrax/algebra/_monoid.py` (imports only from `_mixins.py`)
- `src/algebrax/algebra/_group.py` (imports only from `_mixins.py`)
- `src/algebrax/algebra/_semiring.py` (composes mixins and delegates `nsum`/`power` to `_helpers.py`)
- `src/algebrax/algebra/_ring.py` (imports only from `_mixins.py`)
- `src/algebrax/algebra/_field.py` (imports only from `_mixins.py` for protocols)
- `src/algebrax/algebra/_module.py` (imports only from `_mixins.py`)
- `src/algebrax/algebra/_lattice.py` (imports only from `_mixins.py`)
- `src/algebrax/algebra/__init__.py` (exports all mixins and named protocols)
- `tests/algebrax/test_type_safety.py` (verifies diamond-free MROs, `(R, M)` parameter order, and `__protocol_attrs__` subtyping lattice)

## Rejected Ideas

1. **Retaining Deep Nominal Protocol Chaining**:
   - *Rejected*: Caused 5 distinct diamond inheritance patterns across `Ring`, `Field`, `Algebra`, `CommGroup`, and `BooleanAlgebra`, and forced redundant `Protocol[V]` declarations at every level.
2. **Placing `nsum`, `power`, or `is_zero` Directly on `HasZero` / `HasOne`**:
   - *Rejected*: In Python's `@runtime_checkable` `Protocol`, any method with a default body defined on a protocol is added to `cls.__protocol_attrs__`. Adding `nsum` or `is_zero` to `HasZero` or `power` to `HasOne` would cause unboxed/duck-typed `Monoid`, `Group`, and `Ring` classes that do not define `.nsum()`, `.power()`, or `.is_zero()` to fail `isinstance()` checks. Keeping `is_zero` on `HasZeroPred` (used by `DivisionRing` and `Field`) and keeping `nsum`/`power` in `_helpers.py` (and on `Semiring`) preserves duck-typing minimality.
3. **Removing Named Protocols in Favor of Only Mixins**:
   - *Rejected*: Mathematicians and domain engineers think in terms of `Ring`, `Field`, `Group`, `Module`, and `Algebra`, not `(HasZero[V], HasOne[V], HasNeg[V], HasMul[V])`. Named protocols provide essential semantic clarity while mixins provide the clean compositional substrate.

## Open Questions

- [x] Should `HasNeg`, `HasInv`, and `HasZeroPred` inherit from `HasAdd`, `HasMul`, and `HasZero` or remain purely orthogonal? (**Resolved: Purely orthogonal—each inherits directly from `Protocol[V]` so every named protocol explicitly lists all of its operational mixins in its class declaration, e.g. `Group(HasOne[V], HasMul[V], HasInv[V], Protocol)`**).
- [x] How should `DivisionRing.is_zero` and `Field.is_zero` be shared without polluting `HasZero`? (**Resolved: Via `HasZeroPred(Protocol[V])` used alongside `HasZero[V]` in `DivisionRing` and `Field`**).
- [x] How should `(R, M)` generic type parameter ordering be preserved on two-sorted protocols? (**Resolved: Place `HasScale[R, M]` first in the base tuple and explicitly subscript `Protocol[R, M]`**).

## Change Log

* **2026-11-01:**
    * Initial Draft authored by Eran Rivlis & Antigravity.
    * Accepted following unanimous Grand Council review: added `HasZeroPred` for `DivisionRing`/`Field.is_zero`, locked `(R, M)` parameter order on two-sorted protocols via `HasScale[R, M]`-first ordering, added `HasOp`, `HasIdentity`, `HasBracket`, and `HasSMul` alias, completed Section 2 table (`Quasigroup`, `GroupAction`, `Op*`), deduplicated `Semiring.nsum`/`power` via `_helpers.py`, and codified the Law of Flat Protocol Composition for Phases 7 & 8.
