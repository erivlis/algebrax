"""
Lawvere Metric Spaces & Semiring-Enriched Categories.

Implements F. William Lawvere's theorem (1973), "Metric spaces, generalized logic,
and closed categories": a generalized metric space (X, d) is a category enriched
over the tropical cost semiring <[0, inf], min, +, inf, 0>.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from algebrax.category.matrix import MatrixCategory
from algebrax.matrix.core import add, dot
from algebrax.semiring.optimization import TropicalSemiring
from algebrax.typing import SparseMatrix

K = TypeVar('K')


class LawvereMetricCategory(MatrixCategory[K, float], Generic[K]):
    r"""A Lawvere Metric Space $(X, d)$ realized as a category enriched over `TropicalSemiring`.

    Algebraic Signature:
        $\mathcal{V} = \langle [0, \infty], \ge, +, \infty, 0 \rangle \quad (\text{Tropical Cost Semiring})$

    Enriched Categorical Dictionary:
        - **Objects**: Points / vertices $x \in X$.
        - **Hom-Object $\mathcal{C}(x, y)$**: Directed distance $d(x, y) \in [0, \infty]$ (missing key = $\infty$).
        - **Enriched Identity**: $0 \ge d(x, x) \implies d(x, x) = 0.0$.
        - **Enriched Composition**: Triangle inequality $d(x, y) + d(y, z) \ge d(x, z)$, realized via
          min-plus tropical matrix multiplication $(f \odot_{\mathrm{trop}} g)_{xz} = \min_y (f_{xy} + g_{yz})$.
    """

    def __init__(self, distance_matrix: SparseMatrix[K, float] | None = None) -> None:
        super().__init__(TropicalSemiring())
        self._d: SparseMatrix[K, float] = distance_matrix if distance_matrix is not None else {}

    @property
    def distance_matrix(self) -> SparseMatrix[K, float]:
        """The underlying sparse directed distance matrix."""
        return self._d

    def objects(self) -> frozenset[K]:
        """Return all points present in the distance matrix."""
        pts: set[K] = set(self._d.keys())
        for row in self._d.values():
            pts.update(row.keys())
        return frozenset(pts)

    def distance(self, x: K, y: K) -> float:
        r"""Return the enriched hom-value $d(x, y) \in [0, \infty]$ (0.0 on diagonal, $\infty$ if disconnected)."""
        row = self._d.get(x)
        if row is not None and y in row:
            return float(row[y])
        if x == y:
            return 0.0
        return float('inf')

    def compose_paths(
        self,
        f: SparseMatrix[K, float],
        g: SparseMatrix[K, float],
    ) -> SparseMatrix[K, float]:
        r"""Compose two distance matrices via min-plus tropical matrix multiplication."""
        return dot(f, g, semiring=self._semiring)

    def metric_closure(self, max_steps: int | None = None) -> SparseMatrix[K, float]:
        r"""Compute the Kleene star metric closure $D^* = \bigoplus_{k=0}^{N-1} D^{\otimes k}$ over `TropicalSemiring`.

        Enforces the enriched Lawvere identity ($d(x, x) \le 0$) and triangle inequality
        ($d(x, z) \le d(x, y) + d(y, z)$) across all multi-hop paths.
        """
        pts = self.objects()
        if not pts:
            return {}
        n = len(pts)
        steps = (n - 1) if max_steps is None else max(0, max_steps)

        # Reflexive closure: I (+) D in TropicalSemiring (entrywise min with 0 on diagonal)
        ident = self.id(pts)
        curr = add(ident, self._d, semiring=self._semiring)

        # Repeated squaring / relaxation in TropicalSemiring
        step_count = 1
        while step_count < steps:
            curr = dot(curr, curr, semiring=self._semiring)
            step_count *= 2
        return curr

    def satisfies_triangle_inequality(
        self,
        points: Iterable[K] | None = None,
        tol: float = 1e-9,
    ) -> bool:
        r"""Verify whether $d(x, x) = 0$ and $d(x, z) \le d(x, y) + d(y, z)$ hold for all $x, y, z$."""
        pts = list(points) if points is not None else list(self.objects())
        for x in pts:
            if abs(self.distance(x, x)) > tol:
                return False
        for x in pts:
            for y in pts:
                d_xy = self.distance(x, y)
                if d_xy == float('inf'):
                    continue
                for z in pts:
                    d_yz = self.distance(y, z)
                    if d_yz == float('inf'):
                        continue
                    if self.distance(x, z) > d_xy + d_yz + tol:
                        return False
        return True


__all__ = [
    'LawvereMetricCategory',
]
