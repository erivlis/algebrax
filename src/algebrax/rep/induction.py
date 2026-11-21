r"""
Induced and Restricted Group Representations, Frobenius Adjunction, and Mackey Theory.

Algebraic Signatures:
    Restriction Functor:    $\operatorname{Res}_H^G : \mathbf{Rep}(G) \longrightarrow \mathbf{Rep}(H)$
    Induction Functor:      $\operatorname{Ind}_H^G : \mathbf{Rep}(H) \longrightarrow \mathbf{Rep}(G), \quad
                             \dim \operatorname{Ind}_H^G(W) = [G : H] \dim W$
    Induced Character:      $\chi_{\operatorname{Ind}_H^G(W)}(g) =
                             \frac{1}{|H|} \sum_{x \in G,\; x^{-1} g x \in H} \chi_W(x^{-1} g x)$
    Frobenius Reciprocity:  $\operatorname{Hom}_G(\operatorname{Ind}_H^G(W), V) \cong
                             \operatorname{Hom}_H(W, \operatorname{Res}_H^G(V))$
    Mackey Decomposition:   $\operatorname{Res}_K^G \operatorname{Ind}_H^G(W) \cong
                             \bigoplus_{s \in K \backslash G / H}
                             \operatorname{Ind}_{K \cap s H s^{-1}}^K ({}^s W)$
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from typing import Any, TypeVar

from algebrax.group.finite import FiniteGroup
from algebrax.matrix.core import dot
from algebrax.rep.character import Character
from algebrax.rep.group import ExplicitGroupRep, GroupRepresentation, _prune_matrix
from algebrax.typing import SparseMatrix

K = TypeVar('K')
G = TypeVar('G', bound=Hashable)


def _as_subgroup(
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> FiniteGroup[G]:
    """Validate and materialize a subgroup $H \\le G$ as a `FiniteGroup[G]`."""
    elems = subgroup.elements if isinstance(subgroup, FiniteGroup) else subgroup
    return group.subgroup(elems)


def _character_element_map(
    char: Character[G] | Mapping[Any, complex],
    group: FiniteGroup[G],
) -> dict[G, complex]:
    """Resolve a conjugacy-class-keyed or element-keyed character to every element of `group`."""
    raw_values = char.values if isinstance(char, Character) else char
    group_set = set(group.elements)
    elem_map: dict[G, complex] = {}

    for key, val in raw_values.items():
        c_val = complex(val)
        if key in group_set:
            elem_map[key] = c_val
        elif isinstance(key, (tuple, frozenset)):
            for el in key:
                if el in group_set:
                    elem_map[el] = c_val

    if len(elem_map) != group.order:
        missing = group.order - len(elem_map)
        raise ValueError(
            f'Character does not cover all elements of group (missing {missing} of {group.order}). '
            'Provide a Character built with Character.from_group or keyed by group elements.'
        )
    return elem_map


def _is_class_function_map(
    elem_map: Mapping[G, complex],
    group: FiniteGroup[G],
    tol: float = 1e-9,
) -> bool:
    """Return True iff `elem_map` is constant on every conjugacy class of `group`."""
    for c_class in group.conjugacy_classes():
        ref = elem_map[c_class[0]]
        if any(abs(elem_map[g] - ref) > tol for g in c_class[1:]):
            return False
    return True


def character_inner_product(
    char_a: Character[G] | Mapping[Any, complex],
    char_b: Character[G] | Mapping[Any, complex],
    group: FiniteGroup[G],
) -> complex:
    r"""Compute the Schur inner product $\langle \chi_a, \chi_b \rangle_G$ over a finite group.

    Algebraic Signature:
        $\langle \chi_a, \chi_b \rangle_G = \frac{1}{|G|} \sum_{g \in G} \chi_a(g)\,\overline{\chi_b(g)}$
    """
    map_a = _character_element_map(char_a, group)
    map_b = _character_element_map(char_b, group)
    total = sum(map_a[g] * map_b[g].conjugate() for g in group.elements)
    return total / group.order


def restrict_representation(
    rep: GroupRepresentation[K, G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> ExplicitGroupRep[K, G]:
    r"""Restrict a group representation $\rho : G \to \mathrm{GL}(V)$ to a subgroup $H \le G$.

    Algebraic Signature:
        $\operatorname{Res}_H^G(\rho)(h) = \rho(h) \quad \forall h \in H$

    Args:
        rep: Representation of the ambient group $G$.
        subgroup: Subgroup $H \le G$ as a `FiniteGroup[G]` or iterable of group elements.

    Returns:
        `ExplicitGroupRep[K, G]` of the same dimension over the elements of $H$.
    """
    h_elems = list(subgroup.elements) if isinstance(subgroup, FiniteGroup) else list(dict.fromkeys(subgroup))
    if not h_elems:
        raise ValueError('subgroup must contain at least one element.')
    mats: dict[G, SparseMatrix[int, K]] = {h: rep(h) for h in h_elems}
    return ExplicitGroupRep(matrices=mats, dimension=rep.dimension)


def restrict_character(
    char_g: Character[G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> Character[G]:
    r"""Restrict a class function character $\chi_V$ of $G$ to conjugacy classes of $H \le G$.

    Algebraic Signature:
        $\chi_{\operatorname{Res}_H^G(V)}(h) = \chi_V(h) \quad \forall h \in H$

    Args:
        char_g: Character of the ambient group $G$.
        group: Parent finite group $G$.
        subgroup: Subgroup $H \le G$ as a `FiniteGroup[G]` or iterable of elements.

    Returns:
        `Character[G]` keyed by the conjugacy classes of $H$.
    """
    h_group = _as_subgroup(group, subgroup)
    map_g = _character_element_map(char_g, group)
    classes_h = h_group.conjugacy_classes()
    vals = {c: map_g[c[0]] for c in classes_h}
    deg = round(map_g[h_group.identity].real)
    return Character(values=vals, degree=deg)


def induced_representation(
    sub_rep: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> ExplicitGroupRep[K, G]:
    r"""Construct the induced representation $\operatorname{Ind}_H^G(W)$ over sparse block matrices.

    Given left coset representatives $G = \bigsqcup_{j=0}^{m-1} g_j H$ with $g_0 = e$ and the
    coset transition law $g \cdot g_j = g_i \cdot h$ ($h \in H$), the $(i, j)$ block of
    $\rho_{\operatorname{Ind}}(g)$ equals $\rho_W(h)$ and all other blocks in column $j$ are zero.

    Algebraic Signature:
        $\operatorname{Ind}_H^G(W) = \mathbb{K}[G] \otimes_{\mathbb{K}[H]} W, \quad
        \dim \operatorname{Ind}_H^G(W) = [G : H] \cdot \dim W$

    Args:
        sub_rep: Representation $\rho_W$ of the subgroup $H$.
        group: Parent finite group $G$.
        subgroup: Subgroup $H \le G$ as a `FiniteGroup[G]` or iterable of elements.

    Returns:
        `ExplicitGroupRep[K, G]` of dimension $[G : H] \cdot \dim(\text{sub\_rep})$ whose matrices
        are sparse block permutation matrices.
    """
    h_group = _as_subgroup(group, subgroup)
    reps, coset_act = group.coset_action(h_group)
    index = len(reps)
    d_w = sub_rep.dimension
    if d_w <= 0:
        raise ValueError('sub_rep must have positive dimension.')

    total_dim = index * d_w
    mats: dict[G, SparseMatrix[int, K]] = {}

    for g in group.elements:
        block_mat: dict[int, dict[int, K]] = {}
        for j in range(index):
            i, h = coset_act(g, j)
            row_offset = i * d_w
            col_offset = j * d_w
            h_mat = sub_rep(h)
            for r_idx, row in h_mat.items():
                target_row = block_mat.setdefault(row_offset + r_idx, {})
                for c_idx, val in row.items():
                    target_row[col_offset + c_idx] = val
        mats[g] = block_mat

    return ExplicitGroupRep(matrices=mats, dimension=total_dim)


def induced_character(
    char_h: Character[G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
) -> Character[G]:
    r"""Compute the induced character $\chi_{\operatorname{Ind}_H^G(W)}$ via Frobenius's formula.

    Algebraic Signature:
        $\chi_{\operatorname{Ind}_H^G(W)}(g) =
        \frac{1}{|H|} \sum_{\substack{x \in G \\ x^{-1} g x \in H}} \chi_W(x^{-1} g x)$

    Args:
        char_h: Character of subgroup $H$ (keyed by $H$-conjugacy classes or $H$-elements).
        group: Parent finite group $G$.
        subgroup: Subgroup $H \le G$ as a `FiniteGroup[G]` or iterable of elements.

    Returns:
        `Character[G]` keyed by the conjugacy classes of $G$ with degree $[G : H] \cdot \chi_W(e)$.
    """
    h_group = _as_subgroup(group, subgroup)
    map_h = _character_element_map(char_h, h_group)
    h_set = set(h_group.elements)
    h_order = h_group.order

    vals: dict[tuple[G, ...], complex] = {}
    for c_class in group.conjugacy_classes():
        g = c_class[0]
        acc = 0.0 + 0.0j
        for x in group.elements:
            conj = group.mul(group.mul(group.inv(x), g), x)
            if conj in h_set:
                acc += map_h[conj]
        vals[c_class] = acc / h_order

    id_class = next(c for c in vals if group.identity in c)
    deg = round(vals[id_class].real)
    return Character(values=vals, degree=deg)


def _infer_domain_dim(mat: SparseMatrix[int, Any], dim_w: int | None) -> int:
    """Resolve and validate the column dimension $d_W$ for Frobenius adjunction maps."""
    max_col = -1
    for row in mat.values():
        if row:
            max_col = max(max_col, max(row.keys()))

    if dim_w is not None:
        if dim_w <= 0:
            raise ValueError('dim_w must be a positive integer.')
        if max_col >= dim_w:
            raise ValueError(f'Matrix has column index {max_col} >= dim_w ({dim_w}).')
        return dim_w

    return max_col + 1


def frobenius_adjoint_transpose(
    hom_h_w_res_v: SparseMatrix[int, K],
    rep_v: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    subgroup: FiniteGroup[G] | Iterable[G],
    dim_w: int | None = None,
) -> SparseMatrix[int, K]:
    r"""Apply the Frobenius reciprocity natural isomorphism $\operatorname{Hom}_H(W, \operatorname{Res}_H^G V)
    \xrightarrow{\;\sim\;} \operatorname{Hom}_G(\operatorname{Ind}_H^G W, V)$.

    For left coset representatives $g_0, \dots, g_{m-1}$ of $G / H$ (with $g_0 = e$) and an
    $H$-intertwiner $T : W \to \operatorname{Res}_H^G(V)$, defines $\widetilde{T}(g_j \otimes w) =
    \rho_V(g_j)\, T(w)$, assembling the horizontal sparse block matrix
    $[\rho_V(g_0) T \mid \rho_V(g_1) T \mid \cdots \mid \rho_V(g_{m-1}) T]$.

    Args:
        hom_h_w_res_v: Sparse matrix of an $H$-equivariant linear map $T : W \to V$.
        rep_v: Ambient group representation $\rho_V : G \to \mathrm{GL}(V)$.
        group: Parent finite group $G$.
        subgroup: Subgroup $H \le G$ as a `FiniteGroup[G]` or iterable of elements.
        dim_w: Dimension $\dim W$ of the subgroup representation. Strongly recommended when
            `hom_h_w_res_v` may have trailing all-zero columns; inferred from column keys if omitted.

    Returns:
        Sparse matrix $\widetilde{T} : \operatorname{Ind}_H^G(W) \to V$ of shape
        $\dim V \times ([G : H] \cdot \dim W)$.
    """
    h_group = _as_subgroup(group, subgroup)
    reps, _ = group.coset_action(h_group)
    resolved_dim_w = _infer_domain_dim(hom_h_w_res_v, dim_w)
    if resolved_dim_w == 0:
        return {}

    result: dict[int, dict[int, Any]] = {}
    for j, rep_g in enumerate(reps):
        block = dot(rep_v(rep_g), hom_h_w_res_v)
        col_offset = j * resolved_dim_w
        for r_idx, row in block.items():
            target_row = result.setdefault(r_idx, {})
            for c_idx, val in row.items():
                target_row[col_offset + c_idx] = val

    return _prune_matrix(result)


def frobenius_adjoint_inverse(
    hom_g_ind_w_v: SparseMatrix[int, K],
    dim_w: int,
) -> SparseMatrix[int, K]:
    r"""Apply the inverse Frobenius reciprocity isomorphism $\operatorname{Hom}_G(\operatorname{Ind}_H^G W, V)
    \xrightarrow{\;\sim\;} \operatorname{Hom}_H(W, \operatorname{Res}_H^G V)$.

    Extracts the identity-coset block $e \otimes W$ (columns $0 \le c < \dim W$), yielding
    $T(w) = \widetilde{T}(e \otimes w)$.

    Args:
        hom_g_ind_w_v: Sparse matrix of a $G$-equivariant map $\widetilde{T} : \operatorname{Ind}_H^G(W) \to V$.
        dim_w: Dimension $\dim W$ of the subgroup representation.

    Returns:
        Sparse matrix $T : W \to \operatorname{Res}_H^G(V)$ of shape $\dim V \times \dim W$.
    """
    if dim_w <= 0:
        raise ValueError('dim_w must be a positive integer.')
    restricted: dict[int, dict[int, K]] = {}
    for r_idx, row in hom_g_ind_w_v.items():
        sub_row = {c_idx: val for c_idx, val in row.items() if 0 <= c_idx < dim_w}
        if sub_row:
            restricted[r_idx] = sub_row
    return restricted


def conjugate_representation(
    sub_rep: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    conjugator: G,
    target_subgroup: FiniteGroup[G] | Iterable[G],
) -> ExplicitGroupRep[K, G]:
    r"""Construct the conjugated representation ${}^s W$ on a subgroup $K_s \le s H s^{-1}$.

    Algebraic Signature:
        $\rho_{{}^s W}(x) = \rho_W(s^{-1} x s) \quad \forall x \in K_s$

    Args:
        sub_rep: Representation $\rho_W$ of $H$.
        group: Ambient finite group $G$.
        conjugator: Group element $s \in G$.
        target_subgroup: Subgroup $K_s \le G$ satisfying $s^{-1} K_s s \subseteq H$.

    Returns:
        `ExplicitGroupRep[K, G]` of dimension $\dim W$ over $K_s$.
    """
    ks_group = _as_subgroup(group, target_subgroup)
    s_inv = group.inv(conjugator)
    mats: dict[G, SparseMatrix[int, K]] = {
        x: sub_rep(group.mul(group.mul(s_inv, x), conjugator)) for x in ks_group.elements
    }
    return ExplicitGroupRep(matrices=mats, dimension=sub_rep.dimension)


def mackey_decomposition(
    sub_rep: GroupRepresentation[K, G],
    group: FiniteGroup[G],
    subgroup_h: FiniteGroup[G] | Iterable[G],
    subgroup_k: FiniteGroup[G] | Iterable[G],
) -> list[tuple[G, ExplicitGroupRep[K, G]]]:
    r"""Decompose $\operatorname{Res}_K^G \operatorname{Ind}_H^G(W)$ via Mackey's Double Coset Theorem.

    Algebraic Signature:
        $\operatorname{Res}_K^G \operatorname{Ind}_H^G(W) \cong
        \bigoplus_{s \in K \backslash G / H}
        \operatorname{Ind}_{K \cap s H s^{-1}}^K \left( {}^s \operatorname{Res}_{s^{-1} K s \cap H}^H W \right)$

    Args:
        sub_rep: Representation $W$ of subgroup $H$.
        group: Ambient finite group $G$.
        subgroup_h: Inducing subgroup $H \le G$.
        subgroup_k: Restricting subgroup $K \le G$.

    Returns:
        List of `(s, summand_rep)` pairs for each double coset representative $s \in K \backslash G / H$,
        where `summand_rep` is an `ExplicitGroupRep[K, G]` of $K$.
    """
    h_group = _as_subgroup(group, subgroup_h)
    k_group = _as_subgroup(group, subgroup_k)
    h_set = set(h_group.elements)
    dc_reps = group.double_coset_representatives(k_group, h_group)

    summands: list[tuple[G, ExplicitGroupRep[K, G]]] = []
    for s in dc_reps:
        s_inv = group.inv(s)
        ks_elems = [x for x in k_group.elements if group.mul(group.mul(s_inv, x), s) in h_set]
        ks_group = k_group.subgroup(ks_elems)
        conj_rep = conjugate_representation(sub_rep, group, s, ks_group)
        ind_summand = induced_representation(conj_rep, k_group, ks_group)
        summands.append((s, ind_summand))
    return summands


def _mackey_intertwining_complex(
    char_h: Character[G],
    char_k: Character[G],
    group: FiniteGroup[G],
    subgroup_h: FiniteGroup[G] | Iterable[G],
    subgroup_k: FiniteGroup[G] | Iterable[G],
) -> complex:
    """Compute the complex Mackey double-coset inner product sum prior to integer rounding."""
    h_group = _as_subgroup(group, subgroup_h)
    k_group = _as_subgroup(group, subgroup_k)
    map_h = _character_element_map(char_h, h_group)
    map_k = _character_element_map(char_k, k_group)
    h_set = set(h_group.elements)
    dc_reps = group.double_coset_representatives(k_group, h_group)

    total = 0.0 + 0.0j
    for s in dc_reps:
        s_inv = group.inv(s)
        ks_pairs: list[tuple[G, G]] = []
        for x in k_group.elements:
            h_conj = group.mul(group.mul(s_inv, x), s)
            if h_conj in h_set:
                ks_pairs.append((x, h_conj))
        orbit_sum = sum(map_h[h_conj] * map_k[x].conjugate() for x, h_conj in ks_pairs)
        total += orbit_sum / len(ks_pairs)
    return total


def mackey_intertwining_number(
    char_h: Character[G],
    char_k: Character[G],
    group: FiniteGroup[G],
    subgroup_h: FiniteGroup[G] | Iterable[G],
    subgroup_k: FiniteGroup[G] | Iterable[G],
    tol: float = 1e-9,
) -> int:
    r"""Compute $\dim \operatorname{Hom}_G(\operatorname{Ind}_H^G W, \operatorname{Ind}_K^G V)$ via Mackey's formula.

    Algebraic Signature:
        $\langle \chi_{\operatorname{Ind}_H^G W}, \chi_{\operatorname{Ind}_K^G V} \rangle_G =
        \sum_{s \in K \backslash G / H}
        \frac{1}{|K \cap s H s^{-1}|}
        \sum_{x \in K \cap s H s^{-1}} \chi_W(s^{-1} x s)\,\overline{\chi_V(x)}$

    As a special case (Mackey's Irreducibility Criterion), setting $H = K$ and $\chi_H = \chi_K$
    tests irreducibility of $\operatorname{Ind}_H^G(W)$: it is irreducible iff the returned integer is `1`.

    Args:
        char_h: Character $\chi_W$ of subgroup $H$.
        char_k: Character $\chi_V$ of subgroup $K$.
        group: Ambient finite group $G$.
        subgroup_h: First subgroup $H \le G$.
        subgroup_k: Second subgroup $K \le G$.
        tol: Numerical tolerance for verifying real integrality of the intertwining number.

    Returns:
        Exact integer intertwining dimension
        $\dim \operatorname{Hom}_G(\operatorname{Ind}_H^G W, \operatorname{Ind}_K^G V)$.
    """
    total = _mackey_intertwining_complex(char_h, char_k, group, subgroup_h, subgroup_k)
    if abs(total.imag) > tol:
        raise ValueError(
            f'Mackey intertwining sum has non-real residual {total.imag}; inputs may not be valid characters.'
        )
    rounded = round(total.real)
    if abs(total.real - rounded) > tol:
        raise ValueError(f'Mackey intertwining sum {total.real} is not an integer within tol={tol}.')
    return rounded


__all__ = [
    'character_inner_product',
    'conjugate_representation',
    'frobenius_adjoint_inverse',
    'frobenius_adjoint_transpose',
    'induced_character',
    'induced_representation',
    'mackey_decomposition',
    'mackey_intertwining_number',
    'restrict_character',
    'restrict_representation',
]
