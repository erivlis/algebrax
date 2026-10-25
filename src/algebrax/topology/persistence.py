"""Persistent homology, dual persistent cohomology, simplicial filtrations, and barcode metrics."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from itertools import combinations
from typing import NamedTuple

from algebrax.topology.homology import SimplicialComplex
from algebrax.typing import SparseMatrix, SparseVector

__all__ = [
    'FilteredSimplicialComplex',
    'PersistenceInterval',
    'betti_curve',
    'bottleneck_distance',
    'persistence_entropy',
    'persistent_cohomology',
    'persistent_homology',
]


class PersistenceInterval(NamedTuple):
    r"""A birth-death topological interval $[b_i, d_i)$ in a persistence barcode.

    Algebraic Signature:
        $\mathbb{F}_2[b_i, d_i) \subset H_k(K_\bullet; \mathbb{F}_2)$

    Carrier:
        `NamedTuple(dimension, birth, death, birth_simplex, death_simplex)`

    Operations:
        - `persistence`: Lifespan $d_i - b_i$ (`math.inf` for essential homology classes).

    Properties:
        Satisfies $b_i \le d_i \le \infty$; essential classes have `death = math.inf`
        and `death_simplex = None`.

    Applications:
        Topological Data Analysis (TDA), persistence barcodes, persistence diagrams,
        multiscale cycle and void detection.

    Attributes:
        dimension: Homological dimension $k \ge 0$ of the topological feature.
        birth: Filtration value $b_i \in \mathbb{R}$ at which the feature is born.
        death: Filtration value $d_i \in \mathbb{R} \cup \{\infty\}$ at which the feature dies.
        birth_simplex: Canonical $k$-simplex $\sigma_{\text{birth}}$ that created the cycle.
        death_simplex: Canonical $(k+1)$-simplex $\sigma_{\text{death}}$ that filled the cycle,
            or `None` if the class is essential (`death == math.inf`).
    """

    dimension: int
    birth: float
    death: float
    birth_simplex: tuple[int, ...]
    death_simplex: tuple[int, ...] | None = None

    @property
    def persistence(self) -> float:
        """Lifespan `death - birth` (`math.inf` for essential classes)."""
        return self.death - self.birth


def _extract_vr_edges(
    distance_matrix: SparseMatrix[int, float],
    max_edge_length: float,
) -> tuple[set[int], dict[tuple[int, int], float], dict[int, set[int]]]:
    nodes: set[int] = set(distance_matrix.keys())
    for row in distance_matrix.values():
        nodes.update(row.keys())

    edge_weights: dict[tuple[int, int], float] = {}
    upper_neighbors: dict[int, set[int]] = {u: set() for u in nodes}

    sorted_nodes = sorted(nodes)
    for idx_u, u in enumerate(sorted_nodes):
        row_u = distance_matrix.get(u, {})
        for v in sorted_nodes[idx_u + 1 :]:
            row_v = distance_matrix.get(v, {})
            has_uv = v in row_u
            has_vu = u in row_v
            if not has_uv and not has_vu:
                continue
            if has_uv and has_vu:
                dist = max(float(row_u[v]), float(row_v[u]))
            elif has_uv:
                dist = float(row_u[v])
            else:
                dist = float(row_v[u])
            if dist <= max_edge_length:
                edge_weights[(u, v)] = dist
                upper_neighbors[u].add(v)

    return nodes, edge_weights, upper_neighbors


class FilteredSimplicialComplex:
    r"""Monotone filtration of a simplicial complex $\emptyset = K_0 \subseteq K_1 \subseteq \dots \subseteq K_m$.

    Algebraic Signature:
        $f: K \to \mathbb{R} \quad \text{such that} \quad \tau \subseteq \sigma \implies f(\tau) \le f(\sigma)$

    Carrier:
        `dict[tuple[int, ...], float]` (Mapping canonical sorted simplex tuples to birth filtration values).

    Operations:
        - Monotone Simplex Insertion (`add_simplex`): Inserts $\sigma$ and propagates
          $f(\tau) = \min(f(\tau), f(\sigma))$ to all faces $\tau \subset \sigma$.
        - Sublevel Thresholding (`to_simplicial_complex`): Extracts static `SimplicialComplex`
          $K_{\le t} = \{\sigma \in K \mid f(\sigma) \le t\}$.
        - Vietoris-Rips Constructor (`from_vietoris_rips`): Flag complex filtration
          $f(\sigma) = \max_{u, v \in \sigma} d(u, v)$.
        - Lower-Star Constructor (`from_lower_star`): Vertex scalar sublevel filtration
          $f(\sigma) = \max_{v \in \sigma} h(v)$.
        - Persistent Homology & Cohomology (`persistent_homology`, `persistent_cohomology`):
          Computes birth-death intervals and representative cocycles over $\mathbb{Z}_2$.

    Properties:
        Subcomplex monotonicity guarantees every sublevel set $K_{\le t}$ is a valid abstract
        simplicial complex closed under taking faces.

    Applications:
        Point-cloud topological data analysis, weighted network filtration, time-series attractor
        topology, scalar field sublevel persistence.
    """

    def __init__(
        self,
        simplices: Mapping[tuple[int, ...], float] | Iterable[tuple[tuple[int, ...], float]] | None = None,
    ) -> None:
        self._filtration: dict[tuple[int, ...], float] = {}
        if simplices is not None:
            items = simplices.items() if isinstance(simplices, Mapping) else simplices
            for simplex, f_val in items:
                self.add_simplex(simplex, float(f_val))

    @property
    def simplices(self) -> dict[tuple[int, ...], float]:
        """Dictionary mapping canonical simplex tuples to their filtration birth values."""
        return dict(self._filtration)

    def __len__(self) -> int:
        return len(self._filtration)

    def __contains__(self, simplex: object) -> bool:
        if not isinstance(simplex, tuple):
            return False
        s_tuple = tuple(sorted(simplex))
        return s_tuple in self._filtration

    def __getitem__(self, simplex: tuple[int, ...]) -> float:
        s_tuple = tuple(sorted(simplex))
        return self._filtration[s_tuple]

    def add_simplex(self, simplex: tuple[int, ...], filtration: float = 0.0) -> None:
        r"""Insert a simplex and all its sub-faces, enforcing $f(\tau) \le f(\sigma)$."""
        f_val = float(filtration)
        if math.isnan(f_val):
            raise ValueError('Filtration value cannot be NaN.')

        s_tuple = tuple(sorted(simplex))
        k = len(s_tuple) - 1
        if k < 0 or len(set(s_tuple)) < len(s_tuple):
            return

        existing = self._filtration.get(s_tuple)
        if existing is not None and existing <= f_val:
            return

        self._filtration[s_tuple] = f_val
        if k > 0:
            for face in combinations(s_tuple, k):
                self.add_simplex(face, f_val)

    def to_simplicial_complex(self, threshold: float = math.inf) -> SimplicialComplex:
        r"""Extract the static subcomplex $K_{\le t} = \{\sigma \mid f(\sigma) \le t\}$."""
        included = [s for s, f_val in self._filtration.items() if f_val <= threshold]
        return SimplicialComplex(included)

    @classmethod
    def from_vietoris_rips(
        cls,
        distance_matrix: SparseMatrix[int, float],
        max_dim: int = 2,
        max_edge_length: float = math.inf,
    ) -> FilteredSimplicialComplex:
        r"""Construct the Vietoris-Rips filtration where $f(\sigma) = \max_{u, v \in \sigma} d(u, v)$."""
        if max_dim < 0:
            raise ValueError(f'max_dim must be non-negative, got {max_dim}.')

        fsc = cls()
        nodes, edge_weights, upper_neighbors = _extract_vr_edges(distance_matrix, max_edge_length)

        for u in sorted(nodes):
            fsc._filtration[(u,)] = 0.0

        if max_dim == 0:
            return fsc

        current_k_simplices: list[tuple[tuple[int, ...], float, set[int]]] = []
        for (u, v), dist in sorted(edge_weights.items()):
            fsc._filtration[(u, v)] = dist
            common = upper_neighbors[u] & upper_neighbors[v]
            if common:
                current_k_simplices.append(((u, v), dist, common))

        for _dim in range(2, max_dim + 1):
            next_k_simplices: list[tuple[tuple[int, ...], float, set[int]]] = []
            for simplex, f_sigma, candidates in current_k_simplices:
                for w in sorted(candidates):
                    f_new = max(f_sigma, *(edge_weights[(u, w)] for u in simplex))
                    new_simplex = (*simplex, w)
                    fsc._filtration[new_simplex] = f_new
                    new_candidates = candidates & upper_neighbors[w]
                    if new_candidates:
                        next_k_simplices.append((new_simplex, f_new, new_candidates))
            current_k_simplices = next_k_simplices
            if not current_k_simplices:
                break

        return fsc

    @classmethod
    def from_lower_star(
        cls,
        complex: SimplicialComplex,
        vertex_values: SparseVector[int, float],
    ) -> FilteredSimplicialComplex:
        r"""Construct the lower-star sublevel filtration where $f(\sigma) = \max_{v \in \sigma} h(v)$."""
        fsc = cls()
        for dim_simplices in complex._simplices.values():
            for simplex in dim_simplices:
                f_val = max(float(vertex_values.get(v, 0.0)) for v in simplex)
                fsc.add_simplex(simplex, f_val)
        return fsc

    def persistent_homology(
        self,
        max_k: int = 2,
        include_zero_persistence: bool = False,
    ) -> list[PersistenceInterval]:
        """Compute persistence intervals across dimensions `0 <= k <= max_k`."""
        return persistent_homology(
            self,
            max_k=max_k,
            include_zero_persistence=include_zero_persistence,
        )

    def persistent_cohomology(
        self,
        max_k: int = 2,
        include_zero_persistence: bool = False,
    ) -> tuple[list[PersistenceInterval], dict[PersistenceInterval, set[tuple[int, ...]]]]:
        """Compute dual persistent cohomology intervals and representative cocycles."""
        return persistent_cohomology(
            self,
            max_k=max_k,
            include_zero_persistence=include_zero_persistence,
        )


def persistent_homology(
    filtration: FilteredSimplicialComplex,
    max_k: int = 2,
    include_zero_persistence: bool = False,
) -> list[PersistenceInterval]:
    r"""Compute the persistence barcode of a `FilteredSimplicialComplex` over $\mathbb{Z}_2$."""
    if max_k < 0:
        raise ValueError(f'max_k must be non-negative, got {max_k}.')

    ordered_simplices = sorted(
        ((s, f_val) for s, f_val in filtration._filtration.items() if len(s) - 1 <= max_k + 1),
        key=lambda item: (item[1], len(item[0]), item[0]),
    )
    if not ordered_simplices:
        return []

    idx_of = {s: i for i, (s, _) in enumerate(ordered_simplices)}
    cols_by_dim: dict[int, list[int]] = {}
    for j, (s, _) in enumerate(ordered_simplices):
        dim = len(s) - 1
        if 1 <= dim <= max_k + 1:
            cols_by_dim.setdefault(dim, []).append(j)

    low_to_col: dict[int, int] = {}
    reduced_cols: dict[int, set[int]] = {}
    paired_births: set[int] = set()
    death_cols: set[int] = set()
    intervals: list[PersistenceInterval] = []

    # Top-down dimension loop enables the Chen-Kerber clearing (twist) optimization
    for dim in range(max_k + 1, 0, -1):
        for j in cols_by_dim.get(dim, ()):
            if j in paired_births:
                continue
            s, d_time = ordered_simplices[j]
            col = {idx_of[s[:i] + s[i + 1 :]] for i in range(len(s))}
            while col and max(col) in low_to_col:
                col ^= reduced_cols[low_to_col[max(col)]]
            if col:
                piv = max(col)
                low_to_col[piv] = j
                reduced_cols[j] = col
                paired_births.add(piv)
                death_cols.add(j)
                if dim - 1 <= max_k:
                    b_simplex, b_time = ordered_simplices[piv]
                    if include_zero_persistence or d_time > b_time:
                        intervals.append(
                            PersistenceInterval(
                                dimension=dim - 1,
                                birth=b_time,
                                death=d_time,
                                birth_simplex=b_simplex,
                                death_simplex=s,
                            )
                        )

    for i, (b_simplex, b_time) in enumerate(ordered_simplices):
        dim = len(b_simplex) - 1
        if dim <= max_k and i not in paired_births and i not in death_cols:
            intervals.append(
                PersistenceInterval(
                    dimension=dim,
                    birth=b_time,
                    death=math.inf,
                    birth_simplex=b_simplex,
                    death_simplex=None,
                )
            )

    intervals.sort(key=lambda iv: (iv.dimension, iv.birth, iv.death, iv.birth_simplex))
    return intervals


def persistent_cohomology(
    filtration: FilteredSimplicialComplex,
    max_k: int = 2,
    include_zero_persistence: bool = False,
) -> tuple[list[PersistenceInterval], dict[PersistenceInterval, set[tuple[int, ...]]]]:
    r"""Compute dual persistent cohomology over $\mathbb{Z}_2$ and extract representative cocycles.

    Algebraic Signature:
        $H^k(K_\bullet; \mathbb{F}_2) \cong \bigoplus_{i} \mathbb{F}_2[b_i, d_i)$

    Carrier:
        `tuple[list[PersistenceInterval], dict[PersistenceInterval, set[tuple[int, ...]]]]`

    Operations:
        - De Silva-Morozov-Vejdemo-Johansson Dual Reduction: Sweeps simplices in filtration order,
          evaluating the $\mathbb{Z}_2$ coboundary pairing
          $\langle d z_i, \sigma_j \rangle = |z_i \cap \partial \sigma_j| \bmod 2$
          against active cocycles $z_i$.
        - Elder Cocycle Elimination: Kills the youngest cocycle $p = \max(I)$ with $\langle d z_p, \sigma_j \rangle = 1$
          and updates older cocycles $z_i \leftarrow z_i \oplus z_p$ so $d z_i = 0$ on $K_j$.

    Properties:
        By Universal Coefficient Duality, the returned `PersistenceInterval` list is identical
        to `persistent_homology(filtration, max_k)`, and each essential cocycle $z$ satisfies $d z \equiv 0 \pmod 2$.

    Args:
        filtration: Input `FilteredSimplicialComplex`.
        max_k: Maximum cohomology degree $k$ to compute (default `2`).
        include_zero_persistence: If True, includes ephemeral intervals where `birth == death`.

    Returns:
        Tuple `(intervals, cocycles)` where `cocycles[interval]` is the set of simplices in the
        representative $\mathbb{Z}_2$ cocycle.
    """
    if max_k < 0:
        raise ValueError(f'max_k must be non-negative, got {max_k}.')

    ordered_simplices = sorted(
        ((s, f_val) for s, f_val in filtration._filtration.items() if len(s) - 1 <= max_k + 1),
        key=lambda item: (item[1], len(item[0]), item[0]),
    )
    if not ordered_simplices:
        return [], {}

    idx_of = {s: i for i, (s, _) in enumerate(ordered_simplices)}
    active_cocycles: dict[int, dict[int, set[int]]] = {k: {} for k in range(max_k + 2)}
    intervals: list[PersistenceInterval] = []
    cocycles: dict[PersistenceInterval, set[tuple[int, ...]]] = {}

    for j, (s, d_time) in enumerate(ordered_simplices):
        dim = len(s) - 1
        if dim == 0:
            if max_k >= 0:
                active_cocycles[0][j] = {j}
            continue

        boundary = {idx_of[s[:i] + s[i + 1 :]] for i in range(len(s))}
        cocycles_dm1 = active_cocycles.get(dim - 1, {})
        non_zero_births = [b_idx for b_idx, z_supp in cocycles_dm1.items() if len(z_supp & boundary) % 2 == 1]

        if non_zero_births:
            piv = max(non_zero_births)
            z_piv = cocycles_dm1.pop(piv)
            for b_idx in non_zero_births:
                if b_idx != piv:
                    cocycles_dm1[b_idx] ^= z_piv

            if dim - 1 <= max_k:
                b_simplex, b_time = ordered_simplices[piv]
                if include_zero_persistence or d_time > b_time:
                    iv = PersistenceInterval(
                        dimension=dim - 1,
                        birth=b_time,
                        death=d_time,
                        birth_simplex=b_simplex,
                        death_simplex=s,
                    )
                    intervals.append(iv)
                    cocycles[iv] = {ordered_simplices[idx][0] for idx in z_piv}
        elif dim <= max_k:
            active_cocycles[dim][j] = {j}

    for dim in range(max_k + 1):
        for piv, z_supp in active_cocycles.get(dim, {}).items():
            b_simplex, b_time = ordered_simplices[piv]
            iv = PersistenceInterval(
                dimension=dim,
                birth=b_time,
                death=math.inf,
                birth_simplex=b_simplex,
                death_simplex=None,
            )
            intervals.append(iv)
            cocycles[iv] = {ordered_simplices[idx][0] for idx in z_supp}

    intervals.sort(key=lambda item: (item.dimension, item.birth, item.death, item.birth_simplex))
    return intervals, cocycles


def betti_curve(
    intervals: Iterable[PersistenceInterval],
    thresholds: Sequence[float],
    dimension: int = 0,
) -> list[int]:
    r"""Evaluate the Betti number $\beta_k(t)$ at each filtration threshold $t \in \text{thresholds}$."""
    dim_intervals = [iv for iv in intervals if iv.dimension == dimension and iv.death > iv.birth]
    return [sum(1 for iv in dim_intervals if iv.birth <= t < iv.death) for t in thresholds]


def persistence_entropy(
    intervals: Iterable[PersistenceInterval],
    dimension: int | None = None,
) -> float:
    r"""Compute the Shannon entropy $H = -\sum_i p_i \ln p_i$ of finite persistence lifespans."""
    lifespans = [
        iv.persistence
        for iv in intervals
        if (dimension is None or iv.dimension == dimension) and not math.isinf(iv.death) and iv.persistence > 0.0
    ]
    total_persistence = sum(lifespans)
    if total_persistence <= 0.0:
        return 0.0

    entropy_val = 0.0
    for length in lifespans:
        p = length / total_persistence
        if p > 0.0:
            entropy_val -= p * math.log(p)
    return entropy_val


def _has_perfect_bipartite_matching(adj: list[list[int]], num_left: int, num_right: int) -> bool:
    """Verify whether a bipartite graph on `num_left x num_right` admits a matching saturating all left nodes."""
    from collections import deque

    pair_u = [-1] * num_left
    pair_v = [-1] * num_right
    dist = [0] * num_left

    def bfs() -> bool:
        queue: deque[int] = deque()
        found_augmenting = False
        for u in range(num_left):
            if pair_u[u] == -1:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = -1

        while queue:
            u = queue.popleft()
            for v in adj[u]:
                pu = pair_v[v]
                if pu == -1:
                    found_augmenting = True
                elif dist[pu] == -1:
                    dist[pu] = dist[u] + 1
                    queue.append(pu)
        return found_augmenting

    def dfs(u: int) -> bool:
        for v in adj[u]:
            pu = pair_v[v]
            if pu == -1 or (dist[pu] == dist[u] + 1 and dfs(pu)):
                pair_u[u] = v
                pair_v[v] = u
                return True
        dist[u] = -1
        return False

    matched = 0
    while bfs():
        for u in range(num_left):
            if pair_u[u] == -1 and dfs(u):
                matched += 1

    return matched == num_left


def _bottleneck_finite_points(
    finite_a: list[tuple[float, float]],
    finite_b: list[tuple[float, float]],
) -> float:
    m = len(finite_a)
    n = len(finite_b)
    if m == 0 and n == 0:
        return 0.0

    diag_a = [0.5 * (d - b) for b, d in finite_a]
    diag_b = [0.5 * (d - b) for b, d in finite_b]
    if n == 0:
        return max(diag_a, default=0.0)
    if m == 0:
        return max(diag_b, default=0.0)

    pair_costs = [[max(abs(b_a - b_b), abs(d_a - d_b)) for b_b, d_b in finite_b] for b_a, d_a in finite_a]

    candidates_set: set[float] = {0.0}
    candidates_set.update(diag_a)
    candidates_set.update(diag_b)
    for row in pair_costs:
        candidates_set.update(row)
    candidates = sorted(candidates_set)

    total_nodes = m + n
    diag_right = list(range(n, total_nodes))

    def can_match(delta: float) -> bool:
        adj: list[list[int]] = [[] for _ in range(total_nodes)]
        for i in range(m):
            row_i = pair_costs[i]
            edges_i = [j for j in range(n) if row_i[j] <= delta]
            if diag_a[i] <= delta:
                edges_i.append(n + i)
            if not edges_i:
                return False
            adj[i] = edges_i

        for j in range(n):
            u_diag = m + j
            edges_diag = list(diag_right)
            if diag_b[j] <= delta:
                edges_diag.append(j)
            adj[u_diag] = edges_diag

        return _has_perfect_bipartite_matching(adj, total_nodes, total_nodes)

    lo = 0
    hi = len(candidates) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if can_match(candidates[mid]):
            hi = mid
        else:
            lo = mid + 1

    return candidates[lo]


def _bottleneck_single_dimension(
    intervals_a: list[PersistenceInterval],
    intervals_b: list[PersistenceInterval],
) -> float:
    ess_a = sorted(iv.birth for iv in intervals_a if math.isinf(iv.death))
    ess_b = sorted(iv.birth for iv in intervals_b if math.isinf(iv.death))
    if len(ess_a) != len(ess_b):
        return math.inf

    ess_dist = max((abs(a - b) for a, b in zip(ess_a, ess_b, strict=True)), default=0.0)
    finite_a = [(iv.birth, iv.death) for iv in intervals_a if not math.isinf(iv.death) and iv.death > iv.birth]
    finite_b = [(iv.birth, iv.death) for iv in intervals_b if not math.isinf(iv.death) and iv.death > iv.birth]
    fin_dist = _bottleneck_finite_points(finite_a, finite_b)
    return max(ess_dist, fin_dist)


def bottleneck_distance(
    diagram_a: Iterable[PersistenceInterval],
    diagram_b: Iterable[PersistenceInterval],
    dimension: int | None = None,
) -> float:
    r"""Compute the exact $L_\infty$ bottleneck distance $d_B(D_A, D_B)$ between two persistence diagrams."""
    list_a = list(diagram_a)
    list_b = list(diagram_b)
    if dimension is not None:
        sub_a = [iv for iv in list_a if iv.dimension == dimension]
        sub_b = [iv for iv in list_b if iv.dimension == dimension]
        return _bottleneck_single_dimension(sub_a, sub_b)

    dims = {iv.dimension for iv in list_a} | {iv.dimension for iv in list_b}
    if not dims:
        return 0.0
    return max(
        _bottleneck_single_dimension(
            [iv for iv in list_a if iv.dimension == d],
            [iv for iv in list_b if iv.dimension == d],
        )
        for d in dims
    )
