---
title: "EP-0183: Comparative Verification — Exact Symbolic Algebra, Lie, Galois, Clifford & Group Theory (SymPy Oracle)"
description: "Establishes comparative verification tests pitting AlgebraX exact rational matrices, Lie algebras, BCH series, Galois finite fields GF(p^m), Clifford geometric algebras, and permutation/braid groups against SymPy and exact algebraic oracles."
icon: lucide/sigma
status: final
---

# EP-0183: Comparative Verification — Exact Symbolic Algebra, Lie, Galois, Clifford & Group Theory (`SymPy` Oracle)

| Field             | Value                                                                                                         |
|:------------------|:--------------------------------------------------------------------------------------------------------------|
| **EP**            | 0183                                                                                                          |
| **Title**         | Comparative Verification — Exact Symbolic Algebra, Lie, Galois, Clifford & Group Theory (`SymPy` Oracle)      |
| **Author**        | Eran Rivlis & Antigravity (Council Agent)                                                                     |
| **Sponsor**       | The Council                                                                                                   |
| **Delegate**      | ⚖️ Emmy Noether (Symmetry), 🔬 Karl Popper (Falsifiability), 🧩 Bertrand Russell (Consistency) & 🛡️ The Golem |
| **Status**        | Final                                                                                                         |
| **Type**          | Standards Track                                                                                               |
| **Created**       | 2026-10-24                                                                                                    |
| **Updated**       | 2026-10-24                                                                                                    |
| **Replaces**      | None                                                                                                          |
| **Superseded-By** | None                                                                                                          |

---

## Abstract

This proposal specifies **Wave 1C** of the Phase 5 Mathematical Verification Track
([EP-0180](EP-0180-multi-layered-verification-suite.md)): an exact symbolic and algebraic **Comparative Verification
Suite** validating `algebrax.lie`, `algebrax.galois`, `algebrax.clifford`, `algebrax.group`,
`algebrax.semiring.algebraic` (`PolynomialSemiring`, `DualNumberSemiring`), and exact `fractions.Fraction` matrix
operations against **SymPy** (`sympy.matrices`, `sympy.liealgebras`, `sympy.polys`, `sympy.combinatorics`) and **SciPy**
(`scipy.linalg.expm`). Where floating-point arithmetic obscures subtle algebraic bugs behind $\epsilon$-tolerances,
exact symbolic comparison proves **zero-defect mathematical identity**.

---

## Motivation

`algebrax` extends far beyond standard floating-point arrays into continuous symmetry groups, finite fields, geometric
algebras, and symbolic rings:

1. **Eliminating Floating-Point Masking via Exact $\mathbb{Q}$ and $\mathbb{F}_{p^m}$ Oracles:** When testing
   `determinant`, `inverse`, or `PolynomialSemiring` over IEEE 754 floats, an $\epsilon = 10^{-9}$ tolerance can hide
   off-by-one degree truncations or minor sign errors in small terms. Comparing `algebrax` over `fractions.Fraction`
   directly against `sympy.Matrix` over $\mathbb{Q}$ requires `==` with **zero tolerance**.
2. **Validating Lie Algebras, Root Systems & BCH Dynamics (`algebrax.lie`):** `algebrax` implements classical
   ($\mathfrak{so}_n, \mathfrak{su}_n, \mathfrak{sl}_n, \mathfrak{sp}_n, \mathfrak{se}_3$) and exceptional
   ($\mathfrak{g}_2, \mathfrak{f}_4, \mathfrak{e}_6, \mathfrak{e}_7, \mathfrak{e}_8$) Lie algebras, Killing forms,
   Dynkin diagrams, Cartan matrices, and Baker–Campbell–Hausdorff (BCH) series. Cross-checking Cartan matrices and root
   system ranks against `sympy.liealgebras.RootSystem` and verifying the BCH matrix exponential
   identity $\exp (X)\exp (Y) = \exp (\operatorname{BCH} (X, Y))$ against `scipy.linalg.expm` provides ironclad
   validation of Phase 4's Lie theory engine.
3. **Cryptographic & Coding-Theory Finite Fields (`algebrax.galois`):** `GaloisFieldSemiring` ($GF (p^m)$) and
   `gf_matrix_mul` / `gf_matrix_inv` must satisfy exact field inversion $a \cdot a^{-1} = 1$, Fermat's Little
   Theorem $a^{p^m - 1} = 1$, and Frobenius endomorphism $(a + b)^p = a^p + b^p$, cross-verified against `sympy.GF`
   polynomial quotient arithmetic.
4. **Clifford Geometric Algebra (`algebrax.clifford`) & Group Theory (`algebrax.group`):** 3D/ND rotor
   rotations $v' = R v \tilde{R}$ must match `scipy.spatial.transform.Rotation` / Rodrigues' rotation formula, while
   permutation composition, cycle parity signatures, and Artin braid relations must match
   `sympy.combinatorics.permutations.Permutation`.

---

## Rationale

- **⚖️ Symmetry (Noether):** Directly verifies continuous Lie symmetries ($\exp (\operatorname{ad}_X)$, Killing form
  invariance $B ([X,Y], Z) + B (Y, [X,Z]) = 0$), discrete Weyl reflection symmetries, and spinor/rotor $SO (3)$
  double-cover homomorphisms.
- **🔬 Falsifiability (Popper):** Exact equality (`assert ax_result == sympy_result`) leaves zero room for numerical
  hand-waving—any discrepancy immediately falsifies the implementation.
- **🧩 Consistency (Russell):** Ensures that `PolynomialSemiring`, `DualNumberSemiring`, and `GaloisFieldSemiring` obey
  the exact same ring/field homomorphisms as `sympy.Poly` and `sympy.diff`.
- **🛡️ Safety (The Golem):** Prevents silent bit-twiddling or irreducible-polynomial reduction errors in $GF (2^8)$
  and $GF (p^m)$.

---

## Specification

### 1. Target Modules & Comparative Verification Matrix

Tests reside in `tests/verifications/test_differential_sympy.py` and `tests/verifications/test_exact_algebra.py`:

| AlgebraX Module & Function                       | External Reference Oracle                                                              | Mathematical Truth / Identity Verified                                                                                                       | Precision        |
|:-------------------------------------------------|:---------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
| `matrix.determinant` & `inverse` over `Fraction` | `sympy.Matrix(M).det()` & `.inv()`                                                     | Exact rational determinant, adjugate, and inverse parity                                                                                     | **Exact (`==`)** |
| `lie.roots.RootSystem(cartan_type)`              | `sympy.liealgebras.RootSystem(cartan_type)`                                            | Cartan matrix, number of positive roots $                                                                                                    | \Phi^+           |$, simple roots, Weyl group order | **Exact (`==`)** |
| `lie.bch(g, x, y, order=5)`                      | `scipy.linalg.expm(X) @ scipy.linalg.expm(Y)` vs `expm(BCH(X,Y))`                      | Matrix exponential convergence $\|\exp(X)\exp(Y) - \exp(\operatorname{BCH}_5(X,Y))\|$ for small $\|X\|, \|Y\|$                               | $10^{-7}$        |
| `lie.LieAlgebra.killing_form` & `adjoint_matrix` | Trace of adjoint matrices $\operatorname{Tr}(\operatorname{ad}_X \operatorname{ad}_Y)$ | Adjoint homomorphism $[\operatorname{ad}_X, \operatorname{ad}_Y] = \operatorname{ad}_{[X,Y]}$ & Killing invariance $B([X,Y],Z) = B(X,[Y,Z])$ | $10^{-11}$       |
| `galois.GaloisFieldSemiring(p, m)`               | `sympy.polys.domains.GF(p)` & irreducible poly mod                                     | Addition, multiplication, multiplicative inverse $a \cdot a^{-1} = 1$, $a^{p^m-1} = 1$, $(a+b)^p = a^p + b^p$                                | **Exact (`==`)** |
| `galois.gf_matrix_mul` & `gf_matrix_inv`         | Exact matrix ops over `sympy.GF(p)`                                                    | $A \cdot A^{-1} = I \pmod p$ and determinant non-zero check                                                                                  | **Exact (`==`)** |
| `clifford.rotor_rotation(v, axis, angle)`        | Rodrigues rotation formula / 3D rotation matrix $R(\hat{n}, \theta) v$                 | $R v \tilde{R} = v \cos\theta + (\hat{n} \times v)\sin\theta + \hat{n}(\hat{n}\cdot v)(1-\cos\theta)$                                        | $10^{-11}$       |
| `clifford.CliffordSemiring(p, q, r)`             | Defining relation $e_i e_j + e_j e_i = 2 \eta_{ij}$                                    | Associativity $(AB)C = A(BC)$, reversion $\widetilde{AB} = \tilde{B}\tilde{A}$                                                               | $10^{-12}$       |
| `group.compose`, `inverse`, `signature`          | `sympy.combinatorics.Permutation`                                                      | Group composition, inverse $p \circ p^{-1} = e$, sign homomorphism $\operatorname{sgn}(pq) = \operatorname{sgn}(p)\operatorname{sgn}(q)$     | **Exact (`==`)** |
| `group` Artin Braid crossings                    | Braid group $B_n$ Yang–Baxter relation                                                 | $\sigma_i \sigma_{i+1} \sigma_i = \sigma_{i+1} \sigma_i \sigma_{i+1}$ and far commutativity $\sigma_i \sigma_j = \sigma_j \sigma_i$ ($       | i-j              | \ge 2$) | **Exact (`==`)** |
| `semiring.DualNumberSemiring`                    | `sympy.diff(f(x), x)`                                                                  | Exact automatic differentiation of polynomials & rational expressions vs symbolic derivative                                                 | $10^{-11}$       |
| `semiring.PolynomialSemiring`                    | `sympy.Poly` addition & multiplication                                                 | Exact polynomial ring convolution and degree preservation over $\mathbb{Q}[x]$                                                               | **Exact (`==`)** |

---

## Backwards Compatibility

Purely additive verification test suite under `tests/verifications/`. `sympy` is an optional test dependency in
`--group verification`; tests skip gracefully via `pytest.importorskip("sympy")` if not installed.

---

## How to Teach This / Documentation Plan

1. Document the SymPy exact symbolic verification matrix in the user guide under `docs/guide/discrete/`.
2. Highlight the exact `Fraction` and `DualNumberSemiring` vs `SymPy` differential tests as examples of zero-rounding
   algebraic verification.

---

## Reference Implementation

- `tests/verifications/test_differential_sympy.py`
- `tests/verifications/test_exact_algebra.py`

---

## Rejected Ideas

1. **Symbolic Expansion of $\mathfrak{e}_8$ Structure Constants in SymPy:** Rejected
   because $\dim (\mathfrak{e}_8) = 248$ requires $\approx 1.5 \times 10^7$ triple combinations in symbolic CAS,
   violating Shannon's 15-second CI budget. Instead, Cartan matrices and root system metadata are compared against
   `sympy.liealgebras` for all ranks, while high-dimensional Jacobi identities use Schwartz–Zippel PIT
   (`test_pit_symbolic.py`).

---

## Open Questions

None.

---

## Change Log

- **2026-10-24**: Initial draft created as Wave 1C of the Phase 5 Comparative Verification series.
