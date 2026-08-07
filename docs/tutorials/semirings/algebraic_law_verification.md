---
title: Algebraic Law Verification Engine
description: Property-based testing and automated verification of semiring axioms across 24 built-in semirings.
---

# Algebraic Law Verification Engine

The **`algebrax.verification`** module provides property-based verification of formal algebraic axioms across all built-in semiring types.

---

## Checked Semiring Axioms

| Axiom | Equation |
|:---|:---|
| **`add_associativity`** | $(a + b) + c = a + (b + c)$ |
| **`add_commutativity`** | $a + b = b + a$ |
| **`add_identity`** | $a + \mathbf{0} = a$ |
| **`mul_associativity`** | $(a \cdot b) \cdot c = a \cdot (b \cdot c)$ |
| **`mul_identity`** | $a \cdot \mathbf{1} = a$ |
| **`left_distributivity`** | $a \cdot (b + c) = (a \cdot b) + (a \cdot c)$ |
| **`right_distributivity`** | $(a + b) \cdot c = (a \cdot c) + (b \cdot c)$ |
| **`left_annihilation`** | $\mathbf{0} \cdot a = \mathbf{0}$ |
| **`right_annihilation`** | $a \cdot \mathbf{0} = \mathbf{0}$ |

---

## Python Example: Programmatic Verification

```python
import algebrax as ax

# Programmatic verification for Tropical ax.semiring.Semiring
semiring, samples = ax.verification.get_semiring_samples("Tropical")
results = ax.verification.verify_semiring_laws(semiring, samples)

for axiom, passed in results.items():
    print(f"{axiom:20s}: {'PASS' if passed else 'FAIL'}")
```

---

## CLI Audit Command

Run the law verification auditor across all 24 semirings from the terminal:

```bash
# Verify all 24 catalog semirings
python -m algebrax.verify

# Verify a single semiring
python -m algebrax.verify --semiring GaloisField
```
