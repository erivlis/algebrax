---
title: Clifford Geometric Algebra
description: Clifford geometric algebras Cl(p, q, r), rotor rotations, Dirac spacetime spinors, generalized clock-and-shift algebras, and q-deformed quantum Clifford algebras.
---

# Clifford Geometric Algebra (`algebrax.clifford`)

## 1. The Practical Problem: Rotations in $N$ Dimensions Without Gimbal Lock

Euler angles suffer from gimbal lock, 3D cross products $u \times v$ only exist in 3 dimensions, and quaternions only handle 3D rotations. **Clifford Geometric Algebra** $C\ell(p, q, r)$ unifies scalars, vectors, bivectors (oriented planes), and higher-grade $k$-blades into a single associative unital **`Algebra`** where the **geometric product** combines the inner dot product and exterior wedge product:
$$ab = a \cdot b + a \wedge b$$
Rotations in *any* dimension and metric signature (Euclidean 3D, Minkowski spacetime $C\ell(1, 3)$, Projective/Conformal Geometric Algebra) are executed uniformly by two-sided rotor sandwiching $v' = R v \widetilde{R}$.

---

## 2. The 30-Second Executable Snippet

```python
import math
from algebrax.algebra import Algebra
from algebrax.clifford import CliffordAlgebra, rotor_rotation

# 1. Instantiate Euclidean 3D Geometric Algebra Cl(3, 0)
cl3 = CliffordAlgebra(p=3, q=0)
assert isinstance(cl3, Algebra)

# 2. Vector v = 3 e_1 + 4 e_2; in Cl(3,0), v^2 = |v|^2 = 25.0
v = {(1,): 3.0, (2,): 4.0}
assert cl3.mul(v, v) == {(): 25.0}

# 3. Rotate v by 90 degrees (pi/2) in the e_12 plane -> -4 e_1 + 3 e_2
v_rot = rotor_rotation(v, bivector=(1, 2), angle_rad=math.pi / 2.0, p=3, q=0)
assert math.isclose(v_rot[(1,)], -4.0, abs_tol=1e-9)
assert math.isclose(v_rot[(2,)], 3.0, abs_tol=1e-9)
```

---

## 3. Atomic Mixins & Protocol Contract

`CliffordAlgebra`, `GeneralizedCliffordAlgebra`, and `QuantumCliffordAlgebra` live canonically in `algebrax.clifford` and satisfy `Algebra`, `Ring`, `Module`, and `Semiring`:

| Class (`algebrax.clifford`) | Generator Relation | Metric Signature | Primary Applications |
|:----------------------------|:-------------------|:-----------------|:---------------------|
| `CliffordAlgebra(p, q, r)` | $\mathbf{e}_i \mathbf{e}_j = -\mathbf{e}_j \mathbf{e}_i \ (i \ne j)$ | $\mathbf{e}_i^2 \in \{+1, -1, 0\}$ | 3D rotors, Spacetime Dirac spinors $C\ell(1,3)$, PGA $C\ell(3,0,1)$ |
| `GeneralizedCliffordAlgebra(n_order, num_generators)` | $\mathbf{e}_j \mathbf{e}_k = \omega \mathbf{e}_k \mathbf{e}_j \ (j < k)$ | $\omega = e^{2\pi i / n}, \ \mathbf{e}_j^n = \alpha_j \mathbf{1}$ | Weyl clock-and-shift operators, qudit Pauli groups |
| `QuantumCliffordAlgebra(q, num_generators)` | $\mathbf{e}_j \mathbf{e}_k = -q \mathbf{e}_k \mathbf{e}_j \ (j < k)$ | $\mathbf{e}_j^2 = \alpha_j \mathbf{1}$ | Braided quantum groups, $q$-deformed fermions |

### Generalized Clock-and-Shift & $q$-Deformed Examples

```python
import cmath
from algebrax.clifford import GeneralizedCliffordAlgebra, QuantumCliffordAlgebra

# Order-3 Clock-and-Shift Algebra C_3^(2)
gca = GeneralizedCliffordAlgebra(n_order=3, num_generators=2)
e1, e2 = {(1, 0): 1.0 + 0j}, {(0, 1): 1.0 + 0j}
e1_e2 = gca.mul(e1, e2)
e2_e1 = gca.mul(e2, e1)
omega = cmath.exp(2j * cmath.pi / 3)
assert cmath.isclose(e1_e2[(1, 1)] / e2_e1[(1, 1)], omega)

# q-Deformed Quantum Clifford Algebra Cl_q(2) with q = 0.5
qca = QuantumCliffordAlgebra(q=0.5, num_generators=2)
assert qca.mul(e2, e1) == {(1, 1): -0.5 + 0j}
```

---

## 4. Falsifiability: Law Verification & Non-Commutativity

```python
from algebrax.semiring import StandardSemiring
from algebrax.verification import verify_algebra_laws

# Positive verification: Cl(2, 0) satisfies all associative Algebra and Ring laws
cl2 = CliffordAlgebra(p=2, q=0)
samples = [{}, {(): 1.0}, {(1,): 1.0}, {(2,): 2.0}, {(1, 2): -1.0}]
assert all(verify_algebra_laws(cl2, StandardSemiring(float), [0.0, 1.0, -2.0], samples).values())

# Counterexample to commutativity: e_1 * e_2 = +e_12 != e_2 * e_1 = -e_12
assert cl2.mul({(1,): 1.0}, {(2,): 1.0}) == {(1, 2): 1.0}
assert cl2.mul({(2,): 1.0}, {(1,): 1.0}) == {(1, 2): -1.0}
assert cl2.sub({(1,): 2.0}, {(1,): 2.0}) == {}
```

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **Bivector Lie Algebras ($\mathfrak{spin}(p, q)$)**: Under the commutator bracket $[A, B] = \frac{1}{2}(AB - BA)$, the grade-2 bivectors of $C\ell(p, q)$ form a closed [Lie Algebra](lie_algebras.md) (`lie.clifford_lie_algebra(p, q)`), generating the Spin group double cover of $\operatorname{SO}(p, q)$.
- **Spacetime Algebra (STA)**: Setting `CliffordAlgebra(p=1, q=3)` yields the Dirac gamma algebra $\gamma_\mu \gamma_\nu + \gamma_\nu \gamma_\mu = 2\eta_{\mu\nu}$, unifying electric and magnetic fields into a single Faraday bivector $F = \mathbf{E} + I\mathbf{B}$.
