---
title: "EP-0261: Galois Connections, Tarski Fixed Points & Formal Concept Analysis"
description: "Introduce monotone and antitone Galois connections, Moore closure and interior operators, Knaster-Tarski fixed-point lattices, and bitmask NextClosure Formal Concept Analysis with Duquenne-Guigues implication bases."
icon: lucide/git-compare
status: draft
---

# EP-0261: Galois Connections, Tarski Fixed Points & Formal Concept Analysis

| Field             | Value                                                                                      |
|:------------------|:-------------------------------------------------------------------------------------------|
| **EP**            | 0261                                                                                       |
| **Title**         | Galois Connections, Tarski Fixed Points & Formal Concept Analysis                          |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                |
| **Sponsor**       | Core Maintainers                                                                           |
| **Delegate**      | ⚡ Shannon (Bitmask NextClosure), ⚖️ Noether (Adjoint Duality) & 🔬 Popper (Basis Proofs)  |
| **Status**        | Draft                                                                                      |
| **Type**          | Standards Track                                                                            |
| **Created**       | 2026-11-28                                                                                 |
| **Updated**       | 2026-11-28                                                                                 |
| **Replaces**      | —                                                                                          |
| **Superseded-By** | —                                                                                          |

---

## Abstract

This proposal implements **Phase 12, Wave 2** on top of [`EP-0260`](EP-0260-lattice-protocol-soundness-finite-posets-and-lattices.md), adding the adjunction, closure, fixed-point, and Formal Concept Analysis (FCA) layer to `algebrax.lattice`. It introduces `GaloisConnection` (monotone and antitone adjunctions with constructive counterexample diagnostics), `ClosureOperator` and `InteriorOperator` (with induced Moore lattices), Knaster–Tarski fixed-point lattice computation (`tarski_fixpoints`), and `FormalContext` implementing Ganter's bitmask **NextClosure** algorithm for concept lattice enumeration and the minimal canonical **Duquenne–Guigues** implication basis.

---

## Motivation

Galois connections are the unifying order-theoretic engine behind abstraction, duality, and knowledge discovery across mathematics and computer science:

1. **Missing Categorical Adjunction Primitives on Posets:** While `algebrax.category` models general functors (`EP-0200`), order-theoretic adjunctions $f \dashv g$ ($f(a) \le_B b \iff a \le_A g(b)$) govern Dedekind–MacNeille completion, algebraic closure (ideals $\leftrightarrow$ varieties in `EP-0221`), Galois theory (subgroups $\leftrightarrow$ subfields), and abstract interpretation.
2. **No Fixed-Point Lattice Solver:** Knaster–Tarski's theorem guarantees that the fixed points of any monotone endomorphism on a complete lattice form a complete sub-lattice—essential for computing Boolean skeletons ($\neg\neg$-fixpoints in `EP-0262`), abstract-interpretation invariants, and Kleene/mu-calculus semantics.
3. **No Zero-Dependency Formal Concept Analysis (FCA) Engine:** Mining hierarchical concept lattices and canonical implication rules ($A \Rightarrow B$) from binary object–attribute incidence tables (including AlgebraX's own algebraic structure registry from `EP-0255`) currently requires external packages (`concepts`, `fca`), whereas bitmask NextClosure runs in under a millisecond in pure Python.

---

## Rationale

Validated in [**EXP-0013**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) (Region II prototype: `11` formal concepts and `6` Duquenne–Guigues implications computed in **`0.47 ms`** on AlgebraX's own algebraic trait table, and Tarski $\neg\neg$-fixpoints recovering the exact Boolean skeleton of $C_3$):

- **⚡ Claude Shannon (Packed Bitmask NextClosure & Zero Dependencies):**
  Encoding object extents and attribute intents as Python `int` bitmasks reduces concept derivation $(A', B')$ to bitwise `AND` over incidence masks. Ganter's NextClosure enumerates all closed sets and pseudo-intents in lectic order with $O(|G| \cdot |M|)$ bitwise work per step and zero intermediate set allocations.
- **⚖️ Emmy Noether (Exact Adjunction & Closure/Interior Symmetry):**
  Every monotone Galois connection $(f \dashv g): P \rightleftarrows Q$ induces a dual connection $(g^{\mathrm{op}} \dashv f^{\mathrm{op}}): Q^{\mathrm{op}} \rightleftarrows P^{\mathrm{op}}$, a closure operator $c = g \circ f$ on $P$, an interior operator $k = f \circ g$ on $Q$, and a canonical order isomorphism between $\operatorname{Fix}(c)$ and $\operatorname{Fix}(k)$.
- **🔬 Karl Popper (Constructive Adjunction & Basis Falsification):**
  `find_adjunction_witness()` returns the exact pair $(a, b)$ violating $f(a) \le_B b \iff a \le_A g(b)$. Duquenne–Guigues implication bases are verified for both **soundness** (every object satisfying premise $P$ satisfies conclusion $Q$), **completeness** (implication closure matches exact context closure on every attribute subset), and **minimality** (no implication is derivable from the others).
- **💡 Richard Feynman (Self-Introspecting AlgebraX Context):**
  Providing a `FormalContext.from_incidence` builder (and registry helper) lets users feed AlgebraX's own algebraic structures and traits directly into FCA and automatically rediscover mathematical laws such as `{'has_inv'} => {'assoc', 'comm', 'has_neg'}` on finite fields or `{'residuated'} => {'assoc', 'comm', 'idem'}` on tested semirings.

---

## Specification

### 1. Galois Connections, Closure/Interior Operators & Tarski (`src/algebrax/lattice/_galois.py`)

```python
class GaloisConnection(Generic[A, B]):
    r"""Monotone Galois connection (adjunction) $f \dashv g$ between finite posets:
    $f(a) \le_Q b \iff a \le_P g(b)$.
    """

    def __init__(
        self,
        source: FinitePoset[A],
        target: FinitePoset[B],
        lower: Callable[[A], B],
        upper: Callable[[B], A],
        *,
        validate: bool = True,
    ) -> None: ...

    @classmethod
    def antitone(
        cls,
        source: FinitePoset[A],
        target: FinitePoset[B],
        left: Callable[[A], B],
        right: Callable[[B], A],
        *,
        validate: bool = True,
    ) -> GaloisConnection[A, B]:
        r"""Construct an antitone polarity ($a \le_P r(b) \iff b \le_Q l(a)$) as $P \rightleftarrows Q^{\mathrm{op}}$."""
        ...

    def lower(self, a: A) -> B: ...
    def upper(self, b: B) -> A: ...
    def dual(self) -> GaloisConnection[B, A]: ...
    def find_adjunction_witness(self) -> tuple[A, B] | None: ...
    def is_valid(self) -> bool: ...
    def is_galois_insertion(self) -> bool: ...
    def closure_operator(self) -> ClosureOperator[A]: ...
    def interior_operator(self) -> InteriorOperator[B]: ...


class ClosureOperator(Generic[T]):
    r"""Moore closure operator $c: P \to P$ (extensive, monotone, idempotent)."""

    def __init__(self, poset: FinitePoset[T], fn: Callable[[T], T], *, validate: bool = True) -> None: ...
    def __call__(self, x: T) -> T: ...
    def closed_elements(self) -> tuple[T, ...]: ...
    def closed_lattice(self) -> FiniteLattice[T]: ...


class InteriorOperator(Generic[T]):
    r"""Dual kernel/interior operator $k: P \to P$ (contractive, monotone, idempotent)."""

    def __init__(self, poset: FinitePoset[T], fn: Callable[[T], T], *, validate: bool = True) -> None: ...
    def __call__(self, x: T) -> T: ...
    def open_elements(self) -> tuple[T, ...]: ...
    def open_lattice(self) -> FiniteLattice[T]: ...


def tarski_fixpoints(lattice: FiniteLattice[T], f: Callable[[T], T]) -> FiniteLattice[T]:
    r"""Compute the Knaster–Tarski complete lattice of fixed points $\{x \in L \mid f(x) = x\}$
    for any monotone endomorphism $f: L \to L$.
    """
    ...


def least_fixpoint(lattice: FiniteLattice[T], f: Callable[[T], T]) -> T: ...
def greatest_fixpoint(lattice: FiniteLattice[T], f: Callable[[T], T]) -> T: ...
```

### 2. Formal Concept Analysis (`src/algebrax/lattice/_fca.py`)

```python
@dataclass(frozen=True)
class FormalConcept(Generic[G, M]):
    r"""Formal concept $(A, B)$ where $A' = B$ and $B' = A$."""

    extent: frozenset[G]
    intent: frozenset[M]


@dataclass(frozen=True)
class Implication(Generic[M]):
    r"""Attribute implication $P \Rightarrow Q$ ($P \cap Q = \emptyset$, non-trivial conclusion $Q$)."""

    premise: frozenset[M]
    conclusion: frozenset[M]


class FormalContext(Generic[G, M]):
    r"""Formal context $(G, M, I)$ backed by packed Python int bitmasks."""

    def __init__(
        self,
        objects: Sequence[G],
        attributes: Sequence[M],
        incidence: Mapping[G, Iterable[M]] | Iterable[tuple[G, M]],
    ) -> None: ...

    @property
    def objects(self) -> tuple[G, ...]: ...
    @property
    def attributes(self) -> tuple[M, ...]: ...
    def intent(self, objects: Iterable[G]) -> frozenset[M]: ...
    def extent(self, attributes: Iterable[M]) -> frozenset[G]: ...
    def closure(self, attributes: Iterable[M]) -> frozenset[M]: ...
    def concepts(self) -> tuple[FormalConcept[G, M], ...]: ...
    def concept_lattice(self) -> FiniteLattice[FormalConcept[G, M]]: ...
    def pseudo_intents(self) -> tuple[frozenset[M], ...]: ...
    def duquenne_guigues_basis(self) -> tuple[Implication[M], ...]: ...
    def galois_connection(self) -> GaloisConnection[frozenset[G], frozenset[M]]: ...
```

- `FormalContext` validates non-duplicate objects/attributes and rejects out-of-domain incidence entries (`ValueError`, `EP-0254`).
- `concepts()` and `duquenne_guigues_basis()` use Ganter's lectic NextClosure algorithm; `duquenne_guigues_basis()` computes implication closure via linclosure/fixed-point bitmask propagation.
- Re-exported publicly from `algebrax.lattice`.

### 3. Verification Oracles (`src/algebrax/verification/`)

- `verify_galois_connection(conn)`: checks monotonicity of `lower`/`upper`, adjunction equivalence, unit/counit inequalities ($a \le g(f(a))$, $f(g(b)) \le b$), and isomorphism $\operatorname{Fix}(g \circ f) \cong \operatorname{Fix}(f \circ g)$.
- `verify_closure_operator(op)`: checks extensivity, monotonicity, idempotence, and Moore intersection closure.
- `verify_tarski_fixpoints(lattice, f)`: verifies monotonicity of `f`, completeness of the returned fixed-point lattice, and exact match of `bot == least_fixpoint` / `top == greatest_fixpoint`.
- `verify_duquenne_guigues_basis(ctx, basis)`: verifies soundness on all objects, completeness against `ctx.closure`, and non-redundancy (minimality) of every pseudo-intent implication.

---

## Backwards Compatibility

Strictly additive inside `src/algebrax/lattice/` and `src/algebrax/verification/`. No breaking changes to existing APIs.

---

## How to Teach This / Documentation Plan

1. Add a dedicated section to `docs/guide/algebra/lattices_and_order.md` covering Galois connections, Knaster–Tarski fixed points, and Formal Concept Analysis (with a worked example mining implications from AlgebraX's algebraic structures).
2. Add a Jupyter recipe demonstrating NextClosure concept lattice construction and Duquenne–Guigues implication discovery.

---

## Reference Implementation

- **Research Compendium:** [`references/explorations/EXP-0013-lattice-and-order-continent/README.md`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) (Section 2.2, Region II)
- **Zero-Dependency Prototype:** [`playground/lattice_continent_prototype.py`](https://github.com/erivlis/algebrax/blob/main/playground/lattice_continent_prototype.py) (`GaloisConnection`, `FormalContext`, `next_closure`, `duquenne_guigues_basis`, `tarski_fixpoints`)

---

## Rejected Ideas

1. **Naïve $2^{|M|}$ Subset Enumeration for Concept Lattices:**
   *Rejected*: Exponentially wasteful when the number of formal concepts is far smaller than $2^{|M|}$. Bitmask NextClosure visits each closed set exactly once in lectic order.
2. **Storing `FormalContext` as Dense 2D Boolean Matrices:**
   *Rejected*: Wastes memory and prevents single-instruction bitwise intent/extent intersections. Packed integer row/column bitmasks align with Shannon's zero-overhead carrier principle.
3. **Separate `AntitoneGaloisConnection` Class:**
   *Rejected*: An antitone Galois connection between $P$ and $Q$ is mathematically identical to a monotone Galois connection between $P$ and $Q^{\mathrm{op}}$. Offering `GaloisConnection.antitone(...)` factory avoids duplicating all adjunction/closure logic.

---

## Open Questions

- [ ] Should `FormalContext.duquenne_guigues_basis()` accept an optional `max_implications: int | None` safety cutoff for large pathological contexts (since pseudo-intent enumeration can be exponential in worst-case contexts)?
- [ ] Should `FormalContext.from_registry(entries)` live in `algebrax.lattice._fca` or as a bridge helper in `algebrax.registry` to keep module coupling minimal?

---

## Change Log

* **2026-11-28:**
    * Initial Draft authored from `EXP-0013` as Phase 12 Wave 2.
