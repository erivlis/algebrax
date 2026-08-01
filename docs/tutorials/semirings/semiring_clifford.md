---
title: Clifford Geometric Algebra
description: Tutorial on CliffordSemiring Cl(p, q, r) for multivectors and 3D/4D rotors.
---

# Clifford Geometric Algebra Cl(p, q, r)

The **`CliffordSemiring`** in `algebrax.clifford` implements Clifford Geometric Algebra $Cl(p, q, r)$ over `QuotientMonoidAlgebraSemiring`. Multivectors unify scalars, vectors, bivectors, and pseudoscalars into a single sparse dictionary representation `{blade_tuple: coeff}`.

---

## Geometric Product & Blade Reduction

- **Geometric Product**: $A B = A \cdot B + A \wedge B$
- **Blade Sign Flips**: $\mathbf{e}_i \mathbf{e}_j = -\mathbf{e}_j \mathbf{e}_i$ for $i \ne j$.
- **Metric Signatures**: $\mathbf{e}_i^2 = +1$ ($i \le p$), $-1$ ($p < i \le p+q$), $0$ ($i > p+q$).

---

## Python Example: 3D Spatial Vector Rotor Rotation

```python
import math
from algebrax.clifford import CliffordSemiring, rotor_rotation

# Instantiate Cl(3, 0) Semiring
cs = CliffordSemiring(p=3, q=0, r=0)

# Define 3D Vector v = 3 e1 + 4 e2
v = {(1,): 3.0, (2,): 4.0}

# Geometric Vector Squared v^2 = |v|^2 = 25.0
v_sq = cs.mul(v, v)
print("Vector Squared v^2:", v_sq)
# Output: {(): 25.0}

# Rotate v in e12 bivector plane by 90 degrees (pi/2)
v_rot = rotor_rotation(v, bivector=(1, 2), angle_rad=math.pi / 2.0, p=3, q=0, r=0)
print(f"Rotated Vector v': e1={v_rot.get((1,), 0.0):.2f}, e2={v_rot.get((2,), 0.0):.2f}")
# Output: Rotated Vector v': e1=-4.00, e2=3.00
```
