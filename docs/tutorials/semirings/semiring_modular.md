---
title: Modular Integer Ring Z_p
description: Tutorial on ModularSemiring for finite integer ring arithmetic Z_p.
---

# Modular Integer Ring $\mathbb{Z}_p$

The **`ModularSemiring`** in `algebrax.semiring` represents the modular integer ring $\mathbb{Z}_p = (\{0, 1, \dots, p-1\}, +\bmod p, \times\bmod p, 0, 1)$.

---

## Ring Operations

- **Additive Identity**: `0`
- **Multiplicative Identity**: `1 % p`
- **Addition**: $(a + b) \bmod p$
- **Multiplication**: $(a \times b) \bmod p$
- **Exponentiation**: $a^n \bmod p$

It serves as a foundational coefficient ring for finite field representations ($\text{GF}(p^m)$) and modular matrix arithmetic.

---

## Python Example

```python
from algebrax.semiring import ModularSemiring
from algebrax.matrix import dot

# Create Z_5 modular ring
z5 = ModularSemiring(p=5)

# Ring operations in Z_5
print("3 + 4 mod 5:", z5.add(3, 4))    # 2
print("3 * 4 mod 5:", z5.mul(3, 4))    # 2
print("2^4 mod 5:  ", z5.power(2, 4))  # 1

# Matrix multiplication over Z_5
A = {0: {0: 3, 1: 4}, 1: {0: 2, 1: 1}}
B = {0: {0: 2, 1: 1}, 1: {0: 4, 1: 3}}

C = dot(A, B, semiring=z5)
print("A @ B over Z_5:", C)
```
