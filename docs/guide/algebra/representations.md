---
title: Group Representations & Character Tables
description: Finite group representations over sparse matrices, orthonormal character tables, Maschke isotypic projections, and Schur's Lemma intertwiners.
---

# Group Representations & Character Tables (`algebrax.rep`)

## 1. The Practical Problem: Computing with Symmetries

Abstract groups define symmetry through multiplication tables and permutation rules, whereas physics, chemistry, signal processing, and graph algorithms operate on **vectors, wavefunctions, and matrices**. A **group representation** bridges this gap by mapping every group element $g \in G$ to an invertible linear operator $\rho(g) \in \mathrm{GL}(V)$ preserving group composition:

$$\rho : G \longrightarrow \mathrm{GL}(V), \qquad \rho(g \cdot h) = \rho(g)\,\rho(h), \qquad \rho(e) = \mathbf{I}$$

Once symmetries live on vector spaces as sparse matrices, **Character Theory** and **Schur's Lemma** turn representation analysis into linear algebra:

- **Orthonormal Decomposition (Maschke's Theorem)**: Every finite-group representation over $\mathbb{C}$ splits uniquely into irreducible building blocks $V \cong \bigoplus_i m_i V_i$ with multiplicities $m_i = \langle \chi_V, \chi_i \rangle$.
- **Exact State Projection**: Isotypic projectors $P_{\chi_i} = \frac{d_i}{|G|} \sum_{g \in G} \overline{\chi_i(g)}\,\rho(g)$ isolate invariant subspaces (molecular vibrational modes, symmetry-adapted graph eigenbases) with $P_i^2 = P_i$ and $\sum_i P_i = \mathbf{I}$.
- **Equivariant Map Classification (Schur's Lemma)**: Any linear operator commuting with an irreducible representation collapses to a scalar multiple of the identity, $\lambda \mathbf{I}$, while intertwiners between inequivalent irreps vanish identically.

---

## 2. The 30-Second Executable Snippet

```python
from algebrax.rep import (
    s3_character_table,
    symmetric_defining_rep,
    symmetric_elements,
    symmetric_mul,
)
from algebrax.verification import (
    verify_burnside_dimension_formula,
    verify_representation_homomorphism,
    verify_schur_orthogonality,
)

# 1. Defining 3D permutation representation of S_3 and its character
s3_elems = symmetric_elements(3)
def_s3 = symmetric_defining_rep(3)
assert all(verify_representation_homomorphism(def_s3, s3_elems, symmetric_mul).values())

# 2. Evaluate character on the 3 conjugacy class representatives of S_3
tbl = s3_character_table()
assert all(verify_schur_orthogonality(tbl).values())
assert all(verify_burnside_dimension_formula(tbl).values())

class_reps = [(0, 1, 2), (1, 0, 2), (1, 2, 0)]  # e, (0 1), (0 1 2)
chi_def = [complex(def_s3.trace(g)) for g in class_reps]  # [3, 1, 0]

# 3. Decompose 3D permutation rep -> 1D Trivial (A1) + 2D Standard (E)
assert tbl.decompose(chi_def) == {'Trivial (A1)': 1, 'Standard (E)': 1}
```

---

## 3. Group Representations & Operations (`algebrax.rep.group`)

Representations follow the zero-bloat sparse matrix philosophy: any callable matching the structural `GroupRepresentation[K, G]` protocol (`dimension: int` and `__call__(g) -> SparseMatrix[int, K]`) is accepted everywhere in `algebrax.rep`, with `ExplicitGroupRep` providing precomputed storage and algebraic combinators.

| Symbol | Mathematical Formula | Description |
|:-------|:---------------------|:------------|
| `GroupRepresentation[K, G]` | $\rho : G \to \mathrm{GL}_d(\mathbb{K})$ | Structural `@runtime_checkable` protocol (`dimension`, `__call__`) |
| `ExplicitGroupRep[K, G]` | $g \mapsto M_g \in \mathrm{SparseMatrix}[d \times d]$ | Immutable dataclass storing sparse matrix dictionaries |
| `direct_sum` / `direct_sum_rep` | $(\rho_1 \oplus \rho_2)(g) = \mathrm{diag}(\rho_1(g), \rho_2(g))$ | Block-diagonal direct sum of representations |
| `tensor_product` / `tensor_product_rep` | $(\rho_1 \otimes \rho_2)(g) = \rho_1(g) \otimes \rho_2(g)$ | Kronecker product representation with character $\chi_1 \cdot \chi_2$ |
| `dual(inv_fn=...)` | $\rho^*(g) = \rho(g^{-1})^T$ | Contragredient dual representation via group or sparse matrix inverse |

---

## 4. Character Tables & Canonical Finite Groups

`Character` and `CharacterTable` implement the weighted class-function inner product:

$$\langle \chi_a, \chi_b \rangle = \frac{1}{|G|} \sum_{j} |C_j| \, \chi_a(C_j)\,\overline{\chi_b(C_j)}$$

Built-in exact representations and orthonormal character tables (`algebrax.rep.canonical`) pair cleanly with concrete `FiniteGroup` instances from [`algebrax.group`](groups_and_symmetries.md):

- **Arbitrary Finite Groups**: `trivial_rep(G)`, `regular_rep(G)` (also accepting raw element lists or Cayley tables), and `conjugacy_classes` in `algebrax.group`.
- **Cyclic Groups $C_n$**: `cyclic_rep(n, k)` ($e^{2\pi i k g / n}$) and `cyclic_character_table(n)`.
- **Dihedral Groups $D_{2n}$**: `dihedral_group(n)` in `algebrax.group`, `dihedral_rep(n, k)` (2D geometric rotation-reflection matrices), and `dihedral_character_table(n)` for arbitrary $n \ge 1$.
- **Quaternion Group $Q_8$**: `quaternion_group()` in `algebrax.group`, `quaternion_rep()` (faithful 2D spin representation via Pauli matrices $-i\sigma_1, -i\sigma_2, -i\sigma_3$), and `q8_character_table()`.
- **Symmetric & Alternating Groups ($S_n$, $A_n$)**: `symmetric_group(n)` / `alternating_group(n)` in `algebrax.group`, `symmetric_defining_rep(n)`, `symmetric_sign_rep(n)`, exact integral $(n-1)$-dimensional `symmetric_standard_rep(n)`, `alternating_defining_rep(n)`, `alternating_standard_rep(n)`, plus `s3_character_table()`, `s4_character_table()`, and complex `a4_character_table()`.

---

## 5. Maschke Projectors & Schur's Lemma Intertwiners

Using the regular representation of $S_3$ (dimension $|S_3| = 6$), `isotypic_projector` extracts mutually orthogonal idempotent projectors onto the $A_1$ (dim 1), $A_2$ (dim 1), and $E \oplus E$ (dim $2 \times 2 = 4$) subspaces, while `reynolds_average` projects arbitrary operators onto equivariant intertwiner spaces:

```python
from algebrax.group import quaternion_group, symmetric_group
from algebrax.matrix.core import add, dot, trace
from algebrax.rep import (
    isotypic_projector,
    quaternion_rep,
    regular_rep,
    reynolds_average,
    symmetric_sign_rep,
    symmetric_standard_rep,
)
from algebrax.verification import verify_schurs_lemma

# 1. Partition the 6D regular representation of S_3 via Maschke projectors
s3 = symmetric_group(3)
reg = regular_rep(s3)
sgn = symmetric_sign_rep(3)
std = symmetric_standard_rep(3)

p_a1 = isotypic_projector(reg, s3, {g: 1.0 for g in s3}, irrep_dim=1)
p_a2 = isotypic_projector(reg, s3, {g: complex(sgn.trace(g)) for g in s3}, irrep_dim=1)
p_e = isotypic_projector(reg, s3, {g: complex(std.trace(g)) for g in s3}, irrep_dim=2)

# Traces equal d_i^2 (1 + 1 + 4 = 6) and P_a1 + P_a2 + P_e == I_6
assert round(complex(trace(p_e)).real) == 4
assert dot(p_a2, p_e) == {}
assert trace(add(add(p_a1, p_a2), p_e)) == 6.0

# 2. Schur's Lemma on Q_8: Reynolds averaging an arbitrary matrix collapses to (tr(T)/2) * I_2
q8 = quaternion_group()
rho_q8 = quaternion_rep()
arbitrary = {0: {0: 4.0 + 1.0j, 1: -3.0}, 1: {0: 2.5j, 1: 6.0 - 1.0j}}
intertwiner = reynolds_average(arbitrary, rho_q8, rho_q8, q8)
assert all(verify_schurs_lemma(intertwiner, rho_q8, rho_q8, q8, is_equivalent=True).values())
```

---

## 6. Automated Verification & Falsification

`algebrax.verification` provides falsifiable invariant checks for every representation-theoretic law:

- **`verify_representation_homomorphism(rep, elements, mult)`**: Checks multiplicativity $\rho(gh) = \rho(g)\rho(h)$, identity preservation $\rho(e) = \mathbf{I}$, and class-function conjugation invariance $\chi(hgh^{-1}) = \chi(g)$.
- **`verify_schur_orthogonality(table)`**: Checks both row orthogonality $\langle \chi_i, \chi_j \rangle = \delta_{ij}$ and column orthogonality $\sum_i \chi_i(C_a)\overline{\chi_i(C_b)} = \frac{|G|}{|C_a|}\delta_{ab}$.
- **`verify_burnside_dimension_formula(table)`**: Checks $\sum_i (\dim V_i)^2 = |G|$ and $|\mathrm{Irr}(G)| = |\mathrm{Conj}(G)|$.
- **`verify_schurs_lemma(op, rep1, rep2, elements, is_equivalent=...)`**: Verifies equivariance $T\rho_1(g) = \rho_2(g)T$ and confirms $T = \mathbf{0}$ (inequivalent irreps) or $T = \lambda \mathbf{I}$ (equivalent irreps).

For subgroup restriction, sparse block-permutation induction, Frobenius reciprocity adjunctions, and Mackey double-coset decomposition, continue to [Induced Representations, Frobenius Reciprocity & Mackey Theory](induced_representations.md). For continuous infinitesimal symmetries, spin-$j$ modules, Casimir operators, and Clebsch–Gordan coupling tensors, see [Lie Algebra Representations, Weights & Clebsch–Gordan Tensors](lie_representations.md).
