---
title: Lie Algebras, Commutator Brackets & BCH Dynamics
description: Tutorial on continuous symmetry generators, structure constants tensors, Killing forms, and Baker-Campbell-Hausdorff series in AlgebraX.
---

# Lie Algebras, Commutator Brackets & BCH Dynamics

The `algebrax.lie` module introduces first-class representations for continuous symmetry generators and **Lie Algebras** ($\mathfrak{g}$).

A Lie algebra is a vector space equipped with an alternating bilinear bracket $[\cdot, \cdot]: \mathfrak{g} \times \mathfrak{g} \to \mathfrak{g}$ satisfying:

1. **Antisymmetry**: $[X, Y] = -[Y, X]$
2. **Jacobi Identity**: $[X, [Y, Z]] + [Y, [Z, X]] + [Z, [X, Y]] = 0$

---

## Structure Constants & Tensor Contractions

Given a basis $\{T_0, \dots, T_{d-1}\}$, the commutator relations are encoded in a rank-3 structure constants tensor $f_{ab}^c$:

$$[T_a, T_b] = \sum_{c} f_{ab}^c T_c$$

In AlgebraX, `StructureConstants` stores $f_{ab}^c$ as coordinate 3-tuples `(a, b, c) -> value`. Jacobi identity validation is executed directly via exact tensor contractions over `algebrax.tensor.einsum`:

$$\sum_k \left(f_{ab}^k f_{kc}^d + f_{bc}^k f_{ka}^d + f_{ca}^k f_{kb}^d\right) = 0$$

---

## Adjoint Representation & The Killing Form

The adjoint action maps an algebra element $X$ to the linear operator $\mathrm{ad}_X(Y) = [X, Y]$.

The **Killing form** is the canonical symmetric bilinear form:

$$B(X, Y) = \mathrm{Tr}(\mathrm{ad}_X \circ \mathrm{ad}_Y) = \sum_{a, b} X^a Y^b K_{ab}, \quad K_{ab} = \sum_{c, d} f_{ad}^c f_{bc}^d$$

### Cartan's Criterion for Semisimplicity
A Lie algebra $\mathfrak{g}$ is **semisimple** if and only if its Killing form is non-degenerate:

$$\det(K) \ne 0$$

- $\mathfrak{so}(3)$ (rotations) and $\mathfrak{sl}(2, \mathbb{R})$ are **semisimple**.
- $\mathfrak{se}(3)$ (rigid body motions with translations) is **not semisimple** ($\det K = 0$).

---

## Baker–Campbell–Hausdorff (BCH) Formula

When compounding two non-commutative group transformations $\exp(X) \exp(Y) = \exp(Z)$, the exponent $Z \in \mathfrak{g}$ is evaluated via the Baker–Campbell–Hausdorff series:

$$Z = X + Y + \frac{1}{2}[X, Y] + \frac{1}{12}[X, [X, Y]] - \frac{1}{12}[Y, [X, Y]] - \frac{1}{24}[Y, [X, [X, Y]]] + \mathcal{O}(\epsilon^5)$$

This allows geometric numerical integration and attitude control on Lie groups without numerical drift off the manifold.

---

## Python Examples

### 1. 3D Rotations $\mathfrak{so}(3)$ and Vector Cross Products

```python
import algebrax as ax
from algebrax import lie

# Initialize so(3) algebra
alg = lie.so3()
print(f"Dimension: {alg.dim}, Generators: {alg.basis_names}")
# Output: Dimension: 3, Generators: ['J_x', 'J_y', 'J_z']

# Commutator [J_x, J_y] = J_z
comm = alg.bracket({'J_x': 1.0}, {'J_y': 1.0})
print("Commutator [J_x, J_y]:", alg.to_named(comm))
# Output: {'J_z': 1.0}

# Equivalence to vector cross product u x v
u = [1.0, 0.0, 0.0]  # x-axis
v = [0.0, 1.0, 0.0]  # y-axis
cross = alg.bracket(u, v)
print("u x v:", cross)
# Output: {2: 1.0} (z-axis)
```

### 2. Semisimplicity & The Killing Metric

```python
# Check Cartan's criterion
print("Is so(3) semisimple?", alg.is_semisimple())
# Output: True

print("Killing matrix for so(3):", alg.killing_matrix())
# Output: {0: {0: -2.0}, 1: {1: -2.0}, 2: {2: -2.0}} (-2 * I_3)

# se(3) contains translations forming an abelian ideal
se3_alg = lie.se3()
print("Is se(3) semisimple?", se3_alg.is_semisimple())
# Output: False
```

### 3. Baker–Campbell–Hausdorff Time-Stepping

```python
# Small angular velocity steps in so(3)
omega_1 = {'J_x': 0.05}
omega_2 = {'J_y': 0.05}

# Compute compound step up to order 4
z = alg.bch(omega_1, omega_2, order=4)
print("Compound BCH generator step:", alg.to_named(z))
# Output: {'J_x': 0.049958..., 'J_y': 0.049958..., 'J_z': 0.00125}
```

### 4. Special Unitary Algebra $\mathfrak{su}(2)$ & Complex Matrix Generators

$\mathfrak{su}(2)$ is represented by $2 \times 2$ skew-Hermitian traceless matrices $J_k = -\frac{i}{2}\sigma_k$. It is isomorphic to $\mathfrak{so}(3)$ with real structure constants:

```python
# Initialize su(2) from complex skew-Hermitian matrices
su2_alg = lie.su2()
print(f"su(2) dim: {su2_alg.dim}, Generators: {su2_alg.basis_names}")
# Output: su(2) dim: 3, Generators: ['J_x', 'J_y', 'J_z']

# [J_x, J_y] = J_z
print("Commutator [J_x, J_y]:", su2_alg.to_named(su2_alg.bracket({'J_x': 1.0}, {'J_y': 1.0})))
# Output: {'J_z': 1.0}
print("Is su(2) semisimple?", su2_alg.is_semisimple())
# Output: True
```

### 5. Clifford Bivector Lie Algebras

```python
# Bivectors of Cl(3, 0) form an isomorphic so(3) algebra
cliff_lie = lie.clifford_lie_algebra(p=3, q=0)
print(f"Clifford Lie Algebra dim: {cliff_lie.dim}, Generators: {cliff_lie.basis_names}")
# Output: Clifford Lie Algebra dim: 3, Generators: ['e_01', 'e_02', 'e_12']
print("Jacobi identity satisfied?", cliff_lie.structure_constants.verify_jacobi())
# Output: True
```
