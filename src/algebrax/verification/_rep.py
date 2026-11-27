"""Representation theory, induction, Lie weights, invariant theory,
quantum groups, and quiver verifiers.
"""

from __future__ import annotations

import cmath
import itertools
import math
from collections.abc import Callable, Sequence
from typing import Any

from algebrax.verification._common import _require_samples, semiring_elements_equal


def _sparse_matrices_close(a: Any, b: Any, tol: float) -> bool:
    """Compare two sparse matrices over union of keys within numerical tolerance."""
    for r in set(a.keys()) | set(b.keys()):
        ra = a.get(r, {})
        rb = b.get(r, {})
        for c in set(ra.keys()) | set(rb.keys()):
            if abs(complex(ra.get(c, 0)) - complex(rb.get(c, 0))) > tol:
                return False
    return True


def _infer_identity_and_inverses(
    elements: Sequence[Any],
    mult: Callable[[Any, Any], Any],
) -> tuple[Any | None, dict[Any, Any]]:
    """Infer two-sided identity and element inverses from a finite group multiplication table."""
    identity = None
    for candidate in elements:
        if all(mult(candidate, x) == x and mult(x, candidate) == x for x in elements):
            identity = candidate
            break
    inv_map: dict[Any, Any] = {}
    if identity is not None:
        for g in elements:
            for h in elements:
                if mult(g, h) == identity and mult(h, g) == identity:
                    inv_map[g] = h
                    break
    return identity, inv_map


def _resolve_rep_context(
    elements: Sequence[Any] | Any,
    mult: Callable[[Any, Any], Any] | None,
    identity: Any | None,
    inv: Callable[[Any], Any] | None,
) -> tuple[list[Any], Callable[[Any, Any], Any], Any | None, Callable[[Any], Any] | None]:
    """Extract element list, multiplication, identity, and inverse from a FiniteGroup or raw arguments."""
    from algebrax.group.finite import FiniteGroup

    if isinstance(elements, FiniteGroup):
        resolved_mult = elements.mul if mult is None else mult
        resolved_id = elements.one if identity is None else identity
        resolved_inv = elements.inv if inv is None else inv
        return list(elements.elements), resolved_mult, resolved_id, resolved_inv

    if mult is None:
        raise ValueError('mult callable is required when elements is not a FiniteGroup.')
    return _require_samples(elements, min_count=1), mult, identity, inv


def _resolve_rep_identity_and_inv(
    elem_list: list[Any],
    mult: Callable[[Any, Any], Any],
    identity: Any | None,
    inv: Callable[[Any], Any] | None,
) -> tuple[Any | None, Callable[[Any], Any] | None]:
    """Resolve group identity element and inverse lookup callable."""
    inferred_id, inv_map = _infer_identity_and_inverses(elem_list, mult)
    resolved_id = identity if identity is not None else inferred_id
    if inv is not None:
        return resolved_id, inv
    if len(inv_map) == len(elem_list):
        return resolved_id, inv_map.get
    return resolved_id, None


def _check_rep_multiplicativity(
    rep: Any,
    elem_list: list[Any],
    mult: Callable[[Any, Any], Any],
    tol: float,
) -> bool:
    """Verify rho(g * h) == rho(g) @ rho(h) across all pairs."""
    from algebrax.matrix.core import dot

    for g in elem_list:
        rg = rep(g)
        for h in elem_list:
            if not _sparse_matrices_close(dot(rg, rep(h)), rep(mult(g, h)), tol):
                return False
    return True


def _check_rep_class_invariance(
    rep: Any,
    elem_list: list[Any],
    mult: Callable[[Any, Any], Any],
    inv_lookup: Callable[[Any], Any] | None,
    tol: float,
) -> bool:
    """Verify character class invariance chi(h * g * h^-1) == chi(g)."""
    from algebrax.matrix.core import trace

    if inv_lookup is None:
        return False
    for g in elem_list:
        chi_g = complex(trace(rep(g)))
        for h in elem_list:
            conj = mult(mult(h, g), inv_lookup(h))
            if abs(complex(trace(rep(conj))) - chi_g) > tol:
                return False
    return True


def verify_representation_homomorphism(
    rep: Any,
    elements: Sequence[Any] | Any,
    mult: Callable[[Any, Any], Any] | None = None,
    identity: Any | None = None,
    inv: Callable[[Any], Any] | None = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify group representation axioms for $\rho : G \to \mathrm{GL}(V)$:
    - Multiplicativity: $\rho(g \cdot h) = \rho(g)\rho(h)$ for all $g, h \in G$
    - Identity Preservation: $\rho(e) = \mathbf{I}_d$
    - Class Function Invariance: $\chi(h g h^{-1}) = \chi(g)$
    """
    elem_list, resolved_mult, resolved_id, resolved_inv = _resolve_rep_context(
        elements, mult, identity, inv
    )
    e, inv_lookup = _resolve_rep_identity_and_inv(elem_list, resolved_mult, resolved_id, resolved_inv)

    mult_ok = _check_rep_multiplicativity(rep, elem_list, resolved_mult, tol)
    id_mat = {i: {i: 1.0} for i in range(rep.dimension)}
    id_ok = e is not None and _sparse_matrices_close(rep(e), id_mat, tol)
    class_inv_ok = _check_rep_class_invariance(rep, elem_list, resolved_mult, inv_lookup, tol)

    return {
        'multiplicativity': mult_ok,
        'identity_preservation': id_ok,
        'class_function_invariance': class_inv_ok,
    }


def _check_schur_row_orthogonality(table: Any, n_irreps: int, tol: float) -> bool:
    """Verify first Schur orthogonality relation: <chi_i, chi_j> == delta_ij."""
    if n_irreps <= 0 or len(table.table) != n_irreps:
        return False
    for i in range(n_irreps):
        for j in range(n_irreps):
            expected = 1.0 + 0.0j if i == j else 0.0 + 0.0j
            ip = table.inner_product(table.table[i], table.table[j])
            if abs(ip - expected) > tol:
                return False
    return True


def _check_schur_col_orthogonality(table: Any, n_classes: int, tol: float) -> bool:
    """Verify second Schur orthogonality relation across conjugacy class columns."""
    if n_classes <= 0 or len(table.class_sizes) != n_classes:
        return False
    for a in range(n_classes):
        for b in range(n_classes):
            col_sum = sum(complex(row[a]) * complex(row[b]).conjugate() for row in table.table)
            expected = (table.group_order / table.class_sizes[a]) if a == b else 0.0
            if abs(col_sum - expected) > tol:
                return False
    return True


def verify_schur_orthogonality(table: Any, tol: float = 1e-7) -> dict[str, bool]:
    r"""Verify first and second Schur orthogonality relations for a `CharacterTable`:
    - Row Orthogonality: $\langle \chi_i, \chi_j \rangle = \delta_{ij}$
    - Column Orthogonality: $\sum_i \chi_i(C_a) \overline{\chi_i(C_b)} = \frac{|G|}{|C_a|} \delta_{ab}$
    """
    row_ok = _check_schur_row_orthogonality(table, len(table.irreps), tol)
    col_ok = _check_schur_col_orthogonality(table, len(table.classes), tol)

    return {
        'row_orthogonality': row_ok,
        'column_orthogonality': col_ok,
    }


def verify_burnside_dimension_formula(
    table: Any,
    identity_idx: int = 0,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify Burnside's irrep degree theorem and conjugacy-class count equality:
    - Dimension Square Sum: $\sum_{i} (\dim V_i)^2 = |G|$
    - Class-Irrep Count Equality: $|\mathrm{Irr}(G)| = |\mathrm{Conj}(G)|$
    """
    dims = [row[identity_idx] for row in table.table]
    pos_int_dims = all(
        abs(complex(d).imag) <= tol and complex(d).real > 0.5 and abs(complex(d).real - round(complex(d).real)) <= tol
        for d in dims
    )
    dim_sq_sum = sum(round(complex(d).real) ** 2 for d in dims) if pos_int_dims else -1
    sum_ok = pos_int_dims and dim_sq_sum == table.group_order
    count_ok = len(table.irreps) == len(table.classes) and sum(table.class_sizes) == table.group_order
    return {
        'dimension_square_sum': sum_ok,
        'class_irrep_count_equality': count_ok,
    }


def verify_schurs_lemma(
    op: Any,
    rep1: Any,
    rep2: Any,
    elements: Sequence[Any] | Any,
    is_equivalent: bool = False,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify Schur's Lemma for a $G$-equivariant intertwiner $T : V_1 \to V_2$:
    - Intertwining: $T \rho_1(g) = \rho_2(g) T$ for all $g \in G$
    - Schur Consequence: $T = \mathbf{0}$ if inequivalent; $T = \lambda \mathbf{I}$ if equal irreps.
    """
    from algebrax.group.finite import FiniteGroup
    from algebrax.matrix.core import trace
    from algebrax.rep.group import is_intertwiner

    raw_elems = elements.elements if isinstance(elements, FiniteGroup) else elements
    elem_list = _require_samples(raw_elems, min_count=1)
    intertwines = is_intertwiner(op, rep1, rep2, elem_list, tol=tol)

    if not is_equivalent:
        schur_ok = _sparse_matrices_close(op, {}, tol)
    elif rep1.dimension != rep2.dimension or rep1.dimension <= 0:
        schur_ok = False
    else:
        lam = complex(trace(op)) / rep1.dimension
        scalar_id = {i: {i: lam} for i in range(rep1.dimension)}
        schur_ok = _sparse_matrices_close(op, scalar_id, tol)

    return {
        'intertwining': intertwines,
        'schur_consequence': schur_ok,
    }


def verify_frobenius_reciprocity(
    char_w: Any,
    char_v: Any,
    group: Any,
    subgroup: Any,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify Frobenius reciprocity and induced degree scaling for $H \le G$:
    - Frobenius Reciprocity: $\langle \chi_{\operatorname{Ind}_H^G(W)}, \chi_V \rangle_G =
      \langle \chi_W, \chi_{\operatorname{Res}_H^G(V)} \rangle_H$
    - Induced Degree Formula: $\chi_{\operatorname{Ind}_H^G(W)}(e) = [G : H] \, \chi_W(e)$
    - Class Function Invariance: $\chi_W$ on $H$ and $\chi_V$ on $G$ are conjugation-invariant
    """
    from algebrax.rep.induction import (
        _as_subgroup,
        _character_element_map,
        _is_class_function_map,
        character_inner_product,
        induced_character,
    )

    h_group = _as_subgroup(group, subgroup)
    map_w = _character_element_map(char_w, h_group)
    map_v = _character_element_map(char_v, group)
    ind_w = induced_character(char_w, group, h_group)
    ind_w_map = _character_element_map(ind_w, group)

    lhs = character_inner_product(ind_w, map_v, group)
    res_v_map = {h: map_v[h] for h in h_group.elements}
    rhs = character_inner_product(map_w, res_v_map, h_group)

    index = group.order // h_group.order
    expected_deg = index * map_w[h_group.identity]
    class_ok = _is_class_function_map(map_w, h_group, tol) and _is_class_function_map(map_v, group, tol)

    return {
        'frobenius_reciprocity': abs(lhs - rhs) <= tol,
        'induced_degree_formula': abs(ind_w_map[group.identity] - expected_deg) <= tol,
        'class_function_invariance': class_ok,
    }


def verify_transitivity_of_induction(
    char_k: Any,
    group_g: Any,
    subgroup_h: Any,
    subgroup_k: Any,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify transitivity of representation induction across a subgroup chain $K \le H \le G$:
    - Transitivity Equality: $\chi_{\operatorname{Ind}_H^G(\operatorname{Ind}_K^H(W))} =
      \chi_{\operatorname{Ind}_K^G(W)}$
    - Degree Multiplicativity: $\dim \operatorname{Ind}_K^G(W) = [G : H][H : K] \dim W$
    - Class Function Invariance: $\chi_W$ is conjugation-invariant on $K$
    """
    from algebrax.rep.induction import (
        _as_subgroup,
        _character_element_map,
        _is_class_function_map,
        induced_character,
    )

    h_group = _as_subgroup(group_g, subgroup_h)
    k_group = _as_subgroup(h_group, subgroup_k)
    map_k = _character_element_map(char_k, k_group)

    ind_k_to_h = induced_character(char_k, h_group, k_group)
    two_step = induced_character(ind_k_to_h, group_g, h_group)
    direct = induced_character(char_k, group_g, k_group)

    two_step_map = _character_element_map(two_step, group_g)
    direct_map = _character_element_map(direct, group_g)

    eq_ok = all(abs(two_step_map[g] - direct_map[g]) <= tol for g in group_g.elements)
    expected_deg = (group_g.order // k_group.order) * map_k[k_group.identity]
    deg_ok = two_step.degree == direct.degree and abs(direct_map[group_g.identity] - expected_deg) <= tol
    class_ok = _is_class_function_map(map_k, k_group, tol)

    return {
        'transitivity_character_equality': eq_ok,
        'degree_multiplicativity': deg_ok,
        'class_function_invariance': class_ok,
    }


def verify_mackey_intertwining(
    char_h: Any,
    char_k: Any,
    group: Any,
    subgroup_h: Any,
    subgroup_k: Any,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify Mackey's intertwining number formula over double cosets $K \backslash G / H$:
    - Mackey Equality: $\langle \chi_{\operatorname{Ind}_H^G W}, \chi_{\operatorname{Ind}_K^G V} \rangle_G =
      \sum_{s \in K \backslash G / H} \langle {}^s W, \operatorname{Res}_{K \cap s H s^{-1}}^K V \rangle$
    - Non-Negative Integer Intertwining: The Mackey sum evaluates to a non-negative integer
    - Double Coset Partition: $\sum_{s \in K \backslash G / H} |K s H| = |G|$
    """
    from algebrax.rep.induction import (
        _as_subgroup,
        _mackey_intertwining_complex,
        character_inner_product,
        induced_character,
    )

    h_group = _as_subgroup(group, subgroup_h)
    k_group = _as_subgroup(group, subgroup_k)

    ind_h = induced_character(char_h, group, h_group)
    ind_k = induced_character(char_k, group, k_group)
    direct_ip = character_inner_product(ind_h, ind_k, group)
    mackey_sum = _mackey_intertwining_complex(char_h, char_k, group, h_group, k_group)

    d_cosets = group.double_cosets(k_group, h_group)
    partition_ok = sum(len(dc) for dc in d_cosets) == group.order
    equality_ok = abs(direct_ip - mackey_sum) <= tol
    int_ok = (
        abs(mackey_sum.imag) <= tol
        and mackey_sum.real >= -tol
        and abs(mackey_sum.real - round(mackey_sum.real)) <= tol
    )

    return {
        'mackey_intertwining_equality': equality_ok,
        'nonnegative_integer_intertwining': int_ok,
        'double_coset_partition_order': partition_ok,
    }


def _sparse_mat_commutator(a: Any, b: Any) -> dict[int, dict[int, Any]]:
    """Compute the matrix commutator [A, B] = AB - BA for sparse matrices."""
    from algebrax.matrix.core import add, dot
    from algebrax.rep.group import _scale_matrix

    return add(dot(a, b), _scale_matrix(dot(b, a), -1.0))


def _sparse_mat_allclose(a: Any, b: Any, tol: float) -> bool:
    """Return True if two sparse matrices agree entrywise within tol."""
    rows = set(a.keys()) | set(b.keys())
    for r in rows:
        ra = a.get(r, {})
        rb = b.get(r, {})
        for c in set(ra.keys()) | set(rb.keys()):
            if abs(complex(ra.get(c, 0.0)) - complex(rb.get(c, 0.0))) > tol:
                return False
    return True


def _sparse_mat_is_zero(mat: Any, tol: float) -> bool:
    """Return True if all entries of a sparse matrix have magnitude <= tol."""
    return all(abs(complex(v)) <= tol for row in mat.values() for v in row.values())


def _eval_lie_rep_linear(rep: Any, coeffs: dict[int, Any]) -> dict[int, dict[int, Any]]:
    """Evaluate a Lie representation on a sparse linear combination of basis generators."""
    return rep(coeffs)


def verify_lie_representation_homomorphism(
    rep: Any,
    algebra: Any = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify that $\rho : \mathfrak{g} \to \mathfrak{gl}(V)$ is a valid Lie algebra representation:
    - Bracket Preservation: $\rho([X_i, X_j]) = [\rho(X_i), \rho(X_j)]$ for all basis pairs $(i, j)$
    - Antisymmetry: $[\rho(X_i), \rho(X_j)] + [\rho(X_j), \rho(X_i)] = 0$ and $[\rho(X_i), \rho(X_i)] = 0$
    - Jacobi Identity: $[\rho(X_i), [\rho(X_j), \rho(X_k)]] + \text{cyclic} = \mathbf{0}$
    """
    from algebrax.matrix.core import add
    from algebrax.rep.lie import _resolve_algebra

    alg = _resolve_algebra(rep, algebra)
    n = alg.dim
    gens = [rep({i: 1.0}) for i in range(n)]

    bracket_ok = True
    antisym_ok = True
    for i in range(n):
        if not _sparse_mat_is_zero(_sparse_mat_commutator(gens[i], gens[i]), tol):
            antisym_ok = False
        for j in range(n):
            comm_ij = _sparse_mat_commutator(gens[i], gens[j])
            expected = _eval_lie_rep_linear(rep, alg.bracket({i: 1.0}, {j: 1.0}))
            if not _sparse_mat_allclose(comm_ij, expected, tol):
                bracket_ok = False
            comm_ji = _sparse_mat_commutator(gens[j], gens[i])
            if not _sparse_mat_is_zero(add(comm_ij, comm_ji), tol):
                antisym_ok = False

    jacobi_ok = True
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                t1 = _sparse_mat_commutator(gens[i], _sparse_mat_commutator(gens[j], gens[k]))
                t2 = _sparse_mat_commutator(gens[j], _sparse_mat_commutator(gens[k], gens[i]))
                t3 = _sparse_mat_commutator(gens[k], _sparse_mat_commutator(gens[i], gens[j]))
                if not _sparse_mat_is_zero(add(add(t1, t2), t3), tol):
                    jacobi_ok = False
                    break
            if not jacobi_ok:
                break
        if not jacobi_ok:
            break

    return {
        'bracket_preservation': bracket_ok,
        'antisymmetry': antisym_ok,
        'jacobi_identity': jacobi_ok,
    }


def verify_casimir_commutativity(
    rep: Any,
    algebra: Any = None,
    killing_metric_inv: Any = None,
    expected_eigenvalue: float | complex | None = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify that the quadratic Casimir operator $C = \sum_{i,j} g^{ij} \rho(X_i)\rho(X_j)$
    commutes with all generators ($[C, \rho(X_k)] = \mathbf{0}$) and optionally equals
    $\lambda \mathbf{I}$ when `expected_eigenvalue` is provided (Schur's lemma / Freudenthal check).
    """
    from algebrax.rep.lie import _resolve_algebra, quadratic_casimir

    alg = _resolve_algebra(rep, algebra)
    casimir = quadratic_casimir(rep, algebra=alg, killing_metric_inv=killing_metric_inv)

    commutes_ok = all(
        _sparse_mat_is_zero(_sparse_mat_commutator(casimir, rep({k: 1.0})), tol)
        for k in range(alg.dim)
    )
    results: dict[str, bool] = {'casimir_commutes': commutes_ok}

    if expected_eigenvalue is not None:
        scaled_id = {i: {i: expected_eigenvalue} for i in range(rep.dimension)}
        results['eigenvalue_matches'] = _sparse_mat_allclose(casimir, scaled_id, tol)

    return results


def _check_cg_selection_rules(
    cg_tensor: dict[tuple[tuple[int, int], int, int], float],
    j1_halves: int,
    j2_halves: int,
) -> bool:
    """Validate angular-momentum selection rules for all stored entries of a CG tensor."""
    j_min = abs(j1_halves - j2_halves)
    j_max = j1_halves + j2_halves
    for (j_h, m_h), m1_h, m2_h in cg_tensor:
        if m_h != m1_h + m2_h:
            return False
        if not (j_min <= j_h <= j_max) or (j_h - j_max) % 2 != 0:
            return False
        if abs(m_h) > j_h or abs(m1_h) > j1_halves or abs(m2_h) > j2_halves:
            return False
    return True


def verify_clebsch_gordan_coupling(
    j1_halves: int,
    j2_halves: int,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify the Clebsch-Gordan coupling matrix $U$ and sparse 3-tensor for spins $j_1, j_2$:
    - Orthogonality: $U^T U = \mathbf{I}$ and $U U^T = \mathbf{I}$
    - Selection Rules: $m = m_1 + m_2$ and $|j_1 - j_2| \le j \le j_1 + j_2$ on all stored entries
    - Intertwiner Equivariance: $U^T (\rho_{j_1} \otimes \rho_{j_2})(X) U = \bigoplus_j \rho_j(X)$ on $\mathfrak{su}(2)$
    """
    from algebrax.matrix.core import dot, transpose
    from algebrax.rep.lie import direct_sum_lie_rep, spin_representation
    from algebrax.tensor.coupling import clebsch_gordan_matrix, clebsch_gordan_tensor

    u_mat, coupled_basis = clebsch_gordan_matrix(j1_halves, j2_halves)
    cg_tensor = clebsch_gordan_tensor(j1_halves, j2_halves)
    dim = (j1_halves + 1) * (j2_halves + 1)
    ident = {i: {i: 1.0} for i in range(dim)}

    u_t = transpose(u_mat)
    orth_ok = (
        len(coupled_basis) == dim
        and _sparse_mat_allclose(dot(u_t, u_mat), ident, tol)
        and _sparse_mat_allclose(dot(u_mat, u_t), ident, tol)
    )
    sel_ok = _check_cg_selection_rules(cg_tensor, j1_halves, j2_halves)

    rep1 = spin_representation(j1_halves, form='su2')
    rep2 = spin_representation(j2_halves, form='su2')
    tensor_rep = rep1.tensor_product(rep2)

    j_values = list(range(j1_halves + j2_halves, abs(j1_halves - j2_halves) - 1, -2))
    coupled_rep = direct_sum_lie_rep([spin_representation(j_h, form='su2') for j_h in j_values])

    equiv_ok = all(
        _sparse_mat_allclose(
            dot(dot(u_t, tensor_rep.generator_matrix(k)), u_mat),
            coupled_rep.generator_matrix(k),
            tol,
        )
        for k in range(tensor_rep.algebra.dim)
    )

    return {
        'orthogonality': orth_ok,
        'selection_rules': sel_ok,
        'intertwiner_equivariance': equiv_ok,
    }


# =============================================================================
# Invariant Theory, Molien Series & Higher-Order Casimir Polynomials
# =============================================================================


def _is_finite_scalar(val: Any) -> bool:
    """Return True if a real or complex scalar is finite."""
    c = complex(val)
    return math.isfinite(c.real) and math.isfinite(c.imag)


def verify_reynolds_idempotency(
    reynolds_fn: Callable[[Callable[[Sequence[Any]], Any]], Callable[[Sequence[Any]], Any]],
    test_poly: Callable[[Sequence[Any]], Any],
    test_point: Sequence[float | complex],
    tol: float = 1e-11,
) -> dict[str, bool]:
    r"""Verify idempotency of a polynomial Reynolds projection operator:
    $$\mathcal{R}(\mathcal{R}(f))(\mathbf{x}) = \mathcal{R}(f)(\mathbf{x})$$
    """
    once = reynolds_fn(test_poly)
    twice = reynolds_fn(once)
    v1 = once(test_point)
    v2 = twice(test_point)
    finite_ok = _is_finite_scalar(v1) and _is_finite_scalar(v2)
    idem_ok = finite_ok and abs(complex(v2) - complex(v1)) <= tol
    return {
        'reynolds_idempotency': idem_ok,
        'finite_values': finite_ok,
    }


def verify_polynomial_invariance(
    poly: Callable[[Sequence[Any]], Any] | dict[tuple[int, ...], float | complex],
    rep: Any,
    elements_or_group: Any,
    dimension: int | None = None,
    num_probes: int = 50,
    seed: int = 42,
    tol: float = 1e-11,
) -> dict[str, bool]:
    r"""Verify group invariance of a polynomial $f(\rho(g)\mathbf{x}) = f(\mathbf{x})$ across
    deterministic Gaussian probe vectors and every element $g \in G$.

    Accepts either a callable $f(\mathbf{x})$ or an unboxed sparse polynomial
    `dict[tuple[int, ...], float | complex]`.
    """
    import random

    from algebrax.group.finite import FiniteGroup
    from algebrax.rep.invariant import _apply_rep_to_vector, evaluate_sparse_polynomial

    if num_probes <= 0:
        raise ValueError(f'num_probes must be positive, got {num_probes}.')

    dim = rep.dimension if dimension is None else dimension
    if dim <= 0:
        raise ValueError(f'dimension must be positive, got {dim}.')

    elements = (
        list(elements_or_group.elements)
        if isinstance(elements_or_group, FiniteGroup)
        else list(elements_or_group)
    )
    if not elements:
        raise ValueError('elements_or_group must be non-empty.')

    poly_fn: Callable[[Sequence[Any]], Any]
    if isinstance(poly, dict):
        poly_dict = poly
        poly_fn = lambda x: evaluate_sparse_polynomial(poly_dict, x)  # noqa: E731
    else:
        poly_fn = poly

    mats = [rep(g) for g in elements]
    rng = random.Random(seed)
    invariant_ok = True
    probes_checked = 0

    for _ in range(num_probes):
        x = [rng.gauss(0.0, 1.0) for _ in range(dim)]
        base_val = complex(poly_fn(x))
        if not _is_finite_scalar(base_val):
            invariant_ok = False
            break
        for mat in mats:
            gx = _apply_rep_to_vector(mat, x)
            moved_val = complex(poly_fn(gx))
            if not _is_finite_scalar(moved_val) or abs(moved_val - base_val) > tol:
                invariant_ok = False
                break
        if not invariant_ok:
            break
        probes_checked += 1

    return {
        'polynomial_invariance': invariant_ok,
        'probe_coverage': probes_checked == num_probes,
    }


def verify_molien_expansion(
    series: Any,
    actual_dimensions: Sequence[int],
) -> dict[str, bool]:
    r"""Verify that a `MolienSeries` Hilbert-Poincare expansion matches empirical homogeneous
    invariant subspace dimensions $\dim K[V]_d^G$ for $d = 0, \dots, D$.
    """
    dims = list(actual_dimensions)
    if not dims:
        raise ValueError('actual_dimensions must be non-empty.')
    expected = series.series(len(dims) - 1)
    return {
        'expansion_matches': list(expected) == dims,
        'nonnegative_dimensions': all(d >= 0 for d in dims) and all(e >= 0 for e in expected),
        'degree_zero_unit': dims[0] == 1 and expected[0] == 1,
    }


def _check_cubic_total_symmetry(
    d_tensor: dict[tuple[int, int, int], float | complex],
    tol: float,
) -> bool:
    """Return True if d_{ijk} is invariant under all 6 permutations of (i, j, k)."""
    for (i, j, k), val in d_tensor.items():
        c_val = complex(val)
        for perm in itertools.permutations((i, j, k)):
            if abs(complex(d_tensor.get(perm, 0.0)) - c_val) > tol:
                return False
    return True


def _check_cubic_ad_invariance(
    algebra: Any,
    d_tensor: dict[tuple[int, int, int], float | complex],
    tol: float,
) -> bool:
    """Return True if sum_l (f_{a i}^l d_{l j k} + f_{a j}^l d_{i l k} + f_{a k}^l d_{i j l}) == 0."""
    n = algebra.dim
    brackets = [[algebra.bracket({a: 1.0}, {i: 1.0}) for i in range(n)] for a in range(n)]
    for a in range(n):
        br_a = brackets[a]
        for i in range(n):
            br_ai = br_a[i]
            for j in range(n):
                br_aj = br_a[j]
                for k in range(n):
                    total = 0.0 + 0.0j
                    for idx_l, f_val in br_ai.items():
                        total += complex(f_val) * complex(d_tensor.get((idx_l, j, k), 0.0))
                    for idx_l, f_val in br_aj.items():
                        total += complex(f_val) * complex(d_tensor.get((i, idx_l, k), 0.0))
                    for idx_l, f_val in br_a[k].items():
                        total += complex(f_val) * complex(d_tensor.get((i, j, idx_l), 0.0))
                    if abs(total) > tol:
                        return False
    return True


def verify_cubic_casimir_invariance(
    algebra: Any,
    d_tensor: dict[tuple[int, int, int], float | complex] | None = None,
    rep: Any = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify total symmetry and Lie-algebra ad-invariance of a cubic symmetric invariant tensor $d_{ijk}$:
    - Total Symmetry: $d_{\sigma(i)\sigma(j)\sigma(k)} = d_{ijk}$ for all $\sigma \in S_3$
    - Adjoint Invariance: $\sum_l (f_{ai}^l d_{ljk} + f_{aj}^l d_{ilk} + f_{ak}^l d_{ijl}) = 0$
    """
    from algebrax.rep.lie import cubic_casimir_tensor

    tensor = cubic_casimir_tensor(algebra, rep=rep, tol=tol) if d_tensor is None else d_tensor
    return {
        'total_symmetry': _check_cubic_total_symmetry(tensor, tol),
        'ad_invariance': _check_cubic_ad_invariance(algebra, tensor, tol),
    }


# =============================================================================
# Quantum Groups, Yang-Baxter Equation & Braided Categories
# =============================================================================


def _sparse_complex_equal(
    lhs: dict[int, dict[int, Any]],
    rhs: dict[int, dict[int, Any]],
    tol: float,
) -> bool:
    """Return True if two sparse complex matrices agree entrywise within tolerance tol."""
    rows = set(lhs.keys()) | set(rhs.keys())
    for r in rows:
        row_l = lhs.get(r, {})
        row_r = rhs.get(r, {})
        for c in set(row_l.keys()) | set(row_r.keys()):
            val_l = complex(row_l.get(c, 0.0))
            val_r = complex(row_r.get(c, 0.0))
            if abs(val_l - val_r) > tol:
                return False
    return True


def _sparse_complex_scale(
    mat: dict[int, dict[int, Any]],
    scalar: complex,
    tol: float,
) -> dict[int, dict[int, complex]]:
    """Scale a sparse complex matrix by scalar and prune entries below tol."""
    out: dict[int, dict[int, complex]] = {}
    for r, row in mat.items():
        scaled = {c: scalar * complex(v) for c, v in row.items() if abs(scalar * complex(v)) > tol}
        if scaled:
            out[r] = scaled
    return out


def _sparse_complex_sub(
    lhs: dict[int, dict[int, Any]],
    rhs: dict[int, dict[int, Any]],
    tol: float,
) -> dict[int, dict[int, complex]]:
    """Compute lhs - rhs for two sparse complex matrices."""
    out: dict[int, dict[int, complex]] = {}
    for r in set(lhs.keys()) | set(rhs.keys()):
        row_l = lhs.get(r, {})
        row_r = rhs.get(r, {})
        diff: dict[int, complex] = {}
        for c in set(row_l.keys()) | set(row_r.keys()):
            val = complex(row_l.get(c, 0.0)) - complex(row_r.get(c, 0.0))
            if abs(val) > tol:
                diff[c] = val
        if diff:
            out[r] = diff
    return out


def verify_quantum_sl2_relations(
    q: complex,
    rep: dict[str, dict[int, dict[int, Any]]],
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify the Drinfeld-Jimbo defining relations of $U_q(\mathfrak{sl}_2)$ on a representation:

    - `k_inverse`: $K K^{-1} = I = K^{-1} K$
    - `k_e_commutation`: $K E K^{-1} = q^2 E$
    - `k_f_commutation`: $K F K^{-1} = q^{-2} F$
    - `e_f_commutator`: $[E, F] = (K - K^{-1}) / (q - q^{-1})$ (or the smooth classical
      L'Hopital Cartan relation $[H, E] = 2E$, $[H, F] = -2F$ for $H = [E, F]$ at $q \to \pm 1$).
    """
    from algebrax.matrix.core import dot

    qc = complex(q)
    if abs(qc) <= 1e-15:
        raise ValueError('q must be non-zero.')

    e_mat = rep['E']
    f_mat = rep['F']
    k_mat = rep['K']
    k_inv_mat = rep['K_inv']

    max_idx = -1
    for mat in (e_mat, f_mat, k_mat, k_inv_mat):
        for r, row in mat.items():
            max_idx = max(max_idx, r)
            for c in row:
                max_idx = max(max_idx, c)
    dim = max_idx + 1
    eye = {i: {i: 1.0 + 0.0j} for i in range(dim)}

    k_inv_ok = _sparse_complex_equal(dot(k_mat, k_inv_mat), eye, tol) and _sparse_complex_equal(
        dot(k_inv_mat, k_mat), eye, tol
    )
    ke_kinv = dot(dot(k_mat, e_mat), k_inv_mat)
    kf_kinv = dot(dot(k_mat, f_mat), k_inv_mat)
    k_e_ok = _sparse_complex_equal(ke_kinv, _sparse_complex_scale(e_mat, qc**2, tol * 1e-3), tol)
    k_f_ok = _sparse_complex_equal(kf_kinv, _sparse_complex_scale(f_mat, qc ** (-2), tol * 1e-3), tol)

    comm_ef = _sparse_complex_sub(dot(e_mat, f_mat), dot(f_mat, e_mat), tol * 1e-3)
    q_diff = qc - 1.0 / qc
    if abs(q_diff) > 1e-10:
        rhs_ef = _sparse_complex_scale(_sparse_complex_sub(k_mat, k_inv_mat, tol * 1e-3), 1.0 / q_diff, tol * 1e-3)
        ef_ok = _sparse_complex_equal(comm_ef, rhs_ef, tol)
    else:
        # Smooth q -> +/-1 classical L'Hopital check on H = [E, F]
        diag_ok = all(r == c for r, row in comm_ef.items() for c in row)
        sign = 1.0 if abs(qc - 1.0) <= 1e-10 or (dim % 2 == 0) else -1.0
        he_comm = _sparse_complex_sub(dot(comm_ef, e_mat), dot(e_mat, comm_ef), tol * 1e-3)
        hf_comm = _sparse_complex_sub(dot(comm_ef, f_mat), dot(f_mat, comm_ef), tol * 1e-3)
        ef_ok = (
            diag_ok
            and _sparse_complex_equal(he_comm, _sparse_complex_scale(e_mat, 2.0 * sign, tol * 1e-3), tol)
            and _sparse_complex_equal(hf_comm, _sparse_complex_scale(f_mat, -2.0 * sign, tol * 1e-3), tol)
        )

    return {
        'k_inverse': k_inv_ok,
        'k_e_commutation': k_e_ok,
        'k_f_commutation': k_f_ok,
        'e_f_commutator': ef_ok,
    }


def verify_yang_baxter_equation(
    r_matrix: dict[int, dict[int, Any]],
    dim: int = 2,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify the Quantum Yang-Baxter Equation $R_{12} R_{13} R_{23} = R_{23} R_{13} R_{12}$
    and the equivalent braided relation $B_1 B_2 B_1 = B_2 B_1 B_2$ for $B = P \circ R$
    using pure sparse coordinate embeddings in $V^{\otimes 3}$.
    """
    from algebrax.matrix.core import dot
    from algebrax.rep.quantum import _embed_r13_operator, _embed_two_site_operator, braiding_operator

    if dim < 1:
        raise ValueError(f'dim must be >= 1, got {dim}.')

    r_norm = {r: {c: complex(v) for c, v in row.items() if abs(v) > tol * 1e-3} for r, row in r_matrix.items()}
    r_norm = {r: row for r, row in r_norm.items() if row}
    non_zero = bool(r_norm)

    r12 = _embed_two_site_operator(r_norm, 0, 3, dim=dim, tol=tol * 1e-3)
    r13 = _embed_r13_operator(r_norm, dim=dim, tol=tol * 1e-3)
    r23 = _embed_two_site_operator(r_norm, 1, 3, dim=dim, tol=tol * 1e-3)

    lhs = dot(dot(r12, r13), r23)
    rhs = dot(dot(r23, r13), r12)
    qybe_ok = _sparse_complex_equal(lhs, rhs, tol)

    b_mat = braiding_operator(r_norm, dim=dim)
    b1 = _embed_two_site_operator(b_mat, 0, 3, dim=dim, tol=tol * 1e-3)
    b2 = _embed_two_site_operator(b_mat, 1, 3, dim=dim, tol=tol * 1e-3)
    braid_lhs = dot(dot(b1, b2), b1)
    braid_rhs = dot(dot(b2, b1), b2)
    braid_ok = _sparse_complex_equal(braid_lhs, braid_rhs, tol)

    return {
        'non_zero': non_zero,
        'yang_baxter': qybe_ok,
        'braid_form': braid_ok,
    }


def verify_artin_braid_relations(
    b1: dict[int, dict[int, Any]],
    b2: dict[int, dict[int, Any]],
    b3: dict[int, dict[int, Any]] | None = None,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify the Artin braid group relations on sparse strand operators:

    - `braid_relation`: $B_1 B_2 B_1 = B_2 B_1 B_2$
    - If `b3` is provided (for $n \ge 4$ strands):
      - `far_commutativity`: $B_1 B_3 = B_3 B_1$
      - `braid_relation_23`: $B_2 B_3 B_2 = B_3 B_2 B_3$
    """
    from algebrax.matrix.core import dot

    res: dict[str, bool] = {
        'braid_relation': _sparse_complex_equal(dot(dot(b1, b2), b1), dot(dot(b2, b1), b2), tol),
    }
    if b3 is not None:
        res['far_commutativity'] = _sparse_complex_equal(dot(b1, b3), dot(b3, b1), tol)
        res['braid_relation_23'] = _sparse_complex_equal(dot(dot(b2, b3), b2), dot(dot(b3, b2), b3), tol)
    return res


# =============================================================================
# Quiver Representations, Tits Form & Gabriel's ADE Theorem
# =============================================================================


def verify_quiver_morphism_commutation(
    rep1: Any,
    rep2: Any,
    morphism_maps: dict[Any, dict[int, dict[int, Any]]],
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify that vertex linear maps $f = \{f_v : V_v^{(1)} \to V_v^{(2)}\}$ form a valid
    morphism of quiver representations:

    - `same_quiver`: `rep1.quiver == rep2.quiver`
    - `vertex_coverage`: every vertex $v \in V_Q$ has a map in `morphism_maps`
    - `dimension_compatibility`: every entry of $f_v$ lies in $[0, d_v^{(2)}) \times [0, d_v^{(1)})$
    - `edge_commutation`: $f_{t(\alpha)} \circ M_\alpha = N_\alpha \circ f_{s(\alpha)}$ for all $\alpha \in E_Q$.
    """
    from algebrax.rep.quiver import _compose_morphism_check

    same_quiver = bool(rep1.quiver == rep2.quiver)
    if not same_quiver:
        return {
            'same_quiver': False,
            'vertex_coverage': False,
            'dimension_compatibility': False,
            'edge_commutation': False,
        }

    verts = rep1.quiver.vertices
    coverage = all(v in morphism_maps for v in verts)
    if not coverage:
        return {
            'same_quiver': True,
            'vertex_coverage': False,
            'dimension_compatibility': False,
            'edge_commutation': False,
        }

    dims_ok = True
    for v in verts:
        d_in = rep1.dimensions[v]
        d_out = rep2.dimensions[v]
        for r, row in morphism_maps[v].items():
            if r < 0 or r >= d_out:
                dims_ok = False
                break
            for c, val in row.items():
                if abs(complex(val)) > tol * 1e-3 and (c < 0 or c >= d_in):
                    dims_ok = False
                    break
            if not dims_ok:
                break
        if not dims_ok:
            break

    comm_ok = dims_ok and _compose_morphism_check(rep1, rep2, morphism_maps, tol)
    return {
        'same_quiver': True,
        'vertex_coverage': True,
        'dimension_compatibility': dims_ok,
        'edge_commutation': comm_ok,
    }


def verify_quiver_direct_sum(
    rep1: Any,
    rep2: Any,
    direct_sum_rep: Any,
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify that `direct_sum_rep` is a split biproduct $M \oplus N$ of `rep1` and `rep2`
    via canonical inclusion morphisms $\iota_1, \iota_2$ and projection morphisms $\pi_1, \pi_2$.
    """
    if rep1.quiver != rep2.quiver or rep1.quiver != direct_sum_rep.quiver:
        return {
            'dimension_additivity': False,
            'inclusion_1_morphism': False,
            'inclusion_2_morphism': False,
            'projection_1_morphism': False,
            'projection_2_morphism': False,
        }

    quiver = rep1.quiver
    dim_add = all(
        direct_sum_rep.dimensions[v] == rep1.dimensions[v] + rep2.dimensions[v]
        for v in quiver.vertices
    )
    if not dim_add:
        return {
            'dimension_additivity': False,
            'inclusion_1_morphism': False,
            'inclusion_2_morphism': False,
            'projection_1_morphism': False,
            'projection_2_morphism': False,
        }

    iota1: dict[Any, dict[int, dict[int, float]]] = {}
    iota2: dict[Any, dict[int, dict[int, float]]] = {}
    pi1: dict[Any, dict[int, dict[int, float]]] = {}
    pi2: dict[Any, dict[int, dict[int, float]]] = {}

    for v in quiver.vertices:
        d1 = rep1.dimensions[v]
        d2 = rep2.dimensions[v]
        iota1[v] = {i: {i: 1.0} for i in range(d1)}
        iota2[v] = {d1 + i: {i: 1.0} for i in range(d2)}
        pi1[v] = {i: {i: 1.0} for i in range(d1)}
        pi2[v] = {i: {d1 + i: 1.0} for i in range(d2)}

    inc1_ok = all(verify_quiver_morphism_commutation(rep1, direct_sum_rep, iota1, tol).values())
    inc2_ok = all(verify_quiver_morphism_commutation(rep2, direct_sum_rep, iota2, tol).values())
    proj1_ok = all(verify_quiver_morphism_commutation(direct_sum_rep, rep1, pi1, tol).values())
    proj2_ok = all(verify_quiver_morphism_commutation(direct_sum_rep, rep2, pi2, tol).values())

    return {
        'dimension_additivity': True,
        'inclusion_1_morphism': inc1_ok,
        'inclusion_2_morphism': inc2_ok,
        'projection_1_morphism': proj1_ok,
        'projection_2_morphism': proj2_ok,
    }


def verify_tits_positive_definiteness(
    quiver: Any,
    samples: Sequence[dict[Any, int] | Sequence[int]] | None = None,
) -> dict[str, bool]:
    r"""Verify Gabriel's ADE positive-definiteness criterion on the Euler-Tits quadratic form $q_Q$:

    - `positive_definite`: Exact rational congruence $U^T C_Q U = D$ confirms $C_Q \succ 0$
    - `samples_positive`: $q_Q(\mathbf{d}) > 0$ on all non-zero probe vectors (including any
      exact rational non-positive witness vector when $C_Q$ is not positive definite)
    - `ade_classification`: `classify_representation_type(quiver) == 'finite'`
    - `roots_unit_tits`: Every positive root $\alpha \in \Phi^+$ satisfies $q_Q(\alpha) = 1$
    """
    from algebrax.rep.quiver import (
        _analyze_symmetric_form,
        classify_representation_type,
        gabriel_positive_roots,
        tits_quadratic_form,
    )

    cartan = quiver.symmetric_cartan_matrix()
    definiteness, witness = _analyze_symmetric_form(cartan)
    pd_ok = definiteness == 'positive_definite'
    is_ade = classify_representation_type(quiver) == 'finite'

    probe_vecs: list[dict[Any, int] | Sequence[int]] = []
    n = quiver.num_vertices
    if samples is not None:
        probe_vecs.extend(samples)
    else:
        for i in range(n):
            probe_vecs.append([1 if k == i else 0 for k in range(n)])
        if n > 0:
            probe_vecs.append([1] * n)
    if witness is not None:
        probe_vecs.append(witness)

    samples_pos = True
    for vec in probe_vecs:
        is_zero = all(v == 0 for v in (vec.values() if isinstance(vec, dict) else vec))
        if not is_zero and tits_quadratic_form(quiver, vec) <= 0:
            samples_pos = False
            break

    roots_ok = False
    if is_ade:
        pos_roots = gabriel_positive_roots(quiver)
        roots_ok = all(tits_quadratic_form(quiver, r) == 1 for r in pos_roots)

    return {
        'positive_definite': pd_ok,
        'samples_positive': samples_pos,
        'ade_classification': is_ade,
        'roots_unit_tits': roots_ok,
    }
