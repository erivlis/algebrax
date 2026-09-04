---
title: Arithmetic Semirings
description: Standard and Modular arithmetic semirings in AlgebraX.
---

# Arithmetic Semirings (`algebrax.semiring.arithmetic`)

The arithmetic semirings provide classical numerical and discrete modulo fields:

1. **`StandardSemiring[T]`**: Classical arithmetic $(+, \cdot, 0, 1)$ over numeric types (`float`, `int`, `complex`, or custom rings).
2. **`ModularSemiring`**: Integer arithmetic modulo $n$ $(\mathbb{Z}_n, +_n, \times_n, 0, 1)$.

---

# Standard Semiring (Linear Algebra)

The default semiring uses standard arithmetic ($+, \times$).

<!-- name: test_standard_semiring -->

```python linenums="1"
import algebrax as ax

# Sparse Matrices
A = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
B = {0: {0: 5, 1: 6}, 1: {0: 7, 1: 8}}

# Standard Matrix Multiplication
C = ax.matrix.dot(A, B, semiring=ax.semiring.StandardSemiring())
print(C)
# output: {0: {0: 19.0, 1: 22.0}, 1: {0: 43.0, 1: 50.0}}
```

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
import algebrax as ax

# Create Z_5 modular ring
z5 = ax.semiring.ModularSemiring(p=5)

# Ring operations in Z_5
print("3 + 4 mod 5:", z5.add(3, 4))    # 2
print("3 * 4 mod 5:", z5.mul(3, 4))    # 2
print("2^4 mod 5:  ", z5.power(2, 4))  # 1

# Matrix multiplication over Z_5
A = {0: {0: 3, 1: 4}, 1: {0: 2, 1: 1}}
B = {0: {0: 2, 1: 1}, 1: {0: 4, 1: 3}}

C = ax.matrix.dot(A, B, semiring=z5)
print("A @ B over Z_5:", C)
```

---

## Related Recipes & Applications

* [Forward-Mode Automatic Differentiation](../../recipes.md) — Polymorphic `StandardSemiring(dtype=DualNumber)`.
* [Quantum Feynman Path Integrals](../../recipes.md) — Complex amplitude wave propagation via `StandardSemiring(dtype=complex)`.
* [Combinatorial Dyck Paths & Catalan Numbers](../../recipes.md) — Exact lattice walk counting via `StandardSemiring`.
