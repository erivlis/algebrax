"""Unit & Falsification Tests for `algebrax.group` (Permutations, FiniteGroup, Cosets & Quotients)."""

from __future__ import annotations

import pytest

from algebrax.algebra import (
    CommGroup,
    Group,
    HasContains,
    HasInv,
    HasMul,
    HasOne,
    LawAssociative,
    LawCommutative,
)
from algebrax.group import (
    FiniteCommGroup,
    FiniteGroup,
    alternating_group,
    compose,
    conjugacy_classes,
    cyclic_group,
    dihedral_group,
    direct_product,
    invert,
    quaternion_group,
    signature,
    symmetric_group,
)
from algebrax.verification import verify_group_laws


def test_compose() -> None:
    f = {0: 1, 1: 2, 2: 0}
    g = {0: 0, 1: 2, 2: 1}
    h = compose(f, g)
    assert h == {0: 2, 1: 1, 2: 0}


def test_invert() -> None:
    f = {0: 1, 1: 2, 2: 0}
    inv = invert(f)
    assert inv == {1: 0, 2: 1, 0: 2}


def test_signature() -> None:
    assert signature({0: 0, 1: 1, 2: 2}) == 1
    assert signature({0: 1, 1: 0, 2: 2}) == -1
    assert signature({0: 1, 1: 2, 2: 0}) == 1


def test_signature_broken() -> None:
    with pytest.raises(ValueError):
        signature({0: 1})


def test_canonical_finite_groups_satisfy_group_laws() -> None:
    """Verify FiniteGroup and FiniteCommGroup inherit protocols/mixins and satisfy axioms."""
    assert {Group, HasContains, LawAssociative}.issubset(FiniteGroup.__mro__)
    assert {FiniteGroup, CommGroup, LawCommutative}.issubset(FiniteCommGroup.__mro__)
    groups = [
        cyclic_group(5),
        dihedral_group(4),
        quaternion_group(),
        symmetric_group(3),
        alternating_group(4),
        direct_product(cyclic_group(2), cyclic_group(3)),
    ]
    for grp in groups:
        for proto in (Group, HasOne, HasMul, HasInv, HasContains, LawAssociative):
            assert isinstance(grp, proto)
        assert grp.is_associative is True
        assert grp.contains(grp.one)
        laws = verify_group_laws(grp, grp.elements)
        assert all(laws.values()), f'Group laws failed for {grp}: {laws}'

    # From Cayley table round-trip (promotes abelian tables to FiniteCommGroup automatically)
    c3 = cyclic_group(3)
    assert isinstance(c3, FiniteCommGroup)
    assert isinstance(c3, CommGroup)
    assert c3.is_commutative is True
    c3_from_table = FiniteGroup.from_cayley_table(c3.cayley_table(), name='C_3_table')
    assert isinstance(c3_from_table, FiniteCommGroup)
    assert c3_from_table.one == 0
    assert c3_from_table.order == 3
    assert c3_from_table.is_abelian()
    assert c3_from_table.div(1, 2) == 2


def test_finite_comm_group_promotion_and_falsification() -> None:
    """Verify automatic abelian promotion across constructors/operations and non-abelian rejection."""
    # Small canonical abelian cases promote to FiniteCommGroup automatically
    for abelian_grp in (
        cyclic_group(6),
        dihedral_group(1),
        dihedral_group(2),
        symmetric_group(1),
        symmetric_group(2),
        alternating_group(1),
        alternating_group(2),
        alternating_group(3),
        direct_product(cyclic_group(2), dihedral_group(2)),
    ):
        assert isinstance(abelian_grp, FiniteCommGroup)
        assert isinstance(abelian_grp, CommGroup)
        assert isinstance(abelian_grp, LawCommutative)
        assert abelian_grp.is_abelian() is True
        assert abelian_grp.conjugacy_classes() == [(g,) for g in abelian_grp.elements]
        assert abelian_grp.center() is abelian_grp
        assert abelian_grp.centralizer(abelian_grp.one) is abelian_grp
        assert abelian_grp.is_normal([abelian_grp.one]) is True
        assert abelian_grp.normalizer([abelian_grp.one]) is abelian_grp

    # Subgroups and quotients of a FiniteCommGroup stay FiniteCommGroup
    c6 = cyclic_group(6)
    sub_c3 = c6.subgroup([2], generate=True, name='C_3')
    assert isinstance(sub_c3, FiniteCommGroup)
    assert sub_c3.order == 3
    quot_c2 = c6.quotient(sub_c3)
    assert isinstance(quot_c2, FiniteCommGroup)
    assert quot_c2.order == 2

    # Non-abelian groups remain FiniteGroup (not CommGroup), while abelian raw group can narrow via as_commutative()
    s3 = symmetric_group(3)
    assert not isinstance(s3, CommGroup)
    with pytest.raises(ValueError, match='not abelian'):
        s3.as_commutative()
    with pytest.raises(ValueError, match='commutative'):
        FiniteCommGroup(
            elements=s3.elements,
            identity=s3.identity,
            mul_fn=s3.mul_fn,
            inv_fn=s3.inv_fn,
            name='S_3',
        )
    s3_table = s3.cayley_table()
    with pytest.raises(ValueError, match='commutative'):
        FiniteCommGroup.from_cayley_table(s3_table)

    raw_c4 = FiniteGroup(
        elements=(0, 1, 2, 3),
        identity=0,
        mul_fn=lambda a, b: (a + b) % 4,
    )
    assert isinstance(raw_c4.as_commutative(), FiniteCommGroup)


def test_subgroups_cosets_normalizers_and_quotients() -> None:
    """Verify conjugacy classes, centers, coset actions, double cosets, and quotient groups."""
    s3 = symmetric_group(3)
    assert not s3.is_abelian()
    assert isinstance(s3, Group)
    assert not isinstance(s3, CommGroup)
    assert s3.order == 6
    assert s3.center().order == 1
    assert isinstance(s3.center(), FiniteCommGroup)
    assert sorted(len(c) for c in s3.conjugacy_classes()) == [1, 2, 3]
    assert s3.order_of((1, 2, 0)) == 3
    assert s3.order_of((1, 0, 2)) == 2

    # Subgroup generation: <(1, 2, 0)> == A_3 (normal of index 2, abelian -> FiniteCommGroup)
    a3_gen = s3.subgroup([(1, 2, 0)], generate=True, name='A_3')
    assert isinstance(a3_gen, FiniteCommGroup)
    assert a3_gen.order == 3
    assert set(a3_gen.elements) == set(alternating_group(3).elements)
    assert s3.is_normal(a3_gen)
    assert s3.normalizer(a3_gen).order == 6

    # Cosets and coset action g * g_j = g_i * h
    reps, action = s3.coset_action(a3_gen)
    assert len(reps) == 2
    assert reps[0] == s3.one
    for g in s3:
        for j, gj in enumerate(reps):
            i, h = action(g, j)
            assert h in a3_gen
            assert s3.mul(g, gj) == s3.mul(reps[i], h)

    # Quotient group S_3 / A_3 ~= C_2 (abelian -> FiniteCommGroup)
    q_s3_a3 = s3.quotient(a3_gen)
    assert isinstance(q_s3_a3, FiniteCommGroup)
    assert q_s3_a3.order == 2
    assert q_s3_a3.is_abelian()
    non_id = next(el for el in q_s3_a3 if el != q_s3_a3.one)
    assert q_s3_a3.mul(non_id, non_id) == q_s3_a3.one

    # Non-normal reflection subgroup H = {e, (1, 0, 2)}: double cosets & quotient rejection
    h_refl = s3.subgroup([(1, 0, 2)], generate=True)
    assert isinstance(h_refl, FiniteCommGroup)
    assert h_refl.order == 2
    assert not s3.is_normal(h_refl)
    assert s3.normalizer(h_refl).order == 2
    d_cosets = s3.double_cosets(h_refl, h_refl)
    assert sorted(len(dc) for dc in d_cosets) == [2, 4]
    assert len(s3.double_coset_representatives(h_refl, h_refl)) == 2

    with pytest.raises(ValueError, match='not normal'):
        s3.quotient(h_refl)

    # Quaternion group Q_8: center Z(Q_8) = {1, -1}, quotient Q_8 / Z(Q_8) ~= V_4 (abelian of order 4)
    q8 = quaternion_group()
    z_q8 = q8.center()
    assert isinstance(z_q8, FiniteCommGroup)
    assert set(z_q8.elements) == {'1', '-1'}
    v4_quot = q8.quotient(z_q8)
    assert isinstance(v4_quot, FiniteCommGroup)
    assert v4_quot.order == 4
    assert v4_quot.is_abelian()
    assert all(verify_group_laws(v4_quot, v4_quot.elements).values())
    assert all(v4_quot.order_of(el) in (1, 2) for el in v4_quot)
    assert len(conjugacy_classes(q8.elements, q8.mul, q8.inv)) == 5
