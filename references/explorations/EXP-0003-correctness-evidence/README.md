# EXP-0003: Correctness Evidence — Multi-Layered Verification Methodologies & Formal Proofs for AlgebraX

| Field           | Value                                                                                                                                                                                                                                                        |
|:----------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0003                                                                                                                                                                                                                                                         |
| **Title**       | Correctness Evidence: Differential Testing, Property-Based Axiomatic Verification, Metamorphic Invariants, Schwartz–Zippel PIT, Method of Manufactured Solutions (MMS), and Lean 4 Formal Proofs                                                             |
| **Author**      | Eran Rivlis & Jules (The Explorer & Council Agent)                                                                                                                                                                                                           |
| **Status**      | Active                                                                                                                                                                                                                                                       |
| **Type**        | Architectural & Research Exploration                                                                                                                                                                                                                         |
| **Created**     | 2026-10-12                                                                                                                                                                                                                                                   |
| **Updated**     | 2026-10-24                                                                                                                                                                                                                                                   |
| **Related EPs** | [EP-0099](../../docs/proposals/EP-0099-expansion-roadmap.md), [EP-0110](../../docs/proposals/EP-0110-simplicial-homology.md), [EP-0153](../../docs/proposals/EP-0153-semiring-matrix-symmetry-and-vector-primitives.md), [EP-0160](../../docs/proposals/EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md), [EP-0161](../../docs/proposals/EP-0161-cellular-sheaves-and-network-laplacians.md), [EP-0163](../../docs/proposals/EP-0163-lie-algebras-and-bch-dynamics.md) |

---

## 1. Abstract & Context

### 1.1 Context
`AlgebraX` treats Python's native `dict` as a first-class sparse algebraic object, unifying linear algebra, graph algorithms, semiring computations, signal transforms, information metrics, Clifford geometric algebras, discrete exterior calculus, cellular sheaves, and simplicial homology under a polymorphic, pure-Python framework.

Because `AlgebraX` implements foundational mathematical primitives, software correctness is not merely a software engineering convenience—it is a **mathematical imperative**. A silent bug in a semiring multiplication, Lie bracket commutator, or Hodge Laplacian operator does not just raise an exception: it quietly corrupts downstream algebraic invariants, topological Betti numbers, convergence rates, or cryptographic matrix transformations.

### 1.2 The Core Problem: The Test Oracle & Combinatorial Explosions
1. **The Test Oracle Problem:** For advanced topological constructs (e.g., discrete Helmholtz–Hodge decompositions, cellular sheaf Laplacians, persistent homology), canonical precomputed solutions do not exist for arbitrary graph or simplicial complexes.
2. **The Monomial Explosion Problem:** Symbolic engines attempting canonical monomial expansion of algebraic identities (e.g., Jacobi identity in 14-dimensional exceptional Lie algebras, or high-degree multivector products) suffer exponential $\binom{n+d}{d}$ term blowup, timing out standard test suites.
3. **Continuous vs. Discrete Gap:** Operators in discrete exterior calculus and spectral graph theory approximate continuous differential operators; verifying them requires bounding discretization error rather than testing for bitwise identity.
4. **Floating-Point Imprecision vs. Algebraic Axiom Violations:** IEEE 754 floating-point addition is non-associative ($(0.1 + 0.2) + 0.3 \ne 0.1 + (0.2 + 0.3)$). Testing algebraic axioms directly over `float` produces false alarms unless separated into exact rational domains vs. conditioned numerical bounds.

### 1.3 The Core Question
**How can `AlgebraX` systematically provide mathematically rigorous, multi-layered correctness evidence within standard `pytest` workflows without modifying core application source code?**

---

## 2. The Grand Council Review of EXP-0003

Evaluating the expanded correctness evidence architecture against **The Eight Pillars** (*PRINCIPLES.md*):

### 1. Symmetry (Noether) — *Verdict: Strong Endorsement*
* **Review:** Invariant transformations (metamorphic relations) are direct reflections of Noether’s theorem: symmetries imply conservation laws. Checking dualities ($(A \otimes B)^T = B^T \otimes A^T$), Hodge star involutions ($\star \star = (-1)^{k(n-k)} s I$), and adjoint nilpotency ($\operatorname{ad}_{[X, Y]} = [\operatorname{ad}_X, \operatorname{ad}_Y]$) tests the algebraic structure along its natural planes of symmetry.
* **Directive:** Ensure metamorphic tests cover all duality pairings, including left vs. right semiring distributivity and cochain flow projections.

### 2. Falsifiability (Popper) — *Verdict: Unanimous Approval*
* **Review:** Karl Popper's epistemology requires that every claim be falsifiable against aggressive counterexample search. Using Hypothesis property-based testing and Schwartz–Zippel randomized polynomial identity testing (PIT) operationalizes this pillar: if a false identity is claimed, randomized sampling will falsify it with probability $1 - (d/|S|)^k \approx 1$.
* **Directive:** Never rely on hand-picked happy paths. Parametrize generators over boundary singularities (empty matrices, infinite weights, disconnected complexes, degenerate simplices).

### 3. Efficiency (Shannon) — *Verdict: Strong Endorsement with Pruning Mandate*
* **Review:** Full symbolic monomial expansion is Shannon-inefficient ($O(2^N)$ terms). Schwartz–Zippel PIT reduces identity testing to $O(N)$ black-box polynomial evaluations.
* **Directive:** Cap property-based Hypothesis examples to $\le 100$ runs in standard CI pipelines ($< 15\text{s}$ total runtime), reserving $10,000$-run stress tests for nightly schedules.

### 4. Safety (The Golem) — *Verdict: Approved*
* **Review:** Immutability and state containment are reinforced by verification certificates. Solvers returning witnesses (e.g., Hodge orthogonal residuals, condition numbers) allow callers to verify outputs locally without re-running expensive matrix factorizations.
* **Directive:** Mandate that test suites isolate float comparisons using condition-number-scaled tolerances rather than arbitrary magic epsilons.

### 5. Clarity (Feynman) — *Verdict: Approved*
* **Review:** A test failure must teach the engineer *why* the failure occurred. Instead of an opaque assertion failure, property tests must report the specific algebraic axiom violated (e.g., `"Left Distributivity violated for MinPlus semiring with inputs a=-inf, b=0, c=inf"`).
* **Directive:** Reusable property runners must format informative diagnostic failure cards.

### 6. Consistency (Russell) — *Verdict: Approved*
* **Review:** Differential testing eliminates representation dissonance. A computation performed on nested sparse dictionaries in AlgebraX must yield identical results when mapped to dense NumPy arrays, SciPy CSR matrices, or SymPy exact rationals.
* **Directive:** Bidirectional converters (`to_dense`, `from_dense`, `to_cochain`, `to_flow`) must themselves be verified by round-trip identity tests ($f^{-1}(f(x)) = x$).

### 7. Harmony (The Steward) — *Verdict: Approved*
* **Review:** Zero application intrusion. The entire correctness evidence suite resides in `tests/correctness_evidence/` and integrates into standard `pytest`, maintaining zero heavy runtime dependencies in `src/algebrax`.
* **Directive:** External reference libraries (NumPy, SciPy, NetworkX, GUDHI, SymPy, Z3) must remain optional dev/test dependencies managed under PEP 735 dependency groups (`--group test-evidence`).

### 8. Curiosity (The Explorer) — *Verdict: Enthusiastic Endorsement*
* **Review:** Integrating formal theorem proving (Lean 4) and SMT constraint solvers (Z3) extends the library beyond conventional software testing into verified mathematics.
* **Directive:** Explore automated translation of pure-Python ASTs to Lean 4 inductive definitions for core semiring invariants.

---

## 3. Overview of the 8-Layer Correctness Evidence Architecture

To achieve mathematical certainty, AlgebraX establishes **eight complementary verification methodologies** organized into three distinct tiers:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        AlgebraX Multi-Layered Verification Suite                       │
│                         (tests/verifications/ via Pytest)                              │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
[ Tier 1: Empirical & Metamorphic ] [ Tier 2: Exact & Semi-Formal ]  [ Tier 3: Deductive & Certified ]
  1. Cross-Library Differential       4. Schwartz–Zippel PIT (Random)  7. SMT / Z3 Proof Verification
  2. Metamorphic Invariants (MRs)     5. Method of Manufactured Solns   8. Lean 4 Formal Dual Models
  3. Property-Based Axiomatic (PBT)   6. Exact Symbolic & Rational      +. Self-Certifying Solvers
```

| Layer | Methodology | Target Verification Domain | Underlying Oracle / Engine |
|:------|:------------|:---------------------------|:---------------------------|
| **1** | **Differential Cross-Testing** | Matrices, FFTs, Graphs, Tensors | NumPy, SciPy, NetworkX, GUDHI |
| **2** | **Metamorphic Invariant Testing** | Symmetries, Dualities, Nilpotency | Invariant Relations ($f(T(x)) = g(f(x))$) |
| **3** | **Property-Based Axiomatic Testing** | Semirings, Lattices, Groups, Monoids | Hypothesis Random Property Generators |
| **4** | **Schwartz–Zippel Randomized PIT** | High-Degree Symbolic Equivalence | Black-Box Numeric Evaluation over $\mathbb{Z}_p$ |
| **5** | **Method of Manufactured Solutions (MMS)** | Discrete Exterior Calculus, Laplacians | Exact Analytic PDE Derivatives & Rates |
| **6** | **Exact Rational & Symbolic Testing** | Determinants, Exact Axioms | `fractions.Fraction`, SymPy Symbols |
| **7** | **SMT Automated Proof Verification** | Bounded Universal Algebraic Proofs | Z3 Theorem Prover (`z3-solver`) |
| **8** | **Lean 4 Dual-Specification Models** | Foundational Semiring / Complex Proofs | Lean 4 + Mathlib4 Reference Proofs |

---

## 4. Methodology 1: Differential Testing Against Canonical Math Libraries

Differential testing executes identical mathematical inputs across AlgebraX and trusted reference engines, asserting numerical or structural equivalence.

### 4.1 Canonical Reference Mapping

| AlgebraX Domain | Reference External Library | Mathematical Equivalence Mapping |
|:----------------|:---------------------------|:---------------------------------|
| `algebrax.matrix` | **NumPy** (`ndarray`), **SciPy Sparse** (`csr_matrix`) | Matrix multiplication (`dot`), transpose, trace, power, determinant, block diagonal. |
| `algebrax.transforms` | **NumPy FFT** (`numpy.fft`), **SciPy Signal** | Discrete Fourier Transform (`dft`/`idft`), Walsh-Hadamard, Convolution, Hilbert transform. |
| `algebrax.analysis` | **NetworkX** (`networkx.Graph`), **SciPy Graph** | Graph Laplacians, Forman-Ricci curvature, Fiedler vector, PageRank, Shortest paths. |
| `algebrax.homology` | **GUDHI**, **Dionysus 2**, **SciPy Spatial** | Simplicial complexes, Betti numbers $b_k$, boundary operators $\partial_k$. |
| `algebrax.clifford` | **clifford** (PyDy), **galgebra** (SymPy) | Geometric product, rotor rotations, multivector reverse, grade projection. |
| `algebrax.galois` | **galois** (Python package), **SageMath** | Finite field matrix multiplication and addition over $\text{GF}(p^m)$. |
| `algebrax.probability` | **SciPy Stats**, **scikit-learn** | Shannon entropy, KL-divergence, Mutual information, Wasserstein distance. |
| `algebrax.tensor` | **PyTorch** (`torch.einsum`), **NumPy** (`np.einsum`) | Sparse tensor einsum contractions, outer products, tensor flattening. |

### 4.2 Differential Test Pattern
```python
import numpy as np
import pytest
import algebrax as ax

def test_differential_matrix_dot_numpy():
    A_ax = {0: {0: 2.0, 1: 3.0}, 1: {1: 4.0}}
    B_ax = {0: {1: 5.0}, 1: {0: 1.0, 1: 2.0}}

    C_ax = ax.matrix.dot(A_ax, B_ax)

    A_np = np.array([[2.0, 3.0], [0.0, 4.0]])
    B_np = np.array([[0.0, 5.0], [1.0, 2.0]])
    C_np = A_np @ B_np

    C_ax_dense = ax.matrix.to_dense(C_ax, shape=(2, 2))
    np.testing.assert_allclose(C_ax_dense, C_np, rtol=1e-12, atol=1e-12)
```

---

## 5. Methodology 2: Metamorphic Testing (Invariant Relations)

Metamorphic testing verifies mathematical necessary conditions without requiring an external oracle:

```
                        Random Mathematical Input X
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
     Transform Input: T(X)                       Standard Input: X
               │                                         │
               ▼                                         ▼
      AlgebraX Algorithm                        AlgebraX Algorithm
      Y_transformed = f(T(X))                     Y_standard = f(X)
               │                                         │
               └────────────────────┬────────────────────┘
                                    ▼
                         Metamorphic Relation Check
                         Verify: Y_transformed == g(Y_standard)
```

### 5.1 Catalog of Verified Relations
1. **Transpose Dual Invariant:** $(A \otimes B)^T \equiv B^T \otimes A^T$ (for commutative semirings).
2. **Scalar Homogeneity:** $c \otimes (A \otimes B) \equiv (c \otimes A) \otimes B$.
3. **Graph Automorphism Conjugacy:** For permutation matrix $P$, $L(P A P^T) \equiv P L(A) P^T$.
4. **Boundary Nilpotency:** $\partial_k \circ \partial_{k+1} \equiv \mathbf{0}$ and coboundary $d_{k+1} \circ d_k \equiv \mathbf{0}$.
5. **Hodge Star Involution:** On $k$-forms in $n$-dimensions: $\star \star \omega \equiv (-1)^{k(n-k)} s \omega$.
6. **DFT Circular Shift Theorem:** $\mathcal{F}(\operatorname{shift}_k(x)) \equiv \mathcal{F}(x) \odot e^{-i 2\pi k \mathbf{n} / N}$.

---

## 6. Methodology 3: Property-Based Axiomatic Verification (Hypothesis)

Hypothesis executes randomized property-based testing over formal algebraic axioms across all 35+ semirings, lattices, and Lie algebras in `algebrax`.

### 6.1 Axiom Suite
* **Associativity:** $(a \oplus b) \oplus c = a \oplus (b \oplus c)$ and $(a \otimes b) \otimes c = a \otimes (b \otimes c)$.
* **Commutativity:** $a \oplus b = b \oplus a$.
* **Distributivity:** $a \otimes (b \oplus c) = (a \otimes b) \oplus (a \otimes c)$ and $(a \oplus b) \otimes c = (a \otimes c) \oplus (b \otimes c)$.
* **Identities & Annihilation:** $a \oplus \bar{0} = a$, $a \otimes \bar{1} = a$, $a \otimes \bar{0} = \bar{0} \otimes a = \bar{0}$.
* **Lie Jacobi Identity:** $[x, [y, z]] + [y, [z, x]] + [z, [x, y]] = \mathbf{0}$.

### 6.2 Separating Floats from Pure Axioms
To avoid false failures from floating-point non-associativity, property tests execute in two complementary modes:
1. **Exact Rational Carriers:** Testing axioms over `fractions.Fraction` or integer rings (where associativity is exact).
2. **Approximate Float Carriers:** Testing with scaled epsilon thresholds ($|a - b| \le \epsilon$).

---

## 7. Methodology 4: Schwartz–Zippel Randomized Polynomial Identity Testing (PIT)

### 7.1 The Breakthrough for Symbolic Equivalence
Testing high-dimensional symbolic identities via full monomial expansion (e.g. SymPy) suffers from combinatorial explosion ($\binom{n+d}{d}$). 

Under the **Schwartz–Zippel Lemma**, an unexpanded polynomial expression $P(x_1, \dots, x_n) \equiv 0$ of total degree $d$ evaluated at random coordinates sampled uniformly from finite subset $S \subset \mathbb{F}$ satisfies:

$$\Pr[P(r_1, \dots, r_n) = 0] \le \frac{d}{|S|}$$

### 7.2 PIT Algorithm for AlgebraX
1. Construct the symbolic identity as an evaluation pipeline $P = \text{LHS} - \text{RHS}$.
2. Sample independent integers $r_i \in S = [1, 10^6]$.
3. Evaluate using exact integer arithmetic (preventing rounding errors).
4. Repeat across $k = 3$ independent trials. The probability of an accidental root is bounded by:

$$\left(\frac{d}{|S|}\right)^3 \le \left(\frac{10}{10^6}\right)^3 = 10^{-15}$$

---

## 8. Methodology 5: Method of Manufactured Solutions (MMS) for Discrete Calculus

### 8.1 Continuous to Discrete Convergence Order Verification
In Discrete Exterior Calculus (`EP-0160`), Hodge Laplacians (`EP-0101`, `EP-0152`), and Cellular Sheaves (`EP-0161`), verifying implementation correctness requires verifying asymptotic convergence to continuous calculus:

1. **Manufacture Smooth Potential:** Define smooth analytical continuous field $\phi(x, y) = \sin(2\pi x) \cos(2\pi y)$.
2. **Analytic Continuous Operators:** Compute analytical gradient $\mathbf{u} = \nabla \phi$ and Laplacian $\psi = \Delta \phi = -8\pi^2 \phi$.
3. **De Rham Discretization:** Sample 0-forms on vertex coordinates of planar triangulation meshes $\mathcal{K}_h$ of spacing $h$.
4. **Discrete Operator Evaluation:** Compute discrete Hodge-Laplacian $\Delta_h \phi_h = (\star^{-1} d^T \star d) \phi_h$.
5. **Asymptotic Order Assertion:** Verify that $L_2$ error $\| \Delta_h \phi_h - \Pi_h(\psi) \|_{L_2}$ decays as $O(h^2)$ across a mesh hierarchy.

---

## 9. Methodology 6: Exact Rational & Symbolic Verification

Using Python's standard `fractions.Fraction` carrier or SymPy exact symbols, AlgebraX sparse matrices and semiring operations are evaluated without floating-point approximations:

```python
from fractions import Fraction
import algebrax as ax

def test_exact_rational_matrix_determinant():
    A = {
        0: {0: Fraction(1, 3), 1: Fraction(2, 5)},
        1: {0: Fraction(3, 7), 1: Fraction(4, 9)}
    }
    # Determinant computed with exact rational arithmetic
    det = ax.matrix.academic.determinant(A)
    expected = Fraction(1, 3) * Fraction(4, 9) - Fraction(2, 5) * Fraction(3, 7)
    assert det == expected  # Bitwise exact rational equivalence!
```

---

## 10. Methodology 7: SMT Automated Constraint Verification (PyZ3)

Satisfiability Modulo Theories (SMT) solvers like **Z3** prove that algebraic invariants hold for all possible bounded symbolic inputs:

```python
import pytest
from z3 import Solver, Real, If, unsat

def test_z3_formal_proof_tropical_semiring_distributivity():
    s = Solver()
    a, b, c = Real('a'), Real('b'), Real('c')

    # Negation of Distributivity Law
    lhs = a + If(b < c, b, c)
    rhs = If((a + b) < (a + c), a + b, a + c)

    s.add(lhs != rhs)
    # If unsat, no counterexample exists anywhere in R -> Universal formal proof!
    assert s.check() == unsat
```

---

## 11. Methodology 8: Lean 4 Dual-Specification Models

Interactive theorem proving in **Lean 4** establishes machine-checked mathematical proofs of core algorithms:

```lean
import Mathlib.Algebra.Semiring.Basic
import Mathlib.Data.Matrix.Basic

-- Formal proof in Lean 4 that matrix multiplication over any lawful Semiring is associative
theorem matrix_mul_assoc {n m k l : Type*} [Fintype n] [Fintype m] [Fintype k] [Fintype l]
    [DecidableEq n] [DecidableEq m] [DecidableEq k] [DecidableEq l]
    {R : Type*} [Semiring R]
    (A : Matrix n m R) (B : Matrix m k R) (C : Matrix k l R) :
    (A * B) * C = A * (B * C) := by
  exact Matrix.mul_assoc A B C
```

---

## 12. Certified Computation & Proof-Carrying Solvers

For complex numerical or topological solvers, verifying a certificate is asymptotically cheaper ($O(E)$) than computing the result ($O(N^3)$):

```
┌────────────────────────────────────────────────────────┐
│                   Solver Execution                     │
│  (e.g., Helmholtz-Hodge Decomposition: O(N^3) Pseudoinv)│
└──────────────────────────┬─────────────────────────────┘
                           │ Returns (Solution, Certificate)
                           ▼
┌────────────────────────────────────────────────────────┐
│               Certificate Verifier                     │
│  1. Orthogonality:  <dα, δβ> == 0                      │
│  2. Residual:       ||v - (dα + δβ + γ)|| < tol        │
│  3. Harmonicity:    ||Δ γ|| == 0                       │
│  Complexity:        O(E) Sparse Matrix-Vector Ops      │
└────────────────────────────────────────────────────────┘
```

---

## 13. Pytest Verification Harness Architecture & Test Organization

Generalizing the algebraic law smoke tests in `tests/algebrax/test_verification.py` (EP-0131), the comprehensive multi-layered verification test suite is housed in `tests/verifications/`, decoupled from core regression unit tests:

```text
tests/
├── algebrax/                         # Core unit and fast regression tests (zero heavy deps)
│   ├── ...
│   └── test_verification.py          # Fast catalog law smoke tests (algebrax.verification)
└── verifications/                    # Multi-Layered Verification Suite
    ├── conftest.py                   # Custom pytest markers & fixtures
    ├── test_axiomatic_properties.py  # Hypothesis property tests (generalizing test_verification.py)
    ├── test_differential_numpy.py    # Differential tests vs NumPy / SciPy
    ├── test_differential_networkx.py # Differential tests vs NetworkX
    ├── test_differential_gudhi.py    # Differential tests vs GUDHI / Dionysus
    ├── test_metamorphic_invariants.py# Metamorphic invariant relations
    ├── test_pit_symbolic.py          # Schwartz-Zippel PIT tests
    ├── test_mms_discrete_calculus.py # Method of Manufactured Solutions
    ├── test_exact_rational.py        # Fractions / exact rational tests
    ├── test_smt_z3_proofs.py         # Z3 formal SMT verification
    └── test_certificates.py          # Self-certifying solver tests
```

### Pytest Marks
```bash
# Run complete verification suite
uv run pytest tests/verifications/ -m verification -v

# Run only fast differential & property tests
uv run pytest tests/verifications/ -m "differential or axiomatic" -v

# Run formal SMT / PIT verification
uv run pytest tests/verifications/ -m "formal_smt or pit" -v
```

---

## 14. Comparative Evaluation Matrix (8 Methodologies)

| Methodology | Verification Level | Implementation Effort | Maintenance Overhead | Execution Speed | Primary Catch |
|:---|:---|:---|:---|:---|:---|
| **1. Differential Cross-Testing** | Canonical Empirical | Low | Low | Very Fast (< 2s) | Behavioral mismatches, sign flips |
| **2. Metamorphic Invariants** | Structural Invariant | Low-Medium | Low | Very Fast (< 1s) | Oracle-free transformations, dualities |
| **3. Property Axiom (Hypothesis)** | Universal Empirical | Medium | Very Low | Moderate (~ 4s) | Edge-case boundary bugs, corner cases |
| **4. Schwartz–Zippel PIT** | Probabilistic Exact | Medium | Very Low | Fast (< 2s) | High-degree symbolic equality without blowup |
| **5. Method of Manufactured Solns** | Asymptotic Discretization | Medium | Low | Fast (< 3s) | Discretization errors, Laplacian scaling |
| **6. Exact Rational & Symbolic** | Exact Mathematical | Low | Low | Fast (< 2s) | Float imprecision false alarms |
| **7. SMT / Z3 Proofs** | Formal Proof (Bounded) | Medium-High | Low | Fast (< 3s) | Universal algebraic non-distributivity |
| **8. Lean 4 Formal Models** | Deductive Verification | High | Low | Offline / External | True abstract structural correctness |

---

## 15. Summary & Downstream EP Roadmapping

This exploration serves as the scientific foundation for proposing **[`EP-0180: Multi-Layered Verification Test Architecture`](../../docs/proposals/EP-0180-multi-layered-verification-suite.md)**, which establishes the formal test harness in `tests/verifications/`, dependency specifications under `test-verification`, CI pipeline stages, and certified solver protocols in `AlgebraX`.

---

## 16. Scientific Bibliography & Source Repository

All seminal papers, technical reports, and monographs cited across this exploration are compiled and indexed in:

* **[Scientific Bibliography & Source Repository](./sources/BIBLIOGRAPHY.md)**

### Archived Primary Source Papers:
1. **[Chen et al. (1998/2020) — Metamorphic Testing](./sources/papers/chen_1998_metamorphic_testing.md)** ([PDF](./sources/papers/chen_1998_metamorphic_testing.pdf) | arXiv:2002.12543)
2. **[MacIver & Hatfield-Dodds (2019) — Hypothesis](./sources/papers/maciver_2019_hypothesis.md)** ([PDF](./sources/papers/maciver_2019_hypothesis.pdf) | JOSS 10.21105/joss.01891)
3. **[The Mathlib Community (2019/2020) — The Lean mathematical library](./sources/papers/mathlib_2019_lean_mathematical_library.md)** ([PDF](./sources/papers/mathlib_2019_lean_mathematical_library.pdf) | arXiv:1910.09336)
4. **[Saxena (2014) — Progress on Polynomial Identity Testing – II](./sources/papers/saxena_2014_progress_on_polynomial_identity_testing.md)** ([PDF](./sources/papers/saxena_2014_progress_on_polynomial_identity_testing.pdf) | arXiv:1401.0976)
5. **[Salari & Knupp (2000) — Code Verification by the Method of Manufactured Solutions](./sources/papers/salari_knupp_2000_method_manufactured_solutions.md)** (Sandia SAND2000-1444 | DOI: 10.2172/759450)
6. **[McKeeman (1998) — Differential Testing for Software](./sources/papers/mckeeman_1998_differential_testing.md)** (Digital Technical Journal 10(1): 100–107)
