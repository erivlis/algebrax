---
title: "EP-0197: Decoupled Semiring Foundations — Pure Rigs, Star Semirings & Kleene Algebras"
description: "Decouples Kleene star closure from pure semirings to restore universal mathematical subtyping (Semiring ⊂ Ring) and establishes first-class StarSemiring and KleeneAlgebra protocols."
icon: lucide/scroll-text
status: final
---

# EP-0197: Decoupled Semiring Foundations — Pure Rigs, Star Semirings & Kleene Algebras

| Field | Value |
| :--- | :--- |
| **EP** | 0197 |
| **Title** | Decoupled Semiring Foundations — Pure Rigs, Star Semirings & Kleene Algebras |
| **Author** | Eran Rivlis <eran@algebrax.org>, Antigravity AI |
| **Sponsor** | ⚖️ Noether (Symmetry & Invariance), 🧩 Russell (Taxonomy & Consistency) |
| **Delegate** | 🔬 Popper (Falsifiability & Multi-Layered Testing) |
| **Status** | Final |
| **Type** | Standards Track |
| **Created** | 2026-11-13 |
| **Updated** | 2026-11-13 |
| **Replaces** | None |
| **Superseded-By** | None |

---

## Abstract

This proposal decouples the unary Kleene star closure operator ($^*$) from the core mathematical `Semiring` protocol. In the original AlgebraX architecture, `Semiring` bundled `HasStar[V]`, reflecting the early project focus on shortest-path graph algorithms and regular language automata. However, in classical mathematics, a semiring (or rig/hemiring) $\langle S, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$ does not require or possess a Kleene closure. Bundling `HasStar` broke the fundamental subtyping relation $\text{Semiring} \subset \text{Ring}$, preventing standard rings ($\mathbb{Z}, \mathbb{Q}, \mathbb{R}$, polynomial rings $R[x]$, matrix rings $M_n$) from structurally conforming to `Semiring`, and forced classes like `MonoidAlgebraSemiring` to implement dummy `NotImplementedError` stubs. 

This proposal establishes a three-tiered algebraic hierarchy:
1. **`Semiring` (Pure Rig)**: $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$, satisfied by all semirings, rings, fields, and algebras.
2. **`StarSemiring` (Closed / Conway Semiring)**: $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$, satisfying the Conway star identity $a^* = \mathbf{1} + a \cdot a^* = \mathbf{1} + a^* \cdot a$.
3. **`KleeneAlgebra`**: An idempotent star semiring ($a \oplus a = a$) satisfying the Kozen induction axioms.

---

## Motivation

In standard mathematical algebra (Golan 1999, Kuich & Salomaa 1986):
* A **semiring** (or rig) is an algebraic structure $(S, +, \cdot, 0, 1)$ such that $(S, +, 0)$ is a commutative monoid, $(S, \cdot, 1)$ is a monoid, multiplication distributes over addition from both left and right, and $0$ annihilates multiplication ($0 \cdot a = a \cdot 0 = 0$).
* A **star semiring** (or closed semiring) adds a unary operation $*: S \to S$ satisfying infinite series summation closure properties.
* A **Kleene algebra** is an idempotent star semiring ($a + a = a$).

### The Architectural Problem in AlgebraX

In previous versions, `algebrax.algebra._semiring.py` defined:
```python
# Legacy conflation
class Semiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], Protocol):
```

This bundling caused severe structural contradictions:
1. **Rings Failed Semiring Conformance**: Mathematically, every ring is a semiring ($\text{Semiring} \subset \text{Ring} \subset \text{CommRing} \subset \text{Field}$). A ring simply adds additive inverses (`neg`, `sub`). However, because `Semiring` demanded `star`, calling `isinstance(IntegerRing(), Semiring)` or `isinstance(PolynomialAlgebra(...), Semiring)` returned `False`!
2. **Forced `NotImplementedError` Boilerplate**: `MonoidAlgebraSemiring` was forced to implement:
   ```python
   def star(self, a: SparseVector[K, T]) -> SparseVector[K, T]:
       raise NotImplementedError('Kleene star not implemented for MonoidAlgebraSemiring')
   ```
   This violated the Principle of Least Surprise and polluted pure mathematical types with artificial runtime exceptions.
3. **Overloaded Algorithm Signatures**: Standard matrix multiplication, tensor contraction, Hodge-Laplacians, and simplicial cohomology require only `zero, one, add, mul`. None of them ever call `star`. Requiring `HasStar` artificially restricted the input domain of linear and multilinear solvers.

---

## Rationale

### Council Alignment

* **⚖️ Noether (Symmetry & Invariance)**: Preserves the unbroken mathematical subtyping chain:
  $$\text{AddMonoid} \subset \text{Semiring} \subset \text{Ring} \subset \text{CommRing} \subset \text{DivisionRing} \subset \text{Field}$$
  Any object that can be added and multiplied with distributivity and identities is an invariant semiring.
* **🧩 Russell (Taxonomy & Consistency)**: Orthogonalizes operational capabilities. A rig does not have a star; a star semiring does. Idempotence is witnessed by `LawIdempotent` ($a \oplus a = a$), cleanly distinguishing general star semirings (like Dual Numbers $\mathbb{R}[\varepsilon]/(\varepsilon^2)$ or Standard $\mathbb{R}$) from Kleene algebras (like Tropical $(\mathbb{R} \cup \{\infty\}, \min, +)$ or Boolean $(\mathbb{B}, \vee, \wedge)$).
* **⚡ Shannon (Efficiency & Zero-Boxing)**: Eliminates dead code paths and stub exceptions. Functions accepting `Semiring[V]` operate on unboxed carriers without checking for nonexistent star operators.
* **🔬 Popper (Falsifiability & Multi-Layered Testing)**: The verification engine ([`verify_semiring_laws`](file:///C:/dev/erivlis/algebrax/src/algebrax/verification.py)) already tested strictly the 9 ring-like axioms (associativity, commutativity, identities, distributivity, annihilation) without testing `star`. Decoupling aligns the verification suite with type definitions, adding explicit tests for `verify_star_semiring_laws` and `verify_kleene_algebra_laws`.

---

## Specification

### 1. Layer 1 Law Witness: `LawIdempotent` (`src/algebrax/algebra/_mixins.py`)

Equational axiom witness signaling additive idempotence ($a \oplus a = a$):

```python
@runtime_checkable
class LawIdempotent(Protocol):
    r"""Equational axiom witness: binary addition is idempotent ($a \oplus a = a$)."""

    @property
    def is_idempotent(self) -> Literal[True]:
        return True
```

### 2. Layer 2 Protocols (`src/algebrax/algebra/_semiring.py`)

```python
from typing import Literal, Protocol, TypeVar, runtime_checkable
from algebrax.algebra._mixins import HasAdd, HasMul, HasOne, HasStar, HasZero, LawIdempotent

V = TypeVar('V')


@runtime_checkable
class Semiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], Protocol):
    r"""A mathematical Semiring (Rig / Hemiring) $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$.

    Combines an additive commutative monoid $\langle V, \mathbf{0}, + \rangle$
    and a multiplicative monoid $\langle V, \mathbf{1}, \cdot \rangle$ satisfying two-sided distributivity
    and zero annihilation.
    """
    ...


@runtime_checkable
class StarSemiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], Protocol):
    r"""A Star Semiring (Closed / Conway Semiring) $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$.

    Equipped with a unary Kleene star closure operation $*: V \to V$ satisfying:
        $a^* = \mathbf{1} + a \cdot a^* = \mathbf{1} + a^* \cdot a$.
    """
    ...

# Standard mathematical synonyms:
ClosedSemiring = StarSemiring
ConwaySemiring = StarSemiring


@runtime_checkable
class KleeneAlgebra(
    HasZero[V],
    HasAdd[V],
    HasOne[V],
    HasMul[V],
    HasStar[V],
    LawIdempotent,
    Protocol,
):
    r"""A Kleene Algebra $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$ with $a \oplus a = a$.

    An idempotent star semiring satisfying Kozen's induction axioms:
        $\mathbf{1} + a \cdot a^* \le a^*, \quad b + a \cdot x \le x \implies a^* \cdot b \le x$.
    """

    @property
    def is_idempotent(self) -> Literal[True]:
        return True
```

### 3. Structural Protocol Attribute Lattice

In [`tests/algebrax/test_type_safety.py`](file:///C:/dev/erivlis/algebrax/tests/algebrax/test_type_safety.py), the protocol attributes satisfy:

```python
attrs(AddMonoid) < attrs(Semiring) == {'zero', 'add', 'one', 'mul'}
attrs(Monoid) < attrs(Semiring)
attrs(Semiring) < attrs(Ring) == {'zero', 'one', 'add', 'neg', 'sub', 'mul', 'is_associative'}
attrs(Semiring) < attrs(StarSemiring) == {'zero', 'add', 'one', 'mul', 'star'}
attrs(StarSemiring) < attrs(KleeneAlgebra) == {'zero', 'add', 'one', 'mul', 'star', 'is_idempotent'}
```

### 4. Taxonomy Audit of Built-in Semirings

| Class | Category | Base Protocols | Notes |
| :--- | :--- | :--- | :--- |
| `StandardSemiring` | Arithmetic | `StarSemiring[T_num]` | Star defined for $|a| < 1$ as $\frac{1}{1-a}$ |
| `ModularSemiring` | Arithmetic | `Semiring[int]` | Pure finite ring quotient $\mathbb{Z}/n\mathbb{Z}$ |
| `TropicalSemiring` | Optimization | `KleeneAlgebra[float]` | $(\mathbb{R} \cup \{\infty\}, \min, +, \infty, 0)$; $a^* = 0$ for $a \ge 0$ |
| `ArcticSemiring` | Optimization | `KleeneAlgebra[float]` | $(\mathbb{R} \cup \{-\infty\}, \max, +, -\infty, 0)$ |
| `ViterbiSemiring` | Optimization | `KleeneAlgebra[float]` | $([0, 1], \max, \cdot, 0, 1)$; $a^* = 1$ |
| `BottleneckSemiring` | Optimization | `KleeneAlgebra[float]` | $(\mathbb{R}^+, \max, \min, 0, \infty)$ |
| `BooleanSemiring` | Logic | `KleeneAlgebra[bool]` | $(\mathbb{B}, \vee, \wedge, \text{False}, \text{True})$; $a^* = \text{True}$ |
| `LukasiewiczSemiring`| Logic | `KleeneAlgebra[float]` | Multi-valued fuzzy logic |
| `LogSemiring` | Statistical | `StarSemiring[float]` | Smooth log-sum-exp semiring |
| `DualNumberAlgebra` | Automatic Diff | `StarSemiring`, `Algebra`, `LawCommutative` | Dual number Taylor series star closure |
| `MonoidAlgebraSemiring` | Algebraic | `Semiring`, `Semimodule` | Pure semiring without artificial star stub |
| `PolynomialAlgebra` | Algebraic | `Semiring`, `Algebra`, `CommRing` | Univariate polynomials $R[x]$ |

### 5. Axiomatic Verification Extensions (`src/algebrax/verification.py`)

Two verification functions are added to the verification suite:
* `verify_star_semiring_laws(semiring, samples, tol)`:
  Validates Conway closure:
  $$a^* \approx \mathbf{1} + a \cdot a^* \approx \mathbf{1} + a^* \cdot a$$
* `verify_kleene_algebra_laws(semiring, samples, tol)`:
  Validates full semiring axioms + star closure axioms + addition idempotency ($a \oplus a = a$).

---

## Backwards Compatibility

1. **Fully Backwards Compatible**: Existing call sites passing `semiring: Semiring[V]` to matrix, tensor, or homology functions continue to work without modification.
2. **Expanded Compatibility**: Any standard `Ring`, `Field`, or `Algebra` now passes `isinstance(x, Semiring)`, allowing polynomial rings and matrix rings to be passed directly to generalized semiring routines without wrapping or adapting.
3. **No Breaking Changes**: Classes that previously implemented `star` retain `star` and satisfy both `Semiring` and `StarSemiring`.

---

## How to Teach This / Documentation Plan

* **Guide Update**: Update `docs/guide/algebra/semirings.md` to introduce the three-tiered model: Pure Rig, Star Semiring, and Kleene Algebra.
* **Docstrings**: Update `Semiring` AMDS docstrings to state $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$, and provide clear cross-references to `StarSemiring` and `KleeneAlgebra`.

---

## Reference Implementation

* Core protocols: [`src/algebrax/algebra/_semiring.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/algebra/_semiring.py)
* Idempotent witness: [`src/algebrax/algebra/_mixins.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/algebra/_mixins.py)
* Structural verification: [`tests/algebrax/test_type_safety.py`](file:///C:/dev/erivlis/algebrax/tests/algebrax/test_type_safety.py)

---

## Rejected Ideas

1. **Keep `star` as an optional method on `Semiring` with default returning `None`**:
   * *Rejected*: Contradicts PEP 544 structural subtyping. If `star` exists on the protocol, `hasattr(s, 'star')` is always true, destroying the ability to statically or dynamically check whether an algebra supports Kleene closure.
2. **Create a separate `Rig` protocol and keep `Semiring` with `star`**:
   * *Rejected*: In standard international mathematical usage (Bourbaki, Golan, MacLane), "Rig" and "Semiring" are identical synonyms ("a ring without negative elements"). Renaming standard semirings to "Rig" would confuse practitioners and deviate from NumPy/SciPy/SymPy community conventions.

---

## Open Questions

None. The mathematical definitions are established standards in universal algebra, formal language theory, and category theory.

---

## Change Log

* **2026-11-13**: Initial proposal draft authored, validated, and registered in Phase 6.
