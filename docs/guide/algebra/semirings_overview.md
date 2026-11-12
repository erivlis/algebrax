---
title: Semirings Overview
description: How Semiring[V], StarSemiring[V], and KleeneAlgebra[V] structure commutative path aggregations, sequential compositions, and Kleene closures.
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

In `algebrax.algebra`, the semiring family is structured as a clear three-tiered hierarchy of flat, diamond-free compositions:

1. **`Semiring[V]` (Pure Rig)**: The foundational two-operation system $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$ combining an additive commutative monoid and a multiplicative monoid linked by distributivity and zero annihilation.
2. **`StarSemiring[V]` (Closed / Conway Semiring)**: Equips a `Semiring` with unary Kleene star closure $a^* = \mathbf{1} \oplus a \cdot a^*$ (`HasStar[V]`). Synonyms: `ClosedSemiring`, `ConwaySemiring`.
3. **`KleeneAlgebra[V]`**: An idempotent star semiring ($a \oplus a = a$) witnessing the [`LawIdempotent`](../../concepts.md#equational-law-witness-mixins-pillar-2) marker.

```python
from typing import Protocol, TypeVar
from algebrax.algebra import HasAdd, HasMul, HasOne, HasStar, HasZero, LawIdempotent

V = TypeVar('V')


# 1. Pure Rig: (zero, one, add, mul)
class Semiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], Protocol):
    ...


# 2. Closed / Conway Semiring: adds Kleene star closure
class StarSemiring(HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], Protocol):
    ...


# 3. Kleene Algebra: idempotent star semiring
class KleeneAlgebra(
    HasZero[V], HasAdd[V], HasOne[V], HasMul[V], HasStar[V], LawIdempotent, Protocol
):
    ...
```

| Protocol | Mixin Composition | Formal Signature | Role & Capabilities |
|:---------|:------------------|:-----------------|:--------------------|
| **`Semiring[V]`** | `(HasZero, HasAdd, HasOne, HasMul)` | $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle$ | Standard linear algebra, polynomial algebras, and generic rigs. |
| **`StarSemiring[V]`** | `(..., HasStar)` | $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$ | Graph reachability, all-pairs paths, and Taylor series closures (`DualNumberAlgebra`). |
| **`KleeneAlgebra[V]`** | `(..., HasStar, LawIdempotent)` | $\langle V, \mathbf{0}, +, \mathbf{1}, \cdot, ^* \rangle$ with $a \oplus a = a$ | Regular languages, finite automata, and extremal routing (`TropicalSemiring`, `BooleanSemiring`). |

> [!NOTE]
> **Subtyping Harmony: Every Ring is a Semiring**
> Because `Semiring` requires only `zero, one, add, mul`, the classical mathematical inclusion $\text{Semiring} \subset \text{Ring} \subset \text{CommRing} \subset \text{Field}$ holds strictly under structural subtyping:
> ```python
> from algebrax.algebra import IntegerRing, ModularField, Ring, Semiring, StandardField
>
> assert isinstance(IntegerRing(), Semiring)  # Rings are Semirings!
> assert isinstance(StandardField(float), Semiring)  # Fields are Semirings!
> assert isinstance(ModularField(7), Semiring)  # Modular rings are Semirings!
> ```

Because `Semiring` includes `HasZero`, `HasAdd`, `HasOne`, and `HasMul`, every `Semiring` instance automatically satisfies `AddCommMonoid[V]`, `AddMonoid[V]`, `Monoid[V]`, and `Semigroup[V]` via structural subtyping (`isinstance`).

---

## 4. Falsifiability: Law Verification & Counterexamples

Every semiring must satisfy 9 axioms (additive associativity/commutativity/identity, multiplicative associativity/identity, left/right distributivity, and left/right zero annihilation). Structures equipped with Kleene star (`StarSemiring` and `KleeneAlgebra`) satisfy additional closure laws:

```python
from algebrax.semiring import TropicalSemiring
from algebrax.verification import (
    verify_kleene_algebra_laws,
    verify_semiring_laws,
    verify_star_semiring_laws,
)

samples = [float('inf'), 0.0, 1.5, 4.0]
trop = TropicalSemiring()

# 1. Standard 9 Semiring laws
res_rig = verify_semiring_laws(trop, samples)
assert all(res_rig.values())

# 2. Star Semiring fixed-point closure laws: a* = 1 + a · a* = 1 + a* · a
res_star = verify_star_semiring_laws(trop, samples)
assert all(res_star.values())

# 3. Kleene Algebra laws: Star closure + Additive Idempotence (a + a = a)
res_kleene = verify_kleene_algebra_laws(trop, samples)
assert all(res_kleene.values())

# Counterexample: Idempotent Semirings cannot possess additive inverses (no subtraction!)
# In TropicalSemiring, min(a, a) = a. If an additive inverse (-a) existed,
# adding it to both sides would force a = 0 (tropical infinity), collapsing the carrier.
assert trop.add(3.0, 3.0) == 3.0  # min(3.0, 3.0) == 3.0
```

> [!TIP]
> Explore the complete **[Semiring Taxonomy & Interactive Catalog](../semirings/index.md)** to browse all 34 built-in semirings across Arithmetic, Optimization, Statistical Moments, Logic, and Formal Structures.
