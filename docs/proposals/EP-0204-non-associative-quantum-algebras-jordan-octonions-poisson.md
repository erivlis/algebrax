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

1. **Jordan Algebras (`JordanAlgebra[V, K]`)**: Commutative non-associative algebras satisfying the Jordan
   identity $(x \circ y) \circ x^2 = x \circ (y \circ x^2)$, formalizing quantum mechanical observables and the
   anticommutator product $A \circ B = \frac{1}{2} (AB + BA)$ on sparse Hermitian and symmetric matrices.
2. **Alternative Algebras (`AlternativeAlgebra[V, K]`)**: Non-associative algebras with alternating associators
   ($x (xy) = (xx)y$ and $(yx)x = y (xx)$), satisfying Artin's di-associativity theorem.
3. **The Octonions ($\mathbb{O}$)**: The 8-dimensional non-associative normed division algebra over $\mathbb{R}$,
   constructed via Cayley–Dickson doubling with sparse Fano-plane structure constants.
4. **Malcev Algebras (`MalcevAlgebra[V, K]`)**: The generalization of Lie algebras to alternative algebras, instantiated
   on the 7-dimensional imaginary octonions $\operatorname{Im} (\mathbb{O})$.
5. **Poisson Algebras (`PoissonAlgebra[V, K]`)**: Unifying commutative associative algebra with Lie brackets under the
   Leibniz derivation rule $\{f, g \cdot h\} = \{f, g\} \cdot h + g \cdot \{f, h\}$, formalizing classical Hamiltonian
   phase space dynamics.
6. **Property-Based Verification**: Rigorous axiom testing in `algebrax.verification`: `verify_jordan_laws`,
   `verify_alternative_laws`, and `verify_poisson_laws`.

All abstractions strictly preserve AlgebraX's canonical carrier constraint: unboxed raw values and sparse dictionaries,
introducing zero heap wrapping overhead.

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
  Cleanly situates all non-associative algebras under `NonAssocAlgebra[R, M]`, distinguishing commutative Jordan
  algebras from skew-symmetric Lie/Malcev algebras and alternative octonions.
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

### 1. Jordan Algebra Protocol (`src/algebrax/algebra/jordan.py`)

```python
from typing import Generic, Protocol, TypeVar, runtime_checkable
from algebrax.algebra._module import NonAssocAlgebra

R = TypeVar("R")
M = TypeVar("M")


@runtime_checkable
class JordanAlgebra(NonAssocAlgebra[R, M], Protocol[R, M]):
    r"""A commutative non-associative algebra satisfying the Jordan identity:
    $$(x \circ y) \circ x^2 = x \circ (y \circ x^2)$$
    """

    def jordan_mul(self, a: M, b: M) -> M:
        r"""Symmetric Jordan product $a \circ b = b \circ a$."""
        ...


class SymmetricMatrixJordanAlgebra:
    r"""Jordan algebra of sparse symmetric/Hermitian matrices under anticommutator product:
    $$A \circ B = \frac{1}{2}(AB + BA)$$
    """

    def __init__(self, base_ring: Any) -> None:
        self.base_ring = base_ring

    def jordan_mul(
            self,
            a: dict[Any, dict[Any, float]],
            b: dict[Any, dict[Any, float]],
    ) -> dict[Any, dict[Any, float]]:
        from algebrax.linalg.sparse import add, dot, scale
        ab = dot(a, b, self.base_ring)
        ba = dot(b, a, self.base_ring)
        return scale(add(ab, ba, self.base_ring), 0.5)
```

### 2. Alternative Algebras & The Octonions (`src/algebrax/algebra/octonions.py`)

An alternative algebra satisfies the left and right alternative laws:
$$x (xy) = (xx)y \quad \text{and} \quad (yx)x = y (xx)$$

```python
@runtime_checkable
class AlternativeAlgebra(NonAssocAlgebra[R, M], Protocol[R, M]):
    r"""A non-associative algebra whose associator $[x, y, z] = (xy)z - x(yz)$ is alternating."""
    ...


class Octonions:
    r"""The 8-dimensional real alternative division algebra $\mathbb{O}$.

    Basis: $(1, e_1, e_2, e_3, e_4, e_5, e_6, e_7)$ multiplication governed
    by the 7 oriented lines of the Fano plane.
    """

    FANO_LINES = [
        (1, 2, 3), (1, 4, 5), (1, 7, 6),
        (2, 4, 6), (2, 5, 7),
        (3, 4, 7), (3, 6, 5),
    ]

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

### 3. Poisson Algebra Protocol (`src/algebrax/algebra/poisson.py`)

```python
@runtime_checkable
class PoissonAlgebra(Protocol[R, M]):
    r"""A Poisson algebra $\langle P, +, \cdot, \{\cdot, \cdot\} \rangle$.

    - $\langle P, +, \cdot \rangle$ is an associative commutative algebra.
    - $\langle P, +, \{\cdot, \cdot\} \rangle$ is a Lie algebra.
    - Satisfies the Leibniz derivation rule:
      $$\{f, g \cdot h\} = \{f, g\} \cdot h + g \cdot \{f, h\}$$
    """

    def mul(self, a: M, b: M) -> M:
        """Associative commutative product."""
        ...

    def bracket(self, a: M, b: M) -> M:
        """Lie/Poisson bracket satisfying Jacobi identity."""
        ...
```

### 4. Verification Suite (`src/algebrax/verification/non_assoc.py`)

```python
def verify_jordan_laws(algebra: JordanAlgebra[R, M], samples: list[M]) -> None:
    """Verify Jordan commutativity and the Jordan identity."""
    mul = algebra.jordan_mul
    for a in samples:
        a2 = mul(a, a)
        for b in samples:
            assert mul(a, b) == mul(b, a)
            # (a ∘ b) ∘ a² == a ∘ (b ∘ a²)
            lhs = mul(mul(a, b), a2)
            rhs = mul(a, mul(b, a2))
            assert lhs == rhs


def verify_poisson_leibniz_rule(poisson: PoissonAlgebra[R, M], samples: list[M]) -> None:
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
