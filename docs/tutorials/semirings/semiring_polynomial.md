---
title: Polynomial Semiring
description: An overview of the Polynomial Semiring for algebraic operations on univariate polynomials over a generic coefficient semiring.
---

# The Polynomial Semiring

The **Polynomial Semiring** $R[x]$ provides a generic algebraic structure for working with univariate polynomials over a
coefficient semiring $R$. It is a specialized subclass of the [Monoid Algebra Semiring](semiring_monoid_algebra.md)
where keys are non-negative integer exponents in $(\mathbb{N}_0, +)$.

It finds wide applications in discrete signal processing (as FIR filters), coding theory, and formal algebra.

## Mathematical Definition

- **Set ($S$):** Univariate polynomials, represented as sparse mappings `{exponent: coefficient}`.
    - Example: The polynomial $1 + 2x + 4x^2$ is represented as `{0: 1, 1: 2, 2: 4}`.
- **Coefficient Semiring ($R_C$):** An underlying semiring defining addition and multiplication for the coefficients.
- **Addition ($+$):** Element-wise addition of coefficients for matching exponents.
- **Multiplication ($\cdot$):** Standard polynomial multiplication, corresponding to the **discrete convolution** of
  coefficients.
- **Additive Identity ($0$):** The zero polynomial `{}`.
- **Multiplicative Identity ($1$):** `{0: R_C.one}` (constant polynomial 1).

## Implementation in `algebrax`

`PolynomialSemiring` inherits from `MonoidAlgebraSemiring[int, T]`.

### Example: Polynomials over Integers

```python
import algebrax as ax

# 1. Define the coefficient semiring (integers)
int_semiring = ax.semiring.StandardSemiring(int)

# 2. Initialize the ax.semiring.PolynomialSemiring (R[x])
poly_semiring = ax.semiring.PolynomialSemiring(int_semiring)

# p1(x) = 1 + 2x
p1 = {0: 1, 1: 2}

# p2(x) = 3 + 4x^2
p2 = {0: 3, 2: 4}

# --- Operations ---

# Addition: (1 + 2x) + (3 + 4x^2) = 4 + 2x + 4x^2
added = poly_semiring.add(p1, p2)
# Result: {0: 4, 1: 2, 2: 4}
print(f"p1 + p2 = {added}")

# Multiplication: (1 + 2x) * (3 + 4x^2) = 3 + 6x + 4x^2 + 8x^3
multiplied = poly_semiring.mul(p1, p2)
# Result: {0: 3, 1: 6, 2: 4, 3: 8}
print(f"p1 * p2 = {multiplied}")
```

## Use Cases

- **Signal Processing:** Polynomial multiplication is equivalent to discrete signal convolution, used in Finite Impulse
  Response (FIR) filters.
- **Error-Correcting Codes:** Polynomials over finite fields are fundamental to codes like Reed-Solomon.
- **Abstract Algebra:** As a building block for formal power series, quotient rings, and field extensions.

