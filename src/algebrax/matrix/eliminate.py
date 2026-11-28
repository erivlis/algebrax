r"""
Field-Polymorphic Sparse Linear Elimination Kernel (RREF, Rank, Nullspace).

Provides exact and numerically pivoted sparse Gaussian elimination over any `Field[V]`
(including `float`, `complex`, `Fraction`, `ModularField`, and `GaloisField`) operating
directly on rectangular sparse matrices `RectSparseMatrix[R, C, V]` with arbitrary hashable keys.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from algebrax.algebra._field import Field, StandardField
from algebrax.converters import canonical_sort_keys
from algebrax.typing import C, R, RectSparseMatrix, SparseVector, V

__all__ = [
    'nullspace',
    'rank',
    'sparse_rref',
]


def _is_float_regime(field: Field[Any] | None) -> bool:
    """Return True when elimination should use floating-point partial pivoting."""
    if field is None:
        return True
    return isinstance(field, StandardField) and field._dtype in (float, complex)


def _prepare_float_rows(
    matrix: RectSparseMatrix[R, C, Any],
    row_keys: list[R],
    col_map: dict[C, int],
    field: Field[Any] | None,
    tol: float,
) -> tuple[list[dict[int, Any]], dict[int, set[int]]]:
    """Map sparse matrix entries to dense integer column indices with tolerance pruning."""
    rows_data: list[dict[int, Any]] = []
    col_to_rows: dict[int, set[int]] = {}
    one = field.one if field is not None else None

    for rk in row_keys:
        raw_row = matrix[rk]
        if not raw_row:
            continue
        cur: dict[int, Any] = {}
        for ck, val in raw_row.items():
            v = field.mul(one, val) if field is not None else val
            if abs(v) > tol:
                c_idx = col_map[ck]
                cur[c_idx] = v
        if cur:
            r_idx = len(rows_data)
            rows_data.append(cur)
            for c_idx in cur:
                col_to_rows.setdefault(c_idx, set()).add(r_idx)

    return rows_data, col_to_rows


def _prepare_exact_rows(
    matrix: RectSparseMatrix[R, C, V],
    row_keys: list[R],
    col_map: dict[C, int],
    field: Field[V],
) -> tuple[list[dict[int, V]], dict[int, set[int]]]:
    """Map sparse matrix entries to dense integer column indices over an exact field."""
    rows_data: list[dict[int, V]] = []
    col_to_rows: dict[int, set[int]] = {}
    f_one = field.one
    f_mul = field.mul
    is_zero = field.is_zero

    for rk in row_keys:
        raw_row = matrix[rk]
        if not raw_row:
            continue
        cur: dict[int, V] = {}
        for ck, val in raw_row.items():
            v = f_mul(f_one, val)
            if not is_zero(v):
                c_idx = col_map[ck]
                cur[c_idx] = v
        if cur:
            r_idx = len(rows_data)
            rows_data.append(cur)
            for c_idx in cur:
                col_to_rows.setdefault(c_idx, set()).add(r_idx)

    return rows_data, col_to_rows


def _rank_float(
    rows_data: list[dict[int, Any]],
    col_to_rows: dict[int, set[int]],
    n_cols: int,
    zero: Any,
    tol: float,
) -> int:
    """Compute rank via forward-only sparse partial pivoting (no back-substitution fill-in)."""
    rank_count = 0
    for c in range(n_cols):
        candidates = col_to_rows.pop(c, None)
        if not candidates:
            continue

        piv_r = max(candidates, key=lambda r: abs(rows_data[r][c]))
        piv_row = rows_data[piv_r]
        piv_val = piv_row[c]
        if abs(piv_val) <= tol:
            for r in candidates:
                rows_data[r].pop(c, None)
            continue

        rank_count += 1
        # Pivot row will never be revisited in forward elimination
        for col_j in piv_row:
            if col_j != c and col_j in col_to_rows:
                col_to_rows[col_j].discard(piv_r)

        for r in candidates:
            if r == piv_r:
                continue
            row_r = rows_data[r]
            factor = row_r.pop(c) / piv_val
            if abs(factor) <= tol:
                continue
            for col_j, piv_j in piv_row.items():
                if col_j == c:
                    continue
                new_val = row_r.get(col_j, zero) - factor * piv_j
                if abs(new_val) <= tol:
                    if col_j in row_r:
                        del row_r[col_j]
                        if col_j in col_to_rows:
                            col_to_rows[col_j].discard(r)
                else:
                    if col_j not in row_r:
                        col_to_rows.setdefault(col_j, set()).add(r)
                    row_r[col_j] = new_val

    return rank_count


def _rank_exact(
    rows_data: list[dict[int, V]],
    col_to_rows: dict[int, set[int]],
    n_cols: int,
    field: Field[V],
) -> int:
    """Compute exact rank via forward-only sparse elimination over `Field[V]`."""
    f_zero = field.zero
    f_mul = field.mul
    f_sub = field.sub
    f_inv = field.inv
    is_zero = field.is_zero

    rank_count = 0
    for c in range(n_cols):
        candidates = col_to_rows.pop(c, None)
        if not candidates:
            continue

        # Select sparsest pivot row to minimize fill-in (deterministic tie-break by row index)
        piv_r = min(candidates, key=lambda r: (len(rows_data[r]), r))
        piv_row = rows_data[piv_r]
        inv_piv = f_inv(piv_row[c])

        rank_count += 1
        for col_j in piv_row:
            if col_j != c and col_j in col_to_rows:
                col_to_rows[col_j].discard(piv_r)

        for r in candidates:
            if r == piv_r:
                continue
            row_r = rows_data[r]
            factor = f_mul(row_r.pop(c), inv_piv)
            for col_j, piv_j in piv_row.items():
                if col_j == c:
                    continue
                new_val = f_sub(row_r.get(col_j, f_zero), f_mul(factor, piv_j))
                if is_zero(new_val):
                    if col_j in row_r:
                        del row_r[col_j]
                        if col_j in col_to_rows:
                            col_to_rows[col_j].discard(r)
                else:
                    if col_j not in row_r:
                        col_to_rows.setdefault(col_j, set()).add(r)
                    row_r[col_j] = new_val

    return rank_count


def _rref_float(
    rows_data: list[dict[int, Any]],
    col_to_rows: dict[int, set[int]],
    n_cols: int,
    zero: Any,
    one: Any,
    tol: float,
) -> tuple[list[dict[int, Any]], list[int]]:
    """Compute sparse RREF via partial pivoting for float/complex matrices."""
    used_rows: set[int] = set()
    pivot_order: list[int] = []
    pivot_cols: list[int] = []

    for c in range(n_cols):
        col_rows = col_to_rows.get(c)
        if not col_rows:
            continue
        candidates = [r for r in col_rows if r not in used_rows]
        if not candidates:
            continue

        piv_r = max(candidates, key=lambda r: abs(rows_data[r][c]))
        piv_val = rows_data[piv_r][c]
        if abs(piv_val) <= tol:
            for r in candidates:
                rows_data[r].pop(c, None)
                col_rows.discard(r)
            continue

        used_rows.add(piv_r)
        pivot_order.append(piv_r)
        pivot_cols.append(c)

        # Normalize pivot row
        piv_row = rows_data[piv_r]
        norm_row: dict[int, Any] = {c: one}
        for col_j, val_j in piv_row.items():
            if col_j == c:
                continue
            scaled = val_j / piv_val
            if abs(scaled) > tol:
                norm_row[col_j] = scaled
            elif col_j in col_to_rows:
                col_to_rows[col_j].discard(piv_r)
        rows_data[piv_r] = norm_row

        # Eliminate column c from all other rows (both above and below)
        for r in list(col_rows):
            if r == piv_r:
                continue
            row_r = rows_data[r]
            factor = row_r.pop(c)
            col_rows.discard(r)
            if abs(factor) <= tol:
                continue
            for col_j, piv_j in norm_row.items():
                if col_j == c:
                    continue
                new_val = row_r.get(col_j, zero) - factor * piv_j
                if abs(new_val) <= tol:
                    if col_j in row_r:
                        del row_r[col_j]
                        if col_j in col_to_rows:
                            col_to_rows[col_j].discard(r)
                else:
                    if col_j not in row_r:
                        col_to_rows.setdefault(col_j, set()).add(r)
                    row_r[col_j] = new_val

    return [rows_data[r] for r in pivot_order], pivot_cols


def _rref_exact(
    rows_data: list[dict[int, V]],
    col_to_rows: dict[int, set[int]],
    n_cols: int,
    field: Field[V],
) -> tuple[list[dict[int, V]], list[int]]:
    """Compute exact sparse RREF over `Field[V]`."""
    f_zero = field.zero
    f_one = field.one
    f_mul = field.mul
    f_sub = field.sub
    f_inv = field.inv
    is_zero = field.is_zero

    used_rows: set[int] = set()
    pivot_order: list[int] = []
    pivot_cols: list[int] = []

    for c in range(n_cols):
        col_rows = col_to_rows.get(c)
        if not col_rows:
            continue
        candidates = [r for r in col_rows if r not in used_rows]
        if not candidates:
            continue

        piv_r = min(candidates, key=lambda r: (len(rows_data[r]), r))
        piv_row = rows_data[piv_r]
        inv_piv = f_inv(piv_row[c])

        used_rows.add(piv_r)
        pivot_order.append(piv_r)
        pivot_cols.append(c)

        # Normalize pivot row
        norm_row: dict[int, V] = {c: f_one}
        for col_j, val_j in piv_row.items():
            if col_j == c:
                continue
            scaled = f_mul(inv_piv, val_j)
            if not is_zero(scaled):
                norm_row[col_j] = scaled
            elif col_j in col_to_rows:
                col_to_rows[col_j].discard(piv_r)
        rows_data[piv_r] = norm_row

        # Eliminate column c from all other rows (both above and below)
        for r in list(col_rows):
            if r == piv_r:
                continue
            row_r = rows_data[r]
            factor = row_r.pop(c)
            col_rows.discard(r)
            for col_j, piv_j in norm_row.items():
                if col_j == c:
                    continue
                new_val = f_sub(row_r.get(col_j, f_zero), f_mul(factor, piv_j))
                if is_zero(new_val):
                    if col_j in row_r:
                        del row_r[col_j]
                        if col_j in col_to_rows:
                            col_to_rows[col_j].discard(r)
                else:
                    if col_j not in row_r:
                        col_to_rows.setdefault(col_j, set()).add(r)
                    row_r[col_j] = new_val

    return [rows_data[r] for r in pivot_order], pivot_cols


def sparse_rref(
    matrix: RectSparseMatrix[R, C, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> tuple[RectSparseMatrix[int, C, V], list[C]]:
    r"""Compute sparse Reduced Row Echelon Form (RREF) and pivot columns over any `Field[V]`.

    Algebraic Signature:
        $\mathrm{RREF} : \mathbb{K}^{m \times n} \longrightarrow \mathbb{K}^{r \times n} \times \mathcal{P}(C)$

    Carrier:
        `tuple[RectSparseMatrix[int, C, V], list[C]]` mapping echelon row index `0..r-1` to
        normalized sparse rows keyed by original column labels `C`, paired with the canonical
        ordered list of pivot column keys.

    Operations:
        - Exact Sparse Elimination: When `field` is an exact `Field[V]` (e.g., `StandardField(Fraction)`,
          `ModularField(p)`, `GaloisField`), selects sparsest pivots with zero rounding error via
          `field.is_zero` and `field.inv`.
        - Sparse Partial Pivoting: When `field` is `None` or float/complex `StandardField`, selects
          the maximum-magnitude pivot (`abs(val) > tol`) in each active column for numerical stability.

    Properties:
        - Each pivot row $i$ has unit leading entry $R_{i, p_i} = \mathbf{1}$.
        - Every pivot column $p_i$ has zeros in all other rows ($R_{j, p_i} = \mathbf{0}$ for $j \ne i$).
        - The non-zero rows of $R$ form the unique canonical basis of $\mathrm{row}(A)$.

    Args:
        matrix: Rectangular sparse matrix `RectSparseMatrix[R, C, V]`.
        field: Optional `Field[V]` typeclass for exact arithmetic. Defaults to native float/complex
            partial pivoting when `None`.
        tol: Zero-detection threshold for floating-point/complex regimes (default `1e-12`).

    Returns:
        Tuple `(rref_matrix, pivot_cols)` where `rref_matrix` has integer row indices `0..rank-1`
        and `pivot_cols` lists the corresponding pivot column keys in canonical order.
    """
    if not matrix:
        return {}, []

    row_keys = canonical_sort_keys(matrix.keys())
    col_set: set[C] = set()
    for row in matrix.values():
        col_set.update(row.keys())
    if not col_set:
        return {}, []

    col_keys = canonical_sort_keys(col_set)
    col_map = {ck: i for i, ck in enumerate(col_keys)}
    n_cols = len(col_keys)

    if _is_float_regime(field):
        zero: Any = field.zero if field is not None else 0.0
        one: Any = field.one if field is not None else 1.0
        rows_data, col_to_rows = _prepare_float_rows(matrix, row_keys, col_map, field, tol)
        if not rows_data:
            return {}, []
        echelon_rows, pivot_idx = _rref_float(rows_data, col_to_rows, n_cols, zero, one, tol)
    else:
        assert field is not None
        rows_data_exact, col_to_rows = _prepare_exact_rows(matrix, row_keys, col_map, field)
        if not rows_data_exact:
            return {}, []
        echelon_rows, pivot_idx = _rref_exact(rows_data_exact, col_to_rows, n_cols, field)

    rref_out: dict[int, dict[C, V]] = {}
    for i, row_dict in enumerate(echelon_rows):
        rref_out[i] = {col_keys[c_idx]: val for c_idx, val in sorted(row_dict.items())}
    pivot_keys = [col_keys[c_idx] for c_idx in pivot_idx]
    return rref_out, pivot_keys


def rank(
    matrix: RectSparseMatrix[R, C, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> int:
    r"""Compute matrix rank via forward-only sparse `Field[V]`-polymorphic Gaussian elimination.

    Algebraic Signature:
        $\operatorname{rank}_{\mathbb{K}} : \mathbb{K}^{m \times n} \longrightarrow \mathbb{Z}_{\ge 0}$

    Carrier:
        `int` (Non-negative rank $\dim_{\mathbb{K}} \operatorname{im}(A)$).

    Operations:
        Executes forward sparse elimination only (skipping RREF back-substitution fill-in) using
        exact field arithmetic when an exact `Field[V]` is supplied and sparse partial pivoting
        for float/complex regimes.

    Properties:
        - Rank-Nullity Theorem: $\operatorname{rank}(A) + \dim \ker(A) = n$.
        - Exact Torsion Sensitivity: Computing $\operatorname{rank}_{\mathbb{F}_p}(\partial_k)$ detects
          $p$-torsion invisible over $\mathbb{Q}$ or $\mathbb{R}$.

    Args:
        matrix: Rectangular sparse matrix `RectSparseMatrix[R, C, V]`.
        field: Optional `Field[V]` typeclass for exact arithmetic. Defaults to native float/complex
            partial pivoting when `None`.
        tol: Zero-detection threshold for floating-point/complex regimes (default `1e-12`).

    Returns:
        Integer matrix rank over `field` (or $\mathbb{R}/\mathbb{C}$ when `field is None`).
    """
    if not matrix:
        return 0

    row_keys = canonical_sort_keys(matrix.keys())
    col_set: set[C] = set()
    for row in matrix.values():
        col_set.update(row.keys())
    if not col_set:
        return 0

    col_keys = canonical_sort_keys(col_set)
    col_map = {ck: i for i, ck in enumerate(col_keys)}
    n_cols = len(col_keys)

    if _is_float_regime(field):
        zero: Any = field.zero if field is not None else 0.0
        rows_data, col_to_rows = _prepare_float_rows(matrix, row_keys, col_map, field, tol)
        if not rows_data:
            return 0
        return _rank_float(rows_data, col_to_rows, n_cols, zero, tol)

    assert field is not None
    rows_data_exact, col_to_rows = _prepare_exact_rows(matrix, row_keys, col_map, field)
    if not rows_data_exact:
        return 0
    return _rank_exact(rows_data_exact, col_to_rows, n_cols, field)


def nullspace(
    matrix: RectSparseMatrix[R, C, V],
    *,
    cols: Iterable[C] | None = None,
    field: Field[V] | None = None,
    tol: float = 1e-12,
) -> list[SparseVector[C, V]]:
    r"""Compute a basis of the right nullspace $\ker(A) = \{x \mid A x = 0\}$ via sparse RREF.

    Algebraic Signature:
        $\ker_{\mathbb{K}} : \mathbb{K}^{m \times n} \longrightarrow \mathcal{B}(\ker A) \subset (\mathbb{K}^n)^d$

    Carrier:
        `list[SparseVector[C, V]]` (Linearly independent sparse basis vectors keyed by column labels `C`).

    Operations:
        Computes `(rref, pivot_cols) = sparse_rref(matrix, field=field, tol=tol)` and constructs one
        canonical sparse basis vector per free column (including omitted zero columns supplied via `cols`).

    Properties:
        - Kernel Soundness: $A v = \mathbf{0}$ for every returned basis vector $v$.
        - Rank-Nullity Identity:
          $\operatorname{rank}(A) + \operatorname{len}(\mathrm{nullspace}(A, \mathrm{cols})) = |C|$.

    Args:
        matrix: Rectangular sparse matrix `RectSparseMatrix[R, C, V]`.
        cols: Optional explicit iterable of domain column keys `C` so omitted all-zero columns
            contribute standard basis vectors to $\ker(A)$.
        field: Optional `Field[V]` typeclass for exact arithmetic. Defaults to native float/complex
            partial pivoting when `None`.
        tol: Zero-detection threshold for floating-point/complex regimes (default `1e-12`).

    Returns:
        List of sparse basis vectors spanning $\ker(A)$.
    """
    col_set: set[C] = set(cols) if cols is not None else set()
    for row in matrix.values():
        col_set.update(row.keys())
    if not col_set:
        return []

    col_keys = canonical_sort_keys(col_set)
    rref_mat, pivot_cols = sparse_rref(matrix, field=field, tol=tol)
    pivot_set = set(pivot_cols)
    free_cols = [ck for ck in col_keys if ck not in pivot_set]

    is_float = _is_float_regime(field)
    one: Any = field.one if field is not None else 1.0

    basis: list[SparseVector[C, V]] = []
    for free_c in free_cols:
        vec: dict[C, V] = {free_c: one}
        for row_i, piv_c in enumerate(pivot_cols):
            row_dict = rref_mat.get(row_i)
            if row_dict and free_c in row_dict:
                val = row_dict[free_c]
                neg_val = field.neg(val) if field is not None else (-val)  # type: ignore[operator]
                if is_float:
                    if abs(neg_val) > tol:  # type: ignore[arg-type]
                        vec[piv_c] = neg_val
                elif field is not None and not field.is_zero(neg_val):
                    vec[piv_c] = neg_val
        basis.append(vec)
    return basis
