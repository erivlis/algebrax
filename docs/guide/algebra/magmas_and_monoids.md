---
title: Magmas, Semigroups & Monoids
description: Atomic operational mixins, magmas, semigroups, bands, and monoids over unboxed Python dictionaries and native carriers.
---

# Magmas, Semigroups & Monoids (`algebrax.algebra`)

## 1. The Practical Problem: Why Single-Operation Algebra Matters

Suppose you are aggregating millions of distributed log events across worker nodes. To split a stream into chunks, reduce each chunk in parallel across CPU cores, and merge the partial results—even when some worker nodes return an empty chunk—your combining function **must** satisfy two mathematical laws:
1. **Associativity** ($(a \cdot b) \cdot c = a \cdot (b \cdot c)$): Grouping order does not change the result (**Semigroup**).
2. **Neutral Identity** ($\mathbf{1} \cdot a = a \cdot \mathbf{1} = a$): An empty chunk produces a safe neutral value (**Monoid**).

Without associativity, parallel `MapReduce` produces race-condition bugs depending on thread scheduling. Without an identity element, empty partitions crash with `ValueError: reduce() of empty iterable`.

---

## 2. The 30-Second Executable Snippet

```python
from algebrax.algebra import AddCommMonoid, Monoid, fold_add, fold_mul, nsum, power
from algebrax.semiring import StandardSemiring, TropicalSemiring

# Every Semiring is automatically both an AddCommMonoid (0, +) and a Monoid (1, *)
trop = TropicalSemiring()
assert isinstance(trop, AddCommMonoid)
assert isinstance(trop, Monoid)

# Safe folding over empty and non-empty streams using Monoid (1=0.0, mul=+)
assert fold_mul(trop, []) == 0.0
assert fold_mul(trop, [2.5, 3.0, 4.5]) == 10.0

# Additive dual helpers: fold_add and nsum (repeated addition)
std = StandardSemiring(int)
assert fold_add(std, []) == 0
assert fold_add(std, [1, 2, 3, 4]) == 10
assert nsum(std, 5, 4) == 20  # 4 * 5 = 20

# O(log n) binary exponentiation on any Monoid
assert power(std, 3, 5) == 243
```

---

## 3. Atomic Mixins & Protocol Contracts

In `algebrax.algebra`, named protocols are flat, diamond-free compositions of **Atomic Operational Mixins** defined in `algebrax.algebra._mixins`:

| Named Protocol | Mixin Composition | Algebraic Signature | Key Law |
|:---------------|:------------------|:--------------------|:--------|
| `Magma[V]` | `(HasMul[V], Protocol)` | $\langle V, \cdot \rangle$ | Closure: $a \cdot b \in V$ |
| `Semigroup[V]` | `(HasMul[V], Protocol)` | $\langle V, \cdot \rangle$ | Associativity: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$ |
| `Band[V]` | `(HasMul[V], Protocol)` | $\langle V, \cdot \rangle$ | Idempotence: $a \cdot a = a$ |
| `Quasigroup[V]` | `(HasMul[V], Protocol)` | $\langle V, \cdot, \backslash, / \rangle$ | Latin square divisibility: $a \cdot (a \backslash b) = b$ |
| `Monoid[V]` | `(HasOne[V], HasMul[V], Protocol)` | $\langle V, \mathbf{1}, \cdot \rangle$ | Identity: $\mathbf{1} \cdot a = a \cdot \mathbf{1} = a$ |
| `CommMonoid[V]` | `(HasOne[V], HasMul[V], Protocol)` | $\langle V, \mathbf{1}, \cdot \rangle$ | Commutativity: $a \cdot b = b \cdot a$ |
| `AddMagma[V]` / `AddSemigroup[V]` | `(HasAdd[V], Protocol)` | $\langle V, + \rangle$ | Additive closure / associativity |
| `AddMonoid[V]` / `AddCommMonoid[V]` | `(HasZero[V], HasAdd[V], Protocol)` | $\langle V, \mathbf{0}, + \rangle$ | Additive identity: $\mathbf{0} + a = a$ |
| `OpMagma[V]` / `OpSemigroup[V]` | `(HasOp[V], Protocol)` | $\langle V, \operatorname{op} \rangle$ | Domain-agnostic binary operation |
| `OpMonoid[V]` / `OpCommMonoid[V]` | `(HasIdentity[V], HasOp[V], Protocol)` | $\langle V, \operatorname{identity}, \operatorname{op} \rangle$ | Domain-agnostic identity & composition |

### Domain-Agnostic Monoids (`OpMonoid`)

When an operation is neither numeric addition nor multiplication (e.g., bitwise XOR, string concatenation, list merging), implement `OpMonoid` using `HasIdentity` and `HasOp`:

```python
from algebrax.algebra import OpCommMonoid, fold_op


class XorMonoid:
    @property
    def identity(self) -> int:
        return 0

    def op(self, a: int, b: int) -> int:
        return a ^ b


xor = XorMonoid()
assert isinstance(xor, OpCommMonoid)
assert fold_op(xor, [1, 2, 4, 1]) == 6
```

---

## 4. Falsifiability: Law Verification & Counterexamples

Use `algebrax.verification` to audit any custom magma, semigroup, band, or monoid against the Popper Guard ($|S| \ge 3$ samples):

```python
from algebrax.verification import verify_monoid_laws, verify_semigroup_laws

# Positive verification: TropicalSemiring is a valid Monoid
res = verify_monoid_laws(TropicalSemiring(), [0.0, 1.5, 4.0, float('inf')])
assert all(res.values())


# Counterexample: Subtraction is a Magma, but FAILS Semigroup associativity!
# (10 - 3) - 2 = 5 != 10 - (3 - 2) = 9
class SubtractionMagma:
    def mul(self, a: int, b: int) -> int:
        return a - b


bad_sg = SubtractionMagma()
audit = verify_semigroup_laws(bad_sg, [10, 3, 2])
assert audit['mul_associativity'] is False
```

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **Monoid Algebras ($R[M]$)**: Pairing any monoid $M$ with a coefficient semiring $R$ yields the [Monoid Algebra Semiring](polynomials_and_quotients.md), turning key multiplication into sparse polynomial and group convolution.
- **Syntactic Monoids & Automata**: Every finite automaton induces a transition monoid of state-to-state mappings; see [Weighted Automata](../discrete/automata.md).
- **Bands & Idempotent Routing**: Idempotent semigroups (`Band`) model cache warming and network packet deduplication where re-applying an update is a no-op.
