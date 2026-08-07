---
title: Quotient Monoid Algebra Semiring
description: Tutorial on QuotientMonoidAlgebraSemiring for canonical quotient reductions over monoid algebras.
---

# The Quotient Monoid Algebra Semiring

The **`QuotientMonoidAlgebraSemiring`** is a specialized extension of the [Monoid Algebra Semiring](semiring_monoid_algebra.md) that applies a canonical quotient reduction rule `quotient_fn(key, coeff)` during multiplication.

It allows `algebrax` to compute formal multiplications in **quotient rings** $R[M] / I$ such as Clifford blade canonicalization, Galois field polynomial modulo reductions, and term rewriting systems.

---

## Mathematical Definition

- **Set ($S$):** Formal linear combinations $\sum a_m m$ represented as sparse mappings `{key: coeff}`.
- **Coefficient Semiring ($R_C$):** An underlying semiring for element coefficients (defaults to `StandardSemiring`).
- **Monoid Operator (`key_op`):** Binary multiplication function $k_1 \cdot k_2$ for keys.
- **Quotient Reduction (`quotient_fn`):** Canonical reduction mapping `(key, coeff) -> list[tuple[reduced_key, reduced_coeff]]`.

---

## Python Example: Polynomial Modulo Reduction ($x^2 = -1$)

```python
import algebrax as ax

# 1. Define key operation (addition of exponents for x^a * x^b = x^(a+b))
def key_op(exp1: int, exp2: int) -> int:
    return exp1 + exp2

# 2. Define quotient reduction modulo (x^2 + 1 = 0 => x^2 = -1)
def mod_x2_plus_1(exp: int, coeff: float) -> list[tuple[int, float]]:
    q, r = divmod(exp, 2)
    sign = -1.0 if q % 2 == 1 else 1.0
    return [(r, coeff * sign)]

# 3. Instantiate ax.semiring.QuotientMonoidAlgebraSemiring
semiring = ax.semiring.QuotientMonoidAlgebraSemiring[int, float](
    coeff_semiring=ax.semiring.StandardSemiring[float](),
    key_op=key_op,
    zero_key=0,
    quotient_fn=mod_x2_plus_1,
)

# Multiply (1 + x) * (1 + x) = 1 + 2x + x^2 mod (x^2 = -1) = 2x
p1 = {0: 1.0, 1: 1.0}
p2 = {0: 1.0, 1: 1.0}

result = semiring.mul(p1, p2)
print("Result of (1+x)^2 mod (x^2+1):", result)
# Output: {1: 2.0}
```
