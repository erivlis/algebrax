---
title: "EP-0250: Protocol Integrity, Law Witnesses & Algebraic Soundness"
description: "Restore strict mathematical soundness across algebraic law witnesses, GaloisField and CliffordAlgebra arithmetic, category/groupoid composition conventions, and Layer-2 protocol boundaries."
icon: lucide/scale
status: draft
---

# EP-0250: Protocol Integrity, Law Witnesses & Algebraic Soundness

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0250                                                                       |
| **Title**         | Protocol Integrity, Law Witnesses & Algebraic Soundness                    |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | ⚖️ Noether (Symmetry) & 🧩 Russell (Consistency)                           |
| **Status**        | Draft                                                                      |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-26                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal resolves all protocol, law-witness, and algebraic soundness contradictions uncovered during the Second Grand Council Codebase Audit. It corrects false `CommRing`/`LawAssociative` inheritance on non-commutative and non-associative algebras, fixes critical arithmetic defects in `GaloisField` (non-monic modulus reduction and irreducibility validation) and `CliffordAlgebra` (0- vs. 1-indexed signature contradiction), aligns reversed composition and residual conventions across `SimplicialPathGroupoid`, `Quasigroup`, `RelationActionAlgebra`, and `algebrax.group`, and decouples Layer-2 `algebra/` protocols from upward Layer-3 dependencies.

---

## Motivation

AlgebraX's core value proposition is that Python structural protocols (`CommRing`, `Field`, `HasStar`, `Category`, `Groupoid`) act as **truthful mathematical witnesses**. The codebase audit revealed several cases where concrete classes silently contradict the mathematical contracts they advertise:

1. **False Law Witnesses**: `MonoidAlgebra` unconditionally inherits `CommRing`, branding `CliffordAlgebra`, `GeneralizedCliffordAlgebra`, `QuantumCliffordAlgebra`, `PathAlgebra`, and non-abelian `GroupHopfAlgebra` with `is_commutative == True`. Similarly, `QuotientRing` unconditionally witnesses `CommRing`, and `QuotientAlgebra` (designed for Lie algebras modulo `LieIdeal`) inherits both `LawAssociative` and `LawCommutative` while crashing on `.one`.
2. **Silent Field & Clifford Arithmetic Corruption**:
   - `_gf_poly_mod` in `algebrax.algebra._field` omits the inverse leading coefficient `pow(irreduc_poly[-1], -1, p)`, causing every non-monic irreducible polynomial (e.g., $2x^2 + 1$ over $\mathbb{F}_3$) to return wrong multiplication results and broken inverses. `GaloisField.__init__` also accepts reducible polynomials such as $(x + 1)^2$ over $\mathbb{F}_2$.
   - `_clifford_blade_mul` in `algebrax.clifford` uses 1-based signature thresholds (`idx <= p`) with no lower-bound guard, while `geometric_product` and `rotor_rotation` docstrings prescribe 0-based blades `(0,), (1,)`. Consequently `CliffordAlgebra(0, 1, 0)` evaluates $e_0^2 = +1$ instead of $-1$, and out-of-range singletons like `{(99,): 1.0}` pass unchecked.
3. **Axiom Violations in Semirings**: `MinTimesSemiring` has `zero = inf` and returns `0.0` from `star(0.5)`, yielding `mul(0.0, inf) == nan != inf` (violating zero annihilation $a \otimes \mathbf{0} = \mathbf{0}$). `KCollapsedSemiring(0)` returns `one = 1` outside its carrier $\{0\}$.
4. **Inverted Composition & Residual Conventions**:
   - `SimplicialPathGroupoid.compose(g, f)` reverses both parameter names and composition order relative to `Category.compose(f, g)`, causing `cat.compose(p, cat.id(cat.target(p)))` to raise `ValueError`.
   - `group.compose` composes permutations left-to-right while `group.symmetric_mul` composes right-to-left within the same subpackage.
   - `Quasigroup.rdiv(a, b)` defines $y \cdot a = b$ ($b / a$), inverting `HasResiduals.rdiv(a, b)` ($a / b$), while `RelationActionAlgebra.rdiv(b, a)` swaps parameter names.
5. **Protocol & Layering Erosion**:
   - `DigitalSemiring`, `StringSemiring`, and `BivariateVarianceSemiring` define `star()` stubs that raise `NotImplementedError`, causing `isinstance(s, HasStar)` to return false positives.
   - `LieAlgebra` omits `HasBracket`, `LawAnticommutative`, and `LawLie`; `GroupRepresentation` and `LieRepresentation` inherit Layer-2 homomorphism protocols instead of composing flat Layer-1 mixins.
   - `category.Quiver` (method-based protocol) and `rep.quiver.Quiver` (dict-attribute dataclass) collide in name and structure, while Layer-2 `algebra/_path_algebra.py` and `algebra/_semiring.py` import upward into Layer-3 modules (`rep.quiver`, `clifford`, `semiring`, `display`).

---

## Rationale

Aligned with the Grand Council pillars:

- **⚖️ Emmy Noether (Symmetry)**: Every algebraic operation (`compose`, `rdiv`, `inv`, blade indexing) must obey one unambiguous convention across sibling modules; protocols must compose symmetrically without domain terminology leakage (`HasMorInv.inv` instead of `invert_path`).
- **🧩 Bertrand Russell (Consistency)**: Eliminate every logical paradox in the type/protocol lattice. A structure must never inherit `LawCommutative`, `LawAssociative`, `HasStar`, or `Field` unless every valid instance satisfies the corresponding axioms.
- **🔬 Karl Popper (Falsifiability)**: Adding Rabin irreducibility validation in `GaloisField.__init__`, explicit blade-index bounds in `CliffordAlgebra`, and explicit non-commutative base classes makes illegal states unrepresentable rather than silently producing corrupt outputs.
- **🌿 The Steward (Harmony)**: Where convention fixes touch existing public APIs (such as `SimplicialPathGroupoid.compose`, `HasMorInv`, or `CliffordAlgebra` indexing), provide clear migration guidance and preserve backwards-compatible aliases where safe.

---

## Specification

### 1. Truthful Ring, Algebra, and Quotient Law Witnesses
- **`src/algebrax/algebra/_monoid_algebra.py`**:
  - Remove `CommRing` from `MonoidAlgebra` base classes; inherit `MonoidAlgebraSemiring[K, T], Algebra[T, SparseVector[K, T]], Ring[SparseVector[K, T]]` (associative, not assumed commutative).
  - Keep `CommRing` strictly on provably commutative subclasses (`PolynomialAlgebra`, `MultivariatePolynomialAlgebra`, or an explicit `CommutativeMonoidAlgebra` / `is_commutative` check when both `coeff_ring` and `monoid` are commutative).
- **`src/algebrax/algebra/_quotient.py`**:
  - Change `QuotientRing` to inherit `QuotientSemiring[V], Ring[V], Generic[V]`; introduce `CommQuotientRing` (or dynamically expose commutativity only when `isinstance(base_ring, CommRing)`).
  - Change `QuotientAlgebra` to inherit `QuotientSemiring[V]` (or `NonAssocAlgebra[R, V]`) **without** `QuotientRing`/`CommRing`/`LawAssociative`, and do not require `.one` on non-unital Lie quotients.
- **`src/algebrax/algebra/_ideals.py`**:
  - Fix `NilpotentIdeal.reduce(element)` to return `0` (not `None`) for `int` carriers with `element >= nilpotency_degree`, satisfying `HasReduce[V]`.

### 2. Exact `GaloisField` Reduction & Irreducibility Verification
- **`src/algebrax/algebra/_field.py`**:
  - Normalize `irreduc_poly` to monic form upon construction (or multiply `factor` by `pow(irreduc_poly[-1], -1, p) % p` inside `_gf_poly_mod`).
  - Implement Rabin's irreducibility test over $\mathbb{F}_p[x]$ inside `GaloisField.__init__` (using repeated squaring $x^{p^k} \bmod f(x)$ and polynomial $\gcd$), raising `ValueError` if `irreduc_poly` is reducible over $\mathbb{F}_p$.

### 3. Canonical `CliffordAlgebra` Indexing & Validation
- **`src/algebrax/clifford.py`**:
  - Standardize on **1-based** generator indices $1 \le i \le p + q + r$ (matching mathematical convention $e_1, \dots, e_n$ and existing `Cl(p, q, r)` tests).
  - Enforce `1 <= idx <= p + q + r` on **every** blade index in `_clifford_blade_mul` (not only on adjacent duplicate indices), raising `ValueError` for `idx < 1` or `idx > p + q + r`.
  - Update `geometric_product` and `rotor_rotation` docstrings and examples to use consistent 1-based blade tuples `(1,), (2,)`.

### 4. Semiring Axiom Fixes & Clean `HasStar` Discipline
- **`src/algebrax/semiring/optimization.py`**:
  - Guard zero annihilation in `MinTimesSemiring.mul` (`if a == self.zero or b == self.zero: return self.zero`) and guard `inf + (-inf)` annihilation hazards in `TropicalSemiring`, `ArcticSemiring`, and `LogSemiring`.
- **`src/algebrax/semiring/structures.py`**:
  - Fix `KCollapsedSemiring(0).one` to return `0` (in-carrier identity when `k == 0`, matching `ModularSemiring(1)`).
- **`src/algebrax/semiring/{logic,structures,statistical}.py`**:
  - Remove `def star(...) -> ...: raise NotImplementedError(...)` stubs from `DigitalSemiring`, `StringSemiring`, and `BivariateVarianceSemiring` so `isinstance(s, HasStar)` is strictly truthful.
  - Equip genuine Kleene/star semirings (`ArcticSemiring`, `ViterbiSemiring`, `ReliabilitySemiring`, `BottleneckSemiring`, `MinTimesSemiring`, `LukasiewiczSemiring`, `StandardSemiring`, `LogSemiring`, `KCollapsedSemiring`) with `.plus()` and explicit `StarSemiring` / `KleeneAlgebra` conformance where mathematically valid.

### 5. Composition, Residual, and Groupoid Convention Alignment
- **`src/algebrax/topology/groupoid.py`**:
  - Change `SimplicialPathGroupoid.compose(self, f: PathMor, g: PathMor) -> PathMor` to diagrammatic order (`f[-1] == g[0]`, returning `f + g[1:]`), matching `Category.compose(f, g)`.
- **`src/algebrax/category/_mixins.py`**:
  - Rename `HasMorInv`'s canonical method to `inv(self, morphism: Mor) -> Mor` (retaining `invert_path` as a thin compatibility alias on `SimplicialPathGroupoid`).
- **`src/algebrax/algebra/_magma.py` & `_action.py`**:
  - Compose `HasResiduals[V]` into `Quasigroup` with consistent operand order (`rdiv(a, b)` solves $x \cdot b = a$, i.e. $a / b$) and align `RelationActionAlgebra.rdiv(self, a, b)` parameter names with `HasResiduals`.
- **`src/algebrax/group/`**:
  - Document and unify permutation multiplication order across `group.compose` and `group.symmetric_mul` (adding an explicit `order` convention or aligning `compose` to standard mathematical composition $f \circ g$ with a clear migration note).

### 6. Flat Protocol Composition & Layer-2 Decoupling
- **`src/algebrax/lie/core.py`**: Mix `HasBracket[LieElement]`, `LawAnticommutative`, and `LawLie` into `LieAlgebra`.
- **`src/algebrax/rep/group.py` & `rep/lie.py`**: Remove Layer-2-to-Layer-2 inheritance (`GroupRepresentation(GroupHom)`, `LieRepresentation(LieAlgebraHom)`) in favor of flat Layer-1 capability mixins; type `LieRepresentation` over Lie algebra elements rather than raw generator indices.
- **`src/algebrax/category/core.py` vs. `src/algebrax/rep/quiver.py` & `algebra/_path_algebra.py`**:
  - Give `rep.quiver.Quiver` method-based `source(arrow)` / `target(arrow)` protocol compatibility with `category.Quiver` (e.g., store mappings as `_source`/`_target` or expose a `QuiverProtocol` in `algebra/` so `PathAlgebra` depends on Layer-1/2 protocols rather than Layer-3 `rep.quiver`).
- **`src/algebrax/algebra/_semiring.py`**:
  - Extract `Semiring.catalog()` discovery/registration into a dedicated Layer-3 registry module (e.g., `algebrax.semiring._registry`), keeping a lazy delegator on `Semiring.catalog()` so `algebra/` contains zero upward imports into `clifford/`, `semiring/`, or `display.py`.

---

## Backwards Compatibility

- **Breaking changes (intentional bug/convention fixes)**:
  - `isinstance(CliffordAlgebra(...), CommRing)` and `isinstance(PathAlgebra(...), CommRing)` change from `True` (bug) to `False`.
  - `SimplicialPathGroupoid.compose(f, g)` switches from right-to-left `(g, f)` to diagrammatic `(f, g)` to satisfy `Category` axioms.
  - `GaloisField(p, reducible_poly)` now raises `ValueError` at construction time.
  - `CliffordAlgebra` rejects blade index `0` or out-of-range indices with `ValueError`.
  - `DigitalSemiring`, `StringSemiring`, and `BivariateVarianceSemiring` no longer implement `.star()`.
- **Preserved compatibility**:
  - `SimplicialPathGroupoid.invert_path` kept as alias to `inv`.
  - `Semiring.catalog()` public method signature remains unchanged via lazy registry delegation.

---

## How to Teach This / Documentation Plan

- Update [`docs/guide/algebra/clifford_geometric_algebra.md`](../guide/algebra/clifford_geometric_algebra.md) to state the 1-based blade convention explicitly and add a counterexample for out-of-range indices.
- Update [`docs/guide/algebra/rings_and_fields.md`](../guide/algebra/rings_and_fields.md) with non-monic and reducible `GaloisField` examples.
- Update [`docs/guide/discrete/category.md`](../guide/discrete/category.md) and [`docs/guide/algebra/quivers_and_gabriel.md`](../guide/algebra/quivers_and_gabriel.md) to document unified diagrammatic composition and `Quiver` protocol conformance.
- Update [`docs/guide/algebra/groups_and_symmetries.md`](../guide/algebra/groups_and_symmetries.md) to clarify permutation composition order.

---

## Reference Implementation

No code merged yet; key target files identified in the Second Grand Council Audit:
- `src/algebrax/algebra/{_field.py,_monoid_algebra.py,_quotient.py,_ideals.py,_magma.py,_action.py,_semiring.py,_path_algebra.py}`
- `src/algebrax/clifford.py`, `src/algebrax/semiring/{optimization.py,structures.py,logic.py,statistical.py}`
- `src/algebrax/topology/groupoid.py`, `src/algebrax/category/_mixins.py`, `src/algebrax/lie/core.py`, `src/algebrax/rep/{group.py,lie.py,quiver.py}`

---

## Rejected Ideas

1. **Dynamic `is_commutative` Property While Keeping `CommRing` Inheritance**:
   - *Rejected*: Violates Russell's consistency principle. Static type checkers (`pyrefly`) and `isinstance(alg, CommRing)` checks would still classify Clifford and Path algebras as commutative rings.
2. **Making `CliffordAlgebra` 0-Based Instead of 1-Based**:
   - *Rejected*: Existing `Cl(p, q, r)` unit tests, literature notation ($e_1, \dots, e_p, e_{p+1}, \dots, e_{p+q}$), and `_clifford_blade_mul`'s threshold math are all 1-based; only two helper docstrings drifted to 0-based examples.
3. **Runtime Toggle for `SimplicialPathGroupoid` Composition Order**:
   - *Rejected*: Violates Noether's symmetry and creates mode-flag confusion; every `Category` in `algebrax.category` already uses diagrammatic `(f, g)` order.

---

## Open Questions

- [ ] Should `algebrax.group.compose` change to right-to-left ($f \circ g$) to match `symmetric_mul`, or should `symmetric_mul` switch to left-to-right to match `Category.compose`?
- [ ] Should `GaloisField.__init__` expose an opt-out `validate_irreducible: bool = True` for benchmarking very high-degree pre-validated polynomials?

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Noether, Russell, Popper).
