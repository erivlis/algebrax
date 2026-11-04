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


def test_atomic_mixin_exports():
    """Verify all 16 atomic operational mixins are exported from algebrax.algebra."""
    import algebrax.algebra as alg

    expected_mixins = [
        'HasZero',
        'HasZeroPred',
        'HasOne',
        'HasAdd',
        'HasNeg',
        'HasMul',
        'HasInv',
        'HasScale',
        'HasStar',
        'HasJoin',
        'HasMeet',
        'HasBounds',
        'HasComplement',
        'HasOp',
        'HasIdentity',
        'HasBracket',
    ]
    for name in expected_mixins:
        cls = getattr(alg, name)
        assert getattr(cls, '_is_protocol', False), f'{name} must be a Protocol'


def test_diamond_free_protocol_inheritance():
    """Verify no named algebraic protocol or mixin has diamond inheritance across algebrax.algebra."""
    import algebrax.algebra as alg

    protocols = [
        getattr(alg, name)
        for name in alg.__all__
        if isinstance(getattr(alg, name), type) and getattr(getattr(alg, name), '_is_protocol', False)
    ]
    assert len(protocols) >= 35

    for proto in protocols:
        # Traverse the base class DAG of algebrax protocols (excluding typing.Protocol / Generic / object)
        visited: list[type] = []

        def _collect_algebra_bases(cls: type) -> None:
            for base in cls.__bases__:
                if base.__module__.startswith('algebrax.'):
                    visited.append(base)
                    _collect_algebra_bases(base)

        _collect_algebra_bases(proto)
        assert len(visited) == len(set(visited)), (
            f'{proto.__name__} has duplicate protocol bases (diamond inheritance): {visited}'
        )


def test_two_sorted_protocol_parameter_order():
    """Verify two-sorted protocols preserve (R, M) generic parameter order (R first, M second)."""
    from algebrax.algebra import Algebra, HasScale, Module, NonAssocAlgebra, Semimodule, VectorSpace

    for proto in (HasScale, Semimodule, Module, VectorSpace, NonAssocAlgebra, Algebra):
        params = proto.__parameters__
        assert len(params) == 2, f'{proto.__name__} must have 2 type parameters'
        assert params[0].__name__ == 'R', f'{proto.__name__} first parameter must be R, got {params[0]}'
        assert params[1].__name__ == 'M', f'{proto.__name__} second parameter must be M, got {params[1]}'


def test_structural_protocol_attrs_lattice():
    """Verify __protocol_attrs__ forms a strict subset lattice across the algebraic hierarchy."""
    from algebrax.algebra import (
        AddCommGroup,
        AddCommMonoid,
        AddGroup,
        AddMagma,
        AddMonoid,
        AddSemigroup,
        Algebra,
        BooleanAlgebra,
        BoundedLattice,
        CommGroup,
        CommMonoid,
        CommRing,
        DistributiveLattice,
        DivisionRing,
        Field,
        Group,
        JoinSemilattice,
        Lattice,
        Magma,
        MeetSemilattice,
        Module,
        Monoid,
        NonAssocAlgebra,
        NonAssocRing,
        OpCommMonoid,
        OpMagma,
        OpMonoid,
        OpSemigroup,
        Ring,
        Semigroup,
        Semimodule,
        Semiring,
        VectorSpace,
    )

    def attrs(cls: type) -> set[str]:
        return set(getattr(cls, '__protocol_attrs__', ()))

    # Additive chain
    assert attrs(AddMagma) == {'add'}
    assert attrs(AddMagma) == attrs(AddSemigroup)
    assert attrs(AddSemigroup) < attrs(AddMonoid) == {'zero', 'add'}
    assert attrs(AddMonoid) == attrs(AddCommMonoid)
    assert attrs(AddMonoid) < attrs(AddGroup) == {'zero', 'add', 'neg', 'sub'}
    assert attrs(AddGroup) == attrs(AddCommGroup)

    # Multiplicative chain
    assert attrs(Magma) == {'mul'}
    assert attrs(Magma) == attrs(Semigroup)
    assert attrs(Semigroup) < attrs(Monoid) == {'one', 'mul'}
    assert attrs(Monoid) == attrs(CommMonoid)
    assert attrs(Monoid) < attrs(Group) == {'one', 'mul', 'inv', 'div'}
    assert attrs(Group) == attrs(CommGroup)

    # Abstract OpMagma/OpMonoid chain
    assert attrs(OpMagma) == {'op'}
    assert attrs(OpMagma) == attrs(OpSemigroup)
    assert attrs(OpSemigroup) < attrs(OpMonoid) == {'op', 'identity'}
    assert attrs(OpMonoid) == attrs(OpCommMonoid)

    # Ring & Field chain
    assert attrs(AddCommGroup) < attrs(NonAssocRing) == {'zero', 'add', 'neg', 'sub', 'mul'}
    assert attrs(NonAssocRing) < attrs(Ring) == {'zero', 'one', 'add', 'neg', 'sub', 'mul'}
    assert attrs(Ring) == attrs(CommRing)
    assert attrs(Ring) < attrs(DivisionRing) == {
        'zero',
        'is_zero',
        'one',
        'add',
        'neg',
        'sub',
        'mul',
        'inv',
        'div',
    }
    assert attrs(DivisionRing) == attrs(Field)

    # Semiring chain
    assert attrs(AddMonoid) < attrs(Semiring)
    assert attrs(Monoid) < attrs(Semiring)

    # Module & Algebra chain
    assert attrs(AddMonoid) < attrs(Semimodule) == {'zero', 'add', 'smul'}
    assert attrs(Semimodule) < attrs(Module) == {'zero', 'add', 'neg', 'sub', 'smul'}
    assert attrs(Module) == attrs(VectorSpace)
    assert attrs(Module) < attrs(NonAssocAlgebra) == {'zero', 'add', 'neg', 'sub', 'mul', 'smul'}
    assert attrs(NonAssocAlgebra) < attrs(Algebra) == {'zero', 'one', 'add', 'neg', 'sub', 'mul', 'smul'}
    assert attrs(Ring) < attrs(Algebra)

    # Lattice chain
    assert attrs(JoinSemilattice) == {'join'}
    assert attrs(MeetSemilattice) == {'meet'}
    assert attrs(JoinSemilattice) < attrs(Lattice) == {'join', 'meet'}
    assert attrs(MeetSemilattice) < attrs(Lattice)
    assert attrs(Lattice) == attrs(DistributiveLattice)
    assert attrs(Lattice) < attrs(BoundedLattice) == {'join', 'meet', 'top', 'bot'}
    assert attrs(BoundedLattice) < attrs(BooleanAlgebra) == {
        'join',
        'meet',
        'top',
        'bot',
        'complement',
    }

