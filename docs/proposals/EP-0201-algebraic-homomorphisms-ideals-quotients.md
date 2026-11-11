---
title: "EP-0201: Algebraic Homomorphisms, Ideals & Canonical Quotients"
description: "Formalize mathematical homomorphisms, algebraic ideals, and canonical quotient structures in algebrax, establishing the First Isomorphism Theorem and replacing ad-hoc quotient callables."
icon: lucide/split
status: final
---

# EP-0201: Algebraic Homomorphisms, Ideals & Canonical Quotients

| Field        | Value                                                              |
|:-------------|:-------------------------------------------------------------------|
| **EP**       | 0201                                                               |
| **Title**    | Algebraic Homomorphisms, Ideals & Canonical Quotients              |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Antigravity                        |
| **Sponsor**  | Core Maintainers                                                   |
| **Delegate** | ⚖️ Noether (Symmetries & Invariant Ideals) & 🧩 Russell (Taxonomy & Order) |
| **Status**   | Final                                                              |
| **Type**     | Standards Track                                                    |
| **Created**  | 2026-10-27                                                         |
| **Updated**  | 2026-11-11                                                         |
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

### 1. Homomorphism Protocols (`src/algebrax/algebra/_homomorphisms.py`)

In strict compliance with [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md) (**Law of Flat Protocol Composition**), algebraic homomorphisms are flat `Protocol` definitions (algebraic isomers of `__call__`) with scalar ring parameter `R` placed first on `LinearMap[R, Dom, Cod]`:

```python
from typing import Generic, Protocol, TypeVar, runtime_checkable

R = TypeVar("R")
Dom = TypeVar("Dom", contravariant=True)
Cod = TypeVar("Cod", covariant=True)


@runtime_checkable
class Homomorphism(Protocol[Dom, Cod]):
    """Base protocol for a mathematical homomorphism."""

    def __call__(self, x: Dom) -> Cod:
        """Apply the homomorphism to an element."""
        ...


@runtime_checkable
class RingHom(Protocol[Dom, Cod]):
    r"""A ring homomorphism $\phi : R_1 \to R_2$."""

    def __call__(self, x: Dom) -> Cod: ...


@runtime_checkable
class GroupHom(Protocol[Dom, Cod]):
    r"""A group homomorphism $\phi : G_1 \to G_2$ preserving $\phi(a \cdot b) = \phi(a) \cdot \phi(b)$."""

    def __call__(self, x: Dom) -> Cod: ...


@runtime_checkable
class LinearMap(Protocol[R, Dom, Cod]):
    r"""A module/vector space linear map $\phi : V \to W$ over scalar ring/field $R$."""

    def __call__(self, x: Dom) -> Cod: ...


@runtime_checkable
class LieAlgebraHom(Protocol[Dom, Cod]):
    r"""A Lie algebra homomorphism $\phi : \mathfrak{g}_1 \to \mathfrak{g}_2$ preserving Lie brackets."""

    def __call__(self, x: Dom) -> Cod: ...
```

### 2. The Ideal Protocol Hierarchy (`src/algebrax/algebra/_ideals.py`)

Following [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md), three orthogonal Layer 1 atomic mixins (`HasContains[V]`, `HasReduce[V]`, `HasGenerator[V]`) are defined in `_mixins.py`, and all Layer 2 ideal protocols are flat compositions of those mixins (keeping `__protocol_attrs__` strictly minimal at `{'contains', 'reduce'}` and `{'contains', 'reduce', 'generator'}`):

```python
from typing import Protocol, TypeVar, runtime_checkable
from algebrax.algebra._mixins import HasContains, HasGenerator, HasReduce

V = TypeVar("V")


@runtime_checkable
class Ideal(HasContains[V], HasReduce[V], Protocol):
    r"""A two-sided mathematical ideal $I \triangleleft R$."""
    ...


@runtime_checkable
class LeftIdeal(HasContains[V], HasReduce[V], Protocol):
    r"""A left ideal $I \subseteq R$ satisfying $R \cdot I \subseteq I$."""
    ...


@runtime_checkable
class RightIdeal(HasContains[V], HasReduce[V], Protocol):
    r"""A right ideal $I \subseteq R$ satisfying $I \cdot R \subseteq I$."""
    ...


@runtime_checkable
class PrincipalIdeal(HasContains[V], HasReduce[V], HasGenerator[V], Protocol):
    r"""A principal ideal $I = (a) = aR$ generated by a single element $a$."""
    ...


@runtime_checkable
class LieIdeal(HasContains[V], HasReduce[V], Protocol):
    r"""A Lie ideal $\mathfrak{i} \subseteq \mathfrak{g}$ satisfying $[\mathfrak{g}, \mathfrak{i}] \subseteq \mathfrak{i}$."""
    ...
```

### 3. Concrete Ideal Implementations (`src/algebrax/algebra/_ideals.py`)

In accordance with [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md), concrete Layer 3 ideal implementations nominally subclass their primary Layer 2 protocols (`PrincipalIdeal`, `Ideal`, `LieIdeal`):

```python
class IntegerModuloIdeal(PrincipalIdeal[int]):
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


class NilpotentIdeal(PrincipalIdeal[int | dict[int, T]]):
    r"""Principal ideal $(\epsilon^k) = 0$ for dual and hyper-dual numbers."""

    def __init__(self, nilpotency_degree: int = 2) -> None:
        if nilpotency_degree <= 0:
            raise ValueError(f"nilpotency_degree must be positive, got {nilpotency_degree}")
        self.nilpotency_degree = nilpotency_degree

    @property
    def generator(self) -> int:
        return self.nilpotency_degree

    def contains(self, element: int | dict[int, T]) -> bool:
        if isinstance(element, int):
            return element >= self.nilpotency_degree
        return all(deg >= self.nilpotency_degree for deg, coeff in element.items() if coeff != 0)

    def reduce(self, element: int | dict[int, T]) -> int | dict[int, T] | None:
        if isinstance(element, int):
            return None if element >= self.nilpotency_degree else element
        return {deg: coeff for deg, coeff in element.items() if deg < self.nilpotency_degree and coeff != 0}


class PolynomialTruncationIdeal(PrincipalIdeal[dict[int, T]], Generic[T]):
    r"""Principal ideal $(x^n)$ in polynomial ring $K[x]$, truncating all degrees $\ge n$."""

    def __init__(self, max_degree: int, coeff_one: T = 1) -> None:
        self.max_degree = max_degree
        self._coeff_one = coeff_one

    @property
    def generator(self) -> dict[int, T]:
        return {self.max_degree: self._coeff_one}

    def contains(self, element: dict[int, T]) -> bool:
        return all(deg >= self.max_degree for deg, coeff in element.items() if coeff != 0)

    def reduce(self, element: dict[int, T]) -> dict[int, T]:
        return {deg: coeff for deg, coeff in element.items() if deg < self.max_degree and coeff != 0}
```

### 4. Unified Quotient Constructors (`src/algebrax/algebra/_quotient.py`)

Mathematical quotient structures form a strict refinement hierarchy: every `Ring` is a `Semiring` with additive inverses (`neg`, `sub`), and every `Algebra` over scalar ring $R$ is a ring/module equipped with bilinear scalar action (`smul`). Consequently, `QuotientSemiring`, `QuotientRing`, and `QuotientAlgebra` form a clean single-inheritance chain that eliminates method duplication while nominally satisfying their corresponding Layer 2 protocols:

```python
class QuotientSemiring(Semiring[V], Generic[V]):
    r"""Canonical quotient semiring $S / I$ reduced modulo an ideal or congruence reducer $I$."""

    def __init__(self, base_semiring: Semiring[V], ideal: Ideal[V]) -> None:
        self.base_semiring = base_semiring
        self.ideal = ideal

    @property
    def zero(self) -> V:
        return self.ideal.reduce(self.base_semiring.zero)

    @property
    def one(self) -> V:
        return self.ideal.reduce(self.base_semiring.one)

    def add(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_semiring.add(self.ideal.reduce(a), self.ideal.reduce(b)))

    def mul(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_semiring.mul(self.ideal.reduce(a), self.ideal.reduce(b)))

    def eq(self, a: V, b: V) -> bool:
        return self.ideal.reduce(a) == self.ideal.reduce(b)

    def project(self, x: V) -> V:
        return self.ideal.reduce(x)


class QuotientRing(QuotientSemiring[V], CommRing[V], Generic[V]):
    r"""Canonical quotient ring $R / I$ inheriting `zero`, `one`, `add`, `mul`, `eq`, `project`."""

    def __init__(self, base_ring: Ring[V] | CommRing[V], ideal: Ideal[V]) -> None:
        super().__init__(base_ring, ideal)
        self.base_ring = base_ring

    def neg(self, a: V) -> V:
        return self.ideal.reduce(self.base_ring.neg(self.ideal.reduce(a)))

    def sub(self, a: V, b: V) -> V:
        return self.ideal.reduce(self.base_ring.sub(self.ideal.reduce(a), self.ideal.reduce(b)))


class QuotientAlgebra(QuotientRing[V], NonAssocAlgebra[R, V], Generic[R, V]):
    r"""Canonical quotient algebra $A / I$ over scalar ring $R$."""

    def __init__(self, base_algebra: NonAssocAlgebra[R, V], ideal: Ideal[V]) -> None:
        super().__init__(base_algebra, ideal)
        self.base_algebra = base_algebra

    @property
    def one(self) -> V:
        one_val = getattr(self.base_algebra, "one", None)
        if one_val is None:
            raise AttributeError("Underlying non-associative algebra does not define a multiplicative identity one.")
        return self.ideal.reduce(one_val)

    def smul(self, r: R, m: V) -> V:
        return self.ideal.reduce(self.base_algebra.smul(r, self.ideal.reduce(m)))
```

### 5. Two-Level Quotient Architecture: `QuotientRing` vs. `QuotientMonoidAlgebra`

AlgebraX supports two complementary levels of quotient construction:

1. **Level 1 — Whole-Element Quotienting (`QuotientSemiring`, `QuotientRing`, `QuotientAlgebra`)**:
   - **Mechanism**: Evaluates `base.op(a, b)` in the ambient structure and projects the resulting element via `ideal.reduce(x: V) -> V`.
   - **Domain**: General carrier types $V$ (`int`, `dict[int, T]`, `dict[K, T]`) where ambient multiplication is well-defined and finite before reduction (e.g., $\mathbb{Z}/n\mathbb{Z}$, truncated polynomials $K[x]/(x^n)$ via `PolynomialTruncationIdeal`, Lie algebra quotients $\mathfrak{g}/\mathfrak{i}$ via `SubspaceLieIdeal`).
2. **Level 2 — In-Loop Basis-Pair Rewriting (`QuotientMonoidAlgebraSemiring`, `QuotientMonoidAlgebra`)**:
   - **Mechanism**: Specializes to free monoid algebras $S[M]$ and $R[M]$ over `SparseVector[K, T]`. During convolution $a \ast b$, each raw basis-pair product $(k_1 \cdot k_2, c_1 c_2)$ is rewritten *inside* the inner multiplication loop via `quotient_fn(raw_key, raw_coeff) -> Iterable[tuple[K, T]]`, with optional whole-element `ideal: Ideal[SparseVector[K, T]] | None = None`.
   - **Domain**: Algebras where basis multiplication itself rewrites keys and scales/splits coefficients before accumulation—such as Clifford algebras ($e_i e_j = -e_j e_i$), Galois fields ($\mathbb{F}_p[x]/(P(x))$), group algebras, and Kauffman bracket skein modules—avoiding intermediate degree explosion.
   - **Semiring vs. Ring/Algebra Separation**:
     - `MonoidAlgebraSemiring` and `QuotientMonoidAlgebraSemiring` operate over any coefficient `Semiring[T]` (including idempotent/tropical/Boolean semirings without negation), nominally satisfying `Semiring` and `Semimodule` (`smul`).
     - `MonoidAlgebra` (subclassing `MonoidAlgebraSemiring`) and `QuotientMonoidAlgebra` (subclassing `QuotientMonoidAlgebraSemiring` and `MonoidAlgebra`) add additive inverses (`neg`, `sub`), nominally satisfying `Algebra`, `Module`, `CommRing`, and `Ring`. `PolynomialAlgebra` and the Clifford algebras (`CliffordAlgebra`, `GeneralizedCliffordAlgebra`, `QuantumCliffordAlgebra`) inherit directly from `MonoidAlgebra` and `QuotientMonoidAlgebra`.

### 6. Kernel Ideals & The First Isomorphism Theorem

Every `RingHom` defines a canonical kernel ideal:

```python
class KernelIdeal(Ideal[Dom], Generic[Dom, Cod]):
    r"""The kernel ideal $\ker \phi = \{ x \in R_1 \mid \phi(x) = 0_{R_2} \}$."""

    def __init__(self, hom: RingHom[Dom, Cod], cod_ring: Semiring[Cod] | Ring[Cod], reducer: Callable[[Dom], Dom]) -> None:
        self.hom = hom
        self.cod_ring = cod_ring
        self._reducer = reducer

    def contains(self, element: Dom) -> bool:
        return self.hom(element) == self.cod_ring.zero

    def reduce(self, element: Dom) -> Dom:
        return self._reducer(element)
```

### 7. Verification Test Suite (`src/algebrax/verification.py`)

```python
def verify_ring_homomorphism_laws(
    hom: RingHom[Dom, Cod],
    ring_dom: Semiring[Dom] | Ring[Dom],
    ring_cod: Semiring[Cod] | Ring[Cod],
    samples: Sequence[Dom],
) -> bool:
    """Verify that a ring homomorphism preserves addition, multiplication, 0, and 1."""
    ...


def verify_ideal_absorption_laws(
    ring: Semiring[V] | Ring[V],
    ideal: Ideal[V],
    ring_samples: Sequence[V],
    ideal_samples: Sequence[V],
) -> bool:
    """Verify that I is closed under addition, negation, and absorbs multiplication."""
    ...


def verify_quotient_ring_laws(
    quotient_ring: QuotientSemiring[V] | QuotientRing[V],
    samples: Sequence[V],
) -> bool:
    """Verify canonical quotient projection and ring/semiring axioms on R/I."""
    ...
```

---

## Backwards Compatibility

1. **Separated `MonoidAlgebraSemiring` $\to$ `MonoidAlgebra` & `QuotientMonoidAlgebraSemiring` $\to$ `QuotientMonoidAlgebra`**:
   `MonoidAlgebraSemiring` remains a pure semiring/semimodule (without requiring `neg`), while `MonoidAlgebra` and `QuotientMonoidAlgebra` add `neg` and `sub` for coefficient rings. Both `QuotientMonoidAlgebraSemiring` and `QuotientMonoidAlgebra` accept an optional `ideal: Ideal[SparseVector[K, T]] | None = None` alongside `quotient_fn` while remaining 100% backwards-compatible.
2. **Zero Breaking Changes**:
   All new protocols (`Homomorphism`, `RingHom`, `GroupHom`, `LinearMap`, `LieAlgebraHom`, `Ideal`, `PrincipalIdeal`, `LieIdeal`) and classes (`MonoidAlgebra`, `QuotientMonoidAlgebra`, `QuotientSemiring`, `QuotientRing`, `QuotientAlgebra`) are strictly additive and reside in `algebrax.algebra`.

---

## How to Teach This / Documentation Plan

1. **Tutorial Guide (`docs/guide/algebra/polynomials_and_quotients.md`)**:
   Step-by-step exposition showing how to construct:
   - Modular arithmetic $\mathbb{Z}/12\mathbb{Z}$ (clock arithmetic).
   - Dual numbers $\mathbb{R}[\epsilon]/(\epsilon^2)$ for automatic differentiation.
   - Truncated Taylor polynomials $\mathbb{R}[x]/(x^4)$.
   - When to use whole-element `QuotientRing`/`QuotientAlgebra` vs. in-loop `QuotientMonoidAlgebraSemiring`/`QuotientMonoidAlgebra`.
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
   *Resolution*: Keep `Ideal[V]` as the two-sided default, with `LeftIdeal` and `RightIdeal` as specialized flat protocols in `algebrax.algebra`.

---

## Change Log

- **2026-10-27**: Initial draft authored following Council consensus on EXP-0005.
- **2026-11-11**: Implemented `Homomorphism`, `RingHom`, `GroupHom`, `LinearMap`, `LieAlgebraHom`, `Ideal`, `PrincipalIdeal`, `LieIdeal`, `IntegerModuloIdeal`, `PolynomialTruncationIdeal`, `NilpotentIdeal`, `KernelIdeal`, `SubspaceLieIdeal`, unified `QuotientSemiring` $\to$ `QuotientRing` $\to$ `QuotientAlgebra` and `MonoidAlgebraSemiring` $\to$ `MonoidAlgebra` / `QuotientMonoidAlgebraSemiring` $\to$ `QuotientMonoidAlgebra` inheritance chains, and added verification functions (`verify_ring_homomorphism_laws`, `verify_ideal_absorption_laws`, `verify_quotient_ring_laws`). Status updated to `Final`.


