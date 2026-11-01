---
title: Lattices, Partial Orders & Boolean Algebras
description: Join-semilattices, meet-semilattices, distributive and bounded lattices, and Boolean algebras over sparse sets and coordinate maps.
---

# Lattices, Partial Orders & Boolean Algebras (`algebrax.algebra` & `algebrax.lattice`)

## 1. The Practical Problem: Conflict-Free State Reconciliation

In distributed databases (CRDTs), static type checkers, and security access-control systems, nodes must merge concurrent state updates **without central coordination or locks**. If the merge operation is:
- **Associative**: $(a \vee b) \vee c = a \vee (b \vee c)$
- **Commutative**: $a \vee b = b \vee a$
- **Idempotent**: $a \vee a = a$ (duplicate messages have zero effect)

then the structure is a **Semilattice**, and replica convergence is mathematically guaranteed regardless of network packet reordering or duplication. When paired with a dual operation $\wedge$ satisfying the **Absorption Law** $a \wedge (a \vee b) = a$, it forms a **Lattice**.

---

## 2. The 30-Second Executable Snippet

```python
from algebrax import lattice
from algebrax.algebra import BooleanAlgebra

# 1. Sparse coordinate map lattice operations (vector clocks / fuzzy sets)
clock_a = {'node_1': 3, 'node_2': 1}
clock_b = {'node_1': 2, 'node_2': 5, 'node_3': 1}

# Least Upper Bound (join = elementwise max) & Greatest Lower Bound (meet = elementwise min)
merged_clock = lattice.join(clock_a, clock_b)
assert merged_clock == {'node_1': 3, 'node_2': 5, 'node_3': 1}
assert lattice.meet(clock_a, clock_b) == {'node_1': 2, 'node_2': 1}
```

---

## 3. Atomic Mixins & Protocol Contracts

Order-theoretic structures are composed from four orthogonal mixins (`HasJoin`, `HasMeet`, `HasBounds`, `HasComplement`):

| Named Protocol | Mixin Composition | Algebraic Signature | Defining Axioms |
|:---------------|:------------------|:--------------------|:----------------|
| `JoinSemilattice[V]` | `(HasJoin[V], Protocol)` | $\langle V, \vee \rangle$ | Associative, commutative, idempotent $\vee$ |
| `MeetSemilattice[V]` | `(HasMeet[V], Protocol)` | $\langle V, \wedge \rangle$ | Associative, commutative, idempotent $\wedge$ |
| `Lattice[V]` | `(HasJoin[V], HasMeet[V], Protocol)` | $\langle V, \vee, \wedge \rangle$ | Absorption: $a \wedge (a \vee b) = a, \ a \vee (a \wedge b) = a$ |
| `DistributiveLattice[V]` | `(HasJoin[V], HasMeet[V], Protocol)` | $\langle V, \vee, \wedge \rangle$ | $a \wedge (b \vee c) = (a \wedge b) \vee (a \wedge c)$ |
| `BoundedLattice[V]` | `(HasJoin[V], HasMeet[V], HasBounds[V], Protocol)` | $\langle V, \vee, \wedge, \bot, \top \rangle$ | Identity bounds: $a \vee \bot = a, \ a \wedge \top = a$ |
| `BooleanAlgebra[V]` | `(HasJoin[V], HasMeet[V], HasBounds[V], HasComplement[V], Protocol)` | $\langle V, \vee, \wedge, \bot, \top, \neg \rangle$ | Complements: $a \vee \neg a = \top, \ a \wedge \neg a = \bot$ |

### Power-Set Boolean Algebra Over Native `frozenset`

```python
class PowerSetAlgebra:
    """Boolean algebra over subsets of a finite universe U."""

    def __init__(self, universe: frozenset[int]) -> None:
        self.universe = universe

    @property
    def bot(self) -> frozenset[int]:
        return frozenset()

    @property
    def top(self) -> frozenset[int]:
        return self.universe

    def join(self, a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
        return a | b

    def meet(self, a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
        return a & b

    def complement(self, a: frozenset[int]) -> frozenset[int]:
        return self.universe - a


ba = PowerSetAlgebra(frozenset({1, 2, 3}))
assert isinstance(ba, BooleanAlgebra)
```

### Sparse Mapping Lattice Functions (`algebrax.lattice`)

- **`lattice.join(a, b)`**: Pointwise supremum $\max(a_k, b_k)$ across union of keys.
- **`lattice.meet(a, b)`**: Pointwise infimum $\min(a_k, b_k)$ across intersection of keys.
- **`lattice.difference(a, b)`**: Relative complement keeping keys in `a` diminished by `b`.
- **`lattice.symmetric_difference(a, b)`**: Absolute difference $|a_k - b_k|$ across keys.
- **`lattice.combine(a, b, op)`**: Generalized pointwise binary operation over sparse dictionaries.

---

## 4. Falsifiability: Law Verification & Counterexamples

```python
from algebrax.verification import verify_boolean_algebra_laws

samples = [
    frozenset(),
    frozenset({1}),
    frozenset({1, 2}),
    frozenset({1, 2, 3}),
]
audit = verify_boolean_algebra_laws(ba, samples)
assert all(audit.values())

# Counterexample: Standard (+, *) fails the Lattice Absorption Law a ∧ (a ∨ b) = a
# 2 * (2 + 3) = 10 != 2!
assert 2 * (2 + 3) != 2
```

---

## 5. Frontier Horizons & Cross-Domain Bridges

- **Distributive Lattices $\to$ Semirings**: Every bounded distributive lattice $\langle V, \vee, \wedge, \bot, \top \rangle$ is simultaneously an idempotent commutative semiring where $\oplus = \vee, \ \otimes = \wedge, \ \mathbf{0} = \bot, \ \mathbf{1} = \top$ (e.g., `BooleanSemiring` and `BottleneckSemiring`).
- **Poset Sheaves**: A [Cellular Sheaf](../topology/sheaf.md) assigns vector spaces to the face poset (a graded lattice) of a simplicial complex.
