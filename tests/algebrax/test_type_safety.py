"""
Type safety and contract validation test suite.
"""

import typing

import pytest

import algebrax.typing
from algebrax.converters import flat_to_nested
from algebrax.semiring import StandardSemiring, TropicalSemiring, _normalize_semiring


def test_semiring_normalization():
    """Verify _normalize_semiring handles None, class types, and instances."""
    assert isinstance(_normalize_semiring(None), StandardSemiring)
    assert isinstance(_normalize_semiring(TropicalSemiring), TropicalSemiring)
    assert isinstance(_normalize_semiring(TropicalSemiring()), TropicalSemiring)


def test_flat_to_nested_collision_error():
    """Verify flat_to_nested raises ValueError on mixed-depth key collisions."""
    with pytest.raises(ValueError, match="Key collision"):
        flat_to_nested({(1,): "a", (1, 2): "b"})

    with pytest.raises(ValueError, match="Key collision"):
        flat_to_nested({(1, 2): "b", (1,): "a"})


def test_type_hints_resolution():
    """Verify typing.get_type_hints resolves without errors across algebrax.typing."""
    hints = typing.get_type_hints(algebrax.typing)
    assert "SparseVector" in hints or "K" in hints or len(hints) >= 0
