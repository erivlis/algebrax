---
title: "EP-0253: Verification Engine Hardening, Falsifiability & Grounded Formal Proofs"
description: "Eliminate vacuous passes and iterator-exhaustion bugs across algebrax.verification, ground Z3 SMT proofs directly in algebrax implementations, and close adversarial test blind spots."
icon: lucide/shield-alert
status: draft
---

# EP-0253: Verification Engine Hardening, Falsifiability & Grounded Formal Proofs

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0253                                                                       |
| **Title**         | Verification Engine Hardening, Falsifiability & Grounded Formal Proofs     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | 🔬 Popper (Falsifiability) & 🧪 Bacon (Empiricism)                         |
| **Status**        | Draft                                                                      |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-11-26                                                                 |
| **Updated**       | 2026-11-26                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal hardens `algebrax.verification` and the multi-layered verification test suite so that every verifier is genuinely falsifiable. It eliminates vacuous `True` passes caused by iterator exhaustion, empty/all-zero sample sets, `NaN == NaN` equality, swallowed exceptions, and missing axiom checks (notably $\Delta(ab) = \Delta(a)\Delta(b)$ in `verify_bialgebra_laws` and zero-seminorm rejection in `verify_normed_space_laws`), grounds the `Z3` SMT proof suite in actual `algebrax` code, and closes critical falsification test blind spots across finite fields, Clifford algebras, matrix decompositions, and core utilities.

---

## Motivation

A verification engine that can silently return `True` on broken implementations undermines the entire "Stamp of Trust" promised by AlgebraX. The Second Grand Council Audit uncovered systemic falsifiability holes:

1. **Iterator Exhaustion & Exception Swallowing (`verification/_semiring.py`)**:
   - `verify_semiring_laws` has no minimum-sample guard (`samples=[]` passes all 9 axioms).
   - `verify_star_semiring_laws`, `verify_kleene_algebra_laws`, and `verify_action_algebra_laws` pass `samples: Iterable[V]` to an inner verifier (consuming it via `list(samples)`), then call `elements = list(samples)` again—evaluating to `[]` on any generator and vacuously passing all Conway, star-plus, residuation, and action-induction laws.
   - `except (ValueError, ZeroDivisionError, OverflowError, NotImplementedError): continue` blocks lack a tested-sample counter, so a stub raising `NotImplementedError` or returning `NaN` on every input vacuously passes. Moreover, `left_conway = False; break` exits before evaluating `right_conway`, falsely reporting `right_conway = True`.
2. **Missing Core Axioms & Degenerate Witnesses (`verification/_algebra.py`, `_common.py`, `_rep.py`, `_topology.py`)**:
   - `verify_bialgebra_laws` never checks the defining bialgebra homomorphism law $\Delta(a \cdot b) = \Delta(a) \cdot \Delta(b)$ and checks only `sum(delta_one.values()) == 1` instead of $\Delta(1) = 1 \otimes 1$. `verify_hopf_algebra_laws` also exhausts generator `c_samples` before forwarding.
   - `verify_normed_space_laws` never checks $\|v\| > \text{tol}$ for $v \ne 0$, letting the degenerate zero seminorm `norm(v) = 0.0` pass all 4 axioms (and hardcodes `r_mag = 1.0` for `Fraction`/`Decimal` scalars).
   - `verify_inner_product_space_laws` pins `w = v_elements[0]`, collapsing linearity to `0 == 0` when callers pass `[space.zero, u, v]`.
   - `_float_equal` treats `NaN == NaN` as `True`, masking NaN-producing bugs on both sides of an identity.
   - Empty or all-zero vacuous passes exist in `verify_coassociativity`, `verify_counitality`, `verify_antipode_axiom`, `verify_division_ring_laws` (all-zero samples), `verify_quantum_sl2_relations` (`dim=0`), `verify_sheaf_laplacian_properties` (default `sample_cochains=()`), and `verify_padic_ultrametric_inequality` (`isfinite` silently skipping buggy zero products).
3. **Disconnected SMT Proof Suite (`tests/verifications/test_smt_z3_proofs.py`)**:
   - All 343 lines of `test_smt_z3_proofs.py` contain **zero imports or calls to `algebrax`**, proving only hand-transcribed textbook Z3 formulas (and a pure tautology for `LawvereMetricSpace`). Breaking every semiring in `src/algebrax/` leaves all 8 SMT tests green.
4. **Happy-Path-Only Test Blind Spots**:
   - `tests/algebrax/test_verification.py` has zero falsification or iterator-exhaustion tests for `_rep.py`, `_topology.py`, star/Kleene/action/Conway verifiers, `verify_bialgebra_laws`, or normed/inner-product verifiers.
   - Narrow happy-path tests masked critical bugs: `test_galois.py` only tested monic $p=2$; `test_clifford.py` only tested `Cl(3, 0, 0)` without calling `geometric_product`; `test_matrix_decompose.py` only tested $n \le 5$ (missing `key=str` corruption at $n \ge 11$, asymmetric `cholesky`, rank-deficient `qr`, negative `k` in `svd`); `test_langlands_and_padic.py` never tested disconnected $d$-regular graphs.

---

## Rationale

- **🔬 Karl Popper (Falsifiability)**: *"Assume the happy path is a lie."* Every verifier must have at least one adversarial **falsification unit test** proving it returns `False` (or raises `ValueError`) when given a broken structure, degenerate witness, or generator input.
- **🧪 Francis Bacon (Empiricism)**: Verification claims in `docs/verification.md` must match observable reality. An SMT proof that never executes `algebrax` code is a specification proof, not an implementation proof—connecting Z3 AST execution directly to `algebrax` semiring methods (or verifying symbolic trace equivalence) makes the Stamp of Trust empirically honest.

---

## Specification

### 1. Universal Verifier Guards & NaN Safety (`src/algebrax/verification/`)
- **`_common.py`**:
  - Change `_float_equal(a, b, tol)` so `math.isnan(a) or math.isnan(b)` **always** returns `False` (matching IEEE 754 and `cmath.isclose`).
  - Add shared `_materialize_samples(samples, min_count=...)` helper used as the **first** line of every verifier so iterators/generators are materialized once and forwarded as sequences to nested verifiers.
- **`_semiring.py`**:
  - Require non-empty samples (minimum witness guard) in `verify_semiring_laws`, `verify_star_semiring_laws`, `verify_kleene_algebra_laws`, `verify_conway_matrix_laws`, and `verify_action_algebra_laws`.
  - Track a `tested_count` inside every loop that skips boundary infinities/overflows; if `tested_count == 0` (e.g., all samples threw exceptions or produced `NaN`), mark the law `False` instead of vacuously `True`.
  - Evaluate `left_conway` and `right_conway` independently (do not `break` out of `right_conway` when `left_conway` fails).
- **`_algebra.py`**:
  - Complete `verify_bialgebra_laws`:
    1. Explicitly verify $\Delta(a \cdot b) = \Delta(a) \cdot \Delta(b)$ across all ordered pairs `(a, b)` (using tensor-product multiplication in $B \otimes B$).
    2. Verify exact unit comultiplication $\Delta(1) = 1 \otimes 1$ (not merely `sum(delta_one.values()) == 1`).
    3. Check `counit_homomorphism` over `itertools.product(c_elements, repeat=2)` (covering `a == b` and non-commutative `(b, a)`).
  - Materialize `c_samples` once in `verify_hopf_algebra_laws` before forwarding; enforce `_require_samples` in standalone `verify_coassociativity`, `verify_counitality`, and `verify_antipode_axiom`.
  - In `verify_normed_space_laws`: check positive definiteness (`norm(v) > tol` whenever `not space.is_zero(v)`), and compute `r_mag = float(abs(r))` for `Fraction`/`Decimal` scalars instead of hardcoding `1.0`.
  - In `verify_inner_product_space_laws`: check `first_argument_linearity` across all `w` in `v_elements` (requiring at least one non-zero `w`), never pinning `w = v_elements[0]`.
  - In `verify_division_ring_laws` / `verify_field_laws`: require at least 2 non-zero samples (`ValueError` if all-zero).
- **`_rep.py` & `_topology.py`**:
  - Guard empty-dimension / empty-sample inputs in `verify_quantum_sl2_relations`, `verify_sheaf_laplacian_properties` (auto-generate non-zero deterministic probe cochains if `sample_cochains` is omitted rather than vacuously passing), and `verify_padic_ultrametric_inequality` (fail if a non-zero product yields `val == inf`).

### 2. Grounding the Z3 SMT Suite (`tests/verifications/test_smt_z3_proofs.py`)
- Import and execute actual `algebrax` methods directly on Z3 symbolic expressions where Python operator overloading / `z3.If`-compatible semirings permit (e.g., `DualNumberAlgebra`, `ExpectationSemiring`, `BooleanSemiring`, `matrix.dot`, `matrix.transpose`, `MatrixCategory`), OR perform symbolic-execution equivalence checks plus differential counterexample-guided verification against live `algebrax` instances (`TropicalSemiring`, `ArcticSemiring`, `BottleneckSemiring`, `LukasiewiczSemiring`, `LawvereMetricSpace`).
- Replace the tautological `LawvereMetricSpace` test with a genuine proof over `algebrax.category.enriched.LawvereMetricSpace` shortest-path / Floyd–Warshall closure.
- Clearly distinguish in `docs/verification.md` between *direct symbolic execution over `algebrax` methods* and *abstract Z3 specification proofs*.

### 3. Adversarial Falsification & Boundary Test Expansion (`tests/`)
- Expand `tests/algebrax/test_verification.py` with:
  - Generator/iterator-exhaustion tests for every verifier family (`_semiring`, `_algebra`, `_rep`, `_topology`, `_variety`).
  - Falsification tests proving: broken $\Delta(ab)$ fails `verify_bialgebra_laws`; zero seminorm fails `verify_normed_space_laws`; `NaN`-returning stubs fail `_semiring` verifiers; `NotImplementedError` stubs fail star/action verifiers.
- Add targeted regression suites covering all audit blind spots:
  - Non-monic and reducible `GaloisField` moduli (`test_galois.py` & `test_differential_sympy.py`).
  - Mixed-signature `CliffordAlgebra(0, 1, 0)`, `Cl(0, 0, 1)`, `Cl(1, 1, 0)` and `geometric_product` (`test_clifford.py`).
  - $n \ge 12$ integer-indexed `solve_triangular`, `cholesky` (including asymmetric rejection), rank-deficient `qr`, negative `k` in `svd`, and disjoint-key `lu_decompose`/`det` (`test_matrix_decompose.py`).
  - Disconnected $d$-regular graphs in `is_ramanujan_graph` (`test_langlands_and_padic.py`).
  - Boundary error guards in `transforms` (`n <= 0`, `lorentz_boost(axis=0)`), `probability` (`base=1`, negative probabilities, `evidence=0`), `lattice` (`harmonic_mean(1, -1)`, negative `join`), and `group.permutation.signature` (non-bijections).

---

## Backwards Compatibility

- Callers passing empty lists or all-zero samples to verifiers that previously returned vacuous `True` will now receive `ValueError` or `False` (strictly catching previously masked test bugs).
- Passing a single-use generator to `verify_star_semiring_laws`, `verify_kleene_algebra_laws`, `verify_action_algebra_laws`, or `verify_hopf_algebra_laws` now works reliably instead of silently skipping axioms or crashing.

---

## How to Teach This / Documentation Plan

- Update [`docs/verification.md`](../verification.md) to reflect grounded Z3 SMT proofs and the expanded falsification matrix.
- Update [`docs/guide/semirings/verification.md`](../guide/semirings/verification.md) with guidance on Popper's non-vacuous witness rule and adversarial falsification testing.

---

## Reference Implementation

Target files verified in the Second Grand Council Audit:
- `src/algebrax/verification/{_common.py,_semiring.py,_algebra.py,_rep.py,_topology.py}`
- `tests/verifications/test_smt_z3_proofs.py`
- `tests/algebrax/{test_verification.py,test_galois.py,test_clifford.py,test_matrix_decompose.py,test_langlands_and_padic.py}`

---

## Rejected Ideas

1. **Keeping `NaN == NaN` as `True` in `_float_equal` for "Convenience"**:
   - *Rejected*: Violates Popper's falsifiability principle. Two broken expressions both producing `NaN` would falsely certify an algebraic law.
2. **Deleting `test_smt_z3_proofs.py` Entirely**:
   - *Rejected*: Automated SMT proofs over $\mathbb{R}^n$/$\mathbb{B}^n$ are genuinely valuable when connected directly to `algebrax`'s actual operations (e.g., running `matrix.dot`, `DualNumberAlgebra`, `MatrixCategory` directly on Z3 symbolic terms).

---

## Open Questions

- [ ] For `TropicalSemiring`/`LukasiewiczSemiring` where Python's built-in `min`/`max` cannot accept `z3.ArithRef` directly, should we provide a tiny symbolic-dispatch hook or verify bounded AST-equivalence via Z3 + Hypothesis differential sampling?

---

## Change Log

* **2026-11-26:**
  * Initial Draft authored from the Second Grand Council Codebase Audit (Popper, Bacon).
