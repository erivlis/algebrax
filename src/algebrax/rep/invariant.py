r"""
Classical Invariant Theory: Polynomial Reynolds Projection, Molien Series, and Homogeneous Invariants.

Algebraic Signatures:
    Polynomial Reynolds:  $\mathcal{R}(f)(\mathbf{x}) = \frac{1}{|G|} \sum_{g \in G} f(\rho(g^{-1}) \mathbf{x}), \quad
                           \mathcal{R}^2 = \mathcal{R}$
    Molien Series:        $M(t) = \sum_{d=0}^{\infty} \dim(K[V]_d^G)\, t^d
                           = \frac{1}{|G|} \sum_{g \in G} \frac{1}{\det(\mathbf{I}_n - t\rho(g))}$
    Hironaka Form:        $M(t) = \frac{P(t)}{\prod_{i=1}^{n} (1 - t^{d_i})}$
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from algebrax.group.finite import FiniteGroup
from algebrax.matrix.core import add, dot, mat_vec, trace
from algebrax.rep.group import GroupRepresentation, _prune_matrix, _resolve_elements
from algebrax.typing import SparseMatrix

G = TypeVar('G', bound=Hashable)


# =============================================================================
# Pure-Python Polynomial & Cyclotomic Helpers (for Exact Molien Reduction)
# =============================================================================


def _trim_int_poly(coeffs: list[int]) -> list[int]:
    """Remove trailing zeros from an integer polynomial coefficient list."""
    out = list(coeffs)
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def _poly_mul_int(a: Sequence[int], b: Sequence[int]) -> list[int]:
    """Multiply two integer polynomials represented as ascending coefficient lists."""
    res = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            res[i + j] += ai * bj
    return _trim_int_poly(res)


def _poly_exact_div_int(num: Sequence[int], den: Sequence[int]) -> list[int] | None:
    """Return exact integer quotient num / den if den divides num in Z[t], else None."""
    rem = _trim_int_poly(list(num))
    d = _trim_int_poly(list(den))
    if d == [0]:
        return None
    deg_d = len(d) - 1
    lead_d = d[-1]
    if len(rem) < len(d):
        return [0] if rem == [0] else None

    quot = [0] * (len(rem) - len(d) + 1)
    for k in range(len(quot) - 1, -1, -1):
        coeff = rem[k + deg_d]
        if coeff == 0:
            continue
        if coeff % lead_d != 0:
            return None
        q = coeff // lead_d
        quot[k] = q
        for j in range(deg_d + 1):
            rem[k + j] -= q * d[j]

    if any(r != 0 for r in rem):
        return None
    return _trim_int_poly(quot)


def _divisors(n: int) -> list[int]:
    """Return all positive divisors of n in ascending order."""
    small: list[int] = []
    large: list[int] = []
    limit = math.isqrt(n)
    for k in range(1, limit + 1):
        if n % k == 0:
            small.append(k)
            if k != n // k:
                large.append(n // k)
    return small + list(reversed(large))


def _cyclotomic_constant_one(m: int, cache: dict[int, list[int]]) -> list[int]:
    r"""Return $\tilde{\Phi}_m(t) \in \mathbb{Z}[t]$ normalized so $\tilde{\Phi}_m(0) = 1$
    and $1 - t^m = \prod_{d \mid m} \tilde{\Phi}_d(t)$.
    """
    if m in cache:
        return cache[m]
    if m == 1:
        cache[1] = [1, -1]
        return cache[1]

    # 1 - t^m
    poly = [1] + [0] * (m - 1) + [-1]
    for d in _divisors(m):
        if d < m:
            phi_d = _cyclotomic_constant_one(d, cache)
            quot = _poly_exact_div_int(poly, phi_d)
            if quot is None:  # pragma: no cover - mathematically impossible
                raise RuntimeError(f'Cyclotomic factorization failed for m={m}, d={d}.')
            poly = quot
    cache[m] = poly
    return poly


def _faddeev_leverrier_det_i_minus_tm(
    mat: SparseMatrix[int, Any],
    dim: int,
    tol: float = 1e-13,
) -> list[complex]:
    r"""Compute coefficients $[c_0, c_1, \dots, c_n]$ of $\det(\mathbf{I}_n - t M) = \sum_{k=0}^n c_k t^k$
    using the Faddeev-LeVerrier recurrence over sparse matrices.
    """
    if dim == 0:
        return [1.0 + 0.0j]

    ident: dict[int, dict[int, float]] = {i: {i: 1.0} for i in range(dim)}
    coeffs: list[complex] = [1.0 + 0.0j]
    b_prev: dict[int, dict[int, Any]] = ident

    for k in range(1, dim + 1):
        m_b = _prune_matrix(dot(mat, b_prev), tol=tol)
        c_k = -complex(trace(m_b)) / k
        coeffs.append(c_k)
        if k < dim:
            scaled_id = {i: {i: c_k} for i in range(dim)} if abs(c_k) > tol else {}
            b_prev = _prune_matrix(add(m_b, scaled_id), tol=tol)
    return coeffs


def _root_multiplicity(poly: Sequence[complex], root: complex, tol: float = 1e-7) -> int:
    """Return the multiplicity of `root` as a zero of `poly` via derivative evaluation."""
    deriv = list(poly)
    mult = 0
    while deriv:
        val = 0.0 + 0.0j
        power = 1.0 + 0.0j
        for coeff in deriv:
            val += coeff * power
            power *= root
        if abs(val) > tol:
            break
        mult += 1
        deriv = [k * deriv[k] for k in range(1, len(deriv))]
    return mult


def _max_cyclotomic_multiplicity(
    distinct_polys: Sequence[list[complex]],
    m: int,
    tol: float = 1e-7,
) -> int:
    """Return the maximum root multiplicity among primitive m-th roots of unity across all charpolys."""
    max_mult = 0
    for r in range(1, m + 1):
        if math.gcd(r, m) != 1:
            continue
        angle = 2.0 * math.pi * r / m
        root = complex(math.cos(angle), math.sin(angle))
        for poly in distinct_polys:
            mult = _root_multiplicity(poly, root, tol=tol)
            if mult > max_mult:
                max_mult = mult
    return max_mult


def _inverse_series_coeffs(poly: Sequence[complex], max_degree: int) -> list[complex]:
    """Expand 1 / poly(t) up to t^max_degree assuming poly[0] == 1."""
    n = len(poly) - 1
    out: list[complex] = [1.0 + 0.0j] * (max_degree + 1)
    for d in range(1, max_degree + 1):
        acc = 0.0 + 0.0j
        limit = min(d, n)
        for k in range(1, limit + 1):
            acc -= poly[k] * out[d - k]
        out[d] = acc
    return out


def _group_charpolys(
    rep: GroupRepresentation[Any, G],
    elements: Sequence[G],
    dim: int,
) -> list[tuple[int, list[complex]]]:
    """Group identical characteristic polynomials det(I - t rho(g)) with multiplicity weights."""
    grouped: dict[tuple[tuple[float, float], ...], list[Any]] = {}
    for g in elements:
        poly = _faddeev_leverrier_det_i_minus_tm(rep(g), dim)
        key = tuple((round(c.real, 8), round(c.imag, 8)) for c in poly)
        if key in grouped:
            grouped[key][0] += 1
        else:
            grouped[key] = [1, poly]
    return [(entry[0], entry[1]) for entry in grouped.values()]


def _pack_cyclotomic_factors(
    mults: dict[int, int],
    num_poly: list[int],
    cyc_cache: dict[int, list[int]],
) -> tuple[list[int], list[int]]:
    """Pack cyclotomic denominator multiplicities into exactly Krull-dim factors (1 - t^{d_i})."""
    rem = {m: e for m, e in mults.items() if e > 0}
    if not rem:
        return _trim_int_poly(num_poly), []

    k_slots = max(rem.get(1, 0), max(rem.values()))
    slots = [1] * k_slots

    for m in sorted((d for d in rem if d > 1), reverse=True):
        need = rem[m]
        used: set[int] = set()
        for idx, cur in enumerate(slots):
            if need == 0:
                break
            if cur % m == 0:
                used.add(idx)
                need -= 1
        while need > 0:
            avail = [idx for idx in range(len(slots)) if idx not in used]
            best_idx = min(avail, key=lambda idx: (math.lcm(slots[idx], m), slots[idx]))
            slots[best_idx] = math.lcm(slots[best_idx], m)
            used.add(best_idx)
            need -= 1

    # Multiply numerator by any extra cyclotomic factors introduced by prod_i (1 - t^{d_i})
    covered: dict[int, int] = {}
    for d in slots:
        for div in _divisors(d):
            covered[div] = covered.get(div, 0) + 1

    num = list(num_poly)
    for div in sorted(covered.keys()):
        extra = covered[div] - rem.get(div, 0)
        if extra > 0:
            phi_div = _cyclotomic_constant_one(div, cyc_cache)
            for _ in range(extra):
                num = _poly_mul_int(num, phi_div)

    slots.sort()
    return _trim_int_poly(num), slots


def _make_numerator_nonnegative(
    num: list[int],
    factors: list[int],
    max_rounds: int = 8,
) -> tuple[list[int], list[int]]:
    """Attempt to eliminate negative numerator coefficients by multiplying by (1 + t^{d_i}) or (1 + t^{d_i} + ...)."""
    cur_num = _trim_int_poly(num)
    cur_factors = list(factors)

    for _ in range(max_rounds):
        if all(c >= 0 for c in cur_num):
            break
        improved = False
        # Try doubling any factor d -> 2d: multiply numerator by (1 + t^d)
        for idx, d in enumerate(cur_factors):
            mult_poly = [1] + [0] * (d - 1) + [1]
            cand = _poly_mul_int(cur_num, mult_poly)
            if all(c >= 0 for c in cand):
                cur_num = cand
                cur_factors[idx] = 2 * d
                cur_factors.sort()
                improved = True
                break
        if improved:
            break
        # Try multiplying the smallest negative-eliminating candidate factor by 2 or 3
        best_score = sum(1 for c in cur_num if c < 0)
        best_pair: tuple[list[int], list[int]] | None = None
        for idx, d in enumerate(cur_factors):
            for mult_k in (2, 3):
                # (1 - t^{k*d}) / (1 - t^d) = 1 + t^d + ... + t^{(k-1)*d}
                step_poly = [1 if i % d == 0 else 0 for i in range((mult_k - 1) * d + 1)]
                cand = _poly_mul_int(cur_num, step_poly)
                neg_count = sum(1 for c in cand if c < 0)
                if neg_count < best_score:
                    best_score = neg_count
                    new_f = list(cur_factors)
                    new_f[idx] = mult_k * d
                    new_f.sort()
                    best_pair = (cand, new_f)
        if best_pair is None:
            break
        cur_num, cur_factors = best_pair
    return _trim_int_poly(cur_num), cur_factors


# =============================================================================
# Public Invariant Theory API
# =============================================================================


@dataclass(frozen=True)
class MolienSeries:
    r"""Rational generating function $M(t) = \frac{P(t)}{\prod_i (1 - t^{d_i})}$ for graded invariant dimensions.

    Attributes:
        numerator_coeffs: Ascending integer coefficients $(p_0, p_1, \dots, p_k)$ of $P(t) = \sum_j p_j t^j$.
        denominator_factors: Positive integer primary degrees $(d_1, \dots, d_n)$ representing
            $Q(t) = \prod_{i=1}^n (1 - t^{d_i})$.
    """

    numerator_coeffs: tuple[int, ...]
    denominator_factors: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.numerator_coeffs:
            raise ValueError('numerator_coeffs must be non-empty.')
        if any(d <= 0 for d in self.denominator_factors):
            raise ValueError(
                f'All denominator_factors must be positive integers, got {self.denominator_factors!r}.'
            )

    def series(self, max_degree: int) -> list[int]:
        r"""Return exact invariant dimensions $[\dim(K[V]_0^G), \dots, \dim(K[V]_{\text{max\_degree}}^G)]$.

        Uses exact arbitrary-precision integer dynamic programming over the denominator factors
        $(1 - t^{d_i})^{-1}$ with zero floating-point rounding drift.
        """
        if max_degree < 0:
            raise ValueError(f'max_degree must be non-negative, got {max_degree}.')
        dp = [
            int(self.numerator_coeffs[k]) if k < len(self.numerator_coeffs) else 0
            for k in range(max_degree + 1)
        ]
        for d in self.denominator_factors:
            for k in range(d, max_degree + 1):
                dp[k] += dp[k - d]
        return dp

    def coefficient(self, degree: int) -> int:
        r"""Extract the exact invariant subspace dimension $\dim(K[V]_{\text{degree}}^G)$."""
        return self.series(degree)[degree]

    def denominator_coeffs(self) -> tuple[int, ...]:
        r"""Expand $Q(t) = \prod_i (1 - t^{d_i})$ into ascending integer polynomial coefficients."""
        poly = [1]
        for d in self.denominator_factors:
            factor = [1] + [0] * (d - 1) + [-1]
            poly = _poly_mul_int(poly, factor)
        return tuple(poly)

    def evaluate(self, t: float | complex) -> float | complex:
        r"""Evaluate the rational generating function $M(t) = P(t) / \prod_i (1 - t^{d_i})$ at $t$."""
        num: complex = 0.0 + 0.0j
        power: complex = 1.0 + 0.0j
        for c in self.numerator_coeffs:
            num += c * power
            power *= t
        den: complex = 1.0 + 0.0j
        for d in self.denominator_factors:
            den *= 1.0 - (t**d)
        if abs(den) == 0.0:
            raise ZeroDivisionError(f'MolienSeries has a pole at t={t!r}.')
        val = num / den
        if isinstance(t, (int, float)) and abs(val.imag) <= 1e-13:
            return float(val.real)
        return val


def compute_molien_series(
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    tol: float = 1e-7,
) -> MolienSeries:
    r"""Compute the exact Molien generating series for a finite-group representation:

    $$M(t) = \frac{1}{|G|} \sum_{g \in G} \frac{1}{\det(\mathbf{I}_n - t\rho(g))}
           = \frac{P(t)}{\prod_{i=1}^n (1 - t^{d_i})}$$

    Args:
        rep: Group representation $\rho : G \to \mathrm{GL}_n(K)$.
        elements_or_group: A `FiniteGroup[G]` or complete sequence of group elements.
        tol: Numerical tolerance for characteristic polynomial root detection and integrality checks.

    Returns:
        Exact `MolienSeries` with integer numerator coefficients and primary denominator factors.
    """
    elements = _resolve_elements(elements_or_group)
    order = len(elements)
    if order == 0:
        raise ValueError('Group elements must be non-empty.')

    dim = rep.dimension
    grouped = _group_charpolys(rep, elements, dim)
    distinct_polys = [poly for _, poly in grouped]

    # 1. Exact cyclotomic denominator bound Q_bound(t) = prod_{m | |G|} Phi_m(t)^{e_m}
    cyc_cache: dict[int, list[int]] = {}
    mults: dict[int, int] = {}
    q_bound = [1]
    for m in _divisors(order):
        e_m = _max_cyclotomic_multiplicity(distinct_polys, m, tol=tol)
        if e_m > 0:
            mults[m] = e_m
            phi_m = _cyclotomic_constant_one(m, cyc_cache)
            for _ in range(e_m):
                q_bound = _poly_mul_int(q_bound, phi_m)

    deg_q = len(q_bound) - 1

    # 2. Exact integer Taylor coefficients m_0, ..., m_{deg_q} via per-class recurrences
    taylor: list[int] = []
    expanded = [(w, _inverse_series_coeffs(poly, deg_q)) for w, poly in grouped]
    for d in range(deg_q + 1):
        val = sum(w * coeffs[d] for w, coeffs in expanded) / order
        if abs(val.imag) > tol or abs(val.real - round(val.real)) > tol:
            raise ValueError(
                f'Non-integer Molien coefficient {val!r} at degree {d}; '
                'ensure rep is a valid representation of a closed finite group.'
            )
        taylor.append(round(val.real))

    # 3. Exact integer numerator N_bound(t) = M(t) * Q_bound(t) mod t^{deg_q + 1}
    n_bound: list[int] = []
    for k in range(deg_q + 1):
        coeff_k = 0
        for j in range(k + 1):
            coeff_k += taylor[j] * q_bound[k - j]
        n_bound.append(coeff_k)
    n_bound = _trim_int_poly(n_bound)

    # 4. Reduce N_bound / Q_bound to lowest terms in Z[t] by cancelling cyclotomic factors
    for m in sorted(mults.keys(), reverse=True):
        phi_m = _cyclotomic_constant_one(m, cyc_cache)
        while mults[m] > 0:
            quot = _poly_exact_div_int(n_bound, phi_m)
            if quot is None:
                break
            n_bound = quot
            mults[m] -= 1

    # 5. Pack remaining cyclotomic factors into Cohen-Macaulay (1 - t^{d_i}) denominator form
    packed_num, factors = _pack_cyclotomic_factors(mults, n_bound, cyc_cache)
    final_num, final_factors = _make_numerator_nonnegative(packed_num, factors)
    return MolienSeries(
        numerator_coeffs=tuple(final_num),
        denominator_factors=tuple(final_factors),
    )


def _apply_rep_to_vector(
    mat: SparseMatrix[int, Any],
    x: Sequence[float | complex],
) -> list[float | complex]:
    """Compute M @ x for sparse matrix M and dense sequence x."""
    x_sparse = {i: val for i, val in enumerate(x) if val != 0}
    y_sparse = mat_vec(mat, x_sparse)
    return [y_sparse.get(i, 0.0) for i in range(len(x))]


def _resolve_inverse_rep_matrices(
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
) -> list[SparseMatrix[int, Any]]:
    """Return [rho(g^{-1}) for g in G] (using exact group.inv when FiniteGroup is given)."""
    if isinstance(elements_or_group, FiniteGroup):
        return [rep(elements_or_group.inv(g)) for g in elements_or_group.elements]
    elements = _resolve_elements(elements_or_group)
    if not elements:
        raise ValueError('Group elements must be non-empty.')
    # Over a closed finite group, {g^{-1} : g in G} == G, so averaging over rep(g) is exact
    # without assuming orthogonality or unitarity.
    return [rep(g) for g in elements]


def reynolds_polynomial_operator(
    poly_eval: Callable[[Sequence[Any]], Any],
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
) -> Callable[[Sequence[Any]], Any]:
    r"""Return the Reynolds-symmetrized $G$-invariant polynomial callable:

    $$\mathcal{R}(f)(\mathbf{x}) = \frac{1}{|G|} \sum_{g \in G} f(\rho(g^{-1})\mathbf{x})$$

    Complements operator-level `reynolds_average` in `algebrax.rep.group` and is idempotent
    ($\mathcal{R}^2 = \mathcal{R}$).

    Args:
        poly_eval: Callable evaluating a polynomial $f(\mathbf{x})$ on a coordinate sequence.
        rep: Group representation $\rho : G \to \mathrm{GL}_n(K)$.
        elements_or_group: A `FiniteGroup[G]` or complete sequence of group elements.

    Returns:
        Callable evaluating the $G$-invariant projection $\mathcal{R}(f)(\mathbf{x})$.
    """
    inv_mats = _resolve_inverse_rep_matrices(rep, elements_or_group)
    order = len(inv_mats)
    if order == 0:
        raise ValueError('Group elements must be non-empty.')

    def invariant_poly(x: Sequence[Any]) -> Any:
        total: Any = 0.0
        for mat in inv_mats:
            x_g = _apply_rep_to_vector(mat, x)
            total = total + poly_eval(x_g)
        result = total / order
        if isinstance(result, complex) and abs(result.imag) <= 1e-13:
            return float(result.real)
        return result

    return invariant_poly


def evaluate_sparse_polynomial(
    poly: dict[tuple[int, ...], float | complex],
    x: Sequence[float | complex],
) -> float | complex:
    r"""Evaluate an unboxed sparse multivariate polynomial $\sum_\alpha c_\alpha \mathbf{x}^\alpha$."""
    total: complex = 0.0 + 0.0j
    for exponents, coeff in poly.items():
        term: complex = complex(coeff)
        for xi, exp in zip(x, exponents):
            if exp:
                term *= xi**exp
        total += term
    if abs(total.imag) <= 1e-13:
        return float(total.real)
    return total


def _multiply_sparse_polys(
    p1: dict[tuple[int, ...], complex],
    p2: dict[tuple[int, ...], complex],
    tol: float = 1e-13,
) -> dict[tuple[int, ...], complex]:
    out: dict[tuple[int, ...], complex] = {}
    for e1, c1 in p1.items():
        for e2, c2 in p2.items():
            key = tuple(a + b for a, b in zip(e1, e2))
            out[key] = out.get(key, 0.0 + 0.0j) + c1 * c2
    return {k: v for k, v in out.items() if abs(v) > tol}


def _linear_form_power(
    row: dict[int, Any],
    dim: int,
    power: int,
    tol: float = 1e-13,
) -> dict[tuple[int, ...], complex]:
    """Expand (sum_j row[j] x_j)^power as an unboxed sparse multivariate polynomial."""
    zero_exp = (0,) * dim
    if power == 0:
        return {zero_exp: 1.0 + 0.0j}
    base: dict[tuple[int, ...], complex] = {}
    for col, coeff in row.items():
        if abs(complex(coeff)) > tol:
            exp = tuple(1 if i == col else 0 for i in range(dim))
            base[exp] = complex(coeff)
    if not base:
        return {}
    acc: dict[tuple[int, ...], complex] = {zero_exp: 1.0 + 0.0j}
    for _ in range(power):
        acc = _multiply_sparse_polys(acc, base, tol=tol)
    return acc


def reynolds_monomial_projection(
    exponents: tuple[int, ...],
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    tol: float = 1e-12,
) -> dict[tuple[int, ...], float | complex]:
    r"""Symbolically project a monomial $\mathbf{x}^\alpha$ onto the invariant ring $K[V]^G$:

    $$\mathcal{R}(\mathbf{x}^\alpha) = \frac{1}{|G|} \sum_{g \in G} (\rho(g^{-1})\mathbf{x})^\alpha$$

    Returns an unboxed sparse multivariate polynomial `{exponent_tuple: coeff}`.
    """
    dim = rep.dimension
    if len(exponents) != dim:
        raise ValueError(f'Expected exponent tuple of length {dim}, got {len(exponents)}.')
    if any(e < 0 for e in exponents):
        raise ValueError(f'Monomial exponents must be non-negative, got {exponents!r}.')

    inv_mats = _resolve_inverse_rep_matrices(rep, elements_or_group)
    order = len(inv_mats)
    zero_exp = (0,) * dim

    accum: dict[tuple[int, ...], complex] = {}
    for mat in inv_mats:
        term_poly: dict[tuple[int, ...], complex] = {zero_exp: 1.0 + 0.0j}
        for i, exp in enumerate(exponents):
            if exp == 0:
                continue
            factor = _linear_form_power(dict(mat.get(i, {})), dim, exp, tol=tol)
            if not factor:
                term_poly = {}
                break
            term_poly = _multiply_sparse_polys(term_poly, factor, tol=tol)
        for key, val in term_poly.items():
            accum[key] = accum.get(key, 0.0 + 0.0j) + val

    result: dict[tuple[int, ...], float | complex] = {}
    for key, val in accum.items():
        scaled = val / order
        if abs(scaled) > tol:
            result[key] = float(scaled.real) if abs(scaled.imag) <= tol else scaled
    return result


def _homogeneous_monomials(dim: int, degree: int) -> list[tuple[int, ...]]:
    """Generate all exponent tuples (e_0, ..., e_{dim-1}) summing to `degree`."""
    if degree == 0:
        return [(0,) * dim]
    monomials: list[tuple[int, ...]] = []
    for combo in itertools.combinations_with_replacement(range(dim), degree):
        counts = [0] * dim
        for idx in combo:
            counts[idx] += 1
        monomials.append(tuple(counts))
    return monomials


def _rref_row_basis(rows: list[list[complex]], tol: float = 1e-9) -> list[list[complex]]:
    """Compute a reduced row-echelon basis of the non-zero row space of `rows`."""
    if not rows:
        return []
    mat = [list(r) for r in rows]
    n_rows = len(mat)
    n_cols = len(mat[0])
    r_idx = 0

    for col in range(n_cols):
        if r_idx >= n_rows:
            break
        pivot_row = max(range(r_idx, n_rows), key=lambda i, c=col: abs(mat[i][c]))
        if abs(mat[pivot_row][col]) <= tol:
            continue
        mat[r_idx], mat[pivot_row] = mat[pivot_row], mat[r_idx]
        piv = mat[r_idx][col]
        mat[r_idx] = [v / piv for v in mat[r_idx]]
        for i in range(n_rows):
            if i != r_idx and abs(mat[i][col]) > tol:
                factor = mat[i][col]
                mat[i] = [mat[i][j] - factor * mat[r_idx][j] for j in range(n_cols)]
        r_idx += 1

    return mat[:r_idx]


def invariant_basis_at_degree(
    rep: GroupRepresentation[Any, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    degree: int,
    tol: float = 1e-9,
) -> list[dict[tuple[int, ...], float | complex]]:
    r"""Compute a linearly independent basis of homogeneous degree-`degree` invariants $K[V]_{\text{degree}}^G$.

    Projects every degree-$d$ monomial via `reynolds_monomial_projection` and extracts a canonical
    reduced row-echelon basis of unboxed sparse polynomials.
    """
    if degree < 0:
        raise ValueError(f'degree must be non-negative, got {degree}.')

    dim = rep.dimension
    monomials = _homogeneous_monomials(dim, degree)
    mon_index = {m: idx for idx, m in enumerate(monomials)}
    n_cols = len(monomials)

    dense_rows: list[list[complex]] = []
    for mon in monomials:
        proj = reynolds_monomial_projection(mon, rep, elements_or_group, tol=tol)
        if not proj:
            continue
        row = [0.0 + 0.0j] * n_cols
        for key, val in proj.items():
            row[mon_index[key]] = complex(val)
        dense_rows.append(row)

    basis_rows = _rref_row_basis(dense_rows, tol=tol)
    basis_polys: list[dict[tuple[int, ...], float | complex]] = []
    for row in basis_rows:
        poly: dict[tuple[int, ...], float | complex] = {}
        for mon, val in zip(monomials, row):
            if abs(val) > tol:
                poly[mon] = float(val.real) if abs(val.imag) <= tol else val
        if poly:
            basis_polys.append(poly)
    return basis_polys


__all__ = [
    'MolienSeries',
    'compute_molien_series',
    'evaluate_sparse_polynomial',
    'invariant_basis_at_degree',
    'reynolds_monomial_projection',
    'reynolds_polynomial_operator',
]
