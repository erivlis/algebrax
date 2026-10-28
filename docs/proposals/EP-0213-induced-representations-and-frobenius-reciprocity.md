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
| **Updated**       | 2026-10-28                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational machinery of **Subgroup Representation Functors** in AlgebraX, formalizing the transfer of symmetry data between a group $G$ and its subgroup $H \le G$. EP-0213 introduces:

1. **Subgroup Restriction Functor (`algebrax.rep.restriction`)**:
   $$\operatorname{Res}_H^G : \mathbf{Rep}(G) \longrightarrow \mathbf{Rep}(H)$$
   restricting the domain of a representation $\rho : G \to \mathrm{GL}(V)$ to elements $h \in H$.
2. **Induced Representation Functor (`algebrax.rep.induction`)**:
   $$\operatorname{Ind}_H^G : \mathbf{Rep}(H) \longrightarrow \mathbf{Rep}(G)$$
   constructing a representation of dimension $[G : H] \dim W$ from a subgroup representation $W$, organized as a sparse block permutation matrix over left cosets $G = \bigsqcup_{i=1}^m g_i H$.
3. **Induced Character Formula**:
   $$\chi_{\operatorname{Ind}_H^G(W)}(g) = \frac{1}{|H|} \sum_{x \in G, \, x^{-1} g x \in H} \chi_W(x^{-1} g x)$$
   enabling rapid character calculation without explicitly forming large block matrices.
4. **Frobenius Reciprocity (Categorical Adjunction)**:
   $$\operatorname{Hom}_G(\operatorname{Ind}_H^G(W), V) \cong \operatorname{Hom}_H(W, \operatorname{Res}_H^G(V))$$
   realized computationally via the character inner product identity:
   $$\langle \chi_{\operatorname{Ind}_H^G(W)}, \chi_V \rangle_G = \langle \chi_W, \chi_{\operatorname{Res}_H^G(V)} \rangle_H$$
5. **Mackey’s Double Coset Decomposition (`algebrax.rep.mackey`)**:
   Decomposing restricted induced representations across double cosets $H \backslash G / K$:
   $$\operatorname{Res}_K^G \operatorname{Ind}_H^G(W) \cong \bigoplus_{s \in H \backslash G / K} \operatorname{Ind}_{K \cap s H s^{-1}}^K \left( s \cdot \operatorname{Res}_{s^{-1} K s \cap H}^H W \right)$$
6. **Property-Based Verification (`algebrax.verification.induction`)**:
   Automated verification of the Frobenius character equality, transitivity of induction $\operatorname{Ind}_H^G \operatorname{Ind}_K^H \cong \operatorname{Ind}_K^G$, and Mackey intertwining numbers.

---

## Motivation

In group representation theory, constructing representations of a large group $G$ directly is often intractable. The standard method is to start with simple 1D representations of an abelian subgroup $H$ and **induce** them up to $G$.

1. **Constructing Irreps Systematically**: For semi-direct products $G = N \rtimes H$ (such as Euclidean motion groups $SE(2), SE(3)$, and Poincaré groups in physics), the Wigner-Mackey "little group" method constructs all irreps via induction from normal subgroups.
2. **Categorical Adjunction in Action**: Frobenius reciprocity is one of the most famous and practical adjunctions in mathematics ($\operatorname{Ind} \dashv \operatorname{Res}$). Implementing it in AlgebraX links representation theory with categorical abstractions ([`EP-0200`](EP-0200-categorical-abstractions-and-enriched-matrices.md)).
3. **Sparse Block Permutation Mechanics**: An induced representation matrix is inherently sparse: it consists of $[G : H] \times [G : H]$ blocks where each block row/column has exactly one non-zero block corresponding to coset transitions $g \cdot (g_j H) = g_i H$. AlgebraX's sparse matrix carrier makes this representation maximally compact.

---

## Rationale & Council Alignment

- **🧩 Russell (Categorical Adjunction & Functoriality)**:
  Frobenius reciprocity is the canonical adjunction $\operatorname{Ind}_H^G \dashv \operatorname{Res}_H^G$. Russell insists that induction and restriction be exposed as functorial maps between representation categories.
- **⚖️ Noether (Coset Invariance & Subgroup Symmetry)**:
  Induction formalizes wavefunctions defined on homogeneous spaces $G / H$. Subgroup invariants mirror conserved quantities under broken symmetries.
- **⚡ Shannon (Zero Bloat & Sparse Block Carrier)**:
  The induced matrix for $g \in G$ is a sparse block matrix of size $(m \cdot d) \times (m \cdot d)$ with only $m$ non-zero $d \times d$ blocks (where $m = [G:H]$). Shannon ensures this is stored sparsely as `SparseMatrix` rather than allocating huge zero blocks.
- **🔬 Popper (Falsifiability via Character Equality)**:
  Frobenius reciprocity provides an exact integer check: $\langle \chi_{\operatorname{Ind}}, \chi_V \rangle_G == \langle \chi_W, \chi_{\operatorname{Res}} \rangle_H$. If this fails by $\ge 10^{-12}$, the implementation is definitively falsified.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"If you know how a subgroup acts on a small room, and you know how the big group shuffles the rooms in a building, induction tells you how the big group acts on the whole building!"*

---

## Specification

### 1. Restriction & Induction Operators (`src/algebrax/rep/induction.py`)

```python
"""Induced and restricted representations of finite groups."""

from __future__ import annotations

from typing import Any, Callable, Generic, Hashable, Sequence, TypeVar

from algebrax.matrix import SparseMatrix
from algebrax.rep.character import Character
from algebrax.rep.group import ExplicitGroupRep, GroupRepresentation

G = TypeVar("G", bound=Hashable)
H = TypeVar("H", bound=Hashable)
K = TypeVar("K")


def restrict_representation(
    rep: GroupRepresentation[G, K],
    subgroup_elements: Sequence[H],
) -> GroupRepresentation[H, K]:
    """Restrict representation rho of G to subgroup H."""
    ...


def induced_representation(
    sub_rep: GroupRepresentation[H, K],
    group_elements: Sequence[G],
    subgroup_elements: Sequence[H],
    coset_representatives: Sequence[G],
    coset_action: Callable[[G, G], tuple[int, H]],  # g * g_j = g_i * h
) -> ExplicitGroupRep[G, K]:
    """Construct induced representation Ind_H^G(sub_rep).
    
    Dimension is [G:H] * dim(sub_rep). Each rho(g) is a sparse block permutation matrix.
    """
    ...
```

### 2. Fast Induced Character Formula (`src/algebrax/rep/induced_character.py`)

```python
"""Induced character computation without matrix generation."""

def induced_character(
    char_h: Character[H],
    group_classes: dict[str, Sequence[G]],
    subgroup: Sequence[H],
    group_order: int,
    subgroup_order: int,
) -> Character[G]:
    """Compute character of Ind_H^G using Frobenius formula:
    
    chi_{Ind}(g) = (1 / |H|) sum_{x in G, x^{-1} g x in H} chi_H(x^{-1} g x).
    """
    ...
```

### 3. Frobenius Adjunction Natural Isomorphism (`src/algebrax/rep/adjunction.py`)

```python
"""Frobenius reciprocity as a categorical adjunction Ind_H^G -| Res_H^G."""

def frobenius_adjoint_transpose(
    hom_h_w_res_v: SparseMatrix[K],
    coset_reps: Sequence[G],
    subgroup: Sequence[H],
) -> SparseMatrix[K]:
    """Isomorphism Hom_H(W, Res_H^G(V)) -> Hom_G(Ind_H^G(W), V).
    
    Formalizes the unit and counit of the categorical adjunction from EP-0200.
    """
    ...
```

### 4. Mackey Double Coset Decomposition (`src/algebrax/rep/mackey.py`)

```python
"""Mackey's double coset formula and intertwining numbers."""

def mackey_intertwining_number(
    char_h: Character[H],
    char_k: Character[G],
    double_cosets: Sequence[Sequence[G]],
) -> int:
    """Compute dim Hom_G(Ind_H^G(W), Ind_K^G(V)) via Mackey decomposition."""
    ...
```

### 4. Verification Suite (`src/algebrax/verification/induction.py`)

```python
"""Property-based verification for Frobenius reciprocity and Mackey theory."""

def verify_frobenius_reciprocity(
    char_w: Character[H],
    char_v: Character[G],
    ind_char_w: Character[G],
    res_char_v: Character[H],
    g_order: int,
    h_order: int,
) -> bool:
    """Verify <Ind_H^G(W), V>_G == <W, Res_H^G(V)>_H."""
    ...

def verify_transitivity_of_induction(
    char_k: Character[Any],
    ind_h_k: Character[Any],
    ind_g_k: Character[Any],
) -> bool:
    """Verify Ind_H^G(Ind_K^H(W)) == Ind_K^G(W)."""
    ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. All components live in `algebrax.rep` and build cleanly upon `EP-0210`.

---

## How to Teach This / Documentation Plan

- **Guide**: `guide/algebra/induced_representations.md`:
  - Inducing the 1D sign representation of $C_3 \le S_3$ to obtain the 2D standard representation.
  - Verifying Frobenius reciprocity numerically.
  - The geometry of coset spaces and induced vector bundles.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for Frobenius reciprocity and the Mackey formula.

---

## Reference Implementation

Prototype implementations will reside in `src/algebrax/rep/induction.py` and `src/algebrax/rep/mackey.py`.

---

## Rejected Ideas

1. **Allocating Full Dense Matrices for Coset Shuffling**:
   - *Rejected*: For $[G : H] = 100$ and $\dim W = 5$, a dense matrix is $500 \times 500$, where only $5 \times 500$ entries are non-zero ($99\%$ sparse). Storing this densely violates the zero-bloat principle. Sparse block representations are strictly required.
2. **Ignoring Mackey's Double Cosets**:
   - *Rejected*: Computing intertwining spaces without Mackey decomposition requires huge Kronecker products; double coset indexing reduces calculation complexity drastically.

---

## Open Questions

- [ ] Support for continuous compact Lie group induction (Borel–Weil–Bott theorem constructing irreps from holomorphic line bundles over flag manifolds).
- [ ] Integration with Clifford theory for representations of normal subgroups.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
