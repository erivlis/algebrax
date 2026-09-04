---
title: Lattices & Permutation Groups
description: Coordinate semilattices, meet, join, permutation composition, and parity signatures.
---

# Lattices & Permutation Groups (`algebrax.lattice` & `algebrax.group`)

AlgebraX provides discrete algebraic structures:

## Lattice Operations (`algebrax.lattice`)

* **`join(a, b)`**: Least Upper Bound (LUB) supremum $a \vee b$.
* **`meet(a, b)`**: Greatest Lower Bound (GLB) infimum $a \wedge b$.
* **`combine(a, b, op)`**: Element-wise vector and coordinate map reduction.

## Permutation Groups ($S_n$) (`algebrax.group`)

* **`compose(p1, p2)`**: Function composition of permutations $(\pi_2 \circ \pi_1)(x) = \pi_2(\pi_1(x))$.
* **`signature(p)`**: Permutation parity signature $\operatorname{sgn}(\pi) \in \{+1, -1\}$.
* **`inverse(p)`**: Group inverse permutation $\pi^{-1}$.

## Related Recipes & Applications

* [Distributed Vector Clocks](../../recipes.md) — Join-semilattice synchronization.
* [Algebraic Knot Theory](../../recipes.md) — Artin braid permutations and parity signatures via `group.compose` and `group.signature`.
* [Vibration Structural Analysis](../../recipes.md) — Rotor permutation symmetries via `group.compose`.
