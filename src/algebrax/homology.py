"""
Simplicial Homology, Betti Numbers & Persistent Barcodes (EP-0110).

This module provides tools for constructing simplicial complexes, computing boundary matrices,
evaluating Betti numbers beta_k, and conducting topological data analysis.
"""

from collections.abc import Iterable
from itertools import combinations

from algebrax.analysis import SparseChainComplex
from algebrax.typing import SparseMatrix


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
