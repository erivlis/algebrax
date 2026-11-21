---
title: Induced Representations, Frobenius Reciprocity & Mackey Theory
description: Subgroup restriction, sparse block-permutation induction, Frobenius adjunction intertwiners, and Mackey double-coset decomposition.
---

# Induced Representations, Frobenius Reciprocity & Mackey Theory (`algebrax.rep`)

## 1. The Practical Problem: Lifting Subgroup Symmetries to the Whole Group

Constructing irreducible representations of a large non-abelian group $G$ directly from scratch is hard, whereas constructing 1-dimensional representations of an abelian subgroup $H \le G$ is trivial. **Restriction** and **Induction** form the adjoint bridge between them:

- **Restriction** ($\operatorname{Res}_H^G : \mathbf{Rep}(G) \to \mathbf{Rep}(H)$) forgets symmetries outside $H$, recording how a $G$-representation behaves when restricted to $H$.
- **Induction** ($\operatorname{Ind}_H^G : \mathbf{Rep}(H) \to \mathbf{Rep}(G)$) lifts an $H$-representation $W$ to a $G$-representation of dimension $[G : H] \cdot \dim W$.

> *If you know how a subgroup acts inside a single room ($W$), and you know how the big group shuffles the rooms of a building ($G / H$), induction tells you how the big group acts on the whole building ($\bigoplus_{i} g_i \otimes W$).*

In AlgebraX, `induced_representation` uses `FiniteGroup.coset_action(H)` to assemble $\rho_{\operatorname{Ind}}(g)$ directly as a **sparse block permutation matrix**: each of the $[G : H]$ block columns contains exactly one non-zero $\dim W \times \dim W$ block, avoiding dense $([G : H] \dim W)^2$ allocation completely.

---

## 2. The 30-Second Executable Snippet

Induce the 1D faithful complex character $\omega = e^{2\pi i / 3}$ of $C_3 \le S_3$ to construct the irreducible 2D standard representation $E$ of $S_3$, then verify Frobenius reciprocity and Mackey's irreducibility criterion:

```python
import cmath
import math

from algebrax.group import symmetric_group
from algebrax.rep import (
    Character,
    ExplicitGroupRep,
    induced_character,
    induced_representation,
    mackey_intertwining_number,
    symmetric_standard_rep,
)
from algebrax.verification import (
    verify_frobenius_reciprocity,
    verify_representation_homomorphism,
)

# 1. Define the 1D character omega on C_3 = A_3 <= S_3
s3 = symmetric_group(3)
c3 = s3.subgroup([(1, 2, 0)], generate=True)
omega = cmath.exp(2j * math.pi / 3.0)
w_rep = ExplicitGroupRep(
    matrices={
        (0, 1, 2): {0: {0: 1.0 + 0.0j}},
        (1, 2, 0): {0: {0: omega}},
        (2, 0, 1): {0: {0: omega**2}},
    },
    dimension=1,
)

# 2. Induce W from C_3 to S_3 -> 2D representation isomorphic to Standard (E)
ind_w = induced_representation(w_rep, s3, c3)
assert ind_w.dimension == 2
assert all(verify_representation_homomorphism(ind_w, s3).values())

# 3. Verify character equality, Frobenius reciprocity, and Mackey irreducibility
chi_w = Character.from_group(w_rep, c3)
chi_std = Character.from_group(symmetric_standard_rep(3), s3)
chi_ind = induced_character(chi_w, s3, c3)

assert all(abs(chi_ind(c) - chi_std(c)) < 1e-12 for c in s3.conjugacy_classes())
assert all(verify_frobenius_reciprocity(chi_w, chi_std, s3, c3).values())
assert mackey_intertwining_number(chi_w, chi_w, s3, c3, c3) == 1  # Irreducible!
```

---

## 3. Core API & Mathematical Formulas (`algebrax.rep.induction`)

All functions accept either a concrete `FiniteGroup[G]` or an explicit iterable of subgroup elements (validated against the parent group).

| Symbol | Mathematical Formula | Description |
|:-------|:---------------------|:------------|
| `restrict_representation(rep, H)` | $\operatorname{Res}_H^G(\rho)(h) = \rho(h)$ | Restricts a representation of $G$ to subgroup $H$ |
| `restrict_character(chi, G, H)` | $\chi_{\operatorname{Res}}(h) = \chi(h)$ | Restricts a $G$-character to conjugacy classes of $H$ |
| `induced_representation(sub_rep, G, H)` | $[\rho_{\operatorname{Ind}}(g)]_{i,j} = \rho_W(h)$ where $g g_j = g_i h$ | Sparse block-permutation induced representation of dimension $[G : H] \dim W$ |
| `induced_character(chi_h, G, H)` | $\chi_{\operatorname{Ind}}(g) = \frac{1}{\|H\|} \sum_{x^{-1}gx \in H} \chi_H(x^{-1}gx)$ | Rapid Frobenius character induction without forming block matrices |
| `character_inner_product(chi_a, chi_b, G)` | $\langle \chi_a, \chi_b \rangle_G = \frac{1}{\|G\|}\sum_{g \in G} \chi_a(g)\overline{\chi_b(g)}$ | Exact Schur class-function inner product over `FiniteGroup` |
| `frobenius_adjoint_transpose(T, rep_v, G, H)` | $\widetilde{T}(g_j \otimes w) = \rho_V(g_j) T(w)$ | Natural isomorphism $\operatorname{Hom}_H(W, \operatorname{Res}_H^G V) \xrightarrow{\sim} \operatorname{Hom}_G(\operatorname{Ind}_H^G W, V)$ |
| `frobenius_adjoint_inverse(T_tilde, dim_w)` | $T(w) = \widetilde{T}(e \otimes w)$ | Inverse isomorphism extracting the identity-coset block |
| `conjugate_representation(sub_rep, G, s, K_s)` | $\rho_{{}^s W}(x) = \rho_W(s^{-1} x s)$ | Conjugated subgroup representation on $K_s \le s H s^{-1}$ |
| `mackey_decomposition(sub_rep, G, H, K)` | $\bigoplus_{s \in K \backslash G / H} \operatorname{Ind}_{K \cap sHs^{-1}}^K ({}^s W)$ | Explicit double-coset decomposition of $\operatorname{Res}_K^G \operatorname{Ind}_H^G(W)$ |
| `mackey_intertwining_number(chi_h, chi_k, G, H, K)` | $\sum_{s \in K \backslash G / H} \langle {}^s \chi_H, \chi_K \rangle_{K \cap sHs^{-1}}$ | Exact integer $\dim \operatorname{Hom}_G(\operatorname{Ind}_H^G W, \operatorname{Ind}_K^G V)$ |

---

## 4. Frobenius Reciprocity as an Explicit Adjunction ($\operatorname{Ind}_H^G \dashv \operatorname{Res}_H^G$)

Frobenius reciprocity is not only a character inner-product equality:

$$\langle \chi_{\operatorname{Ind}_H^G(W)}, \chi_V \rangle_G = \langle \chi_W, \chi_{\operatorname{Res}_H^G(V)} \rangle_H$$

It is a **natural isomorphism of intertwiner vector spaces**:

$$\Phi : \operatorname{Hom}_H(W, \operatorname{Res}_H^G V) \xrightarrow{\;\sim\;} \operatorname{Hom}_G(\operatorname{Ind}_H^G W, V)$$

Given any $H$-equivariant matrix $T : W \to V$, `frobenius_adjoint_transpose` lifts $T$ to the $G$-equivariant horizontal block matrix $[\rho_V(g_0) T \mid \rho_V(g_1) T \mid \cdots \mid \rho_V(g_{m-1}) T]$, and `frobenius_adjoint_inverse` recovers $T$ by reading off the identity-coset block $g_0 = e$:

```python
from algebrax.group import symmetric_group
from algebrax.rep import (
    frobenius_adjoint_inverse,
    frobenius_adjoint_transpose,
    induced_representation,
    is_intertwiner,
    restrict_representation,
    reynolds_average,
    symmetric_standard_rep,
    trivial_rep,
)

s4 = symmetric_group(4)
s3_sub = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)  # Stabilizer of 3
w_rep = trivial_rep(s3_sub)       # 1D trivial rep of S_3
v_rep = symmetric_standard_rep(4) # 3D standard rep of S_4

ind_w = induced_representation(w_rep, s4, s3_sub)  # 4D permutation rep on S_4 / S_3
res_v = restrict_representation(v_rep, s3_sub)

# 1. Construct a non-zero S_3-intertwiner T : W -> Res(V) via Reynolds averaging
hom_h = reynolds_average({0: {0: 1.0}, 1: {0: -2.0}, 2: {0: 0.5}}, w_rep, res_v, s3_sub)
assert is_intertwiner(hom_h, w_rep, res_v, s3_sub)

# 2. Lift T to an S_4-intertwiner Ind(W) -> V and verify exact round-trip inverse
hom_g = frobenius_adjoint_transpose(hom_h, v_rep, s4, s3_sub, dim_w=1)
assert is_intertwiner(hom_g, ind_w, v_rep, s4)
assert frobenius_adjoint_inverse(hom_g, dim_w=1).keys() == hom_h.keys()
```

---

## 5. Geometry of Double Cosets & Mackey's Theorem

When you induce a representation from $H \le G$ and then restrict it to a second subgroup $K \le G$, the left action of $K$ on the homogeneous space $G / H$ breaks into disjoint orbits indexed by the **double cosets** $K \backslash G / H$ (`FiniteGroup.double_cosets(K, H)`). On each orbit $K \cdot (sH)$, the stabilizer in $K$ is $K_s = K \cap s H s^{-1}$, yielding **Mackey's Restriction Formula**:

$$\operatorname{Res}_K^G \operatorname{Ind}_H^G(W) \cong \bigoplus_{s \in K \backslash G / H} \operatorname{Ind}_{K \cap s H s^{-1}}^K \left( {}^s \operatorname{Res}_{s^{-1} K s \cap H}^H W \right)$$

```python
from algebrax.group import symmetric_group
from algebrax.rep import (
    Character,
    direct_sum_rep,
    induced_representation,
    mackey_decomposition,
    mackey_intertwining_number,
    restrict_representation,
    trivial_rep,
)
from algebrax.verification import verify_mackey_intertwining, verify_transitivity_of_induction

s4 = symmetric_group(4)
h_sub = s4.subgroup([(1, 0, 2, 3), (1, 2, 0, 3)], generate=True)  # Non-normal S_3 (order 6)
k_sub = s4.subgroup([(1, 2, 3, 0), (0, 3, 2, 1)], generate=True)  # Non-normal D_4 (order 8)
c2_sub = k_sub.subgroup([(2, 3, 0, 1)], generate=True)            # C_2 <= D_4 <= S_4

w_rep = trivial_rep(h_sub)
chi_h = Character.from_group(w_rep, h_sub)
chi_k = Character.from_group(trivial_rep(k_sub), k_sub)

# 1. Explicit Mackey decomposition matches Res_K^G(Ind_H^G(W))
lhs = restrict_representation(induced_representation(w_rep, s4, h_sub), k_sub)
summands = mackey_decomposition(w_rep, s4, h_sub, k_sub)
rhs = direct_sum_rep([rep for _, rep in summands], k_sub)
assert lhs.dimension == rhs.dimension
assert all(abs(complex(lhs.trace(k)) - complex(rhs.trace(k))) < 1e-11 for k in k_sub)

# 2. Mackey intertwining number and transitivity of induction
assert mackey_intertwining_number(chi_h, chi_k, s4, h_sub, k_sub) == 1
assert all(verify_mackey_intertwining(chi_h, chi_k, s4, h_sub, k_sub).values())

chi_c2 = Character(values={(0, 1, 2, 3): 1.0, (2, 3, 0, 1): -1.0}, degree=1)
assert all(verify_transitivity_of_induction(chi_c2, s4, k_sub, c2_sub).values())
```

---

## 6. Automated Verification & Related Guides

`algebrax.verification` exposes falsifiable predicates for subgroup representation laws:

- **`verify_frobenius_reciprocity(char_w, char_v, group, subgroup)`**: Checks $\langle \operatorname{Ind}_H^G W, V \rangle_G = \langle W, \operatorname{Res}_H^G V \rangle_H$, degree scaling $[G : H]\dim W$, and conjugation invariance.
- **`verify_transitivity_of_induction(char_k, group_g, subgroup_h, subgroup_k)`**: Checks $\operatorname{Ind}_H^G(\operatorname{Ind}_K^H W) = \operatorname{Ind}_K^G W$ and index multiplicativity $[G:K] = [G:H][H:K]$.
- **`verify_mackey_intertwining(char_h, char_k, group, subgroup_h, subgroup_k)`**: Checks double-coset intertwining equality, non-negative integrality, and $|G| = \sum |KsH|$.

See also: [Group Representations & Character Tables](representations.md) and [Groups & Symmetries](groups_and_symmetries.md).
