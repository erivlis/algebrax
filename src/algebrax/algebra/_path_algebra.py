r"""
Path Algebras $K Q$ of Finite Quivers.

Implements the associative unital path algebra $KQ$ of a quiver $Q = (V_Q, E_Q, s, t)$ over an
unboxed sparse path basis `dict[tuple[V, tuple[E, ...]], T]`:
- Length-0 stationary paths `(v, ())` form a complete set of primitive orthogonal idempotents
  $e_v$ satisfying $e_u e_v = \delta_{uv} e_v$ and $\sum_{v \in V_Q} e_v = \mathbf{1}_{KQ}$.
- Directed paths `(start_v, (e_1, ..., e_k))` multiply by left-to-right path concatenation
  $p \cdot q = pq$ when $\operatorname{target}(p) = \operatorname{source}(q)$ and $0$ otherwise.
- Evaluating $KQ$ on any `QuiverRepresentation` yields the canonical module action establishing
  the categorical equivalence $\mathbf{Rep}(Q) \simeq KQ\text{-}\mathbf{Mod}$.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from algebrax.algebra._monoid_algebra import QuotientMonoidAlgebra
from algebrax.algebra._semiring import Semiring
from algebrax.typing import SparseMatrix, SparseVector

if TYPE_CHECKING:
    from algebrax.rep.quiver import Quiver, QuiverRepresentation

V = TypeVar('V', bound=Hashable)
E = TypeVar('E', bound=Hashable)
T = TypeVar('T', bound=float | int | complex)

__all__ = [
    'PathAlgebra',
    'path_algebra',
]


def _path_target(quiver: Quiver[V, E], path_key: tuple[V, tuple[E, ...]]) -> V:
    start_v, edges = path_key
    if not edges:
        return start_v
    return quiver.target[edges[-1]]


class PathAlgebra(QuotientMonoidAlgebra[tuple[V, tuple[E, ...]], T], Generic[V, E, T]):
    r"""Associative path algebra $K Q$ of a finite quiver $Q = (V_Q, E_Q, s, t)$.

    Carrier:
        Unboxed sparse dictionaries `dict[tuple[V, tuple[E, ...]], T]` mapping canonical path keys
        `(start_vertex, (e_1, ..., e_k))` to scalar coefficients in $K$.

    Multiplication:
        For basis paths $p = (u_1, \gamma_1)$ and $q = (u_2, \gamma_2)$:
        $$p \cdot q = \begin{cases}
            (u_1, \gamma_1 \mathbin{\Vert} \gamma_2) & \text{if } \operatorname{target}(p) = u_2, \\
            0 & \text{otherwise.}
        \end{cases}$$
    Unit:
        $$\mathbf{1}_{KQ} = \sum_{v \in V_Q} e_v = \{(v, ()): 1_K \mid v \in V_Q\}.$$
    """

    def __init__(
        self,
        quiver: Quiver[V, E],
        coeff_semiring: Semiring[T] | None = None,
        max_path_length: int | None = None,
    ) -> None:
        if coeff_semiring is None:
            from algebrax.semiring.arithmetic import StandardSemiring

            coeff_semiring = StandardSemiring(float)  # type: ignore[assignment]
        if max_path_length is not None and max_path_length < 0:
            raise ValueError(f'max_path_length must be >= 0, got {max_path_length}.')

        self.quiver = quiver
        self.max_path_length = max_path_length

        def _concat_key(
            left: tuple[V, tuple[E, ...]],
            right: tuple[V, tuple[E, ...]],
        ) -> Any:
            if _path_target(quiver, left) != right[0]:
                return None
            combined_edges = left[1] + right[1]
            if max_path_length is not None and len(combined_edges) > max_path_length:
                return None
            return (left[0], combined_edges)

        def _quotient_fn(raw_key: Any, raw_coeff: T) -> Iterable[tuple[tuple[V, tuple[E, ...]], T]]:
            if raw_key is None or raw_coeff == coeff_semiring.zero:
                return ()
            return ((raw_key, raw_coeff),)

        zero_key: tuple[V, tuple[E, ...]] = (quiver.vertices[0], ()) if quiver.vertices else (None, ())  # type: ignore[assignment]
        super().__init__(
            coeff_semiring=coeff_semiring,
            key_op=_concat_key,
            zero_key=zero_key,
            quotient_fn=_quotient_fn,
        )

    @property
    def one(self) -> SparseVector[tuple[V, tuple[E, ...]], T]:
        r"""Multiplicative identity $\mathbf{1}_{KQ} = \sum_{v \in V_Q} e_v$."""
        unit = self.coeff_semiring.one
        return {(v, ()): unit for v in self.quiver.vertices}

    def vertex_idempotent(self, vertex: V) -> SparseVector[tuple[V, tuple[E, ...]], T]:
        r"""Return the length-0 primitive orthogonal idempotent $e_v = \{(v, ()): 1_K\}$."""
        if vertex not in self.quiver.vertices:
            raise KeyError(f'Vertex {vertex!r} not in quiver.')
        return {(vertex, ()): self.coeff_semiring.one}

    def arrow(self, edge: E) -> SparseVector[tuple[V, tuple[E, ...]], T]:
        r"""Return the length-1 path element for directed arrow `edge`."""
        if edge not in self.quiver.source:
            raise KeyError(f'Edge {edge!r} not in quiver.')
        if self.max_path_length is not None and self.max_path_length < 1:
            return {}
        return {(self.quiver.source[edge], (edge,)): self.coeff_semiring.one}

    def path_element(
        self,
        edges: Sequence[E],
        start_vertex: V | None = None,
    ) -> SparseVector[tuple[V, tuple[E, ...]], T]:
        r"""Construct a basis path element from a valid sequence of composable arrows."""
        edge_tuple = tuple(edges)
        if not edge_tuple:
            if start_vertex is None:
                raise ValueError('start_vertex must be provided for an empty (length-0) path.')
            return self.vertex_idempotent(start_vertex)

        if self.max_path_length is not None and len(edge_tuple) > self.max_path_length:
            return {}

        first = edge_tuple[0]
        if first not in self.quiver.source:
            raise KeyError(f'Edge {first!r} not in quiver.')
        origin = self.quiver.source[first]
        if start_vertex is not None and start_vertex != origin:
            raise ValueError(f'start_vertex {start_vertex!r} does not match source {origin!r} of {first!r}.')

        cur_target = self.quiver.target[first]
        for nxt in edge_tuple[1:]:
            if nxt not in self.quiver.source:
                raise KeyError(f'Edge {nxt!r} not in quiver.')
            if self.quiver.source[nxt] != cur_target:
                raise ValueError(
                    f'Non-composable path: target {cur_target!r} != source {self.quiver.source[nxt]!r} of {nxt!r}.'
                )
            cur_target = self.quiver.target[nxt]

        return {(origin, edge_tuple): self.coeff_semiring.one}

    def basis(self, max_length: int | None = None) -> list[tuple[V, tuple[E, ...]]]:
        """Return all basis path keys up to `max_length` (defaulting to `self.max_path_length`)."""
        limit = self.max_path_length if max_length is None else max_length
        return self.quiver.all_paths(max_length=limit)

    def evaluate_in_rep(
        self,
        element: SparseVector[tuple[V, tuple[E, ...]], T],
        rep: QuiverRepresentation[Any, V, E],
    ) -> SparseMatrix[int, complex | float]:
        r"""Evaluate a path algebra element as an endomorphism of $\bigoplus_{v \in V_Q} V_v$.

        Since multiplication in $KQ$ is left-to-right path concatenation ($p \cdot q$ follows $p$
        then $q$), a path $p = \alpha_1 \cdots \alpha_k$ from $u$ to $v$ acts as
        $M_{\alpha_k} \circ \cdots \circ M_{\alpha_1} : V_u \to V_v$ embedded into $\bigoplus_i V_i$,
        satisfying the right-module law $\Phi(p \cdot q) = \Phi(q)\,\Phi(p)$.
        """
        if rep.quiver != self.quiver:
            raise ValueError('Representation quiver does not match PathAlgebra quiver.')

        from algebrax.matrix.core import dot

        offsets: dict[V, int] = {}
        cursor = 0
        for v in self.quiver.vertices:
            offsets[v] = cursor
            cursor += rep.dimensions[v]

        acc: dict[int, dict[int, complex | float]] = {}
        for (start_v, edges), coeff in element.items():
            if coeff == self.coeff_semiring.zero:
                continue
            d_start = rep.dimensions[start_v]
            if d_start == 0:
                continue
            mat: dict[int, dict[int, Any]] = {i: {i: 1.0} for i in range(d_start)}
            end_v = start_v
            for e in edges:
                mat = dot(rep.edge_maps[e], mat)
                end_v = self.quiver.target[e]
            off_row = offsets[end_v]
            off_col = offsets[start_v]
            for r, row in mat.items():
                target_row = acc.setdefault(r + off_row, {})
                for c, val in row.items():
                    prod = coeff * val
                    prev = target_row.get(c + off_col, 0.0)
                    new_val = prev + prod
                    if abs(complex(new_val)) <= 1e-15:
                        target_row.pop(c + off_col, None)
                    else:
                        target_row[c + off_col] = new_val

        return {r: row for r, row in acc.items() if row}


def path_algebra(
    quiver: Quiver[V, E],
    coeff_semiring: Semiring[T] | None = None,
    max_path_length: int | None = None,
) -> PathAlgebra[V, E, T]:
    r"""Construct the associative unital path algebra $K Q$ of `quiver`."""
    return PathAlgebra(quiver=quiver, coeff_semiring=coeff_semiring, max_path_length=max_path_length)
