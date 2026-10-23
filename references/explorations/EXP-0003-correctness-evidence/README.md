# EXP-0003: Correctness Evidence — Multi-Layered Verification Methodologies & Formal Proofs for AlgebraX

| Field           | Value                                                                                                                                                                                                            |
|:----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **EXP**         | 0003                                                                                                                                                                                                             |
| **Title**       | Correctness Evidence: Differential Testing, Property-Based Axiomatic Verification, Metamorphic Invariants, and Lean 4 Formal Proofs |
| **Author**      | Eran Rivlis & Jules (The Explorer & Council Agent)                                                                                                                                                               |
| **Status**      | Active                                                                                                                                                                                                           |
| **Type**        | Architectural & Research Exploration                                                                                                                                                                             |
| **Created**     | 2026-10-12                                                                                                                                                                                                       |
| **Updated**     | 2026-10-12                                                                                                                                                                                                       |
| **Related EPs** | [EP-0099](../../docs/proposals/EP-0099-expansion-roadmap.md), [EP-0110](../../docs/proposals/EP-0110-simplicial-homology.md), [EP-0111](../../docs/proposals/EP-0111-clifford-geometric-algebra.md)               |

---

## 1. Abstract & Context

### 1.1 Context
`AlgebraX` treats Python's native `dict` as a first-class sparse algebraic object, unifying linear algebra, graph algorithms, semiring computations, signal transforms, information metrics, Clifford geometric algebras, and simplicial homology under a single polymorphic pure-Python framework.

Because `AlgebraX` implements foundational mathematical primitives, software correctness is not merely a software engineering convenience—it is a **mathematical imperative**. A bug in a semiring multiplication or graph Laplacian matrix does not just throw a runtime exception; it silently invalidates downstream mathematical calculations, optimization bounds, or topological invariants.

### 1.2 The Core Question
**How can `AlgebraX` systematically supply mathematical correctness evidence by passing `pytest` suites?**
Specifically:
1. How can we verify `AlgebraX` operations by differentially comparing results against canonical, established Python math libraries (e.g., NumPy, SciPy, NetworkX, SymPy, PyTorch, mpmath)?
2. Is formal theorem proving in **Lean 4** possible for Python code, and how can interactive theorem provers or SMT solvers be integrated into the verification pipeline?
3. What additional methodologies (Property-Based Axiomatic Testing, Metamorphic Invariant Testing, Symbolic Verification) are required to achieve 100% mathematical correctness confidence without changing `AlgebraX` application source code?

---

## 2. The Council Framework Alignment

Evaluating correctness evidence methodologies against **The Eight Pillars** (*PRINCIPLES.md*):

1. **Falsifiability (Popper)**: Every mathematical claim (e.g., semiring associativity, boundary nilpotency $\partial^2 = 0$) must be empirically or formally testable against randomly generated counterexamples.
2. **Symmetry (Noether)**: Duality relations (e.g., $(A \otimes B)^T = B^T \otimes A^T$, Hodge star duality $\star \star = \pm I$) must be preserved exactly in test invariant checks.
3. **Efficiency (Shannon)**: The evidence suite must execute rapidly within standard `pytest` workflows, utilizing adaptive sampling in property-based tests.
4. **Safety (The Golem)**: Prevents numerical degradation and subtle algebraic violations from reaching production code.
5. **Clarity (Feynman)**: Test failures must pin-point the precise algebraic axiom violated (e.g., "Left Distributivity failed for TropicalSemiring on negative inf inputs").
6. **Consistency (Russell)**: Ensures zero logical paradoxes between different representations (sparse dict vs. dense NumPy array).
7. **Harmony (The Steward)**: Integrates seamlessly into `pytest` without modifying application source code.
8. **Curiosity (The Explorer)**: Pushes verification beyond basic unit tests into automated theorem proving and SMT constraint satisfaction.

---

## 3. Overview of Correctness Evidence Methodologies

To construct a comprehensive correctness evidence layer, we propose five complementary methodologies operating at different levels of mathematical abstraction:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     Pytest Correctness Evidence Layer                            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                         │
     ┌──────────────────┬────────────────┼────────────────┬──────────────────┐
     ▼                  ▼                ▼                ▼                  ▼
Methodology 1      Methodology 2    Methodology 3    Methodology 4      Methodology 5
Differential       Lean 4 / SMT     Property-Based   Metamorphic        Exact Symbolic
Library Testing    Formal Proofs    Axiomatic (PBT)  Invariants         SymPy Testing
(NumPy/SciPy/NX)   (Lean4 / Z3)     (Hypothesis)     (Dual Relations)   (Exact Rational)
```

---

## 4. Detailed Methodology 1: Differential & Comparative Testing against Canonical Libraries

### 4.1 Concept
Differential testing compares `AlgebraX` sparse dictionary algebraic operations against canonical, battle-tested standard libraries across identical mathematical inputs.

### 4.2 Domain-by-Domain Reference Library Mapping

| AlgebraX Domain | Reference External Library | Mathematical Equivalence Mapping |
|:----------------|:---------------------------|:---------------------------------|
| `algebrax.matrix` | **NumPy** (`ndarray`), **SciPy Sparse** (`csr_matrix`) | Matrix multiplication (`dot`), transpose, power, trace, determinant, block diagonal. |
| `algebrax.transforms` | **NumPy FFT** (`numpy.fft`), **SciPy Signal** | Discrete Fourier Transform (`dft`/`idft`), Walsh-Hadamard, Convolution, Z-transform, Hilbert transform. |
| `algebrax.analysis` | **NetworkX** (`networkx.Graph`), **SciPy Graph** | Graph Laplacians, Forman-Ricci curvature, Fiedler vector, Eigen-centrality, PageRank, Shortest paths. |
| `algebrax.homology` | **GUDHI**, **Dionysus 2**, **SciPy Spatial** | Simplicial complexes, Betti numbers $b_k$, boundary matrices $\partial_k$. |
| `algebrax.clifford` | **clifford** (PyDy), **galgebra** (SymPy) | Geometric product, rotor rotations, multivector reverse, grade projection. |
| `algebrax.galois` | **galois** (Python package), **SageMath** | Finite field matrix multiplication and addition over $\text{GF}(p^m)$. |
| `algebrax.probability` | **SciPy Stats**, **scikit-learn** | Shannon entropy, KL-divergence, Mutual information, Wasserstein distance. |
| `algebrax.tensor` | **PyTorch** (`torch.einsum`), **NumPy** (`np.einsum`) | Sparse tensor einsum contractions, outer products, tensor flattening. |
| `algebrax.automata` | **PyCX**, **Minterpy** | DFA / NFA state transitions and sequence acceptance equivalence. |
| `algebrax.lattice` | **SciPy Hierarchy**, **NetworkX Posets** | Join ($\vee$), Meet ($\wedge$), transitive closure, Hasse diagrams. |
| `algebrax.group` | **SymPy Combinatorics** (`sympy.combinatorics`) | Permutation composition, signature, cycle decomposition. |
| `algebrax.trie` | **pygtrie**, **marisa-trie** | Prefix key lookup, subtree intersection, lattice merging. |

### 4.3 Conversion Layer Architecture
Differential tests utilize bidirectional converters (`algebrax.matrix.to_dense()` / `from_dense()`) to convert sparse nested dictionary matrices to NumPy 2D arrays or SciPy CSR matrices before performing assertions:

```python
import numpy as np
import pytest
import algebrax as ax

def test_differential_matrix_dot_numpy():
    # Sparse AlgebraX Matrix
    A_ax = {0: {0: 2.0, 1: 3.0}, 1: {1: 4.0}}
    B_ax = {0: {1: 5.0}, 1: {0: 1.0, 1: 2.0}}

    # AlgebraX Sparse Matrix Dot Product
    C_ax = ax.matrix.dot(A_ax, B_ax)

    # Dense NumPy Reference Computation
    A_np = np.array([[2.0, 3.0], [0.0, 4.0]])
    B_np = np.array([[0.0, 5.0], [1.0, 2.0]])
    C_np = A_np @ B_np

    # Convert AlgebraX sparse dict result to dense numpy array
    C_ax_dense = ax.matrix.to_dense(C_ax, shape=(2, 2))

    # Assert numerical equivalence within float tolerance
    np.testing.assert_allclose(C_ax_dense, C_np, rtol=1e-12, atol=1e-12)
```

---

## 5. Detailed Methodology 2: Lean 4 Formal Verification & Interactive Theorem Proving

### 5.1 Is Formal Proof Possible for Python Code?
**Yes, but with nuance.** Direct verification of dynamic Python runtime code in Lean 4 is challenging due to dynamic typing, mutability, and interpreter overhead. However, formal mathematical verification of `AlgebraX` algorithms in Lean 4 is achievable through **three distinct architectural pipelines**:

```
Pipeline A: Dual Specification Model in Lean 4
┌────────────────────────────────┐                 ┌────────────────────────────────┐
│  Lean 4 Formal Specification   │   Isomorphism   │ Pure Functional Python Code    │
│  (Mathlib4 Abstract Proofs)    │ ◄─────────────► │ (AlgebraX Execution Primitives) │
└────────────────────────────────┘                 └────────────────────────────────┘

Pipeline B: Python AST Extraction to Lean 4
┌────────────────────────────────┐  AST Transpiler │ Lean 4 Inductive Definitions   │
│ Pure Functional Python AST     │ ──────────────► │ & Automated Proof Obligations  │
└────────────────────────────────┘                 └────────────────────────────────┘

Pipeline C: SMT/Z3 Symbolic Proof Verification
┌────────────────────────────────┐   Symbolic Exec │ Z3 / Lean 4 SMT Solver         │
│ Python Symbolic Matrix Inputs  │ ──────────────► │ (Proves zero counterexamples)  │
└────────────────────────────────┘                 └────────────────────────────────┘
```

### 5.2 Lean 4 & Mathlib4 Formalization Pipeline
In Lean 4, semirings and matrix algebras are formalized using Mathlib's algebraic typeclasses:

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

### 5.3 Automated SMT Proof Integration via PyZ3
For automated execution within `pytest`, SMT solvers like **Z3** can verify that `AlgebraX` semiring logic satisfies algebraic specifications for all symbolic inputs:

```python
import pytest
from z3 import Solver, Real, unsat

def test_z3_formal_proof_tropical_semiring_distributivity():
    # Verify min-plus semiring left distributivity: a + min(b, c) == min(a + b, a + c)
    s = Solver()
    a, b, c = Real('a'), Real('b'), Real('c')

    # Negation of Distributivity Law
    lhs = a + If(b < c, b, c)
    rhs = If((a + b) < (a + c), a + b, a + c)

    s.add(lhs != rhs)

    # If unsat, no counterexample exists -> Formal proof holds universally!
    assert s.check() == unsat
```

---

## 6. Detailed Methodology 3: Property-Based Axiomatic Verification (Hypothesis + Pytest)

### 6.1 Concept
Property-based testing generates thousands of randomized, edge-case mathematical inputs to continuously verify that algebraic axioms hold universally across all 35+ semirings in `AlgebraX`.

### 6.2 Verified Axiom Inventory

1. **Additive & Multiplicative Associativity**:
   $$(a \oplus b) \oplus c = a \oplus (b \oplus c) \quad \text{and} \quad (a \otimes b) \otimes c = a \otimes (b \otimes c)$$
2. **Additive Commutativity**:
   $$a \oplus b = b \oplus a$$
3. **Additive Identity ($\bar{0}$) & Multiplicative Identity ($\bar{1}$)**:
   $$a \oplus \bar{0} = a \quad \text{and} \quad a \otimes \bar{1} = a$$
4. **Left & Right Distributivity**:
   $$a \otimes (b \oplus c) = (a \otimes b) \oplus (a \otimes c)$$
5. **Annihilation by Zero ($\bar{0}$)**:
   $$a \otimes \bar{0} = \bar{0} = \bar{0} \otimes a$$
6. **Lattice Absorption Laws**:
   $$a \wedge (a \vee b) = a \quad \text{and} \quad a \vee (a \wedge b) = a$$

### 6.3 Automated Hypothesis Parameterization
```python
import pytest
from hypothesis import given, strategies as st
import algebrax as ax

ALL_SEMIRINGS = [
    ax.semiring.StandardSemiring(),
    ax.semiring.TropicalSemiring(),
    ax.semiring.ArcticSemiring(),
    ax.semiring.BooleanSemiring(),
    ax.semiring.ViterbiSemiring(),
    ax.semiring.LogSemiring(),
]

@pytest.mark.parametrize("sr", ALL_SEMIRINGS)
@given(a=st.floats(min_value=-1e2, max_value=1e2),
       b=st.floats(min_value=-1e2, max_value=1e2),
       c=st.floats(min_value=-1e2, max_value=1e2))
def test_semiring_distributivity_property(sr, a, b, c):
    # Left Distributivity: a * (b + c) == (a * b) + (a * c)
    lhs = sr.mul(a, sr.add(b, c))
    rhs = sr.add(sr.mul(a, b), sr.mul(a, c))
    assert pytest.approx(lhs) == rhs
```

---

## 7. Detailed Methodology 4: Metamorphic Testing (Invariant Transformations)

### 7.1 Concept
Metamorphic testing verifies **Metamorphic Relations (MRs)**—mathematical necessary conditions linking inputs and transformed outputs—solving the oracle problem for complex custom semirings (`ProvenanceSemiring`, `KnotSemiring`).

### 7.2 Catalog of Metamorphic Relations in AlgebraX

```
1. Transpose Dual Invariant:        dot(A, B)^T == dot(B^T, A^T)  (for commutative semirings)
2. Scalar Homogeneity:              dot(c ⊗ A, B) == c ⊗ dot(A, B)
3. Permutation Conjugacy:           L(P · A · P^T) == P · L(A) · P^T  (Graph Laplacian)
4. Nilpotency of Boundary:          ∂_k ∘ ∂_{k+1} == 0  (Simplicial Homology)
5. DFT Shift Theorem:               F(shift_k(x)) == F(x) · e^{-i 2π k / N}
6. Legendre-Fenchel Involution:      f** == f  (Convex conjugate)
```

---

## 8. Detailed Methodology 5: Exact Symbolic Verification via SymPy

### 8.1 Concept
To eliminate floating-point precision issues, exact symbolic verification replaces numeric inputs with SymPy symbols ($x, y, z$). Evaluating `AlgebraX` functions over SymPy symbols yields exact algebraic expressions that are compared directly against closed-form mathematical theorems.

```python
import sympy as sp
import algebrax as ax

def test_symbolic_determinant_exact():
    a, b, c, d = sp.symbols('a b c d')
    M_sym = {0: {0: a, 1: b}, 1: {0: c, 1: d}}

    # AlgebraX Determinant over SymPy Symbols
    det_ax = ax.matrix.academic.determinant(M_sym)

    # SymPy Reference Determinant
    det_ref = a * d - b * c

    # Exact Symbolic Simplification Asserting Zero Difference
    assert sp.simplify(det_ax - det_ref) == 0
```

---

## 9. Pytest Harness Architecture & Test Suite Organization

### 9.1 Dedicated Directory Structure
The evidence suite is organized under `tests/correctness_evidence/`:

```text
tests/
├── correctness_evidence/
│   ├── conftest.py                   # Custom pytest markers & shared fixtures
│   ├── test_differential_numpy.py    # Differential tests vs NumPy / SciPy
│   ├── test_differential_networkx.py # Differential tests vs NetworkX
│   ├── test_differential_clifford.py # Differential tests vs Clifford / PyDy
│   ├── test_axiomatic_semirings.py   # Hypothesis property-based semiring tests
│   ├── test_metamorphic_invariants.py# Metamorphic relation verification
│   ├── test_symbolic_sympy.py        # SymPy exact symbolic tests
│   └── test_smt_z3_proofs.py         # Formal SMT Z3 proof verification
```

### 9.2 Custom Pytest Marks
```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "evidence: Mark test as belonging to correctness evidence suite")
    config.addinivalue_line("markers", "differential: Differential test against external reference library")
    config.addinivalue_line("markers", "axiomatic: Property-based axiom verification via Hypothesis")
    config.addinivalue_line("markers", "formal_smt: SMT / Z3 formal symbolic proof verification")
```

### 9.3 Executing the Evidence Suite
```bash
# Run the entire correctness evidence suite
uv run pytest tests/correctness_evidence/ -m evidence -v

# Run only formal SMT / property-based tests
uv run pytest tests/correctness_evidence/ -m formal_smt -v
```

---

## 10. Comparative Evaluation & Execution Plan

| Methodology | Verification Level | Implementation Effort | Maintenance Overhead | Execution Speed |
|:------------|:-------------------|:----------------------|:---------------------|:----------------|
| **1. Differential Library Testing** | Empirical vs Standard | Low | Low | Very Fast (< 2s) |
| **2. Lean 4 / SMT Formal Proofs** | Mathematical Proof | Medium-High | Low | Fast (< 3s) |
| **3. Property Axiom Verification** | Continuous Empirical | Medium | Very Low | Moderate (~ 5s) |
| **4. Metamorphic Invariants** | Structural Invariant | Low-Medium | Low | Very Fast (< 1s) |
| **5. Exact Symbolic SymPy** | Closed-Form Symbolic | Low | Low | Fast (< 2s) |

---

## 11. Summary & Next Steps

This exploration establishes the complete blueprint for adding a multi-layered correctness evidence suite to `AlgebraX`. Passing this `pytest` suite guarantees that `AlgebraX`'s sparse dictionary algebraic primitives adhere strictly to mathematical specifications, canonical reference outputs, and formal algebraic laws—without changing any application code.

### Source References & Materials
All reference materials, research papers, and technical specifications are compiled in:
- [`sources/lean4_formal_verification_and_python.md`](./sources/lean4_formal_verification_and_python.md)
- [`sources/property_based_testing_algebraic_axioms.md`](./sources/property_based_testing_algebraic_axioms.md)
- [`sources/differential_and_metamorphic_testing.md`](./sources/differential_and_metamorphic_testing.md)
- [`sources/pytest_evidence_harness_architecture.md`](./sources/pytest_evidence_harness_architecture.md)
