---
title: Invariant Theory, Molien Series & Casimir Polynomials
description: Exact Hilbert–Poincaré Molien series, polynomial Reynolds symmetrization, homogeneous invariant ring bases, and cubic Lie Casimir invariants in AlgebraX.
icon: lucide/sigma
---

# Invariant Theory, Molien Series & Casimir Polynomials

> **Intuition (Noether & Feynman):** *Whenever a physical system or geometric space possesses a symmetry group $G$, the physically meaningful observables are precisely the polynomials $f(\mathbf{x})$ that remain untouched when every symmetry $g \in G$ acts on the coordinates: $f(\rho(g)\mathbf{x}) = f(\mathbf{x})$. Molien's theorem counts how many independent observables exist at every degree before you compute a single one, and the Reynolds operator projects any polynomial straight onto the invariant ring.*

Given a finite-dimensional representation $\rho : G \to \mathrm{GL}(V)$, the **invariant polynomial ring** is the graded subalgebra

$$K[V]^G = \bigoplus_{d=0}^{\infty} K[V]_d^G, \qquad K[V]_d^G = \bigl\{\, f \in K[V]_d \;\big|\; f(\rho(g)\mathbf{x}) = f(\mathbf{x}) \;\forall\, g \in G \,\bigr\}$$

AlgebraX implements polynomial invariant theory in `algebrax.rep.invariant` and higher-order Lie Casimir invariants in `algebrax.rep.lie` (with convenient top-level re-exports in `algebrax.rep` and lazy re-exports in `algebrax.lie`).

---

## 1. Molien's Theorem & Exact Rational Generating Functions

By **Molien's Theorem** (1897), the Hilbert–Poincaré generating function of the graded invariant dimensions $m_d = \dim K[V]_d^G$ is the group average of reciprocal characteristic polynomials:

$$M(t) = \sum_{d=0}^{\infty} \dim\!\bigl(K[V]_d^G\bigr)\, t^d = \frac{1}{|G|} \sum_{g \in G} \frac{1}{\det(\mathbf{I}_n - t\rho(g))} = \frac{P(t)}{\prod_{i=1}^n (1 - t^{d_i})}$$

AlgebraX's `compute_molien_series` evaluates $\det(\mathbf{I}_n - t\rho(g))$ using a pure-Python sparse Faddeev–LeVerrier algorithm, reconstructs the exact integer rational function over $\mathbb{Z}[t]$ via cyclotomic cancellation, and packs the denominator into Cohen–Macaulay primary degrees $(d_1, \dots, d_n)$ with a non-negative secondary numerator $P(t)$:

| Group $G$ | Representation $V$ | Exact Molien Series $M(t)$ | Invariant Ring Structure |
| :--- | :--- | :--- | :--- |
| Klein four-group $V_4 \cong D_4$ | 2D real $\mathbb{R}^2$ | $\dfrac{1}{(1 - t^2)^2}$ | Free polynomial ring $\mathbb{R}[x^2, y^2]$ |
| Dihedral $D_8$ | 2D real $\mathbb{R}^2$ | $\dfrac{1}{(1 - t^2)(1 - t^4)}$ | Reflection group (Chevalley–Shephard–Todd): $\mathbb{R}[x^2 + y^2, x^2 y^2]$ |
| Symmetric $S_3$ | 3D defining $\mathbb{R}^3$ | $\dfrac{1}{(1 - t)(1 - t^2)(1 - t^3)}$ | Elementary symmetric polynomials $e_1, e_2, e_3$ |
| Quaternion $Q_8 \subset \mathrm{SU}(2)$ | 2D complex $\mathbb{C}^2$ | $\dfrac{1 + t^6}{(1 - t^4)^2}$ | Kleinian $D_4$ surface singularity (2 primary deg-4, 1 secondary deg-6) |
| Icosahedral $A_5 \subset \mathrm{SO}(3)$ | 3D rotations $\mathbb{R}^3$ | $\dfrac{1 + t^{15}}{(1 - t^2)(1 - t^6)(1 - t^{10})}$ | Klein's icosahedral invariants (primary deg 2, 6, 10; secondary deg 15) |

Once constructed, `MolienSeries.series(max_degree)` expands $m_0, \dots, m_{\text{max\_degree}}$ via exact arbitrary-precision integer dynamic programming with zero floating-point drift:

```python
import math
from algebrax.group import dihedral_group, quaternion_group, symmetric_group
from algebrax.rep import (
    compute_molien_series,
    dihedral_rep,
    quaternion_rep,
    symmetric_defining_rep,
)

# 1. Reflection group D_8 on R^2 -> 1 / ((1 - t^2)(1 - t^4))
m_d8 = compute_molien_series(dihedral_rep(4), dihedral_group(4))
assert m_d8.numerator_coeffs == (1,)
assert m_d8.denominator_factors == (2, 4)
assert m_d8.series(8) == [1, 0, 1, 0, 2, 0, 2, 0, 3]

# 2. Symmetric group S_3 defining rep -> 1 / ((1 - t)(1 - t^2)(1 - t^3))
m_s3 = compute_molien_series(symmetric_defining_rep(3), symmetric_group(3))
assert m_s3.numerator_coeffs == (1,)
assert m_s3.denominator_factors == (1, 2, 3)
assert m_s3.series(6) == [1, 1, 2, 3, 4, 5, 7]

# 3. Quaternion group Q_8 on C^2 (Kleinian D_4 singularity) -> (1 + t^6) / (1 - t^4)^2
m_q8 = compute_molien_series(quaternion_rep(), quaternion_group())
assert m_q8.numerator_coeffs == (1, 0, 0, 0, 0, 0, 1)
assert m_q8.denominator_factors == (4, 4)
assert m_q8.series(12) == [1, 0, 0, 0, 2, 0, 1, 0, 3, 0, 2, 0, 4]
assert math.isclose(m_q8.evaluate(0.5), (1.0 + 0.5**6) / (1.0 - 0.5**4) ** 2, rel_tol=1e-12)
```

---

## 2. Polynomial Reynolds Projection & Homogeneous Invariant Bases

While `reynolds_average` in `algebrax.rep.group` projects linear operators onto intertwiner spaces, **polynomial invariant theory** acts on scalar functions $f : V \to K$ via the **polynomial Reynolds operator**:

$$\mathcal{R}(f)(\mathbf{x}) = \frac{1}{|G|} \sum_{g \in G} f\!\bigl(\rho(g^{-1})\mathbf{x}\bigr)$$

The operator $\mathcal{R}$ is an exact idempotent projection ($\mathcal{R}^2 = \mathcal{R}$) from $K[V]$ onto $K[V]^G$. Because AlgebraX uses exact group inversion `group.inv(g)` (or full closed-group summation without assuming orthogonality), $\mathcal{R}$ remains exact even for non-orthogonal, similarity-conjugated representations $S\rho(g)S^{-1}$.

AlgebraX provides three complementary entry points:

- **`reynolds_polynomial_operator(poly_eval, rep, elements_or_group)`**: Wraps any Python callable `f(x)` into its $G$-invariant projection $\mathcal{R}(f)(\mathbf{x})$.
- **`reynolds_monomial_projection(exponents, rep, elements_or_group)`**: Symbolically expands $\mathcal{R}(\mathbf{x}^\alpha)$ into an unboxed sparse multivariate polynomial `dict[tuple[int, ...], float | complex]`.
- **`invariant_basis_at_degree(rep, elements_or_group, degree)`**: Projects every homogeneous degree-$d$ monomial and extracts a canonical reduced row-echelon basis of $K[V]_d^G$.

```python
from algebrax.group import dihedral_group, quaternion_group
from algebrax.rep import (
    compute_molien_series,
    dihedral_rep,
    evaluate_sparse_polynomial,
    invariant_basis_at_degree,
    quaternion_rep,
    reynolds_monomial_projection,
    reynolds_polynomial_operator,
)
from algebrax.verification import (
    verify_molien_expansion,
    verify_polynomial_invariance,
    verify_reynolds_idempotency,
)

# 1. Functional Reynolds symmetrization on D_8
d8 = dihedral_group(4)
rho_d8 = dihedral_rep(4)
raw_poly = lambda x: x[0] ** 4 + 3.0 * x[0] ** 2 * x[1] - x[1] ** 2  # noqa: E731
inv_poly = reynolds_polynomial_operator(raw_poly, rho_d8, d8)

assert all(verify_reynolds_idempotency(lambda f: reynolds_polynomial_operator(f, rho_d8, d8), raw_poly, [1.2, -0.8]).values())
assert all(verify_polynomial_invariance(inv_poly, rho_d8, d8, num_probes=30).values())

# 2. Symbolic homogeneous invariant bases for Q_8 matching Molien's theorem through degree 8
q8 = quaternion_group()
rho_q8 = quaternion_rep()
molien_q8 = compute_molien_series(rho_q8, q8)

empirical_dims = []
for deg in range(9):
    basis = invariant_basis_at_degree(rho_q8, q8, deg)
    empirical_dims.append(len(basis))
    for poly in basis:
        assert all(verify_polynomial_invariance(poly, rho_q8, q8, num_probes=20).values())

# Empirical dimensions [1, 0, 0, 0, 2, 0, 1, 0, 3] match (1 + t^6) / (1 - t^4)^2 identically
assert all(verify_molien_expansion(molien_q8, empirical_dims).values())

# Degree-4 invariant projection of x^4 under Q_8 evaluates cleanly on any coordinate vector
deg4_proj = reynolds_monomial_projection((4, 0), rho_q8, q8)
assert len(deg4_proj) > 0
assert abs(evaluate_sparse_polynomial(deg4_proj, [1.0, 0.0])) > 0.0
```

---

## 3. Higher-Order Lie Casimir Invariants ($C_3$ & $d_{ijk}$)

For continuous symmetries modeled by a semisimple Lie algebra $\mathfrak{g}$ of rank $r$, Chevalley's theorem guarantees $r$ algebraically independent polynomial invariants generating the center $Z(\mathcal{U}(\mathfrak{g}))$ of the universal enveloping algebra.

- For rank-1 algebras ($\mathfrak{su}(2), \mathfrak{so}(3), \mathfrak{sl}(2)$), the **quadratic Casimir** $C_2$ alone uniquely classifies every irreducible representation.
- For rank-2 algebras of type $A_2$ ($\mathfrak{sl}(3), \mathfrak{su}(3)$), the quadratic Casimir $C_2$ assigns the **exact same scalar eigenvalue** to the fundamental triplet $\mathbf{3}$ (quarks) and its contragredient dual $\bar{\mathbf{3}}$ (antiquarks)! Separating conjugate representations requires the **cubic Casimir invariant**:

$$d_{ijk} = \operatorname{Tr}\!\bigl(\rho(X_i)\{\rho(X_j), \rho(X_k)\}\bigr), \qquad C_3 = \sum_{i,j,k} d^{ijk} \rho(X_i)\rho(X_j)\rho(X_k)$$

where $d^{ijk} = g^{ia} g^{jb} g^{kc} d_{abc}$ raises indices via the inverse Killing metric $g^{ij} = (B^{-1})^{ij}$.

> **Mathematical Note (Self-Dual Representations):** Because the adjoint representation of any semisimple Lie algebra is self-dual, $\operatorname{Tr}(\mathrm{ad}_i \{\mathrm{ad}_j, \mathrm{ad}_k\}) \equiv 0$ identically. Consequently, `cubic_casimir_tensor(algebra)` defaults to `defining_representation(algebra)` whenever `algebra.matrix_basis` is present so that type-$A_n$ ($n \ge 3$) cubic invariants are non-vanishing by default.

```python
from algebrax.lie import sl_n, su_n
from algebrax.rep.lie import (
    adjoint_representation,
    cubic_casimir_operator,
    cubic_casimir_tensor,
    defining_representation,
    quadratic_casimir,
)
from algebrax.verification import verify_cubic_casimir_invariance

# 1. Compute totally symmetric ad-invariant cubic tensor d_{ijk} for sl(3)
alg = sl_n(3)
d_tensor = cubic_casimir_tensor(alg)
assert len(d_tensor) == 42
assert all(verify_cubic_casimir_invariance(alg, d_tensor=d_tensor).values())

fund = defining_representation(alg)   # 3
dual = fund.dual()                    # 3-bar
adj = adjoint_representation(alg)     # 8 (self-dual)

# Quadratic Casimir cannot distinguish 3 from 3-bar
c2_fund = quadratic_casimir(fund)
c2_dual = quadratic_casimir(dual)
assert abs(c2_fund[0][0] - c2_dual[0][0]) <= 1e-9

# Cubic Casimir acts as opposite non-zero scalars (+lam3 vs -lam3) on 3 vs 3-bar, and 0 on 8!
c3_fund = cubic_casimir_operator(fund, d_tensor=d_tensor)
c3_dual = cubic_casimir_operator(dual, d_tensor=d_tensor)
c3_adj = cubic_casimir_operator(adj, d_tensor=d_tensor)

lam3_fund = complex(c3_fund[0][0])
lam3_dual = complex(c3_dual[0][0])
assert abs(lam3_fund) > 1e-6
assert abs(lam3_fund + lam3_dual) <= 1e-9
assert c3_adj == {}

# 2. Rank-1 su(2) has no cubic Casimir invariant (d_{ijk} == 0 identically)
assert cubic_casimir_tensor(su_n(2)) == {}
```

---

## 4. Automated Verification & Falsification

`algebrax.verification` provides four falsifiable predicates for polynomial and Casimir invariants:

- **`verify_reynolds_idempotency(reynolds_fn, test_poly, test_point)`**: Confirms $\mathcal{R}(\mathcal{R}(f))(\mathbf{x}) = \mathcal{R}(f)(\mathbf{x})$ with finite scalar outputs.
- **`verify_polynomial_invariance(poly, rep, elements_or_group, dimension=None, num_probes=50, seed=42)`**: Checks $f(\rho(g)\mathbf{x}) = f(\mathbf{x})$ across deterministic Gaussian probes and every $g \in G$ for both callables and unboxed sparse polynomials.
- **`verify_molien_expansion(series, actual_dimensions)`**: Cross-checks exact `MolienSeries` Taylor coefficients against empirical homogeneous invariant basis dimensions.
- **`verify_cubic_casimir_invariance(algebra, d_tensor=None, rep=None)`**: Checks $S_3$ total symmetry $d_{\sigma(i)\sigma(j)\sigma(k)} = d_{ijk}$ and Lie-algebra $\mathrm{ad}$-invariance $\sum_l (f_{ai}^l d_{ljk} + f_{aj}^l d_{ilk} + f_{ak}^l d_{ijl}) = 0$.

See also [Group Representations & Character Tables](representations.md), [Induced Representations, Frobenius Reciprocity & Mackey Theory](induced_representations.md), [Lie Algebra Representations, Weights & Clebsch–Gordan Tensors](lie_representations.md), and [Affine Varieties, Coordinate Rings & Stickelberger Solvers](varieties_and_geometry.md) (`syzygy_variety` for GIT invariant relations).
