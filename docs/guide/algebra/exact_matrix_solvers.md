---
title: Exact Matrix Solvers
description: Drift-free Gaussian elimination, LU decomposition, determinant, inverse, and linear system solvers over StandardField(Fraction) and ModularField(p).
---

# Exact Matrix Solvers (`algebrax.matrix` & `algebrax.algebra.Field`)

## 1. The Practical Problem: Catastrophic Floating-Point Cancellation

In IEEE-754 `float64` arithmetic, ill-conditioned linear systems—such as Hilbert matrices $H_{ij} = \frac{1}{i + j + 1}$, topological boundary matrices over finite fields $\mathbb{F}_p$, or cryptographic Reed–Solomon codes—suffer from catastrophic cancellation or require exact modular division. By parameterizing Gaussian elimination over any `Field[V]` (`StandardField(Fraction)` for $\mathbb{Q}$ or `ModularField(p)` for $\mathbb{F}_p$), AlgebraX solves sparse linear systems **with zero rounding error**.

---

## 2. The 30-Second Executable Snippet

```python
from fractions import Fraction
from algebrax.algebra import ModularField, StandardField
from algebrax.matrix import det, inv, solve

# 1. Exact Rational Hilbert Matrix H_2 over Q
q = StandardField(Fraction)
h2 = {
    0: {0: Fraction(1, 1), 1: Fraction(1, 2)},
    1: {0: Fraction(1, 2), 1: Fraction(1, 3)},
}
assert det(h2, field=q) == Fraction(1, 12)
assert inv(h2, field=q) == {
    0: {0: Fraction(4, 1), 1: Fraction(-6, 1)},
    1: {0: Fraction(-6, 1), 1: Fraction(12, 1)},
}

# 2. Exact Linear System over Finite Prime Field F_11
f11 = ModularField(11)
a = {'eq1': {'x': 3, 'y': 2}, 'eq2': {'x': 4, 'y': 9}}
b = {'eq1': 5, 'eq2': 1}
sol = solve(a, b, field=f11)
assert (3 * sol['x'] + 2 * sol['y']) % 11 == 5
assert (4 * sol['x'] + 9 * sol['y']) % 11 == 1
```

---

## 3. Protocol Contract & Solver Operations

All exact matrix solvers accept an optional `field: Field[V]` instance implementing `(HasZero[V], HasZeroPred[V], HasAdd[V], HasNeg[V], HasOne[V], HasMul[V], HasInv[V], Protocol)`:

| Solver Function (`algebrax.matrix`) | Mathematical Meaning | Complexity / Sparsity |
|:------------------------------------|:---------------------|:----------------------|
| `lu_decompose(m, field=...)` | Partial/row-pivoted $PA = LU$ factorization over `Field[V]` | Hoists `inv(pivot)` once per pivot row; skips zero factors |
| `solve(a, b, field=...)` | Solves $Ax = b$ via exact forward/backward substitution | Exact over $\mathbb{Q}$, $\mathbb{F}_p$, $\mathbb{R}$, $\mathbb{C}$ |
| `det(m, field=...)` | Determinant $\det(A) = \operatorname{sgn}(P) \prod_i U_{ii}$ | $O(N^3)$ worst-case, zero-skipping on sparse rows |
| `inv(m, field=...)` | Exact matrix inverse $A^{-1}$ solving $AX = I$ | Raises `ValueError` if $\det(A) = \mathbf{0}$ |

### Performance Engineering (The Shannon Principle)

1. **Pivot Inversion Hoisting**: In `ModularField(p)` and `StandardField(Fraction)`, multiplicative inversion (`pow(a, -1, p)` or GCD reduction) is more expensive than multiplication. `lu_decompose` computes `inv_pivot = field.inv(pivot)` **once** per outer pivot step and multiplies across the row.
2. **Inner Zero-Skipping**: Before updating $U_{ij} \leftarrow U_{ij} - \text{factor} \cdot U_{kj}$, the solver checks `field.is_zero(factor)` and `field.is_zero(U_kj)`, skipping empty coordinates to preserve dictionary sparsity.

---

## 4. Falsifiability: Zero-Division Guards & Singular Matrices

```python
import pytest

# 1. Field zero inversion strictly raises ZeroDivisionError
with pytest.raises(ZeroDivisionError):
    q.inv(Fraction(0, 1))

with pytest.raises(ZeroDivisionError):
    f11.div(5, 0)

# 2. Singular matrix inversion raises ValueError
singular = {0: {0: Fraction(1, 1), 1: Fraction(2, 1)}, 1: {0: Fraction(2, 1), 1: Fraction(4, 1)}}
assert det(singular, field=q) == Fraction(0, 1)
with pytest.raises(ValueError):
    inv(singular, field=q)
```

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **Persistent Homology Over $\mathbb{F}_2$**: Boundary matrix reduction in [Persistent Homology](../topology/persistence.md) is Gaussian elimination over $\mathbb{F}_2 = \text{ModularField}(2)$.
- **Certified Solver Verification**: Every solution $x = \text{solve}(A, b, \text{field}=F)$ can be verified in $O(\text{nnz}(A))$ time by checking $A x - b = \mathbf{0}$.
