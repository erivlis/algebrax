---
title: "EP-0264: Quantales, Scott Domains & Subtraction-Free Non-Associative Quantales"
description: "Unify ActionAlgebras with complete Quantales and Scott domains, add missing equational law witnesses (LawFlexible, LawMoufang, LawCocommutative, HasConvStar), and ship EXP-0012's subtraction-free Jordan, Alternative/Moufang, Kleene-Hopf, and Unital-Drift structures and falsification benchmarks."
icon: lucide/atom
status: draft
---

# EP-0264: Quantales, Scott Domains & Subtraction-Free Non-Associative Quantales

| Field             | Value                                                                                              |
|:------------------|:---------------------------------------------------------------------------------------------------|
| **EP**            | 0264                                                                                               |
| **Title**         | Quantales, Scott Domains & Subtraction-Free Non-Associative Quantales                              |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                        |
| **Sponsor**       | Core Maintainers                                                                                   |
| **Delegate**      | 🧭 Explorer (`EXP-0012` Frontier), ⚖️ Noether (Quantale & Bialgebra Duality) & 🔬 Popper (Oracles) |
| **Status**        | Draft                                                                                              |
| **Type**          | Standards Track                                                                                    |
| **Created**       | 2026-11-28                                                                                         |
| **Updated**       | 2026-11-28                                                                                         |
| **Replaces**      | —                                                                                                  |
| **Superseded-By** | —                                                                                                  |

---

## Abstract

This proposal completes **Phase 12 (Wave 5)** by uniting the order-theoretic continent ([`EXP-0013`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md)) with the subtraction-free idempotent frontier discovered in [`EXP-0012`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0012-subtraction-free-idempotent-corners/README.md). It adds four independent Layer-1 mixins (`LawFlexible`, `LawMoufang`, `LawCocommutative`, `HasConvStar`) to `algebrax.algebra._mixins`, hardens `ActionAlgebra` associativity soundness, introduces flat Layer-2 protocols (`Quantale`, `JordanQuantale`, `AlternativeQuantale`, `FlexibleAlternativeQuantale`, `MoufangQuantale`, `Semibialgebra`, `KleeneHopfBialgebra`), and delivers `FiniteQuantale`, `ScottDomain`, `TropicalMatrixJordanQuantale`, subtraction-free `KleeneHopfBialgebra` models, and the Z3-verified minimal falsification benchmark suite ($J_4, E_5, A_5, F_5, M_7, D_3, DK_4$) in `algebrax.lattice._quantale` and `algebrax.verification`.

---

## Motivation

Two independent explorations (`EXP-0012` and `EXP-0013`) converged on the exact same architectural capstone: **Quantales**—complete lattices equipped with a join-preserving product—are the bridge connecting order theory (`EP-0260`–`EP-0262`) to Kleene/Action algebras (`EP-0197`, `EP-0198`), non-associative algebras (`EP-0204`), Hopf bialgebras (`EP-0206`), and derivations (`EP-0240`):

1. **Associativity Blindness on `ActionAlgebra` (Discovered in `EXP-0012`):**
   `ActionAlgebra` (`EP-0198`) documents Pratt's pure induction invariant $(a \backslash a)^* \le a \backslash a$, yet omits `LawAssociative`. Consequently, strictly non-associative models—including the 5-element exceptional Jordan quantale $E_5$ that **explicitly violates Pratt's pure induction**—falsely pass `isinstance(E_5, ActionAlgebra)` at runtime.
2. **Over-Coupled `HasNeg` / `HasScale` on Non-Associative & Coalgebraic Protocols:**
   `JordanAlgebra`, `AlternativeAlgebra`, `Coalgebra`, `Bialgebra`, and `HopfAlgebra` require `HasNeg` and `HasScale`, locking out subtraction-free idempotent counterparts (Jordan quantales, alternative/Moufang quantales, and Kleene–Hopf semibialgebras).
3. **Missing Independent Law Witnesses in Subtraction-Free Algebra:**
   Z3 finite-model synthesis in `EXP-0012` proved that dropping `HasNeg` shatters Artin's 1931 theorem into three strictly separated tiers ($A_5 \subsetneq F_5 \subsetneq M_7$) and creates a sharp 2×2 phase diagram for Kleene–Hopf convolution stars $\circledast$ depending on commutativity and cocommutativity.
4. **No Quantale or Domain-Theory Primitives:**
   AlgebraX has no `FiniteQuantale` or `ScottDomain` implementation bridging `FiniteLattice`, residuated closure, and Scott-continuous fixed-point semantics.

---

## Rationale

Directly grounded in machine-verified **Z3 5.4.1** theorems from [**EXP-0012**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0012-subtraction-free-idempotent-corners/README.md):

- **Corner 1 — Kleene–Hopf Bialgebras (2×2 Phase Diagram):** Replacing the alternating Takeuchi antipode with the convolution Kleene star $\circledast = \bigoplus_{n \ge 0} \mu^{(n)} \circ \Delta^{(n)}$ yields exact idempotence $\circledast^2 = \circledast$ strictly on the semi-commutative L-boundary (commutative or cocommutative); on the fully non-commutative matrix bialgebra $\mathcal{O}_{\mathrm{nc}}(M_2)$, $\circledast(e_{ij})$ generates all $i \to j$ walks while $\circledast^2$ jumps to 2-strand braided walks.
- **Corner 2 — Jordan Quantales & Exceptional $E_5$:** The Endomorphism-Square Specialness Theorem proves that Pratt's pure induction $(a \multimap_\circ a)^2 \le (a \multimap_\circ a)$ holds for *every* special Jordan quantale embedding into $Q^+$ ($a \circ b = ab \oplus ba$), while $E_5$ (`n=4 UNSAT`, `n=5 SAT` on $N_5$) violates it—acting as a 5-element subtraction-free Albert algebra.
- **Corner 3 — 3-Tier Shattered Artin–Moufang Hierarchy:** $A_5$ (alternative, non-flexible; `n=4 UNSAT`), $F_5$ (flexible-alternative, non-Moufang; `n=4 UNSAT`), and $M_7$ (Moufang + 2-generator associative, non-associative; `n=6 chain UNSAT`, `n=7 SAT`) prove `LawAlternative`, `LawFlexible`, `LawMoufang`, and `LawAssociative` are strictly distinct without `HasNeg`.
- **Corner 4 — Unital-Drift Differential–Kleene Law:** On idempotent semirings with a positive Leibniz derivation $D$, $D(\mathbf{1})$ need not vanish ($D_3$, $DK_4$), modifying naive star commutation into the exact conservation law $D^*(a^*) = D^*(\mathbf{1}) \cdot (D^*(a))^*$.

Grand Council alignment:
- **🧩 Bertrand Russell:** Zero-diamond flat protocols (`EP-0005`); distinguishes multiplicative `HasStar` (`star`) from convolution `HasConvStar` (`conv_star`) so Kleene–Hopf bialgebras never collide with multiplicative Kleene stars.
- **🔬 Karl Popper:** Registers $J_4, E_5, A_5, F_5, M_7, D_3, DK_4$ as deterministic, zero-dependency falsification fixtures verifying that AlgebraX's own verification suite rejects non-associative, non-special, non-flexible, and non-Moufang impostors.
- **⚡ Claude Shannon:** Zero external runtime dependencies; `z3-solver` stays strictly in `tests/verifications/` (`EP-0186`).

---

## Specification

### 1. New Layer-1 Mixins (`src/algebrax/algebra/_mixins.py`)

```python
@runtime_checkable
class HasConvStar(Protocol[V]):
    r"""Convolution Kleene star $\circledast = \bigoplus_{n \ge 0} \mu^{(n)} \circ \Delta^{(n)}$ on idempotent bialgebras."""

    def conv_star(self, a: V) -> V: ...


@runtime_checkable
class LawFlexible(Protocol):
    r"""Equational axiom witness: flexibility identity $(a \cdot b) \cdot a = a \cdot (b \cdot a)$."""

    @property
    def is_flexible(self) -> Literal[True]:
        return True


@runtime_checkable
class LawMoufang(Protocol):
    r"""Equational axiom witness: left, right, and middle Moufang identities."""

    @property
    def is_moufang(self) -> Literal[True]:
        return True


@runtime_checkable
class LawCocommutative(Protocol):
    r"""Coalgebraic axiom witness: cocommutative coproduct ($\tau \circ \Delta = \Delta$)."""

    @property
    def is_cocommutative(self) -> Literal[True]:
        return True
```

### 2. Flat Layer-2 Protocols & `ActionAlgebra` Soundness (`_lattice.py`, `_action.py`, `_non_assoc.py`, `_hopf.py`)

- **Soundness Hardening (`_action.py`):** Add `LawAssociative` to `ActionAlgebra` (and ensure `RelationActionAlgebra` and concrete action algebras declare `is_associative = True`) so non-associative structures like $E_5$ cannot falsely satisfy `isinstance(x, ActionAlgebra)`.
- **New Flat Layer-2 Protocols:**
  - `Quantale[V]`: `(HasJoin[V], HasMeet[V], HasBounds[V], HasMul[V], HasOne[V], HasResiduals[V], LawComplete, LawAssociative, Protocol)`
  - `JordanQuantale[V]`: `(HasZero[V], HasOne[V], HasAdd[V], HasMul[V], HasResiduals[V], HasStar[V], LawIdempotent, LawCommutative, LawJordan, Protocol)`
  - `AlternativeQuantale[V]`: `(HasZero[V], HasOne[V], HasAdd[V], HasMul[V], HasResiduals[V], LawIdempotent, LawAlternative, Protocol)`
  - `FlexibleAlternativeQuantale[V]`: `(..., LawAlternative, LawFlexible, Protocol)`
  - `MoufangQuantale[V]`: `(..., LawAlternative, LawFlexible, LawMoufang, Protocol)`
  - `Semibialgebra[V]`: `(HasZero[V], HasOne[V], HasAdd[V], HasMul[V], HasCoproduct[V], HasCounit[Any, V], LawIdempotent, Protocol)`
  - `KleeneHopfBialgebra[V]`: `(HasZero[V], HasOne[V], HasAdd[V], HasMul[V], HasCoproduct[V], HasCounit[Any, V], HasConvStar[V], LawIdempotent, Protocol)`

### 3. Concrete Quantales, Domains & `EXP-0012` Structures (`src/algebrax/lattice/_quantale.py`)

```python
class FiniteQuantale(Generic[T]):
    r"""Finite unital quantale $(Q, \bigvee, \cdot, \mathbf{1}, \backslash, /, ^*)$."""

    def __init__(
        self,
        lattice: FiniteLattice[T],
        mul_table: Mapping[tuple[T, T], T],
        one: T,
        *,
        require_associative: bool = True,
    ) -> None: ...

    def join(self, a: T, b: T) -> T: ...
    def join_all(self, elements: Iterable[T]) -> T: ...
    def mul(self, a: T, b: T) -> T: ...
    def ldiv(self, a: T, b: T) -> T: ...
    def rdiv(self, a: T, b: T) -> T: ...
    def star(self, a: T) -> T: ...
    def is_special_jordan_compatible(self) -> bool:
        r"""Evaluate Pratt's pure induction specialness criterion $(a \multimap_\circ a)^2 \le a \multimap_\circ a$."""
        ...


class ScottDomain(Generic[T]):
    r"""Finite Scott domain (bounded-complete algebraic dcpo) with way-below relation $x \ll y$
    and Scott-continuity verification for monotone maps.
    """

    def __init__(self, poset: FinitePoset[T]) -> None: ...
    def way_below(self, x: T, y: T) -> bool: ...
    def compact_elements(self) -> tuple[T, ...]: ...
    def is_scott_continuous(self, fn: Callable[[T], T]) -> bool: ...
    def kleene_fixpoint(self, fn: Callable[[T], T]) -> T: ...


class TropicalMatrixJordanQuantale:
    r"""Special Jordan quantale of $n \times n$ matrices over an idempotent semiring under $A \circ B = AB \oplus BA$,
    with symmetric Jordan residual $A \multimap_\circ C = (A \backslash C) \wedge (C / A)$.
    """

    def __init__(self, dim: int, semiring: Semiring[V] | None = None) -> None: ...
    def mul(self, a: SparseMatrix[int, int, V], b: SparseMatrix[int, int, V]) -> SparseMatrix[int, int, V]: ...
    def jdiv(self, a: SparseMatrix[int, int, V], c: SparseMatrix[int, int, V]) -> SparseMatrix[int, int, V]: ...
```

Canonical `EXP-0012` constructors & falsification fixtures:
- `j4_jordan_quantale()` (minimal 4-element non-associative special Jordan quantale)
- `e5_exceptional_jordan_quantale()` (minimal 5-element provably exceptional Jordan quantale on $N_5$)
- `a5_alternative_non_flexible()` (Tier 1 Artin-alternative quantale)
- `f5_flexible_non_moufang()` (Tier 2 flexible-alternative quantale)
- `m7_moufang_quantale()` (Tier 3 Moufang / 2-gen associative quantale)
- `dk4_unital_drift_kleene()` (idempotent differential–Kleene semiring with $D(\mathbf{1}) > \mathbf{0}$)
- `ShuffleDeconcatBialgebra`, `ConcatUnshuffleBialgebra`, and `NonCommMatrixBialgebra` ($\mathcal{O}_{\mathrm{nc}}(M_n)$)

### 4. Verification Oracles (`src/algebrax/verification/`)

- `verify_quantale_laws(q, samples)`: complete join-distributivity, bilateral residuation, and Kleene star fixed-point closure.
- `verify_jordan_quantale_laws(q, samples)` & `verify_jordan_specialness_criterion(q, samples)`: verifies Jordan identity, symmetric residuation, and Pratt's pure induction separator (passes $J_4$ & `TropicalMatrixJordanQuantale`, falsifies $E_5$).
- `verify_artin_moufang_tier(q, samples)`: classifies exact tier (`Alternative`, `Flexible`, `Moufang`, `Associative`).
- `verify_kleene_hopf_laws(b, samples)`: verifies convolution star unfold/induction laws and classifies the 2×2 lax/exact homomorphism quadrant.
- `verify_unital_drift_star_law(d, samples)`: verifies $D^*(a^*) = D^*(\mathbf{1}) \cdot (D^*(a))^*$.

---

## Backwards Compatibility

- **Intentional Soundness Hardening on `ActionAlgebra`:** Adding `LawAssociative` to `ActionAlgebra` requires concrete `ActionAlgebra` implementations to declare `is_associative = True`. All existing AlgebraX `ActionAlgebra` classes (`RelationActionAlgebra`, etc.) will be updated in lockstep so zero existing callers break.
- All new protocols and `algebrax.lattice._quantale` classes are strictly additive.

---

## How to Teach This / Documentation Plan

1. Add a **"Quantales, Scott Domains & Subtraction-Free Non-Associative Algebras"** section to `docs/guide/algebra/lattices_and_order.md` explaining the 3-tier Artin split ($A_5 \subsetneq F_5 \subsetneq M_7$), why $E_5$ is a 5-element subtraction-free Albert algebra, and how $\circledast$ generalizes Hopf antipodes to unbounded fork–join closures.
2. Add a Tier-4 recipe demonstrating tropical matrix Jordan quantales, $E_5$ specialness falsification, and path-language generation in $\mathcal{O}_{\mathrm{nc}}(M_2)$.

---

## Reference Implementation

- **Research Compendiums:**
  - [`references/explorations/EXP-0012-subtraction-free-idempotent-corners/README.md`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0012-subtraction-free-idempotent-corners/README.md)
  - [`references/explorations/EXP-0013-lattice-and-order-continent/README.md`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md)
- **Z3 Synthesis & Prototypes:**
  - [`references/explorations/EXP-0012-subtraction-free-idempotent-corners/sources/z3_corner_hunter.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0012-subtraction-free-idempotent-corners/sources/z3_corner_hunter.py)
  - [`playground/idempotent_corners_prototype.py`](https://github.com/erivlis/algebrax/blob/main/playground/idempotent_corners_prototype.py)

---

## Rejected Ideas

1. **Adding `LawAssociative` to the Base `Semiring` Protocol:**
   *Rejected*: Would break lightweight duck-typed third-party semirings that rely on `verify_semiring_laws` rather than explicit witness properties. Scoping `LawAssociative` to `ActionAlgebra` and `Quantale` closes the Pratt induction soundness hole without disrupting duck-typed semirings.
2. **Reusing `HasStar` (`star`) for Kleene–Hopf Convolution Star $\circledast$:**
   *Rejected*: A bialgebra can simultaneously possess a multiplicative Kleene star $a^*$ and a convolution star $\circledast(a)$. Introducing `HasConvStar` (`conv_star`) prevents method-name collision while staying flat under `EP-0005`.
3. **Shipping `z3-solver` as a Runtime Dependency for Model Synthesis:**
   *Rejected*: Violates AlgebraX's zero-dependency core invariant. All Z3 finite-model proofs remain optional dev-time verification tests (`tests/verifications/`), while the synthesized minimal witnesses ($J_4, E_5, A_5, F_5, M_7, D_3, DK_4$) ship as pure-Python finite tables.

---

## Open Questions

- [ ] Should `ShuffleDeconcatBialgebra` and `NonCommMatrixBialgebra` live in `algebrax.lattice._quantale` or in `algebrax.algebra._hopf` (co-located with `GroupHopfAlgebra` from `EP-0206` / `EP-0252`)?
- [ ] Should `dk4_unital_drift_kleene()` coordinate directly with Phase 11's `HasSkewDerivation` (`EP-0240`) so positive Leibniz derivations reuse `diff(a, var_index=0)` cleanly?

---

## Change Log

* **2026-11-28:**
    * Initial Draft authored from `EXP-0012` & `EXP-0013` as Phase 12 Wave 5.
