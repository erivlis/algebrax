"""
Pytest configuration and custom fixtures for the Verification Test Architecture.
"""

from __future__ import annotations

import importlib.util
from typing import Any

import pytest

HAS_NUMPY = importlib.util.find_spec('numpy') is not None
HAS_SCIPY = importlib.util.find_spec('scipy') is not None
HAS_NETWORKX = importlib.util.find_spec('networkx') is not None
HAS_SYMPY = importlib.util.find_spec('sympy') is not None
HAS_Z3 = importlib.util.find_spec('z3') is not None
HAS_HYPOTHESIS = importlib.util.find_spec('hypothesis') is not None


def pytest_configure(config: Any) -> None:
    """Register custom markers for the verification suite."""
    config.addinivalue_line('markers', 'verification: Part of the multi-layered verification suite')
    config.addinivalue_line('markers', 'differential: Cross-library differential tests (NumPy/SciPy/NetworkX)')
    config.addinivalue_line('markers', 'axiomatic: Property-based testing of algebraic axioms via Hypothesis')
    config.addinivalue_line('markers', 'metamorphic: Metamorphic invariant relations and dualities')
    config.addinivalue_line('markers', 'pit: Schwartz-Zippel Polynomial Identity Testing (probabilistic exact)')
    config.addinivalue_line('markers', 'mms: Method of Manufactured Solutions for discrete differential operators')
    config.addinivalue_line('markers', 'formal_smt: SMT / Z3 formal symbolic proof verification')
    config.addinivalue_line('markers', 'certificates: Self-certifying solver witness verification')


@pytest.fixture
def requires_numpy() -> None:
    """Skip test if NumPy is not available."""
    if not HAS_NUMPY:
        pytest.skip('NumPy is required for this differential test')


@pytest.fixture
def requires_scipy() -> None:
    """Skip test if SciPy is not available."""
    if not HAS_SCIPY:
        pytest.skip('SciPy is required for this differential test')


@pytest.fixture
def requires_networkx() -> None:
    """Skip test if NetworkX is not available."""
    if not HAS_NETWORKX:
        pytest.skip('NetworkX is required for this differential test')


@pytest.fixture
def requires_sympy() -> None:
    """Skip test if SymPy is not available."""
    if not HAS_SYMPY:
        pytest.skip('SymPy is required for this symbolic verification test')


@pytest.fixture
def requires_z3() -> None:
    """Skip test if Z3 is not available."""
    if not HAS_Z3:
        pytest.skip('Z3 solver is required for this SMT formal verification test')
