r"""
Group Representation Protocols, Constructions, and Intertwining Operators.

Algebraic Signatures:
    Group Representation: $\rho : G \longrightarrow \mathrm{GL}(V)$,
                          $\rho(gh) = \rho(g)\rho(h), \quad \rho(e) = \mathbf{I}$
    Isotypic Projector:   $P_\chi = \frac{d_\chi}{|G|} \sum_{g \in G} \overline{\chi(g)} \, \rho(g)$
    Intertwiner Space:    $\mathrm{Hom}_G(V_1, V_2) =
                          \{T : V_1 \to V_2 \mid T \rho_1(g) = \rho_2(g) T \ \forall g \in G\}$
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeAlias, TypeVar, runtime_checkable

from algebrax.algebra._homomorphisms import GroupHom
from algebrax.group.finite import FiniteGroup
from algebrax.matrix.core import add, dot, inverse, trace, transpose
from algebrax.typing import SparseMatrix

K = TypeVar('K')
G = TypeVar('G', bound=Hashable)

RepOperator: TypeAlias = Callable[[G], SparseMatrix[int, K]]
"""Functional signature of a group representation mapping elements to sparse matrices."""


def _resolve_elements(elements_or_group: Iterable[G] | FiniteGroup[G]) -> list[G]:
    if isinstance(elements_or_group, FiniteGroup):
        return list(elements_or_group.elements)
    return list(elements_or_group)


def _prune_matrix(mat: SparseMatrix[int, Any], tol: float = 1e-13) -> dict[int, dict[int, Any]]:
    """Remove near-zero numeric entries from a sparse matrix while preserving exact non-numeric carriers."""
    cleaned: dict[int, dict[int, Any]] = {}
    for r, row in mat.items():
        new_row: dict[int, Any] = {}
        for c, val in row.items():
            if isinstance(val, (int, float, complex)):
                if abs(val) > tol:
                    if isinstance(val, complex) and abs(val.imag) <= tol:
                        new_row[c] = val.real
                    else:
                        new_row[c] = val
            elif val != 0:
                new_row[c] = val
        if new_row:
            cleaned[r] = new_row
    return cleaned


def _scale_matrix(mat: SparseMatrix[int, Any], scalar: Any, tol: float = 1e-13) -> dict[int, dict[int, Any]]:
    """Scale a sparse matrix by a scalar coefficient with sparsity pruning."""
    if scalar == 0:
        return {}
    result: dict[int, dict[int, Any]] = {}
    for r, row in mat.items():
        new_row: dict[int, Any] = {}
        for c, val in row.items():
            prod = scalar * val
            if isinstance(prod, (int, float, complex)):
                if abs(prod) > tol:
                    if isinstance(prod, complex) and abs(prod.imag) <= tol:
                        new_row[c] = prod.real
                    else:
                        new_row[c] = prod
            elif prod != 0:
                new_row[c] = prod
        if new_row:
            result[r] = new_row
    return result


@runtime_checkable
class GroupRepresentation(GroupHom[G, SparseMatrix[int, K]], Protocol[K, G]):
    r"""Protocol for a linear representation $\rho : G \to \mathrm{GL}(V)$ over sparse matrices.

    Refines `GroupHom[G, SparseMatrix[int, K]]` with representation space dimension.

    Algebraic Signature:
        $\rho : G \longrightarrow \mathrm{GL}_d(\mathbb{K}), \quad
        \rho(gh) = \rho(g)\rho(h), \quad \rho(e) = \mathbf{I}_d$

    Carrier:
        Group elements `G` mapped to sparse matrices `SparseMatrix[int, K]` acting on `K^d`.
    """

    @property
    def dimension(self) -> int:
        """Dimension of the representation vector space $V$."""
        ...

    def __call__(self, g: G) -> SparseMatrix[int, K]:
        """Evaluate representation operator $\rho(g)$ as a sparse matrix."""
        ...


# Note: ExplicitGroupRep conforms structurally to GroupRepresentation[K, G] rather than
# subclassing it directly, because GroupRepresentation.dimension is a read-only @property
# data descriptor that conflicts with @dataclass(frozen=True) field assignment. Freezing
# prevents rebinding `dimension` or `matrices` out of sync after verification or sharing.
@dataclass(frozen=True)
class ExplicitGroupRep(Generic[K, G]):
    r"""Explicit finite-group representation backed by precomputed sparse matrices.

    Algebraic Signature:
        $\rho : G \longrightarrow \mathrm{GL}_d(\mathbb{K}), \quad
        g \longmapsto M_g \in \mathrm{SparseMatrix}[d \times d]$

    Attributes:
        matrices: Mapping from group element $g \in G$ to its sparse matrix $\rho(g)$.
        dimension: Dimension $d = \dim V$ of the representation space.
    """

    matrices: Mapping[G, SparseMatrix[int, K]]
    dimension: int

    def __call__(self, g: G) -> SparseMatrix[int, K]:
        return self.matrices[g]

    def trace(self, g: G) -> K:
        r"""Compute the character value $\chi_\rho(g) = \operatorname{tr}(\rho(g))$."""
        return trace(self.matrices[g])

    def character_values(self, class_representatives: Mapping[Any, G] | Iterable[G]) -> dict[Any, complex]:
        r"""Evaluate $\chi_\rho(g) = \operatorname{tr}(\rho(g))$ on class representatives or elements."""
        if isinstance(class_representatives, Mapping):
            return {label: complex(self.trace(rep_el)) for label, rep_el in class_representatives.items()}
        return {el: complex(self.trace(el)) for el in class_representatives}

    def direct_sum(
        self,
        other: GroupRepresentation[K, G],
        elements: Iterable[G] | FiniteGroup[G] | None = None,
    ) -> ExplicitGroupRep[K, G]:
        r"""Form the direct sum representation $(\rho_1 \oplus \rho_2)(g) = \mathrm{diag}(\rho_1(g), \rho_2(g))$."""
        elems = list(self.matrices.keys()) if elements is None else _resolve_elements(elements)
        return direct_sum_rep([self, other], elems)

    def tensor_product(
        self,
        other: GroupRepresentation[K, G],
        elements: Iterable[G] | FiniteGroup[G] | None = None,
    ) -> ExplicitGroupRep[K, G]:
        r"""Form the tensor product representation $(\rho_1 \otimes \rho_2)(g) = \rho_1(g) \otimes \rho_2(g)$."""
        elems = list(self.matrices.keys()) if elements is None else _resolve_elements(elements)
        return tensor_product_rep(self, other, elems)

    def dual(
        self,
        inv_fn: Callable[[G], G] | None = None,
        elements: Iterable[G] | FiniteGroup[G] | None = None,
    ) -> ExplicitGroupRep[K, G]:
        r"""Form the contragredient (dual) representation $\rho^*(g) = \rho(g^{-1})^T$.

        Args:
            inv_fn: Optional group inversion function $g \mapsto g^{-1}$. If omitted and `elements`
                is a `FiniteGroup`, `elements.inv` is used; otherwise each matrix $\rho(g)$ is inverted
                directly via sparse Gauss-Jordan elimination.
            elements: Optional `FiniteGroup` or subset/ordering of group elements.

        Returns:
            Explicit contragredient representation $\rho^*$.
        """
        resolved_inv = inv_fn
        if resolved_inv is None and isinstance(elements, FiniteGroup):
            resolved_inv = elements.inv
        elems = list(self.matrices.keys()) if elements is None else _resolve_elements(elements)
        dual_mats: dict[G, SparseMatrix[int, K]] = {}
        for g in elems:
            if resolved_inv is not None:
                dual_mats[g] = transpose(self(resolved_inv(g)))
            else:
                inv_mat = inverse(self(g))  # type: ignore[type-var]
                dual_mats[g] = transpose(inv_mat)  # type: ignore[assignment]
        return ExplicitGroupRep(matrices=dual_mats, dimension=self.dimension)


def direct_sum_rep(
    reps: Sequence[GroupRepresentation[K, G]],
    elements: Iterable[G] | FiniteGroup[G],
) -> ExplicitGroupRep[K, G]:
    r"""Construct the direct sum $\bigoplus_k \rho_k$ over a sequence of representations.

    Args:
        reps: Non-empty sequence of group representations sharing the same group $G$.
        elements: `FiniteGroup` or elements on which to materialize the block-diagonal matrices.

    Returns:
        `ExplicitGroupRep` of dimension $\sum_k \dim \rho_k$.
    """
    if not reps:
        raise ValueError('direct_sum_rep requires at least one representation.')

    elem_list = _resolve_elements(elements)
    dims = [r.dimension for r in reps]
    total_dim = sum(dims)
    mats: dict[G, SparseMatrix[int, K]] = {}

    for g in elem_list:
        shifted: dict[int, dict[int, K]] = {}
        offset = 0
        for rep, dim in zip(reps, dims):
            m = rep(g)
            for r_idx, row in m.items():
                shifted[r_idx + offset] = {c_idx + offset: val for c_idx, val in row.items()}
            offset += dim
        mats[g] = shifted

    return ExplicitGroupRep(matrices=mats, dimension=total_dim)


def tensor_product_rep(
    rep_a: GroupRepresentation[K, G],
    rep_b: GroupRepresentation[K, G],
    elements: Iterable[G] | FiniteGroup[G],
) -> ExplicitGroupRep[K, G]:
    r"""Construct the tensor product representation $(\rho_a \otimes \rho_b)(g) = \rho_a(g) \otimes \rho_b(g)$.

    Uses lexicographical index encoding $(i, j) \mapsto i \cdot \dim(V_b) + j$.
    Character satisfies $\chi_{\rho_a \otimes \rho_b}(g) = \chi_{\rho_a}(g)\,\chi_{\rho_b}(g)$.
    """
    elem_list = _resolve_elements(elements)
    d_b = rep_b.dimension
    total_dim = rep_a.dimension * d_b
    mats: dict[G, SparseMatrix[int, K]] = {}

    for g in elem_list:
        ma = rep_a(g)
        mb = rep_b(g)
        prod_mat: dict[int, dict[int, K]] = {}
        for r_a, row_a in ma.items():
            for r_b, row_b in mb.items():
                r_out = r_a * d_b + r_b
                out_row: dict[int, K] = {}
                for c_a, va in row_a.items():
                    for c_b, vb in row_b.items():
                        val = va * vb  # type: ignore[operator]
                        if val != 0:
                            out_row[c_a * d_b + c_b] = val
                if out_row:
                    prod_mat[r_out] = out_row
        mats[g] = prod_mat

    return ExplicitGroupRep(matrices=mats, dimension=total_dim)


def isotypic_projector(
    rep: GroupRepresentation[Any, G],
    elements: Sequence[G] | FiniteGroup[G],
    irrep_chi: Mapping[G, complex] | Callable[[G], complex],
    irrep_dim: int,
) -> SparseMatrix[int, complex]:
    r"""Compute the Schur-Maschke canonical projection operator onto an isotypic component.

    Algebraic Signature:
        $P_\chi = \frac{d_\chi}{|G|} \sum_{g \in G} \overline{\chi(g)} \, \rho(g)$

    Properties:
        - Idempotence: $P_\chi^2 = P_\chi$.
        - Orthogonality: $P_{\chi_i} P_{\chi_j} = \mathbf{0}$ for $i \ne j$.
        - Completeness: $\sum_i P_{\chi_i} = \mathbf{I}_V$.
        - Multiplicity Extraction: $\operatorname{tr}(P_{\chi_i}) = m_i \cdot d_{\chi_i}$.

    Args:
        rep: Reducible (or irreducible) group representation $\rho$.
        elements: `FiniteGroup` or sequence of all elements of $G$.
        irrep_chi: Mapping or callable returning irreducible character $\chi(g)$ for each $g \in G$.
        irrep_dim: Degree $d_\chi = \chi(e)$ of the target irreducible representation.

    Returns:
        Sparse projection matrix $P_\chi$ of size $\dim(\rho) \times \dim(\rho)$.
    """
    elem_list = _resolve_elements(elements)
    if not elem_list:
        raise ValueError('elements must be a non-empty sequence of group elements.')

    order = len(elem_list)
    coeff = complex(irrep_dim) / order
    acc: dict[int, dict[int, Any]] = {}

    for g in elem_list:
        chi_g = irrep_chi[g] if isinstance(irrep_chi, Mapping) else irrep_chi(g)
        weight = coeff * complex(chi_g).conjugate()
        if abs(weight) <= 1e-15:
            continue
        term = _scale_matrix(rep(g), weight)
        if term:
            acc = dict(add(acc, term))  # type: ignore[arg-type]

    return _prune_matrix(acc)


def is_intertwiner(
    op: SparseMatrix[int, Any],
    rep1: GroupRepresentation[Any, G],
    rep2: GroupRepresentation[Any, G],
    elements: Iterable[G] | FiniteGroup[G],
    tol: float = 1e-9,
) -> bool:
    r"""Check whether a linear map $T: V_1 \to V_2$ is a $G$-equivariant intertwiner.

    Verifies $T \rho_1(g) = \rho_2(g) T$ for every $g \in G$ within tolerance `tol`.
    """
    for g in _resolve_elements(elements):
        lhs = dot(op, rep1(g))
        rhs = dot(rep2(g), op)
        all_rows = set(lhs.keys()) | set(rhs.keys())
        for r in all_rows:
            row_l = lhs.get(r, {})
            row_r = rhs.get(r, {})
            for c in set(row_l.keys()) | set(row_r.keys()):
                diff = complex(row_l.get(c, 0)) - complex(row_r.get(c, 0))
                if abs(diff) > tol:
                    return False
    return True


def reynolds_average(
    op: SparseMatrix[int, Any],
    rep1: GroupRepresentation[Any, G],
    rep2: GroupRepresentation[Any, G],
    elements: Sequence[G] | FiniteGroup[G],
    inv_fn: Callable[[G], G] | None = None,
) -> SparseMatrix[int, complex]:
    r"""Average an arbitrary linear map into an equivariant intertwiner via the Reynolds operator.

    Algebraic Signature:
        $\overline{T} = \frac{1}{|G|} \sum_{g \in G} \rho_2(g)^{-1} T \rho_1(g) \in \mathrm{Hom}_G(V_1, V_2)$

    By Schur's Lemma, for irreducible complex representations $\rho_1, \rho_2$:
        - If $\rho_1 \not\cong \rho_2$, then $\overline{T} = \mathbf{0}$.
        - If $\rho_1 = \rho_2$, then $\overline{T} = \frac{\operatorname{tr}(T)}{\dim V} \mathbf{I}$.
    """
    resolved_inv = inv_fn
    if resolved_inv is None and isinstance(elements, FiniteGroup):
        resolved_inv = elements.inv
    elem_list = _resolve_elements(elements)
    if not elem_list:
        raise ValueError('elements must be a non-empty sequence of group elements.')

    order = len(elem_list)
    acc: dict[int, dict[int, Any]] = {}
    for g in elem_list:
        r2_inv = rep2(resolved_inv(g)) if resolved_inv is not None else inverse(rep2(g))
        conj_term = dot(r2_inv, dot(op, rep1(g)))
        if conj_term:
            acc = dict(add(acc, conj_term))  # type: ignore[arg-type]

    return _prune_matrix(_scale_matrix(acc, 1.0 / order))


__all__ = [
    'ExplicitGroupRep',
    'GroupRepresentation',
    'RepOperator',
    'direct_sum_rep',
    'is_intertwiner',
    'isotypic_projector',
    'reynolds_average',
    'tensor_product_rep',
]
