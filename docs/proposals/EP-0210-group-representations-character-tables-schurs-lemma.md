---
title: "EP-0210: Group Representations, Character Tables & Schur's Lemma"
description: "Formalize finite and compact group representations, character tables, Schur's orthogonality relations, and irreducible representation decomposition over sparse matrix carriers."
icon: lucide/shapes
status: final
---

# EP-0210: Group Representations, Character Tables & Schur's Lemma

| Field             | Value                                                                   |
|:------------------|:------------------------------------------------------------------------|
| **EP**            | 0210                                                                    |
| **Title**         | Group Representations, Character Tables & Schur's Lemma                 |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                             |
| **Sponsor**       | Core Maintainers                                                        |
| **Delegate**      | ⚖️ Noether (Symmetry Actions) & 🧩 Russell (Representation Functors)     |
| **Status**        | Final                                                                   |
| **Type**          | Standards Track                                                         |
| **Created**       | 2026-10-28                                                              |
| **Updated**       | 2026-11-15                                                              |
| **Replaces**      | —                                                                       |
| **Superseded-By** | —                                                                       |

---

## Abstract

This proposal establishes the computational foundations of **Finite Group Theory & Representation Theory** in AlgebraX, promoting `algebrax.group` into a cornerstone package and formalizing the realization of abstract group symmetries as concrete linear transformations over vector spaces in `algebrax.rep`:

1. **Finite Group Cornerstone Package (`algebrax.group`)**:
   Extending the permutation utilities (`compose`, `invert`, `signature`) into a full `algebrax.group` namespace with `FiniteGroup[G]` (satisfying `Group[G]`), `conjugacy_classes`, subgroup closure, centralizers, centers, normalizers, left cosets & coset actions, double cosets, quotient groups $G/N$, and canonical finite groups (`cyclic_group`, `dihedral_group`, `quaternion_group`, `symmetric_group`, `alternating_group`, `direct_product`).
2. **Group Representation Protocol (`algebrax.rep.group`)**:
   $$\rho : G \longrightarrow \mathrm{GL}(V)$$
   refining `algebra.GroupHom[G, SparseMatrix[int, K]]` and mapping group elements $g \in G$ to invertible sparse linear operators satisfying $\rho(gh) = \rho(g)\rho(h)$ and $\rho(e) = \mathbf{I}$.
3. **Character Functions & Character Tables (`algebrax.rep.character`)**:
   Class functions $\chi_\rho(g) = \operatorname{tr}(\rho(g))$ defined over conjugacy classes, and exact compilation of orthonormal **Character Tables**.
4. **Schur's Orthogonality Relations & Maschke's Decomposition**:
   $$\langle \chi_i, \chi_j \rangle = \frac{1}{|G|} \sum_{g \in G} \chi_i(g) \overline{\chi_j(g)} = \delta_{ij}$$
   enabling exact projection operators and irrep multiplicity decomposition $V \cong \bigoplus_i m_i V_i$ where $m_i = \langle \chi_V, \chi_i \rangle$.
5. **Canonical Group Representations**:
   Out-of-the-box exact representations for cyclic groups $C_n$, dihedral groups $D_{2n}$, symmetric groups $S_n$, alternating groups $A_n$, and the quaternion group $Q_8$.
6. **Property-Based Verification (`algebrax.verification`)**:
   Unified verifier functions (`verify_representation_homomorphism`, `verify_schur_orthogonality`, `verify_burnside_dimension_formula`, `verify_schurs_lemma`) in `src/algebrax/verification.py` accepting `FiniteGroup[G]` directly as well as raw element sequences.

All representations adhere strictly to the Shannon zero-bloat principle: representation operators are stateless closures or sparse matrix dictionaries without heavy OOP wrapper overhead.

---

## Motivation

Groups describe symmetries, but in quantum mechanics, crystallography, computer vision, and chemistry, symmetries act on physical states, wavefunctions, molecules, and vector fields. 

1. **Bridging Abstract Algebra to Linear Algebra**: AlgebraX has robust group axioms ([`EP-0190`](EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md)) and high-performance sparse matrix routines, but lacks a formal bridge connecting a group element $g$ to its matrix action $\rho(g) \in \mathrm{GL}(V)$.
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

### 1. Finite Group Cornerstone Package (`src/algebrax/group/`)

- `src/algebrax/group/permutation.py`: Permutation composition, inversion, and sign (`compose`, `invert`, `signature`).
- `src/algebrax/group/finite.py`: `conjugacy_classes`, `FiniteGroup[G]` inheriting `Group[G]` (`HasOne`, `HasMul`, `HasInv`, `LawAssociative`) and `HasContains[G]`, and `FiniteCommGroup[G]` inheriting `FiniteGroup[G]` + `CommGroup[G]` (`LawCommutative`), with automatic abelian promotion across `from_cayley_table`, `subgroup(..., generate=...)`, `centralizer`, `center`, `normalizer`, `quotient`, and `as_commutative`, alongside `cayley_table`, `regular_action_matrix`, `order_of`, `left_cosets`, `left_coset_representatives`, `coset_action`, `double_cosets`, and `double_coset_representatives`.
- `src/algebrax/group/canonical.py`: Constructors (`cyclic_group`, `dihedral_group`, `quaternion_group`, `symmetric_group`, `alternating_group`, `direct_product`) plus pure group element/multiplication/inversion helpers.

### 2. Representation Protocol & Types (`src/algebrax/rep/group.py`)

```python
"""Group representation protocols, constructions, and intertwining operators."""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

from algebrax.algebra._homomorphisms import GroupHom
from algebrax.typing import SparseMatrix

K = TypeVar("K")                   # Field scalar (float or complex)
G = TypeVar("G", bound=Hashable)  # Group element


@runtime_checkable
class GroupRepresentation(GroupHom[G, SparseMatrix[int, K]], Protocol[K, G]):
    """Protocol for a linear representation rho : G -> GL(V) refining GroupHom."""

    @property
    def dimension(self) -> int:
        """Dimension of the representation space V."""
        ...

    def __call__(self, g: G) -> SparseMatrix[int, K]:
        """Evaluate representation operator rho(g) as a sparse matrix."""
        ...


@dataclass(frozen=True)
class ExplicitGroupRep(Generic[K, G]):
    """Explicit group representation backed by precomputed sparse matrices."""

    matrices: Mapping[G, SparseMatrix[int, K]]
    dimension: int

    def __call__(self, g: G) -> SparseMatrix[int, K]:
        return self.matrices[g]
```

### 3. Character Functions & Tables (`src/algebrax/rep/character.py`)

```python
"""Character theory and character tables for finite groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Sequence, TypeVar

from algebrax.group.finite import FiniteGroup, conjugacy_classes

G = TypeVar("G")


@dataclass(frozen=True)
class Character(Generic[G]):
    """A group character chi(g) = Tr(rho(g))."""

    values: dict[Any, complex]  # Maps ConjugacyClass key -> trace value
    degree: int                 # chi(e) = dim(V)

    @classmethod
    def from_group(cls, rep: Any, group: FiniteGroup[G]) -> Character[G]:
        """Build a Character directly over a FiniteGroup and representation."""
        ...

    def __call__(self, c_class: Any) -> complex:
        return self.values.get(c_class, 0.0 + 0.0j)

    def is_irreducible(self, group_order: int, class_sizes: dict[Any, int]) -> bool:
        """Test irreducibility via <chi, chi> == 1."""
        ...


@dataclass(frozen=True)
class CharacterTable:
    """Orthonormal character table of a finite group."""

    classes: Sequence[str]               # Conjugacy class labels
    class_sizes: Sequence[int]           # Sizes of each conjugacy class |C_j|
    irreps: Sequence[str]                # Irrep labels (e.g., A1, A2, E, T1)
    table: list[list[complex]]          # Matrix of character values [irrep_idx][class_idx]
    group_order: int
    tol: float = 1e-9                    # Defensive tolerance for floating-point cyclotomic inner products
```

### 4. Canonical Representations (`src/algebrax/rep/canonical.py`)

Canonical matrix representations delegating pure group laws to `algebrax.group.canonical`:

- `trivial_rep(elements: Sequence[G] | FiniteGroup[G]) -> ExplicitGroupRep[float, G]`
- `regular_rep(group_table: Mapping[tuple[G, G], G] | FiniteGroup[G]) -> ExplicitGroupRep[float, G]`
- `cyclic_rep(n: int, k: int = 1) -> ExplicitGroupRep[complex, int]`
- `dihedral_rep(n: int, k: int = 1) -> ExplicitGroupRep[float, str]`
- `quaternion_rep() -> ExplicitGroupRep[complex, str]`
- `symmetric_sign_rep(n: int)`, `symmetric_defining_rep(n: int)`, `symmetric_standard_rep(n: int)` and verified character tables (`cyclic_character_table`, `dihedral_character_table`, `quaternion_character_table`, `symmetric_s3_character_table`, `symmetric_s4_character_table`, `alternating_a4_character_table`).

### 5. Verification Suite (`src/algebrax/verification.py`)

```python
"""Property-based verification for representation theory laws."""

def verify_representation_homomorphism(
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    mult: Callable[[G, G], G] | None = None,
    identity: G | None = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify rho(g * h) == rho(g) @ rho(h) and rho(e) == I."""
    ...

def verify_schur_orthogonality(table: CharacterTable, tol: float = 1e-9) -> dict[str, bool]:
    """Verify row and column orthogonality of character table."""
    ...

def verify_burnside_dimension_formula(table: CharacterTable) -> dict[str, bool]:
    """Verify sum (dim V_i)^2 == |G|."""
    ...

def verify_schurs_lemma(
    rep1: GroupRepresentation[Any, G],
    rep2: GroupRepresentation[Any, G],
    intertwiner: SparseMatrix[int, Any],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    expect_isomorphic: bool = False,
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify equivariance and Schur's Lemma scalar/invertibility dichotomy."""
    ...
```

---

## Backwards Compatibility

Strictly additive. Promoting legacy `src/algebrax/group.py` to the `src/algebrax/group/` package preserves `compose`, `invert`, `signature` exports alongside `FiniteGroup` and canonical group constructors, while `algebrax.rep` re-exports compatible group helpers (`conjugacy_classes`, `dihedral_mul`, etc.) and accepts both `FiniteGroup[G]` instances and raw element sequences/tables. Existing group protocols in `algebrax.algebra` remain unchanged (`FiniteGroup` satisfies `Group[G]`).

---

## How to Teach This / Documentation Plan

- **Guides**: `docs/guide/algebra/groups_and_symmetries.md` (`FiniteGroup`, canonical finite groups, subgroups, cosets, quotients) and `docs/guide/algebra/representations.md`:
  - Definition of group representations (`GroupHom`) and matrix actions.
  - Generating character tables for $S_3, S_4, Q_8$.
  - Decomposing vibration modes and quantum states using Maschke isotypic projectors.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX formulas for Schur's relations and coset decompositions.

---

## Reference Implementation

Implemented across `src/algebrax/group/` (`permutation.py`, `finite.py`, `canonical.py`, `__init__.py`) and `src/algebrax/rep/` (`group.py`, `character.py`, `canonical.py`, `__init__.py`), verified in `src/algebrax/verification.py` (`verify_representation_homomorphism`, `verify_schur_orthogonality`, `verify_burnside_dimension_formula`, `verify_schurs_lemma`), `tests/algebrax/test_group.py`, and `tests/algebrax/test_rep.py`, and documented in `docs/guide/algebra/groups_and_symmetries.md` and `docs/guide/algebra/representations.md`.

---

## Rejected Ideas

1. **Heavy OOP `Representation` Class with Embedded Groups**:
   - *Rejected*: Requiring a group representation to bundle its full multiplication table inside a monolithic representation class couples two distinct concerns. Keeping pure group laws in `algebrax.group.FiniteGroup` and morphisms in `algebrax.rep` preserves clean separation while allowing direct `FiniteGroup` interoperability.
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
* **2026-11-15:**
  * Implemented `algebrax.rep` (`group.py`, `character.py`, `canonical.py`), Maschke isotypic projectors, Reynolds intertwiners, canonical representations & character tables ($C_n, D_{2n}, Q_8, S_n, A_n$), verification suite in `src/algebrax/verification.py`, user guide `docs/guide/algebra/representations.md`, and unit/falsification tests in `tests/algebrax/test_rep.py`; promoted status to `Final`.
  * Expanded EP-0210 cornerstone scope to promote `algebrax.group/` (`FiniteGroup[G]`, canonical finite groups, conjugacy classes, subgroups, normalizers, cosets, coset actions, double cosets, quotients), refined `GroupRepresentation` via `algebra.GroupHom`, deduplicated pure group logic between `algebrax.group` and `algebrax.rep`, and upgraded `algebrax.rep` & `src/algebrax/verification.py` to accept `FiniteGroup[G]` directly.
