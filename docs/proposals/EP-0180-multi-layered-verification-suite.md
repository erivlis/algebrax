---
title: "EP-0180: Multi-Layered Verification Test Architecture"
description: "Establishes a dedicated, 8-layer verification test suite under tests/verifications/, generalizing tests/algebrax/test_verification.py through differential testing, property-based axiom verification, metamorphic relations, Schwartz-Zippel PIT, and certified solvers."
icon: lucide/shield-check
status: final
---

# EP-0180: Multi-Layered Verification Test Architecture

| Field             | Value                                                                                                                                                                                                           |
|:------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EP**            | 0180                                                                                                                                                                                                            |
| **Title**         | Multi-Layered Verification Test Architecture                                                                                                                                                                   |
| **Author**        | Eran Rivlis & Jules (The Explorer & Council Agent)                                                                                                                                                              |
| **Sponsor**       | The Council                                                                                                                                                                                                     |
| **Delegate**      | 🔬 Karl Popper (Falsifiability), ⚖️ Emmy Noether (Symmetry), ⚡ Claude Shannon (Efficiency), 🛡️ The Golem (Safety) & 🧭 The Explorer (Curiosity)                                                                 |
| **Status**        | Final                                                                                                                                                                                                           |
| **Type**          | Standards Track                                                                                                                                                                                                 |
| **Created**       | 2026-10-24                                                                                                                                                                                                      |
| **Updated**       | 2026-10-24                                                                                                                                                                                                      |
| **Replaces**      | None                                                                                                                                                                                                            |
| **Superseded-By** | None                                                                                                                                                                                                            |

---

## Abstract

This proposal establishes a dedicated, automated **Verification Test Architecture** housed under `tests/verifications/`, derived from research compendium `references/explorations/EXP-0003-correctness-evidence/README.md`. Generalizing the initial algebraic law verification suite in `tests/algebrax/test_verification.py` (introduced in [EP-0131](EP-0131-algebraic-law-verification.md)), this proposal replaces the unwieldy and descriptive concept of "correctness evidence" as a directory label with a clean, actionable testing discipline: **Verification**. The proposal introduces an **8-layer verification harness** organized across three distinct tiers: (1) **Empirical & Metamorphic Tier** (cross-library differential testing against NumPy, SciPy, NetworkX, and GUDHI; metamorphic invariant checks; and Hypothesis property-based testing); (2) **Exact & Semi-Formal Tier** (Schwartz–Zippel randomized polynomial identity testing (PIT) to defeat monomial explosion; the Method of Manufactured Solutions (MMS) for discrete differential operators; and exact rational arithmetic validation); and (3) **Deductive & Certified Tier** (SMT/Z3 formal proofs; Lean 4 dual-specification reference models; and self-certifying solver witnesses). The suite produces structured correctness evidence artifacts without introducing heavy runtime dependencies into `src/algebrax`.

---

## Motivation

`AlgebraX` serves as a pure-Python, zero-heavy-dependency foundational framework unifying linear algebra, semirings, graph analysis, Clifford geometric algebras, discrete exterior calculus, cellular sheaves, and simplicial homology. In foundational mathematical software, software correctness is not merely a quality goal—it is a **mathematical imperative**:

1. **Semantic Clarity & Architectural Alignment:** In [EP-0131](EP-0131-algebraic-law-verification.md), AlgebraX established the public verification engine (`algebrax.verification`) and an initial test file `tests/algebrax/test_verification.py` to check static semiring samples. However, as verification has expanded to include differential comparison, metamorphic symmetries, Schwartz–Zippel polynomial identity testing, and discrete calculus convergence rates, a single test file is insufficient. Organizing these tests under `tests/verifications/` provides a direct, intuitive generalization. Furthermore, naming the directory `verifications/` correctly identifies the **action and discipline** of testing, whereas "correctness evidence" represents the downstream output report/artifact generated by executing these verification suites.
2. **The Test Oracle Problem:** For advanced discrete differential operators (e.g., discrete exterior derivative $d_k$, Hodge Laplacian $\Delta_k$, and cellular sheaf Laplacians $\mathcal{L}_{\mathcal{F}}$), analytical ground truths do not exist for arbitrary unstructured simplicial meshes or heterogeneous graph topologies.
3. **The Monomial Explosion Barrier:** Attempting to verify high-degree symbolic identities (e.g., Jacobi identity in 14-dimensional exceptional Lie algebras, or high-grade Clifford multivector products) using standard computer algebra systems (CAS) causes exponential $\binom{n+d}{d}$ term blowup, stalling test runners.
4. **Floating-Point Imprecision vs. Axiom Violations:** IEEE 754 floating-point operations violate pure algebraic associativity ($(a + b) + c \neq a + (b + c)$). Naive property testing on floats yields false alarms, while masking errors behind arbitrary epsilons obscures genuine implementation bugs.
5. **Asymmetric Verification Burden:** For algorithms with $O(N^3)$ computational complexity (e.g., Helmholtz–Hodge flow decompositions, spectral graph partitionings), recomputing full solutions inside test loops is computationally expensive, whereas verifying an algebraic certificate is $O(E)$.

A structured, multi-layered verification framework is needed under `tests/verifications/` to provide mathematically sound correctness evidence while keeping `src/algebrax` completely free of heavy third-party dependencies.

---

## Rationale

The architecture of the verification layer is derived directly from **The Council Framework** (*PRINCIPLES.md*):

### 1. Falsifiability (Popper)
Every mathematical claim made by an AlgebraX class or function must be systematically falsifiable. Property-based testing via **Hypothesis** and randomized polynomial identity testing (**Schwartz–Zippel PIT**) subject algebraic axioms to aggressive randomized search across millions of generated states, actively probing boundary cases (empty matrices, infinite semiring weights, disconnected complexes, degenerate simplices).

### 2. Symmetry (Noether)
In accordance with Noether's theorem connecting symmetries to conservation laws, **Metamorphic Invariant Testing** verifies operators along their natural axes of symmetry:
- Matrix transpose duality: $(A \otimes B)^T = B^T \otimes A^T$ (for commutative semirings).
- Hodge star involution: $\star \star \omega = (-1)^{k(n-k)} s \omega$.
- Simplicial boundary nilpotency: $\partial_k \circ \partial_{k+1} = \mathbf{0}$ and coboundary nilpotency $d_{k+1} \circ d_k = \mathbf{0}$.
- Graph automorphism conjugacy: $L(P A P^T) = P L(A) P^T$.

### 3. Efficiency (Shannon)
Standard symbolic canonicalization expands expressions into $O(2^N)$ monomials. Schwartz–Zippel PIT replaces this combinatorial bottleneck with $O(N)$ black-box polynomial evaluations over random samples from a finite set $S \subset \mathbb{Z}$, bounding the probability of an accidental root to $\le (d/|S|)^k \le 10^{-15}$. Furthermore, standard CI executions cap property-based sampling to $\le 100$ examples ($< 15\text{s}$ total run), reserving deep sweeps for nightly benchmarks.

### 4. Safety (The Golem)
Mathematical operations must not silently degrade downstream precision. **Self-Certifying Solvers** emit lightweight $O(E)$ verification certificates (e.g., orthogonality residuals $\langle d\alpha, \delta\beta \rangle$, reconstruction norms $\|v - (d\alpha + \delta\beta + \gamma)\|$, and harmonicity $\|\Delta \gamma\|$), preventing corrupt states from leaking across architectural boundaries.

### 5. Clarity (Feynman)
Test failures must pinpoint the exact algebraic axiom that failed rather than raising an opaque numerical assertion error. Reusable property runners format descriptive failure cards (e.g., `"Left Distributivity violated for MinPlus semiring at a=-inf, b=0, c=inf"`).

### 6. Consistency (Russell)
Differential testing ensures isomorphism across representations: sparse nested dictionary matrices in AlgebraX must yield identical results when mapped to dense NumPy arrays, SciPy CSR matrices, or SymPy exact rationals ($f^{-1}(f(x)) = x$). The naming `tests/verifications/` maintains symmetry with `algebrax.verification` and generalizes `tests/algebrax/test_verification.py`.

### 7. Harmony (The Steward)
The verification suite achieves complete non-leakage. Application code in `src/algebrax` remains lightweight and pure-Python. All heavy numerical, symbolic, and SMT engines (NumPy, SciPy, NetworkX, GUDHI, SymPy, Z3) are isolated in `tests/verifications/` and declared as optional test-group dependencies.

### 8. Curiosity (The Explorer)
The verification layer bridges practical scientific software with formal methods, incorporating automated SMT verification (Z3) and dual-specification models in **Lean 4**.

---

## Specification

### 1. Test Suite Directory Structure

The verification harness is housed in `tests/verifications/`, decoupled from existing unit and regression tests:

```text
tests/
├── algebrax/                                    # Core unit and fast regression tests (zero heavy deps)
│   ├── ...
│   └── test_verification.py                     # Fast catalog law smoke tests (algebrax.verification)
└── verifications/                               # Comprehensive Multi-Layered Verification Suite
    ├── conftest.py                              # Custom pytest markers, fixtures & skip logic
    ├── test_axiomatic_properties.py             # All-34-semiring Hypothesis PBT & exact Q ring laws (EP-0185)
    ├── test_differential_numpy.py               # Comparative tests vs NumPy & SciPy (EP-0181)
    ├── test_differential_graphs.py              # Comparative tests vs NetworkX & csgraph (EP-0182)
    ├── test_differential_sympy.py               # Exact symbolic Lie, Galois, Clifford & Group vs SymPy (EP-0183)
    ├── test_differential_topology_prob.py       # Homology, Stokes, Info Theory & Automata vs SciPy (EP-0184)
    ├── test_differential_statistical_semirings.py # Streaming Moment Semirings vs scipy.stats (EP-0185)
    ├── test_mms_sheaves_and_categories.py       # Cellular Sheaf MMS, Categories, Lattices & Tries (EP-0185)
    ├── test_metamorphic_invariants.py           # Metamorphic invariant relations (EP-0180)
    ├── test_pit_symbolic.py                     # Schwartz-Zippel PIT for Lie & Cayley-Hamilton (EP-0186)
    ├── test_smt_z3_proofs.py                    # Automated SMT / Z3 formal proofs (EP-0186)
    └── test_certificates.py                     # Universal O(nnz) proof-carrying solver certificates (EP-0186)
```

### 2. Relationship to `tests/algebrax/test_verification.py`

- `tests/algebrax/test_verification.py` is retained as the lightweight, in-tree smoke test for `algebrax.verification.verify_semiring_laws` that runs with zero external dependencies in $< 0.1\text{s}$.
- `tests/verifications/test_axiomatic_properties.py` generalizes this by subjecting all semirings to randomized Hypothesis property-based testing across edge-case floats, signed infinities, and exact rational numbers.

### 3. Pytest Markers & Dependency Isolation

To allow developers and CI runners to execute tests with or without optional scientific libraries, `tests/verifications/conftest.py` defines dedicated markers with automatic skip-guards:

```python
# tests/verifications/conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "verification: All verification suite tests")
    config.addinivalue_line("markers", "differential: Tests requiring NumPy, SciPy, NetworkX, or SymPy")
    config.addinivalue_line("markers", "axiomatic: Property-based testing via Hypothesis")
    config.addinivalue_line("markers", "metamorphic: Metamorphic relation invariance tests")
    config.addinivalue_line("markers", "pit: Schwartz-Zippel Polynomial Identity Testing")
    config.addinivalue_line("markers", "mms: Method of Manufactured Solutions tests")
    config.addinivalue_line("markers", "formal_smt: Formal proofs via Z3 SMT solver")
    config.addinivalue_line("markers", "smt: Alias for formal_smt (Z3 SMT formal proofs)")
    config.addinivalue_line("markers", "certificates: Solver verification certificate tests")
```

When an external library (e.g., `z3`, `gudhi`, or `networkx`) is not installed, tests requiring that library are cleanly skipped with an informative diagnostic message rather than failing.

### 4. Dependency Declaration (PEP 735)

In `pyproject.toml`, verification dependencies are declared under the `test` dependency group:

```toml
[dependency-groups]
test = [
    "hypothesis>=6.165.1",
    "numpy",
    "scipy",
    "networkx",
    "sympy",
    "z3-solver>=5.3.1.0",
]
```

### 5. Specification of the 8 Verification Methodologies

#### Methodology 1: Differential Cross-Library Testing (`test_differential_*.py`)
- **Scope:** Sparse matrix operations (`dot`, `power`, `transpose`, `trace`), signal transforms (`dft`, `walsh_hadamard`, `gelfand_transform`, `legendre_fenchel`), graph metrics (Laplacian, Fiedler vector, PageRank), Lie/Galois/Clifford/Group structures, simplicial boundary operators, and streaming statistical moments.
- **Protocol:**
  1. Generate random sparse inputs (density $p \in [0.05, 0.5]$).
  2. Compute result using `algebrax` sparse primitives.
  3. Convert input to dense NumPy array, SciPy CSR matrix, NetworkX graph, or SymPy symbolic object.
  4. Compute reference result via reference library.
  5. Assert equivalence within condition-scaled tolerance ($\text{rtol} = 10^{-12}, \text{atol} = 10^{-12}$, or exact `==` for $\mathbb{Q}$ and $GF(p^m)$).

#### Methodology 2: Metamorphic Invariant Testing (`test_metamorphic_invariants.py`)
- **Scope:** Custom semirings lacking external reference implementations (`ProvenanceSemiring`, `TropicalSemiring`, `MultivariateMomentSemiring`), and high-dimensional operators.
- **Protocol:** Verify that transformed inputs produce algebraically consistent outputs under guaranteed metamorphic relations:
  - $(A \otimes B)^T = B^T \otimes A^T$
  - $\mathcal{F}(\operatorname{shift}_k(x)) = \mathcal{F}(x) \odot e^{-i 2\pi k \mathbf{n} / N}$
  - $d_{k+1}(d_k(\omega)) = \mathbf{0}$
  - $\star \star \omega = (-1)^{k(n-k)} s \omega$
  - $L(P A P^T) = P L(A) P^T$

#### Methodology 3: Property-Based Axiomatic Verification (`test_axiomatic_properties.py`)
- **Scope:** All 34 registered semirings in `Semiring.catalog()`, finite fields $\text{GF}(p^m)$, categories, tries, and lattices in `algebrax`.
- **Protocol:**
  - Test core algebraic axioms: Associativity, Commutativity, Distributivity, Identity, Annihilation by Zero, `nsum`, `power`, and Kleene `star` fixed points.
  - To eliminate floating-point non-associativity false positives, property tests run across two distinct strategies:
    1. **Exact Mode:** Values generated over `fractions.Fraction` or integer rings (strictly testing algebraic logic).
    2. **Conditioned Float Mode:** Values generated over floats with custom epsilon assertion guards.

#### Methodology 4: Schwartz–Zippel Randomized Polynomial Identity Testing (`test_pit_symbolic.py`)
- **Scope:** High-degree symbolic equalities and non-linear algebraic identities (e.g., Lie algebra Jacobi identity across classical and all 5 exceptional simple Lie algebras $\mathfrak{g}_2, \mathfrak{f}_4, \mathfrak{e}_6, \mathfrak{e}_7, \mathfrak{e}_8$, Cayley–Hamilton theorem $p_A(A) = \mathbf{0}$, and Brahmagupta–Fibonacci polynomial identity).
- **Protocol:**
  1. Formulate identity as difference $P(x_1, \dots, x_n) = \text{LHS} - \text{RHS}$.
  2. Sample independent integer coordinates $r_i$ uniformly from $S = [-500, 500]$ ($|S| = 1000$) so that degree-3 products in 248-dimensional $\mathfrak{e}_8$ satisfy $248^2 |r_1 r_2 r_3| \le 7.6 \times 10^{12} \ll 2^{53}$, preserving exact IEEE 754 `float64` integer mantissa precision without ULP overflow.
  3. Evaluate $P(r_1, \dots, r_n)$ using exact integer-float or rational `fractions.Fraction` arithmetic.
  4. Repeat across $k = 6$ independent trials. Under the Schwartz–Zippel Lemma, false-positive error is bounded by:
     $$\Pr[\text{Error}] \le \left(\frac{d}{|S|}\right)^6 \le \left(\frac{2}{1000}\right)^6 = 6.4 \times 10^{-17} < 10^{-16}$$

#### Methodology 5: Method of Manufactured Solutions (`test_mms_sheaves_and_categories.py`)
- **Scope:** Discrete Exterior Calculus (`EP-0160`), Cellular Sheaves (`EP-0161`), discrete Hodge Laplacians, and graph diffusion.
- **Protocol:**
  1. Define a smooth analytical field or manufactured global section $x^*$ on a manifold or $SO(2)$ connection sheaf.
  2. Derive exact forcing residual $f = \mathcal{L} x^*$ or boundary restriction $\partial B$.
  3. Solve the discrete interior boundary-value problem and verify exact analytical recovery and Schur complement equivalence.

#### Methodology 6: Exact Rational & Symbolic Verification (`test_differential_sympy.py` / `test_axiomatic_properties.py`)
- **Scope:** Semiring laws, matrix inversions, determinants, Cayley–Hamilton polynomials, and polynomial rings.
- **Protocol:** Evaluate computations over `fractions.Fraction` or SymPy symbols, verifying bitwise exact closed-form equivalence without floating-point round-off error.

#### Methodology 7: SMT Automated Constraint Solving (`test_smt_z3_proofs.py`)
- **Scope:** Universally quantified algebraic identities over piecewise linear, real, or Boolean arithmetic (`Tropical`, `Arctic`, `Bottleneck`, `Lukasiewicz`, `Boolean`, `DualNumber`/`Expectation`, and $2 \times 2$ tropical matrices).
- **Protocol:** Encode the negation of the algebraic specification in Z3. Assert that `solver.check() == unsat`, proving that no counterexample exists across the entire domain.

#### Methodology 8: Self-Certifying Solvers (`test_certificates.py`)
- **Scope:** $O(N^3)$ decomposition and solver routines (`lu`, `qr`, `cholesky`, `svd`, `cg_solve`, `inverse`, `fiedler_vector`, `pagerank`, `helmholtz_hodge_decomposition`).
- **Protocol:** Verifier functions validate solver outputs in $O(\text{nnz})$ or $O(|E|)$ time via independent algebraic witnesses (e.g., $L^2$ orthogonality residuals $\langle d\alpha, \delta\beta \rangle = 0$, reconstruction norms $\|\omega - (d\alpha + \delta\beta + \gamma)\| \le \epsilon$, curl-free $d_1(d\alpha) = 0$, and divergence-free $\partial_1(\delta\beta) = 0$).

### 6. Phase 5 Child EP Series (Domain & Oracle Decomposition)

While `EP-0180` establishes the foundational 8-layer harness in `tests/verifications/`, full 100% module verification is structured across two waves of focused child EPs (all completed and **[Final]**):

- **Wave 1: Comparative Verification ("Stamp of Trust" vs. Industry Oracles)**
  - **[EP-0181](EP-0181-comparative-verification-linalg-tensors-transforms.md):** Linear Algebra, Factorizations (`lu`, `qr`, `svd`, `cholesky`), Tensors (`einsum`) & Signal Transforms (`dft`, `hilbert`, `walsh_hadamard`, `z_transform`, `gelfand_transform`, `legendre_fenchel`) vs. `NumPy` & `SciPy` **[Final]**.
  - **[EP-0182](EP-0182-comparative-verification-graphs-spectral-semirings.md):** Graph Calculus, Spectral Theory (`pagerank`, `fiedler_vector`, `laplacian_matrix`) & Path Semirings (`Tropical`, `Arctic`, `Boolean`, `Bottleneck`, `Viterbi`) vs. `NetworkX` & `scipy.sparse.csgraph` **[Final]**.
  - **[EP-0183](EP-0183-comparative-verification-symbolic-lie-galois-group.md):** Exact Symbolic Algebra, Lie Algebras, BCH Dynamics, Galois Finite Fields $GF(p^m)$, Clifford Rotors & Group Theory vs. `SymPy` & `scipy.linalg.expm` **[Final]**.
  - **[EP-0184](EP-0184-comparative-verification-topology-probability-automata.md):** Simplicial Homology, Discrete Stokes' Theorem, Information Theory (`entropy`, `kl_divergence`, `js_divergence`) & Automata vs. `scipy.stats` & TDA Manifolds **[Final]**.
- **Wave 2: Intrinsic Mathematical Truths & Deductive Proofs**
  - **[EP-0185](EP-0185-axiomatic-statistical-sheaf-mms-verification.md):** Full 34-Semiring Hypothesis Suite, Streaming Statistical Moment Semirings vs. `scipy.stats`, Categories, Lattices & Cellular Sheaf MMS **[Final]**.
  - **[EP-0186](EP-0186-certificates-pit-and-smt-formal-verification.md):** Universal $O(\text{nnz})$ Proof-Carrying Solver Certificates, Cayley–Hamilton PIT & Automated SMT (`Z3`) Formal Proofs **[Final]**.

---

## Backwards Compatibility

1. **Zero Runtime Impact:** No public API in `src/algebrax/` is broken or deprecated.
2. **Zero Core Dependency Bloat:** All external libraries (NumPy, SciPy, NetworkX, SymPy, Z3) are isolated in `tests/verifications/` and declared exclusively under test dependency groups.
3. **Selective Execution:** Standard test execution (`uv run pytest tests/algebrax`) continues to execute in $< 2\text{s}$ with zero required external dependencies. The verification suite is triggered explicitly via `pytest tests/verifications/`.

---

## How to Teach This / Documentation Plan

1. **Traceability & Stamp of Trust Documentation ([`docs/verification.md`](../verification.md)):** Published in the top-level documentation navigation (`zensical.toml`), mapping every verified `algebrax` function to its exact test in `tests/verifications/`, verification category/marker, external reference oracle, and numerical tolerance, cross-linked from [`docs/guide/semirings/verification.md`](../guide/semirings/verification.md).
2. **Marker-Based CLI Execution:** Documented commands for running the full suite or slicing by category (`-m differential`, `-m axiomatic`, `-m mms`, `-m metamorphic`, `-m pit`, `-m certificates`, `-m smt`).

---

## Reference Implementation

The verification test suite is implemented across 11 files in `tests/verifications/`:
- `tests/verifications/conftest.py` (pytest markers and dependency skip guards)
- `tests/verifications/test_axiomatic_properties.py` (All-34-semiring Hypothesis property suites & exact `Fraction` ring verification — `EP-0180` & `EP-0185`)
- `tests/verifications/test_differential_numpy.py` (25 comparative tests against NumPy & SciPy — `EP-0181`)
- `tests/verifications/test_differential_graphs.py` (16 comparative tests against NetworkX & `scipy.sparse.csgraph` — `EP-0182`)
- `tests/verifications/test_differential_sympy.py` (12 comparative tests against SymPy & `scipy.linalg.expm` — `EP-0183`)
- `tests/verifications/test_differential_topology_prob.py` (10 comparative tests against `scipy.stats` & canonical TDA manifolds — `EP-0184`)
- `tests/verifications/test_differential_statistical_semirings.py` (4 comparative tests for streaming statistical moment semirings vs `scipy.stats` — `EP-0185`)
- `tests/verifications/test_mms_sheaves_and_categories.py` (5 MMS & axiomatic tests for Cellular Sheaves, Categories, Lattices & Tries — `EP-0185`)
- `tests/verifications/test_metamorphic_invariants.py` (8 metamorphic conservation laws across matrices, topology, and transforms — `EP-0180`)
- `tests/verifications/test_pit_symbolic.py` (14 Schwartz–Zippel PIT tests across classical and all 5 exceptional Lie algebras, Cayley–Hamilton, and polynomial rings — `EP-0186`)
- `tests/verifications/test_certificates.py` (6 universal $O(\text{nnz})$ proof-carrying solver certificate verifiers — `EP-0186`)
- `tests/verifications/test_smt_z3_proofs.py` (6 automated deductive SMT formal proofs via `z3-solver` — `EP-0186`)
- [`docs/verification.md`](../verification.md) (Public Verification Traceability Matrix)
- `references/explorations/EXP-0003-correctness-evidence/README.md` (Full architectural compendium)
- `references/explorations/EXP-0003-correctness-evidence/sources/BIBLIOGRAPHY.md` (Scientific bibliography and downloaded source papers)

---

## Rejected Ideas

1. **Naming Directory `tests/correctness_evidence/`:** Rejected as unwieldy and conceptually misplaced. "Correctness Evidence" describes the resulting artifact, report, or telemetry emitted by tests, whereas `tests/verifications/` correctly designates the active testing discipline and directly generalizes `tests/algebrax/test_verification.py`.
2. **Inlining Heavy Dependencies into Core (`src/algebrax`):** Rejected. Violates the core zero-dependency architectural constraint. `AlgebraX` must remain runnable on pure Python environments without C extensions or compiled binaries.
3. **Sole Reliance on Hypothesis with Floats:** Rejected. Floating-point non-associativity produces false failures on legitimate algebraic structures. Separating exact rational carriers from float-tolerance checks preserves mathematical truth.
4. **Full Symbolic Monomial Expansion for High-Degree Identities:** Rejected. Monomial explosion renders full expansion intractable for systems with $> 8$ variables. Schwartz–Zippel PIT provides rigorous, probabilistic equivalence in $O(N)$ evaluation time.
5. **Mandating Lean 4 Installation in CI:** Rejected. Requiring a Lean 4 toolchain and Mathlib4 compilation in standard GitHub Actions runners introduces excessive CI overhead ($> 15\text{min}$ build times). Lean 4 specifications are maintained as offline formal reference models, while SMT/Z3 and Hypothesis provide automated in-pipeline verification.

---

## Open Questions

All initial open questions have been resolved during implementation:
- **Resolved (Certificate Helpers Location):** Solver certificate verifiers reside in `tests/verifications/test_certificates.py` to keep `src/algebrax` lean while testing public decomposition dataclasses (`HodgeDecomposition`, `lu`, `qr`, `svd`, `cholesky`).
- **Resolved (Hypothesis Sample Budget):** Standard CI runs use `@settings(max_examples=20..30)` per property test, achieving full 183-test verification suite execution in $\approx 7\text{s}$ (well within Shannon's $< 15\text{s}$ budget).

---

## Change Log

* **2026-10-24:**
  * Initial proposal formulated from research compendium `references/explorations/EXP-0003-correctness-evidence/README.md` and approved by Grand Council review.
  * Refactored target directory to `tests/verifications/` to directly generalize `tests/algebrax/test_verification.py` and distinguish the verification testing discipline from resulting evidence artifacts.
  * Implemented foundational verification suite, authored public traceability documentation in [`docs/verification.md`](../verification.md), linked child roadmap series `EP-0181` through `EP-0186`, and transitioned status to **Final**.
* **2026-10-25:**
  * Completed full implementation of child series `EP-0181` through `EP-0186` across all 11 modules in `tests/verifications/` (183 total verification tests passing).

