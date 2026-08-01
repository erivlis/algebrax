---
title: "EP-0111: Clifford Geometric Algebra & Multivector Rotors"
description: "Multivectors over Cl(p, q, r), blade quotient rules, 3D/4D rotors, and spacetime algebra."
icon: lucide/orbit
status: draft
---

# EP-0111: Clifford Geometric Algebra & Multivector Rotors

| Field       | Value                    |
|:------------|:-------------------------|
| **EP**      | 0111                     |
| **Title**   | Clifford Geometric Algebra & Multivector Rotors |
| **Author**  | Eran Rivlis & Antigravity |
| **Status**  | Draft                    |
| **Type**    | Standards Track          |
| **Created** | 2026-08-01               |
| **Updated** | 2026-08-01               |

## Abstract

This proposal specifies `algebrax.clifford`, building upon `QuotientMonoidAlgebraSemiring` (`EP-0100`). It implements **Clifford / Geometric Algebra** $Cl(p, q, r)$ as a quotient algebra semiring, representing multivectors as sparse mappings `{blade_tuple: coeff}`, geometric products $A B = A \cdot B + A \wedge B$, outer wedge products $\wedge$, and rotor spatial rotations in $3\text{D} / 4\text{D}$.

---

## Deliverables

1. **Core Implementation**: `src/algebrax/clifford.py` (`CliffordSemiring`, `geometric_product`, `outer_product`, `rotor_rotation`).
2. **Unit Tests**: `tests/algebrax/test_clifford.py` (verifying blade multiplication, rotor rotations, and $Cl(3,0)$ quaternion isomorphism).
3. **Use Case Recipe**: `recipes/clifford_rotor_kinematics.py` & `.ipynb`.
4. **Graphical Laboratory View**: View 22 (`view_clifford_geometric_algebra_group`) in `recipes/lab.py`.
