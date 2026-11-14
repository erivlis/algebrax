r"""
Universal Conway Matrix Closure (EP-0198).

Implements recursive block Kleene star ($A^*$) and strict transitive closure ($A^+$)
for matrices over any StarSemiring / ClosedSemiring using Conway's $2 \times 2$ block
matrix decomposition.
"""

from collections.abc import Iterable, Sequence
from typing import Any

from algebrax.algebra import Semiring, StarSemiring
from algebrax.matrix.core import add, dot
from algebrax.typing import K, SparseMatrix, V

__all__ = [
    'matrix_plus',
    'matrix_star',
    'plus',
    'star',
]


def _partition_2x2_blocks(
    matrix: SparseMatrix[K, V],
    set1: set[K],
    set2: set[K],
) -> tuple[dict[K, dict[K, V]], dict[K, dict[K, V]], dict[K, dict[K, V]], dict[K, dict[K, V]]]:
    """Partition a sparse matrix into 2x2 block submatrices induced by key sets."""
    a11: dict[K, dict[K, V]] = {}
    a12: dict[K, dict[K, V]] = {}
    a21: dict[K, dict[K, V]] = {}
    a22: dict[K, dict[K, V]] = {}

    for r, row in matrix.items():
        if r in set1:
            t11, t12 = a11, a12
        elif r in set2:
            t11, t12 = a21, a22
        else:
            continue
        r_left = {c: v for c, v in row.items() if c in set1}
        r_right = {c: v for c, v in row.items() if c in set2}
        if r_left:
            t11[r] = r_left
        if r_right:
            t12[r] = r_right

    return a11, a12, a21, a22


def _merge_2x2_blocks(
    r11: SparseMatrix[K, V],
    r12: SparseMatrix[K, V],
    r21: SparseMatrix[K, V],
    r22: SparseMatrix[K, V],
    k1: Sequence[K],
    k2: Sequence[K],
) -> SparseMatrix[K, V]:
    """Reassemble four sparse submatrix blocks into a single sparse matrix."""
    res: dict[K, dict[K, V]] = {}
    for keys, left, right in ((k1, r11, r12), (k2, r21, r22)):
        for r in keys:
            row_res: dict[K, V] = {}
            if r in left:
                row_res.update(left[r])
            if r in right:
                row_res.update(right[r])
            if row_res:
                res[r] = row_res
    return res


def _conway_star(
    matrix: SparseMatrix[K, V],
    sr: StarSemiring[V],
    k_list: Sequence[K],
) -> SparseMatrix[K, V]:
    r"""Internal recursive Conway 2x2 block star closure."""
    n = len(k_list)
    if n == 0:
        return {}
    if n == 1:
        k = k_list[0]
        val = matrix.get(k, {}).get(k, sr.zero)
        s = sr.star(val)
        is_zero_fn = getattr(sr, 'is_zero', None)
        if (is_zero_fn is not None and is_zero_fn(s)) or (is_zero_fn is None and s == sr.zero):
            return {}
        return {k: {k: s}}

    m = n // 2
    k1 = k_list[:m]
    k2 = k_list[m:]
    a11, a12, a21, a22 = _partition_2x2_blocks(matrix, set(k1), set(k2))

    # Conway 2x2 Block Identities:
    # 1. A22*
    a22_star = _conway_star(a22, sr, k2)

    # 2. T = A12 · A22*
    t = dot(a12, a22_star, semiring=sr)

    # 3. Schur product S = T · A21 = A12 · A22* · A21
    s = dot(t, a21, semiring=sr)

    # 4. E = (A11 + S)*
    a11_plus_s = add(a11, s, semiring=sr)
    e = _conway_star(a11_plus_s, sr, k1)

    # 5. R11 = E
    r11 = e

    # 6. R12 = E · T = E · A12 · A22*
    r12 = dot(e, t, semiring=sr)

    # 7. U = A22* · A21
    u = dot(a22_star, a21, semiring=sr)

    # 8. R21 = U · E = A22* · A21 · E
    r21 = dot(u, e, semiring=sr)

    # 9. R22 = A22* + R21 · T
    r21_t = dot(r21, t, semiring=sr)
    r22 = add(a22_star, r21_t, semiring=sr)

    return _merge_2x2_blocks(r11, r12, r21, r22, k1, k2)


def matrix_star(
    matrix: SparseMatrix[K, V],
    semiring: StarSemiring[V] | type[StarSemiring[V]] | str | None = None,
    nodes: Iterable[K] | None = None,
) -> SparseMatrix[K, V]:
    r"""Compute the Kleene star closure $A^*$ of a square matrix $A$ over a StarSemiring.

    Uses Conway's recursive block decomposition:
        For $A = \begin{pmatrix} A_{11} & A_{12} \\ A_{21} & A_{22} \end{pmatrix}$:
            $E = (A_{11} + A_{12} A_{22}^* A_{21})^*$
            $A^*_{11} = E$
            $A^*_{12} = E \cdot A_{12} \cdot A_{22}^*$
            $A^*_{21} = A_{22}^* \cdot A_{21} \cdot E$
            $A^*_{22} = A_{22}^* + A_{22}^* \cdot A_{21} \cdot E \cdot A_{12} \cdot A_{22}^*$

    Base Case ($1 \times 1$):
        $[a]^* = [a^*]$

    Args:
        matrix: The input square sparse matrix.
        semiring: The star semiring structure (instance, class, or catalog key).
        nodes: Optional explicit sequence of node keys. If None, inferred from matrix.

    Returns:
        The closed matrix $A^*$.
    """
    sr = Semiring.normalize(semiring)  # type: ignore[arg-type]
    if not hasattr(sr, 'star'):
        raise TypeError(f"Semiring '{type(sr).__name__}' does not implement HasStar / StarSemiring")

    if nodes is not None:
        k_list = list(nodes)
    else:
        all_keys: set[K] = set(matrix.keys())
        for row in matrix.values():
            all_keys.update(row.keys())
        try:
            k_list = sorted(all_keys)
        except TypeError:
            k_list = sorted(all_keys, key=lambda x: (type(x).__name__, str(x)))

    return _conway_star(matrix, sr, k_list)  # type: ignore[arg-type]


def matrix_plus(
    matrix: SparseMatrix[K, V],
    semiring: StarSemiring[V] | type[StarSemiring[V]] | str | None = None,
    nodes: Iterable[K] | None = None,
) -> SparseMatrix[K, V]:
    r"""Compute the strict transitive closure $A^+ = A \cdot A^*$ of a square matrix.

    Unlike $A^*$, $A^+$ represents paths of length $\ge 1$, which does not introduce
    spurious self-loops on nodes that lack directed cycles.

    Args:
        matrix: The input square sparse matrix.
        semiring: The star semiring structure (instance, class, or catalog key).
        nodes: Optional explicit sequence of node keys. If None, inferred from matrix.

    Returns:
        The strict transitive closure $A^+$.
    """
    sr = Semiring.normalize(semiring)  # type: ignore[arg-type]
    a_star = matrix_star(matrix, sr, nodes=nodes)
    return dot(matrix, a_star, semiring=sr)


# Canonical aliases
star = matrix_star
plus = matrix_plus
