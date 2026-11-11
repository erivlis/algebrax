---
title: "EP-0204: Non-Associative & Quantum Algebras — Jordan, Alternative, Octonions & Poisson"
description: "Formalize Jordan algebras of quantum observables, alternative division algebras and octonions via Cayley-Dickson doubling, Malcev algebras, and Poisson algebras for Hamiltonian dynamics."
icon: lucide/atom
status: draft
---

# EP-0204: Non-Associative & Quantum Algebras — Jordan, Alternative, Octonions & Poisson

| Field             | Value                                                                         |
|:------------------|:------------------------------------------------------------------------------|
| **EP**            | 0204                                                                          |
| **Title**         | Non-Associative & Quantum Algebras — Jordan, Alternative, Octonions & Poisson |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                   |
| **Sponsor**       | Core Maintainers                                                              |
| **Delegate**      | ⚖️ Noether (Observables & Invariants) & 🧩 Russell (Taxonomy & Hierarchy)     |
| **Status**        | Draft                                                                         |
| **Type**          | Standards Track                                                               |
| **Created**       | 2026-10-28                                                                    |
| **Updated**       | 2026-10-28                                                                    |
| **Replaces**      | —                                                                             |
| **Superseded-By** | —                                                                             |

---

## Abstract

This proposal extends AlgebraX's pure algebraic hierarchy (`algebrax.algebra`) beyond associative structures,
establishing first-class mathematical protocols and unboxed implementations for the core non-associative and quantum
algebras of modern mathematics and physics. Specifically, EP-0204 introduces:

1. **Jordan Algebras (`JordanAlgebra[R, M]`)**: Commutative non-associative algebras satisfying the Jordan
   identity $(x \circ y) \circ x^2 = x \circ (y \circ x^2)$, formalizing quantum mechanical observables and the
   anticommutator product $A \circ B = \frac{1}{2} (AB + BA)$ on sparse Hermitian and symmetric matrices.
2. **Alternative Algebras (`AlternativeAlgebra[R, M]`)**: Non-associative algebras with alternating associators
   ($x (xy) = (xx)y$ and $(yx)x = y (xx)$), satisfying Artin's di-associativity theorem.
3. **The Octonions ($\mathbb{O}$)**: The 8-dimensional non-associative normed division algebra over $\mathbb{R}$,
   constructed via Cayley–Dickson doubling with sparse Fano-plane structure constants.
4. **Malcev Algebras (`MalcevAlgebra[R, M]`)**: The generalization of Lie algebras to alternative algebras, instantiated
   on the 7-dimensional imaginary octonions $\operatorname{Im} (\mathbb{O})$.
5. **Poisson Algebras (`PoissonAlgebra[R, M]`)**: Unifying commutative associative algebra with Lie brackets under the
   Leibniz derivation rule $\{f, g \cdot h\} = \{f, g\} \cdot h + g \cdot \{f, h\}$, formalizing classical Hamiltonian
   phase space dynamics.
6. **Property-Based Verification**: Rigorous axiom testing in `algebrax.verification`: `verify_jordan_laws`,
   `verify_alternative_laws`, and `verify_poisson_laws`.

All abstractions strictly preserve AlgebraX's canonical carrier constraint: unboxed raw values and sparse dictionaries,
introducing zero heap wrapping overhead, and strictly obey [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md) (**Law of Flat Protocol Composition**).

---

## Motivation

In Phase 6 ([EP-0190](EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md)), AlgebraX introduced the core
`NonAssocAlgebra[R, M]` protocol. However, `LieAlgebra` has remained its sole non-associative realization.

In mathematical physics and modern algebra:

1. **Lie–Jordan Duality**: In any associative matrix algebra, the ordinary product decomposes into an antisymmetric part
   (the Lie commutator $[A, B] = AB - BA$, representing states and generators of symmetry) and a symmetric part (the
   Jordan anticommutator $A \circ B = \frac{1}{2} (AB + BA)$, representing quantum observables and measurements).
   Without Jordan algebras, AlgebraX models only half of quantum mechanics.
2. **The Hurwitz Classification**: By Hurwitz's 1898 theorem, there are only four normed division algebras
   over $\mathbb{R}$: the Reals ($\mathbb{R}$), Complexes ($\mathbb{C}$), Quaternions ($\mathbb{H}$), and Octonions
   ($\mathbb{O}$). While $\mathbb{R}, \mathbb{C}, \mathbb{H}$ are associative, the Octonions $\mathbb{O}$ are
   non-associative, governing exceptional Lie groups ($G_2, F_4, E_6, E_7, E_8$), string theory compactifications, and
   Albert algebras.
3. **Hamiltonian Mechanics**: Classical dynamical systems require Poisson algebras, where energy conservation and
   Hamiltonian vector fields $\dot{f} = \{f, H\}$ depend on the Leibniz derivation rule.

By formalizing Jordan, Alternative, Octonion, and Poisson algebras, AlgebraX completes its non-associative architecture
with exact algebraic fidelity.

---

## Rationale & Council Alignment

- **⚖️ Noether (Symmetries, Observables & Conservation Laws)**:
  Quantum observables are self-adjoint operators closed under Jordan products, while classical conserved quantities are
  Poisson brackets commuting with the Hamiltonian ($\{f, H\} = 0$).
- **🧩 Russell (Taxonomy & Deductive Order)**:
  Cleanly situates all non-associative algebras as flat compositions of Layer 1 atomic mixins (`HasZero`, `HasAdd`,
  `HasNeg`, `HasMul`, `HasScale`), distinguishing commutative Jordan algebras from skew-symmetric Lie/Malcev algebras
  and alternative octonions.
- **⚡ Shannon (Zero Bloat & Sparse Structure Constants)**:
  Octonion multiplication is encoded as a sparse rank-3 structure constant tensor $c_{ijk}$ over the 7 imaginary units
  of the Fano plane. Jordan matrix multiplication uses native sparse `dot(A, B)`.
- **🔬 Popper (Falsifiability & Numerical Invariants)**:
  Provides executable property-based verification of non-trivial axioms: the Jordan identity, Artin's di-associativity,
  and the Poisson-Leibniz derivation rule.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  Demystifies non-associativity: *"Associativity says $(a \cdot b) \cdot c = a \cdot (b \cdot c)$. Jordan and octonions
  say: you can't drop parentheses arbitrarily, but if you repeat the same
  element ($x \cdot (x \cdot y) = (x \cdot x) \cdot y$), the order still doesn't matter!"*

---

## Specification

### 1. Flat Non-Associative Algebra Protocols (`src/algebrax/algebra/_non_assoc.py`)

In strict compliance with [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md) (**Law of Flat Protocol Composition**), `JordanAlgebra`, `AlternativeAlgebra`, `MalcevAlgebra`, and `PoissonAlgebra` inherit **only** from Layer 1 atomic mixins in `algebrax.algebra._mixins` and `Protocol` (never from other Layer 2 protocols), with scalar ring `R` placed first:

```python
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable
from algebrax.algebra._mixins import HasAdd, HasBracket, HasMul, HasNeg, HasScale, HasZero
from algebrax.matrix import add, dot, scale
from algebrax.typing import SparseMatrix

R = TypeVar("R")
M = TypeVar("M")


@runtime_checkable
class JordanAlgebra(HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], HasScale[R, M], Protocol):
    r"""A commutative non-associative algebra satisfying the Jordan identity:
    $$(x \circ y) \circ x^2 = x \circ (y \circ x^2)$$
    where `mul(x, y)` denotes the symmetric Jordan product $x \circ y = y \circ x$.
    """

    def sub(self, a: M, b: M) -> M:
        return self.add(a, self.neg(b))


class SymmetricMatrixJordanAlgebra(JordanAlgebra[float, SparseMatrix[Any, float]]):
    r"""Jordan algebra of sparse symmetric/Hermitian matrices under anticommutator product:
    $$A \circ B = \frac{1}{2}(AB + BA)$$
    """

    def __init__(self, base_semiring: Any) -> None:
        self.base_semiring = base_semiring

    @property
    def zero(self) -> SparseMatrix[Any, float]:
        return {}

    def add(self, a: SparseMatrix[Any, float], b: SparseMatrix[Any, float]) -> SparseMatrix[Any, float]:
        return add(a, b, semiring=self.base_semiring)

    def neg(self, a: SparseMatrix[Any, float]) -> SparseMatrix[Any, float]:
        return scale(a, -1.0, semiring=self.base_semiring)

    def smul(self, r: float, m: SparseMatrix[Any, float]) -> SparseMatrix[Any, float]:
        return scale(m, r, semiring=self.base_semiring)

    def mul(
        self,
        a: SparseMatrix[Any, float],
        b: SparseMatrix[Any, float],
    ) -> SparseMatrix[Any, float]:
        ab = dot(a, b, semiring=self.base_semiring)
        ba = dot(b, a, semiring=self.base_semiring)
        return scale(add(ab, ba, semiring=self.base_semiring), 0.5, semiring=self.base_semiring)
```

### 2. Alternative Algebras, Malcev Algebras & The Octonions (`src/algebrax/algebra/_non_assoc.py`)

An alternative algebra satisfies the left and right alternative laws:
$$x (xy) = (xx)y \quad \text{and} \quad (yx)x = y (xx)$$

```python
@runtime_checkable
class AlternativeAlgebra(HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], HasScale[R, M], Protocol):
    r"""A non-associative algebra whose associator $[x, y, z] = (xy)z - x(yz)$ is alternating."""

    def sub(self, a: M, b: M) -> M:
        return self.add(a, self.neg(b))


@runtime_checkable
class MalcevAlgebra(HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], HasScale[R, M], Protocol):
    r"""A non-associative anticommutative algebra satisfying the Malcev identity."""

    def sub(self, a: M, b: M) -> M:
        return self.add(a, self.neg(b))


class OctonionAlgebra(AlternativeAlgebra[float, dict[int, float]]):
    r"""The 8-dimensional real alternative normed division algebra $\mathbb{O}$.

    Basis: $(1, e_1, e_2, e_3, e_4, e_5, e_6, e_7)$ multiplication governed
    by the 7 oriented lines of the Fano plane. Nominally subclasses `AlternativeAlgebra`.
    """

    FANO_LINES = (
        (1, 2, 3), (1, 4, 5), (1, 7, 6),
        (2, 4, 6), (2, 5, 7),
        (3, 4, 7), (3, 6, 5),
    )

    @property
    def zero(self) -> dict[int, float]:
        return {}

    @property
    def one(self) -> dict[int, float]:
        return {0: 1.0}

    def add(self, a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
        ...

    def neg(self, a: dict[int, float]) -> dict[int, float]:
        return {i: -val for i, val in a.items() if val != 0.0}

    def smul(self, r: float, m: dict[int, float]) -> dict[int, float]:
        return {i: r * val for i, val in m.items() if r * val != 0.0}

    def mul(self, a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
        r"""Compute octonion product $a \cdot b$ using sparse basis combinations."""
        ...

    def conjugate(self, a: dict[int, float]) -> dict[int, float]:
        r"""Octonion conjugation: $\bar{a} = a_0 - \sum_{i=1}^7 a_i e_i$."""
        return {i: (val if i == 0 else -val) for i, val in a.items() if val != 0.0}

    def norm_sq(self, a: dict[int, float]) -> float:
        r"""Norm squared $\|a\|^2 = a \bar{a} = \sum_{i=0}^7 a_i^2$."""
        return sum(v * v for v in a.values())
```

### 3. Flat Poisson Algebra Protocol (`src/algebrax/algebra/_non_assoc.py`)

```python
@runtime_checkable
class PoissonAlgebra(
    HasZero[M], HasAdd[M], HasNeg[M], HasMul[M], HasBracket[M], HasScale[R, M], Protocol
):
    r"""A Poisson algebra $\langle R, P, \cdot_s, \mathbf{0}, +, -, \cdot, \{\cdot, \cdot\} \rangle$.

    - $\langle P, +, \cdot \rangle$ is an associative commutative algebra (`mul`).
    - $\langle P, +, \{\cdot, \cdot\} \rangle$ is a Lie algebra (`bracket`).
    - Satisfies the Leibniz derivation rule:
      $$\{f, g \cdot h\} = \{f, g\} \cdot h + g \cdot \{f, h\}$$
    """

    def sub(self, a: M, b: M) -> M:
        return self.add(a, self.neg(b))
```

### 4. Verification Suite (`src/algebrax/verification.py`)

```python
def verify_jordan_laws(algebra: JordanAlgebra[R, M], samples: list[M]) -> dict[str, bool]:
    """Verify Jordan commutativity and the Jordan identity."""
    mul = algebra.mul
    ...


def verify_poisson_laws(poisson: PoissonAlgebra[R, M], samples: list[M]) -> dict[str, bool]:
    """Verify the Poisson-Leibniz rule: {f, g * h} == {f, g} * h + g * {f, h}."""
    ...
```

---

## Backwards Compatibility

Strictly additive. No existing protocols or functions in `algebrax.algebra` are modified.

---

## How to Teach This / Documentation Plan

1. **User Guide (`docs/guides/quantum-and-non-assoc-algebras.md`)**:
    - Quantum observables and density matrices under Jordan products.
    - The Cayley-Dickson construction and Fano plane octonion multiplication.
    - Symplectic Poisson geometry and Hamiltonian flows.

---

## Reference Implementation

Prototypes of `SymmetricMatrixJordanAlgebra` and `Octonions` were evaluated under Council review in
`references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md`.

---

## Rejected Ideas

1. **Boxing Octonions into `class Octonion`**:
   *Rejected*: Violates Shannon efficiency. Octonions are represented as sparse dictionaries `dict[int, float]` with
   basis indices $0 \le i \le 7$.

---

## Open Questions

1. **Albert Algebra $J_3 (\mathbb{O})$**:
   Should we supply an explicit $3 \times 3$ octonionic Hermitian matrix constructor in `algebrax.algebra`?
   *Recommendation*: Yes, as a standalone constructor demonstrating the exceptional Jordan algebra.

---

## Change Log

- **2026-10-28**: Initial draft authored following Council consensus.
