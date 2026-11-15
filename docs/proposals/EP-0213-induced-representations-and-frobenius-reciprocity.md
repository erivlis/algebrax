---
title: "EP-0213: Induced Representations, Mackey Theory & Frobenius Reciprocity"
description: "Formalize induced representations, subgroup restriction, Frobenius reciprocity adjunction, and Mackey's double coset decomposition over sparse block matrix carriers."
icon: lucide/arrow-up-right
status: draft
---

# EP-0213: Induced Representations, Mackey Theory & Frobenius Reciprocity

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0213                                                                              |
| **Title**         | Induced Representations, Mackey Theory & Frobenius Reciprocity                    |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | 🧩 Russell (Categorical Adjunction) & ⚖️ Noether (Subgroup Invariants)             |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-11-15                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational machinery of **Subgroup Representation Functors** in AlgebraX, formalizing the transfer of symmetry data between a group $G$ and its subgroup $H \le G$ atop [`algebrax.group`](EP-0210-group-representations-character-tables-schurs-lemma.md) (`FiniteGroup`) and [`algebrax.rep`](EP-0210-group-representations-character-tables-schurs-lemma.md). EP-0213 introduces inside `src/algebrax/rep/induction.py`:

1. **Subgroup Restriction Functor (`restrict_representation`)**:
   $$\operatorname{Res}_H^G : \mathbf{Rep}(G) \longrightarrow \mathbf{Rep}(H)$$
   restricting the domain of a representation $\rho : G \to \mathrm{GL}(V)$ to elements $h \in H$ (accepting a subgroup `FiniteGroup[G]` or sequence).
2. **Induced Representation Functor (`induced_representation`)**:
   $$\operatorname{Ind}_H^G : \mathbf{Rep}(H) \longrightarrow \mathbf{Rep}(G)$$
   constructing a representation of dimension $[G : H] \dim W$ from a subgroup representation $W$, organized as a sparse block permutation matrix over left cosets $G = \bigsqcup_{i=1}^m g_i H$ computed directly via `FiniteGroup.coset_action(subgroup)`.
3. **Induced Character Formula (`induced_character`)**:
   $$\chi_{\operatorname{Ind}_H^G(W)}(g) = \frac{1}{|H|} \sum_{x \in G, \, x^{-1} g x \in H} \chi_W(x^{-1} g x)$$
   enabling rapid character calculation without explicitly forming large block matrices.
4. **Frobenius Reciprocity & Adjunction (`frobenius_adjoint_transpose`)**:
   $$\operatorname{Hom}_G(\operatorname{Ind}_H^G(W), V) \cong \operatorname{Hom}_H(W, \operatorname{Res}_H^G(V))$$
   realized computationally via both explicit intertwiner maps and the character inner product identity:
   $$\langle \chi_{\operatorname{Ind}_H^G(W)}, \chi_V \rangle_G = \langle \chi_W, \chi_{\operatorname{Res}_H^G(V)} \rangle_H$$
5. **Mackey’s Double Coset Decomposition (`mackey_intertwining_number`, `mackey_decomposition`)**:
   Decomposing restricted induced representations across double cosets `FiniteGroup.double_cosets(H, K)` ($H \backslash G / K$):
   $$\operatorname{Res}_K^G \operatorname{Ind}_H^G(W) \cong \bigoplus_{s \in H \backslash G / K} \operatorname{Ind}_{K \cap s H s^{-1}}^K \left( s \cdot \operatorname{Res}_{s^{-1} K s \cap H}^H W \right)$$
6. **Property-Based Verification (`src/algebrax/verification.py`)**:
   Automated verification of the Frobenius character equality (`verify_frobenius_reciprocity`), transitivity of induction $\operatorname{Ind}_H^G \operatorname{Ind}_K^H \cong \operatorname{Ind}_K^G$ (`verify_transitivity_of_induction`), and Mackey intertwining numbers returning `dict[str, bool]`.

---

## Motivation

In group representation theory, constructing representations of a large group $G$ directly is often intractable. The standard method is to start with simple 1D representations of an abelian subgroup $H$ and **induce** them up to $G$.

1. **Constructing Irreps Systematically**: For semi-direct products $G = N \rtimes H$ (such as Euclidean motion groups $SE(2), SE(3)$, and Poincaré groups in physics), the Wigner-Mackey "little group" method constructs all irreps via induction from normal subgroups.
2. **Categorical Adjunction in Action**: Frobenius reciprocity is one of the most famous and practical adjunctions in mathematics ($\operatorname{Ind} \dashv \operatorname{Res}$). Implementing it in AlgebraX links representation theory with categorical abstractions ([`EP-0200`](EP-0200-categorical-abstractions-and-enriched-matrices.md)) and subgroup/coset primitives in [`algebrax.group`](EP-0210-group-representations-character-tables-schurs-lemma.md).
3. **Sparse Block Permutation Mechanics**: An induced representation matrix is inherently sparse: it consists of $[G : H] \times [G : H]$ blocks where each block row/column has exactly one non-zero block corresponding to coset transitions $g \cdot (g_j H) = g_i H$. AlgebraX's sparse matrix carrier makes this representation maximally compact.

---

## Rationale & Council Alignment

- **🧩 Russell (Categorical Adjunction & Functoriality)**:
  Frobenius reciprocity is the canonical adjunction $\operatorname{Ind}_H^G \dashv \operatorname{Res}_H^G$. Russell insists that induction and restriction be exposed as functorial maps between representation categories.
- **⚖️ Noether (Coset Invariance & Subgroup Symmetry)**:
  Induction formalizes wavefunctions defined on homogeneous spaces $G / H$. Subgroup invariants mirror conserved quantities under broken symmetries.
- **⚡ Shannon (Zero Bloat & Sparse Block Carrier)**:
  The induced matrix for $g \in G$ is a sparse block matrix of size $(m \cdot d) \times (m \cdot d)$ with only $m$ non-zero $d \times d$ blocks (where $m = [G:H]$). Consolidating restriction, induction, Frobenius adjunction, and Mackey theory into a single cohesive module `src/algebrax/rep/induction.py` backed by `FiniteGroup.left_cosets`, `FiniteGroup.coset_action`, and `FiniteGroup.double_cosets` eliminates boilerplate coset re-derivation.
- **🔬 Popper (Falsifiable via Character Equality)**:
  Frobenius reciprocity provides an exact integer check: $\langle \chi_{\operatorname{Ind}}, \chi_V \rangle_G == \langle \chi_W, \chi_{\operatorname{Res}} \rangle_H$. If this fails by $\ge 10^{-12}$, the implementation is definitively falsified.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"If you know how a subgroup acts on a small room, and you know how the big group shuffles the rooms in a building, induction tells you how the big group acts on the whole building!"*

---

## Specification

### 1. Restriction, Induction, Adjunction & Mackey Theory (`src/algebrax/rep/induction.py`)

```python
"""Induced and restricted representations, Frobenius adjunction, and Mackey theory."""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from typing import Any, TypeVar

from algebrax.group.finite import FiniteGroup
from algebrax.rep.character import Character
from algebrax.rep.group import ExplicitGroupRep, GroupRepresentation
from algebrax.typing import SparseMatrix

K = TypeVar("K")
G = TypeVar("G", bound=Hashable)


def restrict_representation(
    rep: GroupRepresentation[K, G],
    subgroup: FiniteGroup[G] | Sequence[G],
) -> ExplicitGroupRep[K, G]:
    """Restrict representation rho of G to subgroup H."""
    ...


def induced_representation(
    sub_rep: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Sequence[G],
) -> ExplicitGroupRep[K, G]:
    """Construct induced representation Ind_H^G(sub_rep) via group.coset_action(subgroup).

    Dimension is [G:H] * dim(sub_rep). Each rho(g) is a sparse block permutation matrix.
    """
    ...


def induced_character(
    char_h: Character[G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Sequence[G],
) -> Character[G]:
    """Compute character of Ind_H^G using Frobenius formula:

    chi_{Ind}(g) = (1 / |H|) sum_{x in G, x^{-1} g x in H} chi_H(x^{-1} g x).
    """
    ...


def frobenius_adjoint_transpose(
    hom_h_w_res_v: SparseMatrix[int, K],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Sequence[G],
) -> SparseMatrix[int, K]:
    """Natural isomorphism Hom_H(W, Res_H^G(V)) -> Hom_G(Ind_H^G(W), V)."""
    ...


def mackey_intertwining_number(
    char_h: Character[G],
    char_k: Character[G],
    group: FiniteGroup[G],
    subgroup_h: FiniteGroup[G] | Sequence[G],
    subgroup_k: FiniteGroup[G] | Sequence[G],
) -> int:
    """Compute dim Hom_G(Ind_H^G(W), Ind_K^G(V)) via group.double_cosets(subgroup_h, subgroup_k)."""
    ...
```

### 2. Verification Suite (`src/algebrax/verification.py`)

```python
"""Property-based verification for Frobenius reciprocity and Mackey theory."""

def verify_frobenius_reciprocity(
    char_w: Character[G],
    char_v: Character[G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Sequence[G],
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify <Ind_H^G(W), V>_G == <W, Res_H^G(V)>_H."""
    ...

def verify_transitivity_of_induction(
    char_k: Character[G],
    group_g: FiniteGroup[G],
    subgroup_h: FiniteGroup[G] | Sequence[G],
    subgroup_k: FiniteGroup[G] | Sequence[G],
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify Ind_H^G(Ind_K^H(W)) == Ind_K^G(W)."""
    ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. All components live in `algebrax.rep` (`src/algebrax/rep/induction.py`) and `src/algebrax/verification.py`, building cleanly upon `algebrax.group.FiniteGroup` and `algebrax.rep`.

---

## How to Teach This / Documentation Plan

- **Guide**: `guide/algebra/induced_representations.md`:
  - Inducing the 1D sign representation of $C_3 \le S_3$ to obtain the 2D standard representation.
  - Verifying Frobenius reciprocity numerically.
  - The geometry of coset spaces (`FiniteGroup.left_cosets`, `FiniteGroup.double_cosets`) and induced vector bundles.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for Frobenius reciprocity and the Mackey formula.

---

## Reference Implementation

Implementations will reside in `src/algebrax/rep/induction.py` (re-exported in `algebrax.rep`) and verified in `src/algebrax/verification.py`.

---

## Rejected Ideas

1. **Allocating Full Dense Matrices for Coset Shuffling**:
   - *Rejected*: For $[G : H] = 100$ and $\dim W = 5$, a dense matrix is $500 \times 500$, where only $5 \times 500$ entries are non-zero ($99\%$ sparse). Storing this densely violates the zero-bloat principle. Sparse block representations are strictly required.
2. **Ignoring Mackey's Double Cosets**:
   - *Rejected*: Computing intertwining spaces without Mackey decomposition requires huge Kronecker products; `FiniteGroup.double_cosets` indexing reduces calculation complexity drastically.

---

## Open Questions

- [ ] Support for continuous compact Lie group induction (Borel–Weil–Bott theorem constructing irreps from holomorphic line bundles over flag manifolds).
- [ ] Integration with Clifford theory for representations of normal subgroups (`FiniteGroup.is_normal`, `FiniteGroup.quotient`).

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
* **2026-11-15:**
  * Aligned specification to consolidate induction, restriction, Frobenius adjunction, and Mackey double-coset formulas into `src/algebrax/rep/induction.py` backed directly by `algebrax.group.FiniteGroup`, with verifiers returning `dict[str, bool]` in `src/algebrax/verification.py`.
