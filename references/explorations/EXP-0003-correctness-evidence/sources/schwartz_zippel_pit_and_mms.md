# Randomized Polynomial Identity Testing (PIT) & Method of Manufactured Solutions (MMS)

## Overview

This source reference documents two state-of-the-art verification methodologies adapted from computational complexity, computer algebra systems (CAS), and computational physics for verifying discrete algebraic and geometric computations in **AlgebraX**:

1. **Schwartz–Zippel Randomized Polynomial Identity Testing (PIT)** for high-degree symbolic equivalence without monomial explosion.
2. **Method of Manufactured Solutions (MMS)** for verifying discrete differential geometry, Hodge-Laplacians, and topological flow solvers against exact continuous limits.

---

## 1. Schwartz–Zippel Randomized Polynomial Identity Testing (PIT)

### 1.1 The Combinatorial Explosion Problem in Symbolic Verification
When verifying algebraic laws (e.g., Jacobi identity in Lie algebras, associativity of multivector products in Clifford algebras, or determinant expansions), symbolic engines like SymPy expand expressions into canonical sums of monomials:

$$\sum_{i_1, \dots, i_n} c_{i_1 \dots i_n} x_1^{i_1} \cdots x_n^{i_n}$$

For a polynomial in $n$ variables with degree $d$, the number of monomials scales as $\binom{n+d}{d}$. For moderate sizes ($n = 10, d = 6$), monomial expansion requires tracking $\binom{16}{6} = 8,008$ terms; for larger systems, it becomes completely intractable, resulting in timeouts or memory exhaustion during test runs.

### 1.2 The Schwartz–Zippel–DeMillo–Lipton Theorem
Rather than expanding expressions canonically, Randomized PIT tests whether an algebraic identity $P(x_1, \dots, x_n) \equiv 0$ holds by evaluating the unexpanded arithmetic expression (represented as a straight-line computation or AST) at independent, randomly chosen values.

**Theorem (Schwartz–Zippel):**
Let $P(x_1, \dots, x_n) \in \mathbb{F}[x_1, \dots, x_n]$ be a non-zero multivariate polynomial of total degree $d \ge 0$ over a field $\mathbb{F}$. Let $S \subseteq \mathbb{F}$ be a finite subset. If coordinates $r_1, \dots, r_n$ are sampled independently and uniformly at random from $S$, then:

$$\Pr[P(r_1, \dots, r_n) = 0] \le \frac{d}{|S|}$$

### 1.3 One-Sided Error and Amplification
* If $P \equiv 0$, the evaluation $P(r)$ is **identically 0** for every random sample $r$.
* If $P \not\equiv 0$, the probability of an accidental root (false positive zero) is at most $\frac{d}{|S|}$.
* By choosing $|S| = 10^6$ and testing $k$ independent random vectors:

$$\Pr[\text{False Zero in } k \text{ trials}] \le \left(\frac{d}{|S|}\right)^k$$

For $d = 10$, a single evaluation gives error $< 10^{-5}$; $k = 3$ evaluations reduce the probability of error to $< 10^{-15}$ (virtually zero).

### 1.4 Application in AlgebraX
```python
import random


def test_pit_clifford_rotor_norm_conservation():
    # Verify rotor sandwich rotation preserves multivector quadratic form:
    # Q(R * v * ~R) == Q(v) without full symbolic Clifford expansion
    S = range(1, 100_000)
    for _ in range(5):
        # Sample random coordinates for 3D vector v and rotor R
        v_coords = {0: random.choice(S), 1: random.choice(S), 2: random.choice(S)}
        # Evaluate using pure integer/rational arithmetic
        # ...
        # Assert quadratic norm difference evaluates strictly to 0
```

---

## 2. Method of Manufactured Solutions (MMS) for Discrete Calculus & Homology

### 2.1 The Oracle Problem in Discrete Differential Geometry
In Discrete Exterior Calculus (DEC, `EP-0160`) and Graph Laplacians (`EP-0152`), closed-form solutions on arbitrary irregular meshes do not exist. Traditional unit tests only verify trivial topologies (e.g., a 3-vertex triangle).

### 2.2 MMS Formulation
The **Method of Manufactured Solutions (MMS)** (standardized under ASME V&V 20) bridges continuous calculus and discrete mesh operators:
1. **Manufacture an Exact Solution:** Choose an arbitrary smooth, non-trivial continuous potential field $\phi(x, y)$ (e.g., $\phi(x, y) = \sin(2\pi x) \cos(2\pi y)$).
2. **Analytic Operator Application:** Compute the exact continuous gradient $\mathbf{u} = \nabla \phi$ and Laplacian $\psi = \Delta \phi$ analytically.
3. **Discretize (De Rham Projection):**
   * Discretize the domain into a sequence of increasingly refined simplicial meshes $\mathcal{K}_h$ of grid spacing $h$.
   * Sample 0-forms $\phi_h$ at vertices $v \in \mathcal{K}_h$.
   * Integrate 1-forms along oriented edges $e_{ij} = [v_i, v_j]$: $\omega_e = \int_{v_i}^{v_j} \mathbf{u} \cdot d\mathbf{r} = \phi(v_j) - \phi(v_i)$.
4. **Asymptotic Convergence Order Verification:**
   * Apply AlgebraX's discrete exterior derivative $d$ and Hodge-Laplacian $\Delta_h$.
   * Measure the discrete error norm:
     $$E(h) = \| \Delta_h \phi_h - \Pi_h(\psi) \|_{L_2}$$
   * Verify that the empirical order of accuracy $p = \frac{\log(E(h_1) / E(h_2))}{\log(h_1 / h_2)}$ matches the theoretical discretization rate ($O(h)$ or $O(h^2)$).

---

## 3. Certified Computation (Proof-Carrying Solvers)

For linear algebra and topological decompositions where verifying an answer is asymptotically cheaper than computing it ($O(N)$ vs $O(N^3)$), AlgebraX solvers can emit **Verification Certificates**:

| Computation | Solver Complexity | Verifier Check | Certificate Complexity |
|:------------|:------------------|:---------------|:-----------------------|
| **Helmholtz–Hodge Decomposition** | $O(N^3)$ (SVD / Pseudoinverse) | Orthogonality $\langle d\alpha, \delta\beta \rangle = 0$, Reconstruction $\|v - (d\alpha + \delta\beta + \gamma)\| < \epsilon$, Harmonicity $\|\Delta \gamma\| < \epsilon$ | $O(E)$ (Sparse Matrix-Vector product) |
| **Matrix Inversion / Solver** | $O(N^3)$ (LU / QR) | Residual check $\|A x - b\|_\infty < \text{tol}$ | $O(\text{nnz}(A))$ |
| **Simplicial Homology $\partial_k$** | $O(N^3)$ (Smith Normal Form) | Nilpotency $\partial_{k-1} \circ \partial_k = \mathbf{0}$ | $O(\text{nnz}(\partial))$ |
| **Fiedler Eigenvector** | $O(N^2)$ (Rayleigh Iteration) | Eigen-residual $\|L v_2 - \lambda_2 v_2\| < \epsilon$, Orthogonality $\mathbf{1}^T v_2 = 0$ | $O(E)$ |
