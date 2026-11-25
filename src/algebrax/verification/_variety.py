r"""
Algebraic variety, Stickelberger companion matrix, polynomial morphism, and coordinate Hopf verifiers.

Provides exact property-based falsification oracles for:
- `verify_affine_variety_laws`: Protocol conformance, coordinate ring reduction, Nullstellensatz
  dimension consistency, Hilbert function monotonicity, and point-membership/smoothness invariants.
- `verify_stickelberger_laws`: Exact companion matrix pairwise commutativity $[M_{x_i}, M_{x_j}] = 0$
  over `Field[V]`, matrix-polynomial ideal annihilation $g(M_{x_1}, \dots, M_{x_n}) = 0$, and
  root-evaluation residual checks.
- `verify_polynomial_map_laws`: Contravariant pullback `RingHom` preservation, ideal annihilation
  $\phi^*(I(W)) = 0$, and geometric-algebraic adjunction $(\phi^* g)(p) = g(\phi(p))$.
- `verify_coordinate_hopf_laws`: Exact `Field[V]` verification of coassociativity, left/right
  counitality, counit homomorphism, and the antipode axiom on $k[G]$.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Sequence
from typing import TypeVar

from algebrax.algebra import (
    CommRing,
    Field,
    GaloisField,
    ModularField,
    Monomial,
    QuotientRing,
    SparseMPoly,
)
from algebrax.matrix import dot as matrix_dot
from algebrax.typing import SparseMatrix
from algebrax.variety import (
    AffineVariety,
    CoordinateHopfAlgebra,
    GeometricVariety,
    PolynomialMap,
    SmoothableVariety,
    companion_matrix,
    enum_variety_points,
    solve_zero_dimensional,
)

V = TypeVar('V')


def _mat_combine_field(
    m1: SparseMatrix[int, V],
    m2: SparseMatrix[int, V],
    op: Callable[[V, V], V],
    field: Field[V],
) -> SparseMatrix[int, V]:
    """Elementwise combine two sparse matrices using `op` over an arbitrary `Field[V]`."""
    is_zero = field.is_zero
    zero = field.zero
    out: dict[int, dict[int, V]] = {}
    for r in set(m1.keys()) | set(m2.keys()):
        r1 = m1.get(r, {})
        r2 = m2.get(r, {})
        new_row: dict[int, V] = {}
        for c in set(r1.keys()) | set(r2.keys()):
            val = op(r1.get(c, zero), r2.get(c, zero))
            if not is_zero(val):
                new_row[c] = val
        if new_row:
            out[r] = new_row
    return out


def _mat_identity_field(dim: int, field: Field[V]) -> SparseMatrix[int, V]:
    one = field.one
    return {i: {i: one} for i in range(dim)}


def _mat_pow_field(
    mat: SparseMatrix[int, V],
    exp: int,
    dim: int,
    field: Field[V],
) -> SparseMatrix[int, V]:
    if exp == 0:
        return _mat_identity_field(dim, field)
    if exp == 1:
        return mat
    res: SparseMatrix[int, V] | None = None
    cur = mat
    k = exp
    while k > 0:
        if k & 1:
            res = cur if res is None else matrix_dot(res, cur, semiring=field)
        k >>= 1
        if k:
            cur = matrix_dot(cur, cur, semiring=field)
    return res if res is not None else _mat_identity_field(dim, field)


def _eval_poly_on_matrices(
    poly: SparseMPoly[V],
    mats: Sequence[SparseMatrix[int, V]],
    dim: int,
    field: Field[V],
) -> SparseMatrix[int, V]:
    """Evaluate a multivariate polynomial g(M_0, ..., M_{n-1}) over `Field[V]`."""
    acc: SparseMatrix[int, V] = {}
    pow_cache: dict[tuple[int, int], SparseMatrix[int, V]] = {}
    for mon, coeff in poly.items():
        if field.is_zero(coeff):
            continue
        term: SparseMatrix[int, V] = {i: {i: coeff} for i in range(dim)}
        for var_idx, exp in enumerate(mon):
            if exp > 0:
                key = (var_idx, exp)
                mat_pow = pow_cache.get(key)
                if mat_pow is None:
                    mat_pow = _mat_pow_field(mats[var_idx], exp, dim, field)
                    pow_cache[key] = mat_pow
                term = matrix_dot(term, mat_pow, semiring=field)
        acc = _mat_combine_field(acc, term, field.add, field)
    return acc


def verify_affine_variety_laws(
    variety: AffineVariety[V],
    points: Sequence[Sequence[V]] = (),
) -> dict[str, bool]:
    r"""Verify structural and algebraic-geometric invariants of an `AffineVariety`.

    Checks:
    - `protocol_conformance`: Satisfies `GeometricVariety` and `SmoothableVariety`.
    - `coordinate_ring_valid`: `coordinate_ring` is a `QuotientRing` / `CommRing` annihilating all generators.
    - `nullstellensatz_consistency`: `is_empty_over_closure() == (krull_dimension() == -1)`.
    - `hilbert_monotonicity`: Affine Hilbert function satisfies
      $0 \le \operatorname{HF}(0) \le \operatorname{HF}(1) \le \operatorname{HF}(2)$ and
      $\operatorname{HF}(d) \le \binom{d + n}{n}$, stabilizing at $|\mathcal{B}|$ in dimension 0.
    - `point_consistency`: On supplied `points`, `contains_point` matches generator evaluation
      and `is_smooth_at => contains_point`.
    """
    protocol_ok = isinstance(variety, GeometricVariety) and isinstance(variety, SmoothableVariety)
    coord_ok = (
        isinstance(variety.coordinate_ring, QuotientRing)
        and isinstance(variety.coordinate_ring, CommRing)
        and all(variety.ideal.reduce(g) == {} for g in variety.ideal.generators)
    )
    dim = variety.krull_dimension()
    null_ok = (variety.is_empty_over_closure() == (dim == -1)) and (dim == variety.dimension())

    n = variety.ambient_dimension
    hf0 = variety.hilbert_function(0)
    hf1 = variety.hilbert_function(1)
    hf2 = variety.hilbert_function(2)
    if variety.is_empty_over_closure():
        hilbert_ok = hf0 == 0 and hf1 == 0 and hf2 == 0
    else:
        hilbert_ok = (
            hf0 == 1
            and hf0 <= hf1 <= hf2
            and hf1 <= math.comb(1 + n, n)
            and hf2 <= math.comb(2 + n, n)
        )
        if variety.is_zero_dimensional():
            basis = variety.quotient_basis()
            if basis is None:
                hilbert_ok = False
            else:
                max_deg = max((sum(m) for m in basis), default=0)
                if variety.hilbert_function(max_deg) != len(basis):
                    hilbert_ok = False

    point_ok = True
    for pt in points:
        in_var = variety.contains_point(pt)
        in_gens = all(variety.ring.field.is_zero(variety.ring.eval(g, pt)) for g in variety.ideal.generators)
        if in_var != in_gens:
            point_ok = False
            break
        if variety.is_smooth_at(pt) and not in_var:
            point_ok = False
            break

    return {
        'protocol_conformance': protocol_ok,
        'coordinate_ring_valid': coord_ok,
        'nullstellensatz_consistency': null_ok,
        'hilbert_monotonicity': hilbert_ok,
        'point_consistency': point_ok,
    }


def verify_stickelberger_laws(
    variety: AffineVariety[V],
    roots: Sequence[Sequence[float | complex]] | None = None,
    *,
    tol: float = 1e-6,
) -> dict[str, bool]:
    r"""Verify Stickelberger's Eigenvalue Theorem invariants for a 0-dimensional variety.

    Checks:
    - `is_zero_dimensional`: Variety is 0-dimensional with finite basis $\mathcal{B}$.
    - `companion_commutativity`: Exact $[M_{x_i}, M_{x_j}] = \mathbf{0}$ over `Field[V]` for all $i < j$.
    - `ideal_annihilation`: Every Gröbner basis generator satisfies $g(M_{x_0}, \dots, M_{x_{n-1}}) = \mathbf{0}$.
    - `root_residuals`: Over characteristic-0 numeric fields, checks all extracted (or supplied)
      roots satisfy $|g(p)| < \text{tol}$ (rejecting empty root witnesses). Over finite fields
      (`ModularField` / `GaloisField`), verifies exact rational points from `enum_variety_points`.
    """
    if not variety.is_zero_dimensional():
        return {
            'is_zero_dimensional': False,
            'companion_commutativity': False,
            'ideal_annihilation': False,
            'root_residuals': False,
        }

    basis = variety.quotient_basis()
    if basis is None:
        return {
            'is_zero_dimensional': False,
            'companion_commutativity': False,
            'ideal_annihilation': False,
            'root_residuals': False,
        }
    dim = len(basis)
    n = variety.ambient_dimension
    field = variety.ring.field
    mats = [companion_matrix(variety, i) for i in range(n)]

    comm_ok = True
    for i, j in itertools.combinations(range(n), 2):
        ab = matrix_dot(mats[i], mats[j], semiring=field)
        ba = matrix_dot(mats[j], mats[i], semiring=field)
        if _mat_combine_field(ab, ba, field.sub, field):
            comm_ok = False
            break

    annihil_ok = all(
        not _eval_poly_on_matrices(g, mats, dim, field) for g in variety.ideal.basis
    )

    if roots is None and isinstance(field, (ModularField, GaloisField)):
        exact_pts = enum_variety_points(variety)
        residuals_ok = all(variety.contains_point(pt) for pt in exact_pts)
    else:
        check_roots = solve_zero_dimensional(variety) if roots is None else roots
        if not check_roots:
            residuals_ok = False
        else:
            residuals_ok = True
            for pt in check_roots:
                for g in variety.ideal.basis:
                    val = 0j
                    for mon, coeff in g.items():
                        term = complex(coeff)  # type: ignore[arg-type]
                        for coord, exp in zip(pt, mon, strict=True):
                            if exp:
                                term *= complex(coord) ** exp
                        val += term
                    if abs(val) > tol:
                        residuals_ok = False
                        break
                if not residuals_ok:
                    break

    return {
        'is_zero_dimensional': True,
        'companion_commutativity': comm_ok,
        'ideal_annihilation': annihil_ok,
        'root_residuals': residuals_ok,
    }


def verify_polynomial_map_laws(
    phi: PolynomialMap[V],
    poly_samples: Sequence[SparseMPoly[V]],
    point_samples: Sequence[Sequence[V]] = (),
) -> dict[str, bool]:
    r"""Verify contravariant functoriality of a `PolynomialMap` $\phi: V \to W$ and $\phi^*: k[W] \to k[V]$.

    Checks:
    - `unit_preservation`: $\phi^*(0) = 0$ and $\phi^*(1) = 1$ in $k[V]$.
    - `ideal_annihilation`: $\phi^*(g) = 0$ in $k[V]$ for every generator $g \in I(W)$.
    - `ring_homomorphism`: $\phi^*(f + g) = \phi^*(f) + \phi^*(g)$ and $\phi^*(fg) = \phi^*(f)\phi^*(g)$ in $k[V]$.
    - `pointwise_adjunction`: For every supplied $p \in V$ and $g \in k[W]$, $\phi(p) \in W$ and
      $(\phi^* g)(p) = g(\phi(p))$ (fails if `point_samples` is non-empty yet contains zero points on $V$).

    Raises:
        ValueError: If `poly_samples` is empty.
    """
    if not poly_samples:
        raise ValueError('verify_polynomial_map_laws requires at least 1 polynomial sample.')

    dom_cr = phi.domain.coordinate_ring
    cod_cr = phi.codomain.coordinate_ring

    unit_ok = phi(cod_cr.zero) == dom_cr.zero and phi(cod_cr.one) == dom_cr.one
    ideal_ok = all(phi(g) == dom_cr.zero for g in phi.codomain.ideal.basis)

    pulled_samples = [phi(p) for p in poly_samples]
    hom_ok = True
    n_samples = len(poly_samples)
    for i in range(n_samples):
        f, pf = poly_samples[i], pulled_samples[i]
        for j in range(i, n_samples):
            g, pg = poly_samples[j], pulled_samples[j]
            if phi(cod_cr.add(f, g)) != dom_cr.add(pf, pg):
                hom_ok = False
                break
            if phi(cod_cr.mul(f, g)) != dom_cr.mul(pf, pg):
                hom_ok = False
                break
        if not hom_ok:
            break

    adj_ok = True
    dom_ring = phi.domain.ring
    cod_ring = phi.codomain.ring
    checked_on_domain = 0
    for pt in point_samples:
        if not phi.domain.contains_point(pt):
            continue
        checked_on_domain += 1
        img = phi.eval_point(pt)
        if not phi.codomain.contains_point(img):
            adj_ok = False
            break
        for g, pg in zip(poly_samples, pulled_samples, strict=True):
            lhs = dom_ring.eval(pg, pt)
            rhs = cod_ring.eval(g, img)
            if not dom_ring.field.is_zero(dom_ring.field.sub(lhs, rhs)):
                adj_ok = False
                break
        if not adj_ok:
            break
    if point_samples and checked_on_domain == 0:
        adj_ok = False

    return {
        'unit_preservation': unit_ok,
        'ideal_annihilation': ideal_ok,
        'ring_homomorphism': hom_ok,
        'pointwise_adjunction': adj_ok,
    }


def verify_coordinate_hopf_laws(
    hopf: CoordinateHopfAlgebra[V],
    samples: Sequence[SparseMPoly[V]],
) -> dict[str, bool]:
    r"""Verify exact `CoordinateHopfAlgebra` axioms over any exact `Field[V]`.

    Checks:
    - `coassociativity`: $(\Delta \otimes \mathrm{id})\Delta(f) = (\mathrm{id} \otimes \Delta)\Delta(f)$.
    - `counitality`: $(\epsilon \otimes \mathrm{id})\Delta(f) = f = (\mathrm{id} \otimes \epsilon)\Delta(f)$.
    - `counit_homomorphism`: $\epsilon(1) = 1$ and $\epsilon(fg) = \epsilon(f)\epsilon(g)$.
    - `coproduct_homomorphism`: $\Delta(1) = 1 \otimes 1$ and $\Delta(fg) = \Delta(f)\Delta(g)$.
    - `antipode_axiom`:
      $\mu(S \otimes \mathrm{id})\Delta(f) = \epsilon(f)\cdot 1 = \mu(\mathrm{id} \otimes S)\Delta(f)$.
    - `antipode_antihomomorphism`: $S(1) = 1$ and $S(fg) = S(g)S(f)$.

    Raises:
        ValueError: If `samples` is empty.
    """
    if not samples:
        raise ValueError('verify_coordinate_hopf_laws requires at least 1 sample polynomial.')

    field = hopf.field
    is_zero = field.is_zero
    f_add = field.add
    f_mul = field.mul
    f_sub = field.sub
    one_scalar = field.one

    coassoc_ok = True
    counit_id_ok = True
    antipode_ok = True

    reduced_samples = [hopf.group_variety.ideal.reduce(elem) for elem in samples]
    delta_samples = [hopf.coproduct(red) for red in reduced_samples]
    antipode_samples = [hopf.antipode(red) for red in reduced_samples]
    counit_samples = [hopf.counit(red) for red in reduced_samples]

    for red, delta, eps_red in zip(reduced_samples, delta_samples, counit_samples, strict=True):
        # 1. Coassociativity in k[G] (x) k[G] (x) k[G]
        left3: dict[tuple[Monomial, Monomial, Monomial], V] = {}
        right3: dict[tuple[Monomial, Monomial, Monomial], V] = {}
        for (u, v), alpha in delta.items():
            for (x, y), beta in hopf.coproduct({u: one_scalar}).items():
                key = (x, y, v)
                nv = f_add(left3.get(key, field.zero), f_mul(alpha, beta))
                if is_zero(nv):
                    left3.pop(key, None)
                else:
                    left3[key] = nv
            for (y, z), gamma in hopf.coproduct({v: one_scalar}).items():
                key = (u, y, z)
                nv = f_add(right3.get(key, field.zero), f_mul(alpha, gamma))
                if is_zero(nv):
                    right3.pop(key, None)
                else:
                    right3[key] = nv
        if left3 != right3:
            coassoc_ok = False

        # 2. Left & right counitality
        l_eval: SparseMPoly[V] = hopf.zero
        r_eval: SparseMPoly[V] = hopf.zero
        for (u, v), alpha in delta.items():
            eps_u = hopf.counit({u: one_scalar})
            eps_v = hopf.counit({v: one_scalar})
            l_eval = hopf.add(l_eval, hopf.smul(f_mul(alpha, eps_u), {v: one_scalar}))
            r_eval = hopf.add(r_eval, hopf.smul(f_mul(alpha, eps_v), {u: one_scalar}))
        if l_eval != red or r_eval != red:
            counit_id_ok = False

        # 3. Antipode axiom: mu(S (x) id)Delta(f) == eps(f)*1 == mu(id (x) S)Delta(f)
        expected = hopf.smul(eps_red, hopf.one)
        l_anti: SparseMPoly[V] = hopf.zero
        r_anti: SparseMPoly[V] = hopf.zero
        for (u, v), alpha in delta.items():
            u_poly = {u: one_scalar}
            v_poly = {v: one_scalar}
            l_anti = hopf.add(l_anti, hopf.smul(alpha, hopf.mul(hopf.antipode(u_poly), v_poly)))
            r_anti = hopf.add(r_anti, hopf.smul(alpha, hopf.mul(u_poly, hopf.antipode(v_poly))))
        if l_anti != expected or r_anti != expected:
            antipode_ok = False

    # 4. Counit, coproduct, and antipode compatibility with algebra multiplication
    counit_hom_ok = is_zero(f_sub(hopf.counit(hopf.one), one_scalar))
    unit_tensor = {(hopf.ring.zero_key, hopf.ring.zero_key): one_scalar}
    coprod_hom_ok = hopf.coproduct(hopf.one) == unit_tensor
    antipode_hom_ok = hopf.antipode(hopf.one) == hopf.one

    n_samples = len(reduced_samples)
    for i in range(n_samples):
        a = reduced_samples[i]
        eps_a = counit_samples[i]
        da = delta_samples[i]
        sa = antipode_samples[i]
        for j in range(i, n_samples):
            b = reduced_samples[j]
            ab = hopf.mul(a, b)
            if counit_hom_ok:
                lhs_e = hopf.counit(ab)
                rhs_e = f_mul(eps_a, counit_samples[j])
                if not is_zero(f_sub(lhs_e, rhs_e)):
                    counit_hom_ok = False
            if coprod_hom_ok and hopf.coproduct(ab) != hopf._tensor_mul(da, delta_samples[j]):
                coprod_hom_ok = False
            if antipode_hom_ok and hopf.antipode(ab) != hopf.mul(antipode_samples[j], sa):
                antipode_hom_ok = False

    return {
        'coassociativity': coassoc_ok,
        'counitality': counit_id_ok,
        'counit_homomorphism': counit_hom_ok,
        'coproduct_homomorphism': coprod_hom_ok,
        'antipode_axiom': antipode_ok,
        'antipode_antihomomorphism': antipode_hom_ok,
    }


__all__ = [
    'verify_affine_variety_laws',
    'verify_coordinate_hopf_laws',
    'verify_polynomial_map_laws',
    'verify_stickelberger_laws',
]
