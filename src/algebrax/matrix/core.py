from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence

from algebrax.semiring import Semiring, StandardSemiring
from algebrax.typing import K, N, SparseMatrix, SparseVector, V

__all__ = [
    'add',
    'block',
    'block_diag',
    'dot',
    'hstack',
    'inner',
    'kronecker_delta',
    'mat_vec',
    'power',
    'slice_matrix',
    'trace',
    'transpose',
    'vec_mat',
    'vstack',
]


def add(m1: SparseMatrix[K, N], m2: SparseMatrix[K, N]) -> SparseMatrix[K, N]:
    """
    Perform element-wise addition of two sparse matrices (nested mappings).

    Args:
        m1: The first matrix.
        m2: The second matrix.

    Returns:
        A new nested dictionary representing the sum.
    """
    keys = set(m1.keys()) | set(m2.keys())
    result = {}
    for r in keys:
        row1 = m1.get(r, {})
        row2 = m2.get(r, {})
        col_keys = set(row1.keys()) | set(row2.keys())
        new_row = {}
        for c in col_keys:
            val = row1.get(c, 0) + row2.get(c, 0)
            if val != 0:
                new_row[c] = val
        if new_row:
            result[r] = new_row
    return result


def block(
    matrix: SparseMatrix[int, V],
    rows: slice | range,
    cols: slice | range,
) -> SparseMatrix[int, V]:
    """
    Extract a sub-matrix (block) from a sparse matrix.
    Indices are re-based to 0 in the result.

    Args:
        matrix: The input sparse matrix (must have integer keys).
        rows: The range of rows to extract.
        cols: The range of columns to extract.

    Returns:
        A new sparse matrix containing the block.
    """
    result = {}

    r_start = rows.start if rows.start is not None else 0
    r_stop = rows.stop
    r_step = rows.step if rows.step is not None else 1

    c_start = cols.start if cols.start is not None else 0
    c_stop = cols.stop
    c_step = cols.step if cols.step is not None else 1

    for r, row in matrix.items():
        if r < r_start:
            continue
        if r_stop is not None and r >= r_stop:
            continue
        if (r - r_start) % r_step != 0:
            continue

        new_r = (r - r_start) // r_step
        new_row = {}

        for c, val in row.items():
            if c < c_start:
                continue
            if c_stop is not None and c >= c_stop:
                continue
            if (c - c_start) % c_step != 0:
                continue

            new_c = (c - c_start) // c_step
            new_row[new_c] = val

        if new_row:
            result[new_r] = new_row

    return result


def block_diag(matrices: Sequence[SparseMatrix[int, V]]) -> SparseMatrix[int, V]:
    """
    Construct a block diagonal matrix from a sequence of matrices.

    Args:
        matrices: A sequence of sparse matrices.

    Returns:
        A new sparse matrix with the inputs on the diagonal.
    """
    result = {}
    r_offset = 0
    c_offset = 0

    for m in matrices:
        if not m:
            continue

        max_r = max(m.keys())
        max_c = 0
        for row in m.values():
            if row:
                max_c = max(max_c, max(row.keys()))

        for r, row in m.items():
            new_row = {}
            for c, val in row.items():
                new_row[c + c_offset] = val
            result[r + r_offset] = new_row

        r_offset += max_r + 1
        c_offset += max_c + 1

    return result


def dot(
    m1: SparseMatrix[K, V],
    m2: SparseMatrix[K, V],
    semiring: Semiring[V] | None = None,
) -> SparseMatrix[K, V]:
    """
    Perform matrix multiplication (dot product) of two sparse matrices.
    Supports generalized Semirings (e.g., Tropical, Boolean).

    Args:
        m1: The first matrix (left operand).
        m2: The second matrix (right operand).
        semiring: The algebraic structure to use. Defaults to StandardSemiring (+, *).

    Returns:
        A new nested dictionary representing the product.
    """
    if semiring is None:
        semiring = StandardSemiring()

    zero = semiring.zero

    result = {}
    for r, row1 in m1.items():
        new_row = defaultdict(lambda: zero)
        for k, val1 in row1.items():
            if k in m2:
                for c, val2 in m2[k].items():
                    # result[r][c] += val1 * val2
                    # Generalized: result[r][c] = result[r][c] + (val1 * val2)
                    term = semiring.mul(val1, val2)
                    current = new_row[c]
                    new_row[c] = semiring.add(current, term)

        # Remove zeros to maintain sparsity
        cleaned_row = {c: v for c, v in new_row.items() if v != zero}
        if cleaned_row:
            result[r] = cleaned_row
    return result


def hstack(matrices: Sequence[SparseMatrix[int, V]]) -> SparseMatrix[int, V]:
    """
    Stack sparse matrices horizontally (column-wise).

    Args:
        matrices: A sequence of sparse matrices.

    Returns:
        A new sparse matrix.
    """
    result = defaultdict(dict)
    c_offset = 0

    for m in matrices:
        if not m:
            continue

        current_max_c = 0
        for r, row in m.items():
            for c, val in row.items():
                result[r][c + c_offset] = val
                current_max_c = max(current_max_c, c)

        c_offset += current_max_c + 1

    return dict(result)


def inner(
    v1: SparseVector[K, V],
    v2: SparseVector[K, V],
    semiring: Semiring[V] | None = None,
) -> V:
    """
    Compute the inner product (dot product) of two vectors.

    Args:
        v1: The first vector.
        v2: The second vector.
        semiring: The algebraic structure to use. Defaults to StandardSemiring.

    Returns:
        The scalar dot product.
    """
    if semiring is None:
        semiring = StandardSemiring()

    common = set(v1.keys()) & set(v2.keys())

    # Standard inner product is sum(v1[k] * v2[k])
    # Generalized: reduce(add, map(mul, ...))

    result = semiring.zero
    for k in common:
        term = semiring.mul(v1[k], v2[k])
        result = semiring.add(result, term)

    return result


def kronecker_delta(i: K, j: K) -> int:
    """
    Compute the Kronecker delta.
    δ_ij = 1 if i == j, else 0.

    Args:
        i: First index.
        j: Second index.

    Returns:
        1 if i == j, else 0.
    """
    return 1 if i == j else 0


def mat_vec(
    matrix: SparseMatrix[K, V],
    vector: SparseVector[K, V],
    semiring: Semiring[V] | None = None,
) -> SparseVector[K, V]:
    """
    Multiply a matrix by a vector (M * v).

    Args:
        matrix: The matrix.
        vector: The vector.
        semiring: The algebraic structure to use. Defaults to StandardSemiring.

    Returns:
        The resulting vector.
    """
    if semiring is None:
        semiring = StandardSemiring()

    zero = semiring.zero
    result = {}

    for r, row in matrix.items():
        # row * vector (inner product)
        val = inner(row, vector, semiring)
        if val != zero:
            result[r] = val
    return result


def power(
    matrix: SparseMatrix[K, V],
    n: int,
    semiring: Semiring[V] | None = None,
) -> SparseMatrix[K, V]:
    """
    Compute the n-th power of a square matrix using binary exponentiation.

    Args:
        matrix: The input matrix.
        n: The exponent (must be non-negative).
        semiring: The algebraic structure to use. Defaults to StandardSemiring.

    Returns:
        The result of matrix ** n.
    """
    if n < 0:
        raise ValueError('Exponent must be non-negative.')

    if semiring is None:
        semiring = StandardSemiring()

    # Identity matrix construction
    keys = set(matrix.keys()) | {k for row in matrix.values() for k in row}
    one = semiring.one
    result = {k: {k: one} for k in keys}

    base = matrix
    while n > 0:
        if n % 2 == 1:
            result = dot(result, base, semiring)
        base = dot(base, base, semiring)
        n //= 2
    return result


def slice_matrix(
    matrix: SparseMatrix[K, V],
    rows: Iterable[K],
    cols: Iterable[K],
) -> SparseMatrix[K, V]:
    """
    Extract a sub-matrix using explicit row and column keys.
    Does NOT re-base indices (preserves original keys).

    Args:
        matrix: The input sparse matrix.
        rows: Iterable of row keys to keep.
        cols: Iterable of column keys to keep.

    Returns:
        A new sparse matrix containing only the intersection.
    """
    row_set = set(rows)
    col_set = set(cols)
    result = {}

    for r in row_set:
        if r in matrix:
            new_row = {c: v for c, v in matrix[r].items() if c in col_set}
            if new_row:
                result[r] = new_row

    return result


def trace(matrix: SparseMatrix[K, N]) -> N:
    """
    Calculate the trace of a matrix (sum of diagonal elements).

    Args:
        matrix: The input matrix.

    Returns:
        The sum of diagonal elements.
    """
    return sum(row.get(r, 0) for r, row in matrix.items())


def transpose(matrix: Mapping[K, Mapping[K, V]]) -> dict[K, dict[K, V]]:
    """
    Transpose a sparse matrix (swap rows and columns).

    Args:
        matrix: The input matrix (nested mapping).

    Returns:
        A new nested dictionary with rows and columns swapped.
    """
    result = defaultdict(dict)
    for r, row in matrix.items():
        for c, val in row.items():
            result[c][r] = val

    # Convert defaultdicts to regular dicts
    return {k: dict(v) for k, v in result.items()}


def vec_mat(
    vector: SparseVector[K, V],
    matrix: SparseMatrix[K, V],
    semiring: Semiring[V] | None = None,
) -> SparseVector[K, V]:
    """
    Multiply a vector by a matrix (v * M).

    Args:
        vector: The vector.
        matrix: The matrix.
        semiring: The algebraic structure to use. Defaults to StandardSemiring.

    Returns:
        The resulting vector.
    """
    if semiring is None:
        semiring = StandardSemiring()

    zero = semiring.zero
    result = defaultdict(lambda: zero)

    for k, val in vector.items():
        if k in matrix:
            for c, m_val in matrix[k].items():
                # result[c] += val * m_val
                term = semiring.mul(val, m_val)
                result[c] = semiring.add(result[c], term)

    return {k: v for k, v in result.items() if v != zero}


def vstack(matrices: Sequence[SparseMatrix[int, V]]) -> SparseMatrix[int, V]:
    """
    Stack sparse matrices vertically (row-wise).

    Args:
        matrices: A sequence of sparse matrices.

    Returns:
        A new sparse matrix.
    """
    result = {}
    r_offset = 0

    for m in matrices:
        if not m:
            continue

        max_r = max(m.keys())

        for r, row in m.items():
            result[r + r_offset] = dict(row)

        r_offset += max_r + 1

    return result
