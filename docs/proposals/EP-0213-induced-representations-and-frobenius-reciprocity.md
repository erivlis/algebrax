---
title: "EP-0213: Induced Representations, Mackey Theory & Frobenius Reciprocity"
description: "Formalize induced representations, subgroup restriction, Frobenius reciprocity adjunction, and Mackey's double coset decomposition over sparse block matrix carriers."
icon: lucide/arrow-up-right
status: final
---

# EP-0213: Induced Representations, Mackey Theory & Frobenius Reciprocity

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0213                                                                              |
| **Title**         | Induced Representations, Mackey Theory & Frobenius Reciprocity                    |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | 🧩 Russell (Categorical Adjunction) & ⚖️ Noether (Subgroup Invariants)             |
| **Status**        | Final                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-11-21                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational machinery of **Subgroup Representation Functors** in AlgebraX, formalizing the transfer of symmetry data between a group $G$ and its subgroup $H \le G$ atop [`algebrax.group`](EP-0210-group-representations-character-tables-schurs-lemma.md) (`FiniteGroup`) and [`algebrax.rep`](EP-0210-group-representations-character-tables-schurs-lemma.md). EP-0213 introduces inside `src/algebrax/rep/induction.py`:

1. **Subgroup Restriction Functor (`restrict_representation`, `restrict_character`)**:
   $$\operatorname{Res}_H^G : \mathbf{Rep}(G) \longrightarrow \mathbf{Rep}(H)$$
   restricting the domain of a representation $\rho : G \to \mathrm{GL}(V)$ or character $\chi_V$ to elements $h \in H$ (accepting a subgroup `FiniteGroup[G]` or iterable).
2. **Induced Representation Functor (`induced_representation`)**:
   $$\operatorname{Ind}_H^G : \mathbf{Rep}(H) \longrightarrow \mathbf{Rep}(G)$$
   constructing a representation of dimension $[G : H] \dim W$ from a subgroup representation $W$, organized as a sparse block permutation matrix over left cosets $G = \bigsqcup_{i=0}^{m-1} g_i H$ computed directly via `FiniteGroup.coset_action(subgroup)`.
3. **Induced Character Formula (`induced_character`, `character_inner_product`)**:
   $$\chi_{\operatorname{Ind}_H^G(W)}(g) = \frac{1}{|H|} \sum_{x \in G, \, x^{-1} g x \in H} \chi_W(x^{-1} g x)$$
   enabling rapid character calculation without explicitly forming large block matrices.
4. **Frobenius Reciprocity & Adjunction (`frobenius_adjoint_transpose`, `frobenius_adjoint_inverse`)**:
   $$\operatorname{Hom}_G(\operatorname{Ind}_H^G(W), V) \cong \operatorname{Hom}_H(W, \operatorname{Res}_H^G(V))$$
   realized computationally via explicit bidirectional intertwiner isomorphism maps $\widetilde{T}(g_j \otimes w) = \rho_V(g_j) T(w)$ and the character inner product identity:
   $$\langle \chi_{\operatorname{Ind}_H^G(W)}, \chi_V \rangle_G = \langle \chi_W, \chi_{\operatorname{Res}_H^G(V)} \rangle_H$$
5. **Mackey’s Double Coset Decomposition (`conjugate_representation`, `mackey_decomposition`, `mackey_intertwining_number`)**:
   Decomposing restricted induced representations across double cosets `FiniteGroup.double_cosets(K, H)` ($K \backslash G / H$):
   $$\operatorname{Res}_K^G \operatorname{Ind}_H^G(W) \cong \bigoplus_{s \in K \backslash G / H} \operatorname{Ind}_{K \cap s H s^{-1}}^K \left( {}^s \operatorname{Res}_{s^{-1} K s \cap H}^H W \right)$$
6. **Property-Based Verification (`src/algebrax/verification.py`)**:
   Automated verification of Frobenius reciprocity (`verify_frobenius_reciprocity`), transitivity of induction $\operatorname{Ind}_H^G \operatorname{Ind}_K^H \cong \operatorname{Ind}_K^G$ (`verify_transitivity_of_induction`), and Mackey intertwining numbers (`verify_mackey_intertwining`) returning `dict[str, bool]`.

---

## Motivation

In group representation theory, constructing representations of a large group $G$ directly is often intractable. The standard method is to start with simple 1D representations of an abelian subgroup $H$ and **induce** them up to $G$.

1. **Constructing Irreps Systematically**: For semi-direct products $G = N \rtimes H$ (such as Euclidean motion groups $SE(2), SE(3)$, and Poincaré groups in physics), the Wigner-Mackey "little group" method constructs all irreps via induction from normal subgroups.
2. **Categorical Adjunction in Action**: Frobenius reciprocity is one of the most famous and practical adjunctions in mathematics ($\operatorname{Ind} \dashv \operatorname{Res}$). Implementing it in AlgebraX links representation theory with categorical abstractions ([`EP-0200`](EP-0200-categorical-abstractions-and-enriched-matrices.md)) and subgroup/coset primitives in [`algebrax.group`](EP-0210-group-representations-character-tables-schurs-lemma.md).
3. **Sparse Block Permutation Mechanics**: An induced representation matrix is inherently sparse: it consists of $[G : H] \times [G : H]$ blocks where each block row/column has exactly one non-zero block corresponding to coset transitions $g \cdot (g_j H) = g_i H$. AlgebraX's sparse matrix carrier makes this representation maximally compact.

---

## Rationale & Council Alignment

- **🧩 Russell (Categorical Adjunction & Functoriality)**:
  Frobenius reciprocity is the canonical adjunction $\operatorname{Ind}_H^G \dashv \operatorname{Res}_H^G$. Russell insists that induction and restriction be exposed as functorial maps between representation categories, with an explicit round-trip intertwiner isomorphism (`frobenius_adjoint_transpose` and `frobenius_adjoint_inverse`).
- **⚖️ Noether (Coset Invariance & Subgroup Symmetry)**:
  Induction formalizes wavefunctions defined on homogeneous spaces $G / H$. Subgroup invariants mirror conserved quantities under broken symmetries.
- **⚡ Shannon (Zero Bloat & Sparse Block Carrier)**:
  The induced matrix for $g \in G$ is a sparse block matrix of size $(m \cdot d) \times (m \cdot d)$ with only $m$ non-zero $d \times d$ blocks (where $m = [G:H]$). Consolidating restriction, induction, Frobenius adjunction, and Mackey theory into a single cohesive module `src/algebrax/rep/induction.py` backed by `FiniteGroup.left_cosets`, `FiniteGroup.coset_action`, and `FiniteGroup.double_cosets` eliminates boilerplate coset re-derivation.
- **🔬 Popper (Falsifiable via Character Equality)**:
  Frobenius reciprocity provides an exact integer check: $\langle \chi_{\operatorname{Ind}}, \chi_V \rangle_G == \langle \chi_W, \chi_{\operatorname{Res}} \rangle_H$. If this fails by $\ge 10^{-9}$, or if conjugation invariance is broken, the verifier definitively falsifies the input.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"If you know how a subgroup acts on a small room, and you know how the big group shuffles the rooms in a building, induction tells you how the big group acts on the whole building!"*

---

## Specification

### 1. Restriction, Induction, Adjunction & Mackey Theory (`src/algebrax/rep/induction.py`)

```python
"""Induced and restricted representations, Frobenius adjunction, and Mackey theory."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from typing import Any, TypeVar

from algebrax.group.finite import FiniteGroup
from algebrax.rep.character import Character
from algebrax.rep.group import ExplicitGroupRep, GroupRepresentation
from algebrax.typing import SparseMatrix

K = TypeVar("K")
G = TypeVar("G", bound=Hashable)


def character_inner_product(
    char_a: Character[G] | Mapping[Any, complex],
    char_b: Character[G] | Mapping[Any, complex],
    group: FiniteGroup[G],
) -> complex: ...


def restrict_representation(
    rep: GroupRepresentation[K, G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> ExplicitGroupRep[K, G]: ...


def restrict_character(
    char_g: Character[G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> Character[G]: ...


def induced_representation(
    sub_rep: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> ExplicitGroupRep[K, G]: ...


def induced_character(
    char_h: Character[G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> Character[G]: ...


def frobenius_adjoint_transpose(
    hom_h_w_res_v: SparseMatrix[int, K],
    rep_v: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
    dim_w: int | None = None,
) -> SparseMatrix[int, K]: ...


def frobenius_adjoint_inverse(
    hom_g_ind_w_v: SparseMatrix[int, K],
    dim_w: int,
) -> SparseMatrix[int, K]: ...


def conjugate_representation(
    sub_rep: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    conjugator: G,
    target_subgroup: FiniteGroup[G] | Iterable[G],
) -> ExplicitGroupRep[K, G]: ...


def mackey_decomposition(
    sub_rep: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    subgroup_h: FiniteGroup[G] | Iterable[G],
    subgroup_k: FiniteGroup[G] | Iterable[G],
) -> list[tuple[G, ExplicitGroupRep[K, G]]]: ...


def mackey_intertwining_number(
    char_h: Character[G],
    char_k: Character[G],
    group: FiniteGroup[G],
    subgroup_h: FiniteGroup[G] | Iterable[G],
    subgroup_k: FiniteGroup[G] | Iterable[G],
    tol: float = 1e-9,
) -> int: ...
```

### 2. Verification Suite (`src/algebrax/verification.py`)

```python
"""Property-based verification for Frobenius reciprocity, transitivity, and Mackey theory."""

def verify_frobenius_reciprocity(
    char_w: Any,
    char_v: Any,
    group: Any,
    subgroup: Any,
    tol: float = 1e-9,
) -> dict[str, bool]: ...


def verify_transitivity_of_induction(
    char_k: Any,
    group_g: Any,
    subgroup_h: Any,
    subgroup_k: Any,
    tol: float = 1e-9,
) -> dict[str, bool]: ...


def verify_mackey_intertwining(
    char_h: Any,
    char_k: Any,
    group: Any,
    subgroup_h: Any,
    subgroup_k: Any,
    tol: float = 1e-9,
) -> dict[str, bool]: ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. All components live in `algebrax.rep` (`src/algebrax/rep/induction.py`) and `src/algebrax/verification.py`, building cleanly upon `algebrax.group.FiniteGroup` and `algebrax.rep`.

---

## How to Teach This / Documentation Plan

- **Guide**: `docs/guide/algebra/induced_representations.md` (registered in `zensical.toml`):
  - Inducing the 1D faithful complex representation $\omega$ of $C_3 \le S_3$ to obtain the 2D standard representation $E$.
  - Verifying Frobenius reciprocity numerically and via explicit intertwiner adjunction (`frobenius_adjoint_transpose` / `frobenius_adjoint_inverse`).
  - The geometry of double coset spaces (`FiniteGroup.double_cosets`) and Mackey decomposition on non-normal subgroups of $S_4$.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for Frobenius reciprocity and the Mackey formula.

---

## Reference Implementation

- Core module: `src/algebrax/rep/induction.py` (re-exported in `src/algebrax/rep/__init__.py`)
- Verification predicates: `src/algebrax/verification.py` (`verify_frobenius_reciprocity`, `verify_transitivity_of_induction`, `verify_mackey_intertwining`)
- Test suites: `tests/algebrax/test_rep_induction.py` and `tests/verifications/test_metamorphic_invariants.py`
- Guide: `docs/guide/algebra/induced_representations.md`

---

## Rejected Ideas

1. **Allocating Full Dense Matrices for Coset Shuffling**:
   - *Rejected*: For $[G : H] = 100$ and $\dim W = 5$, a dense matrix is $500 \times 500$, where only $5 \times 500$ entries are non-zero ($99\%$ sparse). Storing this densely violates the zero-bloat principle. Sparse block representations are strictly required.
2. **Ignoring Mackey's Double Cosets**:
   - *Rejected*: Computing intertwining spaces without Mackey decomposition requires huge Kronecker products; `FiniteGroup.double_cosets` indexing reduces calculation complexity drastically.
3. **Omitting `rep_v` in `frobenius_adjoint_transpose`**:
   - *Rejected*: Constructing the natural isomorphism $\widetilde{T}(g_j \otimes w) = \rho_V(g_j) T(w)$ mathematically requires evaluating $\rho_V$ on coset representatives $g_j$; requiring `rep_v` (with optional `dim_w` and paired `frobenius_adjoint_inverse`) guarantees an exact, verified $G$-equivariant bijection.

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
* **2026-11-21:**
  * Implemented `src/algebrax/rep/induction.py` (re-exported in `algebrax.rep`), verification predicates (`verify_frobenius_reciprocity`, `verify_transitivity_of_induction`, `verify_mackey_intertwining`), unit/falsification/metamorphic tests, and user guide `docs/guide/algebra/induced_representations.md`. Refined `frobenius_adjoint_transpose` to require `rep_v` (with inverse `frobenius_adjoint_inverse`) and corrected Mackey double-coset orbit indexing to $K \backslash G / H$. Transitioned status to `Final`.
