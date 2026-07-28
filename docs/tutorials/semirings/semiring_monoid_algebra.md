---
title: Monoid Algebra Semiring
description: An overview of the Monoid Algebra Semiring R[M] for formal linear combinations over generic monoids and coefficient semirings.
---

# The Monoid Algebra Semiring

The **Monoid Algebra Semiring** $R[M]$ (or Group Algebra $R[G]$) provides the foundational algebraic structure for
formal linear combinations $\sum_{m \in M} a_m m$ over an arbitrary monoid $M$ and coefficient semiring $R$.

It serves as the parent abstraction for several specialized algebraic structures in `algebrax`, including
the [Polynomial Semiring](semiring_polynomial.md) ($R[x]$) and the [Knot Semiring](semiring_knot.md)
($R[\text{Knots}]$).

## Mathematical Definition

- **Set ($S$):** Formal linear combinations of monoid elements $\sum_{m \in M} a_m m$, represented as sparse mappings
  `{monoid_element: coefficient}`.
- **Coefficient Semiring ($R$):** An underlying semiring defining coefficient addition ($\oplus$) and multiplication
  ($\otimes$).
- **Monoid Operation (`key_op`):** The associative binary operation $\cdot : M \times M \to M$ of the monoid $M$.
- **Addition ($+$):** Element-wise addition of coefficients for matching keys:
  $$\left (\sum a_m m\right) + \left (\sum b_m m\right) = \sum (a_m \oplus b_m) m$$
- **Multiplication ($\cdot$):** Cauchy product / discrete convolution using monoid multiplication and coefficient
  multiplication:
  $$\left (\sum a_m m\right) \cdot \left (\sum b_n n\right) = \sum_{m, n} (a_m \otimes b_n) (m \cdot n)$$
- **Additive Identity ($0$):** The empty mapping `{}`.
- **Multiplicative Identity ($1$):** `{zero_key: R.one}` (where `zero_key` is the monoid identity element $e \in M$).

## Implementation in `algebrax`

The `MonoidAlgebraSemiring` class is generic over both key type `K` and coefficient type `T`:

```python
from algebrax.semiring import MonoidAlgebraSemiring, StandardSemiring

# 1. Define base coefficient semiring
int_semiring = StandardSemiring(int)

# 2. Instantiate MonoidAlgebraSemiring with custom string monoid (concatenation)
string_algebra = MonoidAlgebraSemiring(
    coeff_semiring=int_semiring,
    key_op=lambda a, b: a + b,
    zero_key="",
)

# 3. Define formal linear combinations
a = {'x': 2, 'y': 3}
b = {'z': 4}

# Multiplication performs discrete convolution over key concatenation:
# (2x + 3y) * (4z) = 8xz + 12yz
res = string_algebra.mul(a, b)
# Result: {'xz': 8, 'yz': 12}
print(res)
```

## Derived Subclasses

`MonoidAlgebraSemiring` forms the theoretical foundation for specialized semirings in `algebrax`:

1. **[PolynomialSemiring](semiring_polynomial.md) ($R[x]$):**
   Monoid algebra over non-negative integer exponents $M = (\mathbb{N}_0, +)$ with `key_op = lambda x, y: x + y` and
   `zero_key = 0`.
2. **[KnotSemiring](semiring_knot.md) ($R[\text{Knots}]$):**
   Monoid algebra over topological knots $M = (\text{Knots}, \#)$ with connected sum `key_op = _combine_knots` and
   `zero_key = 'U'`.
3. **[ProvenanceSemiring](semiring_provenance.md) ($\mathbb{N}[X]$):**
   Monoid algebra over multivariate tuple monomials $M = (\text{Monomials}, \cdot)$ with sorted variable concatenation `key_op = _combine_monomials` and `zero_key = ()`.

## Use Cases

- **Group Algebras:** Constructing finite group rings $R[G]$ for representation theory and Fourier analysis.
- **Discrete Signal Processing:** Defining generalized convolution operators over arbitrary monoid domains.
- **Formal Language Theory:** Building formal power series and weighted automata over free monoids.
