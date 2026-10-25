"""
Topological Data Analysis & Homology.

Summary:
    Counts connected components (beta_0) and multidimensional holes (beta_1, beta_2)
    in point clouds, meshes, and graph structures using boundary matrices and Hodge Laplacians.

This module provides tools for constructing simplicial complexes, computing boundary matrices,
evaluating Betti numbers beta_k, and conducting topological data analysis.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Mapping, Sequence
from itertools import combinations
from typing import Any, Generic, Literal, NamedTuple, TypeAlias

from algebrax.semiring import Semiring
from algebrax.typing import K, SparseMatrix, SparseVector, V

__all__ = [
    'CellularSheaf',
    'Cochain',
    'DiscreteForm',
    'EdgeStalkCoord',
    'FilteredSimplicialComplex',
    'HodgeDecomposition',
    'PersistenceInterval',
    'RestrictionMap',
    'SimplicialComplex',
    'SparseChainComplex',
    'StalkCoord',
    'betti_curve',
    'bottleneck_distance',
    'canonicalize_form',
    'coboundary',
    'cochain_to_flow',
    'codifferential',
    'cohomology_rank',
    'exterior_derivative',
    'flow_to_cochain',
    'helmholtz_hodge_decomposition',
    'hodge_laplacian',
    'hodge_star',
    'persistence_entropy',
    'persistent_homology',
    'sheaf_diffusion',
    'sheaf_harmonic_extension',
    'sheaf_laplacian',
]


def _count_inversions_and_sort(s: tuple[K, ...], oriented: bool) -> tuple[tuple[K, ...], int]:
    n = len(s)
    try:
        inversions = 0
        if oriented:
            for i in range(n):
                s_i = s[i]
                for j in range(i + 1, n):
                    if s_i > s[j]:  # type: ignore[operator]
                        inversions += 1
        return tuple(sorted(s)), (-1 if (inversions % 2 == 1) else 1)  # type: ignore[type-var]
    except TypeError:
        keyed = [((str(type(x)), str(x)), x) for x in s]
        inversions = 0
        if oriented:
            for i in range(n):
                k_i = keyed[i][0]
                for j in range(i + 1, n):
                    if k_i > keyed[j][0]:
                        inversions += 1
        keyed.sort(key=lambda item: item[0])
        return tuple(item[1] for item in keyed), (-1 if (inversions % 2 == 1) else 1)


def _canonicalize_simplex(
    simplex: Iterable[K],
    oriented: bool = True,
) -> tuple[tuple[K, ...], int]:
    """Return `(canonical_sorted_simplex, parity_sign)` where `parity_sign` is 0 if degenerate."""
    s = tuple(simplex)
    n = len(s)
    if n <= 1:
        return s, 1
    if len(set(s)) < n:
        return s, 0
    return _count_inversions_and_sort(s, oriented)


def _is_non_zero(val: Any, tol: float) -> bool:
    if isinstance(val, (int, float, complex)) and not isinstance(val, bool):
        return (abs(val) > tol) if tol > 0.0 else (val != 0)
    return bool(val)


def _resolve_bidirectional_edge_flux(
    f_uv: float,
    f_vu: float,
    mode: Literal['auto', 'net', 'half_skew'],
    tol: float,
) -> float:
    if mode == 'half_skew':
        return 0.5 * (f_uv - f_vu)
    if mode == 'net':
        return f_uv - f_vu
    if mode == 'auto':
        if (
            f_uv != 0.0
            and f_vu != 0.0  # NOSONAR - exact sentinel presence check
            and math.isclose(f_uv, -f_vu, rel_tol=1e-9, abs_tol=max(tol, 1e-12))
        ):
            return f_uv
        return f_uv - f_vu
    raise ValueError(f"Unknown mode '{mode}'. Expected 'auto', 'net', or 'half_skew'.")


class Cochain(Mapping[tuple[K, ...], V], Generic[K, V]):
    r"""Alternating discrete differential k-form / cochain over oriented simplices.

    Algebraic Signature:
        $\omega \in C^k(K; R), \quad
        \omega(v_{\pi(0)}, \dots, v_{\pi(k)}) = \operatorname{sgn}(\pi)\,\omega(v_0, \dots, v_k)$

    Carrier:
        `Mapping[tuple[K, ...], V]` (Immutable sparse mapping over canonical simplices $v_0 < v_1 < \dots < v_k$).

    Operations:
        - Orientation Lookup (`__getitem__`, `get`): Evaluates $\omega(\sigma)$ for any vertex permutation $\sigma$,
          returning $\operatorname{sgn}(\pi)\,\omega(\sigma_{\text{sorted}})$ and $0$ on degenerate simplices.
        - Vector Space Arithmetic (`+`, `-`, `*`, unary `-`): Linear combinations in $C^k(K; R)$.
        - Chain Pairing (`eval`): Bilinear Kronecker pairing
          $\langle \omega, c \rangle = \sum_{\sigma} \omega(\sigma) c(\sigma)$.
        - Flow & Node Bridges (`from_flow`, `to_flow`, `from_nodes`, `to_nodes`): Lossless conversion between
          graph adjacency edge flows (`SparseMatrix`), node scalar fields (`SparseVector`), and cochains.

    Properties:
        Alternating antisymmetry, degenerate simplex annihilation ($\omega(\dots, u, \dots, u, \dots) = 0$),
        full compatibility with `SparseVector` (`Mapping[tuple[K, ...], V]`).

    Applications:
        Discrete Exterior Calculus (DEC), Helmholtz-Hodge flow decomposition, simplicial cohomology,
        conservative vs. rotational network flow analysis.
    """

    def __init__(
        self,
        data: Mapping[tuple[K, ...], V] | Iterable[tuple[tuple[K, ...], V]] | None = None,
        *,
        degree: int | None = None,
        oriented: bool = True,
        tol: float = 1e-14,
    ) -> None:
        self._oriented = oriented
        self._tol = tol
        self._data: dict[tuple[K, ...], V] = {}

        if data is not None:
            items = data.items() if isinstance(data, Mapping) else data
            for raw_simplex, raw_val in items:
                if not isinstance(raw_simplex, tuple):
                    raw_simplex = tuple(raw_simplex)
                if degree is not None and len(raw_simplex) != degree + 1:
                    raise ValueError(
                        f'Simplex {raw_simplex} has dimension {len(raw_simplex) - 1}, expected degree {degree}.'
                    )
                canon, sign = _canonicalize_simplex(raw_simplex, oriented=oriented)
                if sign == 0:
                    continue
                signed_val: V = -raw_val if sign == -1 else raw_val  # type: ignore[operator]
                prev = self._data.get(canon)
                combined = (prev + signed_val) if prev is not None else signed_val  # type: ignore[operator]
                if _is_non_zero(combined, tol):
                    self._data[canon] = combined
                else:
                    self._data.pop(canon, None)

        if degree is not None:
            self._degree: int | None = degree
        elif self._data:
            lengths = {len(s) - 1 for s in self._data}
            self._degree = next(iter(lengths)) if len(lengths) == 1 else None
        else:
            self._degree = None

    @property
    def degree(self) -> int | None:
        """Simplicial degree k of the cochain (where simplices are (k+1)-tuples), or None if empty/mixed."""
        return self._degree

    @property
    def oriented(self) -> bool:
        """Whether simplex permutation parity flips the sign of coefficients."""
        return self._oriented

    def __getitem__(self, simplex: tuple[K, ...]) -> V:
        if not isinstance(simplex, tuple):
            raise KeyError(simplex)
        canon, sign = _canonicalize_simplex(simplex, oriented=self._oriented)
        if sign == 0 or canon not in self._data:
            raise KeyError(simplex)
        val = self._data[canon]
        return -val if sign == -1 else val  # type: ignore[operator]

    def get(self, key: tuple[K, ...], default: Any = None) -> Any:
        if not isinstance(key, tuple):
            return default
        canon, sign = _canonicalize_simplex(key, oriented=self._oriented)
        if sign == 0:
            return 0.0 if default is None else default
        if canon not in self._data:
            return default
        val = self._data[canon]
        return -val if sign == -1 else val  # type: ignore[operator]

    def __iter__(self) -> Iterator[tuple[K, ...]]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def _data_matches(self, other_data: dict[tuple[K, ...], V], cmp_tol: float) -> bool:
        if self._data.keys() != other_data.keys():
            return False
        for k, v1 in self._data.items():
            v2 = other_data[k]
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                if not math.isclose(float(v1), float(v2), rel_tol=cmp_tol, abs_tol=cmp_tol):
                    return False
            elif v1 != v2:
                return False
        return True

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Cochain):
            if self._oriented != other._oriented:
                return False
            cmp_tol = max(self._tol, other._tol, 1e-12) if (self._tol > 0 or other._tol > 0) else 0.0
            return self._data_matches(other._data, cmp_tol)
        if isinstance(other, Mapping):
            try:
                other_cochain = Cochain(other, oriented=self._oriented, tol=self._tol)
            except (TypeError, ValueError):
                return False
            cmp_tol = max(self._tol, 1e-12) if self._tol > 0 else 0.0
            return self._data_matches(other_cochain._data, cmp_tol)
        return NotImplemented

    def __add__(self, other: Mapping[tuple[K, ...], V]) -> Cochain[K, V]:
        if not isinstance(other, Mapping):
            return NotImplemented
        other_c = other if isinstance(other, Cochain) else Cochain(other, oriented=self._oriented, tol=self._tol)
        merged: dict[tuple[K, ...], V] = dict(self._data)
        for s, val in other_c._data.items():
            merged[s] = (merged[s] + val) if s in merged else val  # type: ignore[operator]
        deg = self._degree if self._degree == other_c._degree else None
        return Cochain(merged, degree=deg, oriented=self._oriented, tol=self._tol)

    def __sub__(self, other: Mapping[tuple[K, ...], V]) -> Cochain[K, V]:
        if not isinstance(other, Mapping):
            return NotImplemented
        other_c = other if isinstance(other, Cochain) else Cochain(other, oriented=self._oriented, tol=self._tol)
        merged: dict[tuple[K, ...], V] = dict(self._data)
        for s, val in other_c._data.items():
            merged[s] = (merged[s] - val) if s in merged else (-val)  # type: ignore[operator]
        deg = self._degree if self._degree == other_c._degree else None
        return Cochain(merged, degree=deg, oriented=self._oriented, tol=self._tol)

    def __neg__(self) -> Cochain[K, V]:
        neg_data = {s: -val for s, val in self._data.items()}  # type: ignore[operator]
        return Cochain(neg_data, degree=self._degree, oriented=self._oriented, tol=self._tol)

    def __mul__(self, scalar: V) -> Cochain[K, V]:
        if isinstance(scalar, Mapping):
            return NotImplemented
        scaled = {s: val * scalar for s, val in self._data.items()}  # type: ignore[operator]
        return Cochain(scaled, degree=self._degree, oriented=self._oriented, tol=self._tol)

    def __rmul__(self, scalar: V) -> Cochain[K, V]:
        if isinstance(scalar, Mapping):
            return NotImplemented
        scaled = {s: scalar * val for s, val in self._data.items()}  # type: ignore[operator]
        return Cochain(scaled, degree=self._degree, oriented=self._oriented, tol=self._tol)

    def eval(self, chain: Mapping[tuple[K, ...], V]) -> V:
        r"""Evaluate bilinear Kronecker pairing $\langle \omega, c \rangle = \sum_\sigma \omega(\sigma) c_\sigma$."""
        total: Any = 0.0
        for simplex, coeff in chain.items():
            w_val = self.get(simplex, 0.0)
            if w_val != 0.0:  # NOSONAR - exact zero multiplier shortcut
                total += w_val * coeff
        return total  # type: ignore[return-value]

    @classmethod
    def from_nodes(
        cls,
        field: SparseVector[K, V],
        *,
        tol: float = 1e-14,
    ) -> Cochain[K, V]:
        """Lift a 0-form vertex signal `{u: val}` to a 0-cochain `{(u,): val}`."""
        return cls({(u,): val for u, val in field.items()}, degree=0, oriented=True, tol=tol)

    def to_nodes(self) -> dict[K, V]:
        """Project a 0-cochain `{(u,): val}` back to a vertex dictionary `{u: val}`."""
        res: dict[K, V] = {}
        for s, val in self._data.items():
            if len(s) != 1:
                raise ValueError(f'to_nodes requires a 0-cochain (1-tuple simplices), got simplex {s}.')
            res[s[0]] = val
        return res

    @classmethod
    def from_flow(
        cls,
        flow: SparseMatrix[K, float],
        *,
        mode: Literal['auto', 'net', 'half_skew'] = 'auto',
        tol: float = 1e-14,
    ) -> Cochain[K, float]:
        r"""Project a nested adjacency edge-flow matrix onto a canonically oriented 1-cochain.

        Args:
            flow: Nested mapping `u -> {v: flux}` representing directed edge signals.
            mode: Reduction rule when both `(u, v)` and `(v, u)` exist (`u < v`):
                - `'auto'` (default): Preserves $F_{uv}$ if $F_{vu} = -F_{uv}$ (skew-symmetric),
                  otherwise computes net flux $F_{uv} - F_{vu}$.
                - `'net'`: Always computes net flux $F_{uv} - F_{vu}$.
                - `'half_skew'`: Computes the skew-symmetric projection $\frac{1}{2}(F_{uv} - F_{vu})$.
            tol: Magnitude threshold for pruning zero edge flows.

        Returns:
            A degree-1 `Cochain[K, float]`.
        """
        if mode not in ('auto', 'net', 'half_skew'):
            raise ValueError(f"Unknown mode '{mode}'. Expected 'auto', 'net', or 'half_skew'.")

        canonical_edges: set[tuple[K, K]] = set()
        for u, row in flow.items():
            for v in row:
                if u != v:
                    canon, sign = _canonicalize_simplex((u, v), oriented=True)
                    if sign != 0:
                        canonical_edges.add((canon[0], canon[1]))

        cochain_data: dict[tuple[K, ...], float] = {}
        for u, v in canonical_edges:
            f_uv = float(flow.get(u, {}).get(v, 0.0))
            f_vu = float(flow.get(v, {}).get(u, 0.0))
            val = _resolve_bidirectional_edge_flux(f_uv, f_vu, mode, tol)
            if abs(val) > tol:
                cochain_data[(u, v)] = val

        return cls(cochain_data, degree=1, oriented=True, tol=tol)

    def to_flow(
        self,
        *,
        skew_symmetric: bool = True,
        tol: float = 1e-14,
    ) -> dict[K, dict[K, float]]:
        r"""Lift a 1-cochain $\omega \in C^1(K; \mathbb{R})$ to a nested adjacency flow matrix.

        Args:
            skew_symmetric: If True, populates both $F_{uv} = \omega((u, v))$ and $F_{vu} = -\omega((u, v))$.
                If False, populates only the positive-flux direction.
            tol: Magnitude threshold for pruning near-zero flows.

        Returns:
            Nested dictionary `u -> {v: flux}`.
        """
        res: dict[K, dict[K, float]] = {}
        for s, raw_val in self._data.items():
            if len(s) != 2:
                raise ValueError(f'to_flow requires a 1-cochain (2-tuple simplices), got simplex {s}.')
            val = float(raw_val)  # type: ignore[arg-type]
            if abs(val) <= tol:
                continue
            u, v = s[0], s[1]
            if skew_symmetric:
                res.setdefault(u, {})[v] = val
                res.setdefault(v, {})[u] = -val
            elif val > 0.0:
                res.setdefault(u, {})[v] = val
            else:
                res.setdefault(v, {})[u] = -val
        return res

    def __repr__(self) -> str:
        deg_str = f', degree={self._degree}' if self._degree is not None else ''
        return f'Cochain({self._data!r}{deg_str})'

    def _repr_latex_(self) -> str:
        deg = self._degree if self._degree is not None else 'k'
        return f'$$\\omega \\in C^{{{deg}}}(K), \\; |\\mathrm{{supp}}(\\omega)| = {len(self._data)}$$'


def flow_to_cochain(
    flow: SparseMatrix[K, float],
    *,
    mode: Literal['auto', 'net', 'half_skew'] = 'auto',
    tol: float = 1e-14,
) -> Cochain[K, float]:
    """Project a nested adjacency edge-flow matrix onto a canonically oriented 1-cochain."""
    return Cochain.from_flow(flow, mode=mode, tol=tol)


def cochain_to_flow(
    cochain: Mapping[tuple[K, ...], float],
    *,
    skew_symmetric: bool = True,
    tol: float = 1e-14,
) -> dict[K, dict[K, float]]:
    """Lift a 1-cochain mapping to a nested adjacency edge-flow matrix."""
    c = cochain if isinstance(cochain, Cochain) else Cochain(cochain, degree=1, tol=tol)
    return c.to_flow(skew_symmetric=skew_symmetric, tol=tol)


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


def coboundary(complex: SparseChainComplex, k: int) -> SparseMatrix:
    """
    Compute the k-th coboundary operator d^k = D_{k+1}^T : C^k -> C^{k+1}.

    Args:
        complex: SparseChainComplex or SimplicialComplex instance.
        k: Dimension index k.

    Returns:
        Sparse matrix representation of the coboundary operator d^k.

    Example:
        >>> sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
        >>> d0 = coboundary(sc, 0)
        >>> isinstance(d0, dict)
        True
    """
    from algebrax.matrix.core import transpose

    d_k1 = complex.boundary_matrices.get(k + 1, {})
    return transpose(d_k1)


def cohomology_rank(complex: SparseChainComplex, k: int) -> int:
    """
    Compute the k-th cohomology group rank dim(H^k).

    Args:
        complex: SparseChainComplex or SimplicialComplex instance.
        k: Dimension index k.

    Returns:
        The k-th cohomology rank.

    Example:
        >>> sc = SimplicialComplex([(0, 1), (1, 2), (0, 2)])
        >>> cohomology_rank(sc, 1)
        1
    """
    if isinstance(complex, SimplicialComplex):
        return complex.betti_numbers(k).get(k, 0)

    d_k = complex.boundary_matrices.get(k, {})
    d_k1 = complex.boundary_matrices.get(k + 1, {})

    rank_dk = _matrix_rank(d_k)
    rank_dk1 = _matrix_rank(d_k1)

    num_k = len({c for row in d_k.values() for c in row}) if d_k else 0
    if not num_k and d_k1:
        num_k = len(d_k1)

    return max(num_k - rank_dk - rank_dk1, 0)


DiscreteForm: TypeAlias = Cochain[int, float]


class HodgeDecomposition(NamedTuple):
    r"""Orthogonal Helmholtz-Hodge decomposition of a discrete 1-form $\omega = d\alpha + \delta\beta + \gamma$.

    Attributes:
        exact: Curl-free gradient flow $d_0 \alpha \in \operatorname{im}(d_0)$.
        coexact: Divergence-free solenoidal circulation $\delta_2 \beta \in \operatorname{im}(\delta_2)$.
        harmonic: Topological harmonic circulation $\gamma \in \ker(\Delta_1) \cong H^1(K; \mathbb{R})$.
        potential: Node scalar potential 0-cochain $\alpha \in C^0(K; \mathbb{R})$ such that `exact = d_0(alpha)`.
        stream: Triangle curl stream 2-cochain $\beta \in C^2(K; \mathbb{R})$ such that `coexact = delta_2(beta)`.
    """

    exact: Cochain[int, float]
    coexact: Cochain[int, float]
    harmonic: Cochain[int, float]
    potential: Cochain[int, float]
    stream: Cochain[int, float]


def exterior_derivative(complex: SparseChainComplex, k: int) -> SparseMatrix:
    r"""Construct the discrete exterior derivative operator $d_k: \Omega^k(K) \to \Omega^{k+1}(K)$.

    Algebraic Signature:
        $\langle d_k \omega, \sigma_{k+1} \rangle = \langle \omega, \partial_{k+1} \sigma_{k+1} \rangle
        \implies d_k = \partial_{k+1}^T$

    Carrier:
        `SparseMatrix[Simplex, float]` (Incidence matrix mapping $k$-simplices to $(k+1)$-simplices).

    Operations:
        - Boundary Transpose: Transposes the $(k+1)$-th boundary operator $D_{k+1}$.

    Properties:
        Satisfies exact cochain nilpotency $d_{k+1} \circ d_k = 0$.

    Applications:
        - Discrete gradient ($d_0$), discrete curl ($d_1$), and higher exterior derivatives.
        - Simplicial cohomology and Helmholtz-Hodge decomposition.

    Args:
        complex: `SimplicialComplex` or `SparseChainComplex` instance.
        k: Cochain degree $k \ge 0$.

    Returns:
        Sparse matrix representation of $d_k$.
    """
    return coboundary(complex, k)


def codifferential(
    complex: SparseChainComplex,
    k: int,
    dual_weights_k: Mapping[tuple[int, ...], float] | None = None,
    dual_weights_km1: Mapping[tuple[int, ...], float] | None = None,
) -> SparseMatrix:
    r"""Construct the discrete codifferential operator $\delta_k = d_{k-1}^*: \Omega^k(K) \to \Omega^{k-1}(K)$.

    Algebraic Signature:
        $\delta_k = \star_{k-1}^{-1} \circ \partial_k \circ \star_k$
        (reduces to $\partial_k$ under combinatorial unit Hodge star weights).

    Carrier:
        `SparseMatrix[Simplex, float]` (Matrix mapping $k$-simplices to $(k-1)$-simplices).

    Operations:
        - Adjoint Projection: Scales columns by $\star_k$ and rows by $\star_{k-1}^{-1}$ on $D_k$.

    Properties:
        Satisfies nilpotency $\delta_{k-1} \circ \delta_k = 0$ and formal adjointness
        $\langle d_{k-1} \alpha, \beta \rangle = \langle \alpha, \delta_k \beta \rangle$.

    Applications:
        - Discrete divergence ($\delta_1$) of edge flows and rotational coexact flux ($\delta_2$) from 2-simplices.

    Args:
        complex: `SimplicialComplex` or `SparseChainComplex` instance.
        k: Cochain degree $k \ge 1$.
        dual_weights_k: Optional positive Hodge star weights on $k$-simplices.
        dual_weights_km1: Optional positive Hodge star weights on $(k-1)$-simplices.

    Returns:
        Sparse matrix representation of $\delta_k$.
    """
    d_k = complex.boundary_matrices.get(k, {})
    if not d_k:
        return {}
    if dual_weights_k is None and dual_weights_km1 is None:
        return {r: dict(row) for r, row in d_k.items()}

    res = {}
    for face, row in d_k.items():
        w_km1 = float(dual_weights_km1.get(face, 1.0)) if dual_weights_km1 is not None else 1.0
        if w_km1 == 0.0:  # NOSONAR - exact zero singularity guard
            continue
        scaled_row = {}
        for simplex, val in row.items():
            w_k = float(dual_weights_k.get(simplex, 1.0)) if dual_weights_k is not None else 1.0
            scaled = float(val) * (w_k / w_km1)
            if scaled != 0.0:  # NOSONAR - structural sparse zero pruning
                scaled_row[simplex] = scaled
        if scaled_row:
            res[face] = scaled_row
    return res


def hodge_star(
    form: Cochain[K, float] | Mapping[tuple[K, ...], float],
    dual_weights: Mapping[tuple[K, ...], float] | None = None,
    *,
    inverse: bool = False,
    tol: float = 1e-14,
) -> Cochain[K, float]:
    r"""Apply the diagonal discrete Hodge star operator $\star_k$ (or $\star_k^{-1}$) to a $k$-cochain.

    Algebraic Signature:
        $(\star_k \omega)(\sigma) = \frac{|\sigma^\star|}{|\sigma|} \omega(\sigma) = w_\sigma \omega(\sigma)$

    Carrier:
        `Cochain[K, float]` (Metric-weighted dual cochain indexed by primal simplices).

    Operations:
        - Diagonal Volume Scaling: Multiplies (or divides when `inverse=True`) each simplex coefficient
          by its dual-to-primal volume ratio $w_\sigma$ (defaulting to combinatorial identity $w_\sigma = 1$).

    Properties:
        Defines the discrete $L^2$ inner product
        $\langle \alpha, \beta \rangle_\star = \langle \alpha, \star \beta \rangle$.

    Applications:
        - Geometric weighting of circumcentric Voronoi dual meshes in Discrete Exterior Calculus.

    Args:
        form: Input `Cochain` or simplex-keyed dictionary.
        dual_weights: Optional mapping from canonical simplices to positive metric weights $w_\sigma > 0$.
        inverse: If True, divides by $w_\sigma$ to apply $\star_k^{-1}$.
        tol: Numerical pruning threshold.

    Returns:
        Weighted `Cochain[K, float]`.
    """
    c = form if isinstance(form, Cochain) else Cochain(form, tol=tol)
    if dual_weights is None:
        return c

    weights_c = Cochain(dual_weights, oriented=False, tol=0.0)
    scaled: dict[tuple[K, ...], float] = {}
    for s, val in c.items():
        w = float(weights_c.get(s, 1.0))
        if w <= 0.0:
            raise ValueError(f'Hodge star dual weight for simplex {s} must be positive, got {w}.')
        scaled[s] = (float(val) / w) if inverse else (float(val) * w)
    return Cochain(scaled, degree=c.degree, oriented=c.oriented, tol=tol)


def hodge_laplacian(
    complex: SparseChainComplex,
    k: int,
    semiring: Semiring[V] | type[Semiring[V]] | None = None,
) -> SparseMatrix:
    r"""Construct the $k$-th discrete Hodge Laplacian operator $\Delta_k = d_{k-1} \delta_k + \delta_{k+1} d_k$.

    Algebraic Signature:
        $\Delta_k = \partial_k^T \partial_k + \partial_{k+1} \partial_{k+1}^T : \Omega^k(K) \to \Omega^k(K)$

    Carrier:
        `SparseMatrix[Simplex, float]` (Symmetric positive semi-definite operator on $k$-cochains).

    Operations:
        - Down-Laplacian Assembly: Computes $\Delta_k^{\text{down}} = \partial_k^T \partial_k$.
        - Up-Laplacian Assembly: Computes $\Delta_k^{\text{up}} = \partial_{k+1} \partial_{k+1}^T$.

    Properties:
        $\ker(\Delta_k) = \ker(d_k) \cap \ker(\delta_k) \cong H^k(K; \mathbb{R})$ (Discrete Hodge Theorem).

    Applications:
        - Harmonic form extraction, edge flow diffusion, and higher-order spectral clustering.

    Args:
        complex: `SimplicialComplex` or `SparseChainComplex` instance.
        k: Cochain dimension $k \ge 0$.
        semiring: Optional semiring for generalized algebraic Laplacians.

    Returns:
        Sparse matrix representation of $\Delta_k$.
    """
    return complex.hodge_laplacian(k, semiring=semiring)


def canonicalize_form(
    flow: Mapping[tuple[K, ...], float],
    *,
    tol: float = 1e-14,
) -> Cochain[K, float]:
    r"""Normalize simplex orientations into an alternating `Cochain`, flipping sign on odd parity swaps.

    Args:
        flow: Mapping from simplex vertex tuples to float coefficients.
        tol: Numerical pruning threshold.

    Returns:
        Orientation-canonicalized `Cochain[K, float]`.
    """
    return flow if isinstance(flow, Cochain) else Cochain(flow, tol=tol)


def _normalize_hodge_input(
    flow: Cochain[int, float] | Mapping[tuple[int, ...], float] | SparseMatrix[int, float],
    tol: float,
) -> Cochain[int, float]:
    if isinstance(flow, Cochain):
        return flow
    if not flow:
        return Cochain(degree=1, tol=tol)
    first_key = next(iter(flow))
    if isinstance(first_key, tuple):
        return Cochain(flow, degree=1, tol=tol)  # type: ignore[arg-type]
    return Cochain.from_flow(flow, tol=tol)  # type: ignore[arg-type]


def helmholtz_hodge_decomposition(
    complex: SimplicialComplex,
    flow: Cochain[int, float] | Mapping[tuple[int, ...], float] | SparseMatrix[int, float],
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> HodgeDecomposition:
    r"""Decompose a discrete 1-form (edge flow) into orthogonal exact, coexact, and harmonic components.

    Algebraic Signature:
        $\omega = d_0 \alpha + \delta_2 \beta + \gamma \in
        \operatorname{im}(d_0) \oplus \operatorname{im}(\delta_2) \oplus \ker(\Delta_1)$

    Carrier:
        `HodgeDecomposition(exact, coexact, harmonic, potential, stream)` where each component is a `Cochain`.

    Operations:
        - Exact Potential Projection: Solves $\Delta_0 \alpha = \partial_1 \omega$ via deflated `cg_solve`
          and evaluates $\omega_{\text{exact}} = d_0 \alpha = \partial_1^T \alpha$.
        - Coexact Curl Projection: Solves $\Delta_2^{\text{down}} \beta = d_1 \omega = \partial_2^T \omega$
          via `cg_solve` and evaluates $\omega_{\text{coexact}} = \delta_2 \beta = \partial_2 \beta$.
        - Harmonic Residual Extraction: Computes $\gamma = \omega - \omega_{\text{exact}} - \omega_{\text{coexact}}$.

    Properties:
        Mutually $L^2$-orthogonal decomposition satisfying
        $\langle d_0 \alpha, \delta_2 \beta \rangle = \langle d_0 \alpha, \gamma \rangle =
        \langle \delta_2 \beta, \gamma \rangle = 0$, with $d_1(d_0 \alpha) = 0$, $\delta_1(\delta_2 \beta) = 0$,
        and $\Delta_1 \gamma = 0$.

    Applications:
        - HodgeRank global ranking and cyclic inconsistency detection in pairwise comparisons.
        - Financial currency and DeFi triangular vs. global cycle arbitrage isolation.
        - Traffic engineering and fluid vortex separation on meshes.

    Args:
        complex: `SimplicialComplex` defining vertices (0-simplices), edges (1-simplices), and triangles (2-simplices).
        flow: Input 1-form supplied either as a `Cochain`, a tuple-keyed dict `{(u, v): val}`,
            or a nested adjacency matrix `{u: {v: val}}`.
        tol: Conjugate gradient convergence tolerance (default `1e-9`).
        max_iter: Maximum conjugate gradient iterations (default `1000`).

    Returns:
        `HodgeDecomposition` containing `(exact, coexact, harmonic, potential, stream)`.
    """
    from algebrax.matrix.core import cg_solve, dot, mat_vec, transpose

    clean_tol = max(tol * 10.0, 1e-11)
    omega = _normalize_hodge_input(flow, tol=clean_tol)

    # 1. Exact component: Delta_0 alpha = partial_1 omega, exact = d_0 alpha
    b1 = complex.boundary_matrices.get(1, {})
    d0 = transpose(b1)
    delta0 = dot(b1, d0)

    div_flow = mat_vec(b1, omega)
    alpha_raw = cg_solve(delta0, div_flow, tol=tol, max_iter=max_iter, project_nullspace=True)
    potential = Cochain(alpha_raw, degree=0, tol=clean_tol)
    exact = Cochain(mat_vec(d0, potential), degree=1, tol=clean_tol)

    # 2. Coexact component: (partial_2^T partial_2) beta = partial_2^T omega, coexact = partial_2 beta
    coexact: Cochain[int, float] = Cochain(degree=1, tol=clean_tol)
    stream: Cochain[int, float] = Cochain(degree=2, tol=clean_tol)
    b2 = complex.boundary_matrices.get(2)
    if b2:
        d1 = transpose(b2)
        delta2 = dot(d1, b2)
        curl_flow = mat_vec(d1, omega)
        beta_raw = cg_solve(delta2, curl_flow, tol=tol, max_iter=max_iter, project_nullspace=False)
        stream = Cochain(beta_raw, degree=2, tol=clean_tol)
        coexact = Cochain(mat_vec(b2, stream), degree=1, tol=clean_tol)

    # 3. Harmonic component: gamma = omega - exact - coexact
    harmonic_raw = omega - exact - coexact
    harmonic = Cochain(dict(harmonic_raw), degree=1, tol=clean_tol)

    return HodgeDecomposition(
        exact=exact,
        coexact=coexact,
        harmonic=harmonic,
        potential=potential,
        stream=stream,
    )


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
        - Coboundary Assembly ($\delta_{\mathcal{F}}$): Local difference $(\delta_{\mathcal{F}} x)_{e=(u, v)} =
          \rho_{v \trianglelefteq e} x_v - \rho_{u \trianglelefteq e} x_u$.
        - Sheaf Laplacian ($L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$): Positive semi-definite
          block-structured operator over product stalk keys `(v, i)`.
        - Sheaf Cohomology: Global sections dimension $\dim H^0(G; \mathcal{F}) = \dim \ker L_{\mathcal{F}}$.
        - Dirichlet Energy: $E_{\mathcal{F}}(x) = \frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2 =
          \frac{1}{2} \langle x, L_{\mathcal{F}} x \rangle$.

    Properties:
        - Self-Adjoint Hodge Structure: $L_{\mathcal{F}}$ is symmetric positive semi-definite.
        - Orientation Invariance: $L_{\mathcal{F}}$ and $E_{\mathcal{F}}(x)$ are invariant under
          edge orientation choice.
        - Strict Generalization: For constant sheaf with $d_v = d_e = 1$ and $\rho = [1.0]$,
          $L_{\mathcal{F}}$ reduces identically to the combinatorial graph Laplacian $L_0 = D - W$.

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

        For each undirected edge (u, v) with symmetric weight w > 0, the restriction maps are assigned
        as rho_{u trianglelefteq e} = rho_{v trianglelefteq e} = sqrt(w) * I_{stalk_dim}.
        Consequently, the resulting Sheaf Laplacian matches the combinatorial graph Laplacian L = D - W.

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
        r"""Compute the space of global sections dimension $\dim H^0(G; \mathcal{F}) = \dim \ker L_{\mathcal{F}}$.

        Args:
            tol: Numerical tolerance for rank computation.

        Returns:
            Dimension of the 0-th sheaf cohomology group $H^0(G; \mathcal{F})$.
        """
        total_dim = sum(self.vertex_stalks.values())
        if total_dim == 0:
            return 0
        delta = self.coboundary_matrix()
        if not delta:
            return total_dim
        rank_delta = _matrix_rank(delta)
        return max(total_dim - rank_delta, 0)


def sheaf_laplacian(sheaf: CellularSheaf) -> SparseMatrix[StalkCoord, float]:
    r"""Return the sparse Sheaf Laplacian matrix $L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$.

    Args:
        sheaf: Input `CellularSheaf` instance.

    Returns:
        Sparse matrix representation of $L_{\mathcal{F}}$.
    """
    return sheaf.laplacian_matrix()


def sheaf_diffusion(
    sheaf: CellularSheaf,
    initial_state: SparseVector[StalkCoord, float],
    steps: int = 20,
    tau: float = 0.1,
) -> dict[StalkCoord, float]:
    r"""Simulate discrete-time sheaf heat diffusion $x^{(t+1)} = (I - \tau L_{\mathcal{F}}) x^{(t)}$.

    Diffusion under the Sheaf Laplacian models consensus dynamics with heterogeneous transformations
    and opinions. If a non-trivial space of global sections exists ($H^0(G; \mathcal{F}) \ne \{0\}$),
    states converge to the nearest harmonic section; on frustrated bundles, states decay to zero.

    Args:
        sheaf: Input `CellularSheaf` instance.
        initial_state: Initial 0-cochain mapping `(vertex, dim_idx)` to float values.
        steps: Number of forward Euler diffusion steps (default 20).
        tau: Step size parameter (default 0.1).

    Returns:
        Diffused 0-cochain dictionary.
    """
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
    r"""Compute harmonic 0-cochain minimizing Dirichlet energy clamped on boundary.

    Solves the discrete Dirichlet boundary value problem on the cellular sheaf:
    $(L_{\mathcal{F}} x)_u = 0$ for all interior vertices $u \in V \setminus B$,
    subject to $x|_B = \text{boundary\_values}$.

    Algebraic Signature:
        $\arg\min_{x \in C^0(G; \mathcal{F}), \, x|_B = x_B} \frac{1}{2} \langle x, L_{\mathcal{F}} x \rangle \implies
        L_{UU} x_U = - (L_{\mathcal{F}} x_B)_U$

    Args:
        sheaf: Input `CellularSheaf` instance.
        boundary_values: Prescribed values on boundary stalk coordinates.
        boundary_vertices: Set of vertex keys designated as fixed boundary nodes $B$.
        tol: Conjugate gradient convergence tolerance (default 1e-9).
        max_iter: Maximum conjugate gradient iterations (default 1000).

    Returns:
        Complete 0-cochain dictionary containing both fixed boundary values and solved interior values.
    """
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
        - Persistent Homology (`persistent_homology`): Computes birth-death intervals over $\mathbb{Z}_2$.

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
        r"""Insert a simplex and all its sub-faces, enforcing $f(\tau) \le f(\sigma)$.

        Args:
            simplex: Tuple of integer vertex identifiers.
            filtration: Filtration birth value $f(\sigma) \in \mathbb{R}$.

        Raises:
            ValueError: If `filtration` is `NaN`.
        """
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
        r"""Extract the static subcomplex $K_{\le \text{threshold}} = \{\sigma \mid f(\sigma) \le \text{threshold}\}$.

        Args:
            threshold: Maximum filtration value to include.

        Returns:
            Static `SimplicialComplex` containing all simplices born at or before `threshold`.
        """
        included = [s for s, f_val in self._filtration.items() if f_val <= threshold]
        return SimplicialComplex(included)

    @classmethod
    def from_vietoris_rips(
        cls,
        distance_matrix: SparseMatrix[int, float],
        max_dim: int = 2,
        max_edge_length: float = math.inf,
    ) -> FilteredSimplicialComplex:
        r"""Construct the Vietoris-Rips filtration where $f(\sigma) = \max_{u, v \in \sigma} d(u, v)$.

        Args:
            distance_matrix: Sparse pairwise distance matrix `u -> {v: dist}`.
            max_dim: Maximum simplex dimension $k$ to expand (default `2`).
            max_edge_length: Maximum pairwise distance threshold for edge inclusion (default `math.inf`).

        Returns:
            `FilteredSimplicialComplex` representing the Vietoris-Rips flag filtration.

        Raises:
            ValueError: If `max_dim < 0`.
        """
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
        r"""Construct the lower-star sublevel filtration where $f(\sigma) = \max_{v \in \sigma} h(v)$.

        Args:
            complex: Base `SimplicialComplex`.
            vertex_values: Scalar field mapping vertex IDs to height values $h(v)$.

        Returns:
            `FilteredSimplicialComplex` ordered by sublevel sets of `vertex_values`.
        """
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


def persistent_homology(
    filtration: FilteredSimplicialComplex,
    max_k: int = 2,
    include_zero_persistence: bool = False,
) -> list[PersistenceInterval]:
    r"""Compute the persistence barcode of a `FilteredSimplicialComplex` over $\mathbb{Z}_2$.

    Algebraic Signature:
        $H_k(K_\bullet; \mathbb{F}_2) \cong \bigoplus_{i} \mathbb{F}_2[b_i, d_i)$

    Carrier:
        `list[PersistenceInterval]` sorted by `(dimension, birth, death, birth_simplex)`.

    Operations:
        - Total Filtration Ordering: Sorts simplices by `(f(\sigma), dim(\sigma), \sigma)`.
        - Clearing (Twist) Optimization: Reduces boundary dimensions top-down from `max_k + 1`
          down to `1`, zeroing out boundary columns of simplices already identified as pivot births.
        - Sparse $\mathbb{Z}_2$ Pivot Elimination: Symmetric-difference column reduction `col ^= reduced[piv]`.

    Properties:
        At any threshold $t \in \mathbb{R}$, the count of intervals in dimension $k$ satisfying
        $b_i \le t < d_i$ equals $\beta_k(K_{\le t})$.

    Applications:
        Multiscale topological feature extraction, loop and cavity persistence, topological denoising.

    Args:
        filtration: Input `FilteredSimplicialComplex`.
        max_k: Maximum homology dimension $k$ to compute (default `2`).
        include_zero_persistence: If True, includes ephemeral intervals where `birth == death`.

    Returns:
        List of `PersistenceInterval` records across dimensions `0 <= k <= max_k`.

    Raises:
        ValueError: If `max_k < 0`.
    """
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
                # Clearing optimization: sigma_j is already a pivot boundary -> d(sigma_j) = 0
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

    # Unpaired simplices with empty reduced columns are essential (immortal) classes
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


def betti_curve(
    intervals: Iterable[PersistenceInterval],
    thresholds: Sequence[float],
    dimension: int = 0,
) -> list[int]:
    r"""Evaluate the Betti number $\beta_k(t)$ at each filtration threshold $t \in \text{thresholds}$.

    Algebraic Signature:
        $\beta_k(t) = \left|\{[b_i, d_i) \in \operatorname{Dgm}_k \mid b_i \le t < d_i\}\right|$

    Args:
        intervals: Iterable of `PersistenceInterval` instances.
        thresholds: Sequence of filtration scale parameters $t$.
        dimension: Homological dimension $k$ to filter (default `0`).

    Returns:
        List of integer Betti numbers $\beta_k(t)$ corresponding to `thresholds`.
    """
    dim_intervals = [iv for iv in intervals if iv.dimension == dimension and iv.death > iv.birth]
    return [sum(1 for iv in dim_intervals if iv.birth <= t < iv.death) for t in thresholds]


def persistence_entropy(
    intervals: Iterable[PersistenceInterval],
    dimension: int | None = None,
) -> float:
    r"""Compute the Shannon entropy $H = -\sum_i p_i \ln p_i$ of finite persistence lifespans.

    Algebraic Signature:
        $H(\operatorname{Dgm}) = -\sum_{i} p_i \ln p_i, \quad p_i = \frac{d_i - b_i}{\sum_j (d_j - b_j)}$

    Args:
        intervals: Iterable of `PersistenceInterval` instances.
        dimension: Optional homology dimension $k$ to filter. If `None`, aggregates across all dimensions.

    Returns:
        Non-negative Shannon entropy in nats (`0.0` if no positive finite intervals exist).
    """
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
    r"""Compute the exact $L_\infty$ bottleneck distance $d_B(D_A, D_B)$ between two persistence diagrams.

    Algebraic Signature:
        $d_B(D_A, D_B) = \inf_{\eta: D_A \cup \Delta \leftrightarrow D_B \cup \Delta}
        \sup_{x} \|x - \eta(x)\|_\infty$

    Carrier:
        Non-negative `float` metric distance (`math.inf` when essential Betti counts differ).

    Operations:
        - Diagonal Projection Cost: Evaluates $\|x - \Delta\|_\infty = \frac{d - b}{2}$.
        - Hopcroft-Karp Bisection: Binary searches exact candidate $L_\infty$ thresholds
          over augmented $(m+n) \times (m+n)$ bipartite matchings.

    Properties:
        Satisfies metric non-negativity, identity of indiscernibles (up to zero-persistence points),
        symmetry $d_B(A, B) = d_B(B, A)$, triangle inequality $d_B(A, C) \le d_B(A, B) + d_B(B, C)$,
        and Cohen-Steiner stability $\|D(f) - D(g)\|_B \le \|f - g\|_\infty$.

    Applications:
        Topological stability testing, shape comparison, regime-change detection in time series.

    Args:
        diagram_a: First persistence diagram (`Iterable[PersistenceInterval]`).
        diagram_b: Second persistence diagram (`Iterable[PersistenceInterval]`).
        dimension: Optional homology dimension $k$ to filter. If `None`, computes the maximum
            bottleneck distance across all dimensions present.

    Returns:
        Exact $L_\infty$ bottleneck distance $d_B(D_A, D_B)$.
    """
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
