"""
Polymorphic algebraic helpers for exponentiation, scalar multiples, and sequence folding.
"""

from collections.abc import Iterable
from typing import TypeVar

from algebrax.algebra._group import AddGroup, Group
from algebrax.algebra._monoid import AddMonoid, Monoid, OpMonoid

V = TypeVar('V')


def power(monoid: Monoid[V] | OpMonoid[V], a: V, n: int) -> V:
    r"""Compute the $n$-th power of $a$ via logarithmic binary exponentiation ($O(\log n)$).

    Args:
        monoid: Monoid instance providing `mul` and `one` (or `op` and `identity`).
        a: Base element.
        n: Non-negative exponent integer ($n \ge 0$).

    Returns:
        $a^n \in V$.

    Raises:
        ValueError: If $n < 0$.
    """
    if n < 0:
        raise ValueError(f'power requires non-negative n, got {n}. Use zpow for groups.')
    if n == 0:
        return getattr(monoid, 'one', getattr(monoid, 'identity', None))  # type: ignore[return-value]

    mul_fn = getattr(monoid, 'mul', getattr(monoid, 'op', None))
    res = getattr(monoid, 'one', getattr(monoid, 'identity', None))
    base = a
    while n > 0:
        if n % 2 == 1:
            res = mul_fn(res, base)
        base = mul_fn(base, base)
        n //= 2
    return res


def zpow(group: Group[V], a: V, n: int) -> V:
    r"""Compute the integer power $a^z$ for any $z \in \mathbb{Z}$ in a Group.

    Args:
        group: Group instance.
        a: Base element.
        n: Integer exponent ($n \in \mathbb{Z}$).

    Returns:
        $a^n \in V$, where $a^{-k} = (a^{-1})^k$.
    """
    if n >= 0:
        return power(group, a, n)
    inv_a = group.inv(a)
    return power(group, inv_a, -n)


def nsum(monoid: AddMonoid[V], a: V, n: int) -> V:
    r"""Compute the $n$-fold addition $n \cdot a$ via logarithmic binary scalar multiplication.

    Args:
        monoid: AddMonoid instance providing `add` and `zero`.
        a: Base element.
        n: Non-negative integer multiple ($n \ge 0$).

    Returns:
        $n \cdot a \in V$.

    Raises:
        ValueError: If $n < 0$.
    """
    if n < 0:
        raise ValueError(f'nsum requires non-negative n, got {n}. Use zsmul for groups.')
    if n == 0:
        return monoid.zero

    add_fn = monoid.add
    res = monoid.zero
    base = a
    while n > 0:
        if n % 2 == 1:
            res = add_fn(res, base)
        base = add_fn(base, base)
        n //= 2
    return res


def zsmul(group: AddGroup[V], a: V, n: int) -> V:
    r"""Compute the integer scalar multiple $z \cdot a$ for any $z \in \mathbb{Z}$ in an AddGroup.

    Args:
        group: AddGroup instance.
        a: Base element.
        n: Integer multiple ($n \in \mathbb{Z}$).

    Returns:
        $n \cdot a \in V$, where $(-k) \cdot a = k \cdot (-a)$.
    """
    if n >= 0:
        return nsum(group, a, n)
    neg_a = group.neg(a)
    return nsum(group, neg_a, -n)


def fold_mul(monoid: Monoid[V], items: Iterable[V]) -> V:
    """Fold an iterable of elements via monoid multiplication starting from monoid.one."""
    res = monoid.one
    mul_fn = monoid.mul
    for item in items:
        res = mul_fn(res, item)
    return res


def fold_add(monoid: AddMonoid[V], items: Iterable[V]) -> V:
    """Fold an iterable of elements via monoid addition starting from monoid.zero."""
    res = monoid.zero
    add_fn = monoid.add
    for item in items:
        res = add_fn(res, item)
    return res


def fold_op(monoid: OpMonoid[V], items: Iterable[V]) -> V:
    """Fold an iterable of elements via domain-agnostic op starting from monoid.identity."""
    res = monoid.identity
    op_fn = monoid.op
    for item in items:
        res = op_fn(res, item)
    return res
