---
title: "EP-0207: Topological K-Theory, Grothendieck Groups & Characteristic Classes"
description: "Formalize the Grothendieck group construction, topological K-theory ring of discrete vector bundles, and characteristic Chern classes bridging curvature to cohomology."
icon: lucide/orbit
status: draft
---

# EP-0207: Topological K-Theory, Grothendieck Groups & Characteristic Classes

| Field             | Value                                                               |
|:------------------|:--------------------------------------------------------------------|
| **EP**            | 0207                                                                |
| **Title**         | Topological K-Theory, Grothendieck Groups & Characteristic Classes  |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                         |
| **Sponsor**       | Core Maintainers                                                    |
| **Delegate**      | ⚖️ Noether (Chern Invariants) & 🧩 Russell (Universal Grothendieck) |
| **Status**        | Draft                                                               |
| **Type**          | Standards Track                                                     |
| **Created**       | 2026-10-28                                                          |
| **Updated**       | 2026-10-28                                                          |
| **Replaces**      | —                                                                   |
| **Superseded-By** | —                                                                   |

---

## Abstract

This proposal introduces **K-Theory** into AlgebraX, providing the universal classification of discrete vector bundles
and projective modules. EP-0207 establishes:

1. **The Universal Grothendieck Group Functor (`GrothendieckGroup[M]`)**: A universal categorical functor converting any
   commutative monoid $(M, +, 0)$ into an abelian group $K_0 (M)$ via formal difference classes $[a - b]$, satisfying
   the canonical universal arrow property.
2. **Topological K-Theory of Discrete Vector Bundles ($K^0 (K)$)**: Building directly on the discrete vector bundles
   of [EP-0203](EP-0203-discrete-fiber-bundles-and-gauge-connections.md), formalizing the **K-theory ring** equipped
   with Whitney direct sums $E \oplus F$ (block-diagonal transport) and tensor products $E \otimes F$ (Kronecker product
   transport).
3. **Discrete Characteristic Classes & Chern Character**: Mapping discrete vector bundle curvature
   2-forms $F = d_\nabla^2$ to integer cohomology classes in `algebrax.dec`:
   $$\operatorname{ch}_0 (E) = \operatorname{rank} (E), \quad \operatorname{ch}_1 (E) = \frac{1}{2\pi i} \operatorname{tr} (F), \quad \operatorname{ch}_2 (E) = \frac{1}{8\pi^2} \operatorname{tr} (F \wedge F)$$
   proving that $\operatorname{ch}: K^0 (K) \to H^{\text{even}} (K; \mathbb{Q})$ is a ring homomorphism under the
   cochain cup product.
4. **$K_1 (R)$ & Generalized Non-Commutative Determinants**: Formalizing the Whitehead
   group $K_1 (R) = \mathrm{GL} (R) / \mathrm{E} (R)$, giving well-defined determinants over non-commutative rings and
   division algebras.
5. **Axiomatic Verification Suite**: Verifying the universal mapping property of the Grothendieck group, Chern character
   additivity ($\operatorname{ch} (E \oplus F) = \operatorname{ch} (E) + \operatorname{ch} (F)$), and multiplicativity
   ($\operatorname{ch} (E \otimes F) = \operatorname{ch} (E) \smile \operatorname{ch} (F)$).

All bundle operations maintain unboxed block sparse matrices (`dict[tuple[...], dict[tuple[...], float]]`), ensuring
zero heap boxing.

---

## Motivation

K-theory represents one of the deepest organizing principles in modern geometry, mathematical physics, and algebra:

1. **Classification of Topological States**: In condensed matter physics (topological insulators, quantum Hall effect)
   and string theory (D-branes), physical phases are classified not by continuous geometry, but by **Topological
   K-theory classes** $K^0 (X)$.
2. **The Missing Bridge to Cohomology**: In `EP-0203`, we formalized discrete connections and curvature 2-forms $F$.
   However, without characteristic classes, there is no canonical way to compute the topological invariants (first Chern
   number, Euler class) that characterize non-trivial bundles.
3. **The Universal Group Constructor**: In `algebrax.algebra`, we have commutative monoids (`AddCommMonoid`) and
   commutative groups (`AddCommGroup`). However, there is no formal functor to convert a monoid into a group (the
   universal Grothendieck group $K_0 (\mathbb{N}) \cong \mathbb{Z}$).

By formalizing the Grothendieck group and discrete K-theory, AlgebraX unifies bundle curvature with integer topological
cohomology.

---

## Rationale & Council Alignment

- **⚖️ Noether (Conserved Topological Charges & Chern Numbers)**:
  Chern numbers are gauge-invariant integer topological invariants. They are strictly conserved under continuous
  deformations and coordinate changes.
- **⚡ Shannon (Zero Bloat & Sparse Block Whitney Sums)**:
  Whitney direct sums are simple block-diagonal concatenations of existing sparse matrices. Tensor products use standard
  sparse Kronecker matrix products.
- **🔬 Popper (Falsifiability & Integer Quantization)**:
  Popperian tests verify:
    1. Integrality: $\oint_C \operatorname{ch}_1 (E) \in \mathbb{Z}$ over closed 2-cycles.
    2. Ring Homomorphism: $\operatorname{ch} (E \oplus F) = \operatorname{ch} (E) + \operatorname{ch} (F)$
       and $\operatorname{ch} (E \otimes F) = \operatorname{ch} (E) \smile \operatorname{ch} (F)$.
- **🧩 Russell (Universal Categorical Adjunction)**:
  The Grothendieck construction is the universal left adjoint to the forgetful
  functor $\mathbf{Ab} \to \mathbf{CommMonoid}$.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"K-theory is just learning how to do subtraction. If you have vector spaces that you can add together, K-theory
  invents negative vector spaces so you can measure what is left over."*

---

## Specification

### 1. The Universal Grothendieck Group Functor (`src/algebrax/algebra/grothendieck.py`)

```python
from typing import Generic, Protocol, TypeVar
from collections.abc import Callable
from algebrax.algebra._monoid import AddCommMonoid
from algebrax.algebra._group import AddCommGroup

M = TypeVar("M")


class GrothendieckGroup(AddCommGroup[tuple[M, M]], Generic[M]):
    r"""The universal Grothendieck group $K_0(M)$ of commutative monoid $M$.

    Elements are formal differences represented as pairs $(a, b) \in M \times M$ representing $a - b$,
    with equivalence $(a, b) \sim (c, d) \iff a + d + k = b + c + k$ for some $k \in M$.
    """

    def __init__(self, monoid: AddCommMonoid[M]) -> None:
        self.monoid = monoid

    def zero(self) -> tuple[M, M]:
        z = self.monoid.zero()
        return (z, z)

    def add(self, x: tuple[M, M], y: tuple[M, M]) -> tuple[M, M]:
        return (
            self.monoid.add(x[0], y[0]),
            self.monoid.add(x[1], y[1]),
        )

    def neg(self, x: tuple[M, M]) -> tuple[M, M]:
        """Formal negative -(a - b) = (b - a)."""
        return (x[1], x[0])

    def sub(self, x: tuple[M, M], y: tuple[M, M]) -> tuple[M, M]:
        return self.add(x, self.neg(y))
```

### 2. Topological K-Theory Operations (`src/algebrax/topology/k_theory.py`)

```python
from algebrax.topology.bundle import DiscreteOrthogonalConnection


def bundle_direct_sum(
        e1: DiscreteOrthogonalConnection,
        e2: DiscreteOrthogonalConnection,
        edges: list[tuple[Any, Any]],
) -> DiscreteOrthogonalConnection:
    r"""Whitney direct sum $E_1 \oplus E_2$ with block-diagonal transport:
    $$\rho_{E_1 \oplus E_2} = \begin{pmatrix} \rho_1 & \mathbf{0} \\ \mathbf{0} & \rho_2 \end{pmatrix}$$
    """
    d1 = e1.fiber_dim
    d2 = e2.fiber_dim
    res = DiscreteOrthogonalConnection(d1 + d2)

    for u, v in edges:
        t1 = e1.transport(u, v)
        t2 = e2.transport(u, v)
        block: dict[int, dict[int, float]] = {}
        # Block 1
        for i, row in t1.items():
            for j, val in row.items():
                block.setdefault(i, {})[j] = val
        # Block 2 shifted by d1
        for i, row in t2.items():
            for j, val in row.items():
                block.setdefault(i + d1, {})[j + d1] = val
        res.set_transport(u, v, block)

    return res
```

### 3. Discrete Chern Character & Characteristic Classes (`src/algebrax/topology/chern.py`)

```python
def compute_chern_character_1(
        connection: DiscreteOrthogonalConnection,
        faces: list[tuple[Any, ...]],
) -> dict[tuple[Any, ...], float]:
    r"""Compute first Chern class 2-form $c_1(E) = \frac{1}{2\pi} \operatorname{tr}(F)$ on 2-faces."""
    from algebrax.topology.curvature import compute_face_holonomy
    import math

    c1_form: dict[tuple[Any, ...], float] = {}
    for face in faces:
        hol = compute_face_holonomy(connection, face)
        # Trace of holonomy deviation
        trace_val = sum(hol.get(i, {}).get(i, 0.0) for i in range(connection.fiber_dim))
        c1_form[face] = trace_val / (2.0 * math.pi)
    return c1_form
```

---

## Backwards Compatibility

Strictly additive. Extends `algebrax.topology` and `algebrax.algebra` without breaking existing interfaces.

---

## How to Teach This / Documentation Plan

1. **User Guide (`docs/guides/k-theory-and-chern-classes.md`)**:
    - The Grothendieck group: constructing $\mathbb{Z}$ from $\mathbb{N}$ algorithmically.
    - Whitney sums and tensor products of discrete connections.
    - Calculating Chern numbers on curved meshes to detect topological vortices.

---

## Reference Implementation

Evaluated and confirmed under Council review in
`references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md`.

---

## Rejected Ideas

1. **Higher Continuous Quillen K-Theory ($K_n (R)$ for $n \ge 3$)**:
   *Rejected*: AlgebraX operates strictly on discrete and algorithmic structures. Infinite-dimensional algebraic
   K-theory belongs in specialized research packages.

---

## Open Questions

1. **Bott Periodicity**:
   Can we provide a discrete synthetic demonstration of mod-2 / mod-8 Bott periodicity using Clifford algebra
   representations? *Recommendation*: Yes, linking $K^0$ directly with `algebrax.clifford`.

---

## Change Log

- **2026-10-28**: Initial draft authored following Council consensus.
