"""Cellular sheaves, sheaf cohomology (H^0 and H^1), network Laplacians, and harmonic extension."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeAlias

from algebrax.topology._core import _matrix_rank
from algebrax.typing import K, SparseMatrix, SparseVector

__all__ = [
    'CellularSheaf',
    'EdgeStalkCoord',
    'RestrictionMap',
    'StalkCoord',
    'sheaf_diffusion',
    'sheaf_harmonic_extension',
    'sheaf_laplacian',
]

StalkCoord: TypeAlias = tuple[K, int]
EdgeStalkCoord: TypeAlias = tuple[tuple[K, K], int]
RestrictionMap: TypeAlias = Mapping[int, Mapping[int, float]] | Sequence[Sequence[float]] | float | int


def _normalize_restriction_row(row: Any) -> dict[int, float]:
    if isinstance(row, str):
        raise TypeError(f'Unsupported restriction row type: {type(row)}')
    if isinstance(row, Mapping):
        return {int(c): float(v) for c, v in row.items() if abs(float(v)) > 1e-15}
    if isinstance(row, Sequence):
        return {c: float(v) for c, v in enumerate(row) if abs(float(v)) > 1e-15}
    v = float(row)
    return {0: v} if abs(v) > 1e-15 else {}


def _normalize_restriction(
    rho: RestrictionMap,
) -> dict[int, dict[int, float]]:
    if isinstance(rho, str):
        raise TypeError(f'Unsupported restriction map type: {type(rho)}')
    if isinstance(rho, (int, float)):
        val = float(rho)
        return {0: {0: val}} if abs(val) > 1e-15 else {}
    if isinstance(rho, (Mapping, Sequence)):
        items = rho.items() if isinstance(rho, Mapping) else enumerate(rho)
        out: dict[int, dict[int, float]] = {}
        for r, row in items:
            if row_dict := _normalize_restriction_row(row):
                out[int(r)] = row_dict
        return out
    raise TypeError(f'Unsupported restriction map type: {type(rho)}')


def _canonical_edge(u: K, v: K) -> tuple[tuple[K, K], bool]:
    try:
        is_greater = u > v  # type: ignore[operator]
    except TypeError:
        is_greater = str(u) > str(v)

    if is_greater:
        return (v, u), True
    return (u, v), False


class CellularSheaf(Generic[K]):
    r"""Cellular sheaf $\mathcal{F}$ over a 1-dimensional cell complex (graph) $G = (V, E)$.

    Algebraic Signature:
        $\mathcal{F} = \left(\\{\mathcal{F}(v)\\}_{v \in V}, \\{\mathcal{F}(e)\\}_{e \in E},
        \\{\rho_{v \trianglelefteq e}: \mathcal{F}(v) \to \mathcal{F}(e)\\}\right)$

    Carrier:
        - `vertex_stalks: dict[K, int]` mapping vertices to stalk vector dimensions $d_v$.
        - `edge_stalks: dict[tuple[K, K], int]` mapping canonical edges $(u, v)$ with $u < v$ to dimensions $d_e$.
        - `restrictions: dict[tuple[K, tuple[K, K]], dict[int, dict[int, float]]]` mapping $(v, e)$ incidence pairs
          to linear restriction maps $\rho_{v \trianglelefteq e}: \mathbb{R}^{d_v} \to \mathbb{R}^{d_e}$.

    Operations:
        - Stalk & Edge Registration: `add_vertex(v, dim)` and `add_edge(u, v, dim, rho_u, rho_v)`.
        - Constant Sheaf Construction: `CellularSheaf.constant(graph, stalk_dim)`.
        - Coboundary Assembly ($\delta_{\mathcal{F}}$): Local difference $(\delta_{\mathcal{F}} x)_{e=(u, v)} =
          \rho_{v \trianglelefteq e} x_v - \rho_{u \trianglelefteq e} x_u$.
        - Sheaf Laplacian ($L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$): Positive semi-definite
          block-structured operator over product stalk keys `(v, i)`.
        - Sheaf Cohomology: Global sections $\dim H^0(G; \mathcal{F}) = \dim \ker \delta_{\mathcal{F}}$ and
          obstructions $\dim H^1(G; \mathcal{F}) = \dim \operatorname{coker} \delta_{\mathcal{F}}$.
        - Dirichlet Energy: $E_{\mathcal{F}}(x) = \frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2 =
          \frac{1}{2} \langle x, L_{\mathcal{F}} x \rangle$.

    Properties:
        - Self-Adjoint Hodge Structure: $L_{\mathcal{F}}$ is symmetric positive semi-definite.
        - Orientation Invariance: $L_{\mathcal{F}}$ and $E_{\mathcal{F}}(x)$ are invariant under
          edge orientation choice.
        - Sheaf Euler-Poincaré Identity:
          $\chi(G; \mathcal{F}) = \sum_v d_v - \sum_e d_e = \dim H^0(G; \mathcal{F}) - \dim H^1(G; \mathcal{F})$.

    Applications:
        - Multi-agent consensus under local coordinate transformations and orthogonal connection graphs.
        - Heterogeneous sensor calibration, distributed state estimation, and opinion dynamics with polarization.
        - Boundary-value harmonic extension and Dirichlet problem solving over cellular networks.
    """

    def __init__(
        self,
        vertex_stalks: Mapping[K, int] | None = None,
        edge_stalks: Mapping[tuple[K, K], int] | None = None,
        restrictions: Mapping[tuple[K, tuple[K, K]], RestrictionMap] | None = None,
    ) -> None:
        self.vertex_stalks: dict[K, int] = dict(vertex_stalks) if vertex_stalks else {}
        self.edge_stalks: dict[tuple[K, K], int] = {}
        self.restrictions: dict[tuple[K, tuple[K, K]], dict[int, dict[int, float]]] = {}

        if edge_stalks and restrictions:
            for e, dim in edge_stalks.items():
                u, v = e
                rho_u = restrictions.get((u, e), {})
                rho_v = restrictions.get((v, e), {})
                self.add_edge(u, v, dim=dim, rho_u=rho_u, rho_v=rho_v)

    def add_vertex(self, vertex: K, dim: int = 1) -> None:
        """Register a vertex and its vector stalk dimension.

        Args:
            vertex: Vertex identifier.
            dim: Dimension of the stalk vector space (must be positive).
        """
        if dim <= 0:
            raise ValueError(f'Stalk dimension must be positive, got {dim}.')
        self.vertex_stalks[vertex] = dim

    def add_edge(
        self,
        u: K,
        v: K,
        dim: int,
        rho_u: RestrictionMap,
        rho_v: RestrictionMap,
    ) -> None:
        """Add an edge with edge stalk dimension and restriction maps from incident vertices.

        Args:
            u: Source vertex identifier.
            v: Target vertex identifier.
            dim: Edge stalk dimension (must be positive).
            rho_u: Linear restriction map from stalk at u to edge stalk.
            rho_v: Linear restriction map from stalk at v to edge stalk.
        """
        if dim <= 0:
            raise ValueError(f'Edge stalk dimension must be positive, got {dim}.')

        norm_rho_u = _normalize_restriction(rho_u)
        norm_rho_v = _normalize_restriction(rho_v)

        if u not in self.vertex_stalks:
            max_col_u = max((c for r in norm_rho_u.values() for c in r), default=-1)
            self.vertex_stalks[u] = max(max_col_u + 1, dim)
        if v not in self.vertex_stalks:
            max_col_v = max((c for r in norm_rho_v.values() for c in r), default=-1)
            self.vertex_stalks[v] = max(max_col_v + 1, dim)

        canon_e, inverted = _canonical_edge(u, v)
        u_c, v_c = canon_e
        self.edge_stalks[canon_e] = dim

        if not inverted:
            self.restrictions[(u_c, canon_e)] = norm_rho_u
            self.restrictions[(v_c, canon_e)] = norm_rho_v
        else:
            self.restrictions[(u_c, canon_e)] = norm_rho_v
            self.restrictions[(v_c, canon_e)] = norm_rho_u

    @classmethod
    def constant(
        cls,
        graph: SparseMatrix[K, float],
        stalk_dim: int = 1,
    ) -> CellularSheaf[K]:
        """Construct the constant sheaf (or weighted scalar sheaf) of dimension `stalk_dim` over `graph`.

        Args:
            graph: Sparse adjacency matrix representing weighted edges u -> {v: weight}.
            stalk_dim: Dimension of each vector stalk (default 1).

        Returns:
            A new CellularSheaf instance representing the constant sheaf.
        """
        from algebrax.matrix.core import _symmetrize_adjacency

        if stalk_dim <= 0:
            raise ValueError(f'Stalk dimension must be positive, got {stalk_dim}.')

        nodes: set[K] = set(graph.keys())
        for row in graph.values():
            nodes.update(row.keys())

        sheaf = cls()
        for node in nodes:
            sheaf.add_vertex(node, dim=stalk_dim)

        adj = _symmetrize_adjacency(graph, nodes, symmetrize=True)
        seen_edges: set[tuple[K, K]] = set()

        for u, neighbors in adj.items():
            for v, weight in neighbors.items():
                if u == v or weight <= 0:
                    continue
                canon_e, _ = _canonical_edge(u, v)
                if canon_e in seen_edges:
                    continue
                seen_edges.add(canon_e)

                sqrt_w = math.sqrt(weight)
                rho = {i: {i: sqrt_w} for i in range(stalk_dim)}
                sheaf.add_edge(canon_e[0], canon_e[1], dim=stalk_dim, rho_u=rho, rho_v=rho)

        return sheaf

    def coboundary_matrix(self) -> SparseMatrix[EdgeStalkCoord, float]:
        r"""Assemble the sparse sheaf coboundary operator $\delta_{\mathcal{F}}: C^0 \to C^1$.

        Returns:
            Sparse matrix indexed by edge coordinates ((u, v), j) and vertex coordinates (v, i).
        """
        coboundary: dict[EdgeStalkCoord, dict[StalkCoord, float]] = {}

        for canon_e, dim_e in self.edge_stalks.items():
            u_c, v_c = canon_e
            rho_u = self.restrictions.get((u_c, canon_e), {})
            rho_v = self.restrictions.get((v_c, canon_e), {})

            for j in range(dim_e):
                row_key: EdgeStalkCoord = (canon_e, j)
                row: dict[StalkCoord, float] = {}

                for i, val in rho_v.get(j, {}).items():
                    col_key: StalkCoord = (v_c, i)
                    row[col_key] = row.get(col_key, 0.0) + float(val)

                for i, val in rho_u.get(j, {}).items():
                    col_key = (u_c, i)
                    row[col_key] = row.get(col_key, 0.0) - float(val)

                filtered = {c: v for c, v in row.items() if abs(v) > 1e-15}
                if filtered:
                    coboundary[row_key] = filtered

        return coboundary

    def laplacian_matrix(self) -> SparseMatrix[StalkCoord, float]:
        r"""Assemble symmetric positive semi-definite Sheaf Laplacian $L_{\mathcal{F}} = \delta^T \delta$.

        Returns:
            Sparse matrix indexed by vertex stalk coordinates (v, i).
        """
        from algebrax.matrix.core import dot, transpose

        delta = self.coboundary_matrix()
        if not delta:
            return {}
        delta_t = transpose(delta)
        return dot(delta_t, delta)

    def dirichlet_energy(self, section: SparseVector[StalkCoord, float]) -> float:
        r"""Compute total sheaf disagreement Dirichlet energy $\frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2$.

        Args:
            section: 0-cochain vector mapping `(vertex, dim_idx)` to float values.

        Returns:
            Non-negative scalar Dirichlet energy.
        """
        from algebrax.matrix.core import inner, mat_vec

        delta = self.coboundary_matrix()
        if not delta or not section:
            return 0.0
        dx = mat_vec(delta, section)
        return 0.5 * float(inner(dx, dx))

    def global_sections_dimension(self, tol: float = 1e-9) -> int:
        r"""Compute the space of global sections dimension $\dim H^0(G; \mathcal{F}) = \dim \ker L_{\mathcal{F}}$."""
        total_dim = sum(self.vertex_stalks.values())
        if total_dim == 0:
            return 0
        delta = self.coboundary_matrix()
        if not delta:
            return total_dim
        rank_delta = _matrix_rank(delta)
        return max(total_dim - rank_delta, 0)

    def first_cohomology_dimension(self, tol: float = 1e-9) -> int:
        r"""Compute the 1st sheaf cohomology dimension $\dim H^1(G; \mathcal{F})$.

        Defined as $\dim \operatorname{coker} \delta_{\mathcal{F}}$.
        Measures the dimension of the space of edge-stalk obstructions that cannot be realized
        as coboundaries of 0-cochains.
        """
        total_edge_dim = sum(self.edge_stalks.values())
        if total_edge_dim == 0:
            return 0
        delta = self.coboundary_matrix()
        if not delta:
            return total_edge_dim
        rank_delta = _matrix_rank(delta)
        return max(total_edge_dim - rank_delta, 0)

    def euler_characteristic(self) -> int:
        r"""Compute the sheaf Euler characteristic $\chi(G; \mathcal{F}) = \sum_{v \in V} d_v - \sum_{e \in E} d_e$."""
        return sum(self.vertex_stalks.values()) - sum(self.edge_stalks.values())


def sheaf_laplacian(sheaf: CellularSheaf) -> SparseMatrix[StalkCoord, float]:
    r"""Return the sparse Sheaf Laplacian matrix $L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$."""
    return sheaf.laplacian_matrix()


def sheaf_diffusion(
    sheaf: CellularSheaf,
    initial_state: SparseVector[StalkCoord, float],
    steps: int = 20,
    tau: float = 0.1,
) -> dict[StalkCoord, float]:
    r"""Simulate discrete-time sheaf heat diffusion $x^{(t+1)} = (I - \tau L_{\mathcal{F}}) x^{(t)}$."""
    from algebrax.matrix.core import mat_vec, vec_axpy, vec_clean

    if not initial_state or steps <= 0:
        return dict(initial_state)

    lap = sheaf.laplacian_matrix()
    x = dict(initial_state)

    for _ in range(steps):
        lx = mat_vec(lap, x)
        x = vec_axpy(-tau, lx, x, tol=1e-15)  # type: ignore[assignment]

    return vec_clean(x, tol=1e-12)  # type: ignore[return-value]


def sheaf_harmonic_extension(
    sheaf: CellularSheaf[K],
    boundary_values: SparseVector[StalkCoord, float],
    boundary_vertices: set[K],
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> dict[StalkCoord, float]:
    r"""Compute harmonic 0-cochain minimizing Dirichlet energy clamped on boundary."""
    from algebrax.matrix.core import cg_solve, mat_vec

    all_coords: set[StalkCoord] = {(u, i) for u, d in sheaf.vertex_stalks.items() for i in range(d)}
    coord_b: set[StalkCoord] = {c for c in all_coords if c[0] in boundary_vertices}
    coord_u: set[StalkCoord] = all_coords - coord_b

    if not coord_u:
        return dict(boundary_values)

    x_b: dict[StalkCoord, float] = {c: float(boundary_values.get(c, 0.0)) for c in coord_b if c in boundary_values}

    if not coord_b:
        return dict.fromkeys(coord_u, 0.0)

    lap = sheaf.laplacian_matrix()
    if not lap:
        res = dict(x_b)
        res.update(dict.fromkeys(coord_u, 0.0))
        return res

    lap_uu: dict[StalkCoord, dict[StalkCoord, float]] = {}
    for r in coord_u:
        row = lap.get(r, {})
        u_row = {c: val for c, val in row.items() if c in coord_u}
        if u_row:
            lap_uu[r] = u_row

    lx_b = mat_vec(lap, x_b)
    rhs_u = {r: -val for r, val in lx_b.items() if r in coord_u and abs(val) > 1e-15}

    x_u = cg_solve(lap_uu, rhs_u, tol=tol, max_iter=max_iter, project_nullspace=False) if rhs_u else {}

    solution = dict(x_b)
    solution.update(x_u)
    return solution
