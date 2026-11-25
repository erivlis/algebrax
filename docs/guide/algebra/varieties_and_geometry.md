---
title: Affine Varieties, Coordinate Rings & Stickelberger Solvers
description: Affine algebraic varieties V(I), coordinate rings k[V], Stickelberger companion matrix solvers, finite-field elliptic curves, Boolean SAT, polynomial morphisms, Grassmannians, and algebraic K-theory bridges.
---

# Affine Varieties, Coordinate Rings & Stickelberger Solvers (`algebrax.variety`)

## 1. The Practical Problem: Turning Nonlinear Polynomial Systems into Sparse Linear Algebra

Whenever a physical or mathematical constraint is polynomial—robotic joint linkages, quantum separability (rank-1 tensors), statistical independence, elliptic curves over finite fields, or Boolean circuits—traditional numerical methods (Newton–Raphson, gradient descent) suffer from two fatal limitations:

1. **Initial-Guess Fragility**: They find at most one local root per starting seed and diverge near singularities.
2. **Floating-Point Collapse**: Eliminating variables with IEEE-754 floats turns cancellation noise into false pivots.

In AlgebraX, `algebrax.variety` implements Emmy Noether's **Ideal–Variety Duality** over exact fields (`StandardField(Fraction)`, `ModularField(p)`, `GaloisField`):

$$\text{Ideal } I \longleftrightarrow \text{Variety } V(I), \qquad \text{Quotient } k[X]/I \longleftrightarrow \text{Coordinate Ring } k[V], \qquad \text{RingHom } \phi^* \longleftrightarrow \text{Morphism } \phi: V \to W$$

For zero-dimensional varieties (isolated roots), **Stickelberger's Eigenvalue Theorem** constructs exact sparse multiplication matrices $M_{x_i}: k[V] \to k[V]$ on the finite standard monomial basis $\mathcal{B} = \{x^\alpha \notin \langle \mathrm{LT}(I) \rangle\}$, reducing nonlinear root-finding to simultaneous eigenvalues of commuting matrices.

---

## 2. The 30-Second Executable Snippet

```python
from fractions import Fraction
from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
from algebrax.variety import (
    AffineVariety,
    companion_matrix,
    solve_exact_rational,
    solve_zero_dimensional,
)
from algebrax.verification import verify_stickelberger_laws

# Intersect circle x^2 + y^2 = 5 and hyperbola x * y = 2 over exact Q
Q = StandardField(Fraction)
R = MultivariatePolynomialAlgebra(Q, n_vars=2, order='grevlex')
x, y = R.gen(0), R.gen(1)

circle = R.sub(R.add(R.mul(x, x), R.mul(y, y)), R.const(Fraction(5)))
hyperb = R.sub(R.mul(x, y), R.const(Fraction(2)))

V = AffineVariety(R, [circle, hyperb])
assert V.krull_dimension() == 0
assert len(V.quotient_basis() or []) == 4
assert V.is_smooth_at((Fraction(1), Fraction(2)))

# Exact sparse companion matrices M_x, M_y commute: [M_x, M_y] == 0
Mx, My = companion_matrix(V, 0), companion_matrix(V, 1)
assert all(verify_stickelberger_laws(V).values())

# Pure-Python exact rational roots & full complex/real Stickelberger roots
assert solve_exact_rational(V) == [
    (Fraction(-2), Fraction(-1)),
    (Fraction(-1), Fraction(-2)),
    (Fraction(1), Fraction(2)),
    (Fraction(2), Fraction(1)),
]
roots = solve_zero_dimensional(V)
assert len(roots) == 4
```

---

## 3. Atomic Geometric Mixins & Flat Protocols

Following the **Law of Flat Protocol Composition**, `algebrax.variety` introduces four Layer 1 geometric capability mixins and two flat Layer 2 protocols (zero Layer-2-to-Layer-2 inheritance):

| Protocol (`algebrax.variety`) | Layer | Required Capabilities | Algebraic Signature |
|:------------------------------|:------|:----------------------|:--------------------|
| `HasPointLocus[P]` | Layer 1 | `ambient_dimension`, `contains_point(p)` | $\langle \mathbb{A}^n, X, \in \rangle$ |
| `HasDimension` | Layer 1 | `dimension()` | $\langle X, \dim X \rangle$ |
| `HasCoordinateRing[V]` | Layer 1 | `ideal`, `coordinate_ring` | $\langle V(I), I, k[V] \rangle$ |
| `HasTangentLocus[V]` | Layer 1 | `jacobian_at(p)`, `is_smooth_at(p)` | $\langle X, J(p), \operatorname{is\_smooth\_at} \rangle$ |
| `GeometricVariety[P]` | Layer 2 | `HasPointLocus[P]`, `HasDimension` | Unified classical & tropical variety interface |
| `SmoothableVariety[V]` | Layer 2 | `HasPointLocus`, `HasDimension`, `HasCoordinateRing`, `HasTangentLocus` | Smoothable affine variety with Jacobian & $k[V]$ |

---

## 4. Ideal–Variety Operations, Smoothness & Seidenberg Radicalization

`AffineVariety[V]` pairs every geometric set operation with its exact commutative-algebraic dual:

| Geometric Operation | Algebraic Dual | Method |
|:--------------------|:---------------|:-------|
| Empty variety check $V_{\bar{k}}(I) = \emptyset$ | Hilbert's Weak Nullstellensatz ($1 \in I$) | `V.is_empty_over_closure()` |
| Intersection $V(I) \cap V(J)$ | Ideal sum $V(I + J)$ | `V.intersect(W)` |
| Union $V(I) \cup V(J)$ | Ideal intersection $V(I \cap J)$ via $(tI + (1-t)J) \cap k[X]$ | `V.union(W)` |
| Coordinate projection $\overline{\pi(V)}$ | Elimination ideal $I \cap k[x_{k+1}, \dots, x_n]$ (`lex` order) | `V.eliminate(k)` |
| Intrinsic dimension $\dim V$ | Max independent variable set of $\langle \mathrm{LT}(I) \rangle$ | `V.krull_dimension()` |
| Hilbert growth $\dim_k k[V]_{\le d}$ | Graded standard monomial count | `V.hilbert_function(d)` |
| Smooth vs. singular point $p \in V$ | Jacobian rank criterion $\operatorname{rank}_k J(p) = n - \dim V$ | `V.is_smooth_at(p)` |
| Reduced / square-free 0D variety $V(\sqrt{I})$ | Seidenberg's Lemma + `square_free_part` | `V.radical_zero_dim()` |

```python
from fractions import Fraction
from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
from algebrax.variety import AffineVariety

Q = StandardField(Fraction)
R = MultivariatePolynomialAlgebra(Q, n_vars=2)
x, y = R.gen(0), R.gen(1)

# Cuspidal cubic y^2 - x^3 = 0: singular cusp at (0, 0), smooth at (1, 1)
cusp = AffineVariety(R, [R.sub(R.mul(y, y), R.mul(R.mul(x, x), x))])
assert cusp.krull_dimension() == 1
assert cusp.contains_point((Fraction(0), Fraction(0)))
assert not cusp.is_smooth_at((Fraction(0), Fraction(0)))
assert cusp.is_smooth_at((Fraction(1), Fraction(1)))
```

---

## 5. Solving 2R Planar Robot Inverse Kinematics via Stickelberger Matrices

For a 2-link planar arm with link lengths $L_1 = 2, L_2 = 1$ reaching target $(2, 1)$, let $(c_1, s_1, c_2, s_2) = (\cos\theta_1, \sin\theta_1, \cos\theta_2, \sin\theta_2)$. The forward kinematics and trigonometric identities form a 0-dimensional variety with quotient dimension 2 (the exact elbow-up and elbow-down configurations):

```python
from fractions import Fraction
from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
from algebrax.variety import AffineVariety, solve_zero_dimensional
from algebrax.verification import verify_stickelberger_laws

Q = StandardField(Fraction)
R4 = MultivariatePolynomialAlgebra(Q, n_vars=4, order='grevlex')
c1, s1, c2, s2 = (R4.gen(i) for i in range(4))

# Unit-circle constraints: c_1^2 + s_1^2 = 1, c_2^2 + s_2^2 = 1
trig1 = R4.sub(R4.add(R4.mul(c1, c1), R4.mul(s1, s1)), R4.one)
trig2 = R4.sub(R4.add(R4.mul(c2, c2), R4.mul(s2, s2)), R4.one)

# Forward kinematics for L1 = 2, L2 = 1 targeting (2, 1):
#   x = 2*c1 + (c1*c2 - s1*s2) - 2 = 0
#   y = 2*s1 + (s1*c2 + c1*s2) - 1 = 0
cos_12 = R4.sub(R4.mul(c1, c2), R4.mul(s1, s2))
sin_12 = R4.add(R4.mul(s1, c2), R4.mul(c1, s2))
fk_x = R4.sub(R4.add(R4.smul(Fraction(2), c1), cos_12), R4.const(Fraction(2)))
fk_y = R4.sub(R4.add(R4.smul(Fraction(2), s1), sin_12), R4.one)

ik_variety = AffineVariety(R4, [trig1, trig2, fk_x, fk_y])
# quotient_basis() returns None for positive-dimensional varieties and a finite basis for 0D varieties
basis = ik_variety.quotient_basis()
assert basis is not None and len(basis) == 2
assert all(verify_stickelberger_laws(ik_variety).values())
poses = solve_zero_dimensional(ik_variety)  # Both elbow-up and elbow-down poses simultaneously
```

---

## 6. Finite-Field Elliptic Curves, Hasse's Bound & Boolean $\mathbb{F}_2$ SAT

Over finite fields (`ModularField(p)` and `GaloisField`), `enum_variety_points` uses prefix-pruned backtracking against the Gröbner basis, and `solve_f2_sat` solves Boolean CNF formulas via Nullstellensatz reduction in $\mathbb{F}_2[x_1, \dots, x_n] / \langle x_i^2 + x_i \rangle$:

```python
import math
from algebrax.algebra import ModularField, MultivariatePolynomialAlgebra
from algebrax.variety import AffineVariety, enum_variety_points, solve_f2_sat

# Elliptic curve y^2 = x^3 + x + 1 over F_7
p = 7
R = MultivariatePolynomialAlgebra(ModularField(p), n_vars=2)
x, y = R.gen(0), R.gen(1)
ec = AffineVariety(R, [R.sub(R.mul(y, y), R.add(R.add(R.mul(R.mul(x, x), x), x), R.one))])
pts = enum_variety_points(ec)
n_projective = len(pts) + 1  # include point at infinity
assert abs(n_projective - (p + 1)) <= 2 * math.sqrt(p)

# Algebraic 3-SAT over F_2
sat_solutions = solve_f2_sat(3, [[1, 2], [-1, 3], [-2, -3], [1, -3]])
assert sat_solutions == [(0, 1, 0), (1, 0, 1)]
```

---

## 7. Morphisms, GIT Syzygies, Grassmannians, Matrix-Group Hopf Algebras & K-Theory

`algebrax.variety` connects algebraic geometry across the full AlgebraX ecosystem:

- **Contravariant Pullbacks (`PolynomialMap`)**: Realizes $\phi: V \to W$ as a `RingHom` $\phi^*: k[W] \to k[V]$ satisfying $(\phi^* g)(p) = g(\phi(p))$.
- **Invariant Syzygies (`syzygy_variety`)**: Computes the GIT quotient relation ideal $I_{\text{syz}} \triangleleft k[y_1, \dots, y_m]$ among invariant polynomials via `lex` elimination.
- **Plücker Grassmannians (`plucker_grassmannian_variety`)**: Constructs the quadratic Plücker cone over $\operatorname{Gr}(k, n)$ (e.g., $p_{01} p_{23} - p_{02} p_{13} + p_{03} p_{12} = 0$ for $\operatorname{Gr}(2, 4)$).
- **Coordinate Hopf Algebras (`CoordinateHopfAlgebra`)**: Equips $k[\operatorname{SL}_n]$ or $k[\operatorname{SO}_n]$ with exact `HopfAlgebra` comultiplication $\Delta(x_{ij}) = \sum_k x_{ik} \otimes x_{kj}$, counit $\epsilon(x_{ij}) = \delta_{ij}$, and adjugate antipode $S(X) = X^{-1} \bmod I(G)$.
- **Algebraic & Higher K-Theory ($K_0, K_1, K_2^M$)**:
  - `is_serre_swan_projective_bundle`: Checks $P^2 \equiv P \pmod{I(V)}$ for algebraic vector bundles in $K_0(V)$.
  - `schubert_chern_cohomology_ring`: Constructs Borel's Chern/Schubert ring $H^*(\operatorname{Gr}(k, n); k)$ (where the first Chern class $c_1$ equals the hyperplane Schubert cycle $\sigma_1$, verifying $c_1^4 = 2 c_2^2$ on $\operatorname{Gr}(2, 4)$).
  - `motivic_point_count_homomorphism`: Evaluates $\#V(\mathbb{F}_p) - \#W(\mathbb{F}_p)$ on $K_0(\mathbf{Var}_{\mathbb{F}_p})$.
  - `coordinate_ring_unit_inverse`: Certifies units $[u] \in k[V]^\times \hookrightarrow K_1(k[V])$ and extracts exact $u^{-1} \bmod I(V)$.
  - `tame_symbol_padic` & `milnor_symbol_conic_variety`: Evaluates the $p$-adic Tame Symbol $T_p: K_2(\mathbb{Q}) \to \mathbb{F}_p^\times$ (verifying Matsumoto's Steinberg relation $T_p(a, 1-a) = 1$) and constructs the norm-residue conic $a x^2 + b y^2 = 1$.

```python
from fractions import Fraction
from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
from algebrax.variety import (
    AffineVariety,
    CoordinateHopfAlgebra,
    plucker_grassmannian_variety,
    schubert_chern_cohomology_ring,
    tame_symbol_padic,
)
from algebrax.verification import verify_coordinate_hopf_laws

Q = StandardField(Fraction)

# 1. Coordinate Hopf Algebra k[SL_2]
R4 = MultivariatePolynomialAlgebra(Q, n_vars=4)
a, b, c, d = (R4.gen(i) for i in range(4))
sl2 = AffineVariety(R4, [R4.sub(R4.sub(R4.mul(a, d), R4.mul(b, c)), R4.one)])
hopf = CoordinateHopfAlgebra(2, sl2)
assert hopf.antipode(a) == d and hopf.antipode(b) == R4.neg(b)
assert all(verify_coordinate_hopf_laws(hopf, [R4.one, a, b, c, d]).values())

# 2. Grassmannian Gr(2, 4) Plucker variety & Borel Schubert cohomology ring
gr24 = plucker_grassmannian_variety(Q, 2, 4)
assert gr24.krull_dimension() == 5
cohom = schubert_chern_cohomology_ring(Q, 2, 4)
# Generators c1, c2 are the universal Chern classes (c1 = sigma_1, c2 = sigma_{1,1})
c1, c2 = cohom.base_ring.gen(0), cohom.base_ring.gen(1)
# QuotientRing.project reduces any raw polynomial into its canonical normal form modulo the Borel ideal
assert cohom.power(c1, 4) == cohom.project(cohom.base_ring.smul(Fraction(2), cohom.power(c2, 2)))

# 3. K_2 Tame Symbol Steinberg Relation T_7(a, 1 - a) == 1 mod 7
assert tame_symbol_padic(Fraction(3, 5), Fraction(2, 5), 7) == 1
```

---

## 8. Related Guides & Recipes

### Related User Guides
- [**Polynomials, Ideals & Quotients**](polynomials_and_quotients.md): Multivariate polynomial rings (`MultivariatePolynomialAlgebra`), Buchberger/$F_4$ Gröbner bases, `GroebnerIdeal`, and `QuotientRing`.
- [**Rings, Fields & Exact Arithmetic**](rings_and_fields.md): Exact coefficient fields (`StandardField(Fraction)`, `ModularField`, `GaloisField`, `PAdicField`).
- [**Coalgebras, Bialgebras & Hopf Algebras**](coalgebras_and_hopf.md): Arrow-reversal duality, antipodes, and group/coordinate Hopf algebras.
- [**Invariant Theory & Molien Series**](invariant_theory.md): Polynomial group invariants feeding into GIT `syzygy_variety`.
- [**Topological K-Theory & Chern Classes**](../topology/k_theory.md): Grothendieck $K_0$ completions and topological Chern classes dual to algebraic $K_0 / K_1 / K_2^M$.
- [**Exact Matrix Solvers**](exact_matrix_solvers.md): Exact field linear algebra powering Stickelberger companion matrices and Jacobian rank tests.

### Related Recipes
- [**2R Robot Inverse Kinematics & Singularity Loci**](../../recipes.md#robot-kinematics-via-affine-algebraic-varieties): Exact kinematic workspace varieties, Stickelberger elbow-up/down root extraction, and Jacobian singularity detection (`recipes/robot_kinematics_algebraic_variety.py`).
- [**Quantum Segre Entanglement & Algebraic Statistics**](../../recipes.md#quantum-segre-entanglement-and-algebraic-statistics): Segre determinantal separability variety ($z_{00}z_{11} - z_{01}z_{10} = 0$) and Markov toric independence models (`recipes/quantum_segre_entanglement_and_algebraic_stats.py`).
