r"""
Quiver Representations, Tits Quadratic Form, Gabriel's ADE Theorem & CellularSheaf Bridge.

Implements directed multigraph quivers $Q = (V_Q, E_Q, s, t)$, finite-dimensional sparse matrix
representations $M = (\{V_i\}, \{M_\alpha\})$, direct sums and morphisms, the Euler-Tits
quadratic form $q_Q(\mathbf{d})$, exact rational congruence classification of representation type
('finite', 'tame', 'wild'), Gabriel's bijection between finite-type indecomposables and positive
roots $\Phi^+$ of simply-laced ADE Dynkin diagrams ($A_n, D_n, E_6, E_7, E_8$), Weyl/BGP
dimension reflections, and bidirectional equivalence with `CellularSheaf`.

Algebraic Signatures:
    Euler Form:         $\langle \mathbf{u}, \mathbf{v} \rangle_Q =
                         \sum_{i \in V_Q} u_i v_i - \sum_{\alpha \in E_Q} u_{s(\alpha)} v_{t(\alpha)}$
    Tits Form:          $q_Q(\mathbf{d}) = \sum_{i \in V_Q} d_i^2
                         - \sum_{\alpha \in E_Q} d_{s(\alpha)} d_{t(\alpha)}
                         = \tfrac{1}{2} \mathbf{d}^T C_Q \mathbf{d}$
    Quiver Morphism:    $f_{t(\alpha)} \circ M_\alpha = N_\alpha \circ f_{s(\alpha)}
                         \quad \forall \alpha \in E_Q$
    Gabriel's Theorem:  $Q$ is finite representation type $\iff q_Q$ is positive definite
                         $\iff$ underlying graph is $\bigsqcup (A_n, D_n, E_6, E_7, E_8)$
"""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from types import MappingProxyType
from typing import Any, Generic, Literal, TypeVar

from algebrax.lie.roots import RootSystem
from algebrax.matrix.core import dot
from algebrax.topology.sheaf import CellularSheaf
from algebrax.typing import SparseMatrix

K = TypeVar('K')
V = TypeVar('V', bound=Hashable)
E = TypeVar('E', bound=Hashable)

__all__ = [
    'FiniteQuiver',
    'QuiverRepresentation',
    'bgp_reflect_dimension',
    'classify_dynkin_type',
    'classify_representation_type',
    'cycle_quiver',
    'direct_sum_quiver_rep',
    'dynkin_quiver',
    'euler_form',
    'from_cellular_sheaf',
    'gabriel_positive_roots',
    'interval_representation',
    'kronecker_quiver',
    'simple_representation',
    'tits_quadratic_form',
    'to_cellular_sheaf',
]


def _identity_sparse(dim: int) -> dict[int, dict[int, float]]:
    return {i: {i: 1.0} for i in range(dim)}


def _is_identity_sparse(mat: Mapping[int, Mapping[int, Any]], dim: int, tol: float = 1e-12) -> bool:
    for r, row in mat.items():
        if r < 0 or r >= dim:
            return False
        for c, val in row.items():
            expected = 1.0 if r == c else 0.0
            if abs(complex(val) - expected) > tol:
                return False
    return all(abs(complex(mat.get(i, {}).get(i, 0.0)) - 1.0) <= tol for i in range(dim))


def _normalize_dim_vector(quiver: FiniteQuiver[V, Any], dim_vec: Mapping[V, int] | Sequence[int]) -> list[int]:
    if isinstance(dim_vec, Mapping):
        missing = [v for v in quiver.vertices if v not in dim_vec]
        if missing:
            raise KeyError(f'Missing dimension entries for vertices: {missing!r}.')
        return [int(dim_vec[v]) for v in quiver.vertices]
    if len(dim_vec) != len(quiver.vertices):
        raise ValueError(
            f'Dimension vector length {len(dim_vec)} does not match vertex count {len(quiver.vertices)}.'
        )
    return [int(x) for x in dim_vec]


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b) if a and b else max(abs(a), abs(b))


def _column_to_primitive_int_vector(u_mat: list[list[Fraction]], col_idx: int) -> list[int]:
    """Scale rational column `col_idx` of `u_mat` to a primitive integer vector."""
    col = [row[col_idx] for row in u_mat]
    den = 1
    for x in col:
        den = _lcm(den, x.denominator)
    ints = [int(x * den) for x in col]
    g = 0
    for x in ints:
        g = gcd(g, abs(x))
    if g > 1:
        ints = [x // g for x in ints]
    for x in ints:
        if x != 0:
            if x < 0:
                ints = [-y for y in ints]
            break
    return ints


def _find_nonzero_off_diagonal(mat: list[list[Fraction]], start: int) -> tuple[int, int, Fraction] | None:
    n = len(mat)
    for i in range(start, n):
        for j in range(i + 1, n):
            if mat[i][j] != 0:
                return i, j, mat[i][j]
    return None


def _congruence_eliminate_pivot(
    mat: list[list[Fraction]],
    u_mat: list[list[Fraction]],
    k: int,
    pivot: int,
) -> None:
    """Swap pivot into index `k` and eliminate row/column `k` by exact congruence."""
    n = len(mat)
    if pivot != k:
        mat[k], mat[pivot] = mat[pivot], mat[k]
        for r in range(n):
            mat[r][k], mat[r][pivot] = mat[r][pivot], mat[r][k]
            u_mat[r][k], u_mat[r][pivot] = u_mat[r][pivot], u_mat[r][k]

    piv_val = mat[k][k]
    for j in range(k + 1, n):
        factor = mat[k][j] / piv_val
        if factor == 0:
            continue
        for r in range(k, n):
            mat[r][j] -= factor * mat[r][k]
        for c in range(k, n):
            mat[j][c] -= factor * mat[k][c]
        for r in range(n):
            u_mat[r][j] -= factor * u_mat[r][k]


def _analyze_symmetric_form(
    cartan: Sequence[Sequence[int]],
) -> tuple[Literal['positive_definite', 'positive_semidefinite', 'indefinite'], list[int] | None]:
    """Classify symmetric integer matrix C via exact rational congruence U^T C U = D.

    Returns `(definiteness, witness)` where `witness` is None if positive definite,
    or an exact non-zero integer vector d with d^T C d <= 0 otherwise.
    """
    n = len(cartan)
    if n == 0:
        return 'positive_definite', None

    mat = [[Fraction(cartan[i][j]) for j in range(n)] for i in range(n)]
    u_mat = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]

    for k in range(n):
        neg_idx = next((i for i in range(k, n) if mat[i][i] < 0), -1)
        if neg_idx != -1:
            return 'indefinite', _column_to_primitive_int_vector(u_mat, neg_idx)

        pivot = next((i for i in range(k, n) if mat[i][i] > 0), -1)
        if pivot == -1:
            off = _find_nonzero_off_diagonal(mat, k)
            if off is not None:
                i, j, val = off
                sign = Fraction(-1) if val > 0 else Fraction(1)
                for r in range(n):
                    u_mat[r][i] = u_mat[r][i] + sign * u_mat[r][j]
                return 'indefinite', _column_to_primitive_int_vector(u_mat, i)
            return 'positive_semidefinite', _column_to_primitive_int_vector(u_mat, k)

        _congruence_eliminate_pivot(mat, u_mat, k, pivot)

    return 'positive_definite', None


@dataclass(frozen=True)
class FiniteQuiver(Generic[V, E]):
    r"""A finite directed multigraph quiver $Q = (V_Q, E_Q, s, t)$.

    Conforms structurally to `algebrax.category.Quiver[V, E]` via `source(arrow)` and
    `target(arrow)` methods, while exposing read-only `source_map` and `target_map` views.

    Algebraic Signature:
        $Q = \langle V_Q, E_Q, s: E_Q \to V_Q, t: E_Q \to V_Q \rangle$

    Attributes:
        vertices: Ordered tuple of distinct vertex identifiers $V_Q$.
        edges: Ordered tuple of distinct arrow identifiers $E_Q$.
        source_map: Read-only mapping $s : E_Q \to V_Q$ giving each arrow's source (tail) vertex.
        target_map: Read-only mapping $t : E_Q \to V_Q$ giving each arrow's target (head) vertex.
    """

    vertices: tuple[V, ...]
    edges: tuple[E, ...]
    source_map: Mapping[E, V]
    target_map: Mapping[E, V]

    def __post_init__(self) -> None:
        verts = tuple(self.vertices)
        edgs = tuple(self.edges)
        if len(set(verts)) != len(verts):
            raise ValueError('FiniteQuiver vertices must be unique.')
        if len(set(edgs)) != len(edgs):
            raise ValueError('FiniteQuiver edges must be unique.')

        vert_set = set(verts)
        src = dict(self.source_map)
        tgt = dict(self.target_map)
        for e in edgs:
            if e not in src or e not in tgt:
                raise KeyError(f'Edge {e!r} must be present in both source_map and target_map.')
            if src[e] not in vert_set:
                raise ValueError(f'Source vertex {src[e]!r} of edge {e!r} not in quiver vertices.')
            if tgt[e] not in vert_set:
                raise ValueError(f'Target vertex {tgt[e]!r} of edge {e!r} not in quiver vertices.')

        object.__setattr__(self, 'vertices', verts)
        object.__setattr__(self, 'edges', edgs)
        object.__setattr__(self, 'source_map', MappingProxyType(src))
        object.__setattr__(self, 'target_map', MappingProxyType(tgt))

    @classmethod
    def from_edges(
        cls,
        vertices: Sequence[V],
        edge_specs: Sequence[tuple[E, V, V]],
    ) -> FiniteQuiver[V, E]:
        """Construct a FiniteQuiver from vertices and `(edge_id, source, target)` triples."""
        edges = tuple(e for e, _, _ in edge_specs)
        src = {e: u for e, u, _ in edge_specs}
        tgt = {e: v for e, _, v in edge_specs}
        return cls(vertices=tuple(vertices), edges=edges, source_map=src, target_map=tgt)

    def source(self, arrow: E) -> V:
        """Return the source (tail) vertex $s(\\alpha)$ of `arrow`."""
        return self.source_map[arrow]

    def target(self, arrow: E) -> V:
        """Return the target (head) vertex $t(\\alpha)$ of `arrow`."""
        return self.target_map[arrow]

    @property
    def num_vertices(self) -> int:
        return len(self.vertices)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    def incoming(self, vertex: V) -> tuple[E, ...]:
        """Return all arrows with target equal to `vertex`."""
        return tuple(e for e in self.edges if self.target_map[e] == vertex)

    def outgoing(self, vertex: V) -> tuple[E, ...]:
        """Return all arrows with source equal to `vertex`."""
        return tuple(e for e in self.edges if self.source_map[e] == vertex)

    def is_acyclic(self) -> bool:
        """Return True if the quiver contains no directed cycles (including self-loops)."""
        in_deg: dict[V, int] = dict.fromkeys(self.vertices, 0)
        adj: dict[V, list[V]] = {v: [] for v in self.vertices}
        for e in self.edges:
            u, v = self.source_map[e], self.target_map[e]
            adj[u].append(v)
            in_deg[v] += 1
        queue = deque(v for v, d in in_deg.items() if d == 0)
        visited = 0
        while queue:
            u = queue.popleft()
            visited += 1
            for nxt in adj[u]:
                in_deg[nxt] -= 1
                if in_deg[nxt] == 0:
                    queue.append(nxt)
        return visited == len(self.vertices)

    def euler_matrix(self) -> list[list[int]]:
        r"""Return the Euler bilinear form matrix $E_{ij} = \delta_{ij} - \#\{\alpha: i \to j\}$."""
        idx = {v: i for i, v in enumerate(self.vertices)}
        n = len(self.vertices)
        mat = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
        for e in self.edges:
            mat[idx[self.source_map[e]]][idx[self.target_map[e]]] -= 1
        return mat

    def symmetric_cartan_matrix(self) -> list[list[int]]:
        r"""Return the symmetric Cartan matrix $C_Q = E_Q + E_Q^T$.

        Satisfies $q_Q(\mathbf{d}) = \frac{1}{2}\mathbf{d}^T C_Q \mathbf{d}$.
        """
        e_mat = self.euler_matrix()
        n = len(e_mat)
        return [[e_mat[i][j] + e_mat[j][i] for j in range(n)] for i in range(n)]

    def connected_components(self) -> list[FiniteQuiver[V, E]]:
        """Partition the quiver into its weakly connected component subquivers."""
        adj: dict[V, set[V]] = {v: set() for v in self.vertices}
        for e in self.edges:
            u, v = self.source_map[e], self.target_map[e]
            adj[u].add(v)
            adj[v].add(u)

        seen: set[V] = set()
        components: list[FiniteQuiver[V, E]] = []
        for start in self.vertices:
            if start in seen:
                continue
            comp_set: set[V] = set()
            queue = deque([start])
            while queue:
                cur = queue.popleft()
                if cur in comp_set:
                    continue
                comp_set.add(cur)
                seen.add(cur)
                for nbr in adj[cur]:
                    if nbr not in comp_set:
                        queue.append(nbr)
            comp_verts = tuple(v for v in self.vertices if v in comp_set)
            comp_edges = tuple(e for e in self.edges if self.source_map[e] in comp_set)
            components.append(
                FiniteQuiver(
                    vertices=comp_verts,
                    edges=comp_edges,
                    source_map={e: self.source_map[e] for e in comp_edges},
                    target_map={e: self.target_map[e] for e in comp_edges},
                )
            )
        return components

    def all_paths(self, max_length: int | None = None) -> list[tuple[V, tuple[E, ...]]]:
        r"""Enumerate directed paths `(start_vertex, (e_1, ..., e_k))` in the quiver.

        If `max_length` is None, the quiver must be acyclic so the path basis is finite.
        """
        if max_length is None and not self.is_acyclic():
            raise ValueError('Quiver contains a directed cycle; specify max_length to enumerate bounded paths.')
        if max_length is not None and max_length < 0:
            raise ValueError(f'max_length must be >= 0, got {max_length}.')

        paths: list[tuple[V, tuple[E, ...]]] = [(v, ()) for v in self.vertices]
        frontier: list[tuple[V, V, tuple[E, ...]]] = [(v, v, ()) for v in self.vertices]
        length = 0
        while frontier:
            if max_length is not None and length >= max_length:
                break
            next_frontier: list[tuple[V, V, tuple[E, ...]]] = []
            for start_v, cur_v, edge_seq in frontier:
                for e in self.outgoing(cur_v):
                    nxt_v = self.target_map[e]
                    nxt_seq = (*edge_seq, e)
                    paths.append((start_v, nxt_seq))
                    next_frontier.append((start_v, nxt_v, nxt_seq))
            frontier = next_frontier
            length += 1
        return paths


@dataclass(frozen=True)
class QuiverRepresentation(Generic[K, V, E]):
    r"""A finite-dimensional representation $M = (\{V_i\}, \{M_\alpha\})$ of a quiver $Q$ over field $K$.

    For each vertex $v \in V_Q$, assigns vector space $V_v = K^{d_v}$ of dimension `dimensions[v]`.
    For each arrow $\alpha: u \to v$, assigns sparse matrix `edge_maps[alpha]` of shape
    $d_v \times d_u$ representing the linear map $M_\alpha : V_u \to V_v$.
    """

    quiver: FiniteQuiver[V, E]
    dimensions: dict[V, int]
    edge_maps: dict[E, SparseMatrix[int, K]]

    def __post_init__(self) -> None:
        dims: dict[V, int] = {}
        for v in self.quiver.vertices:
            if v not in self.dimensions:
                raise KeyError(f'Missing dimension for vertex {v!r}.')
            d = int(self.dimensions[v])
            if d < 0:
                raise ValueError(f'Dimension at vertex {v!r} must be non-negative, got {d}.')
            dims[v] = d

        maps: dict[E, SparseMatrix[int, K]] = {}
        for e in self.quiver.edges:
            u = self.quiver.source(e)
            v = self.quiver.target(e)
            du, dv = dims[u], dims[v]
            mat = self.edge_maps.get(e, {})
            cleaned: dict[int, dict[int, K]] = {}
            for r, row in mat.items():
                if r < 0 or r >= dv:
                    raise ValueError(f'Row index {r} out of bounds for edge {e!r} target dim {dv}.')
                clean_row: dict[int, K] = {}
                for c, val in row.items():
                    if c < 0 or c >= du:
                        raise ValueError(f'Col index {c} out of bounds for edge {e!r} source dim {du}.')
                    if isinstance(val, (int, float, complex)) and abs(val) <= 1e-15:
                        continue
                    clean_row[c] = val
                if clean_row:
                    cleaned[r] = clean_row
            maps[e] = cleaned

        object.__setattr__(self, 'dimensions', dims)
        object.__setattr__(self, 'edge_maps', maps)

    @property
    def dimension_vector(self) -> tuple[int, ...]:
        """Return the dimension vector $(d_1, \\dots, d_n)$ aligned with `quiver.vertices`."""
        return tuple(self.dimensions[v] for v in self.quiver.vertices)

    @property
    def total_dimension(self) -> int:
        """Return total vector space dimension $\\sum_{v \\in V_Q} d_v$."""
        return sum(self.dimensions.values())

    def direct_sum(self, other: QuiverRepresentation[K, V, E]) -> QuiverRepresentation[K, V, E]:
        """Return the block-diagonal direct sum representation $M \\oplus N$."""
        return direct_sum_quiver_rep(self, other)

    def to_cellular_sheaf(self) -> CellularSheaf[V]:
        """Convert this quiver representation into an equivalent 1D `CellularSheaf`."""
        return to_cellular_sheaf(self)


def direct_sum_quiver_rep(
    rep1: QuiverRepresentation[K, V, E],
    rep2: QuiverRepresentation[K, V, E],
) -> QuiverRepresentation[K, V, E]:
    r"""Construct the block-diagonal direct sum $M \oplus N$ of two representations of the same quiver."""
    if rep1.quiver != rep2.quiver:
        raise ValueError('Cannot form direct sum of representations over different quivers.')

    quiver = rep1.quiver
    dims = {v: rep1.dimensions[v] + rep2.dimensions[v] for v in quiver.vertices}
    maps: dict[E, SparseMatrix[int, K]] = {}
    for e in quiver.edges:
        u = quiver.source(e)
        v = quiver.target(e)
        off_u = rep1.dimensions[u]
        off_v = rep1.dimensions[v]
        combined: dict[int, dict[int, K]] = {}
        for r, row in rep1.edge_maps[e].items():
            combined[r] = dict(row)
        for r, row in rep2.edge_maps[e].items():
            combined[r + off_v] = {c + off_u: val for c, val in row.items()}
        maps[e] = combined

    return QuiverRepresentation(quiver=quiver, dimensions=dims, edge_maps=maps)


def simple_representation(quiver: FiniteQuiver[V, E], vertex: V) -> QuiverRepresentation[float, V, E]:
    r"""Construct the simple 1-dimensional representation $S(i)$ concentrated at `vertex` with zero arrow maps."""
    if vertex not in quiver.vertices:
        raise KeyError(f'Vertex {vertex!r} not in quiver.')
    dims = {v: (1 if v == vertex else 0) for v in quiver.vertices}
    maps: dict[E, SparseMatrix[int, float]] = {e: {} for e in quiver.edges}
    return QuiverRepresentation(quiver=quiver, dimensions=dims, edge_maps=maps)


def interval_representation(
    quiver: FiniteQuiver[V, E],
    support_vertices: Sequence[V],
) -> QuiverRepresentation[float, V, E]:
    r"""Construct the thin indecomposable indicator representation with $K^1$ on `support_vertices`
    and identity maps $[1]$ on every arrow whose endpoints both lie in `support_vertices`.
    """
    sup = set(support_vertices)
    missing = sup - set(quiver.vertices)
    if missing:
        raise KeyError(f'Support vertices not in quiver: {missing!r}.')
    dims = {v: (1 if v in sup else 0) for v in quiver.vertices}
    maps: dict[E, SparseMatrix[int, float]] = {}
    for e in quiver.edges:
        if quiver.source(e) in sup and quiver.target(e) in sup:
            maps[e] = {0: {0: 1.0}}
        else:
            maps[e] = {}
    return QuiverRepresentation(quiver=quiver, dimensions=dims, edge_maps=maps)


def euler_form(
    quiver: FiniteQuiver[V, E],
    dim_u: Mapping[V, int] | Sequence[int],
    dim_v: Mapping[V, int] | Sequence[int],
) -> int:
    r"""Evaluate the non-symmetric Euler bilinear form
    $\langle \mathbf{u}, \mathbf{v} \rangle_Q = \sum_i u_i v_i - \sum_{\alpha: i \to j} u_i v_j$.
    """
    u_vec = _normalize_dim_vector(quiver, dim_u)
    v_vec = _normalize_dim_vector(quiver, dim_v)
    idx = {v: i for i, v in enumerate(quiver.vertices)}
    vertex_term = sum(ui * vi for ui, vi in zip(u_vec, v_vec))
    edge_term = sum(u_vec[idx[quiver.source(e)]] * v_vec[idx[quiver.target(e)]] for e in quiver.edges)
    return vertex_term - edge_term


def tits_quadratic_form(
    quiver: FiniteQuiver[V, E],
    dim_vec: Mapping[V, int] | Sequence[int],
) -> int:
    r"""Evaluate the Euler-Tits quadratic form
    $q_Q(\mathbf{d}) = \sum_{i \in V_Q} d_i^2 - \sum_{\alpha \in E_Q} d_{s(\alpha)} d_{t(\alpha)}$.
    """
    return euler_form(quiver, dim_vec, dim_vec)


def bgp_reflect_dimension(
    quiver: FiniteQuiver[V, E],
    dim_vec: Mapping[V, int],
    vertex: V,
) -> dict[V, int]:
    r"""Apply the Bernstein-Gelfand-Ponomarev (Weyl) simple reflection $s_i$ to a dimension vector:
    $$(s_i \mathbf{d})_j = \begin{cases}
        \sum_{\text{adj } k \text{ to } i} d_k - d_i & \text{if } j = i, \\
        d_j & \text{if } j \neq i.
    \end{cases}$$
    Preserves the Tits quadratic form $q_Q(s_i \mathbf{d}) = q_Q(\mathbf{d})$ on loop-free quivers.
    """
    if vertex not in quiver.vertices:
        raise KeyError(f'Vertex {vertex!r} not in quiver.')
    for e in quiver.edges:
        if quiver.source(e) == vertex and quiver.target(e) == vertex:
            raise ValueError(f'Cannot apply BGP reflection at vertex {vertex!r} with a self-loop.')
    out = {v: int(dim_vec[v]) for v in quiver.vertices}
    neighbor_sum = 0
    for e in quiver.edges:
        if quiver.source(e) == vertex:
            neighbor_sum += out[quiver.target(e)]
        elif quiver.target(e) == vertex:
            neighbor_sum += out[quiver.source(e)]
    out[vertex] = neighbor_sum - out[vertex]
    return out


def _classify_connected_tree(
    n: int,
    adj: dict[int, list[int]],
) -> str:
    """Classify a simple connected tree into ADE Dynkin, extended Euclidean ~D/~E, or Wild."""
    degrees = [len(adj[i]) for i in range(n)]
    branch_nodes = [i for i, d in enumerate(degrees) if d >= 3]

    if not branch_nodes:
        return f'A{n}'

    if len(branch_nodes) == 1:
        center = branch_nodes[0]
        deg = degrees[center]
        arms: list[int] = []
        for nbr in adj[center]:
            arm_len = 1
            prev, cur = center, nbr
            while len(adj[cur]) == 2:
                nxt = adj[cur][0] if adj[cur][1] == prev else adj[cur][1]
                prev, cur = cur, nxt
                arm_len += 1
            arms.append(arm_len)
        arms.sort()
        if deg == 3:
            arm_tuple = (arms[0], arms[1], arms[2])
            if arm_tuple[0] == 1 and arm_tuple[1] == 1:
                return f'D{n}'
            exact_e = {
                (1, 2, 2): 'E6',
                (1, 2, 3): 'E7',
                (1, 2, 4): 'E8',
                (2, 2, 2): '~E6',
                (1, 3, 3): '~E7',
                (1, 2, 5): '~E8',
            }
            return exact_e.get(arm_tuple, 'Wild')
        if deg == 4 and arms == [1, 1, 1, 1]:
            return '~D4'
        return 'Wild'

    if len(branch_nodes) == 2 and all(degrees[b] == 3 for b in branch_nodes):
        # Extended ~D_n (n >= 5): two degree-3 hubs, each with two length-1 leaves
        b1, b2 = branch_nodes
        leaves_b1 = sum(1 for nbr in adj[b1] if degrees[nbr] == 1)
        leaves_b2 = sum(1 for nbr in adj[b2] if degrees[nbr] == 1)
        if leaves_b1 == 2 and leaves_b2 == 2:
            return f'~D{n - 1}'

    return 'Wild'


def _classify_connected_component(comp: FiniteQuiver[V, E]) -> tuple[Literal['finite', 'tame', 'wild'], str]:
    """Classify a single connected quiver component into (rep_type, dynkin_label)."""
    n = comp.num_vertices
    m = comp.num_edges
    idx = {v: i for i, v in enumerate(comp.vertices)}

    loops = sum(1 for e in comp.edges if comp.source(e) == comp.target(e))
    if loops > 0:
        if n == 1 and m == 1:
            return 'tame', '~A0'
        return 'wild', 'Wild'

    # Count undirected multiplicities between distinct vertices
    pair_counts: dict[tuple[int, int], int] = {}
    for e in comp.edges:
        u, v = idx[comp.source(e)], idx[comp.target(e)]
        pair = (u, v) if u < v else (v, u)
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

    max_mult = max(pair_counts.values(), default=0)
    if max_mult > 1:
        if n == 2 and m == 2 and max_mult == 2:
            return 'tame', '~A1'
        return 'wild', 'Wild'

    # Simple connected undirected graph
    if m == n:
        # Cycle graph iff every vertex has degree 2
        deg = [0] * n
        for u, v in pair_counts:
            deg[u] += 1
            deg[v] += 1
        if all(d == 2 for d in deg):
            return 'tame', f'~A{n - 1}'
        return 'wild', 'Wild'

    if m > n:
        return 'wild', 'Wild'

    # Simple connected tree (m == n - 1)
    adj: dict[int, list[int]] = {i: [] for i in range(n)}
    for u, v in pair_counts:
        adj[u].append(v)
        adj[v].append(u)
    label = _classify_connected_tree(n, adj)
    if label == 'Wild':
        return 'wild', 'Wild'
    if label.startswith('~'):
        return 'tame', label
    return 'finite', label


def classify_dynkin_type(quiver: FiniteQuiver[V, E]) -> str:
    r"""Identify the Dynkin / Euclidean ADE label of a quiver (e.g. `'A3'`, `'D4'`, `'E6'`, `'~A1'`, `'Wild'`).

    Disconnected quivers return `' + '`-joined component labels (e.g. `'A2 + D4'`).
    """
    if quiver.num_vertices == 0:
        return 'Empty'
    labels = [_classify_connected_component(c)[1] for c in quiver.connected_components()]
    return ' + '.join(labels)


def classify_representation_type(quiver: FiniteQuiver[V, E]) -> Literal['finite', 'tame', 'wild']:
    r"""Classify quiver representation type via Gabriel's ADE & Donovan-Freislich-Nazarova theorems.

    Returns:
        - `'finite'`: Every connected component is simply-laced Dynkin ($A_n, D_n, E_6, E_7, E_8$)
          (equivalently, the Tits form $q_Q$ is positive definite).
        - `'tame'`: No wild component and at least one extended Euclidean component
          ($\widetilde{A}_n, \widetilde{D}_n, \widetilde{E}_6, \widetilde{E}_7, \widetilde{E}_8$)
          (equivalently, $q_Q$ is positive semidefinite and singular).
        - `'wild'`: Indefinite Tits form (contains wild subquiver).
    """
    if quiver.num_vertices == 0:
        return 'finite'
    rep_types = [_classify_connected_component(c)[0] for c in quiver.connected_components()]
    if 'wild' in rep_types:
        return 'wild'
    if 'tame' in rep_types:
        return 'tame'
    return 'finite'


def gabriel_positive_roots(quiver: FiniteQuiver[V, E]) -> list[dict[V, int]]:
    r"""Return all positive roots $\Phi^+$ (dimension vectors of indecomposables) of a finite-type ADE quiver.

    By Gabriel's Theorem (1972), isomorphism classes of indecomposable representations of an ADE
    quiver $Q$ are in exact 1-to-1 bijection with the positive roots $\Phi^+$ of the associated
    simply-laced root system (`RootSystem`), each satisfying $q_Q(\alpha) = 1$.
    """
    rep_type = classify_representation_type(quiver)
    if rep_type != 'finite':
        raise ValueError(
            f'Gabriel bijection applies only to finite-type ADE quivers; '
            f'got {rep_type!r} ({classify_dynkin_type(quiver)}).'
        )
    if quiver.num_vertices == 0:
        return []

    roots_as_dicts: list[dict[V, int]] = []
    for comp in quiver.connected_components():
        dynkin_label = _classify_connected_component(comp)[1]
        rs = RootSystem.from_cartan_matrix(comp.symmetric_cartan_matrix(), dynkin_type=dynkin_label)
        for root in rs.positive_roots:
            dim_dict: dict[V, int] = dict.fromkeys(quiver.vertices, 0)
            for v_comp, coeff in zip(comp.vertices, root):
                dim_dict[v_comp] = coeff
            roots_as_dicts.append(dim_dict)

    return roots_as_dicts


def dynkin_quiver(
    family: str,
    rank: int | None = None,
    orientation: Literal['linear', 'alternating'] = 'linear',
) -> FiniteQuiver[int, str]:
    r"""Build a canonical simply-laced ADE Dynkin quiver ($A_n, D_n, E_6, E_7, E_8$)
    matching the vertex ordering of `algebrax.lie.RootSystem`.
    """
    fam = family.upper().strip()
    if fam not in ('A', 'D', 'E6', 'E7', 'E8'):
        raise ValueError(f'Gabriel ADE quivers must be simply-laced (A, D, E6, E7, E8); got {family!r}.')
    rs = RootSystem.from_dynkin(fam, rank)

    n = rs.rank
    c_mat = rs.cartan_matrix
    verts = tuple(range(n))

    # Build undirected edges from off-diagonal -1 entries of Cartan matrix
    undirected: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            if c_mat[i][j] == -1:
                undirected.append((i, j))

    # Compute bipartition for alternating (sink/source) orientation
    color: dict[int, int] = {}
    if orientation == 'alternating':
        adj: dict[int, list[int]] = {i: [] for i in verts}
        for u, v in undirected:
            adj[u].append(v)
            adj[v].append(u)
        queue = deque([0])
        color[0] = 0
        while queue:
            cur = queue.popleft()
            for nbr in adj[cur]:
                if nbr not in color:
                    color[nbr] = 1 - color[cur]
                    queue.append(nbr)

    edge_specs: list[tuple[str, int, int]] = []
    for idx_e, (u, v) in enumerate(undirected):
        if orientation == 'alternating' and color.get(u, 0) == 1:
            edge_specs.append((f'e{idx_e}', v, u))
        else:
            edge_specs.append((f'e{idx_e}', u, v))
    return FiniteQuiver.from_edges(verts, edge_specs)


def kronecker_quiver(num_arrows: int = 2) -> FiniteQuiver[int, str]:
    r"""Build the $m$-arrow Kronecker quiver $0 \rightrightarrows 1$.

    `m=1` is $A_2$ (finite), `m=2` is $\widetilde{A}_1$ (tame), and `m>=3` is wild.
    """
    if num_arrows < 1:
        raise ValueError(f'num_arrows must be >= 1, got {num_arrows}.')
    return FiniteQuiver.from_edges((0, 1), [(f'a{k}', 0, 1) for k in range(num_arrows)])


def cycle_quiver(n: int) -> FiniteQuiver[int, str]:
    r"""Build the oriented $n$-cycle quiver $\widetilde{A}_{n-1}$ ($n \ge 1$; $n=1$ is the Jordan self-loop quiver)."""
    if n < 1:
        raise ValueError(f'cycle_quiver requires n >= 1, got {n}.')
    return FiniteQuiver.from_edges(tuple(range(n)), [(f'e{i}', i, (i + 1) % n) for i in range(n)])


def to_cellular_sheaf(rep: QuiverRepresentation[Any, V, E]) -> CellularSheaf[V]:
    r"""Convert a simple loop-free quiver representation into an equivalent 1D `CellularSheaf`.

    For each directed edge $\alpha: u \to v$, sets edge stalk $\mathcal{F}(e) = V_v$ with
    restriction maps $\rho_{u \trianglelefteq e} = M_\alpha$ and $\rho_{v \trianglelefteq e} = \mathbf{I}_{d_v}$.
    Global sections $x \in H^0(G; \mathcal{F}) = \ker \delta_{\mathcal{F}}$ then satisfy
    $x_v = M_\alpha x_u$ identically for every arrow $\alpha: u \to v$.
    """
    quiver = rep.quiver
    for v in quiver.vertices:
        if rep.dimensions[v] <= 0:
            raise ValueError(
                f'CellularSheaf requires positive stalk dimensions; vertex {v!r} has dim {rep.dimensions[v]}.'
            )

    seen_pairs: set[frozenset[V]] = set()
    sheaf: CellularSheaf[V] = CellularSheaf()
    for v in quiver.vertices:
        sheaf.add_vertex(v, rep.dimensions[v])

    for e in quiver.edges:
        u = quiver.source(e)
        v = quiver.target(e)
        if u == v:
            raise ValueError(f'CellularSheaf does not support self-loop edge {e!r} on vertex {u!r}.')
        pair = frozenset((u, v))
        if pair in seen_pairs:
            raise ValueError(
                f'CellularSheaf requires a simple graph without parallel/anti-parallel edges between {u!r} and {v!r}.'
            )
        seen_pairs.add(pair)
        dv = rep.dimensions[v]
        rho_u = {
            r: {c: float(val) for c, val in row.items()}
            for r, row in rep.edge_maps[e].items()
        }
        rho_v = _identity_sparse(dv)
        sheaf.add_edge(u, v, dim=dv, rho_u=rho_u, rho_v=rho_v)

    return sheaf


def from_cellular_sheaf(
    sheaf: CellularSheaf[V],
    mode: Literal['auto', 'direct', 'incidence'] = 'auto',
) -> QuiverRepresentation[float, Any, Any]:
    r"""Convert a 1D `CellularSheaf` into a `QuiverRepresentation`.

    Modes:
        - `'direct'`: Requires each canonical edge $e = (u, v)$ to have an identity restriction map
          on one endpoint ($d_e = d_v, \rho_v = I$ or $d_e = d_u, \rho_u = I$), recovering the
          exact vertex-to-vertex directed quiver representation inverse to `to_cellular_sheaf`.
        - `'incidence'`: Always succeeds for any `CellularSheaf`; builds the bipartite incidence
          quiver with vertices $V \cup E$ and directed arrows $(v \to e)$ carrying $\rho_{v \trianglelefteq e}$.
        - `'auto'`: Uses `'direct'` when every edge has an identity endpoint restriction, else `'incidence'`.
    """
    if mode in ('auto', 'direct'):
        can_direct = True
        direct_edges: list[tuple[tuple[V, V], V, V, SparseMatrix[int, float]]] = []
        for canon_e, d_e in sheaf.edge_stalks.items():
            u, v = canon_e
            rho_u = sheaf.restrictions.get((u, canon_e), {})
            rho_v = sheaf.restrictions.get((v, canon_e), {})
            if sheaf.vertex_stalks[v] == d_e and _is_identity_sparse(rho_v, d_e):
                direct_edges.append((canon_e, u, v, rho_u))
            elif sheaf.vertex_stalks[u] == d_e and _is_identity_sparse(rho_u, d_e):
                direct_edges.append((canon_e, v, u, rho_v))
            else:
                can_direct = False
                break

        if can_direct:
            verts = tuple(sheaf.vertex_stalks.keys())
            q = FiniteQuiver.from_edges(verts, [(e_id, s, t) for e_id, s, t, _ in direct_edges])
            maps = {e_id: mat for e_id, _, _, mat in direct_edges}
            return QuiverRepresentation(quiver=q, dimensions=dict(sheaf.vertex_stalks), edge_maps=maps)
        if mode == 'direct':
            raise ValueError(
                'Cannot convert CellularSheaf in direct mode: at least one edge lacks an identity restriction map. '
                "Use mode='incidence' for general cellular sheaves."
            )

    # Bipartite incidence quiver: vertices = [('v', v), ...] + [('e', edge), ...]
    v_nodes: list[tuple[str, Any]] = [('v', v) for v in sheaf.vertex_stalks]
    e_nodes: list[tuple[str, Any]] = [('e', e) for e in sheaf.edge_stalks]
    all_nodes = tuple(v_nodes + e_nodes)
    dims: dict[tuple[str, Any], int] = {('v', v): d for v, d in sheaf.vertex_stalks.items()}
    for e, d in sheaf.edge_stalks.items():
        dims[('e', e)] = d

    edge_specs: list[tuple[tuple[V, tuple[V, V]], tuple[str, Any], tuple[str, Any]]] = []
    maps_inc: dict[tuple[V, tuple[V, V]], SparseMatrix[int, float]] = {}
    for canon_e in sheaf.edge_stalks:
        u, v = canon_e
        for endpoint in (u, v):
            arrow_id = (endpoint, canon_e)
            edge_specs.append((arrow_id, ('v', endpoint), ('e', canon_e)))
            maps_inc[arrow_id] = sheaf.restrictions.get((endpoint, canon_e), {})

    q_inc = FiniteQuiver.from_edges(all_nodes, edge_specs)
    return QuiverRepresentation(quiver=q_inc, dimensions=dims, edge_maps=maps_inc)


def _compose_morphism_check(
    rep1: QuiverRepresentation[Any, V, E],
    rep2: QuiverRepresentation[Any, V, E],
    morphism_maps: Mapping[V, SparseMatrix[int, Any]],
    tol: float,
) -> bool:
    """Internal helper verifying f_{t(e)} @ M_e == N_e @ f_{s(e)} on all arrows."""
    for e in rep1.quiver.edges:
        u = rep1.quiver.source(e)
        v = rep1.quiver.target(e)
        lhs = dot(morphism_maps[v], rep1.edge_maps[e])
        rhs = dot(rep2.edge_maps[e], morphism_maps[u])
        for r in set(lhs.keys()) | set(rhs.keys()):
            row_l = lhs.get(r, {})
            row_r = rhs.get(r, {})
            for c in set(row_l.keys()) | set(row_r.keys()):
                if abs(complex(row_l.get(c, 0.0)) - complex(row_r.get(c, 0.0))) > tol:
                    return False
    return True
