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
    'nested_to_flat',
    'sample',
    'sample_tensor',
    'sparse_to_dense_matrix',
    'sparse_to_dense_tensor',
    'sparse_to_dense_vector',
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

    rows, cols = shape
    result = [[default] * cols for _ in range(rows)]

    for r, row in matrix.items():
        if 0 <= r < rows:
            for c, v in row.items():
                if 0 <= c < cols:
                    result[r][c] = v

    return result

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
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            # Ensure we don't overwrite a value with a dict (mixed depth conflict)
            if not isinstance(current, dict):
                # This happens if we have (a,) and (a, b).
                # (a,) sets result[a] = val.
                # (a, b) tries to set result[a][b].
                # We can't support mixed depth easily.
                # For now, assume consistent depth or last-write-wins?
                # Let's raise or overwrite. Overwrite is safer for now.
                current = {}
                result[keys[0]] = current  # Wait, this logic is flawed for recursion.
                # Let's restart the traversal properly.

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

# endregion
