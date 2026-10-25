"""Simplicial and chain homology complexes, boundary operators, and Betti numbers."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations

from algebrax.semiring import Semiring
from algebrax.topology._core import _matrix_rank
from algebrax.typing import K, SparseMatrix, V

__all__ = [
    'SimplicialComplex',
    'SparseChainComplex',
]


class SparseChainComplex:
    r"""A sequence space $C_k$ and sparse boundary matrices $D_k$ satisfying $D_{k-1} \circ D_k = 0$.

    Algebraic Signature:
        $\cdots \xrightarrow{\partial_{k+1}} C_k \xrightarrow{\partial_k} C_{k-1} \xrightarrow{\partial_{k-1}} \cdots$

    Nilpotency:
        $\partial_{k-1} \circ \partial_k = 0$

    Carrier:
        `dict[int, SparseMatrix]` (Mapping dimension $k$ to sparse matrix $D_k$).

    Operations:
        - Boundary Operator ($\partial_k$): Maps $k$-chains to $(k-1)$-chains.
        - Hodge Laplacian ($\Delta_k$): $\Delta_k = D_{k+1} D_{k+1}^T + D_k^T D_k$.
        - Nilpotency Verification: $D_{k-1} \circ D_k = 0$.

    Properties:
        Nilpotent boundary differential $\partial^2 = 0$, graded chain complex over vector spaces or modules.

    Applications:
        Topological data analysis, Hodge theory, discrete exterior calculus, cycle detection.

    Attributes:
        boundary_matrices: Dictionary mapping dimension k to sparse boundary matrix D_k.
                           D_k maps k-simplices/forms to (k-1)-simplices/forms.

    Example:
        >>> d1 = {(0,): {(0, 1): -1.0}, (1,): {(0, 1): 1.0}}
        >>> scc = SparseChainComplex({1: d1})
        >>> scc.verify_nilpotency(1)
        True
    """

    def __init__(self, boundary_matrices: dict[int, SparseMatrix[K, V]]):
        self.boundary_matrices = boundary_matrices

    def verify_nilpotency(
        self,
        k: int,
        semiring: Semiring[V] | type[Semiring[V]] | None = None,
    ) -> bool:
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
        s_inst = Semiring.normalize(semiring)
        d_prev = self.boundary_matrices[k - 1]
        d_curr = self.boundary_matrices[k]
        comp = dot(d_prev, d_curr, semiring=s_inst)
        return len(comp) == 0

    def hodge_laplacian(
        self,
        k: int,
        semiring: Semiring[V] | type[Semiring[V]] | None = None,
    ) -> SparseMatrix[K, V]:
        """
        Compute the k-th Hodge-Laplacian matrix Delta_k = D_{k+1} D_{k+1}^T + D_k^T D_k.

        Example:
            >>> sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
            >>> l0 = sc.hodge_laplacian(0)
            >>> (0,) in l0
            True
        """
        from algebrax.matrix.core import add, dot, transpose

        s_inst = Semiring.normalize(semiring)
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


class SimplicialComplex(SparseChainComplex):
    r"""Abstract simplicial complex with sparse boundary operators and homology.

    Algebraic Signature:
        $\cdots \xrightarrow{\partial_{k+1}} C_k \xrightarrow{\partial_k} C_{k-1} \xrightarrow{\partial_{k-1}} \cdots$

    Carrier:
        `dict[int, set[tuple[int, ...]]]` (Mapping dimension $k$ to ordered simplex vertex tuples).

    Operations:
        - Face Addition: Adds a simplex and closes downwards under sub-faces.
        - Boundary Maps: Generates oriented boundary matrices $D_k$.
        - Betti Numbers ($\beta_k$): $\beta_k = \dim(\ker \partial_k) - \mathrm{rank}(\partial_{k+1})$.

    Properties:
        Abstract simplicial closure: $\sigma \in K, \tau \subseteq \sigma \implies \tau \in K$.

    Applications:
        Topological Data Analysis (TDA), persistent homology, sensor coverage, shape analysis.
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
