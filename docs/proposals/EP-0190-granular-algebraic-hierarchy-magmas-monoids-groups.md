---
title: "EP-0190: Granular Algebraic Hierarchy — Magmas, Monoids, Groups & Lattices"
description: "Decompose algebraic abstractions into Lean 4 Mathlib-aligned structural protocols for magmas, semigroups, monoids, groups, and lattices."
icon: lucide/git-fork
status: draft
---

# EP-0190: Granular Algebraic Hierarchy — Magmas, Monoids, Groups & Lattices

| Field        | Value                                                             |
|:-------------|:------------------------------------------------------------------|
| **EP**       | 0190                                                              |
| **Title**    | Granular Algebraic Hierarchy — Magmas, Monoids, Groups & Lattices |
| **Author**   | Eran Rivlis & Antigravity                                         |
| **Sponsor**  | Council Framework                                                 |
| **Delegate** | 🧩 Russell (Taxonomy) & 🔬 Popper (Verification)                  |
| **Status**   | Draft                                                             |
| **Type**     | Standards Track                                                   |
| **Created**  | 2026-10-25                                                        |
| **Updated**  | 2026-10-25                                                        |

## Abstract

This proposal establishes a granular, composable algebraic hierarchy under `algebrax.algebra` for structures that are
simpler than or orthogonal to semirings: **Magmas**, **Semigroups**, **Monoids**, **Groups**, **Abelian Groups**,
**Semilattices**, and **Lattices**. Modeled after **Lean 4's `Mathlib.Algebra`**, the design leverages Python's
`typing.Protocol` with `@runtime_checkable` to provide zero-overhead structural subtyping. This allows algorithms such
as graph path accumulation, string rewriting, and reachability to specify their exact minimal algebraic requirements,
while enabling layered property-based axiomatic verification in `algebrax.verification`.

## Motivation

In AlgebraX, the **`Semiring`** protocol has historically been the foundational atom for algebraic abstraction. While
`Semiring` elegantly captures matrix multiplication $C_{ik} = \bigoplus_j A_{ij} \otimes B_{jk}$, it bundles two
distinct monoids (addition and multiplication) plus distributive laws.

Many core mathematical and computer science structures do not satisfy — and do not need — a full semiring:

1. **Path Concatenation & Automata Words**: Concatenating edges in a path or alphabet symbols in a language requires
   only an associative binary operation with an identity element — a **Monoid** $(M, \cdot, 1)$. Forcing users to embed
   monoids into semirings with dummy addition is conceptually flawed and wasteful.
2. **Reversible Symmetries & Transformations**: Permutations, geometric rotations, and cryptographic cipher steps form a
   **Group** $(G, \cdot, ^{-1}, 1)$ with two-sided inverses. Currently, `algebrax` has no first-class `Group` protocol;
   groups are either simulated as monoids without inverse guarantees or forced into matrix representations.
3. **Reachability, Precedence & Logic**: Graph reachability, transitive closure, and lattice-theoretic domain ordering
   operate over **Semilattices** $(\vee)$ and **Lattices** $(\wedge, \vee)$ where operations are idempotent
   ($x \vee x = x$).
4. **Non-Associative Algebras**: Octonions, sedenions, and loop quasigroups violate associativity
   ($a \cdot (b \cdot c) \ne (a \cdot b) \cdot c$) and are mathematically **Magmas** or **Quasigroups**.

By formalizing these sub-semiring structures, AlgebraX can accept lighter, more precise inputs, prune unnecessary
axioms, and certify correctness axiom by axiom.

## Rationale

### Council Alignment

- **🧩 Russell (Structural Taxonomy)**: Establishes a mathematically rigorous, Bourbaki- and Lean 4-aligned taxonomy
  where every algebraic abstraction lives at its precise categorical tier.
- **🔬 Popper (Layered Falsifiability)**: Enables granular, law-by-law property-based testing in `algebrax.verification`.
  Instead of testing 12 semiring axioms all at once, each level (closure, associativity, identity, inverse,
  commutativity, idempotence) is tested independently.
- **⚡ Shannon (Zero Bloat & Efficiency)**: Uses structural `typing.Protocol`. At runtime, passing a plain object or
  dictionary costs zero wrapping overhead; protocols check contracts via static typing (mypy/pyright) and runtime
  `isinstance` checks.
- **🤝 Steward (Ergonomics & Compatibility)**: 100% backwards-compatible. Existing `Semiring` implementations naturally
  fulfill `AddCommMonoid` and `Monoid` sub-protocols without modifying a single line of client code.

## Specification

### 1. Module Layout

A new top-level subpackage `algebrax.algebra` is introduced:

```text
src/algebrax/algebra/
├── __init__.py          # Unified re-exports of all protocols and axiomatic verifiers
├── _magma.py            # Magma, Semigroup, Band, Quasigroup
├── _monoid.py           # Monoid, CommutativeMonoid, AddMonoid, AddCommMonoid
├── _group.py            # Group, AbelianGroup, AddGroup, AddCommGroup
├── _lattice.py          # Semilattice, BoundedSemilattice, Lattice, BoundedLattice, BooleanAlgebra
└── _helpers.py          # Binary exponentiation (power/nsum), word accumulation
```

### 2. Single-Operation Protocols (`_magma.py`, `_monoid.py`, `_group.py`)

#### Multiplicative / General Signature

```python
from typing import Protocol, TypeVar, runtime_checkable

V = TypeVar('V')


@runtime_checkable
class Magma(Protocol[V]):
    """A set equipped with a single closed binary operation op: V x V -> V."""

    def op(self, a: V, b: V) -> V: ...


@runtime_checkable
class Semigroup(Magma[V], Protocol[V]):
    """An associative magma: op(op(a, b), c) == op(a, op(b, c))."""
    ...


@runtime_checkable
class Band(Semigroup[V], Protocol[V]):
    """An idempotent semigroup: op(a, a) == a."""
    ...


@runtime_checkable
class Monoid(Semigroup[V], Protocol[V]):
    """A semigroup equipped with a neutral identity element."""

    @property
    def id(self) -> V: ...


@runtime_checkable
class CommutativeMonoid(Monoid[V], Protocol[V]):
    """A monoid whose operation is commutative: op(a, b) == op(b, a)."""
    ...


@runtime_checkable
class Group(Monoid[V], Protocol[V]):
    """A monoid where every element possesses a two-sided inverse."""

    def inv(self, a: V) -> V: ...


@runtime_checkable
class AbelianGroup(Group[V], CommutativeMonoid[V], Protocol[V]):
    """A commutative (abelian) group."""
    ...
```

#### Additive Dual Protocols

To align with standard additive arithmetic ($+$, $0$, $-$):

```python
@runtime_checkable
class AddMagma(Protocol[V]):
    def add(self, a: V, b: V) -> V: ...


@runtime_checkable
class AddSemigroup(AddMagma[V], Protocol[V]):
    ...


@runtime_checkable
class AddMonoid(AddSemigroup[V], Protocol[V]):
    @property
    def zero(self) -> V: ...


@runtime_checkable
class AddCommMonoid(AddMonoid[V], Protocol[V]):
    ...


@runtime_checkable
class AddGroup(AddMonoid[V], Protocol[V]):
    def neg(self, a: V) -> V: ...

    def sub(self, a: V, b: V) -> V: ...


@runtime_checkable
class AddCommGroup(AddGroup[V], AddCommMonoid[V], Protocol[V]):
    ...
```

### 3. Lattice Protocols (`_lattice.py`)

```python
@runtime_checkable
class Semilattice(Protocol[V]):
    """A set with an associative, commutative, idempotent operation (join or meet)."""

    def op(self, a: V, b: V) -> V: ...


@runtime_checkable
class Lattice(Protocol[V]):
    """A set equipped with meet (wedge) and join (vee) operations satisfying absorption."""

    def meet(self, a: V, b: V) -> V: ...

    def join(self, a: V, b: V) -> V: ...


@runtime_checkable
class BoundedLattice(Lattice[V], Protocol[V]):
    """A lattice with a unique bottom element (bot) and top element (top)."""

    @property
    def bot(self) -> V: ...

    @property
    def top(self) -> V: ...


@runtime_checkable
class BooleanAlgebra(BoundedLattice[V], Protocol[V]):
    """A complemented distributive lattice."""

    def complement(self, a: V) -> V: ...
```

### 4. Layered Law Verification (`algebrax.verification`)

In `algebrax.verification`, property-based tests verify instances axiom by axiom:

```python
def verify_magma_laws(magma: Magma[V], samples: Sequence[V]) -> None: ...


def verify_semigroup_laws(semigroup: Semigroup[V], samples: Sequence[V]) -> None: ...


def verify_monoid_laws(monoid: Monoid[V], samples: Sequence[V]) -> None: ...


def verify_group_laws(group: Group[V], samples: Sequence[V]) -> None: ...


def verify_lattice_laws(lattice: Lattice[V], samples: Sequence[V]) -> None: ...
```

## Backwards Compatibility

100% backwards-compatible:

- Existing `Semiring` implementations already have `.add()` and `.zero`, so they structurally satisfy
  `AddCommMonoid[V]`.
- Existing `Semiring` implementations already have `.mul()` and `.one`, so they structurally satisfy `Monoid[V]` (when
  wrapped or mapped).
- No existing public APIs in `algebrax.semiring`, `algebrax.matrix`, or `algebrax.topology` are altered or removed.
- `algebrax.algebra` is added as a new namespace and exported from `algebrax`.

## How to Teach This / Documentation Plan

1. **User Guide**: Add `docs/guide/algebra/hierarchy.md` illustrating the Lean 4-aligned hierarchy from Magmas to Groups
   and Lattices.
2. **Interactive Examples**: Provide recipes showing path reduction over `Monoid`, symmetry validation over `Group`, and
   truth-value reasoning over `BooleanAlgebra`.
3. **Verification Matrix**: Register all new protocols and their axiomatic validators in `docs/verification.md`.

## Reference Implementation

A prototype implementation and architectural analysis is provided in
[EXP-0004](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0004-pure-algebraic-hierarchy/README.md).

## Rejected Ideas

1. **Nominal Base Classes (ABC with inheritance enforcement)**:
    - *Rejected*: Requiring users to inherit from `class Monoid(ABC)` would break compatibility with third-party
      objects, dictionaries, and existing semiring classes. Python `typing.Protocol` with `@runtime_checkable` provides
      structural subtyping (duck typing) with complete static and runtime type-checking safety.
2. **Bundling Everything Under `algebrax.semiring`**:
    - *Rejected*: A `Group` or `Lattice` is not a semiring. Cramming them into `algebrax.semiring` violates separation
      of concerns and creates misleading taxonomy. A dedicated `algebrax.algebra` namespace preserves mathematical
      precision.

## Open Questions

- [ ] Should `Monoid` provide a default binary exponentiation helper (`power(a, n)`) via mixin or standalone function?
- [ ] Should we provide adapter classes (e.g. `MultiplicativeMonoid(semiring)`) to adapt any `Semiring` into a `Monoid`
  instance?

## Change Log

* **2026-10-25:** Initial Draft.
