r"""
Normed vector spaces, standard sparse p-norms, inner products, and Gram-Schmidt orthogonalization.

Algebraic Signatures:
    Normed Space:         $\langle R, V, \cdot_s, \mathbf{0}, +, -, \|\cdot\| \rangle$
    Inner Product Space:  $\langle R, V, \cdot_s, \mathbf{0}, +, -, \|\cdot\|, \langle \cdot, \cdot \rangle \rangle$

Key Operations:
    - Vector p-norms: $L_1, L_2, L_\infty, L_p$ on unboxed sparse vectors `dict[K, float]`.
    - Matrix norms: Frobenius norm $\|A\|_F$, operator $1$-norm, operator $\infty$-norm.
    - Inner products: Euclidean/Hermitian dot product $\langle u, v \rangle = \sum u_k \overline{v_k}$.
    - Angles & Cosine similarity: $\cos \theta = \frac{\langle u, v \rangle}{\|u\|_2 \|v\|_2}$.
    - Gram-Schmidt orthogonalization: constructing orthonormal sparse bases.
    - `EuclideanSpace`: Concrete canonical inner product space on sparse vectors.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from typing import Any, TypeVar

from algebrax.algebra._normed import InnerProductSpace, NormedSpace
from algebrax.typing import SparseMatrix, SparseVector

K = TypeVar('K', bound=Hashable)


def norm_p(vec: SparseVector[Any, float], p: float = 2.0) -> float:
    r"""Compute the sparse vector $L_p$ norm: $\|x\|_p = \left( \sum_k |x_k|^p \right)^{1/p}$.

    Complexity:
        Time $O(\operatorname{nnz}(x))$, Space $O(1)$.

    Parameters:
        vec: Unboxed sparse vector `dict[K, float]`.
        p: Norm order ($1.0 \le p \le \infty$). Default is Euclidean $2.0$.

    Returns:
        The non-negative norm value $\|x\|_p \ge 0$.

    Raises:
        ValueError: If $p < 1.0$.
    """
    if p < 1.0:
        raise ValueError(f'Norm order p must be >= 1.0, got {p}')

    if not vec:
        return 0.0

    if p == float('inf'):
        return max((abs(v) for v in vec.values()), default=0.0)
    if p == 1.0:  # NOSONAR - exact fast-path for L1 norm
        return sum(abs(v) for v in vec.values())
    if p == 2.0:  # NOSONAR - exact fast-path for Euclidean L2 norm
        return math.sqrt(sum(v * v for v in vec.values()))

    return math.pow(sum(abs(v) ** p for v in vec.values()), 1.0 / p)


def norm_frobenius(mat: SparseMatrix[Any, float]) -> float:
    r"""Compute the matrix Frobenius norm $\|A\|_F = \sqrt{\sum_{i, j} A_{ij}^2}$.

    Complexity:
        Time $O(\operatorname{nnz}(A))$, Space $O(1)$.
    """
    if not mat:
        return 0.0
    return math.sqrt(sum(val * val for row in mat.values() for val in row.values()))


def norm_operator_1(mat: SparseMatrix[Any, float]) -> float:
    r"""Compute the induced matrix operator $1$-norm (maximum absolute column sum).

    $$\|A\|_1 = \max_j \sum_i |A_{ij}|$$
    """
    if not mat:
        return 0.0
    col_sums: dict[Any, float] = {}
    for row in mat.values():
        for col, val in row.items():
            col_sums[col] = col_sums.get(col, 0.0) + abs(val)
    return max(col_sums.values(), default=0.0)


def norm_operator_inf(mat: SparseMatrix[Any, float]) -> float:
    r"""Compute the induced matrix operator $\infty$-norm (maximum absolute row sum).

    $$\|A\|_\infty = \max_i \sum_j |A_{ij}|$$
    """
    if not mat:
        return 0.0
    return max((sum(abs(val) for val in row.values()) for row in mat.values()), default=0.0)


def inner_euclidean(
    u: SparseVector[Any, Any],
    v: SparseVector[Any, Any],
) -> float | complex:
    r"""Compute the Euclidean (or Hermitian) inner product $\langle u, v \rangle = \sum_{k} u_k \overline{v_k}$.

    Complexity:
        Time $O(\min(\operatorname{nnz}(u), \operatorname{nnz}(v)))$, Space $O(1)$.
    """
    if not u or not v:
        return 0.0

    # Iterate over the sparser vector
    if len(u) > len(v):
        u, v = v, u
        swap = True
    else:
        swap = False

    total: float | complex = 0.0
    for k, val_u in u.items():
        if k in v:
            val_v = v[k]
            if swap:
                # We swapped u and v; originally u was the second argument: v_orig * conj(u_orig)
                val_u, val_v = val_v, val_u
            if isinstance(val_v, complex):
                total += val_u * val_v.conjugate()
            elif isinstance(val_u, complex):
                total += val_u * val_v
            else:
                total += float(val_u) * float(val_v)

    if isinstance(total, complex) and abs(total.imag) < 1e-15:
        return total.real
    return total


def cosine_similarity(
    u: SparseVector[Any, float],
    v: SparseVector[Any, float],
) -> float:
    r"""Compute the cosine similarity $\cos \theta = \frac{\langle u, v \rangle}{\|u\|_2 \|v\|_2} \in [-1, 1]$.

    Returns 0.0 if either vector has norm 0.
    """
    norm_u = norm_p(u, 2.0)
    norm_v = norm_p(v, 2.0)
    if norm_u < 1e-15 or norm_v < 1e-15:
        return 0.0
    val = float(inner_euclidean(u, v))
    cos = val / (norm_u * norm_v)
    return max(-1.0, min(1.0, cos))


def gram_schmidt(
    vectors: Sequence[SparseVector[Any, float]],
    normalize: bool = True,
    tol: float = 1e-12,
) -> list[SparseVector[Any, float]]:
    r"""Orthogonalize a sequence of sparse vectors using the Gram-Schmidt process.

    Parameters:
        vectors: Input sparse vectors $[v_1, v_2, \dots, v_m]$.
        normalize: If True, normalize output vectors to unit Euclidean length ($\|u_k\|_2 = 1$).
        tol: Threshold below which near-zero vectors are discarded (linearly dependent).

    Returns:
        List of mutually orthogonal (or orthonormal) sparse vectors.
    """
    basis: list[SparseVector[Any, float]] = []

    for v in vectors:
        if not v:
            continue
        # Copy input vector
        u: dict[Any, float] = {k: float(val) for k, val in v.items() if abs(val) > tol}

        # Project out components along existing basis vectors
        for b in basis:
            b_norm_sq = float(inner_euclidean(b, b))
            if b_norm_sq < tol:
                continue
            coeff = float(inner_euclidean(u, b)) / b_norm_sq
            if abs(coeff) > tol:
                for k, b_val in b.items():
                    u[k] = u.get(k, 0.0) - coeff * b_val
                    if abs(u[k]) < tol:
                        del u[k]

        u_norm = norm_p(u, 2.0)
        if u_norm > tol:
            if normalize:
                u = {k: val / u_norm for k, val in u.items() if abs(val / u_norm) > tol}
            basis.append(u)

    return basis


class EuclideanSpace(InnerProductSpace[float, SparseVector[K, float]], NormedSpace[float, SparseVector[K, float]]):
    r"""Canonical Euclidean inner product space over unboxed sparse vectors `dict[K, float]`.

    Satisfies both `InnerProductSpace` and `NormedSpace` protocols with zero element boxing.
    """

    @property
    def zero(self) -> SparseVector[K, float]:
        return {}

    def add(self, a: SparseVector[K, float], b: SparseVector[K, float]) -> SparseVector[K, float]:
        res = dict(a)
        for k, v in b.items():
            res[k] = res.get(k, 0.0) + v
        return {k: v for k, v in res.items() if v != 0.0}  # NOSONAR - exact sparse zero pruning

    def neg(self, a: SparseVector[K, float]) -> SparseVector[K, float]:
        return {k: -v for k, v in a.items() if v != 0.0}  # NOSONAR - exact sparse zero pruning

    def sub(self, a: SparseVector[K, float], b: SparseVector[K, float]) -> SparseVector[K, float]:
        return self.add(a, self.neg(b))

    def smul(self, r: float, m: SparseVector[K, float]) -> SparseVector[K, float]:
        if r == 0.0:  # NOSONAR - exact scalar zero fast-path
            return {}
        return {k: r * v for k, v in m.items() if r * v != 0.0}  # NOSONAR - exact sparse zero pruning

    def norm(self, v: SparseVector[K, float]) -> float:
        return norm_p(v, 2.0)

    def inner(self, u: SparseVector[K, float], v: SparseVector[K, float]) -> float:
        return float(inner_euclidean(u, v))

    def distance(self, u: SparseVector[K, float], v: SparseVector[K, float]) -> float:
        return self.norm(self.sub(u, v))
