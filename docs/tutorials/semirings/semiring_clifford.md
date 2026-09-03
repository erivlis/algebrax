---
title: Clifford Geometric Algebra
description: Tutorial on CliffordSemiring Cl(p, q, r) for multivectors and 3D/4D rotors.
---

# Clifford Geometric Algebra Cl (p, q, r)

The **`CliffordSemiring`** in `algebrax.clifford` implements Clifford Geometric Algebra $Cl (p, q, r)$ over
`QuotientMonoidAlgebraSemiring`. Multivectors unify scalars, vectors, bivectors, and pseudoscalars into a single sparse
dictionary representation `{blade_tuple: coeff}`.

---

## Geometric Product & Blade Reduction

- **Geometric Product**: $A B = A \cdot B + A \wedge B$
- **Blade Sign Flips**: $\mathbf{e}_i \mathbf{e}_j = -\mathbf{e}_j \mathbf{e}_i$ for $i \ne j$.
- **Metric Signatures**: $\mathbf{e}_i^2 = +1$ ($i \le p$), $-1$ ($p < i \le p+q$), $0$ ($i > p+q$).

---

## Python Example: 3D Spatial Vector Rotor Rotation

```python
import math
import algebrax as ax

# Instantiate Cl(3, 0) ax.semiring.Semiring
cs = ax.clifford.CliffordSemiring(p=3, q=0, r=0)

# Define 3D Vector v = 3 e1 + 4 e2
v = {(1,): 3.0, (2,): 4.0}

# Geometric Vector Squared v^2 = |v|^2 = 25.0
v_sq = cs.mul(v, v)
print("Vector Squared v^2:", v_sq)
# Output: {(): 25.0}

# Rotate v in e12 bivector plane by 90 degrees (pi/2)
v_rot = ax.clifford.rotor_rotation(v, bivector=(1, 2), angle_rad=math.pi / 2.0, p=3, q=0, r=0)
print(f"Rotated Vector v': e1={v_rot.get((1,), 0.0):.2f}, e2={v_rot.get((2,), 0.0):.2f}")
# Output: Rotated Vector v': e1=-4.00, e2=3.00
```

---

## Generalized Clifford Algebras (GCAs / Clock-and-Shift)

The **`GeneralizedCliffordSemiring`** implements order-$n$ cyclic root-of-unity Clifford algebras $C_n^{ (m)}$:

- **Commutation Relation**: $\mathbf{e}_j \mathbf{e}_k = \omega \mathbf{e}_k \mathbf{e}_j$ ($j < k$)
  where $\omega = \exp\left (\frac{2\pi i}{n}\right)$.
- **Nilpotence / Periodicity**: $\mathbf{e}_j^n = \alpha_j \mathbf{1}$ (default $\alpha_j = 1$).
- **Basis Elements**: Multi-index exponent tuples $(k_1, \dots, k_m) \in \mathbb{Z}_n^m$.

```python
import cmath
import algebrax as ax

# Instantiate order n=3 GCA over m=2 generators
gca = ax.clifford.GeneralizedCliffordSemiring(n_order=3, num_generators=2)

e1 = {(1, 0): 1.0 + 0j}
e2 = {(0, 1): 1.0 + 0j}

# Multiply generators
e1_e2 = gca.mul(e1, e2)  # e1 * e2 = {(1, 1): 1.0 + 0.0j}
e2_e1 = gca.mul(e2, e1)  # e2 * e1 = {(1, 1): exp(-2*pi*i / 3)}

omega = cmath.exp(2j * cmath.pi / 3)
print("e1 * e2 == omega * e2 * e1:", cmath.isclose(e1_e2[(1, 1)] / e2_e1[(1, 1)], omega))
# Output: True
```

---

## $q$-Deformed Quantum Clifford Algebras

The **`QuantumCliffordSemiring`** implements continuous $q$-deformed braided Clifford algebras $Cl_q (m)$:

- **Braided Relation**: $\mathbf{e}_j \mathbf{e}_k = -q \mathbf{e}_k \mathbf{e}_j$ ($j < k$).
- **Quadratic Signature**: $\mathbf{e}_j^2 = \alpha_j \mathbf{1}$.

```python
import algebrax as ax

# Instantiate q=0.5 quantum Clifford algebra
qc = ax.clifford.QuantumCliffordSemiring(q=0.5, num_generators=2)

e1 = {(1, 0): 1.0 + 0j}
e2 = {(0, 1): 1.0 + 0j}

e1_e2 = qc.mul(e1, e2)  # {(1, 1): 1.0}
e2_e1 = qc.mul(e2, e1)  # {(1, 1): -0.5}

print("e2 * e1 =", e2_e1)
# Output: {(1, 1): (-0.5+0j)}
```
