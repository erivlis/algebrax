"""
Discrete Fiber Bundles, Gauge Connections, Parallel Transport, Holonomy & Connection Laplacians.

Formalizes discrete vector bundles and orthogonal gauge connections over cell complexes,
bridging Lie groups, cellular sheaves (EP-0202), and Discrete Exterior Calculus (EP-0160).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Protocol, TypeVar, runtime_checkable

from algebrax.matrix.core import dot, mat_vec, transpose
from algebrax.semiring import StandardSemiring
from algebrax.topology.sheaf import CellularSheaf, StalkCoord
from algebrax.typing import SparseMatrix, SparseVector

G = TypeVar('G')

__all__ = [
    'DiscreteConnection',
    'DiscreteOrthogonalConnection',
    'apply_gauge_transformation',
    'build_connection_laplacian',
    'compute_face_holonomy',
    'covariant_exterior_derivative',
    'is_flat_bundle',
]


@runtime_checkable
class DiscreteConnection(Protocol[G]):
    r"""A discrete connection (gauge field) on a 1-skeleton $K_1$.

    Assigns to each oriented edge $(u, v)$ a parallel transport operator
    $\rho(u, v) \in G \subseteq \mathrm{GL}(d)$ satisfying $\rho(v, u) = \rho(u, v)^{-1}$.
    """

    @property
    def fiber_dim(self) -> int:
        r"""Dimension $d$ of the fiber vector space $\mathbb{R}^d$."""
        ...

    def transport(self, u: Any, v: Any) -> SparseMatrix[int, float]:
        r"""Parallel transport matrix $\rho(u, v): F_u \to F_v$."""
        ...

    def transport_path(self, path: Sequence[Any]) -> SparseMatrix[int, float]:
        r"""Compute parallel transport along a path $\gamma = (v_0, v_1, \dots, v_k)$:
        $$\rho(\gamma) = \rho(v_{k-1}, v_k) \cdots \rho(v_0, v_1)$$
        """
        ...


class DiscreteOrthogonalConnection(DiscreteConnection[SparseMatrix[int, float]]):
    r"""Discrete vector bundle connection with orthogonal structure group $O(d)$ or $SO(d)$.

    Algebraic Signature:
        $\nabla = \left(\{F_v \cong \mathbb{R}^d\}_{v \in V},
        \{\rho(u, v) \in O(d)\}_{(u, v) \in E}\right)$

    Properties:
        - Connection Inversion: $\rho(v, u) = \rho(u, v)^{-1} = \rho(u, v)^T$.
        - Sheaf Specialization: Canonically embeds into a `CellularSheaf` with
          $\rho_{u \trianglelefteq e} = \rho(u, v)$ and $\rho_{v \trianglelefteq e} = I_d$.
    """

    def __init__(self, fiber_dim: int) -> None:
        if fiber_dim <= 0:
            raise ValueError(f'Fiber dimension must be positive, got {fiber_dim}.')
        self._fiber_dim = fiber_dim
        self._edges: dict[tuple[Any, Any], SparseMatrix[int, float]] = {}
        self._vertices: set[Any] = set()
        self._semiring = StandardSemiring(float)

    @property
    def fiber_dim(self) -> int:
        return self._fiber_dim

    @property
    def vertices(self) -> set[Any]:
        """Return the set of vertices incident to registered connection edges."""
        return set(self._vertices)

    @property
    def edges(self) -> set[tuple[Any, Any]]:
        """Return all oriented edges with registered transport matrices."""
        return set(self._edges.keys())

    def set_transport(self, u: Any, v: Any, matrix: SparseMatrix[int, float]) -> None:
        r"""Set parallel transport $\rho(u, v)$ and automatically bind $\rho(v, u) = \rho(u, v)^T$."""
        if u == v:
            raise ValueError(f'Self-loop connection edges are not supported: ({u}, {v}).')
        clean_mat: SparseMatrix[int, float] = {
            int(r): {int(c): float(val) for c, val in row.items() if abs(float(val)) > 1e-15}
            for r, row in matrix.items()
        }
        clean_mat = {r: row for r, row in clean_mat.items() if row}
        self._vertices.add(u)
        self._vertices.add(v)
        self._edges[(u, v)] = clean_mat
        self._edges[(v, u)] = transpose(clean_mat)

    def transport(self, u: Any, v: Any) -> SparseMatrix[int, float]:
        if u == v and u in self._vertices:
            return {i: {i: 1.0} for i in range(self._fiber_dim)}
        if (u, v) not in self._edges:
            raise KeyError(f'No connection defined on edge ({u}, {v})')
        return self._edges[(u, v)]

    def transport_path(self, path: Sequence[Any]) -> SparseMatrix[int, float]:
        if len(path) < 2:
            return {i: {i: 1.0} for i in range(self._fiber_dim)}

        result = self.transport(path[0], path[1])
        for i in range(1, len(path) - 1):
            next_step = self.transport(path[i], path[i + 1])
            result = dot(next_step, result, semiring=self._semiring)
        return result

    def to_sheaf(self) -> CellularSheaf[Any]:
        r"""Convert this orthogonal connection into a `CellularSheaf` (and `FunctorialSheaf`).

        For each canonical edge $e = (u, v)$ with $u < v$, sets $\rho_{u \trianglelefteq e} = \rho(u, v)$
        and $\rho_{v \trianglelefteq e} = I_d$, so $(\delta x)_e = x_v - \rho(u, v) x_u$ and
        $L_{\mathcal{F}} = L_\nabla$.
        """
        sheaf: CellularSheaf[Any] = CellularSheaf()
        for v in self._vertices:
            sheaf.add_vertex(v, dim=self._fiber_dim)

        ident = {i: {i: 1.0} for i in range(self._fiber_dim)}
        seen_undirected: set[frozenset[Any]] = set()
        for u, v in sorted(self._edges.keys(), key=lambda pair: (str(pair[0]), str(pair[1]))):
            undir = frozenset((u, v))
            if undir in seen_undirected:
                continue
            seen_undirected.add(undir)
            sheaf.add_edge(u, v, dim=self._fiber_dim, rho_u=self._edges[(u, v)], rho_v=ident)

        return sheaf


def compute_face_holonomy(
    connection: DiscreteConnection[Any],
    face_boundary_vertices: Sequence[Any],
) -> SparseMatrix[int, float]:
    r"""Compute the holonomy (Wilson loop) around a closed 2-face boundary $(v_0, v_1, \dots, v_{k-1})$:
    $$\operatorname{Hol}(f) = \rho(v_{k-1}, v_0) \cdots \rho(v_1, v_2) \rho(v_0, v_1)$$
    """
    if not face_boundary_vertices:
        return {i: {i: 1.0} for i in range(connection.fiber_dim)}
    cycle = [*face_boundary_vertices, face_boundary_vertices[0]]
    return connection.transport_path(cycle)


def is_flat_bundle(
    connection: DiscreteConnection[Any],
    faces: Iterable[Sequence[Any]],
    tol: float = 1e-9,
) -> bool:
    r"""Test if the discrete bundle is flat (zero curvature on all faces: $\operatorname{Hol}(f) = I_d$)."""
    dim = connection.fiber_dim
    for f in faces:
        hol = compute_face_holonomy(connection, f)
        for i in range(dim):
            for j in range(dim):
                expected = 1.0 if i == j else 0.0
                actual = hol.get(i, {}).get(j, 0.0)
                if abs(actual - expected) > tol:
                    return False
    return True


def build_connection_laplacian(
    connection: DiscreteConnection[Any],
    adjacency: Mapping[Any, Iterable[Any]],
) -> SparseMatrix[StalkCoord[Any], float]:
    r"""Construct the sparse block Connection Laplacian $L_\nabla = D \otimes I_d - A_\rho$.

    For each vertex $u$ and incident neighbor $v \sim u$:
    $$(L_\nabla x)(u) = \sum_{v \sim u} \left(x(u) - \rho(v, u) x(v)\right)$$
    """
    d = connection.fiber_dim
    laplacian: dict[StalkCoord[Any], dict[StalkCoord[Any], float]] = {}

    for u, raw_neighbors in adjacency.items():
        neighbors = [v for v in raw_neighbors if v != u]
        degree = float(len(neighbors))
        if degree > 0.0:
            for i in range(d):
                key_u: StalkCoord[Any] = (u, i)
                laplacian.setdefault(key_u, {})[key_u] = degree

        for v in neighbors:
            rho_vu = connection.transport(v, u)
            for i, row in rho_vu.items():
                key_u = (u, int(i))
                target_row = laplacian.setdefault(key_u, {})
                for j, val in row.items():
                    f_val = float(val)
                    if abs(f_val) > 1e-15:
                        key_v: StalkCoord[Any] = (v, int(j))
                        target_row[key_v] = target_row.get(key_v, 0.0) - f_val

    return {r: row for r, row in laplacian.items() if row}


def covariant_exterior_derivative(
    connection: DiscreteConnection[Any],
    section: SparseVector[StalkCoord[Any], float],
    oriented_edges: Iterable[tuple[Any, Any]],
) -> dict[tuple[tuple[Any, Any], int], float]:
    r"""Evaluate the covariant exterior derivative $d_\nabla: \Omega^0(K; E) \to \Omega^1(K; E)$ on a 0-form section:
    $$(d_\nabla x)(u, v) = x(v) - \rho(u, v) x(u)$$
    """
    d = connection.fiber_dim
    out: dict[tuple[tuple[Any, Any], int], float] = {}

    for u, v in oriented_edges:
        x_u = {i: section[(u, i)] for i in range(d) if (u, i) in section}
        x_v = {i: section[(v, i)] for i in range(d) if (v, i) in section}
        transported_u = mat_vec(connection.transport(u, v), x_u) if x_u else {}

        for j in range(d):
            diff = float(x_v.get(j, 0.0)) - float(transported_u.get(j, 0.0))
            if abs(diff) > 1e-15:
                out[((u, v), j)] = diff

    return out


def apply_gauge_transformation(
    connection: DiscreteOrthogonalConnection,
    gauge_transform: Mapping[Any, SparseMatrix[int, float]],
) -> DiscreteOrthogonalConnection:
    r"""Apply local vertex gauge transformations $g_u \in O(d)$ to `connection`:
    $$\rho'(u, v) = g_v \, \rho(u, v) \, g_u^T$$
    """
    semiring = StandardSemiring(float)
    d = connection.fiber_dim
    ident = {i: {i: 1.0} for i in range(d)}
    transformed = DiscreteOrthogonalConnection(fiber_dim=d)

    seen_undirected: set[frozenset[Any]] = set()
    for u, v in connection.edges:
        undir = frozenset((u, v))
        if undir in seen_undirected:
            continue
        seen_undirected.add(undir)

        g_u = gauge_transform.get(u, ident)
        g_v = gauge_transform.get(v, ident)
        rho_uv = connection.transport(u, v)
        rho_prime = dot(g_v, dot(rho_uv, transpose(g_u), semiring=semiring), semiring=semiring)
        transformed.set_transport(u, v, rho_prime)

    return transformed
