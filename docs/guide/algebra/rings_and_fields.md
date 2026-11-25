---
title: Rings, Commutative Rings & Fields
description: Additive inverses, division rings, exact rational fields, prime modular fields F_p, and Galois extension fields GF(p^m).
---

# Rings, Commutative Rings & Fields (`algebrax.algebra`)

---

## 1. The Hook: What Breaks Without Subtraction and Division?

In a [Semiring](semirings_overview.md), you can accumulate and combine paths, but you **cannot cancel terms** ($\text{no } -a$) and **cannot invert pivots** ($\text{no } a^{-1}$):

- **Graph Laplacians ($L = D - A$) & Discrete Exterior Calculus ($\partial^2 = 0$)** require **subtraction** so oriented boundary flows cancel out. That requires a **Ring**.
- **Gaussian Elimination, Exact Nullspaces, and Reed-Solomon Coding** require dividing by non-zero pivot elements without floating-point rounding drift. That requires a **Field**.

---

## 2. The 30-Second Executable Snippet

```python
from fractions import Fraction
from algebrax.algebra import Field, ModularField, Ring, StandardField

# 1. Exact Rational Field Q
Q = StandardField(Fraction)
assert isinstance(Q, Ring) and isinstance(Q, Field)
assert Q.sub(Fraction(1, 2), Fraction(1, 3)) == Fraction(1, 6)
assert Q.div(Fraction(3, 4), Fraction(9, 8)) == Fraction(2, 3)

# 2. Prime Galois Field F_7 (integers modulo prime p = 7)
F7 = ModularField(7)
assert F7.mul(3, F7.inv(3)) == 1  # 3 * 5 = 15 === 1 (mod 7)
```

---

## 3. The Protocol & Contract

### Mixin-Aligned Algebraic Signatures

`Ring`, `DivisionRing`, and `Field` compose purely orthogonal atomic mixins in strict left-to-right correspondence with their formal mathematical signatures:

| Protocol | Atomic Mixin Composition | Algebraic Signature | Added Capability |
|:---------|:-------------------------|:--------------------|:-----------------|
| **`NonAssocRing[V]`** | `(HasZero[V], HasAdd[V], HasNeg[V], HasMul[V], Protocol)` | $\langle V, \mathbf{0}, +, -, \cdot \rangle$ | Additive abelian group + distributive (possibly non-associative) product |
| **`Ring[V]`** | `(HasZero[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], Protocol)` | $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ | Associative multiplication with identity $\mathbf{1}$ and negation/subtraction |
| **`CommRing[V]`** | `(HasZero[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], Protocol)` | $\langle V, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle$ | Commutative multiplication ($a \cdot b = b \cdot a$) |
| **`DivisionRing[V]`** | `(HasZero[V], HasZeroPred[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], HasInv[V], Protocol)` | $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, {}^{-1} \rangle$ | Non-zero multiplicative inverses ($a \cdot a^{-1} = \mathbf{1}$) |
| **`Field[V]`** | `(HasZero[V], HasZeroPred[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], HasInv[V], Protocol)` | $\langle V, \mathbf{0}, \operatorname{is\_zero}, +, -, \mathbf{1}, \cdot, {}^{-1} \rangle$ | Commutative division ring enabling full exact linear algebra |

### Concrete Implementations

1. **`StandardField[V]`**:
   Wraps Python numeric types (`Fraction` for exact rationals $\mathbb{Q}$, `float` for $\mathbb{R}$, `complex` for $\mathbb{C}$). For exact integer ring arithmetic over $\mathbb{Z}$ (without division), use `StandardSemiring(int)` or `GrothendieckRing`.
2. **`ModularField` ($\mathbb{F}_p$) & `ModularSemiring` ($\mathbb{Z}/n\mathbb{Z}$)**:
   Exact modular arithmetic over integers modulo $n$ (or prime $p$), computing multiplicative inverses via the Extended Euclidean Algorithm.
3. **`GaloisField` ($\operatorname{GF}(p^m)$)**:
   Finite extension fields constructed as quotient polynomial rings $\mathbb{F}_p[x] / \langle P(x) \rangle$ over an irreducible polynomial $P(x)$, with exact multiplicative inverses via the polynomial Extended Euclidean Algorithm:

```python
from algebrax.algebra import Field, GaloisField

# Finite field GF(2^3) modulo x^3 + x + 1 (irreduc_poly=(1, 1, 0, 1))
gf8 = GaloisField(p=2, irreduc_poly=(1, 1, 0, 1))
assert isinstance(gf8, Field)
x = {1: 1}      # x
x2 = {2: 1}     # x^2
# x * x^2 = x^3 === x + 1 (mod x^3 + x + 1, characteristic 2)
assert gf8.mul(x, x2) == {0: 1, 1: 1}
assert gf8.mul(x, gf8.inv(x)) == gf8.one
```

---

## 4. Falsifiability, Law Verification & Counterexamples

### Positive Axiom Audit

```python
from algebrax.algebra import ModularField
from algebrax.verification import verify_comm_ring_laws, verify_field_laws

f5 = ModularField(5)
samples = [0, 1, 2, 3, 4]
assert all(verify_comm_ring_laws(f5, samples).values())
assert all(verify_field_laws(f5, samples).values())
```

### Negative Counterexample: Zero Divisors in $\mathbb{Z}/4\mathbb{Z}$ Break Field Invertibility

Why must the modulus $p$ of `ModularField(p)` be prime? In $\mathbb{Z}/4\mathbb{Z}$, $2 \neq 0$, yet $2 \times 2 = 4 \equiv 0 \pmod 4$. Because $2$ is a **zero divisor**, it has no multiplicative inverse:

```python
import pytest
from algebrax.algebra import ModularField
from algebrax.semiring import ModularSemiring

# ModularSemiring(4) has a non-zero element 2 whose square is 0 (zero divisor!)
z4 = ModularSemiring(4)
assert z4.mul(2, 2) == 0

# ModularField proactively rejects composite moduli at construction time
with pytest.raises(ValueError, match="prime"):
    ModularField(4)
```

### The Zero-Division Contract (Golem Safety Rule)

All `DivisionRing` and `Field` implementations guarantee that inverting or dividing by `zero` raises `ZeroDivisionError`:

```python
import pytest
from algebrax.algebra import ModularField

f7 = ModularField(7)
with pytest.raises(ZeroDivisionError):
    f7.inv(0)
```

### Unboxed $p$-Adic Fields ($\mathbb{Q}_p$) & Tropical Valuations

`PAdicField(p, precision)` implements the non-archimedean $p$-adic field $\mathbb{Q}_p$ over unboxed sparse Laurent digit mappings `dict[int, int]`. Its $p$-adic valuation $v_p(x) = \min\{k \mid a_k \ne 0\}$ forms an exact homomorphism into the **Tropical Min-Plus Semiring** (`TropicalSemiring`):
$$v_p(x \cdot y) = v_p(x) + v_p(y), \quad v_p(x + y) \ge \min(v_p(x), v_p(y)), \quad |x + y|_p \le \max(|x|_p, |y|_p)$$

```python
from algebrax.algebra import PAdicField
from algebrax.semiring import TropicalSemiring
from algebrax.verification import verify_padic_ultrametric_inequality

q5 = PAdicField(p=5, precision=10)
trop = TropicalSemiring()

x = q5.from_rational(25, 3)  # v_5(x) = 2
y = q5.from_rational(2, 5)   # v_5(y) = -1
assert q5.mul(x, q5.inv(x)) == q5.one
assert q5.valuation(q5.mul(x, y)) == trop.mul(q5.valuation(x), q5.valuation(y)) == 1.0
assert all(verify_padic_ultrametric_inequality(q5, [q5.zero, q5.one, x, y]).values())
```

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **[Topological K-Theory, Grothendieck Groups & Characteristic Classes](../topology/k_theory.md)**: Universally complete any commutative monoid or semiring into an abelian group (`GrothendieckGroup`) or commutative ring (`GrothendieckRing`) via formal differences $[a] - [b]$.
- **[Polynomials, Dual Numbers & Gröbner Quotients](polynomials_and_quotients.md)**: Build univariate and multivariate polynomial rings $k[x_1, \dots, x_n]$, exact Gröbner ideals, and quotient rings $R[M]/\mathcal{I}$ over any ring or field.
- **[Affine Varieties, Coordinate Rings & Stickelberger Solvers](varieties_and_geometry.md)**: Solve polynomial systems over $\mathbb{Q}$, enumerate elliptic curves over $\mathbb{F}_p$ and $\operatorname{GF}(p^m)$, and compute $p$-adic $K_2$ tame symbols.
- **[Exact Sparse Matrix Solvers](exact_matrix_solvers.md)**: Use `Field[V]` to compute drift-free LU decompositions, determinants, RREF, and nullspaces.
- **[Simplicial Homology & Persistent Barcodes](../topology/persistence.md)**: Compute topological invariants over $\mathbb{F}_2 = \text{ModularField}(2)$ and $\mathbb{Q}$.

