---
title: Monoid & Extension Algebras
description: Monoid algebras, polynomial rings, provenance, knots, quotient rings, Clifford algebras, and Galois fields.
---

# Monoid & Extension Algebras (`algebrax.semiring.algebraic`)

The algebraic semirings implement formal linear combinations $R[M]$ over monoids, universal polynomial quotients,
multivector Clifford algebras, and finite Galois fields.

---

# The Monoid Algebra Semiring

The **Monoid Algebra Semiring** $R[M]$ (or Group Algebra $R[G]$) provides the foundational algebraic structure for
formal linear combinations $\sum_{m \in M} a_m m$ over an arbitrary monoid $M$ and coefficient semiring $R$.

It serves as the parent abstraction for several specialized algebraic structures in `algebrax`, including
the [Polynomial Semiring] ($R[x]$) and the [Knot Semiring]
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
import algebrax as ax

# 1. Define base coefficient semiring
int_semiring = ax.semiring.StandardSemiring(int)

# 2. Instantiate ax.semiring.MonoidAlgebraSemiring with custom string monoid (concatenation)
string_algebra = ax.semiring.MonoidAlgebraSemiring(
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

1. **[PolynomialSemiring] ($R[x]$):**
   Monoid algebra over non-negative integer exponents $M = (\mathbb{N}_0, +)$ with `key_op = lambda x, y: x + y` and
   `zero_key = 0`.
2. **[KnotSemiring] ($R[\text{Knots}]$):**
   Monoid algebra over topological knots $M = (\text{Knots}, \#)$ with connected sum `key_op = _combine_knots` and
   `zero_key = 'U'`.
3. **[ProvenanceSemiring] ($\mathbb{N}[X]$):**
   Monoid algebra over multivariate tuple monomials $M = (\text{Monomials}, \cdot)$ with sorted variable concatenation `key_op = _combine_monomials` and `zero_key = ()`.

## Use Cases

- **Group Algebras:** Constructing finite group rings $R[G]$ for representation theory and Fourier analysis.
- **Discrete Signal Processing:** Defining generalized convolution operators over arbitrary monoid domains.
- **Formal Language Theory:** Building formal power series and weighted automata over free monoids.

---

# The Quotient Monoid Algebra Semiring

The **`QuotientMonoidAlgebraSemiring`** is a specialized extension of
the [Monoid Algebra Semiring] that applies a canonical quotient reduction rule
`quotient_fn(key, coeff)` during multiplication.

It allows `algebrax` to compute formal multiplications in **quotient rings** $R[M] / I$ such as Clifford blade
canonicalization, Galois field polynomial modulo reductions, and term rewriting systems.

---

## Mathematical Definition

- **Set ($S$):** Formal linear combinations $\sum a_m m$ represented as sparse mappings `{key: coeff}`.
- **Coefficient Semiring ($R_C$):** An underlying semiring for element coefficients (defaults to `StandardSemiring`).
- **Monoid Operator (`key_op`):** Binary multiplication function $k_1 \cdot k_2$ for keys.
- **Quotient Reduction (`quotient_fn`):** Canonical reduction mapping
  `(key, coeff) -> list[tuple[reduced_key, reduced_coeff]]`.

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

---

# The Polynomial Semiring

The **Polynomial Semiring** $R[x]$ provides a generic algebraic structure for working with univariate polynomials over a
coefficient semiring $R$. It is a specialized subclass of the [Monoid Algebra Semiring]
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

---

# Provenance Semiring (History Tracking)

The **Provenance Semiring** ($\mathbb{N}[X]$) is a specialized subclass of the [Monoid Algebra Semiring] that tracks *which* facts contributed to a result and *how many times*.
Values are multivariate polynomials represented as mappings from sorted variable tuples (monomials) to occurrence counts in $\mathbb{N}$.

<!-- name: test_provenance_semiring -->

```python linenums="1"
import algebrax as ax

# Graph with labeled edges
# 0 -> 1 (label 'x')
# 1 -> 2 (label 'y')
# 0 -> 2 (label 'z')
graph = {
    0: {1: {('x',): 1}, 2: {('z',): 1}},
    1: {2: {('y',): 1}}
}

# Paths of length 2
# 0->1->2: x * y = xy
# 0->2: (length 1, not in result)
paths_len_2 = ax.matrix.dot(graph, graph, semiring=ax.semiring.ProvenanceSemiring())

print(paths_len_2[0][2])
# output: {('x', 'y'): 1}
```

---

# The Knot Semiring

The **Knot Semiring** is a specialized subclass of the [Monoid Algebra Semiring] for working
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
import algebrax as ax

# Initialize the semiring (defaults to integer coefficients)
knot_semiring = ax.semiring.KnotSemiring()

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
import algebrax as ax

# 1. Define the coefficient semiring (floats)
float_semiring = ax.semiring.StandardSemiring(float)

# 2. Initialize the ax.semiring.KnotSemiring with the float semiring
knot_semiring_float = ax.semiring.KnotSemiring(float_semiring)

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

---

# Clifford Geometric Algebra Cl (p, q, r)

The **`CliffordSemiring`** in `algebrax.clifford` implements Clifford Geometric Algebra $Cl (p, q, r)$ over
`QuotientMonoidAlgebraSemiring`. Multivectors unify scalars, vectors, bivectors, and pseudoscalars into a single sparse
dictionary representation `{blade_tuple: coeff}`.

---

## Geometric Product & Blade Reduction

- **Geometric Product**: $A B = A \cdot B + A \wedge B$
- **Blade Sign Flips**: $\mathbf{e}_i \mathbf{e}_j = -\mathbf{e}_j \mathbf{e}_i$ for $i \ne j$.
- **Metric Signatures**: $\mathbf{e}_i^2 = +1$ ($i \le p$), $-1$ ($p < i \le p+q$), $0$ ($i > p+q$).

---

## Python Example: 3D Spatial Vector Rotor Rotation

```python
import math
import algebrax as ax

# Instantiate Cl(3, 0) ax.semiring.Semiring
cs = ax.clifford.CliffordSemiring(p=3, q=0, r=0)

# Define 3D Vector v = 3 e1 + 4 e2
v = {(1,): 3.0, (2,): 4.0}

# Geometric Vector Squared v^2 = |v|^2 = 25.0
v_sq = cs.mul(v, v)
print("Vector Squared v^2:", v_sq)
# Output: {(): 25.0}

# Rotate v in e12 bivector plane by 90 degrees (pi/2)
v_rot = ax.clifford.rotor_rotation(v, bivector=(1, 2), angle_rad=math.pi / 2.0, p=3, q=0, r=0)
print(f"Rotated Vector v': e1={v_rot.get((1,), 0.0):.2f}, e2={v_rot.get((2,), 0.0):.2f}")
# Output: Rotated Vector v': e1=-4.00, e2=3.00
```

---

## Generalized Clifford Algebras (GCAs / Clock-and-Shift)

The **`GeneralizedCliffordSemiring`** implements order-$n$ cyclic root-of-unity Clifford algebras $C_n^{ (m)}$:

- **Commutation Relation**: $\mathbf{e}_j \mathbf{e}_k = \omega \mathbf{e}_k \mathbf{e}_j$ ($j < k$)
  where $\omega = \exp\left (\frac{2\pi i}{n}\right)$.
- **Nilpotence / Periodicity**: $\mathbf{e}_j^n = \alpha_j \mathbf{1}$ (default $\alpha_j = 1$).
- **Basis Elements**: Multi-index exponent tuples $(k_1, \dots, k_m) \in \mathbb{Z}_n^m$.

```python
import cmath
import algebrax as ax

# Instantiate order n=3 GCA over m=2 generators
gca = ax.clifford.GeneralizedCliffordSemiring(n_order=3, num_generators=2)

e1 = {(1, 0): 1.0 + 0j}
e2 = {(0, 1): 1.0 + 0j}

# Multiply generators
e1_e2 = gca.mul(e1, e2)  # e1 * e2 = {(1, 1): 1.0 + 0.0j}
e2_e1 = gca.mul(e2, e1)  # e2 * e1 = {(1, 1): exp(-2*pi*i / 3)}

omega = cmath.exp(2j * cmath.pi / 3)
print("e1 * e2 == omega * e2 * e1:", cmath.isclose(e1_e2[(1, 1)] / e2_e1[(1, 1)], omega))
# Output: True
```

---

## $q$-Deformed Quantum Clifford Algebras

The **`QuantumCliffordSemiring`** implements continuous $q$-deformed braided Clifford algebras $Cl_q (m)$:

- **Braided Relation**: $\mathbf{e}_j \mathbf{e}_k = -q \mathbf{e}_k \mathbf{e}_j$ ($j < k$).
- **Quadratic Signature**: $\mathbf{e}_j^2 = \alpha_j \mathbf{1}$.

```python
import algebrax as ax

# Instantiate q=0.5 quantum Clifford algebra
qc = ax.clifford.QuantumCliffordSemiring(q=0.5, num_generators=2)

e1 = {(1, 0): 1.0 + 0j}
e2 = {(0, 1): 1.0 + 0j}

e1_e2 = qc.mul(e1, e2)  # {(1, 1): 1.0}
e2_e1 = qc.mul(e2, e1)  # {(1, 1): -0.5}

print("e2 * e1 =", e2_e1)
# Output: {(1, 1): (-0.5+0j)}
```

---

# Galois Finite Field Semiring GF(p^m)

The **`GaloisFieldSemiring`** in `algebrax.galois` enables matrix linear algebra over finite fields $\text{GF}(p^m)$ by representing field elements as sparse polynomial vectors `{exponent: coeff}` modulo an irreducible polynomial $P(x)$.

---

## Field Arithmetic

- **Addition**: Polynomial addition modulo prime characteristic $p$.
- **Multiplication**: Polynomial multiplication in $\mathbb{F}_p[x]$ reduced by long division modulo $P(x)$ (e.g. $x^8 + x^4 + x^3 + x + 1$ for AES $\text{GF}(2^8)$).

---

## Python Example: AES GF(2^8) MixColumns Matrix Multiplication

```python
import algebrax as ax

# Instantiate AES GF(2^8) ax.semiring.Semiring
gf = ax.galois.GaloisFieldSemiring(p=2, irreduc_poly=(1, 1, 0, 1, 1, 0, 0, 0, 1))

# Element multiplication: x^4 * x^4 = x^8 mod P(x) = x^4 + x^3 + x + 1
res_poly = gf.mul({4: 1}, {4: 1})
print("x^4 * x^4 mod P(x) in GF(2^8):", res_poly)
# Output: {0: 1, 1: 1, 3: 1, 4: 1}

# Sparse Matrix Multiplication over GF(2^8)
mix_col = {
    0: {0: {1: 1}, 1: {0: 1}},
    1: {0: {0: 1}, 1: {1: 1}},
}
state = {
    0: {0: {4: 1}},
    1: {0: {2: 1}},
}

out_state = ax.galois.gf_matrix_mul(mix_col, state, p=2)
print("Transformed AES State:", out_state)
```

---

## Related Recipes & Applications

* [Algebraic Knot Theory](../../recipes.md) — Connected sums and Jones polynomials via `KnotSemiring`.
* [Relativistic Dirac Spinors](../../recipes.md) — Spacetime physics via `CliffordSemiring(p=1, q=3)`.
* [Galois Finite Field Cryptography](../../recipes.md) — AES MixColumns via `GaloisFieldSemiring`.
