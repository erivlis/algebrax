"""Simplicial cohomology, discrete differential k-forms (Cochain), and Alexander-Whitney cup/cap products."""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Literal, TypeAlias

from algebrax.algebra import Algebra, Ring
from algebrax.converters import make_zero_predicate
from algebrax.matrix.eliminate import rank as _sparse_rank
from algebrax.semiring import Semiring, StandardSemiring
from algebrax.topology._core import _canonicalize_simplex, _is_non_zero
from algebrax.topology.homology import SimplicialComplex, SparseChainComplex
from algebrax.typing import K, SparseMatrix, SparseVector, V

__all__ = [
    'Cochain',
    'CochainAlgebra',
    'DiscreteForm',
    'canonicalize_form',
    'cap_product',
    'coboundary',
    'cochain_to_flow',
    'cohomology_rank',
    'cup_product',
    'flow_to_cochain',
]


def _is_exact_structure(structure: Semiring[Any]) -> bool:
    """Return True when structure's zero is not a floating-point or complex number."""
    z = structure.zero
    return not isinstance(z, (float, complex))


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
            f_uv != 0.0  # NOSONAR - exact sentinel presence check
            and f_vu != 0.0  # NOSONAR - exact sentinel presence check
            and math.isclose(f_uv, -f_vu, rel_tol=1e-9, abs_tol=max(tol, 1e-12))
        ):
            return f_uv
        return f_uv - f_vu
    raise ValueError(f"Unknown mode '{mode}'. Expected 'auto', 'net', or 'half_skew'.")


class Cochain(Mapping[tuple[K, ...], V]):
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
        tol: float | None = None,
        ring: Ring[V] | Semiring[V] | None = None,
    ) -> None:
        self._oriented = oriented
        self._ring: Ring[V] | Semiring[V] | None = ring
        if tol is None:
            self._tol = 0.0 if (ring is not None and _is_exact_structure(ring)) else 1e-14
        else:
            self._tol = tol
        self._is_zero = make_zero_predicate(ring, tol=self._tol) if ring is not None else None
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
                signed_val: V = self._neg_val(raw_val) if sign == -1 else raw_val
                prev = self._data.get(canon)
                combined = self._add_val(prev, signed_val) if prev is not None else signed_val
                if not self._check_zero(combined):
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

    def _neg_val(self, val: V) -> V:
        if self._ring is not None:
            neg_fn = getattr(self._ring, 'neg', None)
            if callable(neg_fn):
                return neg_fn(val)  # type: ignore[return-value]
        return -val  # type: ignore[operator]

    def _add_val(self, a: V, b: V) -> V:
        if self._ring is not None:
            return self._ring.add(a, b)
        return a + b  # type: ignore[operator]

    def _check_zero(self, val: V) -> bool:
        if self._is_zero is not None:
            return self._is_zero(val)
        return not _is_non_zero(val, self._tol)

    @property
    def ring(self) -> Ring[V] | Semiring[V] | None:
        """Optional coefficient ring or semiring governing arithmetic and zero pruning."""
        return self._ring

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
        return self._neg_val(val) if sign == -1 else val

    def get(self, key: tuple[K, ...], default: Any = None) -> Any:
        if not isinstance(key, tuple):
            return default
        canon, sign = _canonicalize_simplex(key, oriented=self._oriented)
        if sign == 0:
            zero_val: Any = self._ring.zero if self._ring is not None else 0.0
            return zero_val if default is None else default
        if canon not in self._data:
            return default
        val = self._data[canon]
        return self._neg_val(val) if sign == -1 else val

    def __iter__(self) -> Iterator[tuple[K, ...]]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def _data_matches(self, other_data: dict[tuple[K, ...], V], cmp_tol: float) -> bool:
        if self._data.keys() != other_data.keys():
            return False
        for k, v1 in self._data.items():
            v2 = other_data[k]
            if (
                cmp_tol > 0.0
                and isinstance(v1, (int, float))
                and isinstance(v2, (int, float))
                and not isinstance(v1, bool)
                and not isinstance(v2, bool)
            ):
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
                other_cochain = Cochain(other, oriented=self._oriented, tol=self._tol, ring=self._ring)
            except (TypeError, ValueError):
                return False
            cmp_tol = max(self._tol, 1e-12) if self._tol > 0 else 0.0
            return self._data_matches(other_cochain._data, cmp_tol)
        return NotImplemented

    def __add__(self, other: Mapping[tuple[K, ...], V]) -> Cochain[K, V]:
        if not isinstance(other, Mapping):
            return NotImplemented
        eff_ring = self._ring if self._ring is not None else (other._ring if isinstance(other, Cochain) else None)
        other_c = (
            other
            if isinstance(other, Cochain)
            else Cochain(other, oriented=self._oriented, tol=self._tol, ring=eff_ring)
        )
        merged: dict[tuple[K, ...], V] = dict(self._data)
        for s, val in other_c._data.items():
            if s in merged:
                merged[s] = eff_ring.add(merged[s], val) if eff_ring is not None else (merged[s] + val)  # type: ignore[operator]
            else:
                merged[s] = val
        deg = self._degree if self._degree == other_c._degree else None
        return Cochain(merged, degree=deg, oriented=self._oriented, tol=self._tol, ring=eff_ring)

    def __sub__(self, other: Mapping[tuple[K, ...], V]) -> Cochain[K, V]:
        if not isinstance(other, Mapping):
            return NotImplemented
        eff_ring = self._ring if self._ring is not None else (other._ring if isinstance(other, Cochain) else None)
        other_c = (
            other
            if isinstance(other, Cochain)
            else Cochain(other, oriented=self._oriented, tol=self._tol, ring=eff_ring)
        )
        merged: dict[tuple[K, ...], V] = dict(self._data)
        neg_fn = getattr(eff_ring, 'neg', None) if eff_ring is not None else None
        for s, val in other_c._data.items():
            neg_val = neg_fn(val) if callable(neg_fn) else (-val)  # type: ignore[operator]
            if s in merged:
                merged[s] = eff_ring.add(merged[s], neg_val) if eff_ring is not None else (merged[s] - val)  # type: ignore[operator]
            else:
                merged[s] = neg_val  # type: ignore[assignment]
        deg = self._degree if self._degree == other_c._degree else None
        return Cochain(merged, degree=deg, oriented=self._oriented, tol=self._tol, ring=eff_ring)

    def __neg__(self) -> Cochain[K, V]:
        neg_data = {s: self._neg_val(val) for s, val in self._data.items()}
        return Cochain(neg_data, degree=self._degree, oriented=self._oriented, tol=self._tol, ring=self._ring)

    def __mul__(self, scalar: V) -> Cochain[K, V]:
        if isinstance(scalar, Mapping):
            return NotImplemented
        if self._ring is not None:
            scaled = {s: self._ring.mul(val, scalar) for s, val in self._data.items()}
        else:
            scaled = {s: val * scalar for s, val in self._data.items()}  # type: ignore[operator]
        return Cochain(scaled, degree=self._degree, oriented=self._oriented, tol=self._tol, ring=self._ring)

    def __rmul__(self, scalar: V) -> Cochain[K, V]:
        if isinstance(scalar, Mapping):
            return NotImplemented
        if self._ring is not None:
            scaled = {s: self._ring.mul(scalar, val) for s, val in self._data.items()}
        else:
            scaled = {s: scalar * val for s, val in self._data.items()}  # type: ignore[operator]
        return Cochain(scaled, degree=self._degree, oriented=self._oriented, tol=self._tol, ring=self._ring)

    def cup(
        self,
        other: Cochain[K, V] | Mapping[tuple[K, ...], V],
        *,
        complex: SimplicialComplex | None = None,
        semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
    ) -> Cochain[K, V]:
        r"""Compute the Alexander-Whitney cup product `self \smile other`."""
        eff_semiring = semiring if semiring is not None else self._ring
        return cup_product(self, other, complex=complex, semiring=eff_semiring, tol=self._tol)

    def __xor__(self, other: Cochain[K, V] | Mapping[tuple[K, ...], V]) -> Cochain[K, V]:
        if not isinstance(other, Mapping):
            return NotImplemented
        return cup_product(self, other, semiring=self._ring, tol=self._tol)

    def eval(self, chain: Mapping[tuple[K, ...], V]) -> V:
        r"""Evaluate bilinear Kronecker pairing $\langle \omega, c \rangle = \sum_\sigma \omega(\sigma) c_\sigma$."""
        if self._ring is not None:
            total: Any = self._ring.zero
            add_op = self._ring.add
            mul_op = self._ring.mul
            zero = self._ring.zero
            for simplex, coeff in chain.items():
                w_val = self.get(simplex, zero)
                if not self._check_zero(w_val):
                    total = add_op(total, mul_op(w_val, coeff))
            return total  # type: ignore[return-value]

        total = 0.0
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

    rank_dk = _sparse_rank(d_k, tol=1e-9)
    rank_dk1 = _sparse_rank(d_k1, tol=1e-9)

    num_k = len({c for row in d_k.values() for c in row}) if d_k else 0
    if not num_k and d_k1:
        num_k = len(d_k1)

    return max(num_k - rank_dk - rank_dk1, 0)


def cup_product(
    alpha: Cochain[K, V] | Mapping[tuple[K, ...], V],
    beta: Cochain[K, V] | Mapping[tuple[K, ...], V],
    *,
    complex: SimplicialComplex | None = None,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
    tol: float = 1e-14,
) -> Cochain[K, V]:
    r"""Compute the Alexander-Whitney cup product $\alpha \smile \beta \in C^{p+q}(K; \mathcal{S})$.

    Algebraic Signature:
        $\smile: C^p(K; \mathcal{S}) \times C^q(K; \mathcal{S}) \to C^{p+q}(K; \mathcal{S}), \quad
        (\alpha \smile \beta)(v_0, \dots, v_{p+q}) =
        \alpha(v_0, \dots, v_p) \otimes_{\mathcal{S}} \beta(v_p, \dots, v_{p+q})$

    Carrier:
        `Cochain[K, V]` of degree $p + q$ (or graded total cochain when inputs mix degrees).

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
        complex: Optional `SimplicialComplex` restricting support to simplices in `complex`.
        semiring: Optional `Semiring` instance, class, or catalog name (defaults to `StandardSemiring`).
        tol: Numerical zero-pruning threshold (applied only when `semiring.zero == 0` for numeric values).

    Returns:
        Cup product `Cochain[K, V]`.
    """
    inherited_ring = (
        alpha.ring
        if isinstance(alpha, Cochain) and alpha.ring is not None
        else (beta.ring if isinstance(beta, Cochain) and beta.ring is not None else None)
    )
    s_inst = Semiring.normalize(semiring) if semiring is not None else (
        inherited_ring if inherited_ring is not None else Semiring.normalize(None)
    )
    eff_tol = 0.0 if _is_exact_structure(s_inst) or s_inst.zero != 0 else tol
    is_zero = make_zero_predicate(s_inst, tol=eff_tol)
    preserve_ring = s_inst if (semiring is not None or inherited_ring is not None) else None

    c_a = alpha if isinstance(alpha, Cochain) else Cochain(alpha, tol=eff_tol, ring=preserve_ring)
    c_b = beta if isinstance(beta, Cochain) else Cochain(beta, tol=eff_tol, ring=preserve_ring)
    out_oriented = c_a.oriented and c_b.oriented
    out_deg = (c_a.degree + c_b.degree) if (c_a.degree is not None and c_b.degree is not None) else None

    if not c_a or not c_b:
        return Cochain(degree=out_deg, oriented=out_oriented, tol=eff_tol, ring=preserve_ring)

    beta_by_head: dict[K, list[tuple[tuple[K, ...], V]]] = {}
    for s_b, val_b in c_b.items():
        if s_b:
            beta_by_head.setdefault(s_b[0], []).append((s_b, val_b))

    add_op = s_inst.add
    mul_op = s_inst.mul
    out: dict[tuple[K, ...], V] = {}
    for s_a, val_a in c_a.items():
        if not s_a:
            continue
        pivot_v = s_a[-1]
        for s_b, val_b in beta_by_head.get(pivot_v, ()):
            # Because s_a = (v_0 < ... < v_p) and s_b = (v_p < ... < v_{p+q}),
            # merged = (v_0 < ... < v_{p+q}) is strictly increasing with sign +1.
            merged = s_a + s_b[1:]
            if complex is not None:
                allowed = complex._simplices.get(len(merged) - 1)
                if not allowed or merged not in allowed:
                    continue
            prod = mul_op(val_a, val_b)
            if not is_zero(prod):
                out[merged] = add_op(out[merged], prod) if merged in out else prod

    pruned = {s: v for s, v in out.items() if not is_zero(v)}
    return Cochain(pruned, degree=out_deg, oriented=out_oriented, tol=eff_tol, ring=preserve_ring)


def cap_product(
    chain: Mapping[tuple[K, ...], V],
    cochain: Cochain[K, V] | Mapping[tuple[K, ...], V],
    *,
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
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
        semiring: Optional `Semiring` instance, class, or catalog name.
        tol: Numerical zero-pruning threshold (applied only when `semiring.zero == 0` for numeric values).

    Returns:
        Sparse $(n-p)$-chain dictionary over canonical simplices.
    """
    inherited_ring = cochain.ring if isinstance(cochain, Cochain) and cochain.ring is not None else None
    s_inst = Semiring.normalize(semiring) if semiring is not None else (
        inherited_ring if inherited_ring is not None else Semiring.normalize(None)
    )
    eff_tol = 0.0 if _is_exact_structure(s_inst) or s_inst.zero != 0 else tol
    is_zero = make_zero_predicate(s_inst, tol=eff_tol)
    preserve_ring = s_inst if (semiring is not None or inherited_ring is not None) else None

    phi = cochain if isinstance(cochain, Cochain) else Cochain(cochain, tol=eff_tol, ring=preserve_ring)
    if phi.degree is None or not phi or not chain:
        return {}

    p = phi.degree
    neg_fn = getattr(s_inst, 'neg', None)
    add_op = s_inst.add
    mul_op = s_inst.mul
    out: dict[tuple[K, ...], V] = {}

    for raw_simplex, raw_coeff in chain.items():
        if len(raw_simplex) < p + 1:
            continue
        canon, sign = _canonicalize_simplex(raw_simplex, oriented=phi.oriented)
        if sign == 0:
            continue
        if sign == -1:
            if callable(neg_fn):
                coeff: V = neg_fn(raw_coeff)  # type: ignore[assignment]
            elif isinstance(raw_coeff, (int, float, complex)) and not isinstance(raw_coeff, bool):
                coeff = -raw_coeff  # type: ignore[assignment]
            else:
                coeff = raw_coeff
        else:
            coeff = raw_coeff
        front = canon[: p + 1]
        if front not in phi:
            continue
        phi_val = phi[front]
        back = canon[p:]
        prod = mul_op(phi_val, coeff)
        if not is_zero(prod):
            out[back] = add_op(out[back], prod) if back in out else prod

    return {s: v for s, v in out.items() if not is_zero(v)}


class CochainAlgebra(Algebra[V, Cochain[K, V]]):
    r"""Associative differential graded algebra of simplicial cochains under the
    Alexander-Whitney cup product $\smile$.
    """

    def __init__(self, complex: SimplicialComplex, coefficient_ring: Ring[V]):
        if not isinstance(coefficient_ring, (Ring, StandardSemiring)):
            raise TypeError(
                f'CochainAlgebra requires a Ring (or StandardSemiring) coefficient structure, '
                f'got {type(coefficient_ring).__name__}.'
            )
        self._complex = complex
        self._ring = coefficient_ring
        self._tol = 0.0 if _is_exact_structure(coefficient_ring) else 1e-14
        self._is_zero = make_zero_predicate(coefficient_ring, tol=self._tol)

    @property
    def zero(self) -> Cochain[K, V]:
        """The additive zero cochain."""
        return Cochain({}, tol=self._tol, ring=self._ring)

    @property
    def one(self) -> Cochain[K, V]:
        """Canonical 0-cochain assigning 1_R to every 0-simplex (vertex) in K_0."""
        return Cochain(
            {(v,): self._ring.one for v in self._complex.vertices},
            degree=0,
            tol=self._tol,
            ring=self._ring,
        )

    def add(self, a: Cochain[K, V], b: Cochain[K, V]) -> Cochain[K, V]:
        """Cochain addition routed through `self._ring`."""
        merged: dict[tuple[K, ...], V] = dict(a.items())
        add_op = self._ring.add
        is_zero = self._is_zero
        for s, val in b.items():
            combined = add_op(merged[s], val) if s in merged else val
            if is_zero(combined):
                merged.pop(s, None)
            else:
                merged[s] = combined
        deg = a.degree if a.degree == b.degree else None
        return Cochain(
            merged,
            degree=deg,
            oriented=a.oriented and b.oriented,
            tol=self._tol,
            ring=self._ring,
        )

    def neg(self, a: Cochain[K, V]) -> Cochain[K, V]:
        """Cochain negation routed through `self._ring`."""
        ring_neg = getattr(self._ring, 'neg', None)
        neg_op = ring_neg if callable(ring_neg) else (lambda v: -v)
        is_zero = self._is_zero
        neg_data = {s: nv for s, val in a.items() if not is_zero(nv := neg_op(val))}
        return Cochain(neg_data, degree=a.degree, oriented=a.oriented, tol=self._tol, ring=self._ring)

    def sub(self, a: Cochain[K, V], b: Cochain[K, V]) -> Cochain[K, V]:
        """Cochain subtraction routed through `self._ring`."""
        return self.add(a, self.neg(b))

    def smul(self, r: V, m: Cochain[K, V]) -> Cochain[K, V]:
        """Scalar scaling routed through `self._ring`."""
        is_zero = self._is_zero
        if is_zero(r):
            return Cochain({}, degree=m.degree, oriented=m.oriented, tol=self._tol, ring=self._ring)
        mul_op = self._ring.mul
        scaled = {s: pv for s, val in m.items() if not is_zero(pv := mul_op(r, val))}
        return Cochain(scaled, degree=m.degree, oriented=m.oriented, tol=self._tol, ring=self._ring)

    def mul(self, a: Cochain[K, V], b: Cochain[K, V]) -> Cochain[K, V]:
        r"""Alexander-Whitney cup product $a \smile b$ restricted to `self._complex` over `self._ring`."""
        return cup_product(a, b, complex=self._complex, semiring=self._ring, tol=self._tol)
