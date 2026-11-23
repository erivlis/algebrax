---
title: Quantum Groups, Yang–Baxter & Braids
description: Drinfeld–Jimbo quantum group U_q(sl_2), universal R-matrices, the Quantum Yang–Baxter Equation, Artin braid representations, and the Jones polynomial.
icon: lucide/git-commit
---

# Quantum Groups, Yang–Baxter & Braids

In classical representation theory, swapping two tensor factors $v \otimes w \mapsto w \otimes v$ is an involution ($P^2 = \mathbf{I}$): swapping twice always returns to the starting state. **Quantum groups**—continuous $q$-deformations of universal enveloping algebras introduced by Drinfeld and Jimbo—break this cocommutativity. Their representations form **braided monoidal categories** in which exchange operators satisfy the **Artin braid relations** ($\beta^2 \ne \mathbf{I}$), turning representation traces directly into topological knot and link invariants such as the **Jones polynomial**.

---

## 1. The Quantum Group $U_q(\mathfrak{sl}_2)$ as a Hopf Algebra

`QuantumSL2` in `algebrax.rep.quantum` implements the Drinfeld–Jimbo Hopf algebra $U_q(\mathfrak{sl}_2)$ directly on the unboxed Poincaré–Birkhoff–Witt (PBW) ordered basis $\{E^a K^b F^c \mid a, c \in \mathbb{Z}_{\ge 0},\; b \in \mathbb{Z}\}$, represented as sparse dictionaries `dict[tuple[int, int, int], complex]`.

### Defining Relations & Non-Cocommutative Structure

- **Algebraic relations**:
  $$K K^{-1} = K^{-1} K = \mathbf{1}, \qquad K E K^{-1} = q^2 E, \qquad K F K^{-1} = q^{-2} F, \qquad [E, F] = \frac{K - K^{-1}}{q - q^{-1}}$$
- **Non-cocommutative coproduct ($\Delta \neq \Delta^{\mathrm{op}}$)**:
  $$\Delta(K) = K \otimes K, \qquad \Delta(E) = E \otimes \mathbf{1} + K \otimes E, \qquad \Delta(F) = F \otimes K^{-1} + \mathbf{1} \otimes F$$
- **Counit & non-involutive antipode ($S^2 \neq \mathrm{id}$)**:
  $$\epsilon(E) = \epsilon(F) = 0, \quad \epsilon(K) = 1, \qquad S(K) = K^{-1}, \quad S(E) = -K^{-1} E, \quad S(F) = -F K$$
  Notice that $S^2(E) = q^{-2} E$ and $S^2(F) = q^2 F$: unlike group Hopf algebras where $S^2 = \mathrm{id}$, the quantum antipode has infinite order for generic $q$.

```python
import cmath
from algebrax.algebra._hopf import HopfAlgebra
from algebrax.rep import QuantumSL2
from algebrax.verification import semiring_elements_equal, verify_hopf_algebra_laws

q = cmath.exp(0.35j) * 1.15
u_q = QuantumSL2(q)
assert isinstance(u_q, HopfAlgebra)

# Verify full Hopf algebra axioms (coassociativity, counitality, bialgebra, antipode)
r_samples = [1.0 + 0.0j, -0.5 + 0.25j, 0.0 + 1.0j]
c_samples = [u_q.one, u_q.E, u_q.F, u_q.K, u_q.K_inv, u_q.mul(u_q.E, u_q.F)]
assert all(verify_hopf_algebra_laws(u_q, r_samples, c_samples, tol=1e-8).values())

# Confirm non-cocommutativity and non-involutive antipode S^2(E) = q^{-2} E
delta_e = u_q.coproduct(u_q.E)
delta_e_op = {(v, u): coeff for (u, v), coeff in delta_e.items()}
assert not semiring_elements_equal(delta_e, delta_e_op)
assert semiring_elements_equal(u_q.antipode(u_q.antipode(u_q.E)), u_q.smul(q**-2, u_q.E))
```

---

## 2. $q$-Deformed Spin-$j$ Representations & The Classical Limit $q \to 1$

For any non-negative half-integer spin $j = \text{j\_halves} / 2$, `u_q.spin_representation(j_halves)` constructs the $(2j + 1)$-dimensional irreducible module $V_j$ in the Condon–Shortley weight basis $|j, j\rangle, \dots, |j, -j\rangle$:

$$K |j, m\rangle = q^{2m} |j, m\rangle, \qquad E |j, m - 1\rangle = \sqrt{[j + m]_q [j - m + 1]_q}\, |j, m\rangle, \qquad F |j, m\rangle = \sqrt{[j + m]_q [j - m + 1]_q}\, |j, m - 1\rangle$$

where $[n]_q = \frac{q^n - q^{-n}}{q - q^{-1}}$ is the symmetric quantum integer (`u_q.q_bracket(n)`). As $q \to 1$, $[n]_q \to n$ smoothly and `spin_representation` converges identically to the classical $\mathfrak{sl}_2$ representation in `algebrax.rep.lie.spin_representation(j_halves, form='sl2')`.

```python
import cmath
from algebrax.rep import QuantumSL2
from algebrax.rep.lie import spin_representation as classical_spin_rep
from algebrax.verification import verify_quantum_sl2_relations

q = cmath.exp(0.4j) * 1.1
u_q = QuantumSL2(q)

# Verify Drinfeld-Jimbo relations across spins j = 0, 1/2, 1, 3/2, 2
for j_halves in range(5):
    rep_j = u_q.spin_representation(j_halves)
    assert all(verify_quantum_sl2_relations(q, rep_j).values())

# Smooth q -> 1 limit recovers classical sl_2 Condon-Shortley matrices
q_limit = QuantumSL2(1.0).spin_representation(3)
lie_rep = classical_spin_rep(3, form='sl2')
assert abs(q_limit['E'][0][1] - lie_rep(0)[0][1]) < 1e-12
assert abs(q_limit['F'][1][0] - lie_rep(1)[1][0]) < 1e-12
```

---

## 3. Universal $R$-Matrix, Yang–Baxter Equation & Braiding

On the fundamental tensor product $V_{1/2} \otimes V_{1/2}$ ordered by $\{|00\rangle, |01\rangle, |10\rangle, |11\rangle\}$, the fundamental $R$-matrix returned by `universal_r_matrix_sl2_fundamental(q)` is:

$$R = \begin{pmatrix}
q & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & q - q^{-1} & 1 & 0 \\
0 & 0 & 0 & q
\end{pmatrix}$$

It satisfies the **Quantum Yang–Baxter Equation (QYBE)** on $V_{1/2}^{\otimes 3}$:

$$R_{12} R_{13} R_{23} = R_{23} R_{13} R_{12}$$

Composing with the tensor swap operator $P(|i\rangle \otimes |j\rangle) = |j\rangle \otimes |i\rangle$ gives the **braiding isomorphism** $B = P \circ R$ (`braiding_operator(R, dim=2)`), which:

1. Intertwines the $U_q(\mathfrak{sl}_2)$ coproduct: $B \Delta(x) = \Delta(x) B$ for all $x \in U_q(\mathfrak{sl}_2)$.
2. Obeys the **Hecke quadratic relation** $(B - q\mathbf{I})(B + q^{-1}\mathbf{I}) = \mathbf{0}$, so $B^{-1} = B - (q - q^{-1})\mathbf{I}$ and $B^2 \neq \mathbf{I}$ for $q^2 \neq 1$.
3. Generates an explicit sparse $2^n \times 2^n$ representation of the **Artin braid group $B_n$** (`braid_to_matrix`), obeying $B_i B_{i+1} B_i = B_{i+1} B_i B_{i+1}$ and far commutativity $B_i B_j = B_j B_i$ for $|i - j| \ge 2$.

```python
import cmath
from algebrax.rep import (
    braid_to_matrix,
    braiding_operator,
    universal_r_matrix_sl2_fundamental,
)
from algebrax.rep.quantum import _embed_two_site_operator
from algebrax.verification import verify_artin_braid_relations, verify_yang_baxter_equation

q = cmath.exp(0.37j) * 1.15
r_mat = universal_r_matrix_sl2_fundamental(q)

# Verify QYBE (R_12 R_13 R_23 = R_23 R_13 R_12) and braided form using sparse embeddings
assert all(verify_yang_baxter_equation(r_mat, dim=2).values())

# Verify Artin braid and far-commutativity relations on 4 strands
b_mat = braiding_operator(r_mat, dim=2)
b1 = _embed_two_site_operator(b_mat, 0, 4, dim=2)
b2 = _embed_two_site_operator(b_mat, 1, 4, dim=2)
b3 = _embed_two_site_operator(b_mat, 2, 4, dim=2)
assert all(verify_artin_braid_relations(b1, b2, b3).values())

# Braid word cancellation sigma_1 sigma_2 sigma_2^{-1} sigma_1^{-1} = I
identity_3 = braid_to_matrix([1, 2, -2, -1], num_strands=3, q=q)
assert len(identity_3) == 8 and all(abs(identity_3[i][i] - 1.0) < 1e-11 for i in range(8))
```

---

## 4. Quantum Trace & The Jones Polynomial of Knots and Links

Closing a braid $\beta \in B_n$ yields an oriented knot or link $L = \widehat{\beta}$. Ordinary matrix trace fails Markov II stabilization invariance, but weighting by the Cartan tensor $K^{\otimes n}$ yields the **quantum trace** (`quantum_trace`):

$$\mathrm{Tr}_q(M) = \mathrm{Tr}\!\left(K^{\otimes n} M\right), \qquad \mathrm{Tr}_q(\mathbf{I}_{2^n}) = (q + q^{-1})^n = [2]_q^n$$

Normalizing by the braid writhe $w(\beta) = \sum_k \operatorname{sgn}(g_k)$ gives the **Jones polynomial** $V_L(t)$ evaluated at $t = q^{-2}$ (`jones_polynomial_eval`):

$$V_L(t)\Big|_{t = q^{-2}} = (-1)^{n - 1 + w(\beta)}\, q^{-2 w(\beta)}\, \frac{\mathrm{Tr}_q(\rho(\beta))}{q + q^{-1}}$$

which satisfies the canonical Jones skein relation $t^{-1} V_{L_+}(t) - t V_{L_-}(t) = (t^{1/2} - t^{-1/2}) V_{L_0}(t)$ with $V_{\text{unknot}}(t) = 1$:

| Knot / Link | Braid Presentation $(\beta, n)$ | Exact Jones Polynomial $V_L(t)$ ($t = q^{-2}$) |
|:---|:---|:---|
| **Unknot** $0_1$ | `([], 1)`, `([1], 2)`, `([1, -2], 3)` | $1$ |
| **2-Component Unlink** | `([], 2)` | $-(t^{1/2} + t^{-1/2})$ |
| **Positive Hopf Link** | `([1, 1], 2)` | $-(t^{1/2} + t^{5/2})$ |
| **Right-Handed Trefoil** $3_1$ | `([1, 1, 1], 2)` | $t + t^3 - t^4$ |
| **Left-Handed Trefoil** $\overline{3_1}$ | `([-1, -1, -1], 2)` | $t^{-1} + t^{-3} - t^{-4}$ |
| **Figure-Eight Knot** $4_1$ | `([1, -2, 1, -2], 3)` | $t^{-2} - t^{-1} + 1 - t + t^2$ |

```python
import cmath
from algebrax.rep import jones_polynomial_eval

q = cmath.exp(0.37j) * 1.15
t = q ** (-2)

# Markov II stabilization invariance on the unknot
assert abs(jones_polynomial_eval([], 1, q) - 1.0) < 1e-11
assert abs(jones_polynomial_eval([1, -2], 3, q) - 1.0) < 1e-11

# Right-handed trefoil 3_1 vs its chiral mirror image
v_trefoil_r = jones_polynomial_eval([1, 1, 1], 2, q)
v_trefoil_l = jones_polynomial_eval([-1, -1, -1], 2, q)
assert abs(v_trefoil_r - (t + t**3 - t**4)) < 1e-11
assert abs(v_trefoil_l - (t**-1 + t**-3 - t**-4)) < 1e-11
assert abs(v_trefoil_r - v_trefoil_l) > 1e-2  # detects chirality!

# Amphichiral figure-eight knot 4_1: V(t) == V(t^{-1})
v_fig8 = jones_polynomial_eval([1, -2, 1, -2], 3, q)
assert abs(v_fig8 - (t**-2 - t**-1 + 1 - t + t**2)) < 1e-10
assert abs(v_fig8 - jones_polynomial_eval([1, -2, 1, -2], 3, 1.0 / q)) < 1e-10
```

---

## 5. Automated Verification & Falsification

`algebrax.verification` exposes falsifiable invariants for quantum groups, $R$-matrices, and braids:

- **`verify_hopf_algebra_laws(u_q, r_samples, c_samples)`**: Verifies coassociativity, counitality, bialgebra compatibility, and the non-involutive Hopf antipode axiom over complex scalars.
- **`verify_quantum_sl2_relations(q, rep)`**: Checks $K K^{-1} = \mathbf{I}$, $K E K^{-1} = q^2 E$, $K F K^{-1} = q^{-2} F$, and $[E, F] = (K - K^{-1}) / (q - q^{-1})$ with a smooth L'Hôpital guard at $q \to \pm 1$.
- **`verify_yang_baxter_equation(r_matrix, dim=2)`**: Evaluates $R_{12} R_{13} R_{23} = R_{23} R_{13} R_{12}$ and $B_1 B_2 B_1 = B_2 B_1 B_2$ directly in sparse coordinates without dense $d^3 \times d^3$ allocations.
- **`verify_artin_braid_relations(b1, b2, b3=None)`**: Checks adjacent braiding $B_1 B_2 B_1 = B_2 B_1 B_2$ and (when `b3` is provided) far commutativity $B_1 B_3 = B_3 B_1$.

See also [Coalgebras, Bialgebras & Hopf Algebras](coalgebras_and_hopf.md) for the underlying Hopf algebra protocol hierarchy, [Lie Algebra Representations & Clebsch–Gordan Tensors](lie_representations.md) for the classical $q \to 1$ spin-$j$ modules, and [Invariant Theory, Molien Series & Casimir Polynomials](invariant_theory.md) for classical polynomial and Casimir invariants.
