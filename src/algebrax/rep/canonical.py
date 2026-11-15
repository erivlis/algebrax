r"""
Canonical Finite-Group Representations and Orthonormal Character Tables.

Provides exact sparse matrix representations and verified character tables for:
- Trivial and Left-Regular representations of arbitrary finite groups
- Cyclic groups $C_n$
- Dihedral groups $D_{2n}$
- Quaternion group $Q_8$ (via Pauli spin matrices)
- Symmetric groups $S_n$ and Alternating groups $A_n$
"""

from __future__ import annotations

import cmath
import math
from collections.abc import Hashable, Mapping, Sequence
from typing import TypeVar

from algebrax.group.canonical import (
    alternating_elements,
    dihedral_elements,
    dihedral_mul,
    quaternion_elements,
    quaternion_mul,
    symmetric_elements,
    symmetric_inv,
    symmetric_mul,
)
from algebrax.group.finite import FiniteGroup
from algebrax.group.permutation import signature
from algebrax.rep.character import CharacterTable
from algebrax.rep.group import ExplicitGroupRep, _prune_matrix
from algebrax.typing import SparseMatrix

G = TypeVar('G', bound=Hashable)


def trivial_rep(elements: Sequence[G] | FiniteGroup[G]) -> ExplicitGroupRep[float, G]:
    r"""Construct the trivial 1D representation $\rho(g) = [1.0]$ for all $g \in G$."""
    elem_list = list(elements.elements) if isinstance(elements, FiniteGroup) else list(elements)
    if not elem_list:
        raise ValueError('trivial_rep requires at least one group element.')
    unit: SparseMatrix[int, float] = {0: {0: 1.0}}
    return ExplicitGroupRep(matrices=dict.fromkeys(elem_list, unit), dimension=1)


def regular_rep(group_table: Mapping[tuple[G, G], G] | FiniteGroup[G]) -> ExplicitGroupRep[float, G]:
    r"""Construct the left regular representation $\rho_{\mathrm{reg}}(g) e_h = e_{gh}$ of dimension $|G|$.

    Args:
        group_table: `FiniteGroup` or complete multiplication table mapping `(g, h) -> g * h`.

    Returns:
        Permutation-matrix `ExplicitGroupRep` of dimension $|G|$.
    """
    if isinstance(group_table, FiniteGroup):
        mats = {g: group_table.regular_action_matrix(g) for g in group_table.elements}
        return ExplicitGroupRep(matrices=mats, dimension=group_table.order)

    if not group_table:
        raise ValueError('regular_rep requires a non-empty multiplication table.')

    elements: list[G] = list(dict.fromkeys(g for pair in group_table for g in pair))
    order = len(elements)
    index_of = {el: idx for idx, el in enumerate(elements)}

    mats = {}
    for g in elements:
        mat: dict[int, dict[int, float]] = {}
        for h in elements:
            if (g, h) not in group_table:
                raise ValueError(f'Incomplete group_table: missing product ({g!r}, {h!r}).')
            prod = group_table[(g, h)]
            r_idx = index_of[prod]
            c_idx = index_of[h]
            mat.setdefault(r_idx, {})[c_idx] = 1.0
        mats[g] = mat

    return ExplicitGroupRep(matrices=mats, dimension=order)


def cyclic_rep(n: int, k: int = 1) -> ExplicitGroupRep[complex, int]:
    r"""Construct the 1D irreducible representation of $C_n = \{0, \dots, n-1\}$ at frequency $k$.

    Algebraic Signature:
        $\rho_k(g) = \left[ e^{2\pi i k g / n} \right] \in \mathrm{GL}_1(\mathbb{C})$
    """
    if n < 1:
        raise ValueError(f'Cyclic group order n must be >= 1, got {n}.')
    mats: dict[int, SparseMatrix[int, complex]] = {}
    for g in range(n):
        val = cmath.exp(2j * math.pi * k * g / n)
        if abs(val.imag) <= 1e-14:
            mats[g] = {0: {0: complex(val.real, 0.0)}}
        else:
            mats[g] = {0: {0: val}}
    return ExplicitGroupRep(matrices=mats, dimension=1)


def dihedral_rep(n: int, k: int = 1) -> ExplicitGroupRep[float, str]:
    r"""Construct the 2D geometric rotation-reflection representation of $D_{2n}$.

    Maps rotations `'r{a}'` to $R(2\pi k a / n)$ and reflections `'s{a}'` to $R(2\pi k a / n)\,\mathrm{diag}(1, -1)$.
    """
    if n < 1:
        raise ValueError(f'Dihedral index n must be >= 1, got {n}.')

    mats: dict[str, SparseMatrix[int, float]] = {}
    for a in range(n):
        theta = 2.0 * math.pi * k * a / n
        c = math.cos(theta)
        s = math.sin(theta)
        rot = _prune_matrix({0: {0: c, 1: -s}, 1: {0: s, 1: c}})
        refl = _prune_matrix({0: {0: c, 1: s}, 1: {0: s, 1: -c}})
        mats[f'r{a}'] = rot
        mats[f's{a}'] = refl
    return ExplicitGroupRep(matrices=mats, dimension=2)


def quaternion_rep() -> ExplicitGroupRep[complex, str]:
    r"""Construct the faithful 2D irreducible complex representation of $Q_8$ via Pauli matrices.

    Maps generators $(i, j, k) \mapsto (-i\sigma_1, -i\sigma_2, -i\sigma_3) \in \mathrm{SU}(2)$.
    """
    mats: dict[str, SparseMatrix[int, complex]] = {
        '1': {0: {0: 1.0 + 0.0j}, 1: {1: 1.0 + 0.0j}},
        '-1': {0: {0: -1.0 + 0.0j}, 1: {1: -1.0 + 0.0j}},
        'i': {0: {1: -1.0j}, 1: {0: -1.0j}},
        '-i': {0: {1: 1.0j}, 1: {0: 1.0j}},
        'j': {0: {1: -1.0 + 0.0j}, 1: {0: 1.0 + 0.0j}},
        '-j': {0: {1: 1.0 + 0.0j}, 1: {0: -1.0 + 0.0j}},
        'k': {0: {0: -1.0j}, 1: {1: 1.0j}},
        '-k': {0: {0: 1.0j}, 1: {1: -1.0j}},
    }
    return ExplicitGroupRep(matrices=mats, dimension=2)


def _perm_sign(p: tuple[int, ...]) -> int:
    return signature(dict(enumerate(p)))


def symmetric_defining_rep(n: int) -> ExplicitGroupRep[float, tuple[int, ...]]:
    """Construct the $n$-dimensional defining permutation representation of $S_n$."""
    mats: dict[tuple[int, ...], SparseMatrix[int, float]] = {}
    for p in symmetric_elements(n):
        mats[p] = {p[i]: {i: 1.0} for i in range(n)}
    return ExplicitGroupRep(matrices=mats, dimension=n)


def symmetric_sign_rep(n: int) -> ExplicitGroupRep[float, tuple[int, ...]]:
    r"""Construct the 1D sign (alternating) representation $\rho(p) = [\operatorname{sgn}(p)]$ of $S_n$."""
    mats: dict[tuple[int, ...], SparseMatrix[int, float]] = {
        p: {0: {0: float(_perm_sign(p))}} for p in symmetric_elements(n)
    }
    return ExplicitGroupRep(matrices=mats, dimension=1)


def symmetric_standard_rep(n: int) -> ExplicitGroupRep[float, tuple[int, ...]]:
    r"""Construct the $(n-1)$-dimensional irreducible standard representation of $S_n$ ($n \ge 2$).

    Acts on the invariant hyperplane $\{x \in \mathbb{R}^n : \sum_i x_i = 0\}$ using the
    exact integral basis $v_j = e_j - e_{n-1}$ ($0 \le j < n - 1$).
    """
    if n < 2:
        raise ValueError(f'Standard representation requires n >= 2, got {n}.')
    dim = n - 1
    mats: dict[tuple[int, ...], SparseMatrix[int, float]] = {}
    for p in symmetric_elements(n):
        mat: dict[int, dict[int, float]] = {}
        pn = p[dim]
        for j in range(dim):
            pj = p[j]
            # p(v_j) = e_{p(j)} - e_{p(n-1)} = v_{p(j)} - v_{p(n-1)}, where v_{n-1} = 0
            if pj < dim and pn < dim and pj == pn:
                continue
            if pj < dim:
                mat.setdefault(pj, {})[j] = mat.get(pj, {}).get(j, 0.0) + 1.0
            if pn < dim:
                mat.setdefault(pn, {})[j] = mat.get(pn, {}).get(j, 0.0) - 1.0
        mats[p] = _prune_matrix(mat)
    return ExplicitGroupRep(matrices=mats, dimension=dim)


def alternating_defining_rep(n: int) -> ExplicitGroupRep[float, tuple[int, ...]]:
    """Construct the $n$-dimensional defining permutation representation restricted to $A_n$."""
    even = set(alternating_elements(n))
    full = symmetric_defining_rep(n)
    return ExplicitGroupRep(matrices={p: full(p) for p in even}, dimension=n)


def alternating_standard_rep(n: int) -> ExplicitGroupRep[float, tuple[int, ...]]:
    r"""Construct the $(n-1)$-dimensional standard representation restricted to $A_n$ ($n \ge 2$)."""
    even = set(alternating_elements(n))
    std = symmetric_standard_rep(n)
    return ExplicitGroupRep(matrices={p: std(p) for p in even}, dimension=std.dimension)


def cyclic_character_table(n: int) -> CharacterTable:
    """Compile the exact $n \times n$ Fourier character table of the cyclic group $C_n$."""
    if n < 1:
        raise ValueError(f'Cyclic group order n must be >= 1, got {n}.')
    classes = [f'g^{j}' for j in range(n)]
    sizes = [1] * n
    irreps = [f'chi_{k}' for k in range(n)]
    table = [[cmath.exp(2j * math.pi * k * j / n) for j in range(n)] for k in range(n)]
    return CharacterTable(classes=classes, class_sizes=sizes, irreps=irreps, table=table, group_order=n)


def dihedral_character_table(n: int) -> CharacterTable:
    r"""Compile the orthonormal character table of the dihedral group $D_{2n}$ ($n \ge 1$)."""
    if n < 1:
        raise ValueError(f'Dihedral index n must be >= 1, got {n}.')
    if n == 1:
        return CharacterTable(
            classes=['r0', 's0'],
            class_sizes=[1, 1],
            irreps=['A1', 'A2'],
            table=[[1.0 + 0j, 1.0 + 0j], [1.0 + 0j, -1.0 + 0j]],
            group_order=2,
        )

    order = 2 * n
    if n % 2 == 1:
        m = (n - 1) // 2
        classes = ['e'] + [f'r^{j}' for j in range(1, m + 1)] + ['s']
        class_sizes = [1] + [2] * m + [n]
        irreps = ['A1', 'A2'] + [f'E_{k}' for k in range(1, m + 1)]
        table: list[list[complex]] = [
            [1.0 + 0j] * len(classes),
            [1.0 + 0j] * (1 + m) + [-1.0 + 0j],
        ]
        for k in range(1, m + 1):
            row = [complex(2.0, 0.0)] + [
                complex(2.0 * math.cos(2.0 * math.pi * k * j / n), 0.0) for j in range(1, m + 1)
            ] + [0.0 + 0j]
            table.append(row)
        return CharacterTable(classes=classes, class_sizes=class_sizes, irreps=irreps, table=table, group_order=order)

    m = n // 2
    classes = ['e'] + [f'r^{j}' for j in range(1, m)] + [f'r^{m}', 's_even', 's_odd']
    class_sizes = [1] + [2] * (m - 1) + [1, m, m]
    irreps = ['A1', 'A2', 'B1', 'B2'] + [f'E_{k}' for k in range(1, m)]
    rot_count = m + 1
    table = [
        [1.0 + 0j] * len(classes),
        [1.0 + 0j] * rot_count + [-1.0 + 0j, -1.0 + 0j],
        [complex((-1) ** j, 0) for j in range(rot_count)] + [1.0 + 0j, -1.0 + 0j],
        [complex((-1) ** j, 0) for j in range(rot_count)] + [-1.0 + 0j, 1.0 + 0j],
    ]
    for k in range(1, m):
        row = [complex(2.0 * math.cos(2.0 * math.pi * k * j / n), 0.0) for j in range(rot_count)] + [0.0 + 0j, 0.0 + 0j]
        table.append(row)
    return CharacterTable(classes=classes, class_sizes=class_sizes, irreps=irreps, table=table, group_order=order)


def s3_character_table() -> CharacterTable:
    """Compile the orthonormal character table of the symmetric group $S_3$ (order 6)."""
    return CharacterTable(
        classes=['1^3', '2^1 1^1', '3^1'],
        class_sizes=[1, 3, 2],
        irreps=['Trivial (A1)', 'Sign (A2)', 'Standard (E)'],
        table=[
            [1.0 + 0j, 1.0 + 0j, 1.0 + 0j],
            [1.0 + 0j, -1.0 + 0j, 1.0 + 0j],
            [2.0 + 0j, 0.0 + 0j, -1.0 + 0j],
        ],
        group_order=6,
    )


def s4_character_table() -> CharacterTable:
    """Compile the orthonormal character table of the symmetric group $S_4$ (order 24)."""
    return CharacterTable(
        classes=['1^4', '2 1^2', '2^2', '3 1', '4'],
        class_sizes=[1, 6, 3, 8, 6],
        irreps=['Trivial (A1)', 'Sign (A2)', 'E', 'Standard (T2)', 'T1'],
        table=[
            [1.0 + 0j, 1.0 + 0j, 1.0 + 0j, 1.0 + 0j, 1.0 + 0j],
            [1.0 + 0j, -1.0 + 0j, 1.0 + 0j, 1.0 + 0j, -1.0 + 0j],
            [2.0 + 0j, 0.0 + 0j, 2.0 + 0j, -1.0 + 0j, 0.0 + 0j],
            [3.0 + 0j, 1.0 + 0j, -1.0 + 0j, 0.0 + 0j, -1.0 + 0j],
            [3.0 + 0j, -1.0 + 0j, -1.0 + 0j, 0.0 + 0j, 1.0 + 0j],
        ],
        group_order=24,
    )


def a4_character_table() -> CharacterTable:
    """Compile the orthonormal complex character table of the alternating group $A_4$ (order 12)."""
    omega = cmath.exp(2j * math.pi / 3.0)
    omega2 = omega.conjugate()
    return CharacterTable(
        classes=['e', '(12)(34)', '(123)', '(132)'],
        class_sizes=[1, 3, 4, 4],
        irreps=['1', 'omega', 'omega^2', 'T'],
        table=[
            [1.0 + 0j, 1.0 + 0j, 1.0 + 0j, 1.0 + 0j],
            [1.0 + 0j, 1.0 + 0j, omega, omega2],
            [1.0 + 0j, 1.0 + 0j, omega2, omega],
            [3.0 + 0j, -1.0 + 0j, 0.0 + 0j, 0.0 + 0j],
        ],
        group_order=12,
    )


def q8_character_table() -> CharacterTable:
    """Compile the orthonormal character table of the quaternion group $Q_8$ (order 8)."""
    return CharacterTable(
        classes=['{1}', '{-1}', '{+-i}', '{+-j}', '{+-k}'],
        class_sizes=[1, 1, 2, 2, 2],
        irreps=['A1', 'A2', 'B1', 'B2', 'E'],
        table=[
            [1.0 + 0j, 1.0 + 0j, 1.0 + 0j, 1.0 + 0j, 1.0 + 0j],
            [1.0 + 0j, 1.0 + 0j, 1.0 + 0j, -1.0 + 0j, -1.0 + 0j],
            [1.0 + 0j, 1.0 + 0j, -1.0 + 0j, 1.0 + 0j, -1.0 + 0j],
            [1.0 + 0j, 1.0 + 0j, -1.0 + 0j, -1.0 + 0j, 1.0 + 0j],
            [2.0 + 0j, -2.0 + 0j, 0.0 + 0j, 0.0 + 0j, 0.0 + 0j],
        ],
        group_order=8,
    )


__all__ = [
    'a4_character_table',
    'alternating_defining_rep',
    'alternating_elements',
    'alternating_standard_rep',
    'cyclic_character_table',
    'cyclic_rep',
    'dihedral_character_table',
    'dihedral_elements',
    'dihedral_mul',
    'dihedral_rep',
    'q8_character_table',
    'quaternion_elements',
    'quaternion_mul',
    'quaternion_rep',
    'regular_rep',
    's3_character_table',
    's4_character_table',
    'symmetric_defining_rep',
    'symmetric_elements',
    'symmetric_inv',
    'symmetric_mul',
    'symmetric_sign_rep',
    'symmetric_standard_rep',
    'trivial_rep',
]
