---
title: Knot Semiring
description: An overview of the Knot Semiring for algebraic operations on formal sums of knots over a generic coefficient semiring.
---

# The Knot Semiring

The **Knot Semiring** is a specialized subclass of the [Monoid Algebra Semiring](semiring_monoid_algebra.md) for working
with formal linear combinations of knots (often called a Skein Module) under the connected sum operation ($\#$). It
allows us to use the algebraic machinery of `algebrax` to reason about knots and their compositions over various
coefficient rings (like integers, real numbers, or even polynomials).

## Mathematical Definition

The Knot Semiring is defined over the set of formal sums of knots. It is parameterized by a **coefficient semiring**,
which governs the arithmetic of the coefficients.

- **Set ($S$):** Formal sums of knots, represented as dictionaries from knot identifiers (strings) to coefficients of a
  generic type `T`.
    - Example: `{'3_1': 2, '4_1': -1}` represents the formal sum $2 \cdot 3_1 - 1 \cdot 4_1$ over the integers.
- **Coefficient Semiring ($R_C$):** An underlying semiring that defines addition and multiplication for the
  coefficients. Defaults to `StandardSemiring(int)`.
- **Addition ($+$):** Formal addition of two sums. This corresponds to combining the dictionaries and using the
  coefficient semiring's addition for common knots.
- **Multiplication ($\cdot$):** The **connected sum** ($\#$) of knots, distributed over the formal addition. The
  coefficients are multiplied using the coefficient semiring's multiplication.
- **Additive Identity ($0$):** The empty set, an empty dictionary `{}`.
- **Multiplicative Identity ($1$):** The unknot, represented as `{'U': R_C.one}`, where `R_C.one` is the multiplicative
  identity of the coefficient semiring.

### Knot Representation

To handle composite knots, we use a specific string notation:

- **Prime Knots:** Identified by their standard notation (e.g., `'3_1'` for the trefoil, `'4_1'` for the figure-eight
  knot).
- **The Unknot:** Represented by the string `'U'`.
- **Composite Knots:** Formed by joining the identifiers of their prime knot components with a `#` symbol. To ensure the
  operation is commutative, the components are sorted alphabetically.
    - *Example:* The connected sum of the trefoil (`3_1`) and the figure-eight (`4_1`) is represented by the string
      `'3_1#4_1'`.

## Implementation in `algebrax`

The `KnotSemiring` is a generic class that defaults to using integer coefficients.

### Example 1: Default (Integer Coefficients)

This is the most basic case, forming a Skein module over $\mathbb{Z}$.

```python
from algebrax.semiring import KnotSemiring

# Initialize the semiring (defaults to integer coefficients)
knot_semiring = KnotSemiring()

# Define two formal sums of knots
# a = 2 * (3_1) + 1 * (4_1)
a = {'3_1': 2, '4_1': 1}

# b = 1 * (3_1) - 1 * (5_2)
b = {'3_1': 1, '5_2': -1}

# --- Operations ---

# Addition: (2*3_1 + 4_1) + (3_1 - 5_2) = 3*3_1 + 4_1 - 5_2
added = knot_semiring.add(a, b)
# Result: {'3_1': 3, '4_1': 1, '5_2': -1}
print(f"Addition over Integers: {added}")

# Multiplication (Connected Sum): (2*3_1 + 4_1) # 3_1
# = 2 * (3_1 # 3_1) + 1 * (4_1 # 3_1)
# = 2 * (3_1#3_1) + 1 * (3_1#4_1)
multiplied = knot_semiring.mul(a, {'3_1': 1})
# Result: {'3_1#3_1': 2, '3_1#4_1': 1}
print(f"Multiplication over Integers: {multiplied}")
```

### Example 2: Custom Coefficient Semiring (Real Numbers)

By passing a different semiring to the constructor, we can work with other coefficient types.

```python
from algebrax.semiring import KnotSemiring, StandardSemiring

# 1. Define the coefficient semiring (floats)
float_semiring = StandardSemiring(float)

# 2. Initialize the KnotSemiring with the float semiring
knot_semiring_float = KnotSemiring(float_semiring)

# a = 0.5 * (3_1)
a = {'3_1': 0.5}

# b = 0.5 * (3_1)
b = {'3_1': 0.5}

# Addition: 0.5*3_1 + 0.5*3_1 = 1.0*3_1
added = knot_semiring_float.add(a, b)
# Result: {'3_1': 1.0}
print(f"Addition over Floats: {added}")

# Multiplication: (0.5*3_1) # (0.5*3_1) = 0.25 * (3_1#3_1)
multiplied = knot_semiring_float.mul(a, b)
# Result: {'3_1#3_1': 0.25}
print(f"Multiplication over Floats: {multiplied}")
```

## Use Cases

The generic nature of the `KnotSemiring` allows it to model various algebraic structures in topology:

- **Skein Modules:** Using integer or polynomial coefficients to study knot invariants.
- **Quantum Topology:** Using complex coefficients to compute values of knot polynomials at roots of unity.
- **Probabilistic Models:** Using a probability semiring for coefficients to model stochastic topological processes.
