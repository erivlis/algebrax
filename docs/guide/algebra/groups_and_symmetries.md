---
title: Groups & Permutation Symmetries
description: Multiplicative and additive groups, group actions, integer powers zpow/zsmul, and symmetric permutation groups over sparse dictionaries.
---

# Groups & Permutation Symmetries (`algebrax.algebra` & `algebrax.group`)

## 1. The Practical Problem: Guaranteed Reversibility

A **Monoid** lets you fold forward, but cannot undo an action. Whenever a system requires **reversibility**—such as rolling back database transactions, inverting cryptographic permutations, computing relative coordinate deltas, or reversing 3D rigid-body transformations—every element must possess a two-sided inverse:
- **Multiplicative Group**: $a \cdot a^{-1} = a^{-1} \cdot a = \mathbf{1}$ (`HasInv[V]`).
- **Additive Group**: $a + (-a) = (-a) + a = \mathbf{0}$ (`HasNeg[V]`).

---

## 2. The 30-Second Executable Snippet

```python
from algebrax import group
from algebrax.algebra import AddCommGroup, Group, zpow, zsmul


# 1. Multiplicative Group of non-zero floats
class NonZeroFloatGroup:
    @property
    def one(self) -> float:
        return 1.0

    def mul(self, a: float, b: float) -> float:
        return a * b

    def inv(self, a: float) -> float:
        return 1.0 / a

    def div(self, a: float, b: float) -> float:
        return a / b


grp = NonZeroFloatGroup()
assert isinstance(grp, Group)
assert zpow(grp, 2.0, -3) == 0.125  # 2^(-3) = 1/8

# 2. Symmetric Permutation Group S_n over native dicts
p = {0: 1, 1: 2, 2: 0}  # 3-cycle (0 1 2)
p_inv = group.invert(p)
assert group.compose(p, p_inv) == {0: 0, 1: 1, 2: 2}
assert group.signature(p) == 1  # Even permutation
```

---

## 3. Atomic Mixins & Protocol Contracts

Groups extend monoids with the `HasInv[V]` (multiplicative) or `HasNeg[V]` (additive) mixin, which also provide derived division (`div(a, b) = mul(a, inv(b))`) and subtraction (`sub(a, b) = add(a, neg(b))`):

| Named Protocol | Mixin Composition | Algebraic Signature | Key Operations |
|:---------------|:------------------|:--------------------|:---------------|
| `Group[V]` | `(HasOne[V], HasMul[V], HasInv[V], Protocol)` | $\langle V, \mathbf{1}, \cdot, ^{-1} \rangle$ | `one`, `mul`, `inv`, `div` |
| `CommGroup[V]` / `AbelianGroup[V]` | `(HasOne[V], HasMul[V], HasInv[V], Protocol)` | $\langle V, \mathbf{1}, \cdot, ^{-1} \rangle$ | Commutative group ($a \cdot b = b \cdot a$) |
| `AddGroup[V]` | `(HasZero[V], HasAdd[V], HasNeg[V], Protocol)` | $\langle V, \mathbf{0}, +, - \rangle$ | `zero`, `add`, `neg`, `sub` |
| `AddCommGroup[V]` | `(HasZero[V], HasAdd[V], HasNeg[V], Protocol)` | $\langle V, \mathbf{0}, +, - \rangle$ | Additive abelian group ($a + b = b + a$) |
| `GroupAction[G, X]` | `(Protocol[G, X])` | $\langle G, X, \operatorname{gact} \rangle$ | Left group action $g \cdot (h \cdot x) = (gh) \cdot x$ |

### Unboxed Sparse Vectors as an `AddCommGroup`

In AlgebraX, sparse vectors `dict[K, float]` form a natural additive abelian group without wrapper classes:

```python
class SparseVectorGroup:
    @property
    def zero(self) -> dict[str, float]:
        return {}

    def add(self, u: dict[str, float], v: dict[str, float]) -> dict[str, float]:
        res = {k: u.get(k, 0.0) + v.get(k, 0.0) for k in set(u) | set(v)}
        return {k: val for k, val in res.items() if val != 0.0}

    def neg(self, u: dict[str, float]) -> dict[str, float]:
        return {k: -val for k, val in u.items()}

    def sub(self, u: dict[str, float], v: dict[str, float]) -> dict[str, float]:
        return self.add(u, self.neg(v))


svg = SparseVectorGroup()
assert isinstance(svg, AddCommGroup)
v = {'x': 2.0, 'y': -1.0}
assert zsmul(svg, v, -3) == {'x': -6.0, 'y': 3.0}
```

### Permutation Group Operations (`algebrax.group`)

Permutations $\pi \in S_n$ are represented as bijective dictionaries `{i: pi_i}`:
- **`group.compose(p1, p2)`**: Evaluates $(\pi_1 \circ \pi_2)(x) = \pi_1(\pi_2(x))$.
- **`group.invert(p)`**: Computes the inverse bijection $\pi^{-1} = \{v: k\}$.
- **`group.signature(p)`**: Computes the parity sign $\operatorname{sgn}(\pi) \in \{+1, -1\}$ via cycle decomposition in $O(N)$ time, powering exact symbolic determinants and exterior wedge products.

---

## 4. Falsifiability: Law Verification & Counterexamples

```python
from algebrax.verification import verify_add_comm_group_laws, verify_group_laws

# Positive verification: SparseVectorGroup satisfies all AddCommGroup axioms
samples = [{}, {'x': 1.0}, {'y': -2.0}, {'x': 1.0, 'y': 3.0}]
res = verify_add_comm_group_laws(svg, samples)
assert all(res.values())

# Positive verification: NonZeroFloatGroup satisfies all Group axioms
res_mul = verify_group_laws(grp, [1.0, 2.0, -0.5, 4.0])
assert all(res_mul.values())

# Counterexample: (R, *) is a Monoid, but NOT a Group because 0 has no multiplicative inverse
import pytest


class RealMultWithZero:
    one = 1.0

    def mul(self, a: float, b: float) -> float:
        return a * b

    def inv(self, a: float) -> float:
        if a == 0.0:
            raise ZeroDivisionError('0 has no multiplicative inverse')
        return 1.0 / a


with pytest.raises(ZeroDivisionError):
    RealMultWithZero().inv(0.0)
```

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **Weyl Reflection Groups**: Root systems of simple Lie algebras generate finite reflection groups (`WeylGroup`); see [Lie Algebras](lie_algebras.md).
- **Group Rings ($\mathbb{C}[G]$)**: Combining a finite group $G$ with `MonoidAlgebraSemiring` yields a group algebra for non-abelian Fourier transforms and representation theory.
- **Simplicial Chain Groups ($C_k$)**: Every chain group in [Simplicial Homology](../topology/homology.md) is a free `AddCommGroup` generated by oriented $k$-simplices.
