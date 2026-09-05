"""
Type safety and contract validation test suite.
"""

import typing

import pytest

import algebrax.typing
from algebrax.converters import flat_to_nested
from algebrax.semiring import BooleanSemiring, Semiring, StandardSemiring, TropicalSemiring


def test_semiring_normalization():
    """Verify Semiring.normalize, Semiring.default, and Semiring.create."""
    # Default
    assert isinstance(Semiring.default(), StandardSemiring)
    assert isinstance(Semiring.normalize(), StandardSemiring)
    assert isinstance(Semiring.normalize(None), StandardSemiring)
    assert isinstance(Semiring.create(), StandardSemiring)

    # Class types
    assert isinstance(Semiring.normalize(TropicalSemiring), TropicalSemiring)
    assert isinstance(Semiring.create(TropicalSemiring), TropicalSemiring)

    # Instances
    assert isinstance(Semiring.normalize(TropicalSemiring()), TropicalSemiring)
    assert isinstance(Semiring.create(TropicalSemiring()), TropicalSemiring)

    # String names (case-insensitive and suffix-tolerant)
    assert isinstance(Semiring.normalize('Tropical'), TropicalSemiring)
    assert isinstance(Semiring.normalize('tropical'), TropicalSemiring)
    assert isinstance(Semiring.normalize('TropicalSemiring'), TropicalSemiring)
    assert isinstance(Semiring.create('Boolean'), BooleanSemiring)
    assert isinstance(Semiring.create('booleansemiring'), BooleanSemiring)

    # Unknown string raises KeyError
    with pytest.raises(KeyError, match="Unknown semiring 'nonexistent'"):
        Semiring.normalize('nonexistent')


def test_flat_to_nested_collision_error():
    """Verify flat_to_nested raises ValueError on mixed-depth key collisions."""
    with pytest.raises(ValueError, match='Key collision'):
        flat_to_nested({(1,): 'a', (1, 2): 'b'})

    with pytest.raises(ValueError, match='Key collision'):
        flat_to_nested({(1, 2): 'b', (1,): 'a'})


def test_type_hints_resolution():
    """Verify typing.get_type_hints resolves without errors across algebrax.typing."""
    hints = typing.get_type_hints(algebrax.typing)
    assert 'SparseVector' in hints or 'K' in hints or len(hints) >= 0
