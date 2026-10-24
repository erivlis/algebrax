# Pytest Verification Harness Architecture

## Overview

To serve as a verifiable correctness layer without altering application source code, `algebrax` establishes a dedicated multi-layered verification test suite under `tests/verifications/`. This architecture generalizes and expands the algebraic law smoke testing in [`tests/algebrax/test_verification.py`](../../../../tests/algebrax/test_verification.py) by integrating differential testing, property-based axiom verification, metamorphic testing, Schwartz-Zippel PIT, Method of Manufactured Solutions, exact symbolic verification, and formal specification checks into automated Pytest workflows.

---

## 1. Test Suite Organization

The verification suite is organized under `tests/verifications/`, decoupled from core regression unit tests:

```text
tests/
├── algebrax/                         # Core unit and fast regression tests (zero heavy deps)
│   ├── ...
│   └── test_verification.py          # Fast catalog law smoke tests (algebrax.verification)
└── verifications/                    # Comprehensive Multi-Layered Verification Suite
    ├── conftest.py                   # Custom Pytest fixtures & verification markers
    ├── test_axiomatic_properties.py  # Hypothesis property tests (generalizing test_verification.py)
    ├── test_differential_numpy.py    # Differential testing vs NumPy / SciPy
    ├── test_differential_networkx.py # Differential testing vs NetworkX
    ├── test_differential_gudhi.py    # Differential testing vs GUDHI / Dionysus
    ├── test_metamorphic_invariants.py# Metamorphic relation verification
    ├── test_pit_symbolic.py          # Schwartz-Zippel PIT tests
    ├── test_mms_discrete_calculus.py # Method of Manufactured Solutions (MMS)
    ├── test_exact_rational.py        # Exact rational arithmetic (fractions.Fraction)
    ├── test_smt_z3_proofs.py         # Z3 SMT formal proof verification
    └── test_certificates.py          # Self-certifying solver tests
```

---

## 2. Custom Pytest Marks & CLI Options

### Pytest Custom Marks
- `@pytest.mark.verification`: Marks a test as belonging to the verification suite.
- `@pytest.mark.differential`: Differential tests requiring external reference libraries (e.g. `numpy`, `networkx`).
- `@pytest.mark.axiomatic`: Hypothesis property-based semiring/group/lattice axiom verification.
- `@pytest.mark.metamorphic`: Metamorphic relation tests.
- `@pytest.mark.pit`: Schwartz–Zippel polynomial identity testing.
- `@pytest.mark.mms`: Method of Manufactured Solutions tests.
- `@pytest.mark.formal_smt`: Formal SMT / Z3 symbolic proof tests.
- `@pytest.mark.certificates`: Solver verification certificate tests.

### Command Line Invocation Examples
```bash
# Run the complete verification test suite
uv run pytest tests/verifications/ -m verification -v

# Run only property-based axiomatic semiring tests
uv run pytest tests/verifications/ -m axiomatic -v

# Run differential tests against external libraries
uv run pytest tests/verifications/ -m differential -v
```

---

## 3. Evidence Reporting & CI Artifact Generation

Running the verification suite generates structured correctness evidence reports (JSON summary and OpenMetrics telemetry):

```json
{
  "suite": "AlgebraX Verification Suite",
  "status": "PASSED",
  "summary": {
    "differential_tests_passed": 1420,
    "axiomatic_laws_verified": 3500,
    "metamorphic_invariants_checked": 850,
    "pit_identities_verified": 320,
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
