---
title: Polynomials, Dual Numbers & Quotient Monoid Algebras
description: Formal monoid algebras R[M], quotient monoid algebras R[M]/I, univariate polynomial algebras R[x], and dual number automatic differentiation algebras.
---

# Polynomials, Dual Numbers & Quotient Monoid Algebras (`algebrax.algebra`)

## 1. The Practical Problem: Symbolic Convolution & Infinitesimal Jets

Many domains require computing with **formal linear combinations** $\sum_{m \in M} c_m m$ over a monoid of basis keys $M$:
- When $M = (\mathbb{N}_0, +)$, linear combinations are **univariate polynomials** $R[x]$ and multiplication is discrete Cauchy convolution.
- When $M = \mathbb{R}[\varepsilon] / (\varepsilon^2)$, elements $a + b\varepsilon$ are **dual numbers** that compute exact 1st-order derivatives alongside function evaluation (forward-mode automatic differentiation).
- When a free monoid algebra $R[M]$ is reduced modulo an ideal of relations $I$ (such as $x^2 + 1 = 0$ or Clifford blade anticommutation), it forms a **Quotient Monoid Algebra** $R[M]/I$.

In AlgebraX, when the coefficient domain is a commutative ring, `PolynomialAlgebra` and `DualNumberAlgebra` implement the full `Algebra`, `CommRing`, `Ring`, `Module`, and `Semiring` protocols simultaneously.

---

## 2. The 30-Second Executable Snippet

```python
from algebrax.algebra import (
    Algebra,
    CommRing,
    DualNumberAlgebra,
    MonoidAlgebra,
    PolynomialAlgebra,
    QuotientMonoidAlgebra,
)
from algebrax.semiring import StandardSemiring

# 1. PolynomialAlgebra (subclass of MonoidAlgebra) over integers Z[x]: (1 + 2x) - (1 - 3x) = 5x
poly = PolynomialAlgebra(StandardSemiring(int))
assert isinstance(poly, MonoidAlgebra) and isinstance(poly, Algebra) and isinstance(poly, CommRing)
p1 = {0: 1, 1: 2}
p2 = {0: 1, 1: -3}
assert poly.sub(p1, p2) == {1: 5}
assert poly.smul(3, p1) == {0: 3, 1: 6}

# 2. DualNumberAlgebra R[ε]/(ε²): exact derivative of f(x) = x² - 3x at x = 4.0
# f'(4.0) = 2(4.0) - 3 = 5.0
dual = DualNumberAlgebra()
x = (4.0, 1.0)  # 4.0 + 1.0ε
fx = dual.sub(dual.mul(x, x), dual.smul(3.0, x))
assert fx == (4.0, 5.0)
```

---

## 3. Atomic Mixins & Protocol Contracts

| Class (`algebrax.algebra`) | Carrier Type | Satisfied Protocols | Algebraic Signature |
|:---------------------------|:-------------|:--------------------|:--------------------|
| `MonoidAlgebraSemiring[K, T]` | `dict[K, T]` | `Semiring`, `Semimodule`, `AddCommMonoid`, `Monoid` | $\langle S, S[M], \cdot_s, \mathbf{0}, +, \mathbf{1}, \ast \rangle$ |
| `MonoidAlgebra[K, T]` | `dict[K, T]` | `Algebra`, `CommRing`, `Ring`, `Module`, `Semiring` | $\langle R, R[M], \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \ast \rangle$ |
| `QuotientMonoidAlgebraSemiring[K, T]` | `dict[K, T]` | `Semiring`, `Semimodule`, `AddCommMonoid`, `Monoid` | $S[M] / \mathcal{I}$ with `quotient_fn` & `ideal` |
| `QuotientMonoidAlgebra[K, T]` | `dict[K, T]` | `Algebra`, `CommRing`, `Ring`, `Module`, `Semiring` | $R[M] / \mathcal{I}$ with `quotient_fn`, `ideal`, `neg`, `sub` |
| `PolynomialAlgebra[T]` | `dict[int, T]` | `Algebra`, `CommRing`, `Ring`, `Module`, `Semiring` | $\langle R, R[x], \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ |
| `DualNumberAlgebra` | `tuple[float, float]` | `Algebra`, `CommRing`, `Ring`, `Module`, `Semiring` | $\langle \mathbb{R}, \mathbb{R}[\varepsilon]/(\varepsilon^2), \cdot_s, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ |
| `QuotientSemiring[V]` | `V` (unboxed coset rep) | `Semiring` | $\langle S / I, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$ |
| `QuotientRing[V]` | `V` (unboxed coset rep) | `CommRing`, `Ring`, `Semiring` | $\langle R / I, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ |
| `QuotientAlgebra[R, V]` | `V` (unboxed coset rep) | `NonAssocAlgebra`, `Algebra` | $\langle R, A / I, \cdot_s, \mathbf{0}, +, -, \cdot \rangle$ |

---

## 4. Homomorphisms, Ideals & The First Isomorphism Theorem (`EP-0201`)

In abstract algebra, an **ideal** $I \triangleleft R$ is an additive subgroup that *absorbs* multiplication by any element of the ambient ring ($\forall r \in R, x \in I \implies r \cdot x \in I$). Ideals generalize "multiples of $n$" and arise naturally as the **kernels** of structure-preserving **homomorphisms** $\phi: R \to S$:

$$\ker \phi = \{x \in R \mid \phi(x) = \mathbf{0}_S\}, \qquad R / \ker \phi \cong \operatorname{im} \phi$$

AlgebraX provides zero-overhead, unboxed ideal and quotient primitives in `algebrax.algebra`:

- **Homomorphism Protocols**: `Homomorphism`, `RingHom`, `GroupHom`, `LinearMap`, `LieAlgebraHom`, and `CallableHomomorphism`.
- **Ideal Protocols & Implementations**: `Ideal`, `PrincipalIdeal`, `LieIdeal`, `IntegerModuloIdeal(n)`, `PolynomialTruncationIdeal(n)`, `NilpotentIdeal(k)`, `KernelIdeal(hom, cod_ring, reducer)`, and `SubspaceLieIdeal(keys)`.
- **Canonical Quotients**: `QuotientRing(ring, ideal)`, `QuotientSemiring(semiring, ideal)`, and `QuotientAlgebra(algebra, ideal)`.

```python
from fractions import Fraction
from algebrax.algebra import (
    CallableHomomorphism,
    IntegerModuloIdeal,
    KernelIdeal,
    ModularField,
    PolynomialAlgebra,
    PolynomialTruncationIdeal,
    QuotientRing,
    StandardField,
)
from algebrax.semiring import StandardSemiring
from algebrax.verification import (
    verify_ideal_absorption_laws,
    verify_quotient_ring_laws,
    verify_ring_homomorphism_laws,
)

# 1. Modular Ring Z / 6Z via IntegerModuloIdeal
z_ring = StandardField(int)
ideal_6 = IntegerModuloIdeal(6)
z_mod_6 = QuotientRing(z_ring, ideal_6)

assert 18 in ideal_6
assert z_mod_6.add(4, 5) == 3
assert z_mod_6.mul(4, 5) == 2
assert all(verify_ideal_absorption_laws(z_ring, ideal_6, [-5, 0, 2, 7], [-6, 0, 6, 12]).values())
assert all(verify_quotient_ring_laws(z_mod_6, [-2, 0, 1, 5], [-6, 0, 6]).values())

# 2. First Isomorphism Theorem: Z / ker(phi) ~= F_5
f5 = ModularField(5)
phi = CallableHomomorphism(lambda x: x % 5)
assert all(verify_ring_homomorphism_laws(phi, z_ring, f5, [-3, 0, 1, 4]).values())

ker_phi = KernelIdeal(phi, f5, reducer=lambda x: x % 5)
assert 15 in ker_phi and 7 not in ker_phi

# 3. Truncated Taylor Series Ring Q[x] / (x^3)
poly_q = PolynomialAlgebra(StandardSemiring(Fraction))
trunc_3 = PolynomialTruncationIdeal(3, zero_coeff=Fraction(0))
taylor_3 = QuotientRing(poly_q, trunc_3)

# (1 + x + x^2) * (1 + 2x) === 1 + 3x + 3x^2 (mod x^3)
p1 = {0: Fraction(1), 1: Fraction(1), 2: Fraction(1)}
p2 = {0: Fraction(1), 1: Fraction(2)}
assert taylor_3.mul(p1, p2) == {0: Fraction(1), 1: Fraction(3), 2: Fraction(3)}
```

### Quotient Monoid Algebra Example: Constructing $\mathbb{C} \cong \mathbb{R}[x] / (x^2 + 1)$

```python
from algebrax.semiring import StandardSemiring

# Reduce x^k modulo (x^2 = -1)
def mod_x2_plus_1(exp: int, coeff: float) -> list[tuple[int, float]]:
    q, r = divmod(exp, 2)
    sign = -1.0 if q % 2 == 1 else 1.0
    return [(r, coeff * sign)]


complex_quotient = QuotientMonoidAlgebraSemiring[int, float](
    coeff_semiring=StandardSemiring(float),
    key_op=lambda a, b: a + b,
    zero_key=0,
    quotient_fn=mod_x2_plus_1,
)

# (1 + i)^2 = 2i
one_plus_i = {0: 1.0, 1: 1.0}
assert complex_quotient.mul(one_plus_i, one_plus_i) == {1: 2.0}
```

---

## 5. Falsifiability: Law Verification & Counterexamples

```python
from algebrax.verification import verify_comm_ring_laws

# Verify PolynomialAlgebra(StandardSemiring(int)) satisfies all Commutative Ring axioms
samples = [{}, {0: 1}, {1: 2}, {0: -1, 1: 3, 2: 1}]
assert all(verify_comm_ring_laws(PolynomialAlgebra(StandardSemiring(int)), samples).values())

# Verify DualNumberAlgebra satisfies all Commutative Ring axioms (with nilpotent ε² = 0)
dual_samples = [(0.0, 0.0), (1.0, 0.0), (2.0, 3.0), (-1.5, 4.0)]
assert all(verify_comm_ring_laws(DualNumberAlgebra(), dual_samples).values())
```

**Counterexample (Zero Divisors in Dual Numbers)**: Although `DualNumberAlgebra` is a `CommRing`, it is **not** a `Field` because pure infinitesimals $(0, b)$ are nilpotent zero divisors: $(0, 1) \cdot (0, 1) = (0, 0)$, so $(0, 1)$ has no multiplicative inverse!

---

## 6. Frontier Horizons & Cross-Domain Bridges

- **Higher-Order Divided Power Jets**: Extending $\mathbb{R}[\varepsilon]/(\varepsilon^2)$ to $\mathbb{R}[\varepsilon]/(\varepsilon^{K+1})$ yields `BinomialConvolutionSemiring` and `StatisticalMomentSemiring` for exact single-pass variance, skewness, and kurtosis; see [Statistical Semirings](../semirings/statistical.md).
- **Lie Algebra Quotients ($\mathfrak{se}(3) / \mathbb{R}^3 \cong \mathfrak{so}(3)$)**: Using `SubspaceLieIdeal` and `QuotientAlgebra`, rigid-body twists in $\mathfrak{se}(n)$ project cleanly onto pure rotational angular velocities in $\mathfrak{so}(n)$ by quotienting out the abelian translational ideal $\mathbb{R}^n$.
- **Clifford & Galois Quotients**: `QuotientMonoidAlgebraSemiring` serves as the engine underneath [Clifford Geometric Algebras](clifford_geometric_algebra.md) and [Galois Finite Fields $\operatorname{GF}(p^m)$](rings_and_fields.md).

