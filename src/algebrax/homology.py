"""
Topological Data Analysis & Homology.

Summary:
    Counts connected components (beta_0) and multidimensional holes (beta_1, beta_2)
    in point clouds, meshes, and graph structures using boundary matrices and Hodge Laplacians.

This module provides tools for constructing simplicial complexes, computing boundary matrices,
evaluating Betti numbers beta_k, and conducting topological data analysis.
"""

from collections.abc import Iterable
from itertools import combinations

from algebrax.semiring import Semiring, StandardSemiring
from algebrax.typing import SparseMatrix

__all__ = [
    'SimplicialComplex',
    'SparseChainComplex',
    'coboundary',
    'cohomology_rank',
]


class SparseChainComplex:
    """
    A sequence space C_k and sparse boundary matrices D_k satisfying D_{k-1} o D_k = 0.

    Attributes:
        boundary_matrices: Dictionary mapping dimension k to sparse boundary matrix D_k.
                           D_k maps k-simplices/forms to (k-1)-simplices/forms.

    Example:
        >>> d1 = {(0,): {(0, 1): -1.0}, (1,): {(0, 1): 1.0}}
        >>> scc = SparseChainComplex({1: d1})
        >>> scc.verify_nilpotency(1)
        True
    """

    def __init__(self, boundary_matrices: dict[int, SparseMatrix]):
        self.boundary_matrices = boundary_matrices

    def verify_nilpotency(self, k: int, semiring: type[Semiring] = StandardSemiring) -> bool:
        """
        Verify that D_{k-1} o D_k == 0 (empty sparse matrix).

        Example:
            >>> scc = SparseChainComplex({})
            >>> scc.verify_nilpotency(1)
            True
        """
        from algebrax.matrix.core import dot

        if k - 1 not in self.boundary_matrices or k not in self.boundary_matrices:
            return True
        d_prev = self.boundary_matrices[k - 1]
        d_curr = self.boundary_matrices[k]
        comp = dot(d_prev, d_curr, semiring=semiring())
        return len(comp) == 0

    def hodge_laplacian(self, k: int, semiring: type[Semiring] = StandardSemiring) -> SparseMatrix:
        """
        Compute the k-th Hodge-Laplacian matrix Delta_k = D_{k+1} D_{k+1}^T + D_k^T D_k.

        Example:
            >>> sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
            >>> l0 = sc.hodge_laplacian(0)
            >>> (0,) in l0
            True
        """
        from algebrax.matrix.core import add, dot, transpose

        s_inst = semiring()
        l_down: SparseMatrix = {}
        l_up: SparseMatrix = {}

        # D_k^T D_k (down component)
        if k in self.boundary_matrices:
            d_k = self.boundary_matrices[k]
            d_k_t = transpose(d_k)
            l_down = dot(d_k_t, d_k, semiring=s_inst)

        # D_{k+1} D_{k+1}^T (up component)
        if k + 1 in self.boundary_matrices:
            d_k1 = self.boundary_matrices[k + 1]
            d_k1_t = transpose(d_k1)
            l_up = dot(d_k1, d_k1_t, semiring=s_inst)

        if not l_down:
            return l_up
        if not l_up:
            return l_down

        return add(l_down, l_up)


def _matrix_rank(matrix: SparseMatrix) -> int:
    """
    Compute the rank of a sparse dictionary matrix over real numbers using Gaussian elimination.
    """
    if not matrix:
        return 0

    # Convert sparse matrix dict to row dict mapping row_idx -> dict[col_idx, float]
    rows: list[dict[object, float]] = [dict(row) for row in matrix.values() if row]
    if not rows:
        return 0

    rank = 0
    pivots: set[object] = set()

    while rows:
        # Pick row with smallest non-zero elements
        rows.sort(key=lambda r: len(r))
        row = rows.pop(0)

        # Find pivot col
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

        # Eliminate pivot_col from remaining rows
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


class SimplicialComplex(SparseChainComplex):
    """
    A Simplicial Complex built on SparseChainComplex.
    Stores k-simplices as sorted tuples of node indices.
    """

    def __init__(self, simplices: Iterable[tuple[int, ...]] | None = None):
        self._simplices: dict[int, set[tuple[int, ...]]] = {}
        super().__init__(boundary_matrices={})
        if simplices:
            for s in simplices:
                self.add_simplex(s)

    def add_simplex(self, simplex: tuple[int, ...]) -> None:
        """
        Add a simplex and all of its sub-faces to the complex.
        """
        s_tuple = tuple(sorted(simplex))
        k = len(s_tuple) - 1
        if k < 0:
            return

        if k not in self._simplices:
            self._simplices[k] = set()

        if s_tuple in self._simplices[k]:
            return

        self._simplices[k].add(s_tuple)

        # Recursively add sub-faces
        if k > 0:
            for face in combinations(s_tuple, k):
                self.add_simplex(face)

        self._rebuild_boundary_matrices()

    def _rebuild_boundary_matrices(self) -> None:
        """
        Reconstruct boundary matrices D_k for all dimensions k.
        D_k maps k-simplices (columns) to (k-1)-simplices (rows).
        """
        self.boundary_matrices.clear()
        max_k = max(self._simplices.keys()) if self._simplices else 0

        for k in range(1, max_k + 1):
            if k not in self._simplices or (k - 1) not in self._simplices:
                continue

            k_simplices = sorted(self._simplices[k])
            d_k: SparseMatrix = {}
            for col_simplex in k_simplices:
                for i, _v in enumerate(col_simplex):
                    face = col_simplex[:i] + col_simplex[i + 1 :]
                    sign = -1.0 if i % 2 == 1 else 1.0

                    if face not in d_k:
                        d_k[face] = {}
                    d_k[face][col_simplex] = sign

            self.boundary_matrices[k] = d_k

    def betti_numbers(self, max_k: int = 2) -> dict[int, int]:
        """
        Compute Betti numbers [beta_0, beta_1, ..., beta_max_k].
        beta_k = dim(ker D_k) - rank(D_{k+1})
               = num_simplices(k) - rank(D_k) - rank(D_{k+1})
        """
        betti: dict[int, int] = {}
        ranks: dict[int, int] = {}

        max_dim = max(max_k, max(self._simplices.keys()) if self._simplices else 0)
        for k in range(max_dim + 2):
            d_k = self.boundary_matrices.get(k, {})
            ranks[k] = _matrix_rank(d_k)

        for k in range(max_k + 1):
            num_k = len(self._simplices.get(k, set()))
            rank_dk = ranks.get(k, 0)
            rank_dk1 = ranks.get(k + 1, 0)
            betti[k] = max(num_k - rank_dk - rank_dk1, 0)

        return betti


def coboundary(complex: SparseChainComplex, k: int) -> SparseMatrix:
    """
    Compute the k-th coboundary operator d^k = D_{k+1}^T : C^k -> C^{k+1}.

    Args:
        complex: SparseChainComplex or SimplicialComplex instance.
        k: Dimension index k.

    Returns:
        Sparse matrix representation of the coboundary operator d^k.

    Example:
        >>> sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
        >>> d0 = coboundary(sc, 0)
        >>> isinstance(d0, dict)
        True
    """
    from algebrax.matrix.core import transpose

    d_k1 = complex.boundary_matrices.get(k + 1, {})
    return transpose(d_k1)


def cohomology_rank(complex: SparseChainComplex, k: int) -> int:
    """
    Compute the k-th cohomology group rank dim(H^k).

    Args:
        complex: SparseChainComplex or SimplicialComplex instance.
        k: Dimension index k.

    Returns:
        The k-th cohomology rank.

    Example:
        >>> sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
        >>> cohomology_rank(sc, 1)
        1
    """
    if isinstance(complex, SimplicialComplex):
        return complex.betti_numbers(k).get(k, 0)

    d_k = complex.boundary_matrices.get(k, {})
    d_k1 = complex.boundary_matrices.get(k + 1, {})

    rank_dk = _matrix_rank(d_k)
    rank_dk1 = _matrix_rank(d_k1)

    num_k = len({c for row in d_k.values() for c in row}) if d_k else 0
    if not num_k and d_k1:
        num_k = len(d_k1)

    return max(num_k - rank_dk - rank_dk1, 0)


