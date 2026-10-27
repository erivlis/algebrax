import math
import operator
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Literal

from algebrax.semiring import Semiring, StandardSemiring
from algebrax.typing import K, N, SparseMatrix, SparseVector, V

__all__ = [
    'add',
    'block',
    'block_diag',
    'commutator',
    'dot',
    'element_wise_binary_op',
    'frobenius_inner',
    'hstack',
    'inner',
    'inverse',
    'kronecker_delta',
    'laplacian_matrix',
    'mat_vec',
    'power',
    'slice_matrix',
    'subtract',
    'trace',
    'transpose',
    'vec_add',
    'vec_axpy',
    'vec_clean',
    'vec_mat',
    'vec_norm',
    'vec_scale',
    'vstack',
]


def element_wise_binary_op(
    m1: SparseMatrix[K, V],
    m2: SparseMatrix[K, V],
    op: Callable[[V, V], V],
    zero: V = 0,  # type: ignore[assignment]
) -> SparseMatrix[K, V]:
    """
    Perform element-wise operation of two sparse matrices (nested mappings).

    Args:
        m1: The first matrix.
        m2: The second matrix.
        op: A binary operation function.
        zero: The additive identity element for missing entries and zero-pruning (default 0).
    """
    keys = set(m1.keys()) | set(m2.keys())
    result: dict[K, dict[K, V]] = {}
    for r in keys:
        row1 = m1.get(r, {})
        row2 = m2.get(r, {})
        col_keys = set(row1.keys()) | set(row2.keys())
        new_row: dict[K, V] = {}
        for c in col_keys:
            val = op(row1.get(c, zero), row2.get(c, zero))
            if val != zero:
                new_row[c] = val
        if new_row:
            result[r] = new_row
    return result


def add(
    m1: SparseMatrix[K, V],
    m2: SparseMatrix[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> SparseMatrix[K, V]:
    r"""
    Perform element-wise addition of two sparse matrices (nested mappings) over a semiring.

    Algebraic Signature:
        $(A \oplus B)_{rc} = A_{rc} \oplus B_{rc}$

    Args:
        m1: The first matrix.
        m2: The second matrix.
        semiring: Optional algebraic structure (instance, class, or catalog name).
            Defaults to StandardSemiring (+, *).

    Returns:
        A new nested dictionary representing the sum.
    """
    if semiring is None:
        return element_wise_binary_op(m1, m2, operator.add, zero=0)  # type: ignore[arg-type]
    sr = Semiring.normalize(semiring)
    return element_wise_binary_op(m1, m2, sr.add, zero=sr.zero)


def subtract(m1: SparseMatrix[K, N], m2: SparseMatrix[K, N]) -> SparseMatrix[K, N]:
    """
    Perform element-wise subtraction of two sparse matrices (nested mappings).

    Args:
        m1: The first matrix.
        m2: The second matrix.

    Returns:
        A new nested dictionary representing the difference.
    """
    return element_wise_binary_op(m1, m2, operator.sub)


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


def commutator(m1: SparseMatrix[K, V], m2: SparseMatrix[K, V]) -> SparseMatrix[K, V]:
    """
    Compute the commutator of two sparse matrices: [M1, M2] = M1 @ M2 - M2 @ M1.

    Args:
        m1: The first matrix.
        m2: The second matrix.

    Returns:
        The commutator matrix.
    """
    return subtract(dot(m1, m2), dot(m2, m1))


def dot(
    m1: SparseMatrix[K, V],
    m2: SparseMatrix[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> SparseMatrix[K, V]:
    """
    Perform matrix multiplication (dot product) of two sparse matrices.
    Supports generalized Semirings (e.g., Tropical, Boolean).

    Args:
        m1: The first matrix (left operand).
        m2: The second matrix (right operand).
        semiring: The algebraic structure to use (instance, class, or catalog name).
            Defaults to StandardSemiring (+, *).

    Returns:
        A new nested dictionary representing the product.
    """
    if semiring is None:
        sr = StandardSemiring()
    elif isinstance(semiring, type):
        sr = semiring()
    elif hasattr(semiring, 'add') and hasattr(semiring, 'mul'):
        sr = semiring
    else:
        sr = Semiring.normalize(semiring)

    sr_add = sr.add
    sr_mul = sr.mul
    zero = getattr(sr, 'zero', 0)
    is_zero_fn = getattr(sr, 'is_zero', None)

    result = {}
    for r, row1 in m1.items():
        new_row: dict[K, V] = {}
        for k, val1 in row1.items():
            if k in m2:
                for c, val2 in m2[k].items():
                    term = sr_mul(val1, val2)
                    if c in new_row:
                        new_row[c] = sr_add(new_row[c], term)
                    else:
                        new_row[c] = term
        if is_zero_fn is not None:
            new_row = {c: v for c, v in new_row.items() if not is_zero_fn(v)}
        elif zero is not None:
            new_row = {c: v for c, v in new_row.items() if v != zero}
        if new_row:
            result[r] = new_row
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
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> V:
    """
    Compute the inner product (dot product) of two vectors.

    Args:
        v1: The first vector.
        v2: The second vector.
        semiring: The algebraic structure to use (instance, class, or catalog name).
            Defaults to StandardSemiring.

    Returns:
        The scalar dot product.
    """
    sr = StandardSemiring() if semiring is None else Semiring.normalize(semiring)

    sr_add = sr.add
    sr_mul = sr.mul

    common = set(v1.keys()) & set(v2.keys())
    result = sr.zero
    for k in common:
        term = sr_mul(v1[k], v2[k])
        result = sr_add(result, term)

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


def _symmetrize_adjacency(
    matrix: SparseMatrix[K, float],
    nodes: set[K],
    symmetrize: bool,
) -> dict[K, dict[K, float]]:
    adj: dict[K, dict[K, float]] = {u: {} for u in nodes}
    for u, neighbors in matrix.items():
        for v, w in neighbors.items():
            if u != v and w != 0:
                if symmetrize:
                    rev_w = matrix.get(v, {}).get(u, 0.0)
                    avg_w = 0.5 * (float(w) + float(rev_w))
                    if avg_w != 0:
                        adj[u][v] = avg_w
                        adj[v][u] = avg_w
                else:
                    adj[u][v] = float(w)
    return adj


def _build_unnormalized_laplacian(
    adj: dict[K, dict[K, float]],
    degrees: dict[K, float],
    nodes: set[K],
) -> dict[K, dict[K, float]]:
    lap: dict[K, dict[K, float]] = {u: {} for u in nodes}
    for u in nodes:
        d_u = degrees[u]
        if d_u != 0:
            lap[u][u] = d_u
        for v, w in adj[u].items():
            lap[u][v] = -w
    return lap


def _build_sym_laplacian(
    adj: dict[K, dict[K, float]],
    degrees: dict[K, float],
    nodes: set[K],
) -> dict[K, dict[K, float]]:
    lap: dict[K, dict[K, float]] = {u: {} for u in nodes}
    inv_sqrt_d = {u: (1.0 / math.sqrt(degrees[u]) if degrees[u] > 0 else 0.0) for u in nodes}
    for u in nodes:
        if degrees[u] > 0:
            lap[u][u] = 1.0
        for v, w in adj[u].items():
            val = -w * inv_sqrt_d[u] * inv_sqrt_d[v]
            if val != 0:
                lap[u][v] = val
    return lap


def _build_rw_laplacian(
    adj: dict[K, dict[K, float]],
    degrees: dict[K, float],
    nodes: set[K],
) -> dict[K, dict[K, float]]:
    lap: dict[K, dict[K, float]] = {u: {} for u in nodes}
    for u in nodes:
        d = degrees[u]
        if d > 0:
            lap[u][u] = 1.0
            for v, w in adj[u].items():
                lap[u][v] = -w / d
    return lap


def _build_laplacian_dict(
    adj: dict[K, dict[K, float]],
    degrees: dict[K, float],
    nodes: set[K],
    normalized: Literal['sym', 'rw'] | None,
) -> dict[K, dict[K, float]]:
    if normalized == 'sym':
        return _build_sym_laplacian(adj, degrees, nodes)
    if normalized == 'rw':
        return _build_rw_laplacian(adj, degrees, nodes)
    return _build_unnormalized_laplacian(adj, degrees, nodes)


def laplacian_matrix(
    matrix: SparseMatrix[K, float],
    normalized: Literal['sym', 'rw'] | None = None,
    symmetrize: bool = True,
) -> SparseMatrix[K, float]:
    r"""Construct the graph Laplacian matrix from a sparse adjacency or similarity matrix.

    Algebraic Signature:
        $L = D - W \in \mathbb{R}^{|V| \times |V|}$
        $L_{\mathrm{sym}} = D^{-1/2} L D^{-1/2} = I - D^{-1/2} W D^{-1/2}$
        $L_{\mathrm{rw}} = D^{-1} L = I - D^{-1} W$

    Carrier:
        `SparseMatrix[K, float]` (Symmetric or row-stochastic linear operator).

    Housed In:
        `algebrax.matrix` (canonical), cross-exported in `algebrax.analysis`.

    Args:
        matrix: Sparse adjacency or similarity matrix representing weighted edges `u -> {v: weight}`.
        normalized: Normalization mode:
            - `None`: Combinatorial Laplacian $L = D - W$.
            - `'sym'`: Symmetric normalized Laplacian $L_{\mathrm{sym}} = D^{-1/2} L D^{-1/2}$.
            - `'rw'`: Random-walk normalized Laplacian $L_{\mathrm{rw}} = D^{-1} L$.
        symmetrize: If True, symmetrizes directed inputs as $(W + W^T) / 2$. Defaults to True.

    Returns:
        Sparse matrix representation of the Laplacian operator.
    """
    if normalized not in (None, 'sym', 'rw'):
        raise ValueError(f"Unknown normalization mode: '{normalized}'. Expected None, 'sym', or 'rw'.")

    nodes: set[K] = set(matrix.keys())
    for row in matrix.values():
        nodes.update(row.keys())

    if not nodes:
        return {}

    adj = _symmetrize_adjacency(matrix, nodes, symmetrize)
    degrees = {u: sum(adj[u].values()) for u in nodes}
    lap = _build_laplacian_dict(adj, degrees, nodes, normalized)

    return {
        u: {v: w for v, w in row.items() if abs(w) > 1e-14}
        for u, row in lap.items()
        if any(abs(w) > 1e-14 for w in row.values())
    }


def mat_vec(
    matrix: SparseMatrix[K, V],
    vector: SparseVector[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> SparseVector[K, V]:
    """
    Multiply a matrix by a vector (M * v).

    Args:
        matrix: The matrix.
        vector: The vector.
        semiring: The algebraic structure to use (instance, class, or catalog name).
            Defaults to StandardSemiring.

    Returns:
        The resulting vector.
    """
    sr = StandardSemiring() if semiring is None else Semiring.normalize(semiring)

    zero = sr.zero
    result = {}

    for r, row in matrix.items():
        # row * vector (inner product)
        val = inner(row, vector, sr)
        if val != zero:
            result[r] = val
    return result


def power(
    matrix: SparseMatrix[K, V],
    n: int,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> SparseMatrix[K, V]:
    """
    Compute the n-th power of a square matrix using binary exponentiation.

    Args:
        matrix: The input matrix.
        n: The exponent (must be non-negative).
        semiring: The algebraic structure to use (instance, class, or catalog name).
            Defaults to StandardSemiring.

    Returns:
        The result of matrix ** n.
    """
    if n < 0:
        raise ValueError('Exponent must be non-negative.')

    sr = StandardSemiring() if semiring is None else Semiring.normalize(semiring)

    # Identity matrix construction
    keys = set(matrix.keys()) | {k for row in matrix.values() for k in row}
    one = sr.one
    result = {k: {k: one} for k in keys}

    base = matrix
    while n > 0:
        if n % 2 == 1:
            result = dot(result, base, sr)
        base = dot(base, base, sr)
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


def trace(
    matrix: SparseMatrix[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> V:
    r"""
    Calculate the trace of a matrix (sum of diagonal elements) over a semiring.

    Algebraic Signature:
        $\mathrm{Tr}_{\mathcal{S}}(A) = \bigoplus_{r} A_{rr}$

    Args:
        matrix: The input matrix.
        semiring: Optional algebraic structure (instance, class, or catalog name).
            Defaults to StandardSemiring.

    Returns:
        The sum of diagonal elements.
    """
    if semiring is None:
        return sum(row.get(r, 0) for r, row in matrix.items())  # type: ignore[return-value, misc]
    sr = Semiring.normalize(semiring)
    acc = sr.zero
    sr_add = sr.add
    for r, row in matrix.items():
        if r in row:
            acc = sr_add(acc, row[r])
    return acc


def transpose(matrix: Mapping[K, Mapping[K, V]]) -> dict[K, dict[K, V]]:
    """
    Transpose a sparse matrix (swap rows and columns) in a single pass.

    Args:
        matrix: The input matrix (nested mapping).

    Returns:
        A new nested dictionary with rows and columns swapped.
    """
    result: dict[K, dict[K, V]] = {}
    for r, row in matrix.items():
        for c, val in row.items():
            if c not in result:
                result[c] = {r: val}
            else:
                result[c][r] = val
    return result


def vec_mat(
    vector: SparseVector[K, V],
    matrix: SparseMatrix[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> SparseVector[K, V]:
    """
    Multiply a vector by a matrix (v * M).

    Args:
        vector: The vector.
        matrix: The matrix.
        semiring: The algebraic structure to use (instance, class, or catalog name).
            Defaults to StandardSemiring.

    Returns:
        The resulting vector.
    """
    sr = StandardSemiring() if semiring is None else Semiring.normalize(semiring)

    sr_add = sr.add
    sr_mul = sr.mul
    zero = sr.zero
    result = defaultdict(lambda: zero)

    for k, val in vector.items():
        if k in matrix:
            for c, m_val in matrix[k].items():
                term = sr_mul(val, m_val)
                result[c] = sr_add(result[c], term)

    return {k: v for k, v in result.items() if v != zero}


def vec_add(
    u: SparseVector[K, V],
    v: SparseVector[K, V],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
    tol: float = 0.0,
) -> dict[K, V]:
    r"""Compute sparse vector addition $(u \oplus v)_k = u_k \oplus v_k$.

    Args:
        u: First sparse vector.
        v: Second sparse vector.
        semiring: Optional algebraic structure (instance, class, or catalog name).
            Defaults to StandardSemiring.
        tol: Numerical pruning threshold when using standard numeric addition (default 0.0).

    Returns:
        A new dictionary representing the vector sum.
    """
    keys = set(u.keys()) | set(v.keys())
    if semiring is not None:
        sr = Semiring.normalize(semiring)
        sr_add = sr.add
        zero = sr.zero
        res_sr: dict[K, V] = {}
        for k in keys:
            val = sr_add(u.get(k, zero), v.get(k, zero))
            if val != zero:
                res_sr[k] = val
        return res_sr

    res: dict[K, V] = {}
    for k in keys:
        val = u.get(k, 0) + v.get(k, 0)  # type: ignore[operator]
        keep = (abs(val) > tol) if tol > 0.0 else (val != 0)  # type: ignore[arg-type]
        if keep:
            res[k] = val
    return res


def vec_scale(
    u: SparseVector[K, V],
    scalar: V,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
    tol: float = 1e-14,
) -> dict[K, V]:
    r"""Compute left scalar multiplication $(s \otimes u)_k = s \otimes u_k$ with sparsity pruning.

    Args:
        u: Input sparse vector.
        scalar: Scalar multiplier.
        semiring: Optional algebraic structure (instance, class, or catalog name).
        tol: Numerical magnitude pruning threshold when `semiring` is None (default 1e-14).

    Returns:
        A new scaled sparse vector dictionary.
    """
    if semiring is not None:
        sr = Semiring.normalize(semiring)
        sr_mul = sr.mul
        zero = sr.zero
        res_sr: dict[K, V] = {}
        for k, val in u.items():
            prod = sr_mul(scalar, val)
            if prod != zero:
                res_sr[k] = prod
        return res_sr

    res: dict[K, V] = {}
    for k, val in u.items():
        prod = scalar * val  # type: ignore[operator]
        keep = (abs(prod) > tol) if tol > 0.0 else (prod != 0)  # type: ignore[arg-type]
        if keep:
            res[k] = prod
    return res


def vec_axpy(
    a: float | complex,
    x: SparseVector[K, float | complex],
    y: SparseVector[K, float | complex],
    tol: float = 1e-14,
) -> dict[K, float | complex]:
    r"""Compute fused sparse linear combination $\mathbf{z} = a \mathbf{x} + \mathbf{y}$ in a single pass.

    Args:
        a: Scalar multiplier for vector `x`.
        x: Scaled sparse vector.
        y: Base sparse vector added to `a * x`.
        tol: Numerical magnitude threshold for pruning near-zero entries (default 1e-14).

    Returns:
        A new sparse vector dictionary representing `a * x + y`.
    """
    if a == 0:  # NOSONAR - exact zero multiplier shortcut
        return {k: v for k, v in y.items() if (abs(v) > tol if tol > 0.0 else v != 0)}

    keys = set(x.keys()) | set(y.keys())
    res: dict[K, float | complex] = {}
    for k in keys:
        val = a * x.get(k, 0.0) + y.get(k, 0.0)
        if (abs(val) > tol) if tol > 0.0 else (val != 0):
            res[k] = val
    return res


def vec_norm(
    u: SparseVector[K, float | complex],
    p: float = 2.0,
) -> float:
    r"""Compute the $L_p$ norm $\|\mathbf{u}\|_p = \left(\sum_k |u_k|^p\right)^{1/p}$ of a sparse vector.

    Args:
        u: Input real or complex sparse vector.
        p: Norm order ($p \ge 1$ or `math.inf`, default 2.0).

    Returns:
        Non-negative float norm.

    Raises:
        ValueError: If `p <= 0`.
    """
    if p <= 0.0:
        raise ValueError(f'Norm order p must be positive, got {p}.')
    if not u:
        return 0.0
    if math.isinf(p):
        return float(max(abs(v) for v in u.values()))
    if p == 1.0:  # NOSONAR - exact L1 norm dispatch
        return float(sum(abs(v) for v in u.values()))
    if p == 2.0:  # NOSONAR - exact Euclidean L2 norm dispatch
        return math.sqrt(sum(abs(v) ** 2 for v in u.values()))
    return float(sum(abs(v) ** p for v in u.values()) ** (1.0 / p))


def vec_clean(
    u: SparseVector[K, float | complex],
    tol: float = 1e-12,
) -> dict[K, float | complex]:
    """Prune numerical noise $|u_k| \\le \\text{tol}$ and strip negligible imaginary components.

    Args:
        u: Input real or complex sparse vector.
        tol: Magnitude tolerance threshold (default 1e-12).

    Returns:
        Cleaned sparse vector dictionary.
    """
    res: dict[K, float | complex] = {}
    for k, v in u.items():
        if abs(v) > tol:
            res[k] = v.real if isinstance(v, complex) and abs(v.imag) < tol else v
    return res


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


def frobenius_inner(
    m1: SparseMatrix[K, N],
    m2: SparseMatrix[K, N],
    conjugate: bool = True,
    semiring: Semiring[N] | type[Semiring[N]] | str | None = None,
) -> N:
    r"""Compute the Frobenius (Hilbert-Schmidt) inner product of two sparse matrices.

    Formula:
        $\langle A, B \rangle_F = \mathrm{Tr}(A^\dagger B) = \sum_{r, c} \overline{A_{rc}} B_{rc}$

    Under a semiring $(S, \oplus, \otimes)$:
        $\bigoplus_{r, c} A_{rc} \otimes B_{rc}$

    Args:
        m1: First sparse matrix.
        m2: Second sparse matrix.
        conjugate: Whether to take the complex conjugate of m1 entries (default True).
        semiring: Optional semiring for generalized inner products (instance, class, or catalog name).
            Defaults to standard arithmetic.

    Returns:
        Scalar inner product value.
    """
    if semiring is not None:
        sr = Semiring.normalize(semiring)
        sr_add = sr.add
        sr_mul = sr.mul
        res = sr.zero
        for r, row in m1.items():
            if r in m2:
                row2 = m2[r]
                for c, v1 in row.items():
                    if c in row2:
                        term = sr_mul(v1, row2[c])
                        res = sr_add(res, term)
        return res

    val: complex = 0.0 + 0.0j
    for r, row in m1.items():
        if r in m2:
            row2 = m2[r]
            for c, v in row.items():
                if c in row2:
                    v_conj = v.conjugate() if (conjugate and isinstance(v, complex)) else v
                    val += v_conj * row2[c]
    return val.real if abs(val.imag) < 1e-14 else val


def inverse(  # noqa: C901, NOSONAR - Gauss-Jordan sparse elimination kernel with partial pivoting
    matrix: SparseMatrix[K, N],
    tol: float = 1e-12,
) -> SparseMatrix[K, N]:
    r"""Compute the inverse of a square sparse matrix using Gauss-Jordan elimination with partial pivoting.

    Operates natively on sparse dictionary mappings (`SparseMatrix[K, V]`) without converting
    to dense arrays. Supports real numbers, complex numbers, and arbitrary hashable row/column keys.

    Args:
        matrix: Input square sparse matrix (`dict[K, dict[K, V]]`).
        tol: Tolerance for zero detection and singularity checks (default 1e-12).

    Returns:
        The sparse inverse matrix $A^{-1}$ satisfying $\mathrm{dot}(A, A^{-1}) = I$.

    Raises:
        ValueError: If the matrix is singular (cannot be inverted) or empty.
    """
    keys = sorted(set(matrix.keys()) | {c for row in matrix.values() for c in row}, key=str)
    n = len(keys)
    if n == 0:
        raise ValueError('Cannot invert an empty sparse matrix.')

    key_map = {k: i for i, k in enumerate(keys)}

    # Single augmented matrix [A | I] where columns 0..n-1 are A and n..2n-1 are I
    aug: dict[int, dict[int, N]] = {i: {n + i: 1.0} for i in range(n)}

    for r, row in matrix.items():
        if r in key_map:
            r_idx = key_map[r]
            for c, val in row.items():
                if c in key_map and abs(val) > tol:
                    aug[r_idx][key_map[c]] = val

    for k in range(n):
        pivot_r = k
        max_val = abs(aug[k].get(k, 0.0))
        for p in range(k + 1, n):
            val = abs(aug[p].get(k, 0.0))
            if val > max_val:
                max_val = val
                pivot_r = p

        if max_val < tol:
            raise ValueError(f'Matrix is singular at pivot column {k} (tolerance={tol}).')

        if pivot_r != k:
            aug[k], aug[pivot_r] = aug[pivot_r], aug[k]

        pivot = aug[k][k]
        aug[k] = {c: v / pivot for c, v in aug[k].items()}
        row_k = aug[k]

        # Single-pass elimination across the entire augmented row [A | I]
        for r in range(n):
            if r != k and k in aug[r]:
                factor = aug[r][k]
                if abs(factor) > tol:
                    for c, val in row_k.items():
                        new_val = aug[r].get(c, 0.0) - factor * val
                        if abs(new_val) > tol:
                            aug[r][c] = new_val
                        elif c in aug[r]:
                            del aug[r][c]

    result: dict[K, dict[K, N]] = {}
    for i, row in aug.items():
        r_key = keys[i]
        row_dict = {}
        for c, v in row.items():
            if c >= n:
                col_key = keys[c - n]
                clean_v = v.real if abs(getattr(v, 'imag', 0.0)) < tol else v
                if abs(clean_v) > tol:
                    row_dict[col_key] = clean_v
        if row_dict:
            result[r_key] = row_dict
    return result


def _find_matrix_components(matrix: SparseMatrix[K, float], keys: list[K]) -> list[list[K]]:
    """Partition matrix keys into undirected connected components for component-wise nullspace deflation."""
    adj: dict[K, set[K]] = {k: set() for k in keys}
    for r, row in matrix.items():
        if r in adj:
            for c, val in row.items():
                if c in adj and c != r and val != 0:
                    adj[r].add(c)
                    adj[c].add(r)

    visited: set[K] = set()
    components: list[list[K]] = []
    for k in keys:
        if k not in visited:
            comp: list[K] = []
            queue = [k]
            visited.add(k)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            components.append(comp)
    return components


def _deflate_components(
    v: SparseVector[K, float],
    components: list[list[K]],
    tol: float = 1e-15,
) -> dict[K, float]:
    """Project vector v orthogonal to the piecewise-constant nullspace over each component."""
    out: dict[K, float] = {}
    for comp in components:
        if not comp:
            continue
        mean = sum(float(v.get(k, 0.0)) for k in comp) / len(comp)
        for k in comp:
            shifted = float(v.get(k, 0.0)) - mean
            if abs(shifted) > tol:
                out[k] = shifted
    return out


def cg_solve(
    matrix: SparseMatrix[K, float],
    rhs: SparseVector[K, float],
    tol: float = 1e-9,
    max_iter: int | None = None,
    project_nullspace: bool = False,
) -> dict[K, float]:
    r"""Solve $A \mathbf{x} = \mathbf{b}$ for a symmetric positive semi-definite sparse matrix via Conjugate Gradients.

    Algebraic Signature:
        $\mathbf{x}^* = \arg\min_{\mathbf{x} \perp \ker(A)}
        \left(\frac{1}{2} \mathbf{x}^T A \mathbf{x} - \mathbf{b}^T \mathbf{x}\right)$

    Carrier:
        `dict[K, float]` (Sparse solution vector).

    Operations:
        - Krylov Subspace Iteration: Updates iterate $\mathbf{x}$, residual $\mathbf{r}$, and $A$-conjugate
          search direction $\mathbf{p}$ using sparse `mat_vec`, `inner`, and `vec_axpy`.
        - Nullspace Gauge Deflation (`project_nullspace=True`): Projects residuals onto $\mathbf{1}_C^\perp$
          across each connected component $C$ to solve singular Laplacian systems ($\Delta_0 \alpha = \delta_1 \omega$).

    Properties:
        Converges in at most $\operatorname{rank}(A)$ exact-arithmetic steps or $O(\sqrt{\kappa(A)})$
        iterations without matrix factorization or fill-in.

    Applications:
        - Discrete Poisson and Hodge Laplacian potential equations ($\Delta_k u = f$).
        - Helmholtz-Hodge flow decomposition and harmonic interpolation.

    Args:
        matrix: Symmetric positive (semi-)definite `SparseMatrix[K, float]`.
        rhs: Right-hand side `SparseVector[K, float]`.
        tol: Residual Euclidean norm convergence threshold (default `1e-9`).
        max_iter: Maximum Krylov iterations (defaults to `max(500, 10 * n)`).
        project_nullspace: Whether to deflate the piecewise-constant nullspace at each step.

    Returns:
        Sparse solution dictionary mapping keys `K` to float values.
    """
    if not matrix or not rhs:
        return {}

    keys = sorted(set(matrix.keys()) | {c for row in matrix.values() for c in row}, key=str)
    if not keys:
        return {}

    iters = max_iter if max_iter is not None else max(500, 10 * len(keys))
    components = _find_matrix_components(matrix, keys) if project_nullspace else []

    x: dict[K, float] = {}
    b = _deflate_components(rhs, components) if project_nullspace else {k: float(v) for k, v in rhs.items()}
    r: dict[K, float] = dict(b)
    p: dict[K, float] = dict(r)
    rsold = float(inner(r, r))

    if math.sqrt(rsold) <= tol:
        return x

    for _ in range(iters):
        ap = mat_vec(matrix, p)
        if project_nullspace:
            ap = _deflate_components(ap, components)
        pap = float(inner(p, ap))
        if abs(pap) <= 1e-15:
            break
        alpha = rsold / pap
        x = vec_axpy(alpha, p, x, tol=1e-15)  # type: ignore[assignment]
        r = vec_axpy(-alpha, ap, r, tol=1e-15)  # type: ignore[assignment]
        if project_nullspace:
            r = _deflate_components(r, components)
        rsnew = float(inner(r, r))
        if math.sqrt(rsnew) <= tol:
            break
        beta = rsnew / rsold
        p = vec_axpy(beta, p, r, tol=1e-15)  # type: ignore[assignment]
        rsold = rsnew

    if project_nullspace:
        x = _deflate_components(x, components, tol=1e-12)
    return vec_clean(x, tol=1e-12)  # type: ignore[return-value]
