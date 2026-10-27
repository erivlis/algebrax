---
title: "EP-0201: Algebraic Homomorphisms, Ideals & Canonical Quotients"
description: "Formalize mathematical homomorphisms, algebraic ideals, and canonical quotient structures in algebrax, establishing the First Isomorphism Theorem and replacing ad-hoc quotient callables."
icon: lucide/split
status: draft
---

# EP-0201: Algebraic Homomorphisms, Ideals & Canonical Quotients

| Field        | Value                                                              |
|:-------------|:-------------------------------------------------------------------|
| **EP**       | 0201                                                               |
| **Title**    | Algebraic Homomorphisms, Ideals & Canonical Quotients              |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Antigravity                        |
| **Sponsor**  | Core Maintainers                                                   |
| **Delegate** | ⚖️ Noether (Symmetries & Invariant Ideals) & 🧩 Russell (Taxonomy & Order) |
| **Status**   | Draft                                                              |
| **Type**     | Standards Track                                                    |
| **Created**  | 2026-10-27                                                         |
| **Updated**  | 2026-10-27                                                         |
| **Replaces** | —                                                                  |
| **Superseded-By** | —                                                             |

---

## Abstract

This proposal introduces a mathematically rigorous, Lean 4 Mathlib-aligned framework for algebraic structure-preserving maps (**Homomorphisms**), sub-structures with absorption (**Ideals**), and universal canonical projections (**Quotients**) into AlgebraX. Specifically, EP-0201 establishes:
1. First-class protocols for algebraic morphisms: `RingHom[R1, R2]`, `GroupHom[G1, G2]`, `LinearMap[V, W, K]`, and `LieAlgebraHom[L1, L2]`.
2. Mathematical **Ideals**: `Ideal[V]` (two-sided, left, right), `PrincipalIdeal[V]`, and `LieIdeal[V]`, unifying absorbing sub-structures across rings, algebras, and Lie algebras.
3. Canonical universal quotient constructors: `QuotientRing(ring, ideal)` and `QuotientAlgebra(algebra, ideal)`, replacing ad-hoc, untyped user `quotient_fn` callables with principled normal form reduction operators.
4. Categorical kernel connections realizing the **First Isomorphism Theorem**: every homomorphism $\phi: R \to S$ has a kernel ideal $\ker \phi = \{x \in R \mid \phi(x) = 0\}$ yielding a canonical isomorphism $R / \ker \phi \cong \operatorname{im} \phi$.
5. Property-based verification in `algebrax.verification`: `verify_ring_homomorphism_laws`, `verify_ideal_absorption_laws`, and `verify_quotient_ring_laws`.

All abstractions preserve AlgebraX's fundamental carrier rule: zero-overhead, unboxed raw element types (no `Coset` wrapper allocations on the heap).

---

## Motivation

AlgebraX provides sophisticated quotienting in domain structures such as `QuotientMonoidAlgebraSemiring` and translational subalgebras in `se(3)`. However, the mathematical foundation underlying these constructions is currently unformalized:
1. **Ad-Hoc Quotient Callables**: Currently, `QuotientMonoidAlgebraSemiring` relies on an arbitrary `quotient_fn: Callable[[K], K]` without algebraic guarantees, type checking, or verification that the function respects congruence relations or ideal absorption ($r \cdot x \in I$).
2. **Absence of Ideals**: Ideals—the cornerstone of modern algebra, algebraic geometry, and modular arithmetic—are completely absent as formalized protocols in AlgebraX. They exist only as descriptive comments in docstrings.
3. **No Morphism Protocols**: While `algebrax.algebra` defines semigroups, monoids, groups, rings, semirings, and algebras, it does not define maps between them. There is no `RingHom`, no `LinearMap`, and no standard protocol for evaluating whether a map preserves operations ($\phi(a \cdot b) = \phi(a) \cdot \phi(b)$).
4. **Lean 4 Mathlib Disconnect**: In Lean 4 Mathlib, abstract algebra is anchored by bundled categories (`RingCat`, `ModuleCat R`) where morphisms are typed homomorphisms (`RingHom`, `LinearMap`). Quotients are universally constructed as coequalizers of kernels:
   $$R / \ker \phi \cong \operatorname{im} \phi$$

By formalizing `RingHom`, `Ideal`, and canonical quotients, AlgebraX unifies modular arithmetic ($\mathbb{Z}/n\mathbb{Z}$), dual numbers ($\mathbb{R}[\epsilon]/(\epsilon^2)$), truncated polynomial rings ($\mathbb{R}[x]/(x^n)$), and symmetry group cosets under a single, rigorous, zero-cost algebraic protocol hierarchy.

---

## Rationale & Council Alignment

- **⚖️ Noether (Structural Conservation, Symmetries & Invariants)**:
  Ideals are invariant subspaces under the algebraic group/ring action ($R \cdot I \subseteq I$, $[L, I] \subseteq I$). Noether's core conservation principles require that invariant kernels of physical symmetries map directly to algebraic ideals.
- **🧩 Russell (Taxonomy, Ontological Coherence & Deductive Order)**:
  Bridges universal algebra with category theory. Formulates ideals not as ad-hoc sets, but as the natural kernels of categorical homomorphisms in `algebrax.algebra`.
- **⚡ Shannon (Zero Bloat & Unboxed Efficiency)**:
  Rejects object-oriented wrappers such as `class Coset(Generic[V])` or dynamic quotient class generation. Elements of $R/I$ remain raw, unboxed values $V$ kept in canonical normal form via `ideal.reduce(x)`.
- **🔬 Popper (Falsifiability & Empirical Invariants)**:
  Supplies property-based verification testing ideal absorption axioms ($x \in I \land r \in R \implies r \cdot x \in I$), kernel containment ($\phi(x) = 0 \iff x \in \ker \phi$), and well-defined quotient operations ($(a + I) \cdot (b + I) = (a \cdot b) + I$).
- **💡 Feynman (Demystification & Intuitive Freshness)**:
  Explains ideals plainly: *"An ideal is just the algebraic generalization of 'multiples of a number' (like all multiples of 5). When you divide by an ideal, you are just doing remainder arithmetic where everything in the ideal gets squashed to zero."*

---

## Specification

### 1. Homomorphism Protocols (`src/algebrax/algebra/homomorphisms.py`)

Algebraic homomorphisms are maps between algebraic structures that preserve operations and identities:

```python
from typing import Generic, Protocol, TypeVar, runtime_checkable
from collections.abc import Callable

Dom = TypeVar("Dom")
Cod = TypeVar("Cod")
K = TypeVar("K")


@runtime_checkable
class Homomorphism(Protocol[Dom, Cod]):
    """Base protocol for a mathematical homomorphism."""

    def __call__(self, x: Dom) -> Cod:
        """Apply the homomorphism to an element."""
        ...


@runtime_checkable
class RingHom(Homomorphism[Dom, Cod], Protocol[Dom, Cod]):
    r"""A ring homomorphism $\phi : R_1 \to R_2$.

    Preserves:
    - Addition: $\phi(a + b) = \phi(a) + \phi(b)$
    - Multiplication: $\phi(a \cdot b) = \phi(a) \cdot \phi(b)$
    - Zero: $\phi(0) = 0$
    - One: $\phi(1) = 1$
    """
    ...


@runtime_checkable
class GroupHom(Homomorphism[Dom, Cod], Protocol[Dom, Cod]):
    r"""A group homomorphism $\phi : G_1 \to G_2$ preserving $\phi(a \cdot b) = \phi(a) \cdot \phi(b)$."""
    ...


@runtime_checkable
class LinearMap(Homomorphism[Dom, Cod], Protocol[Dom, Cod, K]):
    r"""A module/vector space linear map $\phi : V \to W$ over scalar field $K$.

    Preserves:
    - Addition: $\phi(v_1 + v_2) = \phi(v_1) + \phi(v_2)$
    - Scalar multiplication: $\phi(c \cdot v) = c \cdot \phi(v)$
    """
    ...


@runtime_checkable
class LieAlgebraHom(Homomorphism[Dom, Cod], Protocol[Dom, Cod]):
    r"""A Lie algebra homomorphism $\phi : \mathfrak{g}_1 \to \mathfrak{g}_2$ preserving Lie brackets:
    $$\phi([x, y]) = [\phi(x), \phi(y)]$$
    """
    ...
```

### 2. The Ideal Protocol Hierarchy (`src/algebrax/algebra/ideals.py`)

An ideal $I \subseteq R$ is an additive subgroup that absorbs multiplication by elements of $R$ ($r \cdot x \in I$ and $x \cdot r \in I$).

```python
from typing import Generic, Protocol, TypeVar, runtime_checkable
from collections.abc import Iterable

V = TypeVar("V")


@runtime_checkable
class Ideal(Protocol[V]):
    r"""A mathematical ideal $I \subseteq R$.

    Provides:
    - Membership testing: `x in ideal`
    - Canonical normal form reduction: `ideal.reduce(x)` mapping $x \mapsto [x] \in R/I$.
    """

    def contains(self, element: V) -> bool:
        r"""Check if element $\in I$."""
        ...

    def reduce(self, element: V) -> V:
        r"""Compute the canonical normal form representative of $element \pmod I$.

        In the quotient $R/I$, $x \sim y \iff \mathrm{reduce}(x) == \mathrm{reduce}(y)$.
        """
        ...

    def __contains__(self, element: V) -> bool:
        return self.contains(element)


@runtime_checkable
class PrincipalIdeal(Ideal[V], Protocol[V]):
    r"""A principal ideal $I = (a) = aR$ generated by a single element $a$."""

    @property
    def generator(self) -> V:
        r"""The generating element $a$."""
        ...


@runtime_checkable
class LieIdeal(Ideal[V], Protocol[V]):
    r"""A Lie ideal $\mathfrak{i} \subseteq \mathfrak{g}$ satisfying $[\mathfrak{g}, \mathfrak{i}] \subseteq \mathfrak{i}$."""
    ...
```

### 3. Concrete Ideal Implementations (`src/algebrax/algebra/ideals.py`)

AlgebraX provides high-performance, standard ideal implementations:

```python
class IntegerModuloIdeal:
    """The principal ideal (n) = nZ in the ring of integers Z."""

    def __init__(self, modulus: int) -> None:
        if modulus <= 0:
            raise ValueError(f"Modulus must be positive, got {modulus}")
        self.modulus = modulus

    @property
    def generator(self) -> int:
        return self.modulus

    def contains(self, element: int) -> bool:
        return element % self.modulus == 0

    def reduce(self, element: int) -> int:
        return element % self.modulus


class NilpotentIdeal:
    r"""Ideal $(\epsilon^k) = 0$ for dual and hyper-dual numbers.

    Used to reduce higher-order infinitesimal terms $\epsilon^k \mapsto 0$.
    """

    def __init__(self, nilpotency_degree: int = 2) -> None:
        self.nilpotency_degree = nilpotency_degree

    def contains(self, degree: int) -> bool:
        return degree >= self.nilpotency_degree

    def reduce(self, degree: int) -> int | None:
        return None if degree >= self.nilpotency_degree else degree


class PolynomialTruncationIdeal:
    r"""Ideal $(x^n)$ in polynomial ring $K[x]$, truncating all degrees $\ge n$."""

    def __init__(self, max_degree: int) -> None:
        self.max_degree = max_degree

    def contains(self, poly: dict[int, float]) -> bool:
        return all(deg >= self.max_degree for deg in poly if poly[deg] != 0.0)

    def reduce(self, poly: dict[int, float]) -> dict[int, float]:
        return {deg: coeff for deg, coeff in poly.items() if deg < self.max_degree and coeff != 0.0}
```

### 4. Canonical Quotient Ring Constructor (`src/algebrax/algebra/quotient.py`)

Instead of requiring ad-hoc functions, `QuotientRing` and `QuotientSemiring` construct formal quotient structures from any valid ring and ideal:

```python
from algebrax.algebra.protocols import CommRing, Semiring


class QuotientRing(CommRing[V]):
    r"""Canonical quotient ring $R / I$.

    Elements are canonical coset representatives computed via $I.\mathrm{reduce}(x)$.
    Addition and multiplication satisfy:
    $[a] + [b] = [a + b]$
    $[a] \cdot [b] = [a \cdot b]$
    """

    def __init__(self, base_ring: CommRing[V], ideal: Ideal[V]) -> None:
        self.base_ring = base_ring
        self.ideal = ideal

    def zero(self) -> V:
        return self.ideal.reduce(self.base_ring.zero())

    def one(self) -> V:
        return self.ideal.reduce(self.base_ring.one())

    def add(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_ring.add(a, b))

    def mul(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_ring.mul(a, b))

    def neg(self, a: V) -> V:
        return self.ideal.reduce(self.base_ring.neg(a))

    def sub(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_ring.sub(a, b))

    def eq(self, a: V, b: V) -> bool:
        return self.ideal.reduce(a) == self.ideal.reduce(b)
```

### 5. Kernel Ideals & The First Isomorphism Theorem

Every `RingHom` defines a canonical kernel ideal:

```python
class KernelIdeal(Ideal[Dom]):
    r"""The kernel ideal $\ker \phi = \{ x \in R_1 \mid \phi(x) = 0_{R_2} \}$."""

    def __init__(self, hom: RingHom[Dom, Cod], cod_ring: CommRing[Cod], reducer: Callable[[Dom], Dom]) -> None:
        self.hom = hom
        self.cod_ring = cod_ring
        self._reducer = reducer

    def contains(self, element: Dom) -> bool:
        return self.cod_ring.eq(self.hom(element), self.cod_ring.zero())

    def reduce(self, element: Dom) -> Dom:
        return self._reducer(element)
```

### 6. Verification Test Suite (`src/algebrax/verification/quotients.py`)

```python
def verify_ring_homomorphism_laws(
    hom: RingHom[Dom, Cod],
    ring_dom: CommRing[Dom],
    ring_cod: CommRing[Cod],
    samples: list[Dom],
) -> None:
    """Verify that a ring homomorphism preserves addition, multiplication, 0, and 1."""
    # Preserves 0 and 1
    assert ring_cod.eq(hom(ring_dom.zero()), ring_cod.zero())
    assert ring_cod.eq(hom(ring_dom.one()), ring_cod.one())

    for a in samples:
        for b in samples:
            # phi(a + b) == phi(a) + phi(b)
            assert ring_cod.eq(
                hom(ring_dom.add(a, b)),
                ring_cod.add(hom(a), hom(b)),
            )
            # phi(a * b) == phi(a) * phi(b)
            assert ring_cod.eq(
                hom(ring_dom.mul(a, b)),
                ring_cod.mul(hom(a), hom(b)),
            )


def verify_ideal_absorption_laws(
    ring: CommRing[V],
    ideal: Ideal[V],
    ring_samples: list[V],
    ideal_samples: list[V],
) -> None:
    """Verify that I is closed under addition, negation, and absorbs multiplication."""
    for i in ideal_samples:
        assert ideal.contains(i)
        assert ideal.contains(ring.neg(i))
        for r in ring_samples:
            # r * i in I
            assert ideal.contains(ring.mul(r, i))
            # i * r in I
            assert ideal.contains(ring.mul(i, r))
```

---

## Backwards Compatibility

1. **Seamless Integration with `QuotientMonoidAlgebraSemiring`**:
   The existing `QuotientMonoidAlgebraSemiring` constructor accepts `quotient_fn: Callable[[K], K]`. Because `Ideal[V].reduce` is a standard method, existing code can pass `quotient_fn=my_ideal.reduce`. In addition, `QuotientMonoidAlgebraSemiring` will be updated to optionally accept `ideal: Ideal[K]`.
2. **Zero Breaking Changes**:
   All new protocols (`RingHom`, `Ideal`, `QuotientRing`) are strictly additive and reside in `algebrax.algebra`.

---

## How to Teach This / Documentation Plan

1. **Tutorial Guide (`docs/guides/ideals-and-quotients.md`)**:
   Step-by-step exposition showing how to construct:
   - Modular arithmetic $\mathbb{Z}/12\mathbb{Z}$ (clock arithmetic).
   - Dual numbers $\mathbb{R}[\epsilon]/(\epsilon^2)$ for automatic differentiation.
   - Truncated Taylor polynomials $\mathbb{R}[x]/(x^4)$.
2. **Lean 4 Mathlib Bridge Guide**:
   Explain the direct correspondence between `AlgebraX`'s `QuotientRing(R, I)` and Mathlib's `Ideal.Quotient`.

---

## Reference Implementation

A reference prototype for `IntegerModuloIdeal`, `KernelIdeal`, and `QuotientRing` has been validated in the Council exploration `references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md`.

---

## Rejected Ideas

1. **Wrapping Cosets in a Class `class Coset(Generic[V])`**:
   *Rejected*: Violates Shannon's zero-bloat principle. Coset wrapping creates millions of intermediate heap objects during matrix operations. Unboxed raw representatives with canonical reduction (`ideal.reduce(x)`) provide mathematical correctness at native speed.
2. **Dynamic Class Generation per Ideal (`type("QuotientRing", ...)`)**:
   *Rejected*: Obscures static type inference, ruins IDE autocomplete, and fails serialization. Parameterized protocol instances (`QuotientRing(ring, ideal)`) are clean, transparent, and fully type-checked.
3. **Pure Predicate Ideals without Normal Form Reducers (`Ideal.contains` only)**:
   *Rejected*: A mathematical quotient $R/I$ requires computing equality and operations on coset representatives. Without a canonical reduction function (`reduce`), algorithms cannot verify if $[a] = [b]$ or compute sparse matrix zero-elimination.

---

## Open Questions

1. **Non-Commutative Ideals**:
   Should we distinguish `LeftIdeal[V]`, `RightIdeal[V]`, and `TwoSidedIdeal[V]` at the protocol level, or provide a unified `Ideal[V]` with flags?
   *Recommendation*: Keep `Ideal[V]` as the two-sided default, with `LeftIdeal` and `RightIdeal` as specialized protocols when needed in non-commutative matrix algebras.

---

## Change Log

- **2026-10-27**: Initial draft authored following Council consensus on EXP-0005.
