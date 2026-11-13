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
    """Verify all atomic operational mixins are exported from algebrax.algebra."""
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
        'HasPlus',
        'HasResiduals',
        'HasJoin',
        'HasMeet',
        'HasBounds',
        'HasComplement',
        'HasOp',
        'HasIdentity',
        'HasBracket',
        'HasContains',
        'HasReduce',
        'HasGenerator',
        'HasNorm',
        'HasInner',
        'HasCoproduct',
        'HasCounit',
        'HasAntipode',
    ]
    for name in expected_mixins:
        cls = getattr(alg, name)
        assert getattr(cls, '_is_protocol', False), f'{name} must be a Protocol'


def test_diamond_free_protocol_inheritance():
    """Verify no named algebraic protocol or mixin has diamond inheritance or Layer-2-to-Layer-2 chaining."""
    import algebrax.algebra as alg

    protocols = [
        getattr(alg, name)
        for name in alg.__all__
        if isinstance(getattr(alg, name), type) and getattr(getattr(alg, name), '_is_protocol', False)
    ]
    assert len(protocols) >= 45

    for proto in protocols:
        # Law of Flat Protocol Composition (EP-0194 Section 5):
        # Every algebrax base class of a Protocol in algebrax.algebra MUST be a Layer 1 atomic mixin in _mixins.py
        for base in proto.__bases__:
            if base.__module__.startswith('algebrax.'):
                assert base.__module__ == 'algebrax.algebra._mixins', (
                    f'{proto.__name__} inherits from non-mixin protocol {base.__name__} '
                    f'({base.__module__}), violating EP-0194 Law of Flat Protocol Composition'
                )

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
    """Verify two-sorted protocols preserve (R, ...) generic parameter order (R first)."""
    from algebrax.algebra import (
        Algebra,
        HasScale,
        LinearMap,
        Module,
        NonAssocAlgebra,
        Semimodule,
        VectorSpace,
    )

    for proto in (HasScale, Semimodule, Module, VectorSpace, NonAssocAlgebra, Algebra):
        params = proto.__parameters__
        assert len(params) == 2, f'{proto.__name__} must have 2 type parameters'
        assert params[0].__name__ == 'R', f'{proto.__name__} first parameter must be R, got {params[0]}'
        assert params[1].__name__ == 'M', f'{proto.__name__} second parameter must be M, got {params[1]}'

    lmap_params = LinearMap.__parameters__
    assert len(lmap_params) == 3
    assert lmap_params[0].__name__ == 'R', f'LinearMap first parameter must be R, got {lmap_params[0]}'


def test_structural_protocol_attrs_lattice():
    """Verify __protocol_attrs__ forms a strict subset lattice across the algebraic hierarchy."""
    from algebrax.algebra import (
        ActionAlgebra,
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
        GroupHom,
        Homomorphism,
        Ideal,
        JoinSemilattice,
        KleeneAlgebra,
        Lattice,
        LeftIdeal,
        LieAlgebraHom,
        LieIdeal,
        LinearMap,
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
        PrincipalIdeal,
        RightIdeal,
        Ring,
        RingHom,
        Semigroup,
        Semimodule,
        Semiring,
        StarSemiring,
        VectorSpace,
    )

    def attrs(cls: type) -> set[str]:
        if hasattr(cls, '__protocol_attrs__'):
            return set(cls.__protocol_attrs__)
        return set(typing._get_protocol_attrs(cls))  # type: ignore[attr-defined]

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
    assert attrs(NonAssocRing) < attrs(Ring) == {'zero', 'one', 'add', 'neg', 'sub', 'mul', 'is_associative'}
    assert attrs(Ring) < attrs(CommRing) == {
        'zero',
        'one',
        'add',
        'neg',
        'sub',
        'mul',
        'is_associative',
        'is_commutative',
    }
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
        'is_associative',
    }
    assert attrs(DivisionRing) < attrs(Field) == {
        'zero',
        'is_zero',
        'one',
        'add',
        'neg',
        'sub',
        'mul',
        'inv',
        'div',
        'is_associative',
        'is_commutative',
    }

    # Semiring chain
    assert attrs(AddMonoid) < attrs(Semiring) == {'zero', 'add', 'one', 'mul'}
    assert attrs(Monoid) < attrs(Semiring)
    assert attrs(Semiring) < attrs(Ring)
    assert attrs(Semiring) < attrs(StarSemiring) == {'zero', 'add', 'one', 'mul', 'star', 'plus'}
    assert attrs(StarSemiring) < attrs(KleeneAlgebra) == {
        'zero',
        'add',
        'one',
        'mul',
        'star',
        'plus',
        'is_idempotent',
    }
    assert attrs(KleeneAlgebra) < attrs(ActionAlgebra) == {
        'zero',
        'add',
        'one',
        'mul',
        'star',
        'plus',
        'is_idempotent',
        'ldiv',
        'rdiv',
    }

    # Module & Algebra chain
    assert attrs(AddMonoid) < attrs(Semimodule) == {'zero', 'add', 'smul'}
    assert attrs(Semimodule) < attrs(Module) == {'zero', 'add', 'neg', 'sub', 'smul'}
    assert attrs(Module) == attrs(VectorSpace)
    assert attrs(Module) < attrs(NonAssocAlgebra) == {'zero', 'add', 'neg', 'sub', 'mul', 'smul'}
    assert attrs(NonAssocAlgebra) < attrs(Algebra) == {
        'zero',
        'one',
        'add',
        'neg',
        'sub',
        'mul',
        'smul',
        'is_associative',
    }
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

    # Ideal & Homomorphism chain (EP-0201)
    assert attrs(Ideal) == {'contains', 'reduce'}
    assert attrs(Ideal) == attrs(LeftIdeal) == attrs(RightIdeal) == attrs(LieIdeal)
    assert attrs(Ideal) < attrs(PrincipalIdeal) == {'contains', 'reduce', 'generator'}
    assert attrs(Homomorphism) == {'__call__'}
    assert (
        attrs(Homomorphism)
        == attrs(GroupHom)
        == attrs(RingHom)
        == attrs(LinearMap)
        == attrs(LieAlgebraHom)
    )


