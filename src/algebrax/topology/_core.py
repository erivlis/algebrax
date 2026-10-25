"""Shared low-level kernels for simplicial canonicalization, orientation parity, and sparse rank."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from algebrax.typing import K, SparseMatrix


def _count_inversions_and_sort(s: tuple[K, ...], oriented: bool) -> tuple[tuple[K, ...], int]:
    n = len(s)
    try:
        inversions = 0
        if oriented:
            for i in range(n):
                s_i = s[i]
                for j in range(i + 1, n):
                    if s_i > s[j]:  # type: ignore[operator]
                        inversions += 1
        return tuple(sorted(s)), (-1 if (inversions % 2 == 1) else 1)  # type: ignore[type-var]
    except TypeError:
        keyed = [((str(type(x)), str(x)), x) for x in s]
        inversions = 0
        if oriented:
            for i in range(n):
                k_i = keyed[i][0]
                for j in range(i + 1, n):
                    if k_i > keyed[j][0]:
                        inversions += 1
        keyed.sort(key=lambda item: item[0])
        return tuple(item[1] for item in keyed), (-1 if (inversions % 2 == 1) else 1)


def _canonicalize_simplex(
    simplex: Iterable[K],
    oriented: bool = True,
) -> tuple[tuple[K, ...], int]:
    """Return `(canonical_sorted_simplex, parity_sign)` where `parity_sign` is 0 if degenerate."""
    s = tuple(simplex)
    n = len(s)
    if n <= 1:
        return s, 1
    if len(set(s)) < n:
        return s, 0
    return _count_inversions_and_sort(s, oriented)


def _is_non_zero(val: Any, tol: float) -> bool:
    if isinstance(val, (int, float, complex)) and not isinstance(val, bool):
        return (abs(val) > tol) if tol > 0.0 else (val != 0)
    return bool(val)


def _matrix_rank(matrix: SparseMatrix) -> int:
    """Compute the rank of a sparse dictionary matrix over real numbers using Gaussian elimination."""
    if not matrix:
        return 0

    rows: list[dict[object, float]] = [dict(row) for row in matrix.values() if row]
    if not rows:
        return 0

    rank = 0
    pivots: set[object] = set()

    while rows:
        rows.sort(key=lambda r: len(r))
        row = rows.pop(0)

        pivot_col = None
        for col in row:
            if col not in pivots and abs(row[col]) > 1e-9:
                pivot_col = col
                break

        if pivot_col is None:
            continue

        rank += 1
        pivots.add(pivot_col)
        pivot_val = row[pivot_col]

        for other in rows:
            if pivot_col in other:
                factor = other[pivot_col] / pivot_val
                for col, val in row.items():
                    new_val = other.get(col, 0.0) - factor * val
                    if abs(new_val) < 1e-9:
                        other.pop(col, None)
                    else:
                        other[col] = new_val

    return rank
