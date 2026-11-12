---
title: "EP-0003: Axiomatic Verification, Falsification & Multi-Layered Testing"
description: "Establishes the foundational correctness architecture: the public algebraic verification engine, floating-point tolerance invariants, property-based testing, and the 8-layer verification test harness."
icon: lucide/shield-check
status: draft
---

# EP-0003: Axiomatic Verification, Falsification & Multi-Layered Testing

| Field             | Value                                                                                                 |
|:------------------|:------------------------------------------------------------------------------------------------------|
| **EP**            | 0003                                                                                                  |
| **Title**         | Axiomatic Verification, Falsification & Multi-Layered Testing                                         |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                           |
| **Sponsor**       | The Grand Council                                                                                     |
| **Delegate**      | 🔬 Karl Popper (Falsifiability) & ⚖️ Emmy Noether (Symmetry)                                           |
| **Status**        | Draft                                                                                                 |
| **Type**          | Standards Track                                                                                       |
| **Created**       | 2026-11-12                                                                                            |
| **Updated**       | 2026-11-12                                                                                            |
| **Replaces**      | [EP-0131](EP-0131-algebraic-law-verification.md), [EP-0180](EP-0180-multi-layered-verification-suite.md) |
| **Superseded-By** | —                                                                                                     |

---

## Abstract

In foundational mathematical computing, software correctness is not an aspirational goal; it is a **mathematical imperative**. As mandated by [EP-0001](EP-0001-mathematical-manifesto-core-invariants-and-foundational-canon.md), every mathematical structure must be accompanied by an executable, property-based falsification oracle.

This proposal establishes the universal **Axiomatic Verification & Testing Architecture** across AlgebraX:
1. **The Public Verification Engine (`algebrax.verification`)**: Over 40 public law verification oracles testing mathematical axioms (groups, rings, fields, modules, Lie algebras, Jordan algebras, alternative algebras, sheaves, bundles) with rigorous floating-point equivalence predicates (`semiring_elements_equal`).
2. **The 8-Layer Multi-Tier Verification Test Suite (`tests/verifications/`)**:
   - *Empirical & Metamorphic Tier*: Cross-library differential testing (NumPy, SciPy, NetworkX, SymPy), metamorphic symmetry relations, and Hypothesis property-based testing.
   - *Exact & Semi-Formal Tier*: Schwartz–Zippel randomized polynomial identity testing (PIT) to defeat monomial explosion, and the Method of Manufactured Solutions (MMS) for discrete calculus.
   - *Deductive & Certified Tier*: SMT/Z3 formal proofs and $O(\operatorname{nnz})$ proof-carrying solver certificates.

This proposal elevates, generalizes, and supersedes [EP-0131](EP-0131-algebraic-law-verification.md) and [EP-0180](EP-0180-multi-layered-verification-suite.md) into the single-digit foundational canon.

---

## Motivation

Standard software unit tests check only known "happy paths" against hardcoded expected values. In abstract algebra and discrete differential geometry, this produces catastrophic blind spots:

1. **The Test Oracle Problem**: For high-dimensional non-associative structures (octonions, exceptional Lie algebras $E_8$) or discrete Laplacians on unstructured simplicial meshes, closed-form analytical solutions do not exist for arbitrary topologies.
2. **Monomial Explosion**: Expanding symbolic expressions $(x \cdot y) \cdot z - x \cdot (y \cdot z)$ symbolically leads to combinatorial blowup ($O(2^N)$ monomials), causing symbolic CAS engines to hang.
3. **Floating-Point Non-Associativity vs. Bug Masking**: IEEE 754 floating-point addition is non-associative ($(a + b) + c \neq a + (b + c)$). Naive equality checks report false alarms, whereas loose epsilons mask genuine implementation defects.
4. **Dependency Bleed**: Testing against mature external libraries (NumPy, SciPy, NetworkX, SymPy, Z3) is vital for comparative correctness, but importing them inside `src/algebrax` violates the Shannon Zero-Dependency Carrier Invariant.

---

## Rationale & Council Alignment

- **🔬 Karl Popper (Falsifiability & Randomized Search)**:
  *"Assume the happy path is a lie."* Every algebraic structure is subjected to property-based fuzzing across millions of edge cases (degenerate simplices, empty matrices, infinite weights, zero divisors) to aggressively attempt to falsify its claimed axioms.
- **⚖️ Emmy Noether (Symmetries & Metamorphic Invariants)**:
  Where input-output oracles do not exist, tests verify fundamental symmetry conservation laws:
  - Hodge star involution: $\star \star \omega = (-1)^{k(n-k)} s \omega$.
  - Boundary nilpotency: $\partial_k \circ \partial_{k+1} = \mathbf{0}$ and coboundary nilpotency $d^{k+1} \circ d^k = \mathbf{0}$.
  - Connection parallel transport inversion: $U_{ij} U_{ji} = I$.
  - Gauge transformation covariance: $d_{\tilde{A}}(\tilde{\phi}) = g \cdot (d_A \phi)$.
- **⚡ Claude Shannon (Efficiency & Schwartz–Zippel PIT)**:
  Replaces exponential monomial expansion with $O(N)$ randomized polynomial identity testing over finite fields or integers, bounding the false-negative probability to $< 10^{-15}$.
- **🛡️ The Golem (Safety & Self-Certifying Solvers)**:
  High-complexity solvers ($O(N^3)$ Hodge decomposition, spectral graph partitioning) emit lightweight $O(E)$ proof certificates (orthogonality residuals, harmonicity norms), preventing corrupt states from leaking across architectural boundaries.
- **The Steward (Harmony & Zero Runtime Bleed)**:
  Application code in `src/algebrax` remains 100% pure Python with zero heavy dependencies. All heavy external tools (NumPy, SciPy, NetworkX, SymPy, Z3) are strictly isolated in `tests/verifications/` as optional dev-dependencies.

---

## Specification

### 1. The Public Verification Engine (`algebrax.verification`)

The public engine [`algebrax.verification`](file:///C:/dev/erivlis/algebrax/src/algebrax/verification.py) exports standardized, deterministic verifiers for every algebraic variety in AlgebraX:

```python
def verify_semiring_laws(semiring: Semiring[T], samples: list[T], tol: float = 1e-12) -> dict[str, bool]: ...
def verify_group_laws(group: Group[V], samples: list[V], tol: float = 1e-12) -> dict[str, bool]: ...
def verify_ring_laws(ring: Ring[V], samples: list[V], tol: float = 1e-12) -> dict[str, bool]: ...
def verify_module_laws(module: Module[R, M], ring: Ring[R], r_samples: list[R], m_samples: list[M], tol: float = 1e-12) -> dict[str, bool]: ...
def verify_jordan_laws(jordan: JordanAlgebra[R, M], samples: list[M], tol: float = 1e-12) -> dict[str, bool]: ...
def verify_alternative_laws(alt: AlternativeAlgebra[R, M], samples: list[M], tol: float = 1e-12) -> dict[str, bool]: ...
def verify_malcev_laws(malcev: MalcevAlgebra[R, M], samples: list[M], tol: float = 1e-12) -> dict[str, bool]: ...
def verify_coboundary_nilpotency(d_k: SparseMatrix[Any, Any], d_next: SparseMatrix[Any, Any], tol: float = 1e-12) -> bool: ...
def verify_gauge_covariance(bundle: DiscreteConnection[float], gauge: dict[Any, SparseMatrix[Any, float]], tol: float = 1e-10) -> dict[str, bool]: ...
```

#### Floating-Point Equality Predicate
```python
def semiring_elements_equal(a: Any, b: Any, tol: float = 1e-12) -> bool:
    """Robust equivalence handling floats, complex numbers, exact rationals, and sparse dicts."""
    ...
```

---

### 2. The 8-Layer Multi-Tier Test Suite (`tests/verifications/`)

The multi-layered verification harness is organized into three distinct tiers:

```text
tests/
├── algebrax/                                    # Core fast regression tests (< 2s, zero heavy deps)
│   └── test_verification.py                     # In-tree smoke test for algebrax.verification
└── verifications/                               # The 8-Layer Verification Test Suite
    ├── conftest.py                              # Pytest markers and dynamic skip-guards
    │
    │   ── TIER 1: EMPIRICAL & METAMORPHIC ──
    ├── test_axiomatic_properties.py             # Hypothesis randomized property fuzzing (EP-0185)
    ├── test_metamorphic_invariants.py           # Invariant relation tests (Stokes, dualities)
    ├── test_differential_numpy.py               # Sparse matrix vs NumPy / SciPy (EP-0181)
    ├── test_differential_graphs.py              # PageRank, Laplacians vs NetworkX (EP-0182)
    ├── test_differential_sympy.py               # Exact Lie, Galois, Clifford vs SymPy (EP-0183)
    ├── test_differential_topology_prob.py       # Simplicial complexes vs GUDHI / SciPy (EP-0184)
    ├── test_mms_sheaves_and_categories.py       # Manufactured solutions on complex sheaves
    │
    │   ── TIER 2: EXACT & SEMI-FORMAL ──
    ├── test_pit_symbolic.py                     # Schwartz–Zippel Randomized PIT (EP-0186)
    │
    │   ── TIER 3: DEDUCTIVE & CERTIFIED ──
    ├── test_smt_z3_proofs.py                    # Automated formal proofs via Z3 SMT solver
    └── test_certificates.py                     # O(nnz) proof-carrying solver witnesses
```

---

### 3. Pytest Markers & Dependency Isolation

All verification tests use dedicated markers defined in `tests/verifications/conftest.py`:
- `@pytest.mark.axiomatic`: Hypothesis property-based tests.
- `@pytest.mark.differential`: Cross-library comparison (skipped if library missing).
- `@pytest.mark.metamorphic`: Metamorphic symmetry invariance.
- `@pytest.mark.pit`: Polynomial Identity Testing.
- `@pytest.mark.smt`: Z3 SMT formal proofs.
- `@pytest.mark.certificates`: Proof-carrying solver verification.

---

## Backwards Compatibility

1. **Fully Backwards-Compatible**: All public verification routines in `algebrax.verification` maintain identical signatures and behavior.
2. **Replaces EP-0131 & EP-0180**: Both earlier proposals are formally superseded by this unified foundational standard.

---

## How to Teach This / Documentation Plan

1. **User Guides**:
   - `docs/guide/verification/` documents how users can test custom algebraic structures using `algebrax.verification`.
2. **Developer Standards**:
   - Any new Layer 2 protocol or concrete algebra must add a corresponding `verify_*_laws` oracle in `src/algebrax/verification.py` and a test file in `tests/algebrax/` or `tests/verifications/`.

---

## Reference Implementation

- **Verification Engine**: [`src/algebrax/verification.py`](file:///C:/dev/erivlis/algebrax/src/algebrax/verification.py).
- **Multi-Layered Harness**: `tests/verifications/`.
- **Precedent Proposals**:
  - [`docs/proposals/EP-0131-algebraic-law-verification.md`](EP-0131-algebraic-law-verification.md)
  - [`docs/proposals/EP-0180-multi-layered-verification-suite.md`](EP-0180-multi-layered-verification-suite.md)

---

## Rejected Ideas

1. **Placing Heavy Dependencies in `src/algebrax`**:
   *Rejected*: Violates the Shannon Carrier Invariant. External solvers belong strictly in optional test harnesses.
2. **Relying Exclusively on SymPy for Axiom Proofs**:
   *Rejected*: Symbolic expansion suffers from exponential monomial blowup. Schwartz–Zippel randomized PIT provides a rigorous, fast alternative.

---

## Open Questions

None. The verification engine and test suite are actively running in CI across all platforms.

---

## Change Log

- **2026-08-02**: Initial verification engine specified as EP-0131.
- **2026-10-24**: Multi-layered test architecture specified as EP-0180.
- **2026-11-12**: Unified and elevated to single-digit foundational canon as EP-0003.
