"""Cellular sheaves, sheaf cohomology (H^0 and H^1), network Laplacians, and harmonic extension."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeAlias, runtime_checkable

from algebrax.category.poset import Cell, CellPosetCategory
from algebrax.topology._core import _matrix_rank
from algebrax.typing import K, SparseMatrix, SparseVector

if TYPE_CHECKING:
    from algebrax.topology.homology import SimplicialComplex

__all__ = [
    'CellStalkCoord',
    'CellularSheaf',
    'ConstantSheaf',
    'EdgeStalkCoord',
    'FunctorialSheaf',
    'RestrictionMap',
    'StalkCoord',
    'build_sheaf_coboundary_matrix',
    'build_sheaf_laplacian',
    'sheaf_diffusion',
    'sheaf_harmonic_extension',
    'sheaf_laplacian',
]

StalkCoord: TypeAlias = tuple[K, int]
EdgeStalkCoord: TypeAlias = tuple[tuple[K, K], int]
CellStalkCoord: TypeAlias = tuple[Cell, int]
RestrictionMap: TypeAlias = Mapping[int, Mapping[int, float]] | Sequence[Sequence[float]] | float | int


@runtime_checkable
class FunctorialSheaf(Protocol):
    r"""A cellular sheaf $\mathcal{F}: \mathbf{Poset}(K)^{\mathrm{op}} \to \mathbf{Mat}(\mathbb{R})$.

    Maps:
        - Cell $\sigma \mapsto$ Stalk dimension $\mathbb{R}^{d_\sigma}$.
        - Face inclusion $\sigma \trianglelefteq \tau \mapsto$ Restriction matrix
          $\mathcal{E}_{\sigma \trianglelefteq \tau}: \mathbb{R}^{d_\sigma} \to \mathbb{R}^{d_\tau}$.
    """

    @property
    def poset_category(self) -> CellPosetCategory:
        r"""The underlying cell poset category $\mathbf{Poset}(K)$."""
        ...

    def stalk_dim(self, cell: Cell) -> int:
        r"""Dimension $d_\sigma$ of the vector stalk $\mathcal{F}(\sigma)$ at `cell`."""
        ...

    def restriction_map(self, face: Cell, coface: Cell) -> SparseMatrix[int, float]:
        r"""Restriction matrix $\mathcal{E}_{\mathrm{face} \trianglelefteq \mathrm{coface}}$."""
        ...


class ConstantSheaf(FunctorialSheaf):
    r"""The constant rank-1 sheaf $\underline{\mathbb{R}}$ over a regular cell or simplicial complex $K$.

    Algebraic Signature:
        $\underline{\mathbb{R}}(\sigma) = \mathbb{R}^1, \quad
        \mathcal{E}_{\sigma \trianglelefteq \tau} = \begin{bmatrix} [\sigma : \tau] \end{bmatrix}$

    Properties:
        - Stalk at every cell $\sigma \in K$ is $\mathbb{R}^1$.
        - Restriction map for oriented face $\sigma \trianglelefteq \tau$ is $[+1]$ or $[-1]$
          according to relative orientation $[\sigma : \tau]$.
        - Its degree-$k$ sheaf coboundary $\delta^k$ is canonically isomorphic to the
          Discrete Exterior Calculus (DEC) exterior derivative $\mathbf{d}_k = \partial_{k+1}^T$.
    """

    def __init__(
        self,
        complex_cells: Iterable[Cell],
        orientations: Mapping[tuple[Cell, Cell], int | float],
    ) -> None:
        self.cells: list[Cell] = sorted(set(complex_cells))
        self.orientations: dict[tuple[Cell, Cell], float] = {
            (f, c): float(s) for (f, c), s in orientations.items()
        }
        self._poset = CellPosetCategory(self.cells, self.orientations.keys())

    @classmethod
    def from_simplicial_complex(cls, sc: SimplicialComplex) -> ConstantSheaf:
        r"""Construct the constant rank-1 sheaf $\underline{\mathbb{R}}$ over a `SimplicialComplex`."""
        cells: list[Cell] = []
        orientations: dict[tuple[Cell, Cell], float] = {}

        for k, simplices in sc._simplices.items():
            for s in sorted(simplices):
                cells.append(Cell(dimension=k, id=s))

        for k, b_k in sc.boundary_matrices.items():
            for face_tuple, row in b_k.items():
                face_cell = Cell(dimension=k - 1, id=face_tuple)
                for coface_tuple, sign in row.items():
                    coface_cell = Cell(dimension=k, id=coface_tuple)
                    orientations[(face_cell, coface_cell)] = float(sign)

        return cls(cells, orientations)

    @property
    def poset_category(self) -> CellPosetCategory:
        return self._poset

    def stalk_dim(self, cell: Cell) -> int:
        if cell not in self._poset.cells:
            raise KeyError(f'Cell {cell} not found in ConstantSheaf.')
        return 1

    def restriction_map(self, face: Cell, coface: Cell) -> SparseMatrix[int, float]:
        if face == coface and face in self._poset.cells:
            return {0: {0: 1.0}}
        sign = self.orientations.get((face, coface))
        if sign is None or abs(sign) <= 1e-15:
            return {}
        return {0: {0: float(sign)}}


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


class CellularSheaf(FunctorialSheaf, Generic[K]):
    r"""Cellular sheaf $\mathcal{F}$ over a 1-dimensional cell complex (graph) $G = (V, E)$.

    Algebraic Signature:
        $\mathcal{F} = \left(\{\mathcal{F}(v)\}_{v \in V}, \{\mathcal{F}(e)\}_{e \in E},
        \{\rho_{v \trianglelefteq e}: \mathcal{F}(v) \to \mathcal{F}(e)\}\right)$

    Carrier:
        - `vertex_stalks: dict[K, int]` mapping vertices to stalk vector dimensions $d_v$.
        - `edge_stalks: dict[tuple[K, K], int]` mapping canonical edges $(u, v)$ with $u < v$ to dimensions $d_e$.
        - `restrictions: dict[tuple[K, tuple[K, K]], dict[int, dict[int, float]]]` mapping $(v, e)$ incidence pairs
          to linear restriction maps $\rho_{v \trianglelefteq e}: \mathbb{R}^{d_v} \to \mathbb{R}^{d_e}$.

    Operations:
        - Stalk & Edge Registration: `add_vertex(v, dim)` and `add_edge(u, v, dim, rho_u, rho_v)`.
        - Constant Sheaf Construction: `CellularSheaf.constant(graph, stalk_dim)`.
        - Functorial Interface: `poset_category`, `stalk_dim(cell)`, and `restriction_map(face, coface)`.
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

    @property
    def poset_category(self) -> CellPosetCategory:
        r"""Construct the underlying cell poset category $\mathbf{Poset}(G)$."""
        cells: list[Cell] = [Cell(dimension=0, id=(v,)) for v in self.vertex_stalks]  # type: ignore[arg-type]
        faces: list[tuple[Cell, Cell]] = []
        for u, v in self.edge_stalks:
            e_cell = Cell(dimension=1, id=(u, v))  # type: ignore[arg-type]
            u_cell = Cell(dimension=0, id=(u,))  # type: ignore[arg-type]
            v_cell = Cell(dimension=0, id=(v,))  # type: ignore[arg-type]
            cells.append(e_cell)
            faces.append((u_cell, e_cell))
            faces.append((v_cell, e_cell))
        return CellPosetCategory(cells, faces)

    def stalk_dim(self, cell: Cell) -> int:
        """Return the dimension of the vector stalk at `cell`."""
        if cell.dimension == 0 and len(cell.id) == 1:
            v = cell.id[0]
            if v in self.vertex_stalks:
                return self.vertex_stalks[v]  # type: ignore[index]
        elif cell.dimension == 1 and len(cell.id) == 2:
            e = (cell.id[0], cell.id[1])
            if e in self.edge_stalks:
                return self.edge_stalks[e]  # type: ignore[index]
        raise KeyError(f'Cell {cell} not found in CellularSheaf.')

    def restriction_map(self, face: Cell, coface: Cell) -> SparseMatrix[int, float]:
        r"""Return the signed restriction matrix $[\sigma : \tau] \rho_{\sigma \trianglelefteq \tau}$."""
        if face == coface:
            d = self.stalk_dim(face)
            return {i: {i: 1.0} for i in range(d)}
        if face.dimension == 0 and coface.dimension == 1 and len(face.id) == 1 and len(coface.id) == 2:
            v = face.id[0]
            e = (coface.id[0], coface.id[1])
            rho = self.restrictions.get((v, e), {})  # type: ignore[arg-type]
            if not rho:
                return {}
            # In canonical edge e = (u_c, v_c), orientation sign [u_c : e] = -1, [v_c : e] = +1
            sign = -1.0 if v == e[0] else 1.0
            return {r: {c: sign * val for c, val in row.items()} for r, row in rho.items()}
        return {}

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


def build_sheaf_coboundary_matrix(
    sheaf: FunctorialSheaf,
    k: int = 0,
) -> SparseMatrix[CellStalkCoord, float]:
    r"""Assemble the degree-$k$ sheaf coboundary matrix $\delta^k: C^k(K; \mathcal{F}) \to C^{k+1}(K; \mathcal{F})$.

    Algebraic Signature:
        $(\delta^k x)(\tau) = \sum_{\sigma \trianglelefteq \tau,\, \dim \sigma = k}
        \mathcal{E}_{\sigma \trianglelefteq \tau} x(\sigma)$

    Carrier:
        `SparseMatrix[tuple[Cell, int], float]` mapping column keys `(face_cell, i)` to
        row keys `(coface_cell, j)`.
    """
    if k < 0:
        return {}
    poset = sheaf.poset_category
    matrix: dict[CellStalkCoord, dict[CellStalkCoord, float]] = {}

    for face, coface in sorted(poset.direct_faces):
        if face.dimension != k or coface.dimension != k + 1:
            continue
        rho = sheaf.restriction_map(face, coface)
        for j, row in rho.items():
            row_key: CellStalkCoord = (coface, int(j))
            target_row = matrix.setdefault(row_key, {})
            for i, val in row.items():
                f_val = float(val)
                if abs(f_val) > 1e-15:
                    col_key: CellStalkCoord = (face, int(i))
                    target_row[col_key] = target_row.get(col_key, 0.0) + f_val
            if not target_row:
                matrix.pop(row_key, None)

    return matrix


def build_sheaf_laplacian(
    sheaf: FunctorialSheaf,
    k: int = 0,
) -> SparseMatrix[CellStalkCoord, float]:
    r"""Assemble the $k$-th Hodge-Sheaf Laplacian $L_k = (\delta^k)^T \delta^k + \delta^{k-1} (\delta^{k-1})^T$.

    For degree $k = 0$ (vertex signals), $L_0 = (\delta^0)^T \delta^0$.
    For a `ConstantSheaf` over a `SimplicialComplex`, $L_k$ is identically isomorphic
    to the discrete Hodge Laplacian $\Delta_k$.
    """
    from algebrax.matrix.core import add, dot, transpose
    from algebrax.semiring import StandardSemiring

    semiring = StandardSemiring(float)
    delta_k = build_sheaf_coboundary_matrix(sheaf, k)
    l_up: SparseMatrix[CellStalkCoord, float] = (
        dot(transpose(delta_k), delta_k, semiring=semiring) if delta_k else {}
    )

    if k <= 0:
        return l_up

    delta_prev = build_sheaf_coboundary_matrix(sheaf, k - 1)
    l_down: SparseMatrix[CellStalkCoord, float] = (
        dot(delta_prev, transpose(delta_prev), semiring=semiring) if delta_prev else {}
    )

    if not l_up:
        return l_down
    if not l_down:
        return l_up
    return add(l_up, l_down, semiring=semiring)


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

