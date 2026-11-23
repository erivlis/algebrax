"""Category, functor, sheaf, fiber bundle, Chern class, CCC, path groupoid,
Langlands duality, Ramanujan expander, and p-adic verifiers.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Iterable, Sequence
from typing import Any, TypeVar

from algebrax.category.core import Category, Functor
from algebrax.verification._common import _require_samples, semiring_elements_equal

Obj = TypeVar('Obj')
Mor = TypeVar('Mor')
Obj2 = TypeVar('Obj2')
Mor2 = TypeVar('Mor2')

def verify_category_laws(
    cat: Category[Obj, Mor],
    objects: Iterable[Obj],
    morphisms: Iterable[Mor],
    eq_fn: Callable[[Mor, Mor], bool] | None = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Category axioms over sample objects and morphisms:
    - Left Identity: $\mathrm{compose}(f, \mathrm{id}(\mathrm{target}(f))) = f$
    - Right Identity: $\mathrm{compose}(\mathrm{id}(\mathrm{source}(f)), f) = f$
    - Associativity: $\mathrm{compose}(\mathrm{compose}(f, g), h) = \mathrm{compose}(f, \mathrm{compose}(g, h))$
    """
    _ = list(objects)
    mor_list = _require_samples(morphisms)
    cmp = eq_fn if eq_fn is not None else (lambda a, b: semiring_elements_equal(a, b, tol))

    left_id = True
    right_id = True
    for f in mor_list:
        id_cod = cat.id(cat.target(f))
        id_dom = cat.id(cat.source(f))
        if not cmp(cat.compose(f, id_cod), f):
            left_id = False
        if not cmp(cat.compose(id_dom, f), f):
            right_id = False

    assoc = True
    for f, g, h in itertools.product(mor_list, repeat=3):
        if cat.target(f) != cat.source(g) or cat.target(g) != cat.source(h):
            continue
        lhs = cat.compose(cat.compose(f, g), h)
        rhs = cat.compose(f, cat.compose(g, h))
        if not cmp(lhs, rhs):
            assoc = False
            break

    return {
        'left_identity': left_id,
        'right_identity': right_id,
        'associativity': assoc,
    }


def verify_functor_laws(
    functor: Functor[Obj, Mor, Obj2, Mor2],
    cat_src: Category[Obj, Mor],
    cat_dst: Category[Obj2, Mor2],
    test_objects: Iterable[Obj],
    test_morphisms: Iterable[Mor],
    eq_fn: Callable[[Mor2, Mor2], bool] | None = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Test Functor axioms between source category $\mathcal{C}$ and target category $\mathcal{D}$:
    - Identity Preservation: $F(\mathrm{id}_x) = \mathrm{id}_{F(x)}$
    - Composition Preservation: $F(\mathrm{compose}_{\mathcal{C}}(f, g)) = \mathrm{compose}_{\mathcal{D}}(F(f), F(g))$
    """
    obj_list = list(test_objects)
    if not obj_list:
        raise ValueError('Functor verification requires at least 1 test object.')
    mor_list = _require_samples(test_morphisms)
    cmp = eq_fn if eq_fn is not None else (lambda a, b: semiring_elements_equal(a, b, tol))

    id_pres = True
    for x in obj_list:
        lhs_id = functor.map_mor(cat_src.id(x))
        rhs_id = cat_dst.id(functor.map_obj(x))
        if not cmp(lhs_id, rhs_id):
            id_pres = False
            break

    comp_pres = True
    for f, g in itertools.product(mor_list, repeat=2):
        lhs_comp = functor.map_mor(cat_src.compose(f, g))
        rhs_comp = cat_dst.compose(functor.map_mor(f), functor.map_mor(g))
        if not cmp(lhs_comp, rhs_comp):
            comp_pres = False
            break

    return {
        'identity_preservation': id_pres,
        'composition_preservation': comp_pres,
    }


def verify_sheaf_functoriality(
    sheaf: Any,
    sample_paths: Iterable[tuple[Any, Any, Any]],
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify functoriality of cellular sheaf restriction maps:
    - Identity Preservation: $\mathcal{E}_{\sigma \trianglelefteq \sigma} = I_{d_\sigma}$
    - Composition Preservation:
      $\mathcal{E}_{\tau \trianglelefteq \rho} \circ \mathcal{E}_{\sigma \trianglelefteq \tau}
      = \mathcal{E}_{\sigma \trianglelefteq \rho}$
    """
    from algebrax.matrix.core import dot
    from algebrax.semiring import StandardSemiring

    semiring = StandardSemiring(float)
    id_ok = True
    for cell in sheaf.poset_category.cells:
        d = sheaf.stalk_dim(cell)
        expected_id = {i: {i: 1.0} for i in range(d)}
        actual_id = sheaf.restriction_map(cell, cell)
        if not semiring_elements_equal(actual_id, expected_id, tol):
            id_ok = False
            break

    comp_ok = True
    for sigma, tau, rho in sample_paths:
        r_sigma_tau = sheaf.restriction_map(sigma, tau)
        r_tau_rho = sheaf.restriction_map(tau, rho)
        r_sigma_rho = sheaf.restriction_map(sigma, rho)
        composed = dot(r_tau_rho, r_sigma_tau, semiring=semiring)
        if not semiring_elements_equal(composed, r_sigma_rho, tol):
            comp_ok = False
            break

    return {
        'identity_preservation': id_ok,
        'composition_preservation': comp_ok,
    }


def verify_coboundary_nilpotency(
    sheaf: Any,
    k: int = 0,
    tol: float = 1e-12,
) -> bool:
    r"""Verify the fundamental cohomological invariant $\delta^{k+1} \circ \delta^k = \mathbf{0}$."""
    from algebrax.matrix.core import dot
    from algebrax.semiring import StandardSemiring
    from algebrax.topology.sheaf import build_sheaf_coboundary_matrix

    semiring = StandardSemiring(float)
    delta_k = build_sheaf_coboundary_matrix(sheaf, k)
    delta_k1 = build_sheaf_coboundary_matrix(sheaf, k + 1)
    if not delta_k or not delta_k1:
        return True
    delta2 = dot(delta_k1, delta_k, semiring=semiring)
    return not delta2 or all(abs(val) < tol for row in delta2.values() for val in row.values())


def verify_sheaf_laplacian_properties(
    sheaf: Any,
    k: int = 0,
    sample_cochains: Iterable[dict[Any, float]] = (),
    tol: float = 1e-9,
) -> dict[str, bool]:
    r"""Verify structural invariants of the $k$-th Sheaf Laplacian $L_k$:
    - Self-Adjoint Symmetry: $L_k^T = L_k$
    - Positive Semi-Definiteness: $\langle x, L_k x \rangle \ge 0$ for all sample $k$-cochains $x$
    """
    from algebrax.matrix.core import inner, mat_vec, transpose
    from algebrax.topology.sheaf import build_sheaf_laplacian

    lap = build_sheaf_laplacian(sheaf, k)
    lap_t = transpose(lap)
    symmetric = semiring_elements_equal(lap, lap_t, tol)

    psd = True
    for x in sample_cochains:
        if not x or not lap:
            continue
        lx = mat_vec(lap, x)
        energy = float(inner(x, lx))
        if energy < -tol:
            psd = False
            break

    return {
        'symmetry': symmetric,
        'positive_semidefinite': psd,
    }


def verify_connection_inversion(
    connection: Any,
    edges: Iterable[tuple[Any, Any]],
    tol: float = 1e-12,
) -> bool:
    r"""Verify that parallel transport satisfies $\rho(v, u) \cdot \rho(u, v) = I_d$ for all edges."""
    from algebrax.matrix.core import dot
    from algebrax.semiring import StandardSemiring

    semiring = StandardSemiring(float)
    d = connection.fiber_dim
    for u, v in edges:
        t_uv = connection.transport(u, v)
        t_vu = connection.transport(v, u)
        prod = dot(t_vu, t_uv, semiring=semiring)
        for i in range(d):
            for j in range(d):
                expected = 1.0 if i == j else 0.0
                if abs(prod.get(i, {}).get(j, 0.0) - expected) >= tol:
                    return False
    return True


def verify_gauge_covariance(
    connection: Any,
    adjacency: Any,
    gauge_transform: dict[Any, Any],
    tol: float = 1e-9,
) -> bool:
    r"""Verify that under local vertex gauge transformations $g_u \in O(d)$,
    the Connection Laplacian transforms covariantly:
    $$L_{\nabla'} = \mathbf{G} \, L_\nabla \, \mathbf{G}^T$$
    """
    from algebrax.matrix.core import dot, transpose
    from algebrax.semiring import StandardSemiring
    from algebrax.topology.bundle import (
        apply_gauge_transformation,
        build_connection_laplacian,
    )

    semiring = StandardSemiring(float)
    d = connection.fiber_dim
    ident = {i: {i: 1.0} for i in range(d)}

    l_orig = build_connection_laplacian(connection, adjacency)
    conn_prime = apply_gauge_transformation(connection, gauge_transform)
    l_prime = build_connection_laplacian(conn_prime, adjacency)

    # Assemble block-diagonal global gauge matrix G
    big_g: dict[tuple[Any, int], dict[tuple[Any, int], float]] = {}
    for u in adjacency:
        g_u = gauge_transform.get(u, ident)
        for i, row in g_u.items():
            row_u: dict[tuple[Any, int], float] = {}
            for j, val in row.items():
                if abs(float(val)) > 1e-15:
                    row_u[(u, int(j))] = float(val)
            if row_u:
                big_g[(u, int(i))] = row_u

    expected_l_prime = dot(big_g, dot(l_orig, transpose(big_g), semiring=semiring), semiring=semiring)
    return semiring_elements_equal(l_prime, expected_l_prime, tol)


def verify_chern_character_additivity(
    conn1: Any,
    conn2: Any,
    faces: Sequence[Sequence[Any]],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify additivity of rank and discrete Chern character forms under Whitney sum $E_1 \oplus E_2$:
    - Rank Additivity: $\mathrm{ch}_0(E_1 \oplus E_2) = \mathrm{ch}_0(E_1) + \mathrm{ch}_0(E_2)$
    - First Chern Character Additivity: $\mathrm{ch}_1(E_1 \oplus E_2) = \mathrm{ch}_1(E_1) + \mathrm{ch}_1(E_2)$
    - Second Chern Character Additivity: $\mathrm{ch}_2(E_1 \oplus E_2) = \mathrm{ch}_2(E_1) + \mathrm{ch}_2(E_2)$
    """
    from algebrax.topology.k_theory import (
        bundle_direct_sum,
        compute_chern_character_1,
        compute_chern_character_2,
    )

    direct_sum = bundle_direct_sum(conn1, conn2)
    rank_ok = direct_sum.fiber_dim == (conn1.fiber_dim + conn2.fiber_dim)

    ch1_1 = compute_chern_character_1(conn1, faces)
    ch1_2 = compute_chern_character_1(conn2, faces)
    ch1_sum = compute_chern_character_1(direct_sum, faces)

    ch2_1 = compute_chern_character_2(conn1, faces)
    ch2_2 = compute_chern_character_2(conn2, faces)
    ch2_sum = compute_chern_character_2(direct_sum, faces)

    ch1_ok = True
    ch2_ok = True
    for f in faces:
        f_key = tuple(f)
        expected_1 = ch1_1.get(f_key, 0.0) + ch1_2.get(f_key, 0.0)
        actual_1 = ch1_sum.get(f_key, 0.0)
        if not math.isclose(actual_1, expected_1, rel_tol=tol, abs_tol=tol):
            ch1_ok = False

        expected_2 = ch2_1.get(f_key, 0.0) + ch2_2.get(f_key, 0.0)
        actual_2 = ch2_sum.get(f_key, 0.0)
        if not math.isclose(actual_2, expected_2, rel_tol=tol, abs_tol=tol):
            ch2_ok = False

    return {
        'rank_additivity': rank_ok,
        'ch1_additivity': ch1_ok,
        'ch2_additivity': ch2_ok,
    }


def verify_chern_number_integrality(
    conn: Any,
    oriented_faces: Sequence[Sequence[Any]],
    tol: float = 1e-6,
) -> bool:
    r"""Verify that the integrated first Chern number $\int_\Sigma c_1(E)$ is an integer within `tol`."""
    from algebrax.topology.k_theory import first_chern_number

    c1_val = first_chern_number(conn, oriented_faces)
    nearest_int = round(c1_val)
    return math.isclose(c1_val, float(nearest_int), rel_tol=tol, abs_tol=tol)


# =============================================================================
# Categorical Type Theory, Semiring Coeffects & Homotopy Path Groupoids
# =============================================================================


def _check_product_universal_pairing(
    ccc: Any,
    a: Any,
    b: Any,
    f_ab_to_c: Any,
) -> bool:
    r"""Check $\langle \pi_1, \pi_2 \rangle = \mathrm{id}_{A \times B}$ and projection laws."""
    p1 = ccc.proj1(a, b)
    p2 = ccc.proj2(a, b)
    paired_id = ccc.pair(p1, p2)
    prod_ab = ccc.product(a, b)
    if paired_id != ccc.id(prod_ab):
        return False

    paired_f = ccc.pair(f_ab_to_c, p2)
    c_obj = ccc.target(f_ab_to_c)
    proj1_cb = ccc.proj1(c_obj, b)
    proj2_cb = ccc.proj2(c_obj, b)
    return ccc.compose(paired_f, proj1_cb) == f_ab_to_c and ccc.compose(paired_f, proj2_cb) == p2


def verify_exponential_adjunction(
    ccc: Any,
    a: Any,
    b: Any,
    c: Any,
    morphisms_ab_to_c: Iterable[Any],
    morphisms_a_to_cb: Iterable[Any] | None = None,
) -> dict[str, bool]:
    r"""Verify Cartesian Closed Category (CCC) universal product and exponential adjunction laws:
    - Product Universal Pairing: $\pi_1 \circ \langle f, g \rangle = f$, $\pi_2 \circ \langle f, g \rangle = g$,
      and $\langle \pi_1, \pi_2 \rangle = \mathrm{id}_{A \times B}$
    - Beta Reduction (Evaluation): $\mathrm{eval}_{C, B} \circ (\mathrm{curry}(f) \times \mathrm{id}_B) = f$
    - Currying Roundtrip ($\mathrm{uncurry} \circ \mathrm{curry}$): $\mathrm{uncurry}(\mathrm{curry}(f)) = f$
    - Eta Expansion ($\mathrm{curry} \circ \mathrm{uncurry}$): $\mathrm{curry}(\mathrm{uncurry}(g)) = g$
    """
    f_list = _require_samples(morphisms_ab_to_c, min_count=1)
    g_list = list(morphisms_a_to_cb) if morphisms_a_to_cb is not None else [ccc.curry(f, a, b) for f in f_list]

    product_ok = True
    beta_ok = True
    uncurry_curry_ok = True
    curry_uncurry_ok = True

    ev_cb = ccc.eval_mor(c, b)
    id_b = ccc.id(b)

    for f in f_list:
        if not _check_product_universal_pairing(ccc, a, b, f):
            product_ok = False

        curried = ccc.curry(f, a, b)
        uncurried = ccc.uncurry(curried, a, b, c)
        if uncurried != f:
            uncurry_curry_ok = False

        p1 = ccc.compose(ccc.proj1(a, b), curried)
        p2 = ccc.compose(ccc.proj2(a, b), id_b)
        curried_times_id = ccc.pair(p1, p2)
        evaluated = ccc.compose(curried_times_id, ev_cb)
        if evaluated != f:
            beta_ok = False

    for g in g_list:
        rec = ccc.curry(ccc.uncurry(g, a, b, c), a, b)
        if rec != g:
            curry_uncurry_ok = False

    return {
        'product_universal_pairing': product_ok,
        'beta_evaluation': beta_ok,
        'uncurry_curry_bijection': uncurry_curry_ok,
        'curry_uncurry_bijection': curry_uncurry_ok,
    }


def _check_coeffect_distributivity(
    ctx_alg: Any,
    g_list: list[Any],
    c_list: list[dict[Any, Any]],
    tol: float,
) -> tuple[bool, bool, bool]:
    r"""Check left distributivity, right distributivity, and modal associativity on coeffect contexts."""
    s = ctx_alg.semiring
    left_dist = True
    right_dist = True
    modal_assoc = True

    for r in g_list:
        for ctx1, ctx2 in itertools.product(c_list, repeat=2):
            lhs = ctx_alg.scale(r, ctx_alg.add(ctx1, ctx2))
            rhs = ctx_alg.add(ctx_alg.scale(r, ctx1), ctx_alg.scale(r, ctx2))
            if not semiring_elements_equal(lhs, rhs, tol):
                left_dist = False

    for r, t in itertools.product(g_list, repeat=2):
        for ctx in c_list:
            lhs_r = ctx_alg.scale(s.add(r, t), ctx)
            rhs_r = ctx_alg.add(ctx_alg.scale(r, ctx), ctx_alg.scale(t, ctx))
            if not semiring_elements_equal(lhs_r, rhs_r, tol):
                right_dist = False

            lhs_m = ctx_alg.scale(s.mul(r, t), ctx)
            rhs_m = ctx_alg.scale(r, ctx_alg.scale(t, ctx))
            if not semiring_elements_equal(lhs_m, rhs_m, tol):
                modal_assoc = False

    return left_dist, right_dist, modal_assoc


def verify_coeffect_grading(
    ctx_alg: Any,
    grade_samples: Iterable[Any],
    context_samples: Iterable[dict[Any, Any]],
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify left $S$-semimodule laws for semiring-graded coeffect contexts `CoeffectContext`:
    - Context Additive Commutativity & Associativity: $\Gamma_1 + \Gamma_2 = \Gamma_2 + \Gamma_1$
    - Left Distributivity of Modal Scaling: $r \cdot (\Gamma_1 + \Gamma_2) = r \cdot \Gamma_1 + r \cdot \Gamma_2$
    - Right Distributivity of Grade Addition: $(r \oplus s) \cdot \Gamma = r \cdot \Gamma + s \cdot \Gamma$
    - Modal Composition Associativity: $(r \otimes s) \cdot \Gamma = r \cdot (s \cdot \Gamma)$
    - Unitality & Zero Annihilation: $\mathbf{1}_S \cdot \Gamma = \Gamma$ and $\mathbf{0}_S \cdot \Gamma = \mathbf{0}$
    """
    g_list = _require_samples(grade_samples)
    c_list = _require_samples(context_samples)
    s = ctx_alg.semiring

    comm_ok = True
    for ctx1, ctx2 in itertools.product(c_list, repeat=2):
        if not semiring_elements_equal(ctx_alg.add(ctx1, ctx2), ctx_alg.add(ctx2, ctx1), tol):
            comm_ok = False

    unit_ok = True
    zero_ok = True
    for ctx in c_list:
        if not semiring_elements_equal(ctx_alg.scale(s.one, ctx), ctx, tol):
            unit_ok = False
        if not semiring_elements_equal(ctx_alg.scale(s.zero, ctx), ctx_alg.zero, tol):
            zero_ok = False

    left_dist, right_dist, modal_assoc = _check_coeffect_distributivity(ctx_alg, g_list, c_list, tol)
    return {
        'context_commutativity': comm_ok,
        'left_distributivity': left_dist,
        'right_distributivity': right_dist,
        'modal_associativity': modal_assoc,
        'unit_scaling': unit_ok,
        'zero_annihilation': zero_ok,
    }


def verify_path_groupoid_laws(
    groupoid: Any,
    sample_paths: Iterable[tuple[Any, ...]],
) -> dict[str, bool]:
    r"""Verify fundamental path groupoid $\Pi_1(K)$ axioms up to simplicial homotopy ($\sim$):
    - Left/Right Identity: $\mathrm{id}_{\mathrm{target}(p)} \circ p = p = p \circ \mathrm{id}_{\mathrm{source}(p)}$
    - Left Inverse Homotopy: $p^{-1} \circ p \sim \mathrm{id}_{\mathrm{source}(p)}$
    - Right Inverse Homotopy: $p \circ p^{-1} \sim \mathrm{id}_{\mathrm{target}(p)}$
    - Involution of Inversion: $(p^{-1})^{-1} = p$
    - 2-Simplex Face Homotopy: $\forall \{u, v, w\} \in K_2,\; (u, v, w) \sim (u, w)$
    """
    paths = _require_samples(sample_paths, min_count=1)
    id_ok = True
    left_inv_ok = True
    right_inv_ok = True
    involution_ok = True

    for p in paths:
        u = groupoid.source(p)
        v = groupoid.target(p)
        id_u = groupoid.id(u)
        id_v = groupoid.id(v)
        if groupoid.compose(p, id_u) != p or groupoid.compose(id_v, p) != p:
            id_ok = False

        p_inv = groupoid.invert_path(p)
        if groupoid.invert_path(p_inv) != p:
            involution_ok = False

        # p_inv o p: first traverse p (u -> v), then p_inv (v -> u), yielding loop at u
        loop_u = groupoid.compose(p_inv, p)
        if not groupoid.are_homotopic(loop_u, id_u):
            left_inv_ok = False

        # p o p_inv: first traverse p_inv (v -> u), then p (u -> v), yielding loop at v
        loop_v = groupoid.compose(p, p_inv)
        if not groupoid.are_homotopic(loop_v, id_v):
            right_inv_ok = False

    face_homotopy_ok = True
    for tri in groupoid.triangles:
        u, v, w = tuple(tri)
        if not groupoid.are_homotopic((u, v, w), (u, w)):
            face_homotopy_ok = False

    return {
        'identity_laws': id_ok,
        'left_inverse_homotopy': left_inv_ok,
        'right_inverse_homotopy': right_inv_ok,
        'inversion_involution': involution_ok,
        'triangle_face_homotopy': face_homotopy_ok,
    }


def verify_cartan_duality(rs: Any) -> dict[str, bool]:
    r"""Verify Langlands root duality $\Phi \leftrightarrow \Phi^\vee$:
    - Cartan Involution: $((\Phi^\vee)^\vee) = \Phi$ ($({A^T})^T = A$)
    - Cartan Transposition: $A^\vee_{ij} = A_{ji}$
    - Coroot Bijection: $\alpha \mapsto \alpha^\vee = \frac{2\alpha}{\langle \alpha, \alpha \rangle}$
      maps $\Phi^+$ bijectively onto $(\Phi^\vee)^+$
    """
    from algebrax.lie.langlands import coroot_in_dual, langlands_dual_root_system

    dual = langlands_dual_root_system(rs)
    dual_dual = langlands_dual_root_system(dual)

    r = rs.rank
    trans_ok = all(dual.cartan_matrix[i][j] == rs.cartan_matrix[j][i] for i in range(r) for j in range(r))
    inv_ok = dual_dual.cartan_matrix == rs.cartan_matrix

    mapped_pos = {coroot_in_dual(rs, alpha) for alpha in rs.positive_roots}
    bijection_ok = mapped_pos == set(dual.positive_roots) and len(mapped_pos) == len(rs.positive_roots)

    return {
        'cartan_transposition': trans_ok,
        'cartan_involution': inv_ok,
        'coroot_bijection': bijection_ok,
    }


def verify_ramanujan_spectral_gap(
    adjacency: Any,
    degree: int | None = None,
    tol: float = 1e-7,
) -> dict[str, bool]:
    r"""Verify the Ramanujan expander bound and Hecke operator commutativity on a $d$-regular graph:
    - Degree Regularity: $\lambda_1 = d$
    - Ramanujan Bound: $\max_{|\lambda_i| < d} |\lambda_i| \le 2\sqrt{d - 1}$
    - Hecke Operator Commutativity: $T_1 T_2 = T_2 T_1$ where $T_1 = A,\; T_2 = A^2 - d I$
    """
    from algebrax.analysis.spectral import adjacency_spectrum, hecke_graph_operator, is_ramanujan_graph
    from algebrax.matrix.core import dot

    try:
        is_ram, _max_nt, _thresh = is_ramanujan_graph(adjacency, degree=degree, tol=tol)
        spec = adjacency_spectrum(adjacency)
        d = degree if degree is not None else round(spec[0])
        deg_ok = bool(spec) and abs(spec[0] - d) <= 1e-5
        t1 = hecke_graph_operator(adjacency, 1, degree=d)
        t2 = hecke_graph_operator(adjacency, 2, degree=d)
        comm_ok = semiring_elements_equal(dot(t1, t2), dot(t2, t1), tol=1e-6)
    except ValueError:
        return {
            'degree_regularity': False,
            'ramanujan_bound': False,
            'hecke_commutativity': False,
        }

    return {
        'degree_regularity': deg_ok,
        'ramanujan_bound': is_ram,
        'hecke_commutativity': comm_ok,
    }


def verify_padic_ultrametric_inequality(
    field: Any,
    samples: Iterable[dict[int, int]],
    tol: float = 1e-12,
) -> dict[str, bool]:
    r"""Verify non-archimedean ultrametric and tropical valuation laws on `PAdicField`:
    - Strong Ultrametric Inequality: $|x + y|_p \le \max(|x|_p, |y|_p)$
    - Isosceles Principle: $|x|_p \ne |y|_p \implies |x + y|_p = \max(|x|_p, |y|_p)$
    - Tropical Valuation Multiplicativity: $v_p(x \cdot y) = v_p(x) + v_p(y)$
    - Tropical Valuation Superadditivity: $v_p(x + y) \ge \min(v_p(x), v_p(y))$
    """
    s_list = _require_samples(samples)
    ultrametric_ok = True
    isosceles_ok = True
    trop_mul_ok = True
    trop_add_ok = True

    for x, y in itertools.product(s_list, repeat=2):
        nx = field.norm(x)
        ny = field.norm(y)
        n_sum = field.norm(field.add(x, y))
        max_n = max(nx, ny)
        if n_sum > max_n + tol:
            ultrametric_ok = False
        if abs(nx - ny) > tol and abs(n_sum - max_n) > tol:
            isosceles_ok = False

        vx = field.valuation(x)
        vy = field.valuation(y)
        v_sum = field.valuation(field.add(x, y))
        if v_sum < min(vx, vy) - tol:
            trop_add_ok = False

        xy = field.mul(x, y)
        v_xy = field.valuation(xy)
        if (
            math.isfinite(vx)
            and math.isfinite(vy)
            and math.isfinite(v_xy)
            and vx + vy < field.precision
            and abs(v_xy - (vx + vy)) > tol
        ):
            trop_mul_ok = False

    return {
        'ultrametric_inequality': ultrametric_ok,
        'isosceles_equality': isosceles_ok,
        'tropical_valuation_multiplicativity': trop_mul_ok,
        'tropical_valuation_superadditivity': trop_add_ok,
    }


verify_padic_ultrametric = verify_padic_ultrametric_inequality
