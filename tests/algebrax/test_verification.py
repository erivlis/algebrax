"""
Tests for the Algebraic Law Verification Engine.
"""

import pytest

from algebrax.semiring import Semiring
from algebrax.verification import (
    get_semiring_samples,
    semiring_elements_equal,
    verify_semiring_laws,
)


def test_semiring_elements_equal_basic():
    """Test element equality comparison across diverse types."""
    assert semiring_elements_equal(1.0, 1.0)
    assert semiring_elements_equal(float('inf'), float('inf'))
    assert semiring_elements_equal(float('-inf'), float('-inf'))
    assert not semiring_elements_equal(float('inf'), float('-inf'))
    assert semiring_elements_equal((1.0, 2.0), (1.0, 2.0))
    assert semiring_elements_equal({'a': 1.0}, {'a': 1.0})
    assert not semiring_elements_equal({'a': 1.0}, {'a': 2.0})


@pytest.mark.parametrize('semiring_name', sorted(Semiring.catalog().keys()))
def test_all_catalog_semirings_satisfy_laws(semiring_name: str):
    """
    Parametrized test verifying all 23 built-in semirings satisfy the 9 algebraic axioms.
    """
    semiring, samples = get_semiring_samples(semiring_name)
    results = verify_semiring_laws(semiring, samples)

    for axiom_name, passed in results.items():
        assert passed, f"Semiring '{semiring_name}' failed axiom '{axiom_name}'"
