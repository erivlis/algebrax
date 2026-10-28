---
title: "EP-0210: Group Representations, Character Tables & Schur's Lemma"
description: "Formalize finite and compact group representations, character tables, Schur's orthogonality relations, and irreducible representation decomposition over sparse matrix carriers."
icon: lucide/shapes
status: draft
---

# EP-0210: Group Representations, Character Tables & Schur's Lemma

| Field             | Value                                                                   |
|:------------------|:------------------------------------------------------------------------|
| **EP**            | 0210                                                                    |
| **Title**         | Group Representations, Character Tables & Schur's Lemma                 |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                             |
| **Sponsor**       | Core Maintainers                                                        |
| **Delegate**      | ⚖️ Noether (Symmetry Actions) & 🧩 Russell (Representation Functors)     |
| **Status**        | Draft                                                                   |
| **Type**          | Standards Track                                                         |
| **Created**       | 2026-10-28                                                              |
| **Updated**       | 2026-10-28                                                              |
| **Replaces**      | —                                                                       |
| **Superseded-By** | —                                                                       |

---

## Abstract

This proposal establishes the computational foundations of **Group Representation Theory** in AlgebraX, formalizing the realization of abstract group symmetries as concrete linear transformations over vector spaces. EP-0210 introduces:

1. **Group Representation Protocol (`algebrax.rep.group`)**:
   $$\rho : G \longrightarrow \mathrm{GL}(V)$$
   mapping group elements $g \in G$ to invertible sparse linear operators satisfying $\rho(gh) = \rho(g)\rho(h)$ and $\rho(e) = \mathbf{I}$.
2. **Character Functions & Character Tables (`algebrax.rep.character`)**:
   Class functions $\chi_\rho(g) = \operatorname{tr}(\rho(g))$ defined over conjugacy classes, and exact compilation of orthonormal **Character Tables**.
3. **Schur's Orthogonality Relations & Maschke's Decomposition**:
   $$\langle \chi_i, \chi_j \rangle = \frac{1}{|G|} \sum_{g \in G} \chi_i(g) \overline{\chi_j(g)} = \delta_{ij}$$
   enabling exact projection operators and irrep multiplicity decomposition $V \cong \bigoplus_i m_i V_i$ where $m_i = \langle \chi_V, \chi_i \rangle$.
4. **Canonical Group Representations**:
   Out-of-the-box exact representations for cyclic groups $C_n$, dihedral groups $D_{2n}$, symmetric groups $S_n$, alternating groups $A_n$, and the quaternion group $Q_8$.
5. **Property-Based Verification (`algebrax.verification.rep`)**:
   Executable tests verifying character orthonormality, dimension sum $\sum d_i^2 = |G|$, class function invariance $\chi(h g h^{-1}) = \chi(g)$, and Schur's Lemma intertwining operators.

All representations adhere strictly to the Shannon zero-bloat principle: representation operators are stateless closures or sparse matrix dictionaries without heavy OOP wrapper overhead.

---

## Motivation

Groups describe symmetries, but in quantum mechanics, crystallography, computer vision, and chemistry, symmetries act on physical states, wavefunctions, molecules, and vector fields. 

1. **Bridging Abstract Algebra to Linear Algebra**: AlgebraX has robust group axioms ([`EP-0190`](EP-0190-pure-algebraic-hierarchy.md)) and high-performance sparse matrix routines, but lacks a formal bridge connecting a group element $g$ to its matrix action $\rho(g) \in \mathrm{GL}(V)$.
2. **Harmonic Analysis on Finite Groups**: Fourier analysis on finite groups (such as Diaconis's work on card shuffling or spectral graph theory on Cayley graphs) is fundamentally representation theory. The character table is the discrete Fourier transform matrix for class functions.
3. **Symmetry Reduction in Sparse Solvers**: In PDEs, finite element analysis, and molecular dynamics, exploiting group symmetries decomposes an $N \times N$ matrix into independent $d_i \times d_i$ block diagonal subproblems, reducing computational complexity by orders of magnitude.

---

## Rationale & Council Alignment

- **⚖️ Noether (Symmetry Actions & Conserved Quantum Numbers)**:
  Emmy Noether's philosophy centers on symmetry. A representation is how symmetry manifests in nature: quantum energy levels, angular momentum eigenstates, and irreducible representations are mathematically identical concepts.
- **⚡ Shannon (Zero Bloat & Sparse Dictionary Operators)**:
  A representation is not an object hierarchy of `Morphism` or `Representation` classes. It is represented as:
  ```python
  RepOperator = Callable[[G], SparseMatrix[K]]
  ```
  or a precomputed dictionary `{g: SparseMatrix}`. Characters are flat dictionaries `{conjugacy_class: complex}`.
- **🔬 Popper (Falsifiable Invariants)**:
  Every representation must pass falsifiable property checks:
  - $\rho(g \cdot h) = \rho(g) \circ \rho(h)$ for all $g, h \in G$.
  - $\sum_{i} (\dim V_i)^2 = |G|$.
  - $\sum_{i} \chi_i(C_a) \overline{\chi_i(C_b)} = \frac{|G|}{|C_a|} \delta_{ab}$ (second orthogonality relation).
- **🧩 Russell (Categorical Functoriality)**:
  A group representation is a functor from the one-object delooping category $\mathbf{B}G$ to the category of vector spaces $\mathbf{Vect}_K$, perfectly harmonizing with [`EP-0200`](EP-0200-categorical-abstractions-and-enriched-matrices.md).
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"A group is a list of rules for shuffling things; a representation is the actual hands that do the shuffling on a table of coordinates."*

---

## Specification

### 1. Representation Protocol & Types (`src/algebrax/rep/group.py`)

```python
"""Group representation protocols and constructions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Hashable, Protocol, TypeVar

from algebrax.matrix import SparseMatrix

G = TypeVar("G", bound=Hashable)  # Group element
K = TypeVar("K")                   # Field scalar (float or complex)


class GroupRepresentation(Protocol[G, K]):
    """Protocol for a linear representation of a group G on a vector space K^d."""

    @property
    def dimension(self) -> int:
        """Dimension of the representation space V."""
        ...

    def __call__(self, g: G) -> SparseMatrix[K]:
        """Evaluate representation operator rho(g) as a sparse matrix."""
        ...


@dataclass(frozen=True)
class ExplicitGroupRep(Generic[G, K]):
    """Explicit group representation backed by precomputed sparse matrices."""

    matrices: dict[G, SparseMatrix[K]]
    dimension: int

    def __call__(self, g: G) -> SparseMatrix[K]:
        return self.matrices[g]
```

### 2. Character Functions & Tables (`src/algebrax/rep/character.py`)

```python
"""Character theory and character tables for finite groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Sequence, TypeVar

G = TypeVar("G")


@dataclass(frozen=True)
class Character(Generic[G]):
    """A group character chi(g) = Tr(rho(g))."""

    values: dict[Any, complex]  # Maps ConjugacyClass key -> trace value
    degree: int                 # chi(e) = dim(V)

    def __call__(self, c_class: Any) -> complex:
        return self.values.get(c_class, 0.0 + 0.0j)

    def is_irreducible(self, group_order: int, class_sizes: dict[Any, int]) -> bool:
        """Test irreducibility via <chi, chi> == 1."""
        inner_prod = sum(
            class_sizes[c] * abs(self.values[c]) ** 2
            for c in class_sizes
        ) / group_order
        return abs(inner_prod - 1.0) < 1e-9


@dataclass(frozen=True)
class CharacterTable:
    """Orthonormal character table of a finite group."""

    classes: Sequence[str]               # Conjugacy class labels
    class_sizes: Sequence[int]           # Sizes of each conjugacy class |C_j|
    irreps: Sequence[str]                # Irrep labels (e.g., A1, A2, E, T1)
    table: list[list[complex]]          # Matrix of character values [irrep_idx][class_idx]
    group_order: int

    def inner_product(self, chi_a: Sequence[complex], chi_b: Sequence[complex]) -> complex:
        """Compute weighted inner product (1/|G|) sum_j |C_j| chi_a(C_j) conj(chi_b(C_j))."""
        return sum(
            size * a * b.conjugate()
            for size, a, b in zip(self.class_sizes, chi_a, chi_b)
        ) / self.group_order

    def decompose(self, character: Sequence[complex]) -> dict[str, int]:
        """Decompose an arbitrary reducible character into irrep multiplicities."""
        multiplicities = {}
        for name, chi_irrep in zip(self.irreps, self.table):
            m = round(self.inner_product(character, chi_irrep).real)
            if m > 0:
                multiplicities[name] = m
        return multiplicities
```

### 3. Canonical Representations (`src/algebrax/rep/canonical.py`)

```python
"""Standard representations for symmetric, cyclic, dihedral, and quaternion groups."""

def trivial_rep(elements: Sequence[G]) -> ExplicitGroupRep[G, float]:
    """Trivial 1D representation rho(g) = [1.0]."""
    ...

def regular_rep(group_table: dict[tuple[G, G], G]) -> ExplicitGroupRep[G, float]:
    """Regular representation of dimension |G| acting by permutation matrices."""
    ...

def cyclic_rep(n: int, k: int = 1) -> GroupRepresentation[int, complex]:
    """1D representation of C_n sending generator to exp(2 pi i k / n)."""
    ...

def dihedral_rep(n: int, k: int = 1) -> GroupRepresentation[str, float]:
    """2D standard geometric rotation-reflection representation of D_2n."""
    ...

def quaternion_rep() -> ExplicitGroupRep[str, complex]:
    """2D irreducible complex representation of Q_8 using Pauli spin matrices."""
    ...
```

### 4. Verification Suite (`src/algebrax/verification/rep.py`)

```python
"""Property-based verification for representation theory laws."""

def verify_representation_homomorphism(rep: GroupRepresentation[G, K], elements: Sequence[G], mult: Callable[[G, G], G]) -> bool:
    """Verify rho(g * h) == rho(g) @ rho(h)."""
    ...

def verify_schur_orthogonality(table: CharacterTable) -> bool:
    """Verify row and column orthogonality of character table."""
    ...

def verify_burnside_dimension_formula(table: CharacterTable) -> bool:
    """Verify sum (dim V_i)^2 == |G|."""
    ...
```

---

## Backwards Compatibility

Strictly additive. All new structures reside in `algebrax.rep` and `algebrax.verification.rep`. Existing group structures in `algebrax.algebra` remain unchanged.

---

## How to Teach This / Documentation Plan

- **Guide**: New chapter `guide/algebra/representations.md` covering:
  - Definition of group representations and matrix actions.
  - Generating character tables for $S_3, S_4, Q_8$.
  - Decomposing vibration modes and quantum states using projection operators.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX formulas for Schur's relations.

---

## Reference Implementation

Draft implementation prototypes will be placed in `src/algebrax/rep/` utilizing existing sparse matrix multiplication (`algebrax.matrix.sparse`).

---

## Rejected Ideas

1. **Heavy OOP `Representation` Class with Embedded Groups**:
   - *Rejected*: Requiring a group representation to bundle its full multiplication table, elements, and cayley graph inside a monolithic class violates Shannon's zero-bloat principle. A representation is simply a function $G \to \mathrm{Mat}(K)$ or a sparse dictionary.
2. **Dense NumPy Character Matrices**:
   - *Rejected*: Storing characters exclusively as NumPy arrays prevents exact symbolic representation of algebraic numbers (roots of unity) and breaks sparse matrix polymorphism.

---

## Open Questions

- [ ] Support for compact continuous groups ($U(1), SU(2), SO(3)$) with Haar measure integration in future EPs.
- [ ] Integration with Dixon-Schneider algorithm for automatic character table computation of arbitrary finite groups.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
