r"""
Exact Gröbner basis computation engines over exact fields:
- Hybrid Gebauer-Möller Buchberger reduction (`method='buchberger'`)
- Faugère F4-style symbolic preprocessing & sparse Macaulay matrix RREF (`method='f4'`)
- Strict exact-field guardrail rejecting IEEE-754 floating-point carriers.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, TypeVar

from algebrax.algebra._field import Field
from algebrax.algebra._polynomial import (
    Monomial,
    MultivariatePolynomialAlgebra,
    SparseMPoly,
    monomial_add,
    monomial_divides,
    monomial_lcm,
    monomial_sub,
)

V = TypeVar('V')

GroebnerMethod = Literal['auto', 'f4', 'buchberger']

_INEXACT_TYPE_NAMES: frozenset[str] = frozenset(
    {
        'float',
        'complex',
        'float16',
        'float32',
        'float64',
        'float128',
        'complex64',
        'complex128',
    }
)


def _validate_exact_field(field: Field[Any]) -> None:
    """Reject non-Field or IEEE-754 floating-point fields to prevent cancellation collapse."""
    if not isinstance(field, Field):
        raise TypeError(f'Groebner basis computation requires an exact Field, got {type(field).__name__}.')
    dtype = getattr(field, '_dtype', None)
    one_val = field.one
    zero_val = field.zero
    if (
        isinstance(one_val, (float, complex))
        or isinstance(zero_val, (float, complex))
        or type(one_val).__name__ in _INEXACT_TYPE_NAMES
        or type(zero_val).__name__ in _INEXACT_TYPE_NAMES
        or dtype in (float, complex)
    ):
        raise TypeError(
            'Groebner basis computation requires an exact Field (such as StandardField(Fraction), '
            'ModularField(p), or GaloisField). IEEE-754 floating-point fields suffer '
            'catastrophic cancellation under S-polynomial subtraction.'
        )


def _gm_insert(
    ring: MultivariatePolynomialAlgebra[V],
    basis_list: list[SparseMPoly[V]],
    lms: list[Monomial],
    pairs: list[tuple[int, int]],
    new_poly: SparseMPoly[V],
) -> list[tuple[int, int]]:
    """Insert a monic polynomial into the basis using the Gebauer-Möller UPDATE criteria.

    Applies Buchberger's B-criterion to existing critical pairs, and the M-, F-, and
    Product criteria to newly generated pairs `(k, t)`.
    """
    t = len(basis_list)
    lm_t = ring.lm(new_poly)

    # B-criterion: drop existing pairs (i, j) superseded by lm_t
    filtered_pairs: list[tuple[int, int]] = []
    for i, j in pairs:
        lcm_ij = monomial_lcm(lms[i], lms[j])
        if (
            monomial_divides(lm_t, lcm_ij)
            and monomial_lcm(lms[i], lm_t) != lcm_ij
            and monomial_lcm(lms[j], lm_t) != lcm_ij
        ):
            continue
        filtered_pairs.append((i, j))

    # M-criterion, F-criterion, and Product criterion on new pairs (k, t)
    cands: list[tuple[int, Monomial, bool]] = []
    for k in range(t):
        lcm_k = monomial_lcm(lms[k], lm_t)
        coprime_k = monomial_add(lms[k], lm_t) == lcm_k
        cands.append((k, lcm_k, coprime_k))

    for k, lcm_k, coprime_k in cands:
        if coprime_k:
            continue
        redundant = False
        for k2, lcm_k2, coprime_k2 in cands:
            if k2 == k:
                continue
            if monomial_divides(lcm_k2, lcm_k) and (lcm_k2 != lcm_k or coprime_k2 or k2 < k):
                redundant = True
                break
        if not redundant:
            filtered_pairs.append((k, t))

    basis_list.append(new_poly)
    lms.append(lm_t)
    return filtered_pairs


def _reduce_basis(
    ring: MultivariatePolynomialAlgebra[V],
    basis_list: list[SparseMPoly[V]],
) -> list[SparseMPoly[V]]:
    """Minimalize and autoreduce a Gröbner basis, returning the unique sorted monic basis."""
    monic_list = [ring.make_monic(g) for g in basis_list if g]
    lms = [ring.lm(g) for g in monic_list]

    minimal: list[SparseMPoly[V]] = []
    for i, g_poly in enumerate(monic_list):
        lm_i = lms[i]
        divisible = False
        for j, lm_j in enumerate(lms):
            if i == j:
                continue
            if monomial_divides(lm_j, lm_i) and (lm_j != lm_i or j < i):
                divisible = True
                break
        if not divisible:
            minimal.append(g_poly)

    for i in range(len(minimal)):
        others = [minimal[j] for j in range(len(minimal)) if j != i]
        reduced_poly = ring.reduce_poly(minimal[i], others)
        if reduced_poly:
            minimal[i] = ring.make_monic(reduced_poly)

    result = [g for g in minimal if g]
    result.sort(key=lambda poly: ring.key_fn(ring.lm(poly)), reverse=True)
    return result


def _groebner_buchberger(
    ring: MultivariatePolynomialAlgebra[V],
    generators: Sequence[SparseMPoly[V]],
) -> list[SparseMPoly[V]]:
    """Compute reduced monic Gröbner basis via Gebauer-Möller Buchberger's algorithm."""
    basis_list: list[SparseMPoly[V]] = []
    lms: list[Monomial] = []
    pairs: list[tuple[int, int]] = []

    for gen_poly in generators:
        cleaned = ring.clean(gen_poly)
        if not cleaned:
            continue
        monic = ring.make_monic(cleaned)
        if ring.lm(monic) == ring.zero_key:
            return [ring.one]
        pairs = _gm_insert(ring, basis_list, lms, pairs, monic)

    if not basis_list:
        return []

    while pairs:
        # Normal selection strategy: pick critical pair with smallest LCM under ring.order
        best_idx = min(
            range(len(pairs)),
            key=lambda idx: ring.key_fn(monomial_lcm(lms[pairs[idx][0]], lms[pairs[idx][1]])),
        )
        i, j = pairs.pop(best_idx)
        s_poly = ring.s_poly(basis_list[i], basis_list[j])
        rem = ring.reduce_poly(s_poly, basis_list)
        if rem:
            monic_rem = ring.make_monic(rem)
            if ring.lm(monic_rem) == ring.zero_key:
                return [ring.one]
            pairs = _gm_insert(ring, basis_list, lms, pairs, monic_rem)

    return _reduce_basis(ring, basis_list)


def _sparse_macaulay_rref(
    ring: MultivariatePolynomialAlgebra[V],
    rows: list[SparseMPoly[V]],
) -> list[SparseMPoly[V]]:
    """Exact sparse Gaussian elimination on polynomial rows over `ring.field`.

    Represents the Macaulay matrix purely as sparse polynomial dicts with zero dense allocation.
    """
    pivots: dict[Monomial, SparseMPoly[V]] = {}

    for row in rows:
        cur = dict(row)
        while cur:
            lm = ring.lm(cur)
            piv = pivots.get(lm)
            if piv is not None:
                factor = cur[lm]
                cur = ring.sub(cur, ring.smul(factor, piv))
            else:
                pivots[lm] = ring.make_monic(cur)
                break

    sorted_lms = sorted(pivots.keys(), key=ring.key_fn)
    for idx, lm in enumerate(sorted_lms):
        row = pivots[lm]
        for earlier_lm in reversed(sorted_lms[:idx]):
            if earlier_lm in row:
                coeff = row[earlier_lm]
                row = ring.sub(row, ring.smul(coeff, pivots[earlier_lm]))
        pivots[lm] = ring.make_monic(row)

    return [pivots[m] for m in sorted_lms]


def _f4_symbolic_preprocess(
    ring: MultivariatePolynomialAlgebra[V],
    basis_list: list[SparseMPoly[V]],
    lms: list[Monomial],
    batch: list[tuple[int, int]],
) -> list[SparseMPoly[V]]:
    """Construct S-pair halves and symbolic reducer rows for an F4 degree batch."""
    rows: list[SparseMPoly[V]] = []
    seen_multipliers: set[tuple[int, Monomial]] = set()
    done_monomials: set[Monomial] = set()
    todo_monomials: set[Monomial] = set()
    one = ring.field.one

    for i, j in batch:
        lm_i, lm_j = lms[i], lms[j]
        lcm_ij = monomial_lcm(lm_i, lm_j)
        done_monomials.add(lcm_ij)

        u_i = monomial_sub(lcm_ij, lm_i)
        if (i, u_i) not in seen_multipliers:
            seen_multipliers.add((i, u_i))
            r1 = ring.mul_term(basis_list[i], u_i, one)
            rows.append(r1)
            todo_monomials.update(r1.keys())

        u_j = monomial_sub(lcm_ij, lm_j)
        if (j, u_j) not in seen_multipliers:
            seen_multipliers.add((j, u_j))
            r2 = ring.mul_term(basis_list[j], u_j, one)
            rows.append(r2)
            todo_monomials.update(r2.keys())

    todo_monomials.difference_update(done_monomials)

    while todo_monomials:
        m = todo_monomials.pop()
        if m in done_monomials:
            continue
        done_monomials.add(m)
        best_reducer_idx = -1
        best_len = 0
        for idx, g_lm in enumerate(lms):
            if monomial_divides(g_lm, m):
                cur_len = len(basis_list[idx])
                if best_reducer_idx < 0 or cur_len < best_len:
                    best_reducer_idx = idx
                    best_len = cur_len
        if best_reducer_idx >= 0:
            u = monomial_sub(m, lms[best_reducer_idx])
            reducer_row = ring.mul_term(basis_list[best_reducer_idx], u, one)
            rows.append(reducer_row)
            todo_monomials.update(k for k in reducer_row if k not in done_monomials)

    return rows


def _groebner_f4(
    ring: MultivariatePolynomialAlgebra[V],
    generators: Sequence[SparseMPoly[V]],
) -> list[SparseMPoly[V]]:
    """Compute reduced monic Gröbner basis via F4 symbolic preprocessing and sparse Macaulay RREF."""
    basis_list: list[SparseMPoly[V]] = []
    lms: list[Monomial] = []
    pairs: list[tuple[int, int]] = []

    for gen_poly in generators:
        cleaned = ring.clean(gen_poly)
        if not cleaned:
            continue
        monic = ring.make_monic(cleaned)
        if ring.lm(monic) == ring.zero_key:
            return [ring.one]
        pairs = _gm_insert(ring, basis_list, lms, pairs, monic)

    if not basis_list:
        return []

    while pairs:
        pairs_with_deg = [(sum(monomial_lcm(lms[i], lms[j])), i, j) for i, j in pairs]
        min_deg = min(d for d, _, _ in pairs_with_deg)
        batch = [(i, j) for d, i, j in pairs_with_deg if d == min_deg]
        batch_set = set(batch)
        pairs = [p for p in pairs if p not in batch_set]

        rows = _f4_symbolic_preprocess(ring, basis_list, lms, batch)
        if not rows:
            continue

        echelon = _sparse_macaulay_rref(ring, rows)
        for row in echelon:
            rlm = ring.lm(row)
            if not any(monomial_divides(glm, rlm) for glm in lms):
                if rlm == ring.zero_key:
                    return [ring.one]
                pairs = _gm_insert(ring, basis_list, lms, pairs, row)

    return _reduce_basis(ring, basis_list)


def groebner_basis(
    ring: MultivariatePolynomialAlgebra[V],
    generators: Sequence[SparseMPoly[V]],
    *,
    method: GroebnerMethod = 'auto',
) -> list[SparseMPoly[V]]:
    r"""Compute the unique reduced monic Gröbner basis of $\langle \text{generators} \rangle$.

    Args:
        ring: Multivariate polynomial ring $k[x_1, \dots, x_n]$ over an exact `Field[V]`.
        generators: Finite sequence of generator polynomials in `ring`.
        method: Reduction algorithm:
            - `'auto'` (default): Gebauer-Möller-filtered F4 sparse Macaulay reduction.
            - `'f4'`: Faugère F4-style symbolic preprocessing + sparse Macaulay RREF.
            - `'buchberger'`: Classical Buchberger reduction with Gebauer-Möller criteria.

    Returns:
        Unique sorted reduced monic Gröbner basis under `ring.order` (descending leading monomials).
        Returns `[]` for the zero ideal and `[ring.one]` for the unit ideal $(1)$.

    Raises:
        TypeError: If `ring.field` is an inexact floating-point field (`float` or `complex`).
        ValueError: If `method` is not one of `'auto'`, `'f4'`, or `'buchberger'`.
    """
    _validate_exact_field(ring.field)
    if method not in ('auto', 'f4', 'buchberger'):
        raise ValueError(f"Unknown groebner_basis method {method!r}. Expected 'auto', 'f4', or 'buchberger'.")
    if method == 'buchberger':
        return _groebner_buchberger(ring, generators)
    return _groebner_f4(ring, generators)


__all__ = [
    'GroebnerMethod',
    'groebner_basis',
]
