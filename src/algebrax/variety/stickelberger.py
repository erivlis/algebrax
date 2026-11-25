r"""
Stickelberger companion matrix solvers and exact rational root isolation for 0-dimensional varieties.

For any zero-dimensional variety $V(I)$ with finite quotient basis
$\mathcal{B} = \{x^\alpha \notin \langle \mathrm{LT}(I) \rangle\}$, the multiplication operators
$M_{x_i}: k[V] \to k[V]$ form a commuting family of exact sparse matrices whose simultaneous
eigenvalues are the exact root coordinates of $V(I)$ (Stickelberger's Eigenvalue Theorem).

Provides:
- `companion_matrix`: Pure-Python exact sparse operator $M_{x_i}$ over any exact `Field[V]`.
- `solve_exact_rational`: Pure-Python exact rational root solver over $\mathbb{Q}$ via triangular
  `lex` elimination and the Rational Root Theorem (zero NumPy dependency).
- `solve_zero_dimensional`: Full complex/real root extractor using optional NumPy eigendecomposition
  of commuting companion matrices, with pure-Python fallback for rational/quadratic `lex` systems.
"""

from __future__ import annotations

import cmath
import math
from fractions import Fraction
from typing import Any, TypeVar

from algebrax.algebra import (
    GaloisField,
    ModularField,
    MultivariatePolynomialAlgebra,
    PAdicField,
    SparseMPoly,
    groebner_basis,
    monomial_add,
)
from algebrax.typing import SparseMatrix
from algebrax.variety.affine import AffineVariety

V = TypeVar('V')


def _require_numeric_char0_field(field: Any) -> None:
    """Reject finite/p-adic/non-numeric fields in complex Stickelberger eigensolvers."""
    if isinstance(field, (ModularField, GaloisField, PAdicField)):
        raise TypeError(
            f'solve_zero_dimensional requires a characteristic-0 numeric field, '
            f'got {type(field).__name__}. Use enum_variety_points() for finite fields.'
        )
    one = field.one
    if isinstance(one, bool) or not isinstance(one, (int, float, complex, Fraction)):
        raise TypeError(
            f'solve_zero_dimensional requires numeric scalars (Fraction, float, complex), '
            f'got {type(one).__name__}.'
        )


def companion_matrix(
    variety: AffineVariety[V],
    var_index: int,
) -> SparseMatrix[int, V]:
    r"""Construct the exact sparse multiplication matrix $M_{x_i}: k[V] \to k[V]$ in basis $\mathcal{B}$.

    Entry $(r, c)$ is the coefficient of basis monomial $b_r$ in $\overline{x_i \cdot b_c}^G$.
    For all $i, j$, the operators commute exactly: $[M_{x_i}, M_{x_j}] = \mathbf{0}$.

    Args:
        variety: A zero-dimensional `AffineVariety[V]`.
        var_index: Variable index $i \in \{0, \dots, n - 1\}$.

    Returns:
        Exact sparse matrix representation of $M_{x_i}$ over `variety.ring.field`.

    Raises:
        IndexError: If `var_index` is out of range.
        ValueError: If `variety` is positive-dimensional (not zero-dimensional).
    """
    n = variety.ambient_dimension
    if not (0 <= var_index < n):
        raise IndexError(f'var_index {var_index} out of range for ambient dimension {n}.')
    if variety.is_empty_over_closure():
        return {}
    basis = variety.quotient_basis()
    if basis is None:
        raise ValueError('companion_matrix requires a zero-dimensional variety.')

    idx_map = {m: idx for idx, m in enumerate(basis)}
    xi_mon = (0,) * var_index + (1,) + (0,) * (n - var_index - 1)
    one = variety.ring.field.one
    is_zero = variety.ring.field.is_zero

    mat: dict[int, dict[int, V]] = {}
    for col_j, mon in enumerate(basis):
        shifted = monomial_add(mon, xi_mon)
        direct_row = idx_map.get(shifted)
        if direct_row is not None:
            mat.setdefault(direct_row, {})[col_j] = one
            continue
        rem = variety.ideal.reduce({shifted: one})
        for rm, rc in rem.items():
            if not is_zero(rc):
                row_i = idx_map[rm]
                mat.setdefault(row_i, {})[col_j] = rc
    return mat


# =============================================================================
# Pure-Python Exact Rational & Quadratic Root Solvers (Zero-Dependency Fallback)
# =============================================================================


def _is_probable_prime(n: int) -> bool:
    """Deterministic Miller-Rabin primality test for 64-bit integers (and strong check beyond)."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n == p:
            return True
        if n % p == 0:
            return False
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _pollard_rho(n: int) -> int:
    """Return a non-trivial factor of composite odd integer n using Pollard's rho."""
    if n % 2 == 0:
        return 2
    for c in range(1, 64):
        x = 2
        y = 2
        d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if 1 < d < n:
            return d
    # Fallback trial division if rho stalls
    limit = math.isqrt(n)
    for d in range(3, limit + 1, 2):
        if n % d == 0:
            return d
    return n


def _prime_factorization(n: int) -> dict[int, int]:
    """Return prime factorization {p: exponent} of positive integer n."""
    factors: dict[int, int] = {}
    if n <= 1:
        return factors
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    stack = [n] if n > 1 else []
    while stack:
        cur = stack.pop()
        if cur == 1:
            continue
        if _is_probable_prime(cur):
            factors[cur] = factors.get(cur, 0) + 1
            continue
        d = _pollard_rho(cur)
        stack.append(d)
        stack.append(cur // d)
    return factors


def _int_divisors(n: int) -> list[int]:
    """Return all positive divisors of a positive integer n via prime factorization."""
    n = abs(n)
    if n == 0:
        return [1]
    divisors = [1]
    for p, exp in _prime_factorization(n).items():
        next_divs: list[int] = []
        p_pow = 1
        for _ in range(exp + 1):
            for d in divisors:
                next_divs.append(d * p_pow)
            p_pow *= p
        divisors = next_divs
    divisors.sort()
    return divisors


def _univariate_rational_roots(poly: dict[int, Fraction]) -> list[Fraction]:
    """Find all exact rational roots of a non-zero univariate polynomial in Q[t]."""
    cleaned = {d: c for d, c in poly.items() if c != 0}
    if not cleaned:
        return []
    max_deg = max(cleaned.keys())
    if max_deg == 0:
        return []

    roots: list[Fraction] = []
    min_deg = min(cleaned.keys())
    if min_deg > 0:
        roots.append(Fraction(0))
        cleaned = {d - min_deg: c for d, c in cleaned.items()}
        max_deg -= min_deg
        if max_deg == 0:
            return roots

    # Clear denominators to obtain an integer polynomial a_d t^d + ... + a_0
    lcm_den = 1
    for c in cleaned.values():
        lcm_den = math.lcm(lcm_den, c.denominator)
    int_coeffs = [0] * (max_deg + 1)
    for d, c in cleaned.items():
        int_coeffs[d] = int(c * lcm_den)

    # Reduce by overall GCD
    g = 0
    for ic in int_coeffs:
        g = math.gcd(g, abs(ic))
    if g > 1:
        int_coeffs = [ic // g for ic in int_coeffs]

    a0 = abs(int_coeffs[0])
    ad = abs(int_coeffs[max_deg])
    candidates: set[Fraction] = set()
    for p in _int_divisors(a0):
        for q in _int_divisors(ad):
            if math.gcd(p, q) == 1:
                candidates.add(Fraction(p, q))
                candidates.add(Fraction(-p, q))

    for cand in sorted(candidates):
        # Horner evaluation in exact Fraction arithmetic
        val = Fraction(0)
        for coeff in reversed(int_coeffs):
            val = val * cand + coeff
        if val == 0:
            roots.append(cand)

    roots.sort()
    return roots


def _univariate_gcd_fraction(
    a: dict[int, Fraction],
    b: dict[int, Fraction],
) -> dict[int, Fraction]:
    """Compute monic Euclidean GCD of two univariate polynomials over Q."""
    r0 = {d: c for d, c in a.items() if c != 0}
    r1 = {d: c for d, c in b.items() if c != 0}
    while r1:
        deg_b = max(r1.keys())
        lc_b = r1[deg_b]
        rem = dict(r0)
        while rem:
            deg_r = max(rem.keys())
            if deg_r < deg_b:
                break
            shift = deg_r - deg_b
            factor = rem[deg_r] / lc_b
            for d, c in r1.items():
                t = d + shift
                nv = rem.get(t, Fraction(0)) - factor * c
                if nv == 0:
                    rem.pop(t, None)
                else:
                    rem[t] = nv
        r0, r1 = r1, rem
    if not r0:
        return {}
    lc = r0[max(r0.keys())]
    return {d: c / lc for d, c in r0.items()}


def _eval_partial_to_univariate(
    poly: SparseMPoly[Fraction],
    var_idx: int,
    assigned_suffix: tuple[Fraction, ...],
) -> dict[int, Fraction]:
    """Evaluate variables > var_idx using `assigned_suffix`, returning univariate dict in x_{var_idx}."""
    uni: dict[int, Fraction] = {}
    for mon, coeff in poly.items():
        if coeff == 0:
            continue
        term = coeff
        for offset, val in enumerate(assigned_suffix):
            exp = mon[var_idx + 1 + offset]
            if exp:
                term *= val**exp
        if term != 0:
            deg = mon[var_idx]
            nv = uni.get(deg, Fraction(0)) + term
            if nv == 0:
                uni.pop(deg, None)
            else:
                uni[deg] = nv
    return uni


def _solve_exact_rational_from_radical(
    rad: AffineVariety[Fraction],
    original: AffineVariety[Fraction],
) -> list[tuple[Fraction, ...]]:
    """Internal helper assuming `rad` is already the radical zero-dimensional variety."""
    n = rad.ambient_dimension
    if rad.ring.order == 'lex':
        lex_gb = rad.ideal.basis
    else:
        lex_ring = MultivariatePolynomialAlgebra(rad.ring.field, n, order='lex')
        lex_gb = groebner_basis(lex_ring, rad.ideal.basis)

    # Group basis polynomials by their smallest (leading) active variable index
    polys_by_min_var: list[list[SparseMPoly[Fraction]]] = [[] for _ in range(n)]
    for g in lex_gb:
        active = [i for i in range(n) if any(m[i] > 0 for m in g)]
        if active:
            polys_by_min_var[min(active)].append(g)

    solutions: list[tuple[Fraction, ...]] = []

    def _backtrack(var_idx: int, suffix: tuple[Fraction, ...]) -> None:
        if var_idx < 0:
            if original.contains_point(suffix):
                solutions.append(suffix)
            return

        # Combine all equations depending only on x_{var_idx}, ..., x_{n-1} via exact GCD
        g_uni: dict[int, Fraction] | None = None
        for poly in polys_by_min_var[var_idx]:
            ev = _eval_partial_to_univariate(poly, var_idx, suffix)
            if not ev:
                continue
            if max(ev.keys()) == 0:
                return  # Contradiction (non-zero constant = 0)
            g_uni = ev if g_uni is None else _univariate_gcd_fraction(g_uni, ev)
            if not g_uni or max(g_uni.keys()) == 0:
                return

        if g_uni is None:
            return

        for root in _univariate_rational_roots(g_uni):
            _backtrack(var_idx - 1, (root, *suffix))

    _backtrack(n - 1, ())
    solutions.sort()
    return solutions


def solve_exact_rational(variety: AffineVariety[Fraction]) -> list[tuple[Fraction, ...]]:
    r"""Find all exact $\mathbb{Q}$-rational points of a 0-dimensional variety in pure Python.

    Uses triangular `lex` Gröbner basis elimination (on the radical variety $V(\sqrt{I})$)
    combined with exact univariate GCDs and the Rational Root Theorem. Requires zero external
    dependencies.

    Args:
        variety: A zero-dimensional `AffineVariety[Fraction]` over $\mathbb{Q}$.

    Returns:
        Sorted list of exact rational root tuples `(Fraction, ...)`.

    Raises:
        TypeError: If the variety's coefficient field does not use `Fraction` elements.
        ValueError: If `variety` is positive-dimensional.

    Example:
        >>> from fractions import Fraction
        >>> from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
        >>> from algebrax.variety import AffineVariety, solve_exact_rational
        >>> R = MultivariatePolynomialAlgebra(StandardField(Fraction), n_vars=2)
        >>> x, y = R.gen(0), R.gen(1)
        >>> V = AffineVariety(R, [R.sub(R.mul(x, x), R.one), R.sub(y, R.smul(Fraction(2), x))])
        >>> solve_exact_rational(V)
        [(Fraction(-1, 1), Fraction(-2, 1)), (Fraction(1, 1), Fraction(2, 1))]
    """
    if not isinstance(variety.ring.field.one, Fraction):
        raise TypeError('solve_exact_rational requires a rational Field with Fraction coefficients.')
    if variety.is_empty_over_closure():
        return []
    if not variety.is_zero_dimensional():
        raise ValueError('solve_exact_rational requires a zero-dimensional variety.')

    rad = variety.radical_zero_dim()
    return _solve_exact_rational_from_radical(rad, variety)


def _clean_scalar(val: complex, imag_tol: float = 1e-9) -> float | complex:
    """Convert near-real complex eigenvalues to clean Python floats."""
    if abs(val.imag) <= imag_tol:
        real_val = float(val.real)
        return 0.0 if abs(real_val) <= 1e-13 else real_val
    real_part = 0.0 if abs(val.real) <= 1e-13 else float(val.real)
    return complex(real_part, float(val.imag))


def _sort_key_point(pt: tuple[float | complex, ...]) -> tuple[tuple[float, float], ...]:
    return tuple((round(complex(c).real, 7), round(complex(c).imag, 7)) for c in pt)


def _deflate_complex_poly(uni: dict[int, complex], root: complex) -> dict[int, complex]:
    """Synthetic division of univariate polynomial `uni` by (t - root)."""
    deg = max(uni.keys())
    coeffs = [uni.get(d, 0j) for d in range(deg + 1)]
    quot = [0j] * deg
    acc = 0j
    for d in range(deg, 0, -1):
        acc = coeffs[d] + acc * root
        quot[d - 1] = acc
    max_abs = max((abs(c) for c in quot), default=0.0)
    if max_abs == 0.0:
        return {}
    return {d: c for d, c in enumerate(quot) if abs(c) > 1e-12 * max_abs}


def _eval_poly_complex(
    poly: SparseMPoly[Any],
    var_idx: int,
    suffix: tuple[complex, ...],
) -> dict[int, complex]:
    """Evaluate trailing variables of a polynomial to a complex univariate dict."""
    uni: dict[int, complex] = {}
    term_scale = 0.0
    for mon, coeff in poly.items():
        term = complex(coeff)
        for offset, val in enumerate(suffix):
            exp = mon[var_idx + 1 + offset]
            if exp:
                term *= val**exp
        t_abs = abs(term)
        if t_abs > term_scale:
            term_scale = t_abs
        deg = mon[var_idx]
        uni[deg] = uni.get(deg, 0j) + term
    if term_scale == 0.0:
        return {}
    max_abs = max((abs(c) for c in uni.values()), default=0.0)
    if max_abs <= 1e-11 * term_scale:
        return {}
    return {d: c for d, c in uni.items() if abs(c) > 1e-12 * max_abs}


def _deflate_rational_roots(
    cur: dict[int, complex],
    extracted: list[complex],
) -> dict[int, complex]:
    """Factor out exact rational roots from a real univariate polynomial of degree >= 3."""
    max_r = max(abs(c.real) for c in cur.values())
    frac_poly = {
        d: Fraction(c.real / max_r).limit_denominator(10**6)
        for d, c in cur.items()
    }
    for r_frac in _univariate_rational_roots(frac_poly):
        r_c = complex(float(r_frac))
        val = sum(c * (r_c**d) for d, c in cur.items())
        scale = max((abs(c * (r_c**d)) for d, c in cur.items()), default=1.0)
        while cur and max(cur.keys()) >= 1 and abs(val) <= 1e-9 * max(1.0, scale):
            if not any(abs(r_c - prev) <= 1e-9 for prev in extracted):
                extracted.append(r_c)
            cur = _deflate_complex_poly(cur, r_c)
            if not cur or max(cur.keys()) == 0:
                break
            val = sum(c * (r_c**d) for d, c in cur.items())
            scale = max((abs(c * (r_c**d)) for d, c in cur.items()), default=1.0)
    return cur


def _solve_uni_complex_deg_le2(uni: dict[int, complex]) -> list[complex]:
    """Solve a univariate complex polynomial via rational deflation and quadratic formula."""
    extracted: list[complex] = []
    cur = dict(uni)

    if max(cur.keys()) >= 3 and all(
        abs(c.imag) <= 1e-12 * max(1.0, abs(c.real)) for c in cur.values()
    ):
        cur = _deflate_rational_roots(cur, extracted)

    if not cur or max(cur.keys()) == 0:
        return extracted

    deg = max(cur.keys())
    if deg == 1:
        r1 = -cur.get(0, 0j) / cur[1]
        if not any(abs(r1 - prev) <= 1e-9 for prev in extracted):
            extracted.append(r1)
        return extracted
    if deg == 2:
        a, b, c = cur[2], cur.get(1, 0j), cur.get(0, 0j)
        disc_sq = b * b - 4 * a * c
        scale = max(abs(b * b), abs(4 * a * c), 1e-30)
        if abs(disc_sq) <= 1e-12 * scale:
            r_dup = -b / (2 * a)
            if not any(abs(r_dup - prev) <= 1e-9 for prev in extracted):
                extracted.append(r_dup)
            return extracted
        disc = cmath.sqrt(disc_sq)
        for root in ((-b - disc) / (2 * a), (-b + disc) / (2 * a)):
            if not any(abs(root - prev) <= 1e-9 for prev in extracted):
                extracted.append(root)
        return extracted
    raise ImportError(
        'Extracting non-rational roots of degree >= 3 requires NumPy. '
        'Install numpy or call solve_exact_rational() for pure-Python rational roots.'
    )


def _solve_lex_pure_python_numeric(
    variety: AffineVariety[Any],
) -> list[tuple[float | complex, ...]]:
    """Pure-Python fallback solver for 0-dimensional varieties (exact rational + degree <= 2 factors)."""
    n = variety.ambient_dimension
    if variety.ring.order == 'lex':
        lex_gb = variety.ideal.basis
    else:
        lex_ring = MultivariatePolynomialAlgebra(variety.ring.field, n, order='lex')
        lex_gb = groebner_basis(lex_ring, variety.ideal.basis)

    polys_by_min_var: list[list[SparseMPoly[Any]]] = [[] for _ in range(n)]
    for g in lex_gb:
        active = [i for i in range(n) if any(m[i] > 0 for m in g)]
        if active:
            polys_by_min_var[min(active)].append(g)

    solutions: list[tuple[float | complex, ...]] = []

    def _backtrack(var_idx: int, suffix: tuple[complex, ...]) -> None:
        if var_idx < 0:
            solutions.append(tuple(_clean_scalar(c) for c in suffix))
            return
        candidates = []
        for poly in polys_by_min_var[var_idx]:
            ev = _eval_poly_complex(poly, var_idx, suffix)
            if not ev:
                continue
            if max(ev.keys()) == 0:
                return
            candidates.append(ev)
        if not candidates:
            return
        chosen = min(candidates, key=lambda d: max(d.keys()))
        for root in _solve_uni_complex_deg_le2(chosen):
            if all(
                abs(sum(c * (root**d) for d, c in eq.items()))
                <= 1e-6 * max(1.0, max((abs(c * (root**d)) for d, c in eq.items()), default=0.0))
                for eq in candidates
            ):
                _backtrack(var_idx - 1, (root, *suffix))

    _backtrack(n - 1, ())
    solutions.sort(key=_sort_key_point)
    return solutions


def _to_dense_numpy(
    sparse_mat: SparseMatrix[int, Any],
    dim: int,
    np_mod: Any,
) -> Any:
    """Convert an exact sparse companion matrix to a dense NumPy array."""
    is_complex = any(isinstance(v, complex) for row in sparse_mat.values() for v in row.values())
    dtype = complex if is_complex else float
    arr = np_mod.zeros((dim, dim), dtype=dtype)
    for r, cols in sparse_mat.items():
        for c, val in cols.items():
            arr[r, c] = complex(val) if is_complex else float(val)
    return arr


def solve_zero_dimensional(
    variety: AffineVariety[V],
    *,
    use_radical: bool = True,
) -> list[tuple[float | complex, ...]]:
    r"""Extract isolated root coordinates of a 0-dimensional variety via Stickelberger's Theorem.

    When `use_radical=True` (default), first reduces to $\sqrt{I}$ via Seidenberg's Lemma so
    repeated roots do not produce defective Jordan blocks, then extracts simultaneous Rayleigh
    quotients of the commuting companion matrices $M_{x_1}, \dots, M_{x_n}$.

    Uses NumPy (`np.linalg.eig`) when available, with a pure-Python fallback for rational
    or degree $\le 2$ triangular `lex` systems when NumPy is not installed.

    Args:
        variety: A zero-dimensional `AffineVariety[V]` over a characteristic-0 numeric field.
        use_radical: If True (default), radicalize via Seidenberg's Lemma before eigendecomposition.

    Returns:
        Deterministically sorted list of complex/real root coordinate tuples.

    Raises:
        TypeError: If the variety's coefficient field is a finite or non-numeric field.
        ValueError: If `variety` is positive-dimensional.
    """
    _require_numeric_char0_field(variety.ring.field)
    if variety.is_empty_over_closure():
        return []
    if not variety.is_zero_dimensional():
        raise ValueError('solve_zero_dimensional requires a zero-dimensional variety.')

    target = variety.radical_zero_dim() if use_radical else variety
    basis = target.quotient_basis()
    if not basis:
        return []

    dim = len(basis)
    n = target.ambient_dimension

    try:
        import numpy as np  # type: ignore[import-not-found]
    except ImportError:
        if isinstance(target.ring.field.one, Fraction):
            rat_roots = _solve_exact_rational_from_radical(
                target if use_radical else target.radical_zero_dim(),
                variety,
            )
            if len(rat_roots) == dim:
                return [tuple(float(c) for c in pt) for pt in rat_roots]
        return _solve_lex_pure_python_numeric(target)

    sparse_mats = [companion_matrix(target, i) for i in range(n)]
    dense_mats = [_to_dense_numpy(m, dim, np) for m in sparse_mats]

    # Deterministic incommensurable linear combinations until eigenvalues separate cleanly
    weight_seeds = [
        [math.sqrt(2.0 + 3.0 * i) for i in range(n)],
        [math.pi ** (i + 1) % 7.0 + 0.13 * (i + 1) for i in range(n)],
        [math.e ** (i + 1) % 5.0 + 0.37 * (i + 1) for i in range(n)],
        [float((i + 1) ** 3 + 17) / float(29 + 7 * i) for i in range(n)],
        *[
            [math.sin(1.37 * (seed + 1) * (i + 1) + 0.41 * seed) + 1.5 + 0.19 * i for i in range(n)]
            for seed in range(8)
        ],
    ]

    best_vecs = None
    best_min_gap = -1.0
    for weights in weight_seeds:
        comb = sum(w * mat for w, mat in zip(weights, dense_mats, strict=True))
        eigvals, eigvecs = np.linalg.eig(comb)
        if dim == 1:
            best_vecs = eigvecs
            break
        min_gap = min(
            abs(eigvals[a] - eigvals[b]) for a in range(dim) for b in range(a + 1, dim)
        )
        if min_gap > best_min_gap:
            best_min_gap = min_gap
            best_vecs = eigvecs
        if min_gap > 1e-6:
            break

    if best_vecs is None:
        raise RuntimeError('Failed to compute companion matrix eigenvectors.')

    points: list[tuple[float | complex, ...]] = []
    for k in range(dim):
        v = best_vecs[:, k]
        denom = np.vdot(v, v)
        coords = tuple(
            _clean_scalar(complex(np.vdot(v, mat @ v) / denom))
            for mat in dense_mats
        )
        points.append(coords)

    points.sort(key=_sort_key_point)
    return points


__all__ = [
    'companion_matrix',
    'solve_exact_rational',
    'solve_zero_dimensional',
]
