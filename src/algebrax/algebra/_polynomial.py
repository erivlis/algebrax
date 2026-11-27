r"""
Univariate and multivariate polynomial algebras $R[x]$ and $k[x_1, \dots, x_n]$.

Provides unboxed sparse polynomial rings built on `MonoidAlgebra`:
- `PolynomialAlgebra`: Univariate ring $R[x]$ over the additive monoid $(\mathbb{N}_0, +)$.
- `MultivariatePolynomialAlgebra`: Multivariate ring $k[x_1, \dots, x_n]$ over $(\mathbb{N}_0^n, +)$
  with admissible monomial orderings (`lex`, `grlex`, `grevlex`), formal derivations,
  univariate Euclidean GCD / square-free extraction, symplectic Poisson brackets,
  S-polynomials, and multivariate remainder reduction.
"""

from __future__ import annotations

import operator
from collections.abc import Callable, Sequence
from typing import Any, Generic, Literal, TypeVar

from algebrax.algebra._field import Field, ModularField
from algebrax.algebra._mixins import HasDerivation
from algebrax.algebra._monoid_algebra import MonoidAlgebra
from algebrax.algebra._ring import CommRing
from algebrax.algebra._semiring import Semiring

T = TypeVar('T')
V = TypeVar('V')

Monomial = tuple[int, ...]
SparseMPoly = dict[Monomial, V]
MonomialOrder = Literal['lex', 'grlex', 'grevlex']


# =============================================================================
# Monomial Operations & Admissible Orderings
# =============================================================================


def monomial_add(a: Monomial, b: Monomial) -> Monomial:
    r"""Multiply monomials $x^\alpha \cdot x^\beta = x^{\alpha + \beta}$."""
    return tuple(x + y for x, y in zip(a, b, strict=True))


def monomial_sub(a: Monomial, b: Monomial) -> Monomial:
    r"""Divide monomials $x^\alpha / x^\beta = x^{\alpha - \beta}$ (requires $x^\beta \mid x^\alpha$)."""
    return tuple(x - y for x, y in zip(a, b, strict=True))


def monomial_divides(a: Monomial, b: Monomial) -> bool:
    r"""Return True iff $x^\alpha$ divides $x^\beta$ ($\alpha_i \le \beta_i$ for all $i$)."""
    return all(x <= y for x, y in zip(a, b, strict=True))


def monomial_lcm(a: Monomial, b: Monomial) -> Monomial:
    r"""Least common multiple $\operatorname{lcm}(x^\alpha, x^\beta) = x^{\max(\alpha, \beta)}$."""
    return tuple(max(x, y) for x, y in zip(a, b, strict=True))


def order_key_lex(m: Monomial) -> tuple[int, ...]:
    """Lexicographic monomial order key (variable elimination order)."""
    return m


def order_key_grlex(m: Monomial) -> tuple[int, tuple[int, ...]]:
    """Graded lexicographic monomial order key (total degree, then lex)."""
    return (sum(m), m)


def order_key_grevlex(m: Monomial) -> tuple[int, tuple[int, ...]]:
    """Graded reverse lexicographic monomial order key (total degree, then reverse negated)."""
    return (sum(m), tuple(-x for x in reversed(m)))


_ORDER_KEYS: dict[MonomialOrder, Callable[[Monomial], Any]] = {
    'lex': order_key_lex,
    'grlex': order_key_grlex,
    'grevlex': order_key_grevlex,
}


# =============================================================================
# Internal Field Arithmetic & Univariate Helpers
# =============================================================================


def _field_scale_int(field: Field[V], elem: V, n: int) -> V:
    """Compute integer multiple n * elem in a Field via O(log n) binary doubling."""
    if n <= 0 or field.is_zero(elem):
        return field.zero
    res = field.zero
    base = elem
    k = n
    while k > 0:
        if k & 1:
            res = field.add(res, base)
        k >>= 1
        if k:
            base = field.add(base, base)
    return res


def _field_pow(field: Field[V], base: V, exp: int) -> V:
    """Compute base ** exp in a Field via O(log exp) binary exponentiation."""
    if exp == 0:
        return field.one
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


def _extract_univariate(
    poly: SparseMPoly[V],
    var_index: int,
    field: Field[V],
) -> dict[int, V]:
    """Extract a univariate degree-to-coefficient map from a multivariate polynomial."""
    uni: dict[int, V] = {}
    for mon, coeff in poly.items():
        if field.is_zero(coeff):
            continue
        for idx, exp in enumerate(mon):
            if idx != var_index and exp != 0:
                raise ValueError(f'Polynomial is not univariate in variable index {var_index}: found {mon}.')
        deg = mon[var_index]
        uni[deg] = field.add(uni.get(deg, field.zero), coeff)
        if field.is_zero(uni[deg]):
            del uni[deg]
    return uni


def _lift_univariate(uni: dict[int, V], n_vars: int, var_index: int, field: Field[V]) -> SparseMPoly[V]:
    """Lift a univariate degree map back to an n-variate SparseMPoly."""
    res: SparseMPoly[V] = {}
    prefix = (0,) * var_index
    suffix = (0,) * (n_vars - var_index - 1)
    for deg, coeff in uni.items():
        if not field.is_zero(coeff):
            res[(*prefix, deg, *suffix)] = coeff
    return res


def _uni_make_monic(poly: dict[int, V], field: Field[V]) -> dict[int, V]:
    """Scale a non-zero univariate polynomial dict so its leading coefficient is 1."""
    if not poly:
        return {}
    deg = max(poly.keys())
    inv_lc = field.inv(poly[deg])
    return {d: prod for d, c in poly.items() if not field.is_zero(prod := field.mul(inv_lc, c))}


def _uni_divmod(
    dividend: dict[int, V],
    divisor: dict[int, V],
    field: Field[V],
) -> tuple[dict[int, V], dict[int, V]]:
    """Exact Euclidean division of univariate polynomials over a Field."""
    if not divisor:
        raise ZeroDivisionError('Cannot divide by the zero polynomial.')
    rem = dict(dividend)
    quot: dict[int, V] = {}
    deg_b = max(divisor.keys())
    lc_b = divisor[deg_b]
    while rem:
        deg_r = max(rem.keys())
        if deg_r < deg_b:
            break
        shift = deg_r - deg_b
        factor = field.div(rem[deg_r], lc_b)
        quot[shift] = field.add(quot.get(shift, field.zero), factor)
        if field.is_zero(quot[shift]):
            del quot[shift]
        for d, c in divisor.items():
            target = d + shift
            updated = field.sub(rem.get(target, field.zero), field.mul(factor, c))
            if field.is_zero(updated):
                rem.pop(target, None)
            else:
                rem[target] = updated
    return quot, rem


def _uni_mul(a: dict[int, V], b: dict[int, V], field: Field[V]) -> dict[int, V]:
    """Multiply two univariate polynomial dicts over a Field."""
    if not a or not b:
        return {}
    res: dict[int, V] = {}
    for d1, c1 in a.items():
        for d2, c2 in b.items():
            deg = d1 + d2
            val = field.add(res.get(deg, field.zero), field.mul(c1, c2))
            if field.is_zero(val):
                res.pop(deg, None)
            else:
                res[deg] = val
    return res


def _uni_gcd(a: dict[int, V], b: dict[int, V], field: Field[V]) -> dict[int, V]:
    """Compute monic Euclidean GCD of two univariate polynomials over a Field."""
    r0 = dict(a)
    r1 = dict(b)
    while r1:
        _, r2 = _uni_divmod(r0, r1, field)
        r0, r1 = r1, r2
    return _uni_make_monic(r0, field)


def _uni_pth_root(poly: dict[int, V], field: Field[V]) -> dict[int, V] | None:
    """Compute exact p-th root of a pure p-th power polynomial over F_p or GF(p^m), or None."""
    if isinstance(field, ModularField):
        p = field.p
        if not all(deg % p == 0 for deg in poly):
            return None
        return {deg // p: coeff for deg, coeff in poly.items()}
    p_attr = getattr(field, 'p', None)
    irreduc = getattr(field, 'irreduc_poly', None)
    if isinstance(p_attr, int) and p_attr >= 2 and isinstance(irreduc, tuple) and len(irreduc) >= 2:
        p = p_attr
        if not all(deg % p == 0 for deg in poly):
            return None
        ext_deg = len(irreduc) - 1
        frob_inv_exp = p ** (ext_deg - 1)
        return {deg // p: _field_pow(field, coeff, frob_inv_exp) for deg, coeff in poly.items()}
    return None


# =============================================================================
# Univariate Polynomial Algebra R[x]
# =============================================================================


class PolynomialAlgebra(MonoidAlgebra[int, T]):
    r"""The Univariate Polynomial Algebra $R[x]$ over coefficient semiring/ring $R$.

    Algebraic Signature:
        $\langle R, R[x], \cdot_s, \emptyset, +, -, \{0: 1_R\}, \cdot \rangle$

    Carrier:
        `dict[int, T]` (Sparse mapping from degree $k \in \mathbb{N}_0$ to coefficient $c_k \in R$).

    Operations:
        - Addition ($+$): Elementwise polynomial addition (inherited from `MonoidAlgebraSemiring`).
        - Multiplication ($\cdot$): Cauchy polynomial product $(a \cdot b)_k = \sum_{j=0}^k a_j b_{k-j}$.
        - Negation ($-a$): Degree-wise coefficient negation (inherited from `MonoidAlgebra`).
        - Subtraction ($a - b$): Direct polynomial difference (inherited from `MonoidAlgebra`).
        - Scalar Multiplication ($r \cdot_s m$): Scaling by scalar $r \in R$ (inherited from `MonoidAlgebraSemiring`).
        - Zero Element ($\mathbb{0}$): `{}` (empty mapping).
        - One Element ($\mathbb{1}$): `{0: 1_R}` ($x^0 = 1$).

    Properties:
        Associative, distributive; commutative if $R$ is commutative.
        Fulfills `Algebra`, `Ring`, `Module`, and `Semiring`.

    Applications:
        Generating functions, algebraic combinatorics, spectral graph polynomials.
    """

    def __init__(self, coeff_semiring: Semiring[T]):
        super().__init__(coeff_semiring, key_op=operator.add, zero_key=0)


# =============================================================================
# Multivariate Polynomial Algebra k[x_1, ..., x_n]
# =============================================================================


class MultivariatePolynomialAlgebra(
    MonoidAlgebra[Monomial, V],
    CommRing[SparseMPoly[V]],
    HasDerivation[SparseMPoly[V]],
    Generic[V],
):
    r"""The Multivariate Polynomial Algebra $k[x_1, \dots, x_n]$ over an exact `Field[V]`.

    Algebraic Signature:
        $\langle k, k[x_1, \dots, x_n], \cdot_s, \emptyset, +, -, \{\mathbf{0}: 1_k\}, \cdot, \partial_i \rangle$

    Carrier:
        `dict[tuple[int, ...], V]` (Unboxed sparse mapping from exponent vector $\alpha \in \mathbb{N}_0^n$
        to non-zero coefficient $c_\alpha \in k$).

    Operations:
        - Ring & Algebra Operations: `add`, `sub`, `neg`, `mul`, `smul`, `mul_term`, `zero`, `one`.
        - Monomial Orderings (`lex`, `grlex`, `grevlex`): `lm`, `lc`, `lt`, `make_monic`.
        - Formal Calculus & Univariate Factorization: `eval`, `diff`, `univariate_gcd`, `square_free_part`.
        - Symplectic Phase-Space Structure: `poisson_bracket` / `bracket` for even `n_vars = 2m`.
        - Ideal Reduction Primitives: `s_poly`, `reduce_poly`.

    Properties:
        Satisfies `CommRing`, `Algebra`, `HasDerivation`, and (when `n_vars` is even) `PoissonAlgebra`.

    Example:
        >>> from fractions import Fraction
        >>> from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
        >>> Q = StandardField(Fraction)
        >>> R = MultivariatePolynomialAlgebra(Q, n_vars=2, order='grevlex')
        >>> x, y = R.gen(0), R.gen(1)
        >>> f = R.sub(R.mul(x, x), y)
        >>> R.lm(f)
        (2, 0)
        >>> R.eval(f, (Fraction(3), Fraction(4)))
        Fraction(5, 1)
    """

    def __init__(
        self,
        field: Field[V],
        n_vars: int,
        order: MonomialOrder = 'grevlex',
    ) -> None:
        if not isinstance(field, Field):
            raise TypeError(f'MultivariatePolynomialAlgebra requires a Field, got {type(field).__name__}.')
        if n_vars < 1:
            raise ValueError(f'n_vars must be at least 1, got {n_vars}.')
        if order not in _ORDER_KEYS:
            raise ValueError(f'Unknown monomial order {order!r}. Expected one of {tuple(_ORDER_KEYS)}.')
        self.field: Field[V] = field
        self.n_vars: int = n_vars
        self.order: MonomialOrder = order
        self.key_fn: Callable[[Monomial], Any] = _ORDER_KEYS[order]
        if n_vars % 2 == 0:
            self.is_lie: Literal[True] = True
        super().__init__(field, key_op=monomial_add, zero_key=(0,) * n_vars)  # type: ignore[arg-type]

    def clean(self, poly: SparseMPoly[V]) -> SparseMPoly[V]:
        """Strip zero-valued coefficients according to `self.field.is_zero`."""
        is_zero = self.field.is_zero
        return {m: c for m, c in poly.items() if not is_zero(c)}

    def const(self, value: V) -> SparseMPoly[V]:
        """Construct the constant polynomial `value * 1`."""
        if self.field.is_zero(value):
            return {}
        return {self.zero_key: value}

    def gen(self, index: int) -> SparseMPoly[V]:
        """Return the `index`-th coordinate generator polynomial $x_{\text{index}}$."""
        if not (0 <= index < self.n_vars):
            raise IndexError(f'Variable index {index} out of range for n_vars={self.n_vars}.')
        exp = (0,) * index + (1,) + (0,) * (self.n_vars - index - 1)
        return {exp: self.field.one}

    def add(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
        """Add two multivariate polynomials using exact field zero checks."""
        res = dict(a)
        f_add = self.field.add
        is_zero = self.field.is_zero
        zero = self.field.zero
        for m, c in b.items():
            nc = f_add(res.get(m, zero), c)
            if is_zero(nc):
                res.pop(m, None)
            else:
                res[m] = nc
        return res

    def neg(self, a: SparseMPoly[V]) -> SparseMPoly[V]:
        """Negate a multivariate polynomial coefficient-wise in `self.field`."""
        f_neg = self.field.neg
        is_zero = self.field.is_zero
        return {m: neg_c for m, c in a.items() if not is_zero(neg_c := f_neg(c))}

    def sub(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
        """Subtract two multivariate polynomials: $a - b$."""
        res = dict(a)
        f_sub = self.field.sub
        is_zero = self.field.is_zero
        zero = self.field.zero
        for m, c in b.items():
            nc = f_sub(res.get(m, zero), c)
            if is_zero(nc):
                res.pop(m, None)
            else:
                res[m] = nc
        return res

    def mul(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
        """Multiply two multivariate polynomials via sparse Cauchy convolution."""
        if not a or not b:
            return {}
        res: SparseMPoly[V] = {}
        f_mul = self.field.mul
        f_add = self.field.add
        is_zero = self.field.is_zero
        zero = self.field.zero
        for m1, c1 in a.items():
            for m2, c2 in b.items():
                nm = monomial_add(m1, m2)
                nc = f_add(res.get(nm, zero), f_mul(c1, c2))
                if is_zero(nc):
                    res.pop(nm, None)
                else:
                    res[nm] = nc
        return res

    def smul(self, r: V, m: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Scale a polynomial by scalar $r \in k$."""
        if self.field.is_zero(r) or not m:
            return {}
        f_mul = self.field.mul
        is_zero = self.field.is_zero
        return {k: prod for k, c in m.items() if not is_zero(prod := f_mul(r, c))}

    def mul_term(self, poly: SparseMPoly[V], mon: Monomial, coeff: V) -> SparseMPoly[V]:
        r"""Multiply a polynomial by a single term $c \cdot x^\alpha$."""
        if self.field.is_zero(coeff) or not poly:
            return {}
        f_mul = self.field.mul
        is_zero = self.field.is_zero
        return {
            monomial_add(m, mon): prod
            for m, c in poly.items()
            if not is_zero(prod := f_mul(coeff, c))
        }

    def lm(self, poly: SparseMPoly[V]) -> Monomial:
        r"""Return the leading monomial $\operatorname{LM}(f)$ under `self.order`."""
        if not poly:
            raise ValueError('The zero polynomial has no leading monomial.')
        return max(poly.keys(), key=self.key_fn)

    def lc(self, poly: SparseMPoly[V]) -> V:
        r"""Return the leading coefficient $\operatorname{LC}(f)$ in `self.field`."""
        return poly[self.lm(poly)]

    def lt(self, poly: SparseMPoly[V]) -> tuple[Monomial, V]:
        r"""Return the leading term pair $(\operatorname{LM}(f), \operatorname{LC}(f))$."""
        m = self.lm(poly)
        return (m, poly[m])

    def make_monic(self, poly: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Scale a non-zero polynomial by $\operatorname{LC}(f)^{-1}$ so $\operatorname{LC} = 1$."""
        cleaned = self.clean(poly)
        if not cleaned:
            return {}
        inv_lc = self.field.inv(self.lc(cleaned))
        return self.smul(inv_lc, cleaned)

    def eval(self, poly: SparseMPoly[V], point: Sequence[V]) -> V:
        """Evaluate polynomial at `point = (p_1, ..., p_n)` in $k^n$."""
        if len(point) != self.n_vars:
            raise ValueError(f'Expected evaluation point of length {self.n_vars}, got {len(point)}.')
        res = self.field.zero
        f_mul = self.field.mul
        f_add = self.field.add
        for mon, coeff in poly.items():
            term = coeff
            for xi, exp in zip(point, mon, strict=True):
                if exp:
                    term = f_mul(term, _field_pow(self.field, xi, exp))
            res = f_add(res, term)
        return res

    def diff(self, a: SparseMPoly[V], var_index: int = 0) -> SparseMPoly[V]:
        r"""Formal algebraic partial derivative $\frac{\partial f}{\partial x_i}$ over `self.field`.

        Purely algebraic ($\alpha_i c_\alpha x^{\alpha - e_i}$); works over any exact field,
        including finite prime fields `ModularField(p)` and Galois extensions `GaloisField`.
        """
        if not (0 <= var_index < self.n_vars):
            raise IndexError(f'Variable index {var_index} out of range for n_vars={self.n_vars}.')
        res: SparseMPoly[V] = {}
        is_zero = self.field.is_zero
        for mon, coeff in a.items():
            exp = mon[var_index]
            if exp == 0:
                continue
            scaled = _field_scale_int(self.field, coeff, exp)
            if not is_zero(scaled):
                new_mon = (*mon[:var_index], exp - 1, *mon[var_index + 1 :])
                res[new_mon] = scaled
        return res

    def univariate_gcd(
        self,
        f: SparseMPoly[V],
        g: SparseMPoly[V],
        var_index: int = 0,
    ) -> SparseMPoly[V]:
        r"""Compute the monic Euclidean GCD of two univariate polynomials in variable $x_i$."""
        if not (0 <= var_index < self.n_vars):
            raise IndexError(f'Variable index {var_index} out of range for n_vars={self.n_vars}.')
        uf = _extract_univariate(f, var_index, self.field)
        ug = _extract_univariate(g, var_index, self.field)
        gcd_uni = _uni_gcd(uf, ug, self.field)
        return _lift_univariate(gcd_uni, self.n_vars, var_index, self.field)

    def square_free_part(self, f: SparseMPoly[V], var_index: int = 0) -> SparseMPoly[V]:
        r"""Return the monic square-free part of a univariate polynomial in variable $x_{\text{var\_index}}$.

        In characteristic 0 computes $f / \gcd(f, \partial f / \partial x_i)$.
        In finite characteristic $p > 0$ (e.g. `ModularField(p)`, `GaloisField`),
        also extracts pure $p$-th power factors via exact Frobenius inversion.
        """
        if not (0 <= var_index < self.n_vars):
            raise IndexError(f'Variable index {var_index} out of range for n_vars={self.n_vars}.')
        uf = _extract_univariate(f, var_index, self.field)
        if not uf:
            return {}
        if max(uf.keys()) == 0:
            return self.one
        sf_uni = self._uni_square_free(uf)
        return _lift_univariate(sf_uni, self.n_vars, var_index, self.field)

    def _uni_square_free(self, uf: dict[int, V]) -> dict[int, V]:
        """Compute monic square-free part of a non-constant univariate dict over `self.field`."""
        df: dict[int, V] = {}
        for deg, coeff in uf.items():
            if deg > 0:
                scaled = _field_scale_int(self.field, coeff, deg)
                if not self.field.is_zero(scaled):
                    df[deg - 1] = scaled

        if not df:
            root = _uni_pth_root(uf, self.field)
            if root is not None:
                return self._uni_square_free(root)
            return _uni_make_monic(uf, self.field)

        g = _uni_gcd(uf, df, self.field)
        if max(g.keys()) == 0:
            return _uni_make_monic(uf, self.field)

        w, _ = _uni_divmod(uf, g, self.field)
        w = _uni_make_monic(w, self.field)

        # Remove any remaining factors of w from g; what remains in char p is a pure p-th power.
        rem_g = g
        while max(rem_g.keys()) > 0:
            h = _uni_gcd(w, rem_g, self.field)
            if max(h.keys()) == 0:
                break
            rem_g, _ = _uni_divmod(rem_g, h, self.field)

        if max(rem_g.keys()) > 0:
            root = _uni_pth_root(rem_g, self.field)
            if root is not None:
                sf_tail = self._uni_square_free(root)
                return _uni_make_monic(_uni_mul(w, sf_tail, self.field), self.field)
        return w

    def poisson_bracket(self, f: SparseMPoly[V], g: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Canonical symplectic Poisson bracket on $k[q_1, \dots, q_m, p_1, \dots, p_m]$:
        $$\{f, g\} = \sum_{i=1}^{m} \left( \frac{\partial f}{\partial q_i} \frac{\partial g}{\partial p_i}
        - \frac{\partial f}{\partial p_i} \frac{\partial g}{\partial q_i} \right)$$

        Requires even `n_vars = 2 * m` ordered as $(q_1, \dots, q_m, p_1, \dots, p_m)$.
        """
        if self.n_vars % 2 != 0:
            raise ValueError(
                f'Canonical Poisson bracket requires an even number of phase-space variables, got n_vars={self.n_vars}.'
            )
        m = self.n_vars // 2
        res: SparseMPoly[V] = {}
        for i in range(m):
            df_dq = self.diff(f, i)
            dg_dp = self.diff(g, m + i)
            df_dp = self.diff(f, m + i)
            dg_dq = self.diff(g, i)
            term = self.sub(self.mul(df_dq, dg_dp), self.mul(df_dp, dg_dq))
            res = self.add(res, term)
        return res

    def bracket(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
        """Poisson bracket alias fulfilling the `PoissonAlgebra` / `HasBracket` protocol."""
        return self.poisson_bracket(a, b)

    def s_poly(self, f: SparseMPoly[V], g: SparseMPoly[V]) -> SparseMPoly[V]:
        r"""Compute the S-polynomial $S(f, g) = \frac{\operatorname{lcm}}{\operatorname{LT}(f)} f
        - \frac{\operatorname{lcm}}{\operatorname{LT}(g)} g$.
        """
        lm_f, lc_f = self.lt(f)
        lm_g, lc_g = self.lt(g)
        lcm = monomial_lcm(lm_f, lm_g)
        t_f = self.mul_term(f, monomial_sub(lcm, lm_f), self.field.inv(lc_f))
        t_g = self.mul_term(g, monomial_sub(lcm, lm_g), self.field.inv(lc_g))
        return self.sub(t_f, t_g)

    def reduce_poly(
        self,
        f: SparseMPoly[V],
        basis: Sequence[SparseMPoly[V]],
    ) -> SparseMPoly[V]:
        """Multivariate division algorithm returning remainder of `f` modulo `basis`."""
        p = self.clean(f)
        rem: SparseMPoly[V] = {}
        basis_lms: list[tuple[SparseMPoly[V], Monomial, V]] = []
        for g in basis:
            g_clean = self.clean(g)
            if g_clean:
                g_lm = self.lm(g_clean)
                basis_lms.append((g_clean, g_lm, g_clean[g_lm]))

        while p:
            lt_m = self.lm(p)
            lt_c = p[lt_m]
            reduced = False
            for g, g_lm, g_lc in basis_lms:
                if monomial_divides(g_lm, lt_m):
                    q_m = monomial_sub(lt_m, g_lm)
                    q_c = self.field.div(lt_c, g_lc)
                    p = self.sub(p, self.mul_term(g, q_m, q_c))
                    reduced = True
                    break
            if not reduced:
                del p[lt_m]
                rem[lt_m] = lt_c
        return rem


__all__ = [
    'Monomial',
    'MonomialOrder',
    'MultivariatePolynomialAlgebra',
    'PolynomialAlgebra',
    'SparseMPoly',
    'monomial_add',
    'monomial_divides',
    'monomial_lcm',
    'monomial_sub',
    'order_key_grevlex',
    'order_key_grlex',
    'order_key_lex',
]
