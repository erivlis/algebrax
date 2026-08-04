"""
A collection of functions for working with dense and sparse representations of vectors,
matrices, tensors, and related utilities.

This module provides methods to convert between dense and sparse formats for vectors,
matrices, and tensors, as well as sampling utility functions for constructing sparse
representations.

Exported Functions:
- dense_to_sparse_vector: Converts a dense vector to a sparse representation.
- sparse_to_dense_vector: Converts a sparse vector to a dense representation.
- dense_to_sparse_matrix: Converts a dense matrix to a sparse representation.
- sparse_to_dense_matrix: Converts a sparse matrix to a dense representation.
- dense_to_sparse_tensor: Converts a dense tensor to a sparse representation.
- sparse_to_dense_tensor: Converts a sparse tensor to a dense representation.
- sample: Samples values from a function over a finite domain to create a sparse vector.
- sample_tensor: Samples values from a multidimensional function over a grid to create a sparse tensor.
"""

import itertools
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from algebrax.typing import (
    DenseMatrix,
    DenseVector,
    K,
    N,
    SparseMatrix,
    SparseVector,
    V,
)

__all__ = [
    'dense_to_sparse_matrix',
    'dense_to_sparse_tensor',
    'dense_to_sparse_vector',
    'flat_to_nested',
    'from_numpy',
    'from_scipy',
    'get_matrix_keys',
    'grid_to_sparse',
    'nested_to_flat',
    'prune_sparse',
    'sample',
    'sample_tensor',
    'sparse_to_dense_matrix',
    'sparse_to_dense_tensor',
    'sparse_to_dense_vector',
    'sparse_to_grid',
    'to_numpy',
    'to_scipy',
]


# region Vector


def dense_to_sparse_vector(
    vector: Sequence[V],
    default: V = 0,
) -> SparseVector[int, V]:
    """
    Convert a dense vector (sequence) to a sparse vector (mapping).

    Args:
        vector: The dense vector (e.g., list or tuple).
        default: The value to treat as "empty" (not stored).

    Returns:
        A dictionary mapping indices to non-default values.
    """
    return {i: v for i, v in enumerate(vector) if v != default}


def sparse_to_dense_vector(
    vector: SparseVector[int, V],
    size: int | None = None,
    default: V = 0,
) -> DenseVector[V]:
    """
    Convert a sparse vector (mapping) to a dense vector (list).

    Args:
        vector: The sparse vector.
        size: The size of the resulting list. If None, inferred from max key.
        default: The value to fill for missing keys.

    Returns:
        A list of values.
    """
    if not vector:
        return [default] * (size or 0)

    if size is None:
        size = max(vector.keys()) + 1

    result = [default] * size
    for k, v in vector.items():
        if 0 <= k < size:
            result[k] = v
    return result


# endregion


# region Matrix


def dense_to_sparse_matrix(
    matrix: Sequence[Sequence[V]],
    default: V = 0,
) -> SparseMatrix[int, V]:
    """
    Convert a dense matrix (sequence of sequences) to a sparse matrix (mapping of mappings).

    Args:
        matrix: The dense matrix.
        default: The value to treat as "empty".

    Returns:
        A nested dictionary mapping row indices to column indices to values.
    """
    result = {}
    for r, row in enumerate(matrix):
        sparse_row = {c: v for c, v in enumerate(row) if v != default}
        if sparse_row:
            result[r] = sparse_row
    return result


def sparse_to_dense_matrix(
    matrix: SparseMatrix[int, V],
    shape: tuple[int, int] | None = None,
    default: V = 0,
) -> DenseMatrix[V]:
    """
    Convert a sparse matrix (mapping of mappings) to a dense matrix (list of lists).

    Args:
        matrix: The sparse matrix.
        shape: A tuple (rows, cols). If None, inferred from max keys.
        default: The value to fill for missing entries.

    Returns:
        A list of lists representing the matrix.
    """
    if not matrix:
        if shape:
            return [[default] * shape[1] for _ in range(shape[0])]
        return []

    if shape is None:
        max_row = max(matrix.keys())
        max_col = 0
        for row in matrix.values():
            if row:
                max_col = max(max_col, max(row.keys()))
        shape = (max_row + 1, max_col + 1)

    rows = list(range(shape[0]))
    cols = list(range(shape[1]))
    return sparse_to_grid(matrix, rows, cols, fill_value=default)


def get_matrix_keys(matrix: SparseMatrix) -> tuple[list[Any], list[Any]]:
    """
    Extract sorted row keys and column keys from a sparse matrix.

    Args:
        matrix: A sparse matrix dict[i, dict[j, val]].

    Returns:
        A tuple (sorted_rows, sorted_cols).
    """
    rows = sorted(matrix.keys(), key=str)
    cols_set: set[Any] = set()
    for r in rows:
        cols_set.update(matrix[r].keys())
    cols = sorted(cols_set, key=str)
    return rows, cols


def sparse_to_grid(
    matrix: SparseMatrix,
    rows: list[Any],
    cols: list[Any],
    fill_value: Any = 0.0,
) -> list[list[Any]]:
    """
    Convert a sparse matrix mapping to a 2D dense float list for fast indexing.

    Args:
        matrix: Sparse matrix mapping.
        rows: Ordered list of row keys.
        cols: Ordered list of column keys.
        fill_value: Value for missing entries (default: 0.0).

    Returns:
        A 2D list grid[row_idx][col_idx].
    """
    return [
        [matrix.get(r, {}).get(c, fill_value) for c in cols]
        for r in rows
    ]


def grid_to_sparse(
    grid: list[list[Any]],
    rows: list[Any],
    cols: list[Any],
    tol: float = 1e-12,
) -> SparseMatrix:
    """
    Convert a 2D dense list back to a pruned sparse matrix mapping.

    Args:
        grid: A 2D list grid[row_idx][col_idx].
        rows: Ordered list of row keys.
        cols: Ordered list of column keys.
        tol: Absolute tolerance below which values are pruned as zero.

    Returns:
        A sparse matrix dict[row, dict[col, val]].
    """
    res: dict[Any, dict[Any, Any]] = {}
    for i, r in enumerate(rows):
        row_dict: dict[Any, Any] = {}
        for j, c in enumerate(cols):
            val = grid[i][j]
            if isinstance(val, (int, float)):
                if abs(val) > tol:
                    row_dict[c] = val
            elif val != 0:
                row_dict[c] = val
        if row_dict:
            res[r] = row_dict
    return res


def prune_sparse(matrix: SparseMatrix, tol: float = 1e-12) -> SparseMatrix:
    """
    Prune zero or near-zero values from a sparse matrix dictionary.

    Args:
        matrix: A sparse matrix mapping.
        tol: Absolute tolerance threshold.

    Returns:
        A new sparse matrix with near-zero entries removed.
    """
    res = {}
    for r, row in matrix.items():
        clean_row = {}
        for c, v in row.items():
            if isinstance(v, (int, float)):
                if abs(v) > tol:
                    clean_row[c] = v
            elif v != 0:
                clean_row[c] = v
        if clean_row:
            res[r] = clean_row
    return res


# endregion


# region Tensor


def dense_to_sparse_tensor(
    tensor: Sequence[Any],
    default: V = 0,
) -> Any:
    """
    Convert a dense tensor (nested sequence) to a sparse tensor (nested mapping).
    Recursively processes the structure.

    Args:
        tensor: The dense tensor.
        default: The value to treat as "empty".

    Returns:
        A nested dictionary representing the sparse tensor, or the value itself if scalar.
    """
    # Base case: not a sequence (scalar) or string (treated as scalar here)
    if not isinstance(tensor, Sequence) or isinstance(tensor, (str, bytes)):
        return tensor

    # Recursive case
    result = {}
    for i, item in enumerate(tensor):
        # If item is a scalar equal to default, skip
        if not isinstance(item, Sequence) and item == default:
            continue

        # If item is a sequence, recurse
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            sparse_item = dense_to_sparse_tensor(item, default)
            if sparse_item:  # Only add if sub-structure is not empty
                result[i] = sparse_item
        elif item != default:
            result[i] = item

    return result


def _get_shape(t: Any, current_depth: int = 0) -> list[int]:
    """Helper to find max shape of a sparse tensor."""
    if not isinstance(t, Mapping):
        return []
    if not t:
        return [0]

    max_idx = max(t.keys())
    dim = max_idx + 1

    # Recurse to find sub-shapes
    sub_shapes = []
    for v in t.values():
        sub_shapes.append(_get_shape(v, current_depth + 1))

    # Merge sub-shapes (take max of each dimension)
    # This assumes all sub-tensors have the same rank.
    # Note: sub_shapes is never empty here because t is not empty.

    max_rank = max(len(s) for s in sub_shapes)
    merged_sub = [0] * max_rank
    for s in sub_shapes:
        for i, val in enumerate(s):
            merged_sub[i] = max(merged_sub[i], val)

    return [dim, *merged_sub]


def sparse_to_dense_tensor(
    tensor: Mapping[int, Any],
    shape: tuple[int, ...] | None = None,
    default: V = 0,
) -> Any:
    """
    Convert a sparse tensor (nested mapping) to a dense tensor (nested list).

    Args:
        tensor: The sparse tensor.
        shape: A tuple representing the dimensions (d1, d2, ...).
               If None, inferred from the keys (assumes rectangular).
        default: The value to fill for missing entries.

    Returns:
        A nested list representing the tensor.
    """
    # Base case: tensor is not a mapping (scalar)
    if not isinstance(tensor, Mapping):
        return tensor

    if shape is None:
        shape = tuple(_get_shape(tensor))

    # Build dense structure
    dim = shape[0]
    sub_shape = shape[1:]

    if not sub_shape:
        # 1D case (Vector)
        result = [default] * dim
        for k, v in tensor.items():
            if 0 <= k < dim:
                result[k] = v
        return result

    # Recursive case
    result = []
    for i in range(dim):
        sub_tensor = tensor.get(i, {})
        # If sub_tensor is missing (empty), we pass empty dict to recurse
        # which will produce a zero-filled dense sub-structure.
        dense_sub = sparse_to_dense_tensor(sub_tensor, shape=sub_shape, default=default)
        result.append(dense_sub)

    return result


# endregion


# region Sampling


def sample(
    func: Callable[[K], V],
    domain: Iterable[K],
    default: V = 0,
) -> SparseVector[K, V]:
    """
    Sample a function over a finite domain to create a sparse vector (mapping).

    Args:
        func: The function to sample (K -> V).
        domain: The set of keys to evaluate.
        default: The value to treat as "empty" (not stored).

    Returns:
        A dictionary {k: func(k)} where func(k) != default.
    """
    result = {}
    for k in domain:
        val = func(k)
        if val != default:
            result[k] = val
    return result


def sample_tensor(
    func: Callable[[tuple[Any, ...]], V],
    ranges: Sequence[Iterable[Any]],
    default: V = 0,
) -> Mapping[Any, Any]:
    """
    Sample a multidimensional function over a grid to create a sparse tensor (nested mapping).

    To sample over the domain of an existing sparse tensor (resampling), use:
    `flat_to_nested(sample(func, nested_to_flat(tensor).keys()))`

    Args:
        func: The function to sample. Takes a tuple of coordinates.
        ranges: A sequence of iterables, one for each dimension.
        default: The value to treat as "empty".

    Returns:
        A nested dictionary representing the sparse tensor.
    """
    # Generate domain as Cartesian product
    domain = itertools.product(*ranges)

    # Sample to flat mapping
    flat = sample(func, domain, default)

    # Convert to nested mapping
    return flat_to_nested(flat)


# endregion


# region Flattening


def flat_to_nested(
    mapping: Mapping[tuple, V],
) -> Mapping[Any, Any]:
    """
    Convert a flat mapping with tuple keys to a nested mapping.
    {(a, b): v} -> {a: {b: v}}

    Args:
        mapping: The flat mapping.

    Returns:
        A nested dictionary.
    """
    result = {}
    for keys, value in mapping.items():
        if not isinstance(keys, tuple):
            # Handle scalar keys (depth 1)
            result[keys] = value
            continue

        current = result
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                raise ValueError(
                    f"Key collision: cannot nest dict under existing non-dict leaf at {keys[: i + 1]}"
                )
            current = current[key]

        if keys[-1] in current and isinstance(current[keys[-1]], dict):
            raise ValueError(
                f"Key collision: cannot assign non-dict value to dict node at {keys}"
            )
        current[keys[-1]] = value

    return result


def nested_to_flat(
    nested: Mapping[Any, Any],
) -> Mapping[tuple, V]:
    """
    Convert a nested mapping to a flat mapping with tuple keys.
    {a: {b: v}} -> {(a, b): v}

    Args:
        nested: The nested mapping.

    Returns:
        A flat dictionary.
    """
    result = {}
    path = []

    def _recurse(current):
        if isinstance(current, Mapping):
            for k, v in current.items():
                path.append(k)
                _recurse(v)
                path.pop()
        else:
            result[tuple(path)] = current

    _recurse(nested)
    return result


def to_numpy(
    matrix: SparseMatrix[K, V],
    shape: tuple[int, int] | None = None,
) -> Any:
    """
    Convert a sparse dict matrix to a 2D NumPy ndarray.

    Requires `numpy` to be installed.

    Args:
        matrix: Sparse dictionary matrix with integer indices.
        shape: Optional (rows, cols) dimensions tuple.

    Returns:
        A 2D numpy.ndarray.

    Raises:
        ImportError: If numpy is not installed.
    """
    try:
        import numpy as np
    except ImportError as err:
        raise ImportError('to_numpy() requires numpy. Install with: pip install numpy') from err

    if not matrix:
        h, w = shape if shape else (0, 0)
        return np.zeros((h, w))

    r_max = max(matrix.keys()) if isinstance(max(matrix.keys()), int) else len(matrix)
    c_max = max(c for row in matrix.values() for c in row) if any(row for row in matrix.values()) else 0
    h, w = shape if shape else (r_max + 1, c_max + 1)

    arr = np.zeros((h, w))
    for r, row in matrix.items():
        for c, val in row.items():
            if isinstance(r, int) and isinstance(c, int) and r < h and c < w:
                arr[r, c] = val

    return arr


def from_numpy(arr: Any) -> SparseMatrix[int, Any]:
    """
    Convert a 2D NumPy ndarray to a sparse dict matrix (zero entries pruned).

    Requires `numpy` to be installed.

    Args:
        arr: 2D numpy.ndarray.

    Returns:
        Sparse dictionary matrix {r: {c: val}}.

    Raises:
        ImportError: If numpy is not installed.
    """
    try:
        import numpy as np
    except ImportError as err:
        raise ImportError('from_numpy() requires numpy. Install with: pip install numpy') from err

    if not isinstance(arr, np.ndarray) or arr.ndim != 2:
        raise ValueError('from_numpy requires a 2D numpy.ndarray')

    mat: dict[int, dict[int, Any]] = {}
    h, w = arr.shape
    for r in range(h):
        row = {}
        for c in range(w):
            val = arr[r, c]
            if val != 0:
                row[c] = val.item() if hasattr(val, 'item') else val
        if row:
            mat[r] = row

    return mat


def to_scipy(
    matrix: SparseMatrix[K, V],
    format: str = 'csr',
) -> Any:
    """
    Convert a sparse dict matrix to a SciPy sparse matrix (csr, csc, coo, etc.).

    Requires `scipy` to be installed.

    Args:
        matrix: Sparse dictionary matrix with integer indices.
        format: SciPy matrix format string ('csr', 'csc', 'coo', 'dok', 'lil').

    Returns:
        A scipy.sparse matrix instance.

    Raises:
        ImportError: If scipy is not installed.
    """
    try:
        import scipy.sparse as sp
    except ImportError as err:
        raise ImportError('to_scipy() requires scipy. Install with: pip install scipy') from err

    rows, cols, data = [], [], []
    for r, row in matrix.items():
        for c, val in row.items():
            rows.append(r)
            cols.append(c)
            data.append(val)

    if not rows:
        return sp.csr_matrix((0, 0))

    r_max = max(rows) + 1
    c_max = max(cols) + 1
    coo = sp.coo_matrix((data, (rows, cols)), shape=(r_max, c_max))
    return coo.asformat(format)


def from_scipy(sp_matrix: Any) -> SparseMatrix[int, Any]:
    """
    Convert a SciPy sparse matrix to a sparse dict matrix (zero entries pruned).

    Requires `scipy` to be installed.

    Args:
        sp_matrix: scipy.sparse matrix instance.

    Returns:
        Sparse dictionary matrix {r: {c: val}}.

    Raises:
        ImportError: If scipy is not installed.
    """
    try:
        import scipy.sparse as sp
    except ImportError as err:
        raise ImportError('from_scipy() requires scipy. Install with: pip install scipy') from err

    coo = sp_matrix.tocoo()
    mat: dict[int, dict[int, Any]] = {}
    for r, c, val in zip(coo.row, coo.col, coo.data, strict=False):
        if val != 0:
            val_py = val.item() if hasattr(val, 'item') else val
            r_int, c_int = int(r), int(c)
            if r_int not in mat:
                mat[r_int] = {}
            mat[r_int][c_int] = val_py

    return mat


# endregion
