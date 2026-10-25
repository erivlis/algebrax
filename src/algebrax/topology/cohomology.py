"""Simplicial cohomology, discrete differential k-forms (Cochain), and Alexander-Whitney cup/cap products."""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Generic, Literal, TypeAlias

from algebrax.semiring import Semiring
from algebrax.topology._core import _canonicalize_simplex, _is_non_zero, _matrix_rank
from algebrax.topology.homology import SimplicialComplex, SparseChainComplex
from algebrax.typing import K, SparseMatrix, SparseVector, V

__all__ = [
    'Cochain',
    'DiscreteForm',
    'canonicalize_form',
    'cap_product',
    'coboundary',
    'cochain_to_flow',
    'cohomology_rank',
    'cup_product',
    'flow_to_cochain',
]


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
        - Cochain Ring Product (`cup`, `^`): Alexander-Whitney cup product $\alpha \smile \beta \in C^{p+q}(K; R)$.
        - Chain Pairing (`eval`): Bilinear Kronecker pairing
          $\langle \omega, c \rangle = \sum_{\sigma} \omega(\sigma) c(\sigma)$.
        - Flow & Node Bridges (`from_flow`, `to_flow`, `from_nodes`, `to_nodes`): Lossless conversion between
          graph adjacency edge flows (`SparseMatrix`), node scalar fields (`SparseVector`), and cochains.

    Properties:
        Alternating antisymmetry, degenerate simplex annihilation ($\omega(\dots, u, \dots, u, \dots) = 0$),
        graded-associative cup product, full compatibility with `SparseVector` (`Mapping[tuple[K, ...], V]`).

    Applications:
        Discrete Exterior Calculus (DEC), Helmholtz-Hodge flow decomposition, simplicial cohomology ring,
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

    def cup(
        self,
        other: Cochain[K, V] | Mapping[tuple[K, ...], V],
        *,
        complex: SimplicialComplex | None = None,
        semiring: Semiring[V] | type[Semiring[V]] | None = None,
    ) -> Cochain[K, V]:
        r"""Compute the Alexander-Whitney cup product `self \smile other`."""
        return cup_product(self, other, complex=complex, semiring=semiring, tol=self._tol)

    def __xor__(self, other: Cochain[K, V] | Mapping[tuple[K, ...], V]) -> Cochain[K, V]:
        if not isinstance(other, Mapping):
            return NotImplemented
        return cup_product(self, other, tol=self._tol)

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


DiscreteForm: TypeAlias = Cochain[int, float]


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


def cup_product(
    alpha: Cochain[K, V] | Mapping[tuple[K, ...], V],
    beta: Cochain[K, V] | Mapping[tuple[K, ...], V],
    *,
    complex: SimplicialComplex | None = None,
    semiring: Semiring[V] | type[Semiring[V]] | None = None,
    tol: float = 1e-14,
) -> Cochain[K, V]:
    r"""Compute the Alexander-Whitney cup product $\alpha \smile \beta \in C^{p+q}(K; \mathcal{S})$.

    Algebraic Signature:
        $\smile: C^p(K; \mathcal{S}) \times C^q(K; \mathcal{S}) \to C^{p+q}(K; \mathcal{S}), \quad
        (\alpha \smile \beta)(v_0, \dots, v_{p+q}) =
        \alpha(v_0, \dots, v_p) \otimes_{\mathcal{S}} \beta(v_p, \dots, v_{p+q})$

    Carrier:
        `Cochain[K, V]` of degree $p + q$.

    Operations:
        - Front/Back Pivot Join: Joins canonical $p$-simplices $(v_0 < \dots < v_p)$ with canonical
          $q$-simplices $(v_p < \dots < v_{p+q})$ sharing pivot vertex $v_p$.

    Properties:
        - Associativity: $(\alpha \smile \beta) \smile \gamma = \alpha \smile (\beta \smile \gamma)$.
        - Graded Leibniz Rule: $d(\alpha \smile \beta) = (d\alpha) \smile \beta + (-1)^p \, \alpha \smile (d\beta)$.
        - Semiring Polymorphism: Uses only $\oplus_{\mathcal{S}}$ and $\otimes_{\mathcal{S}}$ on canonically
          ordered simplices.

    Applications:
        Cohomology ring structure $H^*(K; \mathcal{S})$, distinguishing manifolds with identical Betti numbers
        (e.g. $T^2$ vs $S^2 \vee S^1 \vee S^1$), topological intersection numbers.

    Args:
        alpha: Left cochain $\alpha \in C^p(K; \mathcal{S})$.
        beta: Right cochain $\beta \in C^q(K; \mathcal{S})$.
        complex: Optional `SimplicialComplex` restricting support to $(p+q)$-simplices in `complex`.
        semiring: Optional `Semiring` instance or class (defaults to `StandardSemiring`).
        tol: Numerical zero-pruning threshold.

    Returns:
        Cup product `Cochain[K, V]` of degree $p + q$.
    """
    s_inst = Semiring.normalize(semiring)
    c_a = alpha if isinstance(alpha, Cochain) else Cochain(alpha, tol=tol)
    c_b = beta if isinstance(beta, Cochain) else Cochain(beta, tol=tol)
    if c_a.degree is None or c_b.degree is None or not c_a or not c_b:
        deg = (c_a.degree + c_b.degree) if (c_a.degree is not None and c_b.degree is not None) else None
        return Cochain(degree=deg, oriented=c_a.oriented and c_b.oriented, tol=tol)

    p = c_a.degree
    q = c_b.degree
    allowed = complex._simplices.get(p + q) if complex is not None else None

    beta_by_head: dict[K, list[tuple[tuple[K, ...], V]]] = {}
    for s_b, val_b in c_b.items():
        beta_by_head.setdefault(s_b[0], []).append((s_b, val_b))

    out: dict[tuple[K, ...], V] = {}
    for s_a, val_a in c_a.items():
        pivot_v = s_a[-1]
        for s_b, val_b in beta_by_head.get(pivot_v, ()):
            # Because s_a = (v_0 < ... < v_p) and s_b = (v_p < ... < v_{p+q}),
            # merged = (v_0 < ... < v_{p+q}) is strictly increasing with sign +1.
            merged = s_a + s_b[1:]
            if allowed is not None and merged not in allowed:
                continue
            prod = s_inst.mul(val_a, val_b)
            if prod != s_inst.zero:
                out[merged] = s_inst.add(out[merged], prod) if merged in out else prod

    pruned = {s: v for s, v in out.items() if v != s_inst.zero and _is_non_zero(v, tol)}
    return Cochain(pruned, degree=p + q, oriented=c_a.oriented and c_b.oriented, tol=tol)


def cap_product(
    chain: Mapping[tuple[K, ...], V],
    cochain: Cochain[K, V] | Mapping[tuple[K, ...], V],
    *,
    semiring: Semiring[V] | type[Semiring[V]] | None = None,
    tol: float = 1e-14,
) -> dict[tuple[K, ...], V]:
    r"""Compute the Alexander-Whitney cap product $c \frown \phi \in C_{n-p}(K; \mathcal{S})$.

    Algebraic Signature:
        $\frown: C_n(K; \mathcal{S}) \times C^p(K; \mathcal{S}) \to C_{n-p}(K; \mathcal{S}), \quad
        (v_0, \dots, v_n) \frown \phi = \phi(v_0, \dots, v_p) \otimes_{\mathcal{S}} (v_p, \dots, v_n)$

    Carrier:
        `dict[tuple[K, ...], V]` mapping canonical $(n-p)$-simplices to chain coefficients.

    Operations:
        - Front-Face Evaluation: Evaluates $p$-cochain $\phi$ on the front $p$-face $(v_0, \dots, v_p)$
          and weights the back $(n-p)$-face $(v_p, \dots, v_n)$.

    Properties:
        Satisfies Kronecker cup-cap duality:
        $\langle \psi, c \frown \phi \rangle = \langle \phi \smile \psi, c \rangle$.

    Applications:
        Poincaré duality isomorphism $H^p(M) \xrightarrow{\sim} H_{n-p}(M) $ on closed oriented $n$-manifolds.

    Args:
        chain: Sparse $n$-chain mapping simplex tuples to coefficients.
        cochain: Degree-$p$ `Cochain` or mapping.
        semiring: Optional `Semiring` instance or class.
        tol: Numerical zero-pruning threshold.

    Returns:
        Sparse $(n-p)$-chain dictionary over canonical simplices.
    """
    s_inst = Semiring.normalize(semiring)
    phi = cochain if isinstance(cochain, Cochain) else Cochain(cochain, tol=tol)
    if phi.degree is None or not phi or not chain:
        return {}

    p = phi.degree
    out: dict[tuple[K, ...], V] = {}

    for raw_simplex, raw_coeff in chain.items():
        if len(raw_simplex) < p + 1:
            continue
        canon, sign = _canonicalize_simplex(raw_simplex, oriented=phi.oriented)
        if sign == 0:
            continue
        coeff: V = -raw_coeff if (sign == -1 and isinstance(raw_coeff, (int, float, complex))) else raw_coeff  # type: ignore[assignment]
        front = canon[: p + 1]
        if front not in phi:
            continue
        phi_val = phi[front]
        back = canon[p:]
        prod = s_inst.mul(phi_val, coeff)
        if prod != s_inst.zero:
            out[back] = s_inst.add(out[back], prod) if back in out else prod

    return {s: v for s, v in out.items() if v != s_inst.zero and _is_non_zero(v, tol)}
