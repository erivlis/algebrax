"""
Tests for the Algebraic Law Verification Engine (`algebrax.verification`).
"""

from __future__ import annotations

import pytest

from algebrax.semiring import Semiring
from algebrax.verification import (
    get_semiring_samples,
    semiring_elements_equal,
    verify_semiring_laws,
)


def test_semiring_elements_equal_basic() -> None:
    """Test element equality comparison across diverse types and edge cases."""
    assert semiring_elements_equal(1.0, 1.0)
    assert semiring_elements_equal(float('inf'), float('inf'))
    assert semiring_elements_equal(float('-inf'), float('-inf'))
    assert not semiring_elements_equal(float('inf'), float('-inf'))
    assert semiring_elements_equal(float('nan'), float('nan'))
    assert semiring_elements_equal(1.0 + 2.0j, 1.0 + 2.0j + 1e-12j)
    assert not semiring_elements_equal(1.0 + 2.0j, 1.0 - 2.0j)
    assert semiring_elements_equal((1.0, 2.0), (1.0, 2.0))
    assert not semiring_elements_equal((1.0, 2.0), (1.0, 2.0, 3.0))
    assert semiring_elements_equal({'a': 1.0}, {'a': 1.0})
    assert not semiring_elements_equal({'a': 1.0}, {'a': 2.0})
    assert not semiring_elements_equal({'a': 1.0}, {'b': 1.0})
    assert not semiring_elements_equal(1.0, 'not_a_float')


@pytest.mark.parametrize('semiring_name', sorted(Semiring.catalog().keys()))
def test_all_catalog_semirings_satisfy_laws(semiring_name: str) -> None:
    """Parametrized test verifying all 33 built-in semirings satisfy the 9 algebraic axioms."""
    semiring, samples = get_semiring_samples(semiring_name)
    results = verify_semiring_laws(semiring, samples)

    for axiom_name, passed in results.items():
        assert passed, f"Semiring '{semiring_name}' failed axiom '{axiom_name}'"


def test_get_semiring_samples_unknown_raises() -> None:
    """Verify get_semiring_samples raises ValueError for unknown semiring names."""
    with pytest.raises(ValueError, match='Unknown semiring'):
        get_semiring_samples('NonExistentSemiring')


def test_verify_semiring_laws_detects_broken_semiring() -> None:
    """Verify that verify_semiring_laws falsifies a broken semiring across all 9 axioms."""

    class BrokenSemiring(Semiring[float]):
        @property
        def zero(self) -> float:
            return 99.0  # Wrong additive identity & non-annihilating

        @property
        def one(self) -> float:
            return -77.0  # Wrong multiplicative identity

        def add(self, a: float, b: float) -> float:
            return a - 2.0 * b + 1.0  # Non-commutative & non-associative

        def mul(self, a: float, b: float) -> float:
            return (a + 1.0) / (abs(b) + 2.0)  # Non-associative & non-distributive

    broken = BrokenSemiring()
    res = verify_semiring_laws(broken, [0.0, 1.0, 2.0, 3.0])
    assert all(not passed for passed in res.values()), f'Expected all 9 axioms to fail, got: {res}'


def test_granular_verifiers_falsify_broken_structures() -> None:
    """Verify that every granular hierarchy verifier detects broken algebraic axioms."""
    from algebrax.verification import (
        verify_add_comm_group_laws,
        verify_band_laws,
        verify_boolean_algebra_laws,
        verify_comm_group_laws,
        verify_comm_monoid_laws,
        verify_comm_ring_laws,
        verify_field_laws,
        verify_group_action_laws,
        verify_lie_algebra_laws,
        verify_magma_laws,
        verify_semimodule_laws,
        verify_algebra_laws,
    )

    class BrokenStructure:
        zero = 99.0
        one = -77.0
        bot = 55.0
        top = -44.0

        def is_zero(self, a: float) -> bool:
            return a == 99.0

        def add(self, a: float, b: float) -> float:
            return a - 2.0 * b + 1.0

        def neg(self, a: float) -> float:
            return a + 5.0

        def sub(self, a: float, b: float) -> float:
            return a + b + 99.0

        def mul(self, a: float, b: float) -> float:
            return 2.0 * a - b + 3.0

        def inv(self, a: float) -> float:
            return a + 7.0  # Also fails zero_division_guard since it does not raise ZeroDivisionError

        def div(self, a: float, b: float) -> float:
            return a - b - 11.0

        def smul(self, r: float, m: float) -> float:
            return r - 2.0 * m + 4.0

        def join(self, a: float, b: float) -> float:
            return a - 2.0 * b + 1.0

        def meet(self, a: float, b: float) -> float:
            return 2.0 * a - b + 3.0

        def complement(self, a: float) -> float:
            return a + 1.0

        def gact(self, g: float, x: float) -> float:
            return g - 2.0 * x + 1.0

    b = BrokenStructure()
    samples = [0.0, 1.0, 2.0]

    assert not all(verify_band_laws(b, samples).values())  # type: ignore[arg-type]
    assert not all(verify_comm_monoid_laws(b, samples).values())  # type: ignore[arg-type]
    assert not all(verify_comm_group_laws(b, samples).values())  # type: ignore[arg-type]
    assert not all(verify_add_comm_group_laws(b, samples).values())  # type: ignore[arg-type]
    assert not all(verify_boolean_algebra_laws(b, samples).values())  # type: ignore[arg-type]
    assert not all(verify_group_action_laws(b, b, samples, samples).values())  # type: ignore[arg-type]
    assert not all(verify_comm_ring_laws(b, samples).values())  # type: ignore[arg-type]
    assert not all(verify_field_laws(b, samples).values())  # type: ignore[arg-type]
    assert not all(verify_semimodule_laws(b, b, samples, samples).values())  # type: ignore[arg-type]
    assert not all(verify_algebra_laws(b, b, samples, samples).values())  # type: ignore[arg-type]
    assert not all(verify_lie_algebra_laws(b, b, samples, samples).values())  # type: ignore[arg-type]

    # Closure failure when operation returns None or raises
    class NoneMagma:
        def mul(self, a: float, b: float) -> None:
            return None

        def add(self, a: float, b: float) -> None:
            raise RuntimeError('boom')

    from algebrax.verification import verify_add_magma_laws

    assert verify_magma_laws(NoneMagma(), samples) == {'mul_closure': False}  # type: ignore[arg-type]
    assert verify_add_magma_laws(NoneMagma(), samples) == {'add_closure': False}  # type: ignore[arg-type]

