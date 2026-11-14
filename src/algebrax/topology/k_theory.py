r"""
Topological K-Theory ($K^0$), Characteristic Chern Classes & Discrete Vector Bundle Ring Operations.

Formalizes:
- Whitney direct sums $E_1 \oplus E_2$ (block-diagonal parallel transport)
- Tensor products $E_1 \otimes E_2$ (Kronecker product parallel transport)
- Discrete curvature angles and first/second Chern character forms ($\mathrm{ch}_0, \mathrm{ch}_1, \mathrm{ch}_2$)
- Integer first Chern numbers $\int_\Sigma c_1(E) \in \mathbb{Z}$ on oriented closed 2-surfaces
- The Topological K-Theory ring $K^0(K)$ over virtual vector bundles $[E] - [F]$
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any

from algebrax.algebra._ring import CommRing
from algebrax.topology.bundle import DiscreteConnection, DiscreteOrthogonalConnection, compute_face_holonomy
from algebrax.topology.cohomology import Cochain, cup_product
from algebrax.typing import SparseMatrix

__all__ = [
    'TopologicalKTheoryRing',
    'bundle_direct_sum',
    'bundle_tensor_product',
    'chern_character',
    'compute_chern_character_1',
    'compute_chern_character_2',
    'compute_face_curvature_angle',
    'first_chern_number',
    'trivial_bundle',
]


def _canonical_undirected_edges(
    e1: DiscreteOrthogonalConnection,
    e2: DiscreteOrthogonalConnection,
    edges: Iterable[tuple[Any, Any]] | None,
) -> list[tuple[Any, Any]]:
    raw_edges = list(edges) if edges is not None else sorted(
        e1.edges & e2.edges,
        key=lambda pair: (str(pair[0]), str(pair[1])),
    )
    seen: set[frozenset[Any]] = set()
    canonical: list[tuple[Any, Any]] = []
    for u, v in raw_edges:
        undir = frozenset((u, v))
        if undir in seen:
            continue
        seen.add(undir)
        canonical.append((u, v))
    return canonical


def trivial_bundle(
    fiber_dim: int,
    edges: Iterable[tuple[Any, Any]],
) -> DiscreteOrthogonalConnection:
    r"""Construct a flat trivial rank-$d$ orthogonal vector bundle $\underline{\mathbb{R}}^d$ with $\rho = I_d$."""
    conn = DiscreteOrthogonalConnection(fiber_dim)
    ident: SparseMatrix[int, float] = {i: {i: 1.0} for i in range(fiber_dim)}
    seen: set[frozenset[Any]] = set()
    for u, v in edges:
        undir = frozenset((u, v))
        if undir in seen:
            continue
        seen.add(undir)
        conn.set_transport(u, v, ident)
    return conn


def bundle_direct_sum(
    e1: DiscreteOrthogonalConnection,
    e2: DiscreteOrthogonalConnection,
    edges: Iterable[tuple[Any, Any]] | None = None,
) -> DiscreteOrthogonalConnection:
    r"""Whitney direct sum $E_1 \oplus E_2$ with block-diagonal parallel transport:
    $$\rho_{E_1 \oplus E_2}(u, v) = \operatorname{diag}(\rho_1(u, v), \rho_2(u, v))$$
    """
    d1 = e1.fiber_dim
    d2 = e2.fiber_dim
    res = DiscreteOrthogonalConnection(d1 + d2)

    for u, v in _canonical_undirected_edges(e1, e2, edges):
        t1 = e1.transport(u, v)
        t2 = e2.transport(u, v)
        block: dict[int, dict[int, float]] = {}
        for i, row in t1.items():
            block[i] = dict(row)
        for i, row in t2.items():
            block[i + d1] = {j + d1: val for j, val in row.items()}
        res.set_transport(u, v, block)

    return res


def bundle_tensor_product(
    e1: DiscreteOrthogonalConnection,
    e2: DiscreteOrthogonalConnection,
    edges: Iterable[tuple[Any, Any]] | None = None,
) -> DiscreteOrthogonalConnection:
    r"""Tensor product $E_1 \otimes E_2$ with Kronecker product parallel transport:
    $$\rho_{E_1 \otimes E_2}(u, v) = \rho_1(u, v) \otimes \rho_2(u, v)$$
    """
    d1 = e1.fiber_dim
    d2 = e2.fiber_dim
    res = DiscreteOrthogonalConnection(d1 * d2)

    for u, v in _canonical_undirected_edges(e1, e2, edges):
        t1 = e1.transport(u, v)
        t2 = e2.transport(u, v)
        kron: dict[int, dict[int, float]] = {}
        for i1, row1 in t1.items():
            for i2, row2 in t2.items():
                r_idx = i1 * d2 + i2
                r_out: dict[int, float] = {}
                for j1, val1 in row1.items():
                    for j2, val2 in row2.items():
                        prod = val1 * val2
                        if abs(prod) > 1e-15:
                            r_out[j1 * d2 + j2] = prod
                if r_out:
                    kron[r_idx] = r_out
        res.set_transport(u, v, kron)

    return res


def _extract_block_angles(hol: SparseMatrix[int, float], dim: int) -> list[float]:
    """Extract oriented 2x2 planar rotation angles from an orthogonal holonomy matrix."""
    angles: list[float] = []
    pair_count = dim // 2
    for b in range(pair_count):
        i0 = 2 * b
        i1 = 2 * b + 1
        h00 = hol.get(i0, {}).get(i0, 0.0)
        h01 = hol.get(i0, {}).get(i1, 0.0)
        h10 = hol.get(i1, {}).get(i0, 0.0)
        h11 = hol.get(i1, {}).get(i1, 0.0)
        cos_theta = 0.5 * (h00 + h11)
        sin_theta = 0.5 * (h10 - h01)
        angles.append(math.atan2(sin_theta, cos_theta))
    return angles


def compute_face_curvature_angle(
    connection: DiscreteConnection[Any],
    face: Sequence[Any],
) -> float:
    r"""Compute the total oriented curvature angle $\Omega(f) = \sum_b \theta_b(f) \in \mathbb{R}$ on a 2-face.

    For an $SO(2) \cong U(1)$ bundle with $2 \times 2$ holonomy matrix
    $R(\theta) = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}$,
    returns the principal holonomy angle $\theta \in [-\pi, \pi]$. For Whitney sums of $SO(2)$ bundles,
    returns the trace of the skew-symmetric logarithm $\sum_b \theta_b$.
    """
    hol = compute_face_holonomy(connection, face)
    return sum(_extract_block_angles(hol, connection.fiber_dim))


def compute_chern_character_1(
    connection: DiscreteConnection[Any],
    faces: Iterable[Sequence[Any]],
) -> dict[tuple[Any, ...], float]:
    r"""Compute the first Chern character 2-form $\mathrm{ch}_1(E) = c_1(E) = \frac{1}{2\pi} \Omega$ on 2-faces.

    Satisfies Whitney sum additivity:
        $$\mathrm{ch}_1(E_1 \oplus E_2) = \mathrm{ch}_1(E_1) + \mathrm{ch}_1(E_2)$$
    """
    c1_form: dict[tuple[Any, ...], float] = {}
    inv_two_pi = 1.0 / (2.0 * math.pi)
    for face in faces:
        f_key = tuple(face)
        angle = compute_face_curvature_angle(connection, f_key)
        c1_form[f_key] = angle * inv_two_pi
    return c1_form


def compute_chern_character_2(
    connection: DiscreteConnection[Any],
    faces: Iterable[Sequence[Any]],
    four_simplices: Iterable[Sequence[Any]] | None = None,
) -> dict[tuple[Any, ...], float]:
    r"""Compute the second Chern character $\mathrm{ch}_2(E) = \frac{1}{2} c_1(E) \smile c_1(E)$.

    When `four_simplices` are provided, evaluates the Alexander-Whitney cup product
    $\frac{1}{2}(\mathrm{ch}_1(E) \smile \mathrm{ch}_1(E))$ on 4-simplices; otherwise returns the
    facewise quadratic curvature density $\frac{1}{2} \sum_b (\theta_b / 2\pi)^2$ on 2-faces.
    """
    c1_map = compute_chern_character_1(connection, faces)
    if four_simplices is not None:
        c1_cochain = Cochain(c1_map, degree=2)
        cup_c1 = cup_product(c1_cochain, c1_cochain)
        out_4: dict[tuple[Any, ...], float] = {}
        for simp in four_simplices:
            s_key = tuple(simp)
            out_4[s_key] = 0.5 * float(cup_c1.get(s_key, 0.0))
        return out_4

    inv_two_pi = 1.0 / (2.0 * math.pi)
    out_2: dict[tuple[Any, ...], float] = {}
    for face in faces:
        f_key = tuple(face)
        angles = _extract_block_angles(compute_face_holonomy(connection, f_key), connection.fiber_dim)
        out_2[f_key] = 0.5 * sum((theta * inv_two_pi) ** 2 for theta in angles)
    return out_2


def first_chern_number(
    connection: DiscreteConnection[Any],
    oriented_faces: Iterable[Sequence[Any]],
) -> float:
    r"""Evaluate the total first Chern number $\int_\Sigma c_1(E) = \sum_{f \in \Sigma} c_1(E)(f)$ over a 2-cycle."""
    c1 = compute_chern_character_1(connection, oriented_faces)
    return sum(c1.values())


def chern_character(
    connection: DiscreteConnection[Any],
    faces: Iterable[Sequence[Any]],
    *,
    complex_rank: int | None = None,
) -> tuple[int, dict[tuple[Any, ...], float], dict[tuple[Any, ...], float]]:
    r"""Compute the truncated discrete Chern character $(\mathrm{ch}_0(E), \mathrm{ch}_1(E), \mathrm{ch}_2(E))$.

    Args:
        connection: Discrete vector bundle connection.
        faces: Collection of oriented 2-faces.
        complex_rank: Optional complex rank $\mathrm{ch}_0(E)$ (defaults to `fiber_dim // 2` if even,
            else `fiber_dim`).

    Returns:
        Tuple `(ch_0, ch_1, ch_2)` representing rank, 2-form first Chern character, and quadratic second
        Chern character.
    """
    face_list = [tuple(f) for f in faces]
    d = connection.fiber_dim
    rank = complex_rank if complex_rank is not None else (d // 2 if d % 2 == 0 else d)
    ch1 = compute_chern_character_1(connection, face_list)
    ch2 = compute_chern_character_2(connection, face_list)
    return rank, ch1, ch2


class TopologicalKTheoryRing(
    CommRing[tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]],
):
    r"""Topological K-Theory ring $K^0(K)$ of virtual orthogonal vector bundles $[E] - [F]$.

    Algebraic Signature:
        $\langle K^0(K), [\mathbf{0}], \oplus, -, [\underline{\mathbb{R}}^1], \otimes \rangle$

    Carrier:
        Pairs `(pos_bundle, neg_bundle)` where `None` denotes the zero-rank trivial bundle $\mathbf{0}$.
        - Addition (`add`): Whitney direct sum
          $([E_1] - [F_1]) \oplus ([E_2] - [F_2]) = [E_1 \oplus E_2] - [F_1 \oplus F_2]$.
        - Negation (`neg`): Formal bundle reversal $-([E] - [F]) = [F] - [E]$.
        - Multiplication (`mul`): Virtual tensor product
          $[(E_1 \otimes E_2) \oplus (F_1 \otimes F_2)] - [(E_1 \otimes F_2) \oplus (F_1 \otimes E_2)]$.
    """

    def __init__(self, edges: Iterable[tuple[Any, Any]]) -> None:
        self._edges = list(edges)

    @property
    def zero(self) -> tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]:
        """Zero virtual bundle (0, 0)."""
        return (None, None)

    @property
    def one(self) -> tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]:
        r"""Multiplicative identity $[\underline{\mathbb{R}}^1] - [\mathbf{0}]$."""
        return (trivial_bundle(1, self._edges), None)

    def embed(
        self,
        bundle: DiscreteOrthogonalConnection,
    ) -> tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]:
        """Embed a concrete vector bundle E as virtual class [E] - [0]."""
        return (bundle, None)

    def _sum_opt(
        self,
        b1: DiscreteOrthogonalConnection | None,
        b2: DiscreteOrthogonalConnection | None,
    ) -> DiscreteOrthogonalConnection | None:
        if b1 is None:
            return b2
        if b2 is None:
            return b1
        return bundle_direct_sum(b1, b2, self._edges)

    def _tensor_opt(
        self,
        b1: DiscreteOrthogonalConnection | None,
        b2: DiscreteOrthogonalConnection | None,
    ) -> DiscreteOrthogonalConnection | None:
        if b1 is None or b2 is None:
            return None
        return bundle_tensor_product(b1, b2, self._edges)

    def add(
        self,
        a: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
        b: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
    ) -> tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]:
        """Whitney sum of virtual bundles."""
        return (self._sum_opt(a[0], b[0]), self._sum_opt(a[1], b[1]))

    def neg(
        self,
        a: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
    ) -> tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]:
        """Formal virtual inverse -([E] - [F]) = [F] - [E]."""
        return (a[1], a[0])

    def sub(
        self,
        a: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
        b: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
    ) -> tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]:
        """Virtual bundle difference."""
        return self.add(a, self.neg(b))

    def mul(
        self,
        a: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
        b: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
    ) -> tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None]:
        """Virtual bundle tensor product."""
        e1, f1 = a
        e2, f2 = b
        pos = self._sum_opt(self._tensor_opt(e1, e2), self._tensor_opt(f1, f2))
        neg = self._sum_opt(self._tensor_opt(e1, f2), self._tensor_opt(f1, e2))
        return (pos, neg)

    def virtual_rank(
        self,
        a: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
    ) -> int:
        r"""Compute virtual fiber dimension $\mathrm{rank}(E) - \mathrm{rank}(F) \in \mathbb{Z}$."""
        r_pos = a[0].fiber_dim if a[0] is not None else 0
        r_neg = a[1].fiber_dim if a[1] is not None else 0
        return r_pos - r_neg

    def virtual_chern_1(
        self,
        a: tuple[DiscreteOrthogonalConnection | None, DiscreteOrthogonalConnection | None],
        faces: Iterable[Sequence[Any]],
    ) -> dict[tuple[Any, ...], float]:
        r"""Compute virtual first Chern character $\mathrm{ch}_1([E] - [F]) = \mathrm{ch}_1(E) - \mathrm{ch}_1(F)$."""
        face_list = [tuple(f) for f in faces]
        c_pos = compute_chern_character_1(a[0], face_list) if a[0] is not None else {}
        c_neg = compute_chern_character_1(a[1], face_list) if a[1] is not None else {}
        return {f: c_pos.get(f, 0.0) - c_neg.get(f, 0.0) for f in face_list}
