---
title: Algebraic Law Verification Engine
description: Property-based testing and automated verification of semiring axioms across 34 built-in semirings.
---

# Algebraic Law Verification Engine

The **`algebrax.verification`** module provides property-based verification of formal algebraic axioms across all
built-in semiring types.

---

## Checked Semiring Axioms

| Axiom                      | Equation                                      |
|:---------------------------|:----------------------------------------------|
| **`add_associativity`**    | $(a + b) + c = a + (b + c)$                   |
| **`add_commutativity`**    | $a + b = b + a$                               |
| **`add_identity`**         | $a + \mathbf{0} = a$                          |
| **`mul_associativity`**    | $(a \cdot b) \cdot c = a \cdot (b \cdot c)$   |
| **`mul_identity`**         | $a \cdot \mathbf{1} = a$                      |
| **`left_distributivity`**  | $a \cdot (b + c) = (a \cdot b) + (a \cdot c)$ |
| **`right_distributivity`** | $(a + b) \cdot c = (a \cdot c) + (b \cdot c)$ |
| **`left_annihilation`**    | $\mathbf{0} \cdot a = \mathbf{0}$             |
| **`right_annihilation`**   | $a \cdot \mathbf{0} = \mathbf{0}$             |

### Star Semiring & Kleene Algebra Axioms

For structures implementing `StarSemiring` and `KleeneAlgebra`:

| Axiom                      | Protocol                | Equation                                      |
|:---------------------------|:------------------------|:----------------------------------------------|
| **`star_left_fixed_point`** | `StarSemiring`          | $a^* = \mathbf{1} + a \cdot a^*$              |
| **`star_right_fixed_point`**| `StarSemiring`          | $a^* = \mathbf{1} + a^* \cdot a$              |
| **`additive_idempotence`**  | `KleeneAlgebra`         | $a + a = a$                                   |

---

## Python Example: Programmatic Verification

```python
import algebrax as ax

# Programmatic verification for Tropical Semiring (a Kleene Algebra)
semiring, samples = ax.verification.get_semiring_samples('Tropical')

# 1. Verify standard semiring axioms
res_rig = ax.verification.verify_semiring_laws(semiring, samples)
for axiom, passed in res_rig.items():
    print(f'{axiom:25s}: {"PASS" if passed else "FAIL"}')

# 2. Verify star semiring fixed-point closure laws
res_star = ax.verification.verify_star_semiring_laws(semiring, samples)
for axiom, passed in res_star.items():
    print(f'{axiom:25s}: {"PASS" if passed else "FAIL"}')

# 3. Verify Kleene algebra laws (idempotence)
res_kleene = ax.verification.verify_kleene_algebra_laws(semiring, samples)
for axiom, passed in res_kleene.items():
    print(f'{axiom:25s}: {"PASS" if passed else "FAIL"}')
```

---

## CLI Audit Command

Run the law verification auditor across all 33 semirings from the terminal:

```bash
# Verify all 33 catalog semirings
python -m algebrax.verification

# Verify a single semiring
python -m algebrax.verification --semiring GaloisField
```

---

## Multi-Layered Verification Suite (`tests/verifications/`)

Beyond semiring law auditing, `algebrax` maintains a comprehensive **Multi-Layered Verification Suite** comparing linear algebra, matrix decompositions, tensors, spectral transforms, homology, and Lie algebras against **NumPy**, **SciPy**, **Hypothesis**, **Schwartz–Zippel PIT**, and **Proof-Carrying Certificates**.

See the full traceability matrix in **[Mathematical Verification & Stamp of Trust](../../verification.md)**.

