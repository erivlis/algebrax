---
title: Lie Algebras, Root Systems & BCH Dynamics
description: Continuous symmetry generators, NonAssocAlgebra protocol conformance, structure constants, Killing forms, root systems, and Baker-Campbell-Hausdorff series.
---

# Lie Algebras, Root Systems & BCH Dynamics (`algebrax.lie`)

## 1. The Practical Problem: Infinitesimal Symmetries & Non-Commutative Motion

Continuous transformations in robotics, quantum mechanics, and gauge physics ($\operatorname{SO}(3)$ rotations, $\operatorname{SE}(3)$ rigid-body poses, $\operatorname{SU}(n)$ unitary gates) live on curved manifolds where matrices do not commute ($e^X e^Y \ne e^{X+Y}$). Their tangent space at the identity is a flat vector space equipped with a bilinear, antisymmetric, non-associative commutator bracket $[X, Y]$ satisfying the **Jacobi Identity**:
$$[X, [Y, Z]] + [Y, [Z, X]] + [Z, [X, Y]] = \mathbf{0}$$
That structure is a **Lie Algebra** $\mathfrak{g}$ — the canonical archetype of a **`NonAssocAlgebra`** in AlgebraX.

---

## 2. The 30-Second Executable Snippet

```python
from algebrax import lie
from algebrax.algebra import HasBracket, NonAssocAlgebra

# 1. Initialize 3D spin / rotation Lie algebra su(2) ~= so(3)
alg = lie.su_n(2, names=['J_x', 'J_y', 'J_z'])
assert isinstance(alg, NonAssocAlgebra) and isinstance(alg, HasBracket)

# 2. Lie bracket [J_x, J_y] = J_z (accessible via both .bracket() and .mul())
jx, jy = {'J_x': 1.0}, {'J_y': 1.0}
assert alg.to_named(alg.bracket(jx, jy)) == {'J_z': 1.0}
assert alg.to_named(alg.mul(jx, jy)) == {'J_z': 1.0}

# 3. Compound two non-commutative rotation steps via 4th-order BCH formula
z = alg.bch({'J_x': 0.05}, {'J_y': 0.05}, order=4)
assert round(alg.to_named(z)['J_z'], 6) == 0.00125
```

---

## 3. Atomic Mixins & Protocol Contract

`LieAlgebra` implements `NonAssocAlgebra[float, dict[int, float]]`, `NonAssocRing`, `Module`, `AddCommGroup`, and `HasBracket`:
- **`zero` / `add(X, Y)` / `neg(X)` / `sub(X, Y)` / `smul(r, X)`**: Vector space operations on $\mathfrak{g}$.
- **`bracket(X, Y)` & `mul(X, Y)`**: Evaluate the Lie bracket $[X, Y]_c = \sum_{a,b} f_{ab}^c X^a Y^b$.
- **Why `LieAlgebra` is NOT an `Algebra` or `Ring`**: By antisymmetry $[X, X] = \mathbf{0}$, no non-trivial Lie algebra can possess a two-sided multiplicative identity $\mathbf{1}$ satisfying $[\mathbf{1}, X] = X$, nor is the bracket associative.

### Structure Constants, Killing Form & Cartan's Semisimplicity Criterion

Given a basis $\{T_0, \dots, T_{d-1}\}$, `StructureConstants` stores $f_{ab}^c$ as a sparse 3-tensor `(a, b, c) -> val`. The **Killing form** $K_{ab} = \operatorname{Tr}(\operatorname{ad}_{T_a} \circ \operatorname{ad}_{T_b}) = \sum_{c,d} f_{ad}^c f_{bc}^d$ tests semisimplicity ($\det(K) \ne 0$):

```python
# so(3) and su(2) are semisimple (det K != 0); se(3) has an abelian translation ideal (det K == 0)
assert lie.so_n(3).is_semisimple() is True
assert lie.su_n(2).is_semisimple() is True
assert lie.se_n(3).is_semisimple() is False
```

### Root Systems, Dynkin Diagrams & Chevalley Bases

AlgebraX includes complete root system classification ($A_n, B_n, C_n, D_n, E_6, E_7, E_8, F_4, G_2$), Weyl reflection groups, Dynkin diagrams, and Chevalley–Serre Lie algebra construction:

```python
rs = lie.RootSystem.from_dynkin('A', 2)
assert len(rs.roots) == 6
chevalley_sl3 = lie.chevalley_lie_algebra(rs)
assert chevalley_sl3.dim == 8
assert chevalley_sl3.structure_constants.verify_jacobi() is True
```

---

## 4. Falsifiability: Jacobi Verification & Non-Associativity Counterexample

```python
from algebrax.semiring import StandardSemiring
from algebrax.verification import verify_non_assoc_algebra_laws

# 1. Positive verification: so(3) satisfies all NonAssocAlgebra bilinearity and additive group laws
vecs = [{}, {0: 1.0}, {1: 1.0}, {2: -1.0}]
assert all(verify_non_assoc_algebra_laws(alg, StandardSemiring(float), [0.0, 1.0, -2.0], vecs).values())
assert alg.structure_constants.verify_jacobi() is True

# 2. Counterexample to Associativity: [[J_x, J_y], J_y] = [J_z, J_y] = -J_x != [J_x, [J_y, J_y]] = 0
lhs = alg.mul(alg.mul(jx, jy), jy)
rhs = alg.mul(jx, alg.mul(jy, jy))
assert alg.to_named(lhs) == {'J_x': -1.0}
assert alg.to_named(rhs) == {}
```

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **Clifford Bivector Bridge**: Every [Clifford Geometric Algebra](clifford_geometric_algebra.md) $C\ell(p, q)$ induces a spin Lie algebra on its grade-2 bivectors via `lie.clifford_lie_algebra(p=3, q=0)`.
- **Baker–Campbell–Hausdorff (BCH) Lie Group Integrators**: Geometric ODE solvers use `alg.bch(X, Y, order=4)` to compose angular velocities in $\mathfrak{so}(3)$ and twists in $\mathfrak{se}(3)$ without leaving the Lie group manifold.
