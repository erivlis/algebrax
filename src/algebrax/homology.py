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
from collections.abc import Iterable, Iterator, Mapping
from itertools import combinations
from typing import Any, Generic, Literal, NamedTuple, TypeAlias

from algebrax.semiring import Semiring
from algebrax.typing import K, SparseMatrix, SparseVector, V

__all__ = [
    'Cochain',
    'DiscreteForm',
    'HodgeDecomposition',
    'SimplicialComplex',
    'SparseChainComplex',
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
        if f_uv != 0.0 and f_vu != 0.0 and math.isclose(f_uv, -f_vu, rel_tol=1e-9, abs_tol=max(tol, 1e-12)):
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
            if w_val != 0.0:
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

    res: SparseMatrix = {}
    for face, row in d_k.items():
        w_km1 = float(dual_weights_km1.get(face, 1.0)) if dual_weights_km1 is not None else 1.0
        if w_km1 == 0.0:  # NOSONAR - exact zero singularity guard
            continue
        scaled_row = {}
        for simplex, val in row.items():
            w_k = float(dual_weights_k.get(simplex, 1.0)) if dual_weights_k is not None else 1.0
            scaled = float(val) * (w_k / w_km1)
            if scaled != 0.0:
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
