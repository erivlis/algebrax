# Pytest Correctness Evidence Harness Architecture

## Overview

To serve as a verifiable correctness layer without altering application source code, `algebrax` requires a dedicated Pytest evidence test suite architecture. This architecture integrates differential testing, property-based axiom verification, metamorphic testing, symbolic verification, and formal specification checks into automated Pytest workflows.

---

## 1. Test Suite Organization

The correctness evidence suite is isolated in a dedicated test directory:

```text
tests/
├── correctness_evidence/             # Dedicated Correctness Evidence Suite
│   ├── conftest.py                   # Custom Pytest fixtures & evidence markers
│   ├── test_differential_numpy.py    # Differential testing vs NumPy / SciPy
│   ├── test_differential_networkx.py # Differential testing vs NetworkX
│   ├── test_differential_clifford.py # Differential testing vs Clifford/SymPy
│   ├── test_axiomatic_semirings.py   # Property-based axiom tests (Hypothesis)
│   ├── test_metamorphic_invariants.py# Metamorphic relation verification
│   ├── test_symbolic_sympy.py        # Exact symbolic verification via SymPy
│   └── test_smt_z3_verification.py   # Z3 SMT formal proof verification
```

---

## 2. Custom Pytest Marks & CLI Options

### Pytest Custom Marks
- `@pytest.mark.evidence`: Marks a test as belonging to the formal correctness evidence layer.
- `@pytest.mark.differential`: Differential tests requiring external reference libraries (e.g. `numpy`, `networkx`).
- `@pytest.mark.axiomatic`: Hypothesis property-based semiring/group/lattice axiom verification.
- `@pytest.mark.metamorphic`: Metamorphic relation tests.
- `@pytest.mark.formal_smt`: Formal SMT / Z3 symbolic proof tests.

### Command Line Invocation Examples
```bash
# Run the complete correctness evidence layer
uv run pytest tests/correctness_evidence/ -m evidence -v

# Run only property-based axiomatic semiring tests
uv run pytest tests/correctness_evidence/ -m axiomatic -v

# Run differential tests against external libraries
uv run pytest tests/correctness_evidence/ -m differential -v
```

---

## 3. Evidence Reporting & CI Artifact Generation

The evidence suite outputs structured evidence metrics (JSON / Markdown summary report) upon passing:

```json
{
  "suite": "AlgebraX Correctness Evidence Layer",
  "status": "PASSED",
  "summary": {
    "differential_tests_passed": 1420,
    "axiomatic_laws_verified": 3500,
    "metamorphic_invariants_checked": 850,
    "symbolic_proofs_passed": 120
  },
  "coverage_by_domain": {
    "matrix": "100% Verified against NumPy/SciPy",
    "semirings": "100% (35/35 semirings verified under Hypothesis)",
    "homology": "Boundary nilpotency (d^2 = 0) verified",
    "clifford": "Clifford sandwich rotor products verified"
  }
}
```
