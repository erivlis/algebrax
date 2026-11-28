---
title: "EP-0262: Non-Classical & Quantum Logics — Heyting Locales, MV-Algebras & Orthomodular Lattices"
description: "Add flat Layer-2 protocols and concrete zero-dependency implementations for Heyting algebras, Alexandroff locales, Lukasiewicz MV-algebras, Birkhoff-von Neumann orthomodular quantum lattices, and residuated lattices."
icon: lucide/sparkles
status: draft
---

# EP-0262: Non-Classical & Quantum Logics — Heyting Locales, MV-Algebras & Orthomodular Lattices

| Field             | Value                                                                                          |
|:------------------|:-----------------------------------------------------------------------------------------------|
| **EP**            | 0262                                                                                           |
| **Title**         | Non-Classical & Quantum Logics — Heyting Locales, MV-Algebras & Orthomodular Lattices          |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                    |
| **Sponsor**       | Core Maintainers                                                                               |
| **Delegate**      | ⚖️ Noether (Residuation & Duality), 🧩 Russell (Flat Logic Protocols) & 🔬 Popper (Z3 Oracles) |
| **Status**        | Draft                                                                                          |
| **Type**          | Standards Track                                                                                |
| **Created**       | 2026-11-28                                                                                     |
| **Updated**       | 2026-11-28                                                                                     |
| **Replaces**      | —                                                                                              |
| **Superseded-By** | —                                                                                              |

---

## Abstract

This proposal delivers **Phase 12, Wave 3** on top of [`EP-0260`](EP-0260-lattice-protocol-soundness-finite-posets-and-lattices.md) and [`EP-0261`](EP-0261-galois-connections-tarski-fixpoints-and-formal-concept-analysis.md), expanding AlgebraX into intuitionistic, many-valued, substructural, and quantum logics. It introduces flat Layer-2 protocols (`HeytingAlgebra`, `Ortholattice`, `OrthomodularLattice`, `ResiduatedLattice`, `MVAlgebra`) in `algebrax.algebra._lattice` and concrete implementations in `algebrax.lattice._logic`: `FiniteHeytingAlgebra` & Alexandroff locales $\mathcal{O}(P)$, `LukasiewiczMVAlgebra` (bridging `LukasiewiczSemiring`), `FiniteOrtholattice` (with constructive Benzene $O_6$ failure witnesses, Sasaki projections, and spin-$\frac{1}{2}$ $MO_k$ quantum lattices), and `FiniteResiduatedLattice` (including the Z3-discovered minimal non-distributive integral commutative witness $RL_6 = N_5 \oplus 1$).

---

## Motivation

Classical Boolean logic is only one corner of algebraic logic. Modern type theory, pointless topology, fuzzy reasoning, and quantum mechanics all replace Boolean axioms with strictly weaker order-theoretic laws:

1. **Intuitionistic Logic & Pointless Topology:** Dropping the law of excluded middle ($a \vee \neg a = \top$) yields **Heyting algebras** and **Locales**, where implication $a \to b$ is the right adjoint to meet ($a \wedge x \le b \iff x \le a \to b$). Every finite poset $P$ canonically generates an Alexandroff open-set locale $\mathcal{O}(P)$, yet AlgebraX currently offers no `HeytingAlgebra` or `Locale` structure.
2. **Unbridged Łukasiewicz Logic Semiring:** `algebrax.semiring.logic.LukasiewiczSemiring` provides truncated Łukasiewicz arithmetic without its residuated implication $a \to b = \min(1, 1 - a + b)$, Chang's `MVAlgebra` axioms, or exact rational/finite-chain $\L_n$ variants.
3. **Quantum Logic (Birkhoff–von Neumann):** Quantum propositions (closed subspaces of a Hilbert space) fail distributivity and satisfy the weaker **orthomodular law** ($a \le b \implies b = a \vee (a^\perp \wedge b)$). AlgebraX models quantum groups (`EP-0215`) and Hilbert spaces (`EP-0205`), but lacks orthomodular lattices, Sasaki projections, and constructive $O_6$ falsifiers.
4. **Substructural Residuated Lattices:** Generalizing Heyting implication from $\wedge$ to an arbitrary monoidal product $\cdot$ yields **Residuated Lattices**, directly bridging `algebrax.lattice` to `algebrax.algebra.ActionAlgebra` (`EP-0198`) and quantales (`EP-0264`).

---

## Rationale

Validated in [**EXP-0013**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) with machine-verified **Z3 5.4.1** variety-separation proofs:
- **$H_3$ (3-Chain $C_3$):** Minimal non-Boolean Heyting algebra (`n=2 UNSAT`, `n=3 SAT` in `0.033s`).
- **$O_6$ (Benzene):** Minimal non-orthomodular ortholattice (`n=4, 5 UNSAT`, `n=6 SAT` in `0.214s`).
- **$RL_6$ ($N_5 \oplus 1$):** Minimal non-distributive integral commutative residuated lattice (`n=4, 5 UNSAT`, `n=6 SAT` in `0.757s` — proving residuation at $\top = \mathbf{1}$ forces lifting $\top$ one step above $N_5$).

Grand Council alignment:
- **⚖️ Emmy Noether (Residuation as Universal Adjunction):**
  Heyting implication ($\wedge \dashv \to$), Łukasiewicz MV-implication ($\odot \dashv \to$), and general residuation ($\cdot \dashv \backslash, /$) are all instances of Galois adjunctions from `EP-0261`. Double-negation $\neg\neg$ on any `FiniteHeytingAlgebra` connects directly to `tarski_fixpoints` (`EP-0261`) to recover its canonical Boolean skeleton.
- **🧩 Bertrand Russell (Strict Flat Protocol Composition):**
  All five new Layer-2 protocols compose directly from Layer-1 atoms (`HasJoin`, `HasMeet`, `HasBounds`, `HasImplication`, `HasOrthocomplement`, `HasMul`, `HasOne`, `HasResiduals`, `LawDistributive`, `LawOrthomodular`, `LawAssociative`) with zero diamond MROs (`EP-0005`).
- **🔬 Karl Popper (Constructive Quantum Falsification & Exact Arithmetic):**
  `FiniteOrtholattice.find_o6_witness()` returns the exact violating triple/sublattice whenever orthomodularity fails (e.g., `('a', 'b', 'a')` on $O_6$). `LukasiewiczMVAlgebra` supports exact `Fraction` and discrete $\L_n$ modes alongside `float` (avoiding float drift in axiomatic proofs, per `EP-0253`).

---

## Specification

### 1. Flat Layer-2 Logic Protocols (`src/algebrax/algebra/_lattice.py`)

```python
@runtime_checkable
class HeytingAlgebra(
    HasJoin[V], HasMeet[V], HasBounds[V], HasImplication[V], LawModular, LawDistributive, Protocol
):
    r"""Intuitionistic Heyting algebra $\langle V, \vee, \wedge, \bot, \top, \to \rangle$."""

    def pseudo_complement(self, a: V) -> V:
        """Intuitionistic negation $\neg a = a \to \bot$."""
        return self.implies(a, self.bot)


@runtime_checkable
class Ortholattice(HasJoin[V], HasMeet[V], HasBounds[V], HasOrthocomplement[V], Protocol):
    r"""Bounded lattice with order-reversing involutive orthocomplement $a^\perp$."""
    ...


@runtime_checkable
class OrthomodularLattice(
    HasJoin[V], HasMeet[V], HasBounds[V], HasOrthocomplement[V], LawOrthomodular, Protocol
):
    r"""Birkhoff–von Neumann quantum logic lattice satisfying $a \le b \implies b = a \vee (a^\perp \wedge b)$."""
    ...


@runtime_checkable
class ResiduatedLattice(
    HasJoin[V], HasMeet[V], HasBounds[V], HasMul[V], HasOne[V], HasResiduals[V], LawAssociative, Protocol
):
    r"""Lattice-ordered monoid with left and right residuals ($a \cdot x \le b \iff x \le a \backslash b$)."""
    ...


@runtime_checkable
class MVAlgebra(
    HasJoin[V], HasMeet[V], HasBounds[V], HasMul[V], HasOne[V], HasImplication[V], HasComplement[V],
    LawAssociative, LawCommutative, LawModular, LawDistributive, Protocol
):
    r"""Chang MV-algebra for Łukasiewicz many-valued logic ($a \to b = \neg a \oplus b$, $a \vee b = (a \to b) \to b$)."""
    ...
```

### 2. Concrete Non-Classical & Quantum Logics (`src/algebrax/lattice/_logic.py`)

```python
class FiniteHeytingAlgebra(Generic[T]):
    r"""Finite Heyting algebra / Locale derived automatically from any finite distributive lattice."""

    def __init__(self, lattice: FiniteLattice[T]) -> None: ...  # Raises ValueError if non-distributive
    def join(self, a: T, b: T) -> T: ...
    def meet(self, a: T, b: T) -> T: ...
    def implies(self, a: T, b: T) -> T: ...
    def pseudo_complement(self, a: T) -> T: ...
    def double_negation(self, a: T) -> T: ...
    def is_boolean(self) -> bool: ...
    def boolean_skeleton(self) -> FiniteLattice[T]: ...  # Tarski fixpoints of double_negation


def alexandroff_locale(poset: FinitePoset[T]) -> FiniteHeytingAlgebra[frozenset[T]]:
    r"""Construct the Alexandroff open-set locale $\mathcal{O}(P)$ of upper sets / order ideals of $P$."""
    ...


class LukasiewiczMVAlgebra(Generic[V]):
    r"""Łukasiewicz MV-algebra over continuous $[0, 1]$ (`float`), exact `Fraction`, or finite chain $\L_n$.

    Bridges `algebrax.semiring.logic.LukasiewiczSemiring` with exact residuated implication.
    """

    def __init__(self, *, exact: bool = False, steps: int | None = None) -> None: ...
    def join(self, a: V, b: V) -> V: ...
    def meet(self, a: V, b: V) -> V: ...
    def mul(self, a: V, b: V) -> V: ...        # Strong conjunction a ⊙ b = max(0, a + b - 1)
    def oplus(self, a: V, b: V) -> V: ...      # Strong disjunction a ⊕ b = min(1, a + b)
    def implies(self, a: V, b: V) -> V: ...    # Residuated implication min(1, 1 - a + b)
    def complement(self, a: V) -> V: ...       # Involution 1 - a


class FiniteOrtholattice(Generic[T]):
    r"""Finite orthocomplemented lattice with Birkhoff–von Neumann orthomodularity witness."""

    def __init__(self, lattice: FiniteLattice[T], ortho_map: Mapping[T, T]) -> None: ...
    def ortho(self, a: T) -> T: ...
    def find_o6_witness(self) -> tuple[T, T, T] | None: ...
    def is_orthomodular(self) -> bool: ...
    def commutes(self, a: T, b: T) -> bool:
        r"""Quantum compatibility relation $a \mathbin{C} b \iff a = (a \wedge b) \vee (a \wedge b^\perp)$."""
        ...
    def sasaki_hook(self, a: T, b: T) -> T:
        r"""Quantum Sasaki implication $a \to_S b = a^\perp \vee (a \wedge b)$."""
        ...
    def sasaki_projection(self, a: T, b: T) -> T:
        r"""Quantum Sasaki projection $\varphi_a(b) = a \wedge (a^\perp \vee b)$."""
        ...


class FiniteResiduatedLattice(Generic[T]):
    r"""Finite associative lattice-ordered monoid with auto-derived exact Galois residuals."""

    def __init__(
        self,
        lattice: FiniteLattice[T],
        mul_table: Mapping[tuple[T, T], T],
        one: T,
    ) -> None: ...

    def mul(self, a: T, b: T) -> T: ...
    def ldiv(self, a: T, b: T) -> T: ...
    def rdiv(self, a: T, b: T) -> T: ...
    def is_integral(self) -> bool: ...
    def is_commutative_monoid(self) -> bool: ...
```

Canonical constructors in `_logic.py`:
- `heyting_chain(n: int) -> FiniteHeytingAlgebra[int]` (`n = 3` gives minimal non-Boolean $H_3$)
- `benzene_o6() -> FiniteOrtholattice[str]` (minimal non-orthomodular ortholattice $O_6$)
- `chinese_lantern_mo(k: int) -> FiniteOrtholattice[str]` (spin-$\frac{1}{2}$ modular orthomodular quantum lattice $MO_k$, $k \ge 2$)
- `rl6_n5_plus_1() -> FiniteResiduatedLattice[str]` (Z3-verified minimal non-distributive integral commutative residuated lattice $N_5 \oplus 1$)

### 3. Verification Oracles (`src/algebrax/verification/`)

- `verify_heyting_laws(alg, samples)` (adjunction $a \wedge x \le b \iff x \le a \to b$, pseudo-complement, Glivenko $\neg\neg$-skeleton).
- `verify_mv_algebra_laws(alg, samples)` (Wajsberg axiom $(a \to b) \to b = (b \to a) \to a$, residuation, involutive negation).
- `verify_ortholattice_laws(alg, samples)` & `verify_orthomodular_laws(alg, samples)` (involution, De Morgan antitonicity, orthomodularity + Sasaki adjunction $\varphi_a(b) \le c \iff b \le a \to_S c$).
- `verify_residuated_lattice_laws(alg, samples)` (monoid associativity/unit, bilateral Galois residuation).

---

## Backwards Compatibility

Strictly additive. Existing `LukasiewiczSemiring` and `BooleanSemiring` in `algebrax.semiring.logic` remain unchanged; `LukasiewiczMVAlgebra` provides an explicit bridge without altering semiring carriers.

---

## How to Teach This / Documentation Plan

1. Add a **"Non-Classical & Quantum Logics"** guide section comparing Boolean, Intuitionistic ($H_3$ / Alexandroff locales), Łukasiewicz MV, and Quantum ($O_6$ vs. $MO_2$ compatibility & Sasaki projections) truth tables side by side.
2. Add a Tier-4 recipe illustrating quantum non-distributivity on spin-$\frac{1}{2}$ propositions ($MO_2$) versus classical Boolean measurement contexts.

---

## Reference Implementation

- **Research Compendium:** [`references/explorations/EXP-0013-lattice-and-order-continent/README.md`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/README.md) (Sections 2.1 & 2.2, Region III)
- **Z3 Separation Suite:** [`references/explorations/EXP-0013-lattice-and-order-continent/sources/z3_lattice_verifier.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0013-lattice-and-order-continent/sources/z3_lattice_verifier.py) ($H_3, O_6, RL_6$)
- **Zero-Dependency Prototype:** [`playground/lattice_continent_prototype.py`](https://github.com/erivlis/algebrax/blob/main/playground/lattice_continent_prototype.py)

---

## Rejected Ideas

1. **Mutating `LukasiewiczSemiring` In-Place to Implement `MVAlgebra`:**
   *Rejected*: `LukasiewiczSemiring` uses `add = min(1, a + b)` and `mul = max(0, a + b - 1)` under the `Semiring` protocol (`zero=0.0, one=1.0`), whereas an `MVAlgebra` also exposes lattice `join = max`, `meet = min`, `implies`, and `complement`. Keeping `LukasiewiczMVAlgebra` as a dedicated bridge preserves clean separation between semirings and lattices.
2. **Representing Orthomodular Quantum Lattices via Floating-Point Dense Hilbert Projectors:**
   *Rejected*: Floating-point projection tolerances cannot reliably decide exact lattice equalities. Finite ortholattices ($O_6, MO_k$) and exact finite-field/rational orthogonal subspace lattices remain bit-exact and zero-dependency.

---

## Open Questions

- [ ] Should `FiniteOrtholattice` expose an `as_orthomodular()` certified view (declaring `LawOrthomodular`) or return a lightweight subclass `FiniteOrthomodularLattice` when `is_orthomodular()` is verified?
- [ ] Should `LukasiewiczMVAlgebra` also provide a `from_semiring(LukasiewiczSemiring)` classmethod?

---

## Change Log

* **2026-11-28:**
    * Initial Draft authored from `EXP-0013` as Phase 12 Wave 3.
