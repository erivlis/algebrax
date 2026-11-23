---
title: Lie Algebra Representations, Weights & Clebsch–Gordan Tensors
description: Infinitesimal symmetries, spin-j representations, weight-space decompositions, quadratic Casimir operators, Freudenthal eigenvalues, and sparse Clebsch–Gordan coupling tensors in AlgebraX.
icon: lucide/orbit
---

# Lie Algebra Representations, Weights & Clebsch–Gordan Tensors

> **Intuition (Feynman):** *A Lie algebra representation turns abstract infinitesimal symmetries into concrete sparse matrices whose commutator matches the bracket. Adding two quantum spins $j_1$ and $j_2$ is simply a sparse change of basis — the Clebsch–Gordan matrix — from the uncoupled product world $|m_1, m_2\rangle$ to the total-spin world $|j, m\rangle$.*

A **Lie algebra representation** is a Lie algebra homomorphism from $\mathfrak{g}$ into the general linear algebra of endomorphisms on a vector space $V$:

$$\rho : \mathfrak{g} \longrightarrow \mathfrak{gl}(V), \qquad \rho([X, Y]) = [\rho(X), \rho(Y)] = \rho(X)\rho(Y) - \rho(Y)\rho(X)$$

AlgebraX implements Lie representations in `algebrax.rep.lie` (with convenient lazy re-exports in `algebrax.lie` and sparse coupling tensors in `algebrax.tensor.coupling`), strictly adhering to unboxed sparse matrix carriers.

---

## 1. Spin-$j$ Representations & The Exponential Bridge

The irreducible $(2j+1)$-dimensional representations of $\mathfrak{su}(2)$ and $\mathfrak{sl}(2)$ are parameterized by exact integer **half-spin units** `j_halves = 2*j` (so `1` is spin-$1/2$, `2` is spin-$1$, `3` is spin-$3/2$), preventing floating-point key drift:

- `form='su2'` (default): Skew-Hermitian generators matching `lie.su_n(2)` with $[T_0, T_1] = T_2$ (cyclic).
- `form='sl2'`: Split Chevalley generators $(E, F, H) = (J_+, J_-, 2J_z)$ matching `lie.sl_n(2)`.

Exponentiating via `rep.exp_map(element)` bridges from the Lie algebra to the Lie group — cleanly revealing the $SU(2) \to SO(3)$ double cover where a $2\pi$ rotation flips the sign of a spin-$1/2$ fermion ($-\mathbf{I}_2$) while leaving a spin-$1$ boson invariant ($+\mathbf{I}_3$):

```python
import math
from algebrax.rep.lie import spin_representation
from algebrax.verification import verify_lie_representation_homomorphism

# Spin-1/2 (dim 2), Spin-1 (dim 3), and Spin-3/2 (dim 4) of su(2)
spin_half = spin_representation(1, form='su2')
spin_one = spin_representation(2, form='su2')
spin_three_halves = spin_representation(3, form='su2')

assert spin_half.dimension == 2
assert spin_one.dimension == 3
assert spin_three_halves.dimension == 4

for rep in (spin_half, spin_one, spin_three_halves):
    assert all(verify_lie_representation_homomorphism(rep).values())

# Double cover signature: exp(2*pi * T_2) = -I_2 for spin-1/2, +I_3 for spin-1
rot_half = spin_half.exp_map({2: 2.0 * math.pi})
rot_one = spin_one.exp_map({2: 2.0 * math.pi})

assert math.isclose(rot_half[0][0].real, -1.0, abs_tol=1e-9)
assert math.isclose(rot_one[0][0].real, 1.0, abs_tol=1e-9)
```

---

## 2. Standard Representations & Functorial Operations

Every `LieAlgebra` supports canonical representations and functorial constructions without duplicating generator tables:

- **`adjoint_representation(alg)`**: Delegates directly to `alg.adjoint_matrix` ($\mathrm{ad}_X(Y) = [X, Y]$).
- **`defining_representation(alg)`**: Wraps `alg.matrix_basis` directly (for classical $\mathfrak{su}(n), \mathfrak{sl}(n), \mathfrak{so}(n), \mathfrak{sp}(n), \mathfrak{se}(n)$ as well as the 7-dimensional octonionic fundamental representation of $\mathfrak{g}_2$).
- **`direct_sum` / `direct_sum_lie_rep`**: Block-diagonal sum $(\rho_1 \oplus \rho_2)(X)$.
- **`tensor_product` / `tensor_product_lie_rep`**: Derivation (Leibniz) product $(\rho_1 \otimes \rho_2)(X) = \rho_1(X) \otimes \mathbf{I} + \mathbf{I} \otimes \rho_2(X)$.
- **`dual()`**: Contragredient dual $\rho^*(X) = -\rho(X)^T$.
- **`is_lie_intertwiner(T, rep1, rep2)`**: Verifies equivariance $T \rho_1(X) = \rho_2(X) T$ for all generators.

```python
from algebrax.lie import sl_n
from algebrax.rep.lie import (
    adjoint_representation,
    defining_representation,
    is_lie_intertwiner,
    spin_representation,
)
from algebrax.verification import verify_lie_representation_homomorphism

# Spin-1/2 of su(2) is pseudoreal: self-dual via the antisymmetric epsilon tensor
r_half = spin_representation(1, form='su2')
eps = {0: {1: 1.0}, 1: {0: -1.0}}
assert is_lie_intertwiner(eps, r_half, r_half.dual())

# Fundamental 3 and antifundamental 3-bar of sl(3) are inequivalent
sl3 = sl_n(3)
fund_3 = defining_representation(sl3)
anti_3 = fund_3.dual()
adj_8 = adjoint_representation(sl3)

assert fund_3.dimension == 3
assert adj_8.dimension == 8
assert all(verify_lie_representation_homomorphism(anti_3).values())
assert not is_lie_intertwiner({0: {0: 1.0}, 1: {1: 1.0}, 2: {2: 1.0}}, fund_3, anti_3)
```

---

## 3. Weight Spaces & Highest-Weight Decomposition

In a diagonalized Cartan basis $\mathfrak{h} = \operatorname{span}\{H_1, \dots, H_r\}$, any representation decomposes into simultaneous Cartan eigenspaces $V = \bigoplus_\mu V_\mu$. A **highest-weight vector** $v_\Lambda \in V_\Lambda$ is annihilated by every positive raising operator ($\rho(E_\alpha) v_\Lambda = \mathbf{0}$). Each linearly independent highest-weight vector generates an irreducible summand in $V$:

```python
from algebrax.lie import sl_n
from algebrax.rep.lie import (
    defining_representation,
    highest_weight_vectors,
    spin_representation,
    weight_space_decomposition,
)

# Decompose V_{1/2} (x) V_{1/2} = V_1 (+) V_0 via highest-weight vectors in sl(2)
r_half = spin_representation(1, form='sl2')
prod = r_half.tensor_product(r_half)

# Cartan H_0 is index 2; raising E_{01} is index 0
weights = weight_space_decomposition(prod, cartan_indices=(2,))
assert len(weights[(2.0,)]) == 1
assert len(weights[(0.0,)]) == 2   # m = 0 has multiplicity 2 (triplet + singlet)
assert len(weights[(-2.0,)]) == 1

hw = highest_weight_vectors(prod, cartan_indices=(2,), raising_indices=(0,))
hw_weights = sorted((w[0] for w, _ in hw), reverse=True)
assert hw_weights == [2.0, 0.0]    # Highest weights 2j = 2 (j=1) and 2j = 0 (j=0)

# Fundamental weight diagram of sl(3): Cartan (6, 7), raising (0, 1, 3)
def_sl3 = defining_representation(sl_n(3))
hw_sl3 = highest_weight_vectors(def_sl3, cartan_indices=(6, 7), raising_indices=(0, 1, 3))
assert len(hw_sl3) == 1
assert hw_sl3[0][0] == (1.0, 0.0)
```

---

## 4. Quadratic Casimir Operators & Freudenthal's Formula

For any semisimple Lie algebra with inverse Killing metric $g^{ij} = (K^{-1})_{ij}$, the **quadratic Casimir operator**

$$C = \sum_{i, j} g^{ij} \rho(X_i) \rho(X_j)$$

lies in the center of the universal enveloping algebra ($[C, \rho(X)] = \mathbf{0}$). By Schur's lemma, $C$ acts as a scalar multiple of the identity on every irreducible highest-weight module $V_\Lambda$, given exactly by **Freudenthal's eigenvalue formula**:

$$C|_{V_\Lambda} = \langle \Lambda, \Lambda + 2\delta \rangle_K \, \mathbf{I}$$

- In the canonical Killing normalization, $C = \frac{1}{2}j(j+1)\mathbf{I}$ for spin-$j$ of $\mathfrak{su}(2)/\mathfrak{sl}(2)$, $C = \frac{4}{9}\mathbf{I}$ for fundamental $\mathfrak{sl}(3)$, $C = \frac{1}{2}\mathbf{I}$ for the 7-dimensional fundamental of $\mathfrak{g}_2$, and $C = 1\cdot\mathbf{I}$ on the adjoint representation of **every** simple Lie algebra.
- Passing the physics angular-momentum metric `killing_metric_inv = {0: {0: -1.0}, 1: {1: -1.0}, 2: {2: -1.0}}` on skew-Hermitian $\mathfrak{su}(2)$ directly yields $J^2 = j(j+1)\mathbf{I}$.

```python
import math
from algebrax.lie import RootSystem, g2, sl_n
from algebrax.rep.lie import (
    adjoint_representation,
    defining_representation,
    freudenthal_casimir_eigenvalue,
    spin_representation,
)
from algebrax.verification import verify_casimir_commutativity

# 1. Killing-normalized Casimir matches Freudenthal formula on spin-3/2
rs_a1 = RootSystem.from_dynkin('A', 1)
r_3_2 = spin_representation(3, form='su2')
lam_3_2 = freudenthal_casimir_eigenvalue(rs_a1, [3])   # (1/2) * (3/2) * (5/2) = 15/8
assert math.isclose(lam_3_2, 15.0 / 8.0, rel_tol=1e-12)
assert all(verify_casimir_commutativity(r_3_2, expected_eigenvalue=lam_3_2).values())

# 2. Physics angular momentum Casimir J^2 = j(j+1) I via custom metric
phys_metric = {0: {0: -1.0}, 1: {1: -1.0}, 2: {2: -1.0}}
assert all(
    verify_casimir_commutativity(
        r_3_2,
        killing_metric_inv=phys_metric,
        expected_eigenvalue=1.5 * 2.5,
    ).values()
)

# 3. Exceptional Lie algebra G_2: 7-dim fundamental ([1, 0] -> 1/2) and 14-dim adjoint ([0, 1] -> 1)
g2_alg = g2()
rs_g2 = RootSystem.from_dynkin('G', 2)
assert all(
    verify_casimir_commutativity(
        defining_representation(g2_alg),
        expected_eigenvalue=freudenthal_casimir_eigenvalue(rs_g2, [1, 0]),
    ).values()
)
assert all(
    verify_casimir_commutativity(
        adjoint_representation(g2_alg),
        expected_eigenvalue=freudenthal_casimir_eigenvalue(rs_g2, [0, 1]),
    ).values()
)
```

---

## 5. Sparse Clebsch–Gordan Coupling 3-Tensors

When coupling two angular momenta $V_{j_1} \otimes V_{j_2} \cong \bigoplus_{j=|j_1 - j_2|}^{j_1 + j_2} V_j$, selection rules ($m = m_1 + m_2$ and $|j_1 - j_2| \le j \le j_1 + j_2$) make the coupling tensor overwhelmingly sparse. `algebrax.tensor.coupling` (re-exported from `algebrax.tensor` and `algebrax.rep.lie`) evaluates Racah's closed-form sum in exact rational arithmetic (`fractions.Fraction`) before a single final square root:

- **`clebsch_gordan_coefficient(j1_h, m1_h, j2_h, m2_h, j_h, m_h)`**: Single Condon–Shortley coefficient $\langle j_1 m_1; j_2 m_2 \mid j m \rangle$.
- **`clebsch_gordan_tensor(j1_h, j2_h)`**: Sparse dictionary `{((j_h, m_h), m1_h, m2_h): coeff}` storing only non-zero entries.
- **`clebsch_gordan_matrix(j1_h, j2_h)`**: Orthogonal change-of-basis matrix $U$ satisfying $U^T (\rho_{j_1} \otimes \rho_{j_2})(X) U = \bigoplus_j \rho_j(X)$.

```python
import math
from algebrax.tensor import (
    clebsch_gordan_coefficient,
    clebsch_gordan_matrix,
    clebsch_gordan_tensor,
)
from algebrax.verification import verify_clebsch_gordan_coupling

# Singlet state |0, 0> = (|+-> - |-+>) / sqrt(2)
assert math.isclose(clebsch_gordan_coefficient(1, 1, 1, -1, 0, 0), 1.0 / math.sqrt(2.0))
assert math.isclose(clebsch_gordan_coefficient(1, -1, 1, 1, 0, 0), -1.0 / math.sqrt(2.0))

# Spin 1 x Spin 1 = Spin 2 (+) Spin 1 (+) Spin 0 (only 18 non-zero entries out of 81 dense slots)
cg_1_1 = clebsch_gordan_tensor(2, 2)
assert len(cg_1_1) == 18

u_mat, coupled_basis = clebsch_gordan_matrix(2, 2)
assert len(coupled_basis) == 9

# Verify orthogonality, selection rules, and intertwiner equivariance on su(2)
assert all(verify_clebsch_gordan_coupling(2, 2).values())
assert all(verify_clebsch_gordan_coupling(3, 2).values())
```

---

## 6. Automated Verification & Falsification

`algebrax.verification` provides falsifiable invariants for every Lie representation law:

- **`verify_lie_representation_homomorphism(rep, algebra=None)`**: Checks bracket preservation $\rho([X_i, X_j]) = [\rho(X_i), \rho(X_j)]$, antisymmetry, and the Jacobi identity across all generator triples.
- **`verify_casimir_commutativity(rep, algebra=None, killing_metric_inv=None, expected_eigenvalue=None)`**: Checks centrality $[C, \rho(X_k)] = \mathbf{0}$ and optionally verifies Schur/Freudenthal scalarity $C = \lambda \mathbf{I}$.
- **`verify_clebsch_gordan_coupling(j1_halves, j2_halves)`**: Checks $U^T U = U U^T = \mathbf{I}$, angular-momentum selection rules, and $\mathfrak{su}(2)$ intertwiner equivariance $U^T (\rho_{j_1} \otimes \rho_{j_2})(X) U = \bigoplus_j \rho_j(X)$.

See also [Lie Algebras, Root Systems & BCH Dynamics](lie_algebras.md) for the underlying structure constants and root systems, [Group Representations & Character Tables](representations.md) for the finite-group counterpart, [Invariant Theory, Molien Series & Casimir Polynomials](invariant_theory.md) for Molien series, polynomial Reynolds projections, and cubic Casimir invariants ($C_3$, $d_{ijk}$), [Quantum Groups, Yang–Baxter & Braids](quantum_groups_and_braids.md) for the $q$-deformed quantum group $U_q(\mathfrak{sl}_2)$, universal $R$-matrices, and Jones polynomial invariants, and [Quiver Representations, Path Algebras & Gabriel's ADE Theorem](quivers_and_gabriel.md) for directed-graph representations, path algebras $KQ$, and Gabriel's ADE root bijection.
