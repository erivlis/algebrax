"""
Cell Poset Category Poset(K) of a Regular Cell or Simplicial Complex.

Formalizes the incidence poset category of a cell complex where objects are cells
and morphisms are face inclusion relations sigma <= tau, serving as the indexing
domain category for cellular sheaves (Justin Curry, 2014).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass

from algebrax.category.core import Category


@dataclass(frozen=True, order=True)
class Cell:
    r"""A cell $\sigma$ in a regular cell or simplicial complex $K$.

    Attributes:
        dimension: Topological dimension $k = \dim(\sigma) \ge 0$.
        id: Canonical tuple identifier (e.g., `(0,)` for vertex `0`, `(0, 1)` for edge `(0, 1)`).
    """

    dimension: int
    id: tuple[int, ...]


@dataclass(frozen=True)
class FaceInclusion:
    r"""Morphism $\sigma \trianglelefteq \tau$ in $\mathbf{Poset}(K)$ representing face inclusion.

    Attributes:
        source_cell: Lower-dimensional face $\sigma$.
        target_cell: Higher-dimensional coface $\tau$.
    """

    source_cell: Cell
    target_cell: Cell


class CellPosetCategory(Category[Cell, FaceInclusion]):
    r"""Poset category $\mathbf{Poset}(K)$ of a regular cell complex $K$.

    Algebraic Signature:
        $\mathbf{Poset}(K) = \langle \mathrm{Cells}(K), \trianglelefteq, \mathrm{id}, \circ \rangle$

    Carrier:
        - Objects: `Cell(dimension, id)`
        - Morphisms: `FaceInclusion(source_cell, target_cell)` for $\sigma \trianglelefteq \tau$

    Operations:
        - `id(x)`: Reflexive inclusion $\sigma \trianglelefteq \sigma$.
        - `compose(f, g)`: Transitive face inclusion
          $\sigma \trianglelefteq \tau \trianglelefteq \rho \implies \sigma \trianglelefteq \rho$.
        - `source(f)`: Face cell $\sigma$.
        - `target(f)`: Coface cell $\tau$.
        - `is_face(sigma, tau)`: Check whether $\sigma \trianglelefteq \tau$ holds in the transitive closure.
    """

    def __init__(
        self,
        cells: Iterable[Cell],
        faces: Iterable[tuple[Cell, Cell]] = (),
    ) -> None:
        self._cells: set[Cell] = set(cells)
        self._direct_faces: set[tuple[Cell, Cell]] = set()
        self._adj: dict[Cell, set[Cell]] = {c: set() for c in self._cells}

        for face, coface in faces:
            self._cells.add(face)
            self._cells.add(coface)
            self._adj.setdefault(face, set())
            self._adj.setdefault(coface, set())
            if face != coface:
                self._direct_faces.add((face, coface))
                self._adj[face].add(coface)

    @property
    def cells(self) -> set[Cell]:
        """Return all cells in the complex."""
        return set(self._cells)

    @property
    def direct_faces(self) -> set[tuple[Cell, Cell]]:
        """Return direct cover relations (face, coface)."""
        return set(self._direct_faces)

    def cells_of_dim(self, k: int) -> list[Cell]:
        """Return sorted list of cells of dimension `k`."""
        return sorted(c for c in self._cells if c.dimension == k)

    def is_face(self, sigma: Cell, tau: Cell) -> bool:
        r"""Check whether $\sigma \trianglelefteq \tau$ in the reflexive-transitive poset closure."""
        if sigma not in self._cells or tau not in self._cells:
            return False
        if sigma == tau:
            return True
        if sigma.dimension > tau.dimension:
            return False
        visited: set[Cell] = {sigma}
        queue: deque[Cell] = deque([sigma])
        while queue:
            curr = queue.popleft()
            for nxt in self._adj.get(curr, ()):
                if nxt == tau:
                    return True
                if nxt not in visited and nxt.dimension <= tau.dimension:
                    visited.add(nxt)
                    queue.append(nxt)
        return False

    def id(self, x: Cell) -> FaceInclusion:
        if x not in self._cells:
            raise ValueError(f'Cell {x} is not in Poset(K).')
        return FaceInclusion(x, x)

    def compose(self, f: FaceInclusion, g: FaceInclusion) -> FaceInclusion:
        if f.target_cell != g.source_cell:
            raise ValueError(f'Incompatible face composition: {f.target_cell} != {g.source_cell}')
        if not self.is_face(f.source_cell, f.target_cell) or not self.is_face(g.source_cell, g.target_cell):
            raise ValueError('Morphism is not a valid face inclusion in Poset(K).')
        return FaceInclusion(f.source_cell, g.target_cell)

    def source(self, f: FaceInclusion) -> Cell:
        return f.source_cell

    def target(self, f: FaceInclusion) -> Cell:
        return f.target_cell


__all__ = [
    'Cell',
    'CellPosetCategory',
    'FaceInclusion',
]
