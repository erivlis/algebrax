---
title: "EP-0250: Protocol Integrity, Law Witnesses & Algebraic Soundness"
description: "Restore strict mathematical soundness across algebraic law witnesses, GaloisField and CliffordAlgebra arithmetic, category/groupoid composition conventions, and Layer-2 protocol boundaries."
icon: lucide/scale
status: accepted
---

# EP-0250: Protocol Integrity, Law Witnesses & Algebraic Soundness

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0250                                                                       |
| **Title**         | Protocol Integrity, Law Witnesses & Algebraic Soundness                    |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | ⚖️ Noether (Symmetry) & 🧩 Russell (Consistency)                           |
| **Status**        | Accepted                                                                   |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-27                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal resolves all protocol, law-witness, and algebraic soundness contradictions uncovered during the Second Grand Council Codebase Audit. It replaces false `CommRing`/`LawAssociative` inheritance on non-commutative and non-associative algebras with strict nominal subclasses (`CommQuotientRing`, `CommMonoidAlgebra`, `CommGrothendieckRing`), fixes critical arithmetic defects in `GaloisField` (non-monic modulus reduction and Rabin irreducibility validation) and `CliffordAlgebra` (1-based generator indexing and bounds validation), aligns reversed composition and residual conventions across `SimplicialPathGroupoid`, `Quasigroup`, `RelationActionAlgebra`, and `algebrax.group`, repairs inverted generic parameters in `NormedSpace`/`InnerProductSpace`, and cleanly decouples Layer-2 `algebra/` protocols from upward Layer-3 dependencies.

---

## Motivation

AlgebraX's core value proposition is that Python structural protocols (`CommRing`, `Field`, `HasStar`, `Category`, `Groupoid`) act as **truthful mathematical witnesses**. The codebase audit revealed several cases where concrete classes silently contradict the mathematical contracts they advertise:

1. **False Law Witnesses & Inverted Generics**:
   - `MonoidAlgebra` unconditionally inherits `CommRing`, branding `CliffordAlgebra`, `GeneralizedCliffordAlgebra`, `QuantumCliffordAlgebra`, `PathAlgebra`, and non-abelian `GroupHopfAlgebra` with `is_commutative == True`.
   - `QuotientRing` and `GrothendieckRing` unconditionally inherit `CommRing` even for non-commutative base structures, and `QuotientAlgebra` (designed for Lie algebras modulo `LieIdeal`) inherits both `LawAssociative` and `LawCommutative` while crashing on `.one`.
   - `PolynomialAlgebra` accepts any `Semiring[T]` (not necessarily a commutative ring) and must not unconditionally witness `CommRing`.
   - `NilpotentIdeal.reduce` currently accepts bare `int` degree exponents and returns `None` at or above `nilpotency_degree` (violating `HasReduce[V]`—and returning `0` for a degree exponent would falsely assert $\varepsilon^d \equiv \varepsilon^0 = 1$).
   - `NormedSpace` and `InnerProductSpace` in `algebra/_normed.py` place `HasZero[V]` before `HasScale[R, V]` without `Protocol[R, V]`, inverting `__parameters__` to `(V, R)`.
   - `Bialgebra`/`HopfAlgebra` omit `LawAssociative` (failing `isinstance(h, Algebra)`), and `PoissonAlgebra` omits `LawAssociative` and `LawLie`.
2. **Silent Field & Clifford Arithmetic Corruption**:
   - `_gf_poly_mod` in `algebrax.algebra._field` omits the inverse leading coefficient `pow(irreduc_poly[-1], -1, p)`, causing every non-monic irreducible polynomial (e.g., $2x^2 + 1$ over $\mathbb{F}_3$) to return wrong multiplication results and broken inverses. `GaloisField.__init__` also accepts reducible polynomials such as $(x + 1)^2$ over $\mathbb{F}_2$.
   - `_clifford_blade_mul` in `algebrax.clifford` uses 1-based signature thresholds (`idx <= p`) with no lower-bound guard, while `geometric_product` and `rotor_rotation` docstrings prescribe 0-based blades `(0,), (1,)`. Consequently `CliffordAlgebra(0, 1, 0)` evaluates $e_0^2 = +1$ instead of $-1$, and out-of-range singletons like `{(99,): 1.0}` pass unchecked.
3. **Axiom Violations in Semirings**:
   - `MinTimesSemiring` (`zero = inf`, `star(0.5) = 0.0`), `TropicalSemiring`, `ArcticSemiring`, and `LogSemiring` produce `NaN` when multiplying zero by $\pm\infty$, violating zero annihilation $a \otimes \mathbf{0} = \mathbf{0}$.
   - `KCollapsedSemiring(0)` returns `1` outside its carrier $\{0\}$ in `.one`, `power(a, 0)`, and `star(0)`, and lacks a `k < 0` guard.
4. **Inverted Composition & Residual Conventions**:
   - `SimplicialPathGroupoid.compose(g, f)` reverses both parameter names and composition order relative to `Category.compose(f, g)`, causing `cat.compose(p, cat.id(cat.target(p)))` to raise `ValueError`.
   - `HasMorInv` leaks domain-specific terminology (`invert_path`) instead of canonical `inv`.
   - `group.compose` composes permutations left-to-right while `group.symmetric_mul` composes right-to-left within the same subpackage.
   - `Quasigroup.rdiv(a, b)` defines $y \cdot a = b$ ($b / a$), inverting `HasResiduals.rdiv(a, b)` ($a / b$), while `RelationActionAlgebra.rdiv(b, a)` swaps parameter names.
5. **Protocol & Layering Erosion**:
   - `DigitalSemiring`, `StringSemiring`, and `BivariateVarianceSemiring` define `star()` stubs that raise `NotImplementedError`, causing `isinstance(s, HasStar)` to return false positives.
   - `LieAlgebra` omits `HasBracket`, `LawAnticommutative`, and `LawLie`; `GroupRepresentation` and `LieRepresentation` inherit Layer-2 homomorphism protocols instead of composing flat Layer-1 mixins.
   - `category.Quiver` (method-based protocol) and `rep.quiver.Quiver` (dict-attribute dataclass) collide in name and structure, while Layer-2 `algebra/` modules import upward into Layer-3 modules (`rep.quiver`, `semiring`, `matrix`, `display`).

---

## Rationale

Aligned with the Grand Council pillars:

- **⚖️ Emmy Noether (Symmetry)**: Every algebraic operation (`compose`, `rdiv`, `inv`, blade indexing) obeys one unambiguous convention across sibling modules; protocols compose symmetrically without domain terminology leakage (`HasMorInv.inv`, `FiniteQuiver` implementing `category.Quiver`).
- **🧩 Bertrand Russell (Consistency)**: Because Python's `@runtime_checkable` `isinstance(x, LawCommutative)` checks only attribute *existence* (never truthiness), equational distinctions **must** be expressed via distinct nominal classes (`QuotientRing` vs. `CommQuotientRing`, `MonoidAlgebra` vs. `CommMonoidAlgebra`, matching `FiniteGroup` vs. `FiniteCommGroup`).
- **🔬 Karl Popper (Falsifiability)**: Rabin irreducibility validation in `GaloisField.__init__`, strict 1-based blade bounds in `CliffordAlgebra`, and truthful `Law*`/`HasStar` conformance make illegal states unrepresentable rather than silently producing corrupt results.
- **⚡ Claude Shannon (Zero Overhead)**: Hoisting monic normalization into `GaloisField.__init__` and using module-level `_INF`/`_NEG_INF` constants in semiring `.mul` guards keeps inner-loop arithmetic allocation-free.
- **💡 Richard Feynman (Clean Cuts)**: No deprecated compatibility shims or half-measures; breaking convention fixes are made cleanly and documented transparently.

---

## Specification

### 1. Truthful Ring, Algebra, Ideal, and Quotient Law Witnesses
- **`src/algebrax/algebra/_monoid_algebra.py`**:
  - Remove `CommRing` from `MonoidAlgebra` base classes; inherit `MonoidAlgebraSemiring[K, T], Algebra[T, SparseVector[K, T]], Ring[SparseVector[K, T]]` (associative, not assumed commutative).
  - Add distinct nominal subclass `CommMonoidAlgebra(MonoidAlgebra[K, T], CommRing[SparseVector[K, T]])` for provably commutative monoid algebras (validating commutative coefficient ring and commutative monoid).
- **`src/algebrax/algebra/_polynomial.py`**:
  - Do **not** unconditionally attach `CommRing` to univariate `PolynomialAlgebra` (which accepts arbitrary `Semiring[T]`); keep `CommRing` on `MultivariatePolynomialAlgebra` (which enforces `isinstance(field, Field)`) and guard `PoissonAlgebra` conformance so odd `n_vars` never falsely claims canonical symplectic Poisson structure.
- **`src/algebrax/algebra/_quotient.py`**:
  - Change `QuotientRing` to inherit `QuotientSemiring[V], Ring[V], Generic[V]`.
  - Introduce distinct nominal subclass `CommQuotientRing(QuotientRing[V], CommRing[V])` (validating `isinstance(base_ring, CommRing)`). Update all commutative quotient construction sites (`variety/affine.py`, `variety/_mixins.py`, `variety/k_theory.py`, and `verification/_algebra.py:verify_groebner_basis_laws`) to instantiate `CommQuotientRing`.
  - Change `QuotientAlgebra` to inherit `QuotientSemiring[V]` **without** `QuotientRing`/`CommRing`/`LawAssociative`, and do not require `.one` on non-unital Lie quotients.
- **`src/algebrax/algebra/_grothendieck.py`**:
  - Remove unconditional `CommRing` from `GrothendieckRing` (inherit `Ring[tuple[M, M]]`) and introduce `CommGrothendieckRing(GrothendieckRing[M], CommRing[tuple[M, M]])` requiring `isinstance(semiring, CommSemiring)`.
- **`src/algebrax/algebra/_ideals.py`**:
  - Separate carrier types strictly: `NilpotentIdeal` implements `PrincipalIdeal[dict[int, T]]` (matching `PolynomialTruncationIdeal`) whose `reduce(poly: dict[int, T]) -> dict[int, T]` drops terms of degree $\ge k$ and satisfies `HasReduce[dict[int, T]]`. Move bare-exponent truncation to `reduce_degree(deg: int) -> int | None`.
- **`src/algebrax/algebra/_normed.py`, `_hopf.py`, `_non_assoc.py`**:
  - Fix inverted `__parameters__ == (V, R)` on `NormedSpace` and `InnerProductSpace` by placing `HasScale[R, V]` first and declaring `Protocol[R, V]`.
  - Add `LawAssociative` to `Bialgebra` and `HopfAlgebra` (so every `HopfAlgebra` structurally satisfies `Algebra`), and add `LawAssociative` and `LawLie` to `PoissonAlgebra`.
  - Do **not** retroactively add `Law*` witnesses to `Semigroup`, `Band`, `Monoid`, or `CommMonoid` (preserving zero-boilerplate duck-typing for basic carriers).

### 2. Exact `GaloisField` Reduction & Irreducibility Verification
- **`src/algebrax/algebra/_field.py`**:
  - Normalize `irreduc_poly` to monic form once in `GaloisField.__init__` (multiplying every coefficient by `pow(irreduc_poly[-1], -1, p) % p`), and also multiply by `pow(irreduc_poly[-1], -1, p) % p` inside `_gf_poly_mod` so standalone helper callers are safe.
  - Implement Rabin's irreducibility test over $\mathbb{F}_p[x]$ inside `GaloisField.__init__` (using repeated squaring $x^{p^k} \bmod f(x)$ and polynomial $\gcd$), raising `ValueError` if `irreduc_poly` is reducible over $\mathbb{F}_p$. Expose `validate_irreducible: bool = True` for pre-validated high-degree benchmarking.

### 3. Canonical `CliffordAlgebra` Indexing & Validation
- **`src/algebrax/clifford.py`**:
  - Standardize on **1-based** generator indices $1 \le i \le p + q + r$ (matching $e_1, \dots, e_n$ and existing `Cl(p, q, r)` tests).
  - Enforce `1 <= idx <= p + q + r` on **every** blade index in `_clifford_blade_mul` (including unpaired indices), raising `ValueError` for `idx < 1` or `idx > p + q + r`.
  - Update `geometric_product` and `rotor_rotation` docstrings and examples to use consistent 1-based blade tuples `(1,), (2,)`.

### 4. Semiring Axiom Fixes & Clean `HasStar` / `KleeneAlgebra` Discipline
- **`src/algebrax/semiring/optimization.py` & `statistical.py`**:
  - Hoist module-level `_INF = float('inf')` and `_NEG_INF = float('-inf')` constants and guard zero annihilation in `MinTimesSemiring.mul`, `TropicalSemiring.mul`, `ArcticSemiring.mul`, and `LogSemiring.mul` (`if a == _INF or b == _INF: return _INF` / `_NEG_INF` as appropriate) so `0 * ±inf` and `inf + (-inf)` never yield `NaN`.
- **`src/algebrax/semiring/structures.py`**:
  - Validate `k >= 0` in `KCollapsedSemiring.__init__` (raising `ValueError` for `k < 0`), fix `KCollapsedSemiring(0).one` to return `0`, and route `power(a, 0)` and `star(0)` through `self.one` instead of hardcoding `1`.
- **`src/algebrax/semiring/{logic,structures,statistical}.py`**:
  - Remove `def star(...) -> ...: raise NotImplementedError(...)` stubs from `DigitalSemiring`, `StringSemiring`, and `BivariateVarianceSemiring` so `isinstance(s, HasStar)` is strictly truthful.
  - Partition genuine star/Kleene semirings with exact protocol conformance and `.plus()` methods:

    | Semiring | Protocol Conformance | Rationale |
    |:---|:---|:---|
    | `TropicalSemiring`, `BooleanSemiring`, `ArcticSemiring`, `ViterbiSemiring`, `ReliabilitySemiring`, `BottleneckSemiring`, `MinTimesSemiring`, `LukasiewiczSemiring` | `KleeneAlgebra` (`HasStar`, `HasPlus`, `LawIdempotent`) | Additively idempotent with total Kleene star |
    | `KCollapsedSemiring`, `LogSemiring` | `StarSemiring` (`HasStar`, `HasPlus`) | Total star, not additively idempotent (for $k \ge 2$ / $\mathbb{R}$) |
    | `StandardSemiring` | `Semiring` (NOT `StarSemiring` / `KleeneAlgebra`) | `.star()` is partial (`int` raises `ValueError` for $a \ne 0$; `float` fails at $a \le -1$) |

### 5. Composition, Residual, and Groupoid Convention Alignment
- **`src/algebrax/topology/groupoid.py` & `src/algebrax/category/_mixins.py`**:
  - Change `SimplicialPathGroupoid.compose(self, f: PathMor, g: PathMor) -> PathMor` to diagrammatic order (`f[-1] == g[0]`, returning `f + g[1:]`), matching `Category.compose(f, g)`.
  - Rename `HasMorInv`'s canonical method cleanly to `inv(self, morphism: Mor) -> Mor` (clean cut — remove `invert_path` from `HasMorInv` and `SimplicialPathGroupoid`, updating all callers/tests and `EP-0005`).
- **`src/algebrax/algebra/_magma.py` & `_action.py`**:
  - Compose `HasResiduals[V]` into `Quasigroup` with consistent operand order (`rdiv(a, b)` solves $x \cdot b = a$, i.e., $a / b$) and align `RelationActionAlgebra.rdiv(self, a, b)` parameter names with `HasResiduals`.
- **`src/algebrax/group/canonical.py` & `permutation.py`**:
  - Standardize permutation composition across `algebrax.group` on **diagrammatic left-to-right** order (`(p ; q)(i) = q(p(i))`), aligning `symmetric_mul` directly with `group.compose`, `Category.compose`, and `SimplicialPathGroupoid.compose` with zero mode flags.

### 6. Flat Protocol Composition & Layer-2 Decoupling
- **`src/algebrax/lie/core.py`**: Mix `HasBracket[LieElement]`, `LawAnticommutative`, and `LawLie` into `LieAlgebra`.
- **`src/algebrax/rep/group.py` & `rep/lie.py`**:
  - Remove Layer-2-to-Layer-2 inheritance (`GroupRepresentation(GroupHom)`, `LieRepresentation(LieAlgebraHom)`) in favor of flat Layer-1 capability mixins.
  - Type `LieRepresentation.__call__(self, x: LieElement) -> SparseMatrix[int, V]` over Lie algebra elements and update `ExplicitLieRep.__call__` cleanly to evaluate `LieElement` (exposing `generator_matrix(idx: int)` for single-generator access).
- **`src/algebrax/rep/quiver.py` & `src/algebrax/algebra/_path_algebra.py`**:
  - Cleanly rename `rep.quiver.Quiver` → `FiniteQuiver` (removing the `Quiver` name collision with `category.core.Quiver`). Implement `source(arrow)` and `target(arrow)` methods on `FiniteQuiver` (storing edge maps as read-only `source_map`/`target_map` `MappingProxyType` views) so `FiniteQuiver` directly satisfies `category.core.Quiver`.
  - Decouple `algebra/_path_algebra.py` to accept any `category.core.Quiver` (or a minimal Layer-2 `FiniteQuiverProtocol`) instead of importing Layer-3 `rep.quiver`.
- **Layer-2 Upward-Import Cleanup (`src/algebrax/algebra/`)**:
  - Extract `Semiring.catalog()` discovery and domain-tag metadata (`DOMAIN_TAGS: dict[str, str]`, consumed by `EP-0254`'s CLI) into `algebrax.semiring._registry`.
  - Replace `_field.py:382`'s `ModularSemiring` import with `ModularField(self.p)` (already in `_field.py`).
  - Eliminate all remaining **top-level / import-time** upward imports from `algebra/` into `semiring/`, `matrix/`, `rep/`, `clifford/`, and `display.py` (documenting the minimal lazy delegators on `Semiring.catalog()` / `default()` / `_repr_*` cleanly).

---

## Acceptance Criteria

1. `isinstance(CliffordAlgebra(3, 0, 0), CommRing)` is `False`; `isinstance(PathAlgebra(...), CommRing)` is `False`; `isinstance(QuotientRing(...), CommRing)` is `False`; `isinstance(CommQuotientRing(...), CommRing)` is `True`; `isinstance(QuotientAlgebra(...), LawAssociative)` is `False`.
2. `isinstance(so_n(3), LieAlgebra)`, `isinstance(so_n(3), LawAnticommutative)`, `isinstance(so_n(3), LawLie)`, and `isinstance(GroupHopfAlgebra(...), Algebra)` are all `True`; `NormedSpace.__parameters__ == (R, V)` and `InnerProductSpace.__parameters__ == (R, V)`.
3. `GaloisField(3, [1, 0, 2])` (non-monic $2x^2 + 1$) passes `verify_field_laws` and matches SymPy; `GaloisField(2, [1, 0, 1])` ($x^2 + 1 = (x+1)^2$) raises `ValueError`.
4. `CliffordAlgebra(0, 1, 0)` rejects `(0,)` and `(2,)` with `ValueError` and computes `e_1^2 == -1` for `(1,)`.
5. `MinTimesSemiring().mul(0.0, float('inf')) == float('inf')`; `TropicalSemiring`, `ArcticSemiring`, and `LogSemiring` never return `NaN` on zero annihilation; `KCollapsedSemiring(0)` returns `0` for `.one`, `power(0, 0)`, and `star(0)` and raises `ValueError` for `k < 0`.
6. `isinstance(s, HasStar)` is `False` for `DigitalSemiring`, `StringSemiring`, and `BivariateVarianceSemiring`; all 8 idempotent star semirings satisfy `KleeneAlgebra` and `KCollapsedSemiring`/`LogSemiring` satisfy `StarSemiring`.
7. `SimplicialPathGroupoid` passes `verify_category_laws` and `Groupoid` with `inv` (no `invert_path`); `group.compose` and `group.symmetric_mul` agree on all non-commuting pairs in $S_3$; `Quasigroup.rdiv` satisfies $x \cdot b = a$.
8. `FiniteQuiver` satisfies `isinstance(q, category.Quiver)`; `NilpotentIdeal(2).reduce({0: 1.0, 1: 2.0, 2: 3.0}) == {0: 1.0, 1: 2.0}` and `NilpotentIdeal(2).reduce_degree(2) is None`.
9. Zero top-level upward imports from `src/algebrax/algebra/` into Layer-3 modules; all new classes (`CommQuotientRing`, `CommMonoidAlgebra`, `CommGrothendieckRing`, `FiniteQuiver`) comply with `EP-0002` (AMDS) and pass `tests/algebrax/test_docstrings.py`.

---

## Backwards Compatibility

This proposal makes intentional, clean breaking cuts (no deprecated aliases or compatibility shims):

- `isinstance(CliffordAlgebra(...), CommRing)`, `isinstance(PathAlgebra(...), CommRing)`, `isinstance(QuotientRing(...), CommRing)`, and `isinstance(GrothendieckRing(...), CommRing)` change from `True` (bug) to `False`; callers needing commutative quotients/monoid/Grothendieck rings use `CommQuotientRing`, `CommMonoidAlgebra`, `CommGrothendieckRing`.
- `NilpotentIdeal.reduce` accepts `dict[int, T]` polynomials; bare integer exponents move to `NilpotentIdeal.reduce_degree(int)`.
- `GaloisField(p, reducible_poly)` raises `ValueError` at construction time.
- `CliffordAlgebra` rejects blade index `0` or indices $> p + q + r$ with `ValueError`.
- `DigitalSemiring`, `StringSemiring`, and `BivariateVarianceSemiring` no longer define `.star()`.
- `SimplicialPathGroupoid.compose(f, g)` uses diagrammatic `(f, g)` order, and `HasMorInv.invert_path` is cleanly renamed to `inv`.
- `Quasigroup.rdiv(a, b)` solves $x \cdot b = a$ (updating `ModularSubtractionQuasigroup.rdiv` in `tests/algebrax/test_algebra.py`).
- `group.symmetric_mul` switches to diagrammatic left-to-right order matching `group.compose` and `Category.compose`.
- `rep.quiver.Quiver` is renamed to `FiniteQuiver` with `source(e)`/`target(e)` methods and `source_map`/`target_map` views; `ExplicitLieRep.__call__` takes `LieElement` (with `generator_matrix(idx)` for integer indices).

---

## How to Teach This / Documentation Plan

- Ensure all new/updated algebraic classes conform to `EP-0002` (AMDS) and pass `tests/algebrax/test_docstrings.py`.
- Update [`docs/guide/algebra/clifford_geometric_algebra.md`](../guide/algebra/clifford_geometric_algebra.md) for 1-based blade indexing and bounds validation.
- Update [`docs/guide/algebra/rings_and_fields.md`](../guide/algebra/rings_and_fields.md) and [`docs/guide/algebra/polynomials_and_quotients.md`](../guide/algebra/polynomials_and_quotients.md) for `CommQuotientRing`, `CommMonoidAlgebra`, and non-monic/reducible `GaloisField` checks.
- Update [`docs/guide/discrete/category.md`](../guide/discrete/category.md), [`docs/guide/algebra/quivers_and_gabriel.md`](../guide/algebra/quivers_and_gabriel.md), and [`docs/guide/algebra/groups_and_symmetries.md`](../guide/algebra/groups_and_symmetries.md) for diagrammatic composition, `HasMorInv.inv`, and `FiniteQuiver`.
- Update [`docs/guide/algebra/magmas_and_monoids.md`](../guide/algebra/magmas_and_monoids.md), [`docs/guide/algebra/lie_algebras.md`](../guide/algebra/lie_algebras.md), [`docs/guide/algebra/representations.md`](../guide/algebra/representations.md), [`docs/guide/algebra/lie_representations.md`](../guide/algebra/lie_representations.md), and [`docs/guide/semirings/optimization.md`](../guide/semirings/optimization.md), [`logic.md`](../guide/semirings/logic.md), [`statistical.md`](../guide/semirings/statistical.md).

---

## Reference Implementation

Target files verified in the Second Grand Council Audit & Review:
- `src/algebrax/algebra/{_field.py,_monoid_algebra.py,_polynomial.py,_quotient.py,_grothendieck.py,_ideals.py,_normed.py,_hopf.py,_non_assoc.py,_magma.py,_action.py,_semiring.py,_path_algebra.py}`
- `src/algebrax/clifford.py`, `src/algebrax/semiring/{_registry.py,optimization.py,structures.py,logic.py,statistical.py}`
- `src/algebrax/topology/groupoid.py`, `src/algebrax/category/_mixins.py`, `src/algebrax/lie/core.py`, `src/algebrax/rep/{group.py,lie.py,quiver.py}`, `src/algebrax/group/{canonical.py,permutation.py}`

---

## Rejected Ideas

1. **Dynamic `is_commutative` Property on `CommRing` / `QuotientRing`**:
   - *Rejected*: Python's `@runtime_checkable` `isinstance(x, LawCommutative)` checks only attribute existence, never return value. Distinct nominal subclasses (`CommQuotientRing`, `CommMonoidAlgebra`, `CommGrothendieckRing`) are the only sound design.
2. **Returning `0` for `int` Exponents in `NilpotentIdeal.reduce`**:
   - *Rejected*: In `NilpotentIdeal`, an `int` represents a monomial degree exponent $d$ ($\varepsilon^d$); returning `0` asserts $\varepsilon^d \equiv \varepsilon^0 = 1$ and collapses the dual-number ring to the zero ring.
3. **Marking `StandardSemiring` as `StarSemiring`**:
   - *Rejected*: `StandardSemiring.star` is partial (`int` raises `ValueError` for $a \ne 0$; `float` violates $a^* = 1 + a a^*$ for $a \le -1$), which would re-introduce a false law witness.
4. **Runtime Mode Flags or Compatibility Shims for Composition / `Quiver` / `invert_path`**:
   - *Rejected*: Violates Noether's symmetry and Feynman's simplicity. Clean cuts keep the protocol surface minimal and unambiguous.

---

## Open Questions

None. All Council review items (composition order, `FiniteQuiver` rename, `NilpotentIdeal` typing, `GaloisField.validate_irreducible`, and `StarSemiring`/`KleeneAlgebra` partition) are resolved.

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Noether, Russell, Popper).
* **2026-11-27:**
  * Incorporated Grand Council Pre-Implementation Review revisions: fixed `NilpotentIdeal.reduce` carrier typing, mandated nominal `CommQuotientRing`/`CommMonoidAlgebra`/`CommGrothendieckRing`, fixed `NormedSpace`/`InnerProductSpace` inverted generics, added `Bialgebra`/`HopfAlgebra`/`PoissonAlgebra` law witnesses, partitioned `KleeneAlgebra` vs. `StarSemiring` (excluding `StandardSemiring`), added `LogSemiring` annihilation & `KCollapsedSemiring` `power`/`star`/`k < 0` fixes, adopted clean cuts (`FiniteQuiver`, `HasMorInv.inv`, left-to-right `symmetric_mul`, `ExplicitLieRep.__call__(LieElement)`), added Acceptance Criteria and AMDS/guide checklist, and promoted status to `Accepted`.
