import warnings
from collections import defaultdict

from algebrax.matrix.core import mat_vec, transpose
from algebrax.typing import K, N, SparseMatrix, SparseVector

__all__ = [
    'PerformanceWarning',
    'adjoint',
    'cofactor',
    'determinant',
    'eigen_centrality',
    'inverse',
]


class PerformanceWarning(UserWarning):
    """Warning for computationally expensive academic operations."""


def adjoint(matrix: SparseMatrix[K, N]) -> SparseMatrix[K, N]:
    """
    Compute the adjugate (classical adjoint) matrix.
    Defined as the transpose of the cofactor matrix.

    WARNING: This operation is computationally expensive (O(N^5)) and is intended
    for small matrices or academic demonstration only. For large numerical matrices,
    use a specialized library like NumPy.

    Args:
        matrix: The input square matrix.

    Returns:
        The adjugate matrix.
    """
    warnings.warn(
        'adjoint() is O(N^5) and intended for academic demonstration only.',
        PerformanceWarning,
        stacklevel=2,
    )
    # Suppress internal warnings to avoid duplicate alerts
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', PerformanceWarning)
        return transpose(cofactor(matrix))


def cofactor(matrix: SparseMatrix[K, N]) -> SparseMatrix[K, N]:
    """
    Compute the cofactor matrix.
    C[i, j] = (-1)^(i+j) * det(Minor(i, j))

    WARNING: This operation is computationally expensive (O(N^5)) and is intended
    for small matrices or academic demonstration only.

    Args:
        matrix: The input square matrix.

    Returns:
        The cofactor matrix.
    """
    warnings.warn(
        'cofactor() is O(N^5) and intended for academic demonstration only.',
        PerformanceWarning,
        stacklevel=2,
    )
    keys = sorted(set(matrix.keys()) | {k for row in matrix.values() for k in row}, key=str)
    n = len(keys)
    if n == 0:
        return {}
    if n == 1:
        return {keys[0]: {keys[0]: 1}}

    # Map keys to indices 0..n-1 for consistent ordering
    key_map = {k: i for i, k in enumerate(keys)}

    result = defaultdict(dict)

    for i, r_key in enumerate(keys):
        for j, c_key in enumerate(keys):
            # Compute minor for element (r_key, c_key)
            # Exclude row r_key and column c_key

            # We need to construct the minor such that determinant() sees it as a square matrix
            # of size N-1.
            # determinant() infers size from the union of keys.
            # If we just filter, we get keys K \ {r_key} and K \ {c_key}.
            # If r_key != c_key, these sets are different, so union size is N (or N-1 if overlap).
            # We must re-map the keys of the minor to 0..N-2.

            minor_mapped = defaultdict(dict)

            # Mapping for the minor:
            # Original index k -> New index k'
            # If k < excluded_index, k' = k
            # If k > excluded_index, k' = k - 1

            for r, row in matrix.items():
                if r == r_key:
                    continue

                r_idx = key_map[r]
                new_r_idx = r_idx if r_idx < i else r_idx - 1

                for c, val in row.items():
                    if c == c_key:
                        continue

                    c_idx = key_map[c]
                    new_c_idx = c_idx if c_idx < j else c_idx - 1

                    minor_mapped[new_r_idx][new_c_idx] = val

            # We suppress the warning for the inner determinant call to avoid spamming
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', PerformanceWarning)
                det = determinant(minor_mapped, n=n - 1)

            if det != 0:
                sign = 1 if (i + j) % 2 == 0 else -1
                result[r_key][c_key] = sign * det

    return {k: dict(v) for k, v in result.items()}


def determinant(matrix: SparseMatrix[K, N], n: int | None = None) -> N:
    """
    Compute the determinant of a square matrix using Gaussian elimination.

    WARNING: This operation has O(N^3) complexity and modifies a local copy of the matrix.
    It is not efficient for very large matrices. Use for small, sparse symbolic data only.

    Args:
        matrix: The input square matrix.
        n: The dimension of the matrix. If None, inferred from keys.
           If provided, assumes keys are integers 0..n-1.

    Returns:
        The determinant value.
    """
    warnings.warn(
        'determinant() is O(N^3) and intended for academic demonstration only.',
        PerformanceWarning,
        stacklevel=2,
    )

    if n is None:
        # Identify the universe of keys
        keys = sorted(set(matrix.keys()) | {k for row in matrix.values() for k in row}, key=str)
        n = len(keys)
        # Map keys to indices 0..n-1
        key_map = {k: i for i, k in enumerate(keys)}
    else:
        # Assume keys are 0..n-1
        key_map = {i: i for i in range(n)}

    # Create a local mutable copy (using dicts for sparsity, though fill-in will occur)
    # We use indices for the local calculation
    m = defaultdict(dict)
    for r, row in matrix.items():
        # Only process rows that map to valid indices (if n provided)
        if r in key_map:
            r_idx = key_map[r]
            for c, val in row.items():
                if c in key_map:
                    m[r_idx][key_map[c]] = val

    sign = 1
    for i in range(n):
        # Find pivot
        pivot = m[i].get(i, 0)

        # Swap rows if pivot is zero
        if pivot == 0:
            for j in range(i + 1, n):
                if m[j].get(i, 0) != 0:
                    m[i], m[j] = m[j], m[i]
                    sign *= -1
                    pivot = m[i].get(i, 0)
                    break
            else:
                return 0  # Singular matrix

        # Eliminate rows below
        for j in range(i + 1, n):
            factor = m[j].get(i, 0)
            if factor != 0:
                multiplier = factor / pivot
                # Row operation: R[j] = R[j] - multiplier * R[i]
                # Optimization: Only iterate over non-zero elements of R[i]
                for k, val in m[i].items():
                    if k >= i:  # Only update relevant columns
                        m[j][k] = m[j].get(k, 0) - multiplier * val

    # Product of diagonals
    result = sign
    for i in range(n):
        result *= m[i].get(i, 0)

    return result


def eigen_centrality(
    matrix: SparseMatrix[K, N],
    iterations: int = 100,
    tolerance: float = 1e-6,
) -> SparseVector[K, float]:
    """
    Compute the eigenvector centrality (principal eigenvector) using the Power Iteration method.
    This is useful for ranking nodes in a graph (like PageRank).

    Args:
        matrix: The adjacency matrix (must be square and non-negative).
        iterations: Maximum number of iterations.
        tolerance: Convergence tolerance.

    Returns:
        A normalized dictionary representing the principal eigenvector.
    """
    # Initialize vector with uniform probability
    nodes = set(matrix.keys()) | {k for row in matrix.values() for k in row}
    n = len(nodes)
    if n == 0:
        return {}

    vector = dict.fromkeys(nodes, 1.0 / n)

    for _ in range(iterations):
        # v_new = M * v_old (Note: usually defined as v M for row vectors, or M v for col vectors)
        # Here we treat 'vector' as a column vector, so we do M * v
        new_vector = mat_vec(matrix, vector)

        # Normalize
        # (L2 norm or Sum norm? Centrality usually uses L2, but simple power iteration often just normalizes max or sum)
        # Let's use Euclidean norm (L2) to keep it standard for eigenvectors
        norm = sum(x * x for x in new_vector.values()) ** 0.5
        if norm == 0:
            return vector  # Matrix is likely zero

        new_vector = {k: v / norm for k, v in new_vector.items()}

        # Check convergence (L1 diff)
        diff = sum(abs(new_vector.get(k, 0) - vector.get(k, 0)) for k in nodes)
        vector = new_vector
        if diff < tolerance:
            break

    return vector


def inverse(matrix: SparseMatrix[K, N]) -> SparseMatrix[K, N]:
    """
    Compute the multiplicative inverse of a square matrix.
    A^-1 = (1 / det(A)) * adj(A)

    WARNING: This operation is computationally expensive and intended for small
    matrices or academic demonstration only.

    Args:
        matrix: The input square matrix.

    Returns:
        The inverse matrix.

    Raises:
        ValueError: If the matrix is singular (determinant is zero).
    """
    warnings.warn(
        'inverse() is computationally expensive and intended for academic demonstration only.',
        PerformanceWarning,
        stacklevel=2,
    )
    # Suppress internal warnings to avoid duplicate alerts
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', PerformanceWarning)
        det = determinant(matrix)
        if det == 0:
            raise ValueError('Matrix is singular (determinant is 0)')

        adj = adjoint(matrix)

    # Scalar multiplication
    return {r: {c: v / det for c, v in row.items()} for r, row in adj.items()}
