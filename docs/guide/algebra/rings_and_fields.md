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

1. **`StandardField[V]` / `IntegerField()`**:
   Wraps Python numeric types (`Fraction`, `float`, `complex` for `StandardField`; exact integer ring $\mathbb{Z}$ via `StandardSemiring(int)` / `IntegerField()`).
2. **`ModularField` ($\mathbb{F}_p$) & `ModularSemiring` ($\mathbb{Z}/n\mathbb{Z}$)**:
   Exact modular arithmetic over integers modulo $n$ (or prime $p$), computing multiplicative inverses via the Extended Euclidean Algorithm.
3. **`GaloisFieldSemiring` ($\operatorname{GF}(p^m)$)**:
   Finite extension fields constructed as quotient polynomial rings $\mathbb{F}_p[x] / \langle P(x) \rangle$ over an irreducible polynomial $P(x)$:

```python
from algebrax.galois import GaloisFieldSemiring

# Finite field GF(2^3) modulo x^3 + x + 1 (irreduc_poly=(1, 1, 0, 1))
gf8 = GaloisFieldSemiring(p=2, irreduc_poly=(1, 1, 0, 1))
x = {1: 1}      # x
x2 = {2: 1}     # x^2
# x * x^2 = x^3 === x + 1 (mod x^3 + x + 1, characteristic 2)
assert gf8.mul(x, x2) == {0: 1, 1: 1}
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

# Attempting to invert zero divisor 2 modulo 4 raises ValueError (not invertible!)
bad_f4 = ModularField(4)
with pytest.raises(ValueError, match="not invertible"):
    bad_f4.inv(2)
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

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **[Topological K-Theory, Grothendieck Groups & Characteristic Classes](../topology/k_theory.md)**: Universally complete any commutative monoid or semiring into an abelian group (`GrothendieckGroup`) or commutative ring (`GrothendieckRing`) via formal differences $[a] - [b]$.
- **[Polynomials, Dual Numbers & Quotient Algebras](polynomials_and_quotients.md)**: Build polynomial rings $R[x]$ and quotient rings $R[M]/\mathcal{I}$ over any ring or field.
- **[Exact Sparse Matrix Solvers](exact_matrix_solvers.md)**: Use `Field[V]` to compute drift-free LU decompositions, determinants, RREF, and nullspaces.
- **[Simplicial Homology & Persistent Barcodes](../topology/persistence.md)**: Compute topological invariants over $\mathbb{F}_2 = \text{ModularField}(2)$ and $\mathbb{Q}$.

