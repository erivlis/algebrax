r"""
Canonical Finite Group Constructors: Cyclic, Dihedral, Quaternion, Symmetric, Alternating & Products.

Provides `FiniteGroup` constructors and pure group laws decoupled from matrix representations:
- Cyclic groups $C_n$
- Dihedral groups $D_{2n}$
- Quaternion group $Q_8$
- Symmetric groups $S_n$ and Alternating groups $A_n$
- Direct product groups $G \times H$
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Hashable
from typing import TypeVar

from algebrax.group.finite import FiniteCommGroup, FiniteGroup
from algebrax.group.permutation import signature

G1 = TypeVar('G1', bound=Hashable)
G2 = TypeVar('G2', bound=Hashable)


def cyclic_group(n: int) -> FiniteCommGroup[int]:
    r"""Construct the cyclic group $C_n = \langle \{0, \dots, n-1\}, 0, + \bmod n \rangle$."""
    if n < 1:
        raise ValueError(f'Cyclic group order n must be >= 1, got {n}.')
    return FiniteCommGroup(
        elements=tuple(range(n)),
        identity=0,
        mul_fn=lambda a, b, m=n: (a + b) % m,
        inv_fn=lambda a, m=n: (-a) % m,
        name=f'C_{n}',
        verify_commutative=False,
    )


def dihedral_elements(n: int) -> list[str]:
    """Return canonical element labels `['r0', ..., 'r{n-1}', 's0', ..., 's{n-1}']` for $D_{2n}$."""
    if n < 1:
        raise ValueError(f'Dihedral index n must be >= 1, got {n}.')
    return [f'r{i}' for i in range(n)] + [f's{i}' for i in range(n)]


def dihedral_mul(n: int) -> Callable[[str, str], str]:
    r"""Return the multiplication law of $D_{2n}$ on elements `'r{a}'`, `'s{a}'` where $s_a = r_a s_0$."""
    if n < 1:
        raise ValueError(f'Dihedral index n must be >= 1, got {n}.')

    def _mul(a: str, b: str) -> str:
        ta, ia = a[0], int(a[1:]) % n
        tb, ib = b[0], int(b[1:]) % n
        if ta == 'r' and tb == 'r':
            return f'r{(ia + ib) % n}'
        if ta == 'r' and tb == 's':
            return f's{(ia + ib) % n}'
        if ta == 's' and tb == 'r':
            return f's{(ia - ib) % n}'
        return f'r{(ia - ib) % n}'

    return _mul


def dihedral_inv(n: int) -> Callable[[str], str]:
    r"""Return the inversion law of $D_{2n}$: $(r_a)^{-1} = r_{-a}$, $(s_a)^{-1} = s_a$."""
    if n < 1:
        raise ValueError(f'Dihedral index n must be >= 1, got {n}.')

    def _inv(a: str) -> str:
        ta, ia = a[0], int(a[1:]) % n
        if ta == 'r':
            return f'r{(-ia) % n}'
        return f's{ia}'

    return _inv


def dihedral_group(n: int) -> FiniteGroup[str]:
    r"""Construct the dihedral group $D_{2n}$ of order $2n$ (`FiniteCommGroup` for $n \le 2$)."""
    elems = tuple(dihedral_elements(n))
    mul_fn = dihedral_mul(n)
    inv_fn = dihedral_inv(n)
    if n <= 2:
        return FiniteCommGroup(
            elements=elems,
            identity='r0',
            mul_fn=mul_fn,
            inv_fn=inv_fn,
            name=f'D_{2 * n}',
            verify_commutative=False,
        )
    return FiniteGroup(
        elements=elems,
        identity='r0',
        mul_fn=mul_fn,
        inv_fn=inv_fn,
        name=f'D_{2 * n}',
    )


_Q8_BASE: dict[tuple[str, str], str] = {
    ('i', 'i'): '-1',
    ('i', 'j'): 'k',
    ('i', 'k'): '-j',
    ('j', 'i'): '-k',
    ('j', 'j'): '-1',
    ('j', 'k'): 'i',
    ('k', 'i'): 'j',
    ('k', 'j'): '-i',
    ('k', 'k'): '-1',
}


def quaternion_elements() -> list[str]:
    """Return canonical elements `['1', '-1', 'i', '-i', 'j', '-j', 'k', '-k']` of $Q_8$."""
    return ['1', '-1', 'i', '-i', 'j', '-j', 'k', '-k']


def quaternion_mul(a: str, b: str) -> str:
    """Multiply two elements in the quaternion group $Q_8$."""
    sa = -1 if a.startswith('-') else 1
    sb = -1 if b.startswith('-') else 1
    ua = a[1:] if a.startswith('-') else a
    ub = b[1:] if b.startswith('-') else b
    if ua == '1':
        unit = ub
        sign = sa * sb
    elif ub == '1':
        unit = ua
        sign = sa * sb
    else:
        base = _Q8_BASE[(ua, ub)]
        sign = sa * sb * (-1 if base.startswith('-') else 1)
        unit = base[1:] if base.startswith('-') else base
    return f'-{unit}' if sign < 0 else unit


def quaternion_inv(a: str) -> str:
    """Invert an element in $Q_8$: $1^{-1}=1, (-1)^{-1}=-1, q^{-1}=-q$ for $q \\in \\{\\pm i, \\pm j, \\pm k\\}$."""
    if a in ('1', '-1'):
        return a
    return a[1:] if a.startswith('-') else f'-{a}'


def quaternion_group() -> FiniteGroup[str]:
    """Construct the quaternion group $Q_8$ of order 8 as a `FiniteGroup`."""
    return FiniteGroup(
        elements=tuple(quaternion_elements()),
        identity='1',
        mul_fn=quaternion_mul,
        inv_fn=quaternion_inv,
        name='Q_8',
    )


def _perm_sign(p: tuple[int, ...]) -> int:
    return signature(dict(enumerate(p)))


def symmetric_elements(n: int) -> list[tuple[int, ...]]:
    r"""Generate all $n!$ permutations of $\{0, \dots, n-1\}$ as tuples."""
    if n < 1:
        raise ValueError(f'Symmetric group degree n must be >= 1, got {n}.')
    return list(itertools.permutations(range(n)))


def alternating_elements(n: int) -> list[tuple[int, ...]]:
    """Generate all even permutations in $A_n$ as tuples."""
    return [p for p in symmetric_elements(n) if _perm_sign(p) == 1]


def symmetric_mul(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    r"""Compose two tuple permutations $(p \circ q)(i) = p[q[i]]$."""
    return tuple(p[q[i]] for i in range(len(p)))


def symmetric_inv(p: tuple[int, ...]) -> tuple[int, ...]:
    """Invert a tuple permutation."""
    inv = [0] * len(p)
    for i, v in enumerate(p):
        inv[v] = i
    return tuple(inv)


def symmetric_group(n: int) -> FiniteGroup[tuple[int, ...]]:
    """Construct the symmetric group $S_n$ of order $n!$ (`FiniteCommGroup` for $n \\le 2$)."""
    elems = tuple(symmetric_elements(n))
    if n <= 2:
        return FiniteCommGroup(
            elements=elems,
            identity=tuple(range(n)),
            mul_fn=symmetric_mul,
            inv_fn=symmetric_inv,
            name=f'S_{n}',
            verify_commutative=False,
        )
    return FiniteGroup(
        elements=elems,
        identity=tuple(range(n)),
        mul_fn=symmetric_mul,
        inv_fn=symmetric_inv,
        name=f'S_{n}',
    )


def alternating_group(n: int) -> FiniteGroup[tuple[int, ...]]:
    """Construct the alternating group $A_n$ of order $n!/2$ ($n \\ge 2$) or $1$ ($n=1$)."""
    elems = tuple(alternating_elements(n))
    if n <= 3:
        return FiniteCommGroup(
            elements=elems,
            identity=tuple(range(n)),
            mul_fn=symmetric_mul,
            inv_fn=symmetric_inv,
            name=f'A_{n}',
            verify_commutative=False,
        )
    return FiniteGroup(
        elements=elems,
        identity=tuple(range(n)),
        mul_fn=symmetric_mul,
        inv_fn=symmetric_inv,
        name=f'A_{n}',
    )


def direct_product(
    g1: FiniteGroup[G1],
    g2: FiniteGroup[G2],
    name: str = '',
) -> FiniteGroup[tuple[G1, G2]]:
    r"""Construct the direct product group $G_1 \times G_2$ (`FiniteCommGroup` when both factors are abelian)."""
    elems = tuple((a, b) for a in g1.elements for b in g2.elements)
    label = name or (f'{g1.name} x {g2.name}' if g1.name and g2.name else '')
    if g1.is_abelian() and g2.is_abelian():
        return FiniteCommGroup(
            elements=elems,
            identity=(g1.identity, g2.identity),
            mul_fn=lambda x, y: (g1.mul(x[0], y[0]), g2.mul(x[1], y[1])),
            inv_fn=lambda x: (g1.inv(x[0]), g2.inv(x[1])),
            name=label,
            verify_commutative=False,
        )
    return FiniteGroup(
        elements=elems,
        identity=(g1.identity, g2.identity),
        mul_fn=lambda x, y: (g1.mul(x[0], y[0]), g2.mul(x[1], y[1])),
        inv_fn=lambda x: (g1.inv(x[0]), g2.inv(x[1])),
        name=label,
    )


__all__ = [
    'alternating_elements',
    'alternating_group',
    'cyclic_group',
    'dihedral_elements',
    'dihedral_group',
    'dihedral_inv',
    'dihedral_mul',
    'direct_product',
    'quaternion_elements',
    'quaternion_group',
    'quaternion_inv',
    'quaternion_mul',
    'symmetric_elements',
    'symmetric_group',
    'symmetric_inv',
    'symmetric_mul',
]
