---
title: "EP-0260: Lattice Protocol Soundness, Package Promotion & Finite Posets/Lattices"
description: "Harden lattice protocols with equational law witnesses, promote algebrax.lattice to a backward-compatible package, and deliver bitmask FinitePoset, FiniteLattice, Birkhoff duality, Dedekind-MacNeille completion, and Rota Mobius transforms."
icon: lucide/network
status: draft
---

# EP-0260: Lattice Protocol Soundness, Package Promotion & Finite Posets/Lattices

| Field             | Value                                                                                          |
|:------------------|:-----------------------------------------------------------------------------------------------|
| **EP**            | 0260                                                                                           |
| **Title**         | Lattice Protocol Soundness, Package Promotion & Finite Posets/Lattices                         |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                    |
| **Sponsor**       | Core Maintainers                                                                               |
| **Delegate**      | 🧩 Russell (Protocol Soundness), ⚖️ Noether (Order & Birkhoff Duality) & ⚡ Shannon (Bitmasks) |
| **Status**        | Draft                                                                                          |
| **Type**          | Standards Track                                                                                |
| **Created**       | 2026-11-28                                                                                     |
| **Updated**       | 2026-11-28                                                                                     |
| **Replaces**      | —                                                                                              |
| **Superseded-By** | —                                                                                              |

---

## Abstract

This proposal establishes **Phase 12, Wave 1** (scheduled to execute ahead of Phase 10 [`EP-0231`](EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md)) by transforming `algebrax.lattice` from a sparse-dictionary helper module into a first-class order-theoretic continent. It adds atomic order-theoretic capabilities and law witnesses (`HasImplication`, `HasOrthocomplement`, `LawModular`, `LawDistributive`, `LawOrthomodular`, `LawComplete`) to `algebrax.algebra._mixins`, eliminates the runtime protocol isomer bug where the non-modular pentagon $N_5$ passes `isinstance(N_5, DistributiveLattice)`, promotes `src/algebrax/lattice.py` to a 100% backward-compatible `src/algebrax/lattice/` package, and delivers zero-dependency bitmask `FinitePoset`, `FiniteLattice`, Birkhoff $M_3$/$N_5$ constructive witnesses, Birkhoff representation duality, Dedekind–MacNeille completion, canonical cross-continent lattice families (`Sub(G)`, `Subspace(F_q^n)`, $\Pi_n$), and the Rota Zeta/Möbius substrate required by `EP-0231`.

---

## Motivation

An empirical audit conducted during [`EXP-0013`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) exposed four structural defects in AlgebraX's order-theoretic layer:

1. **Zero Concrete Lattice Structures:** `src/algebrax/algebra/_lattice.py` defines six `@runtime_checkable` protocols (`JoinSemilattice`, `MeetSemilattice`, `Lattice`, `BoundedLattice`, `DistributiveLattice`, `BooleanAlgebra`), yet zero concrete lattice classes exist anywhere in `src/algebrax/`. Consequently, the unified structure registry (`EP-0255`) has no lattice entries to catalog or verify.
2. **Active Protocol Isomer Bug (`isinstance(N_5, DistributiveLattice) == True`):** `Lattice` and `DistributiveLattice` currently inherit the exact same base mixins `(HasJoin[V], HasMeet[V], Protocol)` with no equational law witness. Any duck-typed non-modular lattice—including Birkhoff's pentagon $N_5$—falsely passes `isinstance(L, DistributiveLattice)` at runtime.
3. **Namespace Shadowing by Sparse-Dict Utilities:** `src/algebrax/lattice.py` exports 13 pointwise `dict` combination functions (`average`, `combine`, `difference`, `exclude`, `exclusive`, `geometric_mean`, `harmonic_mean`, `join`, `mask`, `meet`, `product`, `ratio`, `symmetric_difference`), preventing `algebrax.lattice` from hosting order-theoretic sub-modules cleanly without a package promotion.
4. **Missing Substrate for Phase 10 (`EP-0231`) & Cross-Continent Bridges:** [`EP-0231`](EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md) specifies Rota Zeta/Möbius transforms on finite posets without a canonical `FinitePoset` class, while `algebrax.group.FiniteGroup` and `algebrax.algebra.ModularField` cannot yet project onto their canonical subgroup lattices $\operatorname{Sub}(G)$ or projective subspace lattices $\operatorname{Subspace}(\mathbb{F}_q^n)$.

---

## Rationale

Validated in [**EXP-0013**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) (Z3 5.4.1 separation proofs for $M_3$ and $N_5$ and live AlgebraX prototype benchmarks) and aligned with **EP-0005** and **Phase 8.5 (`EP-0250`–`EP-0255`)**:

- **🧩 Bertrand Russell (Flat Protocol Composition & Isomer Elimination):**
  Follows [`EP-0005`](EP-0005-universal-algebraic-protocol-architecture.md) and [`EP-0250`](EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md) by adding orthogonal Layer-1 operational atoms (`HasImplication[V]`, `HasOrthocomplement[V]`) and Layer-1 law witnesses (`LawModular`, `LawDistributive`, `LawOrthomodular`, `LawComplete`). All Layer-2 lattice protocols (`ModularLattice`, `DistributiveLattice`, `CompleteLattice`, `BooleanAlgebra`) remain strictly flat depth-2 compositions with zero diamond MROs.
- **⚖️ Emmy Noether (Order-Reversal & Birkhoff Duality):**
  Every poset and lattice carries an exact contravariant dual $P^{\mathrm{op}}$ swapping $\le \leftrightarrow \ge$, $\vee \leftrightarrow \wedge$, $\bot \leftrightarrow \top$, and $J(L) \leftrightarrow M(L)$. For every finite distributive lattice $L$, Birkhoff's Representation Theorem $L \cong \mathcal{O}(J(L))$ is implemented as an explicit invertible functor.
- **🔬 Karl Popper (Constructive Forbidden-Sublattice Falsification):**
  Instead of opaque boolean predicates, `is_modular()` and `is_distributive()` delegate to constructive witness finders (`find_n5_witness()` and `find_m3_witness()`), returning the exact 5-element pentagon $(o, a, b, c, i)$ or diamond $(o, a, b, c, i)$ sublattice whenever an axiom fails. All verification routines adhere to [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts.
- **⚡ Claude Shannon (Packed Bitmask Kernel & Mode vs. Type):**
  Representing a finite order relation on $n$ elements as two tuples of Python `int` bitmasks (`_up_masks`, `_down_masks`) delivers $O(1)$ `leq(a, b)`, bitwise transitive closure, and zero external dependencies. Following **Mode vs. Type**, a single immutable `FiniteLattice[T]` class represents arbitrary finite lattices rather than fragmenting into redundant subclass hierarchies; certified distributive/modular wrappers opt into `LawModular`/`LawDistributive` only after verifying the invariant.
- **🛡️ The Golem & 🌿 The Steward (100% Backward-Compatible Package Promotion):**
  Moving `src/algebrax/lattice.py` to `src/algebrax/lattice/_mapping.py` and re-exporting all 13 legacy functions plus all protocols from `src/algebrax/lattice/__init__.py` preserves 100% source compatibility for existing callers, tests, and recipes.

---

## Specification

### 1. Layer-1 Order Mixins & Law Witnesses (`src/algebrax/algebra/_mixins.py`)

```python
@runtime_checkable
class HasImplication(Protocol[V]):
    r"""Relative pseudo-complement / residuated implication $a \to b$."""

    def implies(self, a: V, b: V) -> V: ...


@runtime_checkable
class HasOrthocomplement(Protocol[V]):
    r"""Order-reversing involutive orthocomplement $a^\perp$ satisfying $a^{\perp\perp} = a$."""

    def ortho(self, a: V) -> V: ...


@runtime_checkable
class LawModular(Protocol):
    r"""Equational axiom witness: lattice modularity ($a \le c \implies a \vee (b \wedge c) = (a \vee b) \wedge c$)."""

    @property
    def is_modular_law(self) -> Literal[True]:
        return True


@runtime_checkable
class LawDistributive(Protocol):
    r"""Equational axiom witness: lattice distributivity ($a \wedge (b \vee c) = (a \wedge b) \vee (a \wedge c)$)."""

    @property
    def is_distributive_law(self) -> Literal[True]:
        return True


@runtime_checkable
class LawOrthomodular(Protocol):
    r"""Equational axiom witness: orthomodular law ($a \le b \implies b = a \vee (a^\perp \wedge b)$)."""

    @property
    def is_orthomodular_law(self) -> Literal[True]:
        return True


@runtime_checkable
class LawComplete(Protocol):
    r"""Order axiom witness: all subsets admit a supremum ($\bigvee S$) and infimum ($\bigwedge S$)."""

    @property
    def is_complete_law(self) -> Literal[True]:
        return True
```

*(Note: Law witness properties use `is_*_law` to avoid colliding with runtime structural inspection methods `is_modular() -> bool` and `is_distributive() -> bool` on `FiniteLattice`.)*

### 2. Hardened Flat Layer-2 Protocols (`src/algebrax/algebra/_lattice.py`)

```python
@runtime_checkable
class ModularLattice(HasJoin[V], HasMeet[V], LawModular, Protocol): ...


@runtime_checkable
class DistributiveLattice(HasJoin[V], HasMeet[V], LawModular, LawDistributive, Protocol): ...


@runtime_checkable
class CompleteLattice(HasJoin[V], HasMeet[V], HasBounds[V], LawComplete, Protocol):
    def join_all(self, elements: Iterable[V]) -> V: ...
    def meet_all(self, elements: Iterable[V]) -> V: ...


@runtime_checkable
class BooleanAlgebra(
    HasJoin[V], HasMeet[V], HasBounds[V], HasComplement[V], LawModular, LawDistributive, Protocol
): ...
```

### 3. Package Layout (`src/algebrax/lattice/`)

```text
src/algebrax/lattice/
├── __init__.py     # Public exports + 100% backward-compatible re-exports of _mapping
├── _mapping.py     # Existing 13 pointwise sparse-dict helpers (untouched signatures)
├── _poset.py       # FinitePoset, Hasse covers, order ideals O(P), Rota Zeta & Mobius
├── _finite.py      # FiniteLattice, Birkhoff M3/N5 witnesses, Birkhoff dual, Dedekind-MacNeille
└── _families.py    # power_set, divisor, chain, diamond_m3, pentagon_n5, partition, subgroup, subspace
```

### 4. `FinitePoset[T]` & Rota Incidence Substrate (`src/algebrax/lattice/_poset.py`)

```python
class FinitePoset(Generic[T]):
    r"""Immutable bitmask-backed finite partially ordered set $(P, \le)$."""

    @classmethod
    def from_relations(cls, elements: Sequence[T], relations: Iterable[tuple[T, T]]) -> FinitePoset[T]: ...

    @classmethod
    def from_covers(cls, elements: Sequence[T], covers: Iterable[tuple[T, T]]) -> FinitePoset[T]: ...

    @property
    def elements(self) -> tuple[T, ...]: ...
    def leq(self, a: T, b: T) -> bool: ...
    def lt(self, a: T, b: T) -> bool: ...
    def dual(self) -> FinitePoset[T]: ...
    def upper_set(self, a: T) -> frozenset[T]: ...
    def lower_set(self, a: T) -> frozenset[T]: ...
    def covers(self) -> tuple[tuple[T, T], ...]: ...
    def hasse_diagram(self) -> dict[T, tuple[T, ...]]: ...
    def minimal_elements(self) -> tuple[T, ...]: ...
    def maximal_elements(self) -> tuple[T, ...]: ...
    def topological_order(self) -> tuple[T, ...]: ...
    def order_ideals(self) -> tuple[frozenset[T], ...]: ...
    def order_ideal_lattice(self) -> FiniteLattice[frozenset[T]]: ...
    def zeta_matrix(self) -> SparseMatrix[T, T, int]: ...
    def mobius_matrix(self) -> SparseMatrix[T, T, int]: ...
    def mobius(self, a: T, b: T) -> int: ...
    def zeta_transform(self, signal: SparseVector[T, V], ring: Ring[V] | None = None) -> dict[T, V]: ...
    def mobius_transform(self, spectrum: SparseVector[T, V], ring: Ring[V] | None = None) -> dict[T, V]: ...
```

- Raises `ValueError` on antisymmetry cycles (validating strict DAG order) and empty/duplicate elements.
- `zeta_matrix()` and `mobius_matrix()` return unboxed `SparseMatrix[T, T, int]` compatible directly with `algebrax.matrix` and `EP-0231`.

### 5. `FiniteLattice[T]` & Canonical Constructions (`_finite.py`, `_families.py`)

```python
class FiniteLattice(Generic[T]):
    r"""Immutable finite complete lattice $(L, \vee, \wedge, \bot, \top)$ satisfying CompleteLattice."""

    @classmethod
    def from_poset(cls, poset: FinitePoset[T]) -> FiniteLattice[T]: ...

    @property
    def poset(self) -> FinitePoset[T]: ...
    @property
    def elements(self) -> tuple[T, ...]: ...
    @property
    def bot(self) -> T: ...
    @property
    def top(self) -> T: ...
    def join(self, a: T, b: T) -> T: ...
    def meet(self, a: T, b: T) -> T: ...
    def join_all(self, elements: Iterable[T]) -> T: ...
    def meet_all(self, elements: Iterable[T]) -> T: ...
    def leq(self, a: T, b: T) -> bool: ...
    def dual(self) -> FiniteLattice[T]: ...
    def atoms(self) -> tuple[T, ...]: ...
    def coatoms(self) -> tuple[T, ...]: ...
    def join_irreducibles(self) -> tuple[T, ...]: ...
    def meet_irreducibles(self) -> tuple[T, ...]: ...
    def find_n5_witness(self) -> tuple[T, T, T, T, T] | None: ...
    def find_m3_witness(self) -> tuple[T, T, T, T, T] | None: ...
    def is_modular(self) -> bool: ...
    def is_distributive(self) -> bool: ...
    def is_complemented(self) -> bool: ...
    def is_atomistic(self) -> bool: ...
    def is_upper_semimodular(self) -> bool: ...
    def is_geometric(self) -> bool: ...
    def birkhoff_dual(self) -> FinitePoset[T]: ...


def dedekind_macneille(poset: FinitePoset[T]) -> FiniteLattice[frozenset[T]]: ...
```

Canonical families in `_families.py`:
- `chain_lattice(n: int) -> FiniteLattice[int]`
- `power_set_lattice(ground: Sequence[T]) -> FiniteLattice[frozenset[T]]`
- `divisor_lattice(n: int) -> FiniteLattice[int]`
- `diamond_m3() -> FiniteLattice[str]`
- `pentagon_n5() -> FiniteLattice[str]`
- `partition_lattice(n: int) -> FiniteLattice[tuple[frozenset[int], ...]]`
- `subgroup_lattice(group: FiniteGroup[G]) -> FiniteLattice[frozenset[G]]`
- `subspace_lattice_fq(dim: int, prime: int) -> FiniteLattice[frozenset[tuple[int, ...]]]` (using `algebrax.algebra.ModularField(prime)`)

### 6. Verification & Registry Integration (`algebrax.verification`, `algebrax.registry`)

- Add `verify_poset_laws`, `verify_lattice_laws`, `verify_modular_laws`, `verify_distributive_laws`, `verify_birkhoff_duality`, and `verify_rota_mobius_inversion` to `algebrax.verification`.
- Register canonical lattice structures (`diamond_m3`, `pentagon_n5`, `divisor_lattice(12)`, `power_set_lattice`, `partition_lattice`) in `algebrax.registry` (`EP-0255`).

---

## Backwards Compatibility

- **100% Backwards-Compatible Imports:** `from algebrax.lattice import join, meet, average, combine, ...` continues working identically via re-exports from `algebrax.lattice._mapping`.
- **Intentional Soundness Fix on `DistributiveLattice`:** Code checking `isinstance(obj, DistributiveLattice)` will now return `False` for duck-typed classes that do not declare `LawDistributive` (`is_distributive_law = True`). Since zero concrete classes in `src/algebrax/` previously implemented `DistributiveLattice`, no existing AlgebraX structure breaks.

---

## How to Teach This / Documentation Plan

1. Upgrade `docs/guide/algebra/lattices_and_order.md` with runnable examples for `FinitePoset`, `FiniteLattice`, Hasse covers, Birkhoff $M_3$/$N_5$ witness diagnostics, Dedekind–MacNeille completion, subgroup/subspace lattices, and Rota Möbius inversion.
2. Add AMDS mathematical docstrings (`EP-0002`) and Jupyter `_repr_html_()` Hasse summaries (`RichDisplayable`, HTML-escaped per `EP-0254`).
3. Cross-link `EP-0231` so Boolean FZT/FMT and general poset Zeta/Möbius transforms share `FinitePoset` as their canonical substrate.

---

## Reference Implementation

- **Research Compendium:** [`references/explorations/EXP-0013-lattice-and-order-continent/README.md`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md)
- **Z3 Separation Suite:** [`references/explorations/EXP-0013-lattice-and-order-continent/sources/z3_lattice_verifier.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/sources/z3_lattice_verifier.py) ($M_3$ and $N_5$ minimal order-5 proofs)
- **Zero-Dependency Prototype:** [`playground/lattice_continent_prototype.py`](https://github.com/erivlis/algebrax/blob/main/playground/lattice_continent_prototype.py) (Region I & Region V live verification on `D_12`, `4-Crown`, `Sub(S_3)`, `Sub(D_4)`, `Sub(A_4)`, $\Pi_4$, and Fano $PG(2, 2)$)

---

## Rejected Ideas

1. **Breaking Rename of `algebrax.lattice.py` to `algebrax.mapping`:**
   *Rejected*: Would break existing imports of `algebrax.lattice.average`, `join`, `meet`, `combine`, and recipes. Package promotion with `_mapping.py` re-exports achieves zero breakage.
2. **Deep Subclass Hierarchy (`FiniteLattice` → `FiniteModularLattice` → `FiniteDistributiveLattice`):**
   *Rejected*: Violates Shannon's Mode-vs-Type principle and creates brittle construction branches when a lattice's modularity is only known after inspection. A single `FiniteLattice` class with constructive property queries and optional certified view/protocol witnesses stays flat and composable.
3. **Graph-Library Dependency (`networkx`) for Poset Transitive Closure and Hasse Reduction:**
   *Rejected*: Violates AlgebraX's zero-dependency core invariant. Bitmask transitive closure and cover reduction in pure Python are ~30 LOC and orders of magnitude faster for finite lattices.

---

## Open Questions

- [ ] Should `FiniteLattice` expose explicit certified factory constructors (e.g., `as_distributive() -> FiniteDistributiveLattice` declaring `LawDistributive`) or keep law witnesses exclusively on specialized algebraic lattice classes (`FiniteHeytingAlgebra`, `FiniteBooleanAlgebra`)?
- [ ] What default element-count guardrail should `subgroup_lattice(group)` and `partition_lattice(n)` enforce (`n <= 8` for Bell $B_8 = 4140$) before requiring an explicit `max_elements` override?

---

## Change Log

* **2026-11-28:**
    * Initial Draft authored from `EXP-0013` as Phase 12 Wave 1 (scheduled ahead of Phase 10 `EP-0231`).
