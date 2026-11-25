r"""
Finite-field algebraic varieties, rational point enumeration, and Boolean $\mathbb{F}_2$ algebraic SAT.

Provides:
- `enum_variety_points`: Exact enumeration of rational points $V(I)(\mathbb{F}_q) \subseteq \mathbb{F}_q^n$
  over prime fields `ModularField(p)` and extension fields `GaloisField(p, irreduc_poly)`,
  with prefix-pruned backtracking over the reduced Gröbner basis.
- `boolean_variety`: Construct a Boolean variety in
  $\mathbb{F}_2[x_1, \dots, x_n] / \langle x_1^2 + x_1, \dots, x_n^2 + x_n \rangle$.
- `solve_f2_sat`: Solve CNF Boolean satisfiability problems algebraically via Nullstellensatz
  and Gröbner basis reduction over $\mathbb{F}_2$.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from typing import Any, TypeVar, cast

from algebrax.algebra import (
    Field,
    GaloisField,
    ModularField,
    MonomialOrder,
    MultivariatePolynomialAlgebra,
    SparseMPoly,
)
from algebrax.variety.affine import AffineVariety

V = TypeVar('V')


def _finite_field_domain(field: Field[V]) -> Sequence[V]:
    """Return all elements of a supported finite field (`ModularField` or `GaloisField`)."""
    if isinstance(field, ModularField):
        return cast(Sequence[V], range(field.p))
    if isinstance(field, GaloisField):
        p = field.p
        ext_deg = len(field.irreduc_poly) - 1
        elements: list[dict[int, int]] = [
            {deg: c for deg, c in enumerate(coeffs) if c != 0}
            for coeffs in itertools.product(range(p), repeat=ext_deg)
        ]
        return cast(Sequence[V], elements)
    raise TypeError(
        f'Finite point enumeration requires ModularField(p) or GaloisField, got {type(field).__name__}.'
    )


def _field_pow(field: Field[V], base: V, exp: int) -> V:
    """Compute base ** exp in `field` via O(log exp) binary exponentiation."""
    res = field.one
    cur = base
    k = exp
    while k > 0:
        if k & 1:
            res = field.mul(res, cur)
        k >>= 1
        if k:
            cur = field.mul(cur, cur)
    return res


def _eval_active_poly(
    field: Field[V],
    poly: SparseMPoly[V],
    active_vars: tuple[int, ...],
    partial: Sequence[V],
) -> V:
    """Evaluate a polynomial using only its active variable indices."""
    zero_elem = field.zero
    is_zero = field.is_zero
    f_mul = field.mul
    f_add = field.add
    acc = zero_elem
    for mon, coeff in poly.items():
        term = coeff
        for i in active_vars:
            exp = mon[i]
            if exp:
                val = partial[i]
                if is_zero(val):
                    term = zero_elem
                    break
                term = f_mul(term, val if exp == 1 else _field_pow(field, val, exp))
        if not is_zero(term):
            acc = f_add(acc, term)
    return acc


def enum_variety_points(
    variety: AffineVariety[V],
) -> list[tuple[V, ...]]:
    r"""Enumerate all rational points $V(I)(\mathbb{F}_q) \subseteq \mathbb{F}_q^n$.

    Supports prime fields `ModularField(p)` and finite extension fields `GaloisField`.
    Automatically selects forward or reverse variable assignment order so triangular / `lex`
    Gröbner bases prune invalid partial assignments at the earliest possible depth.

    Args:
        variety: An `AffineVariety[V]` over `ModularField(p)` or `GaloisField`.

    Returns:
        List of all rational point tuples in $\mathbb{F}_q^n$ satisfying the variety ideal.

    Raises:
        TypeError: If the variety's coefficient field is not a finite field.
    """
    field = variety.ring.field
    if not isinstance(field, (ModularField, GaloisField)):
        raise TypeError(
            f'Finite point enumeration requires ModularField(p) or GaloisField, got {type(field).__name__}.'
        )
    if variety.is_empty_over_closure():
        return []

    domain = _finite_field_domain(field)
    is_galois_dict = isinstance(field, GaloisField)
    n = variety.ambient_dimension
    basis = variety.ideal.basis
    if not basis:
        if is_galois_dict:
            return [
                tuple(cast(V, dict(cast(Any, x))) for x in pt)
                for pt in itertools.product(domain, repeat=n)
            ]
        return list(itertools.product(domain, repeat=n))

    is_zero = field.is_zero
    non_const: list[tuple[SparseMPoly[V], list[int]]] = []
    for g in basis:
        active = [i for i in range(n) if any(m[i] > 0 for m in g)]
        if not active:
            if not is_zero(g.get(variety.ring.zero_key, field.zero)):
                return []
        else:
            non_const.append((g, active))

    # Pick forward (0..n-1) vs reverse (n-1..0) DFS variable order to maximize early pruning
    fwd_score = sum(max(active) for _, active in non_const)
    bwd_score = sum((n - 1 - min(active)) for _, active in non_const)
    use_reverse = bwd_score < fwd_score or (bwd_score == fwd_score and variety.ring.order == 'lex')
    var_order: list[int] = list(range(n - 1, -1, -1)) if use_reverse else list(range(n))
    pos_of_var = {v: depth for depth, v in enumerate(var_order)}

    checks_by_depth: list[list[tuple[SparseMPoly[V], tuple[int, ...]]]] = [[] for _ in range(n)]
    for g, active in non_const:
        trigger_depth = max(pos_of_var[v] for v in active)
        checks_by_depth[trigger_depth].append((g, tuple(active)))

    points: list[tuple[V, ...]] = []
    partial: list[V] = [field.zero] * n

    def _dfs(depth: int) -> None:
        if depth == n:
            if is_galois_dict:
                points.append(tuple(cast(V, dict(cast(Any, x))) for x in partial))
            else:
                points.append(tuple(partial))
            return
        var_idx = var_order[depth]
        level_checks = checks_by_depth[depth]
        for elem in domain:
            partial[var_idx] = elem
            if all(is_zero(_eval_active_poly(field, g, act, partial)) for g, act in level_checks):
                _dfs(depth + 1)

    _dfs(0)
    if isinstance(field, ModularField):
        points.sort()  # type: ignore[type-var]
    return points


def boolean_variety(
    n_vars: int,
    clauses_or_polys: Sequence[SparseMPoly[int]],
    *,
    order: MonomialOrder = 'grevlex',
) -> AffineVariety[int]:
    r"""Construct a Boolean variety in $\mathbb{F}_2[x_1, \dots, x_n] / \langle x_i^2 + x_i \rangle$.

    Automatically adjoins the field equations $x_i^2 + x_i = 0$ over `ModularField(2)` so the
    coordinate ring encodes exact Boolean functions on $\{0, 1\}^n$.

    Args:
        n_vars: Number of Boolean variables ($n \ge 1$).
        clauses_or_polys: Defining Boolean polynomials over $\mathbb{F}_2$.
        order: Monomial ordering (`'grevlex'`, `'grlex'`, or `'lex'`).

    Raises:
        ValueError: If `n_vars < 1`.
    """
    if n_vars < 1:
        raise ValueError(f'n_vars must be at least 1, got {n_vars}.')
    ring = MultivariatePolynomialAlgebra(ModularField(2), n_vars, order=order)
    field_eqs: list[SparseMPoly[int]] = []
    for i in range(n_vars):
        xi = ring.gen(i)
        field_eqs.append(ring.add(ring.mul(xi, xi), xi))
    return AffineVariety(ring, [*clauses_or_polys, *field_eqs])


def solve_f2_sat(
    n_vars: int,
    clauses: Sequence[Sequence[int]],
) -> list[tuple[int, ...]]:
    r"""Solve a CNF Boolean satisfiability formula algebraically over $\mathbb{F}_2$.

    Each clause is a sequence of non-zero 1-indexed DIMACS literals:
    - Positive literal `+k` represents variable $x_{k-1}$ (falsified when $x_{k-1} = 0$, factor $1 + x_{k-1}$).
    - Negative literal `-k` represents $\neg x_{k-1}$ (falsified when $x_{k-1} = 1$, factor $x_{k-1}$).

    A formula is unsatisfiable iff $1 \in I$ (certified by Hilbert's Weak Nullstellensatz).

    Args:
        n_vars: Number of Boolean variables ($n \ge 1$).
        clauses: Sequence of clauses in 1-indexed DIMACS literal format.

    Returns:
        Sorted list of all satisfying assignments in $\{0, 1\}^n$.

    Raises:
        ValueError: If `n_vars < 1` or any literal is 0 or outside `[-n_vars, n_vars]`.

    Example:
        >>> from algebrax.variety import solve_f2_sat
        >>> # (x1 OR x2) AND (NOT x1 OR x2) AND (x1 OR NOT x2) => unique solution (1, 1)
        >>> solve_f2_sat(2, [[1, 2], [-1, 2], [1, -2]])
        [(1, 1)]
    """
    if n_vars < 1:
        raise ValueError(f'n_vars must be at least 1, got {n_vars}.')

    # Validate all literals across all clauses before short-circuiting on empty clauses
    has_empty_clause = False
    dedup_clauses: list[list[int]] = []
    for clause in clauses:
        if not clause:
            has_empty_clause = True
            continue
        seen: set[int] = set()
        tautology = False
        ordered: list[int] = []
        for lit in clause:
            if isinstance(lit, bool) or not isinstance(lit, int) or lit == 0 or abs(lit) > n_vars:
                raise ValueError(f'Literal {lit!r} out of valid 1..{n_vars} range.')
            if -lit in seen:
                tautology = True
            if lit not in seen:
                seen.add(lit)
                ordered.append(lit)
        if not tautology:
            dedup_clauses.append(ordered)

    if has_empty_clause:
        return []

    ring = MultivariatePolynomialAlgebra(ModularField(2), n_vars, order='lex')
    clause_polys: list[SparseMPoly[int]] = []
    for clause in dedup_clauses:
        poly: SparseMPoly[int] = ring.one
        for lit in clause:
            xi = ring.gen(abs(lit) - 1)
            factor = ring.add(ring.one, xi) if lit > 0 else xi
            poly = ring.mul(poly, factor)
        clause_polys.append(poly)

    field_eqs: list[SparseMPoly[int]] = [
        ring.add(ring.mul(ring.gen(i), ring.gen(i)), ring.gen(i)) for i in range(n_vars)
    ]
    var = AffineVariety(ring, [*clause_polys, *field_eqs])
    if var.is_empty_over_closure():
        return []
    return enum_variety_points(var)


__all__ = [
    'boolean_variety',
    'enum_variety_points',
    'solve_f2_sat',
]
