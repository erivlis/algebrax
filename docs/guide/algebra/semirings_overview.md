---
title: Semirings Overview
description: How Semiring[V] combines an additive commutative monoid, a multiplicative monoid, and Kleene star closure to power polymorphic graph and matrix algorithms.
---

# Semirings Overview (`algebrax.algebra.Semiring`)

## 1. The Practical Problem: One Algorithm, 34 Domains

Consider classic matrix multiplication $C_{ij} = \sum_k A_{ik} \cdot B_{kj}$. In standard linear algebra, $\sum$ is addition ($+$) and $\cdot$ is multiplication ($\times$). What if you replace $(+, \times)$ with:
- $(\min, +)$ $\longrightarrow$ **Shortest Paths** (Bellman–Ford / Floyd–Warshall)
- $(\max, \times)$ $\longrightarrow$ **Most Probable Viterbi Path** (HMM decoding)
- $(\vee, \wedge)$ $\longrightarrow$ **Transitive Reachability**
- $(\max, \min)$ $\longrightarrow$ **Maximum Capacity Bottleneck Flow**

All of these share the exact same algebraic laws: an **Additive Commutative Monoid** $\langle V, \mathbf{0}, + \rangle$ and a **Multiplicative Monoid** $\langle V, \mathbf{1}, \cdot \rangle$ linked by two-sided distributivity and zero annihilation—**without requiring subtraction or division**. That structure is a **Semiring**.

---

## 2. The 30-Second Executable Snippet

```python
import algebrax as ax

graph = {0: {1: 2.0, 2: 10.0}, 1: {2: 3.0}}

# 1. Standard linear path weight: (2.0 * 3.0) = 6.0
lin = ax.matrix.dot(graph, graph, semiring='Standard')
assert lin[0][2] == 6.0

# 2. Tropical shortest 2-hop path: min(inf, 2.0 + 3.0) = 5.0
short = ax.matrix.dot(graph, graph, semiring='Tropical')
assert short[0][2] == 5.0
```

---

## 3. Atomic Mixins & Protocol Contract

In `algebrax.algebra`, `Semiring[V]` is a flat, diamond-free composition of five atomic operational mixins:

```python
from typing import Protocol, TypeVar
from algebrax.algebra import HasAdd, HasMul, HasOne, HasStar, HasZero

V = TypeVar('V')


class Semiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], Protocol):
    ...
```

| Mixin | Operation / Property | Semiring Role |
|:------|:---------------------|:--------------|
| `HasZero[V]` | `zero: V` | Additive neutral element $\mathbf{0}$ (annihilator for $\cdot$) |
| `HasAdd[V]` | `add(a, b) -> V` | Commutative, associative path aggregation $\oplus$ |
| `HasOne[V]` | `one: V` | Multiplicative neutral element $\mathbf{1}$ |
| `HasMul[V]` | `mul(a, b) -> V` | Associative sequential path composition $\otimes$ |
| `HasStar[V]` | `star(a) -> V` | Kleene closure $a^* = \mathbf{1} \oplus a \oplus a^2 \oplus \cdots$ |

Because `Semiring` includes `HasZero`, `HasAdd`, `HasOne`, and `HasMul`, every `Semiring` instance automatically satisfies `AddCommMonoid[V]`, `AddMonoid[V]`, `Monoid[V]`, and `Semigroup[V]` via structural subtyping (`isinstance`).

---

## 4. Falsifiability: Law Verification & Counterexamples

Every semiring must satisfy 9 axioms (additive associativity/commutativity/identity, multiplicative associativity/identity, left/right distributivity, and left/right zero annihilation):

```python
from algebrax.semiring import TropicalSemiring
from algebrax.verification import verify_semiring_laws

res = verify_semiring_laws(TropicalSemiring(), [float('inf'), 0.0, 1.5, 4.0])
assert all(res.values())

# Counterexample: Idempotent Semirings cannot possess additive inverses (no subtraction!)
# In TropicalSemiring, min(a, a) = a. If an additive inverse (-a) existed,
# adding it to both sides would force a = 0 (tropical infinity), collapsing the carrier.
trop = TropicalSemiring()
assert trop.add(3.0, 3.0) == 3.0  # min(3.0, 3.0) == 3.0
```

> [!TIP]
> Explore the complete **[Semiring Taxonomy & Interactive Catalog](../semirings/index.md)** to browse all 34 built-in semirings across Arithmetic, Optimization, Statistical Moments, Logic, and Formal Structures.
