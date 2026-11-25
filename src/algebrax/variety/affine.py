r"""
Affine algebraic varieties $V(I) \subseteq k^n$ and their coordinate rings $k[V] = k[x_1, \dots, x_n]/I$.

Implements the Noetherian ideal-variety dictionary over exact fields:
- Zero-overhead coordinate rings via `QuotientRing(ring, GroebnerIdeal)`
- Exact Krull dimension via maximal independent variable sets of $\langle \mathrm{LT}(I) \rangle$
- Exact affine Hilbert function $\operatorname{HF}_{k[V]}(d) = \dim_k k[V]_{\le d}$
- Standard monomial quotient bases $\mathcal{B} = \{x^\alpha \notin \langle \mathrm{LT}(I) \rangle\}$
- Algebraic Jacobian matrices $J(p)$ and exact smoothness testing over any `Field[V]`
- Zero-dimensional radicalization $V(\sqrt{I})$ via Seidenberg's Lemma
- Variety intersection $V(I+J)$, union $V(I \cap J)$, and projection via `lex` elimination
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, TypeVar

from algebrax.algebra import (
    Field,
    GaloisField,
    GroebnerIdeal,
    GroebnerMethod,
    ModularField,
    Monomial,
    MultivariatePolynomialAlgebra,
    PAdicField,
    QuotientRing,
    SparseMPoly,
    StandardField,
    groebner_basis,
    monomial_divides,
    monomial_sub,
)
from algebrax.typing import SparseMatrix
from algebrax.variety._mixins import SmoothableVariety

V = TypeVar('V')


def _fields_compatible(f1: Field[Any], f2: Field[Any]) -> bool:
    """Return True iff two `Field` instances represent the same mathematical coefficient field."""
    if type(f1) is not type(f2):
        return False
    if isinstance(f1, ModularField) and isinstance(f2, ModularField):
        return f1.p == f2.p
    if isinstance(f1, GaloisField) and isinstance(f2, GaloisField):
        return f1.p == f2.p and f1.irreduc_poly == f2.irreduc_poly
    if isinstance(f1, PAdicField) and isinstance(f2, PAdicField):
        return f1.p == f2.p and f1.precision == f2.precision
    if isinstance(f1, StandardField) and isinstance(f2, StandardField):
        return f1._dtype is f2._dtype
    return True


def _sparse_jacobian_pivot_rows(
    matrix: SparseMatrix[int, V],
    field: Field[V],
) -> list[int]:
    """Return row indices forming a maximal linearly independent subset via exact Gaussian elimination."""
    pivots: dict[int, dict[int, V]] = {}
    pivot_rows: list[int] = []
    is_zero = field.is_zero
    f_mul = field.mul
    f_sub = field.sub
    f_inv = field.inv

    for row_idx in sorted(matrix.keys()):
        row = matrix[row_idx]
        cur = {c: v for c, v in row.items() if not is_zero(v)}
        while cur:
            col = min(cur.keys())
            piv = pivots.get(col)
            if piv is not None:
                factor = cur[col]
                for pc, pv in piv.items():
                    updated = f_sub(cur.get(pc, field.zero), f_mul(factor, pv))
                    if is_zero(updated):
                        cur.pop(pc, None)
                    else:
                        cur[pc] = updated
            else:
                inv_lead = f_inv(cur[col])
                pivots[col] = {c: f_mul(inv_lead, v) for c, v in cur.items()}
                pivot_rows.append(row_idx)
                break

    return pivot_rows


def _exact_poly_quotient(
    ring: MultivariatePolynomialAlgebra[V],
    dividend: SparseMPoly[V],
    divisor: SparseMPoly[V],
) -> SparseMPoly[V]:
    """Compute exact quotient dividend / divisor when divisor divides dividend in `ring`."""
    p = ring.clean(dividend)
    g = ring.clean(divisor)
    if not g:
        raise ZeroDivisionError('Cannot divide by the zero polynomial.')
    g_lm = ring.lm(g)
    g_lc = g[g_lm]
    quot: SparseMPoly[V] = {}
    while p:
        p_lm = ring.lm(p)
        if not monomial_divides(g_lm, p_lm):
            raise ValueError('Polynomial is not an exact multiple of divisor.')
        q_m = monomial_sub(p_lm, g_lm)
        q_c = ring.field.div(p[p_lm], g_lc)
        quot[q_m] = ring.field.add(quot.get(q_m, ring.field.zero), q_c)
        if ring.field.is_zero(quot[q_m]):
            del quot[q_m]
        p = ring.sub(p, ring.mul_term(g, q_m, q_c))
    return quot


def _min_hitting_set_size(masks: list[int], n_vars: int) -> int:
    """Return minimum cardinality of a set hitting every non-zero bitmask in `masks`."""
    if not masks:
        return 0

    # Keep only inclusion-minimal support bitmasks
    unique_masks = sorted(set(masks), key=lambda m: m.bit_count())
    minimal: list[int] = []
    for mask in unique_masks:
        if not any((prev & mask) == prev for prev in minimal):
            minimal.append(mask)

    best = n_vars

    def _search(remaining: list[int], chosen_count: int) -> None:
        nonlocal best
        if chosen_count >= best:
            return
        if not remaining:
            best = chosen_count
            return

        # Pick the smallest uncovered support mask to branch on
        pivot_mask = remaining[0]
        # Order candidate bits by how many remaining masks they cover (most first)
        bits = [bit for bit in range(n_vars) if (pivot_mask >> bit) & 1]
        bits.sort(key=lambda b: sum(1 for m in remaining if (m >> b) & 1), reverse=True)

        for bit in bits:
            bit_flag = 1 << bit
            next_rem = [m for m in remaining if not (m & bit_flag)]
            _search(next_rem, chosen_count + 1)

    _search(minimal, 0)
    return best


def _count_standard_monomials(
    n_vars: int,
    lms: Sequence[Monomial],
    max_degree: int,
) -> int:
    r"""Count monomials $x^\alpha \notin \langle \mathrm{lms} \rangle$ with total degree $|\alpha| \le d$."""
    if max_degree < 0:
        return 0
    if not lms:
        return math.comb(max_degree + n_vars, n_vars)
    if any(all(e == 0 for e in lm) for lm in lms):
        return 0

    # Precompute pure-power upper bounds for each variable x_i
    var_caps: list[int] = [max_degree + 1] * n_vars
    for lm in lms:
        nz = [i for i, e in enumerate(lm) if e > 0]
        if len(nz) == 1:
            idx = nz[0]
            var_caps[idx] = min(var_caps[idx], lm[idx])

    # Group leading monomials by their last active variable index for early pruning
    lms_by_last: list[list[Monomial]] = [[] for _ in range(n_vars)]
    for lm in lms:
        last_idx = max(i for i, e in enumerate(lm) if e > 0)
        lms_by_last[last_idx].append(lm)

    prefix: list[int] = [0] * n_vars

    def _dfs(var_idx: int, remaining_deg: int) -> int:
        if var_idx == n_vars:
            return 1
        upper = min(remaining_deg, var_caps[var_idx] - 1)
        if upper < 0:
            return 0
        checks = lms_by_last[var_idx]
        total = 0
        for exp in range(upper + 1):
            prefix[var_idx] = exp
            blocked = False
            for lm in checks:
                if all(lm[j] <= prefix[j] for j in range(var_idx + 1)):
                    blocked = True
                    break
            if not blocked:
                total += _dfs(var_idx + 1, remaining_deg - exp)
        prefix[var_idx] = 0
        return total

    return _dfs(0, max_degree)


def _minimal_univariate_poly(
    variety: AffineVariety[V],
    var_index: int,
    basis: list[Monomial],
) -> SparseMPoly[V]:
    r"""Compute the unique monic generator of $I \cap k[x_i]$ via linear dependence in $k[V]$."""
    ring = variety.ring
    field = ring.field
    is_zero = field.is_zero
    f_mul = field.mul
    f_sub = field.sub
    f_inv = field.inv

    idx_map = {m: idx for idx, m in enumerate(basis)}
    xi = ring.gen(var_index)
    max_deg = len(basis)

    # Incremental echelon basis mapping pivot_col -> (normalized_vec, poly_coeffs_in_xi)
    pivots: dict[int, tuple[dict[int, V], dict[int, V]]] = {}
    cur_power: SparseMPoly[V] = variety.ideal.reduce(ring.one)

    for deg in range(max_deg + 1):
        vec: dict[int, V] = {idx_map[m]: c for m, c in cur_power.items() if not is_zero(c)}
        comb: dict[int, V] = {deg: field.one}

        while vec:
            col = min(vec.keys())
            piv = pivots.get(col)
            if piv is not None:
                piv_vec, piv_comb = piv
                factor = vec[col]
                for pc, pv in piv_vec.items():
                    updated = f_sub(vec.get(pc, field.zero), f_mul(factor, pv))
                    if is_zero(updated):
                        vec.pop(pc, None)
                    else:
                        vec[pc] = updated
                for pd, pc_val in piv_comb.items():
                    updated_c = f_sub(comb.get(pd, field.zero), f_mul(factor, pc_val))
                    if is_zero(updated_c):
                        comb.pop(pd, None)
                    else:
                        comb[pd] = updated_c
            else:
                inv_lead = f_inv(vec[col])
                pivots[col] = (
                    {c: f_mul(inv_lead, v) for c, v in vec.items()},
                    {d: f_mul(inv_lead, c) for d, c in comb.items()},
                )
                break
        else:
            # vec reduced completely to 0 => comb encodes the exact monic minimal polynomial in x_i
            prefix = (0,) * var_index
            suffix = (0,) * (ring.n_vars - var_index - 1)
            poly: SparseMPoly[V] = {
                (*prefix, d, *suffix): coeff for d, coeff in comb.items() if not is_zero(coeff)
            }
            return ring.make_monic(poly)

        cur_power = variety.ideal.reduce(ring.mul(cur_power, xi))

    raise RuntimeError(f'Failed to find univariate minimal polynomial for variable index {var_index}.')


class AffineVariety(SmoothableVariety[V]):
    r"""An affine algebraic variety $V(I) = \{p \in k^n \mid f(p) = 0 \;\forall f \in I\}$.

    Algebraic Signature:
        $\langle \mathbb{A}^n, V(I), I, k[V], J(p), \operatorname{is\_smooth\_at}, \dim V(I) \rangle$

    Carrier:
        Geometric zero locus $V(I) \subseteq k^n$ paired with its dual coordinate ring
        $k[V] = k[x_1, \dots, x_n] / I$ realized via `QuotientRing(ring, GroebnerIdeal)`.

    Operations:
        - `contains_point(p)`, `is_empty_over_closure()`, `is_zero_dimensional()`: Locus & Nullstellensatz queries.
        - `krull_dimension()`, `hilbert_function(d)`, `quotient_basis()`: Exact dimension and standard basis invariants.
        - `jacobian_at(p)`, `is_smooth_at(p)`: Exact algebraic Jacobian and local scheme regularity test.
        - `radical_zero_dim()`: Zero-dimensional radical $V(\sqrt{I})$ via Seidenberg's Lemma.
        - `intersect(other)`, `union(other)`, `eliminate(k)`: Exact Zariski set-theoretic and projection operations.

    Properties:
        Satisfies `GeometricVariety[V]` and `SmoothableVariety[V]`. Works over any exact `Field[V]`
        (including $\mathbb{Q}$, $\mathbb{F}_p$, and $\mathrm{GF}(p^m)$).

    Args:
        ring: Ambient multivariate polynomial ring $k[x_1, \dots, x_n]$.
        generators: Defining polynomial generators of the ideal $I$.
        method: Gröbner basis algorithm (`'auto'`, `'buchberger'`, or `'f4'`).

    Example:
        >>> from fractions import Fraction
        >>> from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
        >>> from algebrax.variety import AffineVariety
        >>> Q = StandardField(Fraction)
        >>> R = MultivariatePolynomialAlgebra(Q, n_vars=2, order='grevlex')
        >>> circle = {(2, 0): Fraction(1), (0, 2): Fraction(1), (0, 0): Fraction(-5)}
        >>> hyperb = {(1, 1): Fraction(1), (0, 0): Fraction(-2)}
        >>> V = AffineVariety(R, [circle, hyperb])
        >>> V.krull_dimension()
        0
        >>> V.contains_point((Fraction(1), Fraction(2)))
        True
        >>> V.is_smooth_at((Fraction(1), Fraction(2)))
        True
    """

    def __init__(
        self,
        ring: MultivariatePolynomialAlgebra[V],
        generators: Sequence[SparseMPoly[V]],
        *,
        method: GroebnerMethod = 'auto',
    ) -> None:
        n = ring.n_vars
        for gen in generators:
            for mon in gen:
                if len(mon) != n:
                    raise ValueError(
                        f'Generator monomial {mon!r} has arity {len(mon)}, expected {n}.'
                    )
        self.ring: MultivariatePolynomialAlgebra[V] = ring
        self._method: GroebnerMethod = method
        self._ideal: GroebnerIdeal[V] = GroebnerIdeal(ring, generators, method=method)
        self._coordinate_ring: QuotientRing[SparseMPoly[V]] = QuotientRing(ring, self._ideal)
        self._quotient_basis_computed: bool = False
        self._quotient_basis_cache: list[Monomial] | None = None
        self._graded_lms_cache: tuple[Monomial, ...] | None = None
        self._krull_dim_cache: int | None = None
        self._jacobian_sparse_cache: list[tuple[int, int, SparseMPoly[V]]] | None = None

    def __repr__(self) -> str:
        return (
            f'AffineVariety(n_vars={self.ring.n_vars}, '
            f'order={self.ring.order!r}, n_basis={len(self._ideal.basis)})'
        )

    @property
    def ambient_dimension(self) -> int:
        r"""Ambient affine space dimension $n$ of $k^n$."""
        return self.ring.n_vars

    @property
    def ideal(self) -> GroebnerIdeal[V]:
        r"""Defining Gröbner ideal $I(V)$."""
        return self._ideal

    @property
    def coordinate_ring(self) -> QuotientRing[SparseMPoly[V]]:
        r"""Coordinate ring $k[V] = k[x_1, \dots, x_n] / I$."""
        return self._coordinate_ring

    def has_same_ideal(self, other: AffineVariety[V]) -> bool:
        r"""Return True iff `self` and `other` define the exact same ideal $I = J$ (order-invariant)."""
        self._validate_compatible(other)
        return all(other.ideal.contains(g) for g in self._ideal.basis) and all(
            self._ideal.contains(g) for g in other.ideal.basis
        )

    def contains_point(self, point: Sequence[V]) -> bool:
        r"""Return True iff point $p \in k^n$ satisfies $f(p) = 0$ for all generators.

        Args:
            point: Coordinate sequence $(p_1, \dots, p_n) \in k^n$.

        Raises:
            ValueError: If `len(point) != self.ambient_dimension`.
        """
        if len(point) != self.ring.n_vars:
            raise ValueError(f'Expected point of length {self.ring.n_vars}, got {len(point)}.')
        return all(self.ring.field.is_zero(self.ring.eval(g, point)) for g in self._ideal.basis)

    def is_empty_over_closure(self) -> bool:
        r"""Weak Nullstellensatz check: True iff $1 \in I$ ($V_{\bar{k}}(I) = \emptyset$)."""
        return self._ideal.is_unit()

    def is_zero_dimensional(self) -> bool:
        r"""Return True iff $V(I)$ is non-empty and $k[V]$ is a finite-dimensional $k$-vector space."""
        if self.is_empty_over_closure():
            return False
        if self._quotient_basis_computed:
            return self._quotient_basis_cache is not None
        pure_vars: set[int] = set()
        for g in self._ideal.basis:
            lm = self.ring.lm(g)
            nz = [i for i, e in enumerate(lm) if e > 0]
            if len(nz) == 1:
                pure_vars.add(nz[0])
        return len(pure_vars) == self.ring.n_vars

    def krull_dimension(self) -> int:
        r"""Compute the affine Krull dimension $\dim V(I)$ from the initial ideal $\langle \mathrm{LT}(I) \rangle$.

        Equals the maximum cardinality of an independent subset of variables $S \subseteq \{x_1, \dots, x_n\}$
        such that $\langle \mathrm{LT}(I) \rangle \cap k[S] = \{0\}$ (returns `-1` if $V(I) = \emptyset$).
        """
        if self._krull_dim_cache is not None:
            return self._krull_dim_cache
        if self.is_empty_over_closure():
            self._krull_dim_cache = -1
            return -1
        if not self._ideal.basis:
            self._krull_dim_cache = self.ring.n_vars
            return self.ring.n_vars

        support_masks: list[int] = []
        for g in self._ideal.basis:
            lm = self.ring.lm(g)
            mask = 0
            for idx, exp in enumerate(lm):
                if exp > 0:
                    mask |= 1 << idx
            if mask == 0:
                self._krull_dim_cache = -1
                return -1
            support_masks.append(mask)

        dim = self.ring.n_vars - _min_hitting_set_size(support_masks, self.ring.n_vars)
        self._krull_dim_cache = dim
        return dim

    def dimension(self) -> int:
        """Return intrinsic Krull dimension (`HasDimension` protocol)."""
        return self.krull_dimension()

    def _graded_leading_monomials(self) -> tuple[Monomial, ...]:
        """Return leading monomials under a degree-compatible (`grevlex`/`grlex`) order."""
        if self._graded_lms_cache is not None:
            return self._graded_lms_cache
        if self.ring.order in ('grevlex', 'grlex'):
            lms = tuple(self.ring.lm(g) for g in self._ideal.basis)
        else:
            graded_ring = MultivariatePolynomialAlgebra(self.ring.field, self.ring.n_vars, order='grevlex')
            graded_gb = groebner_basis(graded_ring, self._ideal.basis, method=self._method)
            lms = tuple(graded_ring.lm(g) for g in graded_gb)
        self._graded_lms_cache = lms
        return lms

    def hilbert_function(self, degree: int) -> int:
        r"""Compute the affine Hilbert function $\operatorname{HF}_{k[V]}(d) = \dim_k k[V]_{\le d}$.

        Counts standard monomials $x^\alpha \notin \langle \mathrm{LT}_{\text{graded}}(I) \rangle$
        of total degree $|\alpha| \le d$.
        """
        if degree < 0 or self.is_empty_over_closure():
            return 0
        lms = self._graded_leading_monomials()
        return _count_standard_monomials(self.ring.n_vars, lms, degree)

    def quotient_basis(self) -> list[Monomial] | None:
        r"""Return standard monomial basis $\mathcal{B} = \{x^\alpha \notin \langle \mathrm{LT}(I) \rangle\}$.

        Returns `[]` for the empty variety $V(1) = \emptyset$, and `None` when $\dim V(I) \ge 1$.
        """
        if self._quotient_basis_computed:
            return None if self._quotient_basis_cache is None else list(self._quotient_basis_cache)

        if self.is_empty_over_closure():
            self._quotient_basis_cache = []
            self._quotient_basis_computed = True
            return []

        n = self.ring.n_vars
        lms = [self.ring.lm(g) for g in self._ideal.basis]
        bounds: list[int | None] = [None] * n
        for lm in lms:
            nonzero_dims = [i for i, e in enumerate(lm) if e > 0]
            if len(nonzero_dims) == 1:
                idx = nonzero_dims[0]
                deg = lm[idx]
                cur = bounds[idx]
                bounds[idx] = deg if cur is None else min(cur, deg)

        if any(b is None for b in bounds):
            self._quotient_basis_cache = None
            self._quotient_basis_computed = True
            return None

        int_bounds: list[int] = [b for b in bounds if b is not None]
        lms_by_last: list[list[Monomial]] = [[] for _ in range(n)]
        for lm in lms:
            last_idx = max(i for i, e in enumerate(lm) if e > 0)
            lms_by_last[last_idx].append(lm)

        basis: list[Monomial] = []
        prefix: list[int] = [0] * n

        def _dfs(var_idx: int) -> None:
            if var_idx == n:
                basis.append(tuple(prefix))
                return
            checks = lms_by_last[var_idx]
            for exp in range(int_bounds[var_idx]):
                prefix[var_idx] = exp
                blocked = False
                for lm in checks:
                    if all(lm[j] <= prefix[j] for j in range(var_idx + 1)):
                        blocked = True
                        break
                if not blocked:
                    _dfs(var_idx + 1)
            prefix[var_idx] = 0

        _dfs(0)
        basis.sort(key=self.ring.key_fn)
        self._quotient_basis_cache = basis
        self._quotient_basis_computed = True
        return list(basis)

    def jacobian_poly_matrix(self) -> list[list[SparseMPoly[V]]]:
        r"""Return the formal $m \times n$ algebraic Jacobian matrix $J_{ij} = \frac{\partial g_i}{\partial x_j}$."""
        n = self.ring.n_vars
        return [[self.ring.diff(g, j) for j in range(n)] for g in self._ideal.basis]

    def _jacobian_sparse_entries(self) -> list[tuple[int, int, SparseMPoly[V]]]:
        """Return cached non-zero formal Jacobian entries `(row, col, partial_poly)`."""
        if self._jacobian_sparse_cache is not None:
            return self._jacobian_sparse_cache
        n = self.ring.n_vars
        entries: list[tuple[int, int, SparseMPoly[V]]] = []
        for row_idx, g in enumerate(self._ideal.basis):
            for col_idx in range(n):
                diff_g = self.ring.diff(g, col_idx)
                if diff_g:
                    entries.append((row_idx, col_idx, diff_g))
        self._jacobian_sparse_cache = entries
        return entries

    def jacobian_at(self, point: Sequence[V]) -> SparseMatrix[int, V]:
        r"""Evaluate the Jacobian matrix $J(p)$ at `point` $p \in k^n$ (tangent space $T_p V = \ker J(p)$).

        Args:
            point: Coordinate sequence $(p_1, \dots, p_n) \in k^n$.

        Raises:
            ValueError: If `len(point) != self.ambient_dimension`.
        """
        if len(point) != self.ring.n_vars:
            raise ValueError(f'Expected point of length {self.ring.n_vars}, got {len(point)}.')
        is_zero = self.ring.field.is_zero
        mat: dict[int, dict[int, V]] = {}
        for row_idx, col_idx, poly in self._jacobian_sparse_entries():
            val = self.ring.eval(poly, point)
            if not is_zero(val):
                mat.setdefault(row_idx, {})[col_idx] = val
        return mat

    def is_smooth_at(self, point: Sequence[V]) -> bool:
        r"""Exact local regularity / smoothness criterion at $p \in V(I)$.

        Tests whether the local ring $\mathcal{O}_{V, p} = (k[X]/I)_{\mathfrak{m}_p}$ is regular
        (valid for irreducible, reducible, mixed-dimension, and positive-characteristic ideals;
        non-reduced ideals such as $\langle x^2 \rangle$ are scheme-theoretically non-regular).

        Uses the exact Jacobian-colon characterization: if $r = \operatorname{rank} J(p)$ is
        realized by generators $L = \langle g_{i_1}, \dots, g_{i_r} \rangle \subseteq I$, then
        $\mathcal{O}_{V, p}$ is regular iff $I_{\mathfrak{m}_p} = L_{\mathfrak{m}_p}$, i.e., iff
        $(L : g) \not\subseteq \mathfrak{m}_p$ for every remaining generator $g \in I$.

        Args:
            point: Coordinate sequence $(p_1, \dots, p_n) \in k^n$.

        Raises:
            ValueError: If `len(point) != self.ambient_dimension`.
        """
        if not self.contains_point(point):
            return False
        basis = self._ideal.basis
        if not basis:
            return True

        jac = self.jacobian_at(point)
        pivot_rows = _sparse_jacobian_pivot_rows(jac, self.ring.field)
        rank = len(pivot_rows)
        if rank == self.ambient_dimension:
            return True
        if rank == 0:
            return False
        if rank == len(basis):
            return True

        # General mixed-dimension / reducible case: verify I_{m_p} == L_{m_p} via (L : g) not in m_p
        pivot_set = set(pivot_rows)
        l_ideal = GroebnerIdeal(self.ring, [basis[i] for i in pivot_rows], method=self._method)
        n = self.ring.n_vars
        ext_ring = MultivariatePolynomialAlgebra(self.ring.field, n + 1, order='lex')
        t = ext_ring.gen(0)
        one_minus_t = ext_ring.sub(ext_ring.one, t)
        l_lifted = [ext_ring.mul(t, {(0, *m): c for m, c in f.items()}) for f in l_ideal.basis]
        is_zero = self.ring.field.is_zero

        for idx, g in enumerate(basis):
            if idx in pivot_set or l_ideal.contains(g):
                continue
            g_lifted = ext_ring.mul(one_minus_t, {(0, *m): c for m, c in g.items()})
            gb = groebner_basis(ext_ring, [*l_lifted, g_lifted], method=self._method)
            has_unit_colon = False
            for poly in gb:
                if all(m[0] == 0 for m in poly):
                    inter_poly = {m[1:]: c for m, c in poly.items()}
                    quot = _exact_poly_quotient(self.ring, inter_poly, g)
                    if not is_zero(self.ring.eval(quot, point)):
                        has_unit_colon = True
                        break
            if not has_unit_colon:
                return False
        return True

    def radical_zero_dim(self) -> AffineVariety[V]:
        r"""Compute the 0-dimensional radical variety $V(\sqrt{I})$ via Seidenberg's Lemma.

        Adjoins the square-free parts $f_i / \gcd(f_i, f_i')$ (with Frobenius $p$-th root extraction
        in finite characteristic) of the univariate minimal polynomials $f_i \in I \cap k[x_i]$,
        guaranteeing semisimple (diagonalizable) Stickelberger companion matrices.

        Raises:
            ValueError: If `self` is positive-dimensional.
        """
        if self.is_empty_over_closure():
            return self
        basis = self.quotient_basis()
        if basis is None:
            raise ValueError('radical_zero_dim requires a zero-dimensional variety.')

        sf_gens: list[SparseMPoly[V]] = []
        for var_idx in range(self.ring.n_vars):
            min_poly = _minimal_univariate_poly(self, var_idx, basis)
            sf_poly = self.ring.square_free_part(min_poly, var_index=var_idx)
            sf_gens.append(sf_poly)

        if all(self._ideal.contains(sf) for sf in sf_gens):
            return self
        return AffineVariety(self.ring, [*self._ideal.basis, *sf_gens], method=self._method)

    def _validate_compatible(self, other: AffineVariety[V]) -> None:
        if self.ring.n_vars != other.ring.n_vars:
            raise ValueError(
                f'Incompatible ambient dimensions: {self.ring.n_vars} vs {other.ring.n_vars}.'
            )
        if not _fields_compatible(self.ring.field, other.ring.field):
            raise TypeError(
                f'Incompatible coefficient fields: {self.ring.field!r} vs {other.ring.field!r}.'
            )

    def intersect(self, other: AffineVariety[V]) -> AffineVariety[V]:
        r"""Geometric intersection $V(I) \cap V(J) = V(I + J)$.

        Args:
            other: Another `AffineVariety` in the same ambient space and coefficient field.

        Raises:
            ValueError: If ambient dimensions differ.
            TypeError: If coefficient fields are incompatible.
        """
        self._validate_compatible(other)
        return AffineVariety(self.ring, [*self._ideal.basis, *other.ideal.basis], method=self._method)

    def union(self, other: AffineVariety[V]) -> AffineVariety[V]:
        r"""Geometric union $V(I) \cup V(J) = V(I \cap J)$ via ideal intersection $(tI + (1-t)J) \cap k[X]$.

        Args:
            other: Another `AffineVariety` in the same ambient space and coefficient field.

        Raises:
            ValueError: If ambient dimensions differ.
            TypeError: If coefficient fields are incompatible.
        """
        self._validate_compatible(other)
        if self.is_empty_over_closure():
            if other.ring.order == self.ring.order:
                return other
            return AffineVariety(self.ring, other.ideal.basis, method=self._method)
        if other.is_empty_over_closure():
            return self
        if not self._ideal.basis or not other.ideal.basis:
            return AffineVariety(self.ring, [], method=self._method)

        n = self.ring.n_vars
        ext_ring = MultivariatePolynomialAlgebra(self.ring.field, n + 1, order='lex')
        t = ext_ring.gen(0)
        one_minus_t = ext_ring.sub(ext_ring.one, t)

        ext_gens: list[SparseMPoly[V]] = []
        for f in self._ideal.basis:
            lifted = {(0, *m): c for m, c in f.items()}
            ext_gens.append(ext_ring.mul(t, lifted))
        for g in other.ideal.basis:
            lifted = {(0, *m): c for m, c in g.items()}
            ext_gens.append(ext_ring.mul(one_minus_t, lifted))

        gb = groebner_basis(ext_ring, ext_gens, method=self._method)
        inter_gens = [
            {m[1:]: c for m, c in poly.items()}
            for poly in gb
            if all(m[0] == 0 for m in poly)
        ]
        return AffineVariety(self.ring, inter_gens, method=self._method)

    def eliminate(self, num_vars_to_eliminate: int) -> AffineVariety[V]:
        r"""Compute the $k$-th elimination variety $V(I \cap k[x_{k+1}, \dots, x_n])$ using `lex` order.

        Args:
            num_vars_to_eliminate: Number of leading variables $k$ ($0 \le k < n$) to eliminate.

        Raises:
            ValueError: If `num_vars_to_eliminate` is not in `[0, n - 1]`.
        """
        if not (0 <= num_vars_to_eliminate < self.ring.n_vars):
            raise ValueError(
                f'num_vars_to_eliminate must satisfy 0 <= k < {self.ring.n_vars}, got {num_vars_to_eliminate}.'
            )
        if num_vars_to_eliminate == 0:
            return self

        if self.ring.order == 'lex':
            lex_gb: Sequence[SparseMPoly[V]] = self._ideal.basis
        else:
            lex_ring = MultivariatePolynomialAlgebra(self.ring.field, self.ring.n_vars, order='lex')
            lex_gb = groebner_basis(lex_ring, self._ideal.basis, method=self._method)

        elim_ring = MultivariatePolynomialAlgebra(
            self.ring.field,
            self.ring.n_vars - num_vars_to_eliminate,
            order=self.ring.order,
        )
        projected: list[SparseMPoly[V]] = []
        for poly in lex_gb:
            if all(all(m[i] == 0 for i in range(num_vars_to_eliminate)) for m in poly):
                projected.append({m[num_vars_to_eliminate:]: c for m, c in poly.items()})

        return AffineVariety(elim_ring, projected, method=self._method)


__all__ = [
    'AffineVariety',
]
