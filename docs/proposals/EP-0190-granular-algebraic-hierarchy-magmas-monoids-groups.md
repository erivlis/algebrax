---
title: "EP-0190: Granular Algebraic Hierarchy — Magmas, Monoids, Groups & Lattices"
description: "Decompose algebraic abstractions into Lean 4 Mathlib-aligned structural protocols for magmas, semigroups, monoids, groups, and lattices."
icon: lucide/git-fork
status: accepted
---

# EP-0190: Granular Algebraic Hierarchy — Magmas, Monoids, Groups & Lattices

| Field | Value |
| :--- | :--- |
| **EP** | 0190 |
| **Title** | Granular Algebraic Hierarchy — Magmas, Monoids, Groups & Lattices |
| **Author** | Eran Rivlis & Antigravity |
| **Sponsor** | Council Framework |
| **Delegate** | 🧩 Russell (Taxonomy) & 🔬 Popper (Verification) |
| **Status** | Accepted |
| **Type** | Standards Track |
| **Created** | 2026-10-25 |
| **Updated** | 2026-10-25 |

## Abstract

This proposal establishes a granular, composable algebraic hierarchy under `algebrax.algebra` for structures that are simpler than or orthogonal to semirings: **Magmas**, **Semigroups**, **Monoids**, **Groups**, **Commutative Groups**, **Semilattices**, and **Lattices**. Modeled after **Lean 4's `Mathlib.Algebra`**, the design leverages Python's `typing.Protocol` with `@runtime_checkable` to provide zero-overhead structural subtyping. Crucially, the carrier data structures remain **raw, unboxed native Python types and sparse dictionaries** (`dict[K, V]`, `dict[K, K]`), while algebraic operators act as stateless typeclasses. This allows algorithms such as graph path accumulation, string rewriting, and reachability to specify their exact minimal algebraic requirements, while enabling layered property-based axiomatic verification in `algebrax.verification`.

## Motivation

In AlgebraX, the **`Semiring`** protocol has historically been the foundational atom for algebraic abstraction. While `Semiring` elegantly captures matrix multiplication $C_{ik} = \bigoplus_j A_{ij} \otimes B_{jk}$, it bundles two distinct monoids (addition and multiplication) plus distributive laws.

Many core mathematical and computer science structures do not satisfy — and do not need — a full semiring:

1. **Path Concatenation & Automata Words**: Concatenating edges in a path or alphabet symbols in a language requires only an associative binary operation with an identity element — a **Monoid** $(M, \cdot, 1)$. Forcing users to embed monoids into semirings with dummy addition is conceptually flawed and wasteful.
2. **Reversible Symmetries & Transformations**: Permutations, geometric rotations, and cryptographic cipher steps form a **Group** $(G, \cdot, 1, ^{-1})$ with two-sided inverses. Currently, `algebrax` has no first-class `Group` protocol; groups are either simulated as monoids without inverse guarantees or forced into matrix representations.
3. **Reachability, Precedence & Logic**: Graph reachability, transitive closure, and lattice-theoretic domain ordering operate over **Semilattices** $(\vee)$ and **Lattices** $(\wedge, \vee)$ where operations are idempotent ($x \vee x = x$).
4. **Non-Associative Algebras**: Octonions, sedenions, and loop quasigroups violate associativity ($a \cdot (b \cdot c) \ne (a \cdot b) \cdot c$) and are mathematically **Magmas** or **Quasigroups**.

### The Mental Model (The Freshman Test)

To make abstract algebra immediately intuitive to any software engineer, each tier corresponds to a familiar computational pattern:
- **`Magma` (The Combiner)**: Takes any two elements of type $T$ and combines them into an element of type $T$ without crashing.
- **`Semigroup` (The Parallelizer)**: Parentheses do not matter: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$. This is the algebraic engine of **parallel MapReduce**—you can partition a massive list across CPU cores, fold each partition, and combine results in any tree order without altering the outcome.
- **`Monoid` (The Safe Empty Accumulator)**: An associative combiner with a neutral "do-nothing" identity element ($0$ for $+$, $1$ for $\times$, `""` for strings). Enables safe folding over empty sequences without throwing `ValueError: reduce() of empty sequence`.
- **`Group` (The Undo Button)**: Every action can be perfectly undone via an inverse element: $g \cdot g^{-1} = 1$. Models time-travel undo, reversible state machines, cryptographic ciphers, and permutation networks.
- **`Lattice` (The Merger & Filter)**: Equipped with `join` ($\vee$, least upper bound / merge) and `meet` ($\wedge$, greatest lower bound / filter), satisfying absorption $a \wedge (a \vee b) = a$. Models CRDT branch merges, type inference, and access control role hierarchies.

## Rationale & Council Alignment

- **🧩 Russell (Structural Taxonomy)**: Establishes a mathematically rigorous, Bourbaki- and Lean 4-aligned taxonomy where every algebraic abstraction lives at its precise categorical tier. Dual additive (`AddMonoid`) and multiplicative (`Monoid`) hierarchies share identical method signatures with `Semiring` (`add`/`zero`, `mul`/`one`), eliminating structural subtyping mismatches.
- **🔬 Popper (Layered Falsifiability)**: Enables granular, law-by-law property-based testing in `algebrax.verification`. Each verifier returns `dict[str, bool]` rather than failing blindly, testing closure, associativity, identity, inverse, commutativity, and absorption independently.
- **⚡ Shannon (Zero Bloat & Minimal Representation)**: Pure-carrier unboxed design. Elements are plain numbers, strings, or sparse dictionaries (`dict[K, V]`). Algebraic protocols are stateless typeclasses. Zero object wrappers or boxing overhead.
- **🛡️ The Golem (Safety & Contract Hardening)**: The identity property is named `.identity` (or `.one`/`.zero`), avoiding collision with Python's built-in `id()` function. Marker protocols include boolean discriminants (`is_commutative`, `is_associative`) to guard against false-positive duck typing under `@runtime_checkable`.
- **💡 Feynman (Clarity & AMDS Standard)**: Every protocol class docstring includes an official LaTeX algebraic signature ($\langle M, \cdot, 1 \rangle$) complying with the EP-0150 standard.

## Specification

### 1. Module Layout

A new top-level subpackage `algebrax.algebra` is introduced:

```text
src/algebrax/algebra/
├── __init__.py          # Unified re-exports of all protocols and axiomatic verifiers
├── _magma.py            # Magma, Semigroup, Band, Quasigroup, OpMagma, AddMagma, AddSemigroup
├── _monoid.py           # Monoid, CommMonoid, AddMonoid, AddCommMonoid, OpMonoid
├── _group.py            # Group, CommGroup, AddGroup, AddCommGroup, GroupAction
├── _lattice.py          # JoinSemilattice, MeetSemilattice, Lattice, BoundedLattice, DistributiveLattice, BooleanAlgebra
└── _helpers.py          # Polymorphic binary exponentiation (power, nsum), sequence folding
```

### 2. Multiplicative & Additive Dual Protocols

#### Multiplicative Hierarchy (`_magma.py`, `_monoid.py`, `_group.py`)

The primary single-operation hierarchy uses multiplicative conventions (`mul`, `one`, `inv`, `div`):

```python
from typing import Protocol, TypeVar, runtime_checkable

V = TypeVar('V')

@runtime_checkable
class Magma(Protocol[V]):
    r"""Carrier equipped with a closed binary operation $\cdot: V \times V \to V$."""
    def mul(self, a: V, b: V) -> V: ...

@runtime_checkable
class Semigroup(Magma[V], Protocol[V]):
    r"""Associative magma: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$."""
    is_associative: bool = True

@runtime_checkable
class Band(Semigroup[V], Protocol[V]):
    r"""Idempotent semigroup: $a \cdot a = a$."""
    is_idempotent: bool = True

@runtime_checkable
class Monoid(Semigroup[V], Protocol[V]):
    r"""Semigroup equipped with a multiplicative identity element $\mathbf{1}$."""
    @property
    def one(self) -> V: ...

@runtime_checkable
class CommMonoid(Monoid[V], Protocol[V]):
    r"""Monoid with commutative multiplication: $a \cdot b = b \cdot a$."""
    is_commutative: bool = True

@runtime_checkable
class Group(Monoid[V], Protocol[V]):
    r"""Monoid where every element possesses a two-sided inverse $a^{-1}$."""
    def inv(self, a: V) -> V: ...
    def div(self, a: V, b: V) -> V:
        """Quotient a / b = a * inv(b)."""
        return self.mul(a, self.inv(b))

@runtime_checkable
class CommGroup(Group[V], CommMonoid[V], Protocol[V]):
    r"""Abelian group satisfying commutativity: $a \cdot b = b \cdot a$."""
    ...

AbelianGroup = CommGroup  # Canonical alias
```

#### Additive Dual Hierarchy

Mirroring standard additive arithmetic (`add`, `zero`, `neg`, `sub`):

```python
@runtime_checkable
class AddMagma(Protocol[V]):
    def add(self, a: V, b: V) -> V: ...

@runtime_checkable
class AddSemigroup(AddMagma[V], Protocol[V]):
    is_associative: bool = True

@runtime_checkable
class AddMonoid(AddSemigroup[V], Protocol[V]):
    @property
    def zero(self) -> V: ...

@runtime_checkable
class AddCommMonoid(AddMonoid[V], Protocol[V]):
    is_commutative: bool = True

@runtime_checkable
class AddGroup(AddMonoid[V], Protocol[V]):
    def neg(self, a: V) -> V: ...
    def sub(self, a: V, b: V) -> V:
        return self.add(a, self.neg(b))

@runtime_checkable
class AddCommGroup(AddGroup[V], AddCommMonoid[V], Protocol[V]):
    ...
```

#### Domain-Agnostic Single-Operation Protocols

For operations without arithmetic connotations (e.g. string concatenation, token folding):

```python
@runtime_checkable
class OpMagma(Protocol[V]):
    def op(self, a: V, b: V) -> V: ...

@runtime_checkable
class OpMonoid(OpMagma[V], Protocol[V]):
    @property
    def identity(self) -> V: ...
```

### 3. Order & Lattice Protocols (`_lattice.py`)

Factored categorically into dual semilattices:

```python
@runtime_checkable
class JoinSemilattice(Protocol[V]):
    """Carrier equipped with an associative, commutative, idempotent join (vee)."""
    def join(self, a: V, b: V) -> V: ...

@runtime_checkable
class MeetSemilattice(Protocol[V]):
    """Carrier equipped with an associative, commutative, idempotent meet (wedge)."""
    def meet(self, a: V, b: V) -> V: ...

@runtime_checkable
class Lattice(JoinSemilattice[V], MeetSemilattice[V], Protocol[V]):
    """Lattice satisfying absorption: a wedge (a vee b) = a and a vee (a wedge b) = a."""
    ...

@runtime_checkable
class BoundedLattice(Lattice[V], Protocol[V]):
    """Lattice equipped with bottom (bot) and top (top) bounds."""
    @property
    def bot(self) -> V: ...
    @property
    def top(self) -> V: ...

@runtime_checkable
class DistributiveLattice(Lattice[V], Protocol[V]):
    """Lattice satisfying distributivity of meet over join and join over meet."""
    ...

@runtime_checkable
class BooleanAlgebra(BoundedLattice[V], DistributiveLattice[V], Protocol[V]):
    """Complemented distributive lattice: a vee not(a) = top, a wedge not(a) = bot."""
    def complement(self, a: V) -> V: ...
```

### 4. Group Action Protocol (`_group.py`)

```python
G = TypeVar('G')
X = TypeVar('X')

@runtime_checkable
class GroupAction(Protocol[G, X]):
    r"""Group G acting on a set X: $g \cdot (h \cdot x) = (g h) \cdot x$ and $1 \cdot x = x$."""
    def gact(self, g: G, x: X) -> X: ...
```

### 5. Architectural Principle: Dictionary as Unboxed Sparse Representation

To uphold AlgebraX's defining identity, algebraic structures do **not** box values into wrapper objects. The carriers are native Python types and sparse dictionaries:
- `SparseVector[K, V] = dict[K, V]`
- `SparseMatrix[R, C, V] = dict[R, dict[C, V]]`
- Permutation mappings = `dict[K, K]`
- Words / Automata traces = `tuple[K, ...]`

When a `Monoid` operates over word paths, it operates on raw tuples or strings. When a `Group` operates on permutations, it acts on raw `dict[K, K]`. When an `AbelianGroup` operates on sparse vector additions, it operates directly on `dict[K, V]`.

### 6. Layered Law Verification (`algebrax.verification`)

Property-based tests in `algebrax.verification.hierarchy` verify instances axiom by axiom, returning structured `dict[str, bool]` reports:

```python
def verify_magma_laws(magma: Magma[V], samples: Sequence[V]) -> dict[str, bool]: ...
def verify_semigroup_laws(semigroup: Semigroup[V], samples: Sequence[V]) -> dict[str, bool]: ...
def verify_monoid_laws(monoid: Monoid[V], samples: Sequence[V]) -> dict[str, bool]: ...
def verify_group_laws(group: Group[V], samples: Sequence[V]) -> dict[str, bool]: ...
def verify_lattice_laws(lattice: Lattice[V], samples: Sequence[V]) -> dict[str, bool]: ...
def verify_boolean_algebra_laws(ba: BooleanAlgebra[V], samples: Sequence[V]) -> dict[str, bool]: ...

# Additive duals
def verify_add_monoid_laws(monoid: AddMonoid[V], samples: Sequence[V]) -> dict[str, bool]: ...
def verify_add_group_laws(group: AddGroup[V], samples: Sequence[V]) -> dict[str, bool]: ...
```

*Verification Invariant*: Verifiers enforce a minimum sample witness count ($|S| \ge 3$) to guarantee that laws are non-vacuously falsifiable.

## Backwards Compatibility

100% backwards-compatible:
- Existing `Semiring` implementations define `.add()`, `.zero`, `.mul()`, and `.one`. Because `AddCommMonoid[V]` expects `add`/`zero` and `Monoid[V]` expects `mul`/`one`, every existing semiring naturally and structurally fulfills both protocols without modification!
- `algebrax.group` and `algebrax.lattice` continue to export their dictionary functions (`compose`, `join`, `meet`), while re-exporting the new structural protocols.
- `algebrax.algebra` is added as a new top-level export in `algebrax`.

## How to Teach This / Documentation Plan

1. **User Guide**: Author `docs/guide/algebra/hierarchy.md` detailing the Lean 4 Mathlib alignment with intuitive mental models (MapReduce, Undo buttons, Mergers).
2. **Interactive Recipes**: Provide executable recipes demonstrating:
   - Parallel string/path reduction over `Monoid`.
   - Permutation and symmetry composition over `Group`.
   - Set-theoretic and fuzzy reasoning over `BooleanAlgebra`.
3. **Verification Matrix**: Register all new protocols and verifiers in `docs/verification.md`.

## Reference Implementation

A complete analysis and architectural blueprint is provided in
[EXP-0004](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0004-pure-algebraic-hierarchy/README.md).

## Rejected Ideas

1. **`op` vs `mul` Divergence in `Monoid`**:
   - *Rejected*: Defining `Monoid` with `op` and `id` while `Semiring` defines `mul` and `one` caused structural subtyping to fail. Unifying `Monoid` on `mul` and `one` aligns with Lean 4 and ensures seamless semiring subtyping.
2. **Nominal Base Classes (ABCs)**:
   - *Rejected*: Requiring inheritance would break compatibility with third-party types and plain dictionaries. Structural typing (`typing.Protocol`) allows unboxed carriers to fulfill protocols purely by shape.
3. **Boxed Element Objects (`MonoidElement[V]`)**:
   - *Rejected*: Violates the core AlgebraX principle of unboxed sparse representations.

## Open Questions

- [ ] Should `Band` (idempotent semigroup) expose an explicit `is_idempotent` property or rely strictly on verification testing?
- [ ] Should we provide a canonical `FreeMonoid` generator for word traces in `algebrax.automata`?

## Change Log

* **2026-10-25:** Initial Draft.
* **2026-10-25:** Accepted following Council review (incorporating Noether symmetry duality, Russell lattice factoring, Golem `.identity` renaming, Feynman Freshman Test glosses, and unboxed dictionary carrier purity).
