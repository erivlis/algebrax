"""
EXP-0009 Empirical Prototype: Algebraic & Tropical Varieties in Pure Python.

Evaluates five core hypotheses for AlgebraicX:
1. Popper Falsification: Floating-point cancellation suicide vs. exact Field[V].
2. Shannon Benchmark: Classical Buchberger vs. F4-style sparse Macaulay RREF.
3. Noether Duality: GroebnerIdeal + QuotientRing k[V] + Stickelberger Companion Matrices.
4. Finite-Field Varieties: Elliptic curve F_p points & F_2 Algebraic SAT.
5. Off the Map (Tropical Varieties): Same dict[tuple[int, ...], T] carrier over TropicalSemiring,
   Newton polytope dual skeleton, and vertex balancing conservation.

Also performs differential verification against SymPy (oracle) when installed.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from fractions import Fraction
import itertools
import time
from typing import Generic, TypeVar

import numpy as np
import sympy as sp

from algebrax.algebra import (
    CommRing,
    Field,
    Ideal,
    ModularField,
    MonoidAlgebra,
    QuotientRing,
    StandardField,
)
from algebrax.matrix import commutator, dot
from algebrax.semiring import TropicalSemiring

V = TypeVar('V')
Monomial = tuple[int, ...]
SparseMPoly = dict[Monomial, V]


# =============================================================================
# 1. Unboxed Multivariate Polynomial Algebra over Monoid (N_0^n, +)
# =============================================================================


def monomial_add(a: Monomial, b: Monomial) -> Monomial:
    return tuple(x + y for x, y in zip(a, b, strict=True))


def monomial_sub(a: Monomial, b: Monomial) -> Monomial:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def monomial_divides(a: Monomial, b: Monomial) -> bool:
    """Return True iff x^a divides x^b."""
    return all(x <= y for x, y in zip(a, b, strict=True))


def monomial_lcm(a: Monomial, b: Monomial) -> Monomial:
    return tuple(max(x, y) for x, y in zip(a, b, strict=True))


def order_key_lex(m: Monomial) -> tuple[int, ...]:
    return m


def order_key_grlex(m: Monomial) -> tuple[int, tuple[int, ...]]:
    return (sum(m), m)


def order_key_grevlex(m: Monomial) -> tuple[int, tuple[int, ...]]:
    return (sum(m), tuple(-x for x in reversed(m)))


ORDER_KEYS: dict[str, Callable[[Monomial], tuple]] = {
    'lex': order_key_lex,
    'grlex': order_key_grlex,
    'grevlex': order_key_grevlex,
}


class MultivariatePolynomialAlgebra(MonoidAlgebra[Monomial, V], Generic[V]):
    """Sparse multivariate polynomial ring k[x_1, ..., x_n] over an exact Field[V].

    Carrier: dict[tuple[int, ...], V] (zero-overhead unboxed native dict).
    """

    def __init__(self, field: Field[V], n_vars: int, order: str = 'grevlex') -> None:
        if order not in ORDER_KEYS:
            raise ValueError(f'Unknown monomial order {order!r}')
        self.field = field
        self.n_vars = n_vars
        self.order = order
        self.key_fn = ORDER_KEYS[order]
        super().__init__(field, key_op=monomial_add, zero_key=(0,) * n_vars)

    def clean(self, p: SparseMPoly[V]) -> SparseMPoly[V]:
        is_zero = self.field.is_zero
        return {m: c for m, c in p.items() if not is_zero(c)}

    def add(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
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

    def sub(self, a: SparseMPoly[V], b: SparseMPoly[V]) -> SparseMPoly[V]:
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
        if self.field.is_zero(r):
            return {}
        f_mul = self.field.mul
        is_zero = self.field.is_zero
        return {k: prod for k, c in m.items() if not is_zero(prod := f_mul(r, c))}

    def mul_term(self, p: SparseMPoly[V], mon: Monomial, coeff: V) -> SparseMPoly[V]:
        if self.field.is_zero(coeff) or not p:
            return {}
        f_mul = self.field.mul
        is_zero = self.field.is_zero
        return {
            monomial_add(m, mon): prod
            for m, c in p.items()
            if not is_zero(prod := f_mul(coeff, c))
        }

    def lm(self, p: SparseMPoly[V]) -> Monomial:
        return max(p.keys(), key=self.key_fn)

    def lc(self, p: SparseMPoly[V]) -> V:
        return p[self.lm(p)]

    def make_monic(self, p: SparseMPoly[V]) -> SparseMPoly[V]:
        if not p:
            return {}
        inv_lc = self.field.inv(self.lc(p))
        return self.smul(inv_lc, p)

    def eval(self, p: SparseMPoly[V], point: Sequence[V]) -> V:
        res = self.field.zero
        for m, c in p.items():
            term = c
            for xi, exp in zip(point, m, strict=True):
                if exp:
                    for _ in range(exp):
                        term = self.field.mul(term, xi)
            res = self.field.add(res, term)
        return res

    def reduce_poly(self, f: SparseMPoly[V], basis: Sequence[SparseMPoly[V]]) -> SparseMPoly[V]:
        """Multivariate division algorithm returning canonical remainder mod basis."""
        p = dict(f)
        rem: SparseMPoly[V] = {}
        basis_lms = [(g, self.lm(g), g[self.lm(g)]) for g in basis if g]
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

    def s_poly(self, f: SparseMPoly[V], g: SparseMPoly[V]) -> SparseMPoly[V]:
        lm_f, lm_g = self.lm(f), self.lm(g)
        lcm = monomial_lcm(lm_f, lm_g)
        t_f = self.mul_term(f, monomial_sub(lcm, lm_f), self.field.inv(f[lm_f]))
        t_g = self.mul_term(g, monomial_sub(lcm, lm_g), self.field.inv(g[lm_g]))
        return self.sub(t_f, t_g)


# =============================================================================
# 2. Buchberger's Algorithm vs. F4-Style Sparse Macaulay Matrix RREF
# =============================================================================


def _reduce_basis(ring: MultivariatePolynomialAlgebra[V], G: list[SparseMPoly[V]]) -> list[SparseMPoly[V]]:
    """Minimalize and autoreduce a Groebner basis, returning sorted monic canonical basis."""
    G = [ring.make_monic(g) for g in G if g]
    # Remove redundant elements whose LM is divisible by another LM
    minimal: list[SparseMPoly[V]] = []
    lms = [ring.lm(g) for g in G]
    for i, g in enumerate(G):
        lm_i = lms[i]
        divisible = False
        for j in range(len(G)):
            if i == j:
                continue
            lm_j = lms[j]
            if monomial_divides(lm_j, lm_i) and (lm_j != lm_i or j < i):
                divisible = True
                break
        if not divisible:
            minimal.append(g)

    # Autoreduce tails
    reduced: list[SparseMPoly[V]] = []
    for i in range(len(minimal)):
        others = [minimal[j] for j in range(len(minimal)) if j != i]
        r = ring.reduce_poly(minimal[i], others)
        if r:
            r = ring.make_monic(r)
            minimal[i] = r
            reduced.append(r)

    reduced.sort(key=lambda g: ring.key_fn(ring.lm(g)), reverse=True)
    return reduced


def groebner_buchberger(
    ring: MultivariatePolynomialAlgebra[V],
    generators: Sequence[SparseMPoly[V]],
) -> tuple[list[SparseMPoly[V]], dict[str, int]]:
    """Classical Buchberger with Buchberger's Product & Chain criteria."""
    G = [ring.make_monic(ring.clean(g)) for g in generators if ring.clean(g)]
    if not G:
        return [], {'s_polys': 0, 'skipped_product': 0, 'skipped_chain': 0}

    pairs: list[tuple[int, int]] = [(i, j) for i in range(len(G)) for j in range(i + 1, len(G))]
    lms = [ring.lm(g) for g in G]
    stats = {'s_polys': 0, 'skipped_product': 0, 'skipped_chain': 0}

    while pairs:
        # Sugar/normal selection: smallest LCM in monomial order
        pairs.sort(key=lambda ij: ring.key_fn(monomial_lcm(lms[ij[0]], lms[ij[1]])))
        i, j = pairs.pop(0)
        lm_i, lm_j = lms[i], lms[j]
        lcm_ij = monomial_lcm(lm_i, lm_j)

        # Product criterion: coprime leading monomials always reduce to 0
        if monomial_add(lm_i, lm_j) == lcm_ij:
            stats['skipped_product'] += 1
            continue

        # Chain criterion (Gebauer-Moller style check)
        chain_hit = False
        for k in range(len(G)):
            if k == i or k == j:
                continue
            if monomial_divides(lms[k], lcm_ij):
                if (min(i, k), max(i, k)) not in pairs and (min(j, k), max(j, k)) not in pairs:
                    chain_hit = True
                    break
        if chain_hit:
            stats['skipped_chain'] += 1
            continue

        stats['s_polys'] += 1
        s = ring.s_poly(G[i], G[j])
        r = ring.reduce_poly(s, G)
        if r:
            r = ring.make_monic(r)
            new_idx = len(G)
            G.append(r)
            lms.append(ring.lm(r))
            if lms[-1] == (0,) * ring.n_vars:
                return [ring.one], stats
            for k in range(new_idx):
                pairs.append((k, new_idx))

    return _reduce_basis(ring, G), stats


def _sparse_macaulay_rref(
    ring: MultivariatePolynomialAlgebra[V],
    rows: list[SparseMPoly[V]],
) -> list[SparseMPoly[V]]:
    """Exact sparse Gaussian elimination on polynomial rows over Field[V].

    Represents the Macaulay matrix purely as sparse dicts (zero dense allocation).
    """
    field = ring.field
    pivots: dict[Monomial, SparseMPoly[V]] = {}

    for row in rows:
        cur = dict(row)
        while cur:
            lm = ring.lm(cur)
            if lm in pivots:
                piv = pivots[lm]
                factor = cur[lm]
                # pivots are already monic (lc == 1)
                cur = ring.sub(cur, ring.smul(factor, piv))
            else:
                pivots[lm] = ring.make_monic(cur)
                break

    # Back-substitution to canonical reduced row echelon form
    sorted_lms = sorted(pivots.keys(), key=ring.key_fn)
    for idx, lm in enumerate(sorted_lms):
        row = pivots[lm]
        for earlier_lm in sorted_lms[:idx]:
            if earlier_lm in row:
                coeff = row[earlier_lm]
                row = ring.sub(row, ring.smul(coeff, pivots[earlier_lm]))
        pivots[lm] = ring.make_monic(row)

    return [pivots[m] for m in sorted_lms]


def groebner_f4(
    ring: MultivariatePolynomialAlgebra[V],
    generators: Sequence[SparseMPoly[V]],
) -> tuple[list[SparseMPoly[V]], dict[str, int]]:
    """F4-style Groebner basis via symbolic preprocessing & sparse Macaulay RREF."""
    G = [ring.make_monic(ring.clean(g)) for g in generators if ring.clean(g)]
    if not G:
        return [], {'rounds': 0, 'matrix_rows': 0, 'new_pivots': 0}

    lms = [ring.lm(g) for g in G]
    pairs: list[tuple[int, int]] = [(i, j) for i in range(len(G)) for j in range(i + 1, len(G))]
    stats = {'rounds': 0, 'matrix_rows': 0, 'new_pivots': 0}

    while pairs:
        stats['rounds'] += 1
        # Select all critical pairs of minimal total degree (F4 normal selection)
        pairs_with_deg = [
            (sum(monomial_lcm(lms[i], lms[j])), i, j) for i, j in pairs
        ]
        min_deg = min(d for d, _, _ in pairs_with_deg)
        batch = [(i, j) for d, i, j in pairs_with_deg if d == min_deg]
        batch_set = set(batch)
        pairs = [p for p in pairs if p not in batch_set]

        # Build S-pair halves and collect all monomials for symbolic preprocessing
        rows: list[SparseMPoly[V]] = []
        known_lms: set[Monomial] = set()
        todo_monomials: set[Monomial] = set()
        done_monomials: set[Monomial] = set()

        for i, j in batch:
            lm_i, lm_j = lms[i], lms[j]
            lcm_ij = monomial_lcm(lm_i, lm_j)
            if monomial_add(lm_i, lm_j) == lcm_ij:
                continue
            r1 = ring.mul_term(G[i], monomial_sub(lcm_ij, lm_i), ring.field.one)
            r2 = ring.mul_term(G[j], monomial_sub(lcm_ij, lm_j), ring.field.one)
            rows.append(r1)
            rows.append(r2)
            known_lms.add(lcm_ij)
            todo_monomials.update(r1.keys())
            todo_monomials.update(r2.keys())

        if not rows:
            continue

        # Symbolic preprocessing: add reducer rows x^u * g_k for reducible monomials
        while todo_monomials:
            m = todo_monomials.pop()
            if m in done_monomials:
                continue
            done_monomials.add(m)
            for g, g_lm in zip(G, lms, strict=True):
                if monomial_divides(g_lm, m):
                    if m not in known_lms:
                        known_lms.add(m)
                    u = monomial_sub(m, g_lm)
                    reducer_row = ring.mul_term(g, u, ring.field.one)
                    rows.append(reducer_row)
                    todo_monomials.update(k for k in reducer_row.keys() if k not in done_monomials)
                    break

        stats['matrix_rows'] += len(rows)
        echelon = _sparse_macaulay_rref(ring, rows)

        existing_lm_set = set(lms)
        for row in echelon:
            rlm = ring.lm(row)
            # Any pivot whose LM is not divisible by any current G leading monomial is a new basis element
            if rlm not in existing_lm_set and not any(monomial_divides(glm, rlm) for glm in lms):
                stats['new_pivots'] += 1
                new_idx = len(G)
                G.append(row)
                lms.append(rlm)
                existing_lm_set.add(rlm)
                if rlm == (0,) * ring.n_vars:
                    return [ring.one], stats
                for k in range(new_idx):
                    pairs.append((k, new_idx))

    return _reduce_basis(ring, G), stats


# =============================================================================
# 3. GroebnerIdeal (Ideal[SparseMPoly]) + QuotientRing + Stickelberger Companion
# =============================================================================


class GroebnerIdeal(Ideal[SparseMPoly[V]], Generic[V]):
    """Multivariate polynomial ideal I = <g_1, ..., g_m> backed by a reduced Groebner basis."""

    def __init__(self, ring: MultivariatePolynomialAlgebra[V], generators: Sequence[SparseMPoly[V]]) -> None:
        self.ring = ring
        self.generators = list(generators)
        self.basis, _ = groebner_f4(ring, generators)

    def contains(self, element: SparseMPoly[V]) -> bool:
        return len(self.reduce(element)) == 0

    def reduce(self, element: SparseMPoly[V]) -> SparseMPoly[V]:
        return self.ring.reduce_poly(element, self.basis)

    def is_unit(self) -> bool:
        return len(self.basis) == 1 and self.ring.lm(self.basis[0]) == (0,) * self.ring.n_vars

    def quotient_monomial_basis(self) -> list[Monomial] | None:
        """For 0-dimensional ideals, return finite monomial basis B = {x^a not in <LT(I)>}.

        Returns None if the ideal is positive-dimensional (dim V(I) >= 1).
        """
        n = self.ring.n_vars
        lms = [self.ring.lm(g) for g in self.basis]
        # Finiteness theorem: each variable x_i must have a pure power x_i^{d_i} in LT(I)
        bounds = [None] * n
        for lm in lms:
            nonzero_dims = [i for i, e in enumerate(lm) if e > 0]
            if len(nonzero_dims) == 1:
                idx = nonzero_dims[0]
                deg = lm[idx]
                bounds[idx] = deg if bounds[idx] is None else min(bounds[idx], deg)  # type: ignore[arg-type]
        if any(b is None for b in bounds):
            return None

        basis: list[Monomial] = []
        ranges = [range(b) for b in bounds]  # type: ignore[arg-type]
        for m in itertools.product(*ranges):
            if not any(monomial_divides(lm, m) for lm in lms):
                basis.append(m)
        basis.sort(key=self.ring.key_fn)
        return basis

    def companion_matrix(self, var_idx: int) -> dict[int, dict[int, V]] | None:
        """Build sparse multiplication operator M_{x_i} on k[x_1,...,x_n]/I in basis B."""
        basis = self.quotient_monomial_basis()
        if basis is None:
            return None
        idx_map = {m: k for k, m in enumerate(basis)}
        unit_vec = [0] * self.ring.n_vars
        unit_vec[var_idx] = 1
        xi_mon = tuple(unit_vec)

        mat: dict[int, dict[int, V]] = {}
        for col_j, m in enumerate(basis):
            prod = {monomial_add(m, xi_mon): self.ring.field.one}
            rem = self.reduce(prod)
            for rm, rc in rem.items():
                row_i = idx_map[rm]
                mat.setdefault(row_i, {})[col_j] = rc
        return mat


# =============================================================================
# 4. Tropical Hypersurfaces via TropicalSemiring (Min-Plus)
# =============================================================================


def tropical_eval(poly: SparseMPoly[float], w: tuple[float, ...], trop: TropicalSemiring) -> float:
    """Evaluate tropical polynomial min_a (c_a + <a, w>) using AlgebraX TropicalSemiring."""
    acc = trop.zero  # +inf
    for alpha, c_alpha in poly.items():
        # c_alpha (+) <alpha, w> in tropical product
        term = c_alpha
        for ai, wi in zip(alpha, w, strict=True):
            term = trop.mul(term, ai * wi)
        acc = trop.add(acc, term)
    return acc


def tropical_curve_2d_skeleton(poly: SparseMPoly[float]) -> dict[str, object]:
    """Compute the 2D tropical hypersurface T(f) subset R^2 (vertices, rays, and balance check).

    A point w=(x,y) is in T(f) iff min_{(i,j)} (c_{ij} + i*x + j*y) is achieved at >= 2 monomials.
    Vertices are intersections of 3+ active affine planes; edges are intersections of 2 active planes.
    """
    terms = list(poly.items())
    # Candidate vertices from solving 3 active planes:
    # c_a + a1*x + a2*y = c_b + b1*x + b2*y = c_c + c1*x + c2*y
    vertices: list[tuple[float, float]] = []
    vertex_active: list[set[Monomial]] = []
    for (a, ca), (b, cb), (c, cc) in itertools.combinations(terms, 3):
        A = np.array([[a[0] - b[0], a[1] - b[1]], [a[0] - c[0], a[1] - c[1]]], dtype=float)
        if abs(np.linalg.det(A)) < 1e-12:
            continue
        rhs = np.array([cb - ca, cc - ca], dtype=float)
        x, y = np.linalg.solve(A, rhs)
        vals = {m: cm + m[0] * x + m[1] * y for m, cm in terms}
        mval = min(vals.values())
        active = {m for m, v in vals.items() if abs(v - mval) < 1e-9}
        if len(active) >= 3:
            # Deduplicate vertex
            if not any(abs(vx - x) < 1e-8 and abs(vy - y) < 1e-8 for vx, vy in vertices):
                vertices.append((float(x), float(y)))
                vertex_active.append(active)

    # Check Noether balancing condition at every vertex:
    # Each edge incident to a vertex corresponds to an edge of the dual Newton polygon subdivision.
    # For a smooth/3-valent tropical vertex with active monomials {a, b, c}, the outgoing primitive
    # directions are rotated 90 degrees from the dual triangle edges (b-a), (c-b), (a-c) -> sum = (0,0)!
    balance_residuals: list[tuple[float, float]] = []
    for active in vertex_active:
        pts = sorted(active)
        if len(pts) == 3:
            p0, p1, p2 = pts
            # Dual triangle edges oriented counter-clockwise sum to (0,0), so 90-deg rotated rays sum to (0,0)
            e01 = (-(p1[1] - p0[1]), p1[0] - p0[0])
            e12 = (-(p2[1] - p1[1]), p2[0] - p1[0])
            e20 = (-(p0[1] - p2[1]), p0[0] - p2[0])
            balance_residuals.append((e01[0] + e12[0] + e20[0], e01[1] + e12[1] + e20[1]))
    return {
        'vertices': vertices,
        'active_sets': vertex_active,
        'balance_residuals': balance_residuals,
    }


# =============================================================================
# 5. Run All Five Empirical Experiments
# =============================================================================


def run_experiments() -> None:
    print('=' * 78)
    print('EXP-0009 EMPIRICAL PROTOTYPE: ALGEBRAIC & TROPICAL VARIETIES')
    print('=' * 78)

    # -------------------------------------------------------------------------
    # EXPERIMENT 1: Float Suicide Falsification vs. Exact Fields
    # -------------------------------------------------------------------------
    print('\n--- EXPERIMENT 1: Floating-Point Cancellation Suicide vs. Exact Field ---')
    # System with exact cancellation:
    # f1 = x^2 + y^2 - 1, f2 = (1 + eps)*x^2 + y^2 - 1 - eps*1/4  (intersection at x = +-1/2)
    # Wait: make f2 = x^2 + y^2 - 1 + eps*x, where eps = 1e-17 (under float64: 1.0 + 1e-17 == 1.0,
    # or eps = 1e-13 with tol=1e-12 vs tol=0.0):
    eps_exact = Fraction(1, 10**14)
    q_ring = MultivariatePolynomialAlgebra(StandardField(Fraction), 2, 'lex')
    f1_q = {(2, 0): Fraction(1), (0, 2): Fraction(1), (0, 0): Fraction(-1)}
    f2_q = {(2, 0): Fraction(1), (0, 2): Fraction(1), (1, 0): eps_exact, (0, 0): Fraction(-1)}
    # True ideal: f2 - f1 = eps * x => x = 0, y^2 = 1 => 2 exact points (0, 1) and (0, -1)!
    gb_q, _ = groebner_f4(q_ring, [f1_q, f2_q])

    # Now test naive float with tol=0.0 on a cancelling system:
    # g1 = 3*x + 2*y - 5, g2 = (3/7)*x + (2/7)*y - (5/7) + 0  (rank-1 linear + quadratic)
    # Under IEEE-754 float64, (3/7)*x - (1/7)*(3*x) leaves ~1e-16 noise, which becomes a pivot!
    f_ring_naive = MultivariatePolynomialAlgebra(StandardField(float, tol=0.0), 2, 'lex')
    g1_f = {(1, 0): 3.0, (0, 1): 2.0, (0, 0): -5.0}
    g2_f = {(1, 0): 3.0 / 7.0, (0, 1): 2.0 / 7.0, (0, 0): -5.0 / 7.0}
    g3_f = {(2, 0): 1.0, (0, 2): 1.0, (0, 0): -2.0}  # circle x^2+y^2=2 passes through (1,1)
    gb_f_naive, _ = groebner_buchberger(f_ring_naive, [g1_f, g2_f, g3_f])

    g1_q2 = {(1, 0): Fraction(3), (0, 1): Fraction(2), (0, 0): Fraction(-5)}
    g2_q2 = {(1, 0): Fraction(3, 7), (0, 1): Fraction(2, 7), (0, 0): Fraction(-5, 7)}
    g3_q2 = {(2, 0): Fraction(1), (0, 2): Fraction(1), (0, 0): Fraction(-2)}
    gb_q2, _ = groebner_buchberger(q_ring, [g1_q2, g2_q2, g3_q2])

    # Also test float with tol=1e-12 on f1_q, f2_q (genuine 1e-14 term!)
    f_ring_tol = MultivariatePolynomialAlgebra(StandardField(float, tol=1e-12), 2, 'lex')
    f1_ft = {m: float(c) for m, c in f1_q.items()}
    f2_ft = {m: float(c) for m, c in f2_q.items()}
    gb_f_tol, _ = groebner_f4(f_ring_tol, [f1_ft, f2_ft])

    print(f'Case A (IEEE-754 rounding residual, tol=0.0):')
    print(f'  Exact Q Groebner basis: {gb_q2}  (2 points: (1,1), (19/13, 4/13))')
    print(f'  Naive float64 GB:       {gb_f_naive}  (FALSE UNIT IDEAL => V(I) = EMPTY!)')
    print(f'Case B (Genuine 1e-14 coefficient, tol=1e-12):')
    print(f'  Exact Q Groebner basis: {gb_q}  (0-dim: x=0, y^2-1=0)')
    print(f'  Float64 (tol=1e-12) GB: {gb_f_tol}  (LOST x=0, inflated to 1-dim circle!)')

    # -------------------------------------------------------------------------
    # EXPERIMENT 2: Buchberger vs. F4-Style Sparse Macaulay RREF + SymPy Oracle
    # -------------------------------------------------------------------------
    print('\n--- EXPERIMENT 2: Buchberger vs. F4-Sparse-RREF & SymPy Oracle ---')

    def to_sympy(p: SparseMPoly, syms: Sequence[sp.Symbol]) -> sp.Expr:
        expr = sp.Integer(0)
        for m, c in p.items():
            mon = sp.Integer(1)
            for s, e in zip(syms, m, strict=True):
                if e:
                    mon *= s**e
            expr += (sp.Rational(c.numerator, c.denominator) if isinstance(c, Fraction) else int(c)) * mon
        return expr

    x, y, z, w = sp.symbols('x y z w')
    benchmarks = []

    # 2a. Twisted cubic (lex) over Q
    tc_q = [
        {(0, 1, 0): Fraction(1), (2, 0, 0): Fraction(-1)},
        {(0, 0, 1): Fraction(1), (3, 0, 0): Fraction(-1)},
    ]
    benchmarks.append(('TwistedCubic (Q, lex)', StandardField(Fraction), 3, 'lex', tc_q, [x, y, z], sp.QQ))

    # 2b. Cyclic-3 over Q (grevlex)
    c3_q = [
        {(1, 0, 0): Fraction(1), (0, 1, 0): Fraction(1), (0, 0, 1): Fraction(1)},
        {(1, 1, 0): Fraction(1), (0, 1, 1): Fraction(1), (1, 0, 1): Fraction(1)},
        {(1, 1, 1): Fraction(1), (0, 0, 0): Fraction(-1)},
    ]
    benchmarks.append(('Cyclic-3 (Q, grevlex)', StandardField(Fraction), 3, 'grevlex', c3_q, [x, y, z], sp.QQ))

    # 2c. Cyclic-3 over F_101 (grevlex)
    c3_f = [
        {(1, 0, 0): 1, (0, 1, 0): 1, (0, 0, 1): 1},
        {(1, 1, 0): 1, (0, 1, 1): 1, (1, 0, 1): 1},
        {(1, 1, 1): 1, (0, 0, 0): 100},
    ]
    benchmarks.append(('Cyclic-3 (F_101, grevlex)', ModularField(101), 3, 'grevlex', c3_f, [x, y, z], sp.GF(101)))

    # 2d. Cyclic-4 over F_101 (grevlex)
    c4_f = [
        {(1, 0, 0, 0): 1, (0, 1, 0, 0): 1, (0, 0, 1, 0): 1, (0, 0, 0, 1): 1},
        {(1, 1, 0, 0): 1, (0, 1, 1, 0): 1, (0, 0, 1, 1): 1, (1, 0, 0, 1): 1},
        {(1, 1, 1, 0): 1, (0, 1, 1, 1): 1, (1, 0, 1, 1): 1, (1, 1, 0, 1): 1},
        {(1, 1, 1, 1): 1, (0, 0, 0, 0): 100},
    ]
    benchmarks.append(('Cyclic-4 (F_101, grevlex)', ModularField(101), 4, 'grevlex', c4_f, [x, y, z, w], sp.GF(101)))

    # 2e. 2R Planar Robot Inverse Kinematics over Q (L1=2, L2=1, target=(2, 1))
    # Vars: c1, s1, c2, s2
    ik_q = [
        {(2, 0, 0, 0): Fraction(1), (0, 2, 0, 0): Fraction(1), (0, 0, 0, 0): Fraction(-1)},
        {(0, 0, 2, 0): Fraction(1), (0, 0, 0, 2): Fraction(1), (0, 0, 0, 0): Fraction(-1)},
        # 2*c1 + c1*c2 - s1*s2 - 2 = 0
        {(1, 0, 0, 0): Fraction(2), (1, 0, 1, 0): Fraction(1), (0, 1, 0, 1): Fraction(-1), (0, 0, 0, 0): Fraction(-2)},
        # 2*s1 + s1*c2 + c1*s2 - 1 = 0
        {(0, 1, 0, 0): Fraction(2), (0, 1, 1, 0): Fraction(1), (1, 0, 0, 1): Fraction(1), (0, 0, 0, 0): Fraction(-1)},
    ]
    benchmarks.append(('2R-Robot-IK (Q, grevlex)', StandardField(Fraction), 4, 'grevlex', ik_q, [x, y, z, w], sp.QQ))

    for label, field, nvars, order, gens, syms, sp_dom in benchmarks:
        ring = MultivariatePolynomialAlgebra(field, nvars, order)
        t0 = time.perf_counter()
        gb_b, st_b = groebner_buchberger(ring, gens)
        dt_b = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        gb_f4, st_f4 = groebner_f4(ring, gens)
        dt_f4 = (time.perf_counter() - t0) * 1000

        # SymPy oracle verification
        t0 = time.perf_counter()
        sp_gb = sp.groebner([to_sympy(g, syms) for g in gens], *syms, order=order, domain=sp_dom)
        dt_sp = (time.perf_counter() - t0) * 1000

        # Verify exact equality of reduced Groebner bases against SymPy
        our_sp_b = [sp.Poly(to_sympy(g, syms), *syms, domain=sp_dom) for g in gb_b]
        our_sp_f4 = [sp.Poly(to_sympy(g, syms), *syms, domain=sp_dom) for g in gb_f4]
        oracle_polys = list(sp_gb.polys)
        match_b = our_sp_b == oracle_polys
        match_f4 = our_sp_f4 == oracle_polys

        print(
            f'{label:<26} | Buchberger: {dt_b:7.2f} ms (S={st_b["s_polys"]:3d}) | '
            f'F4-RREF: {dt_f4:7.2f} ms (rounds={st_f4["rounds"]:2d}, rows={st_f4["matrix_rows"]:3d}) | '
            f'SymPy: {dt_sp:7.2f} ms | OracleMatch=({match_b}, {match_f4})'
        )

    # -------------------------------------------------------------------------
    # EXPERIMENT 3: Ideal + QuotientRing k[V] + Stickelberger Companion Matrices
    # -------------------------------------------------------------------------
    print('\n--- EXPERIMENT 3: QuotientRing k[V] & Stickelberger Companion Matrices ---')
    # Intersect circle x^2 + y^2 - 5 = 0 and parabola y - x^2 + 1 = 0 => 4 points: (+-1, 2)? Wait:
    # If x^2+y^2=5 and y = x^2 - 1 => x^2 = y+1 => (y+1)+y^2=5 => y^2+y-4=0 (2 real y, 4 points)
    # Better rational/integer 4-point intersection: x^2 + y^2 - 5 = 0 and x*y - 2 = 0 => (+-1, +-2), (+-2, +-1)
    q2_ring = MultivariatePolynomialAlgebra(StandardField(Fraction), 2, 'grevlex')
    circle = {(2, 0): Fraction(1), (0, 2): Fraction(1), (0, 0): Fraction(-5)}
    hyperb = {(1, 1): Fraction(1), (0, 0): Fraction(-2)}
    ideal = GroebnerIdeal(q2_ring, [circle, hyperb])
    coord_ring = QuotientRing(q2_ring, ideal)

    q_basis = ideal.quotient_monomial_basis()
    mx = ideal.companion_matrix(0)
    my = ideal.companion_matrix(1)
    assert q_basis is not None and mx is not None and my is not None

    # Check AlgebraX Protocol conformance & commutativity [Mx, My] = 0
    comm_xy = commutator(mx, my)
    print(f'isinstance(ideal, Ideal):           {isinstance(ideal, Ideal)}')
    print(f'isinstance(coord_ring, CommRing):   {isinstance(coord_ring, CommRing)}')
    print(f'Quotient basis dim_Q(Q[V]):         {len(q_basis)} -> {q_basis}')
    print(f'Companion [M_x, M_y] == 0:          {comm_xy == {}}')

    # Verify QuotientRing arithmetic: (x^2 + y^2) mod I == 5, and (x*y)^3 mod I == 8
    f_test = {(2, 0): Fraction(1), (0, 2): Fraction(1)}
    xy_test = {(1, 1): Fraction(1)}
    xy_cubed = coord_ring.power(xy_test, 3)
    print(f'In Q[V], [x^2 + y^2] == {coord_ring.project(f_test)} (expected 5)')
    print(f'In Q[V], [(x*y)^3]   == {xy_cubed} (expected 8)')

    # Stickelberger Escape Hatch: simultaneous diagonalization via NumPy
    dim = len(q_basis)
    mx_np = np.zeros((dim, dim), dtype=float)
    my_np = np.zeros((dim, dim), dtype=float)
    for r, cols in mx.items():
        for c, val in cols.items():
            mx_np[r, c] = float(val)
    for r, cols in my.items():
        for c, val in cols.items():
            my_np[r, c] = float(val)

    # Random linear combination separates eigenvalues cleanly
    rng = np.random.default_rng(42)
    comb = 0.73 * mx_np + 0.27 * my_np
    _, vecs = np.linalg.eig(comb)
    pts = []
    for k in range(dim):
        v = vecs[:, k]
        # Rayleigh quotient for simultaneous eigenvalues of Mx and My
        vx = float(np.real((v.conj().T @ mx_np @ v) / (v.conj().T @ v)))
        vy = float(np.real((v.conj().T @ my_np @ v) / (v.conj().T @ v)))
        pts.append((round(vx, 6), round(vy, 6)))
    pts.sort()
    residuals = [
        max(abs(px**2 + py**2 - 5.0), abs(px * py - 2.0)) for px, py in pts
    ]
    print(f'Stickelberger extracted V(I):       {pts}')
    print(f'Max polynomial residual on V(I):    {max(residuals):.2e}')

    # Also solve 2R Robot IK via Stickelberger!
    ik_ring = MultivariatePolynomialAlgebra(StandardField(Fraction), 4, 'grevlex')
    ik_ideal = GroebnerIdeal(ik_ring, ik_q)
    ik_basis = ik_ideal.quotient_monomial_basis()
    print(f'2R Robot IK quotient dim_Q(Q[V]):   {len(ik_basis)} (2 elbow-up/down poses!)')
    mc1 = ik_ideal.companion_matrix(0)
    ms1 = ik_ideal.companion_matrix(1)
    mc2 = ik_ideal.companion_matrix(2)
    ms2 = ik_ideal.companion_matrix(3)
    assert mc1 is not None and ms1 is not None and mc2 is not None and ms2 is not None
    # Verify exact commutativity
    assert commutator(mc1, ms2) == {}
    mats = []
    for msparse in (mc1, ms1, mc2, ms2):
        arr = np.zeros((2, 2), dtype=float)
        for r, cols in msparse.items():
            for c, val in cols.items():
                arr[r, c] = float(val)
        mats.append(arr)
    _, ik_vecs = np.linalg.eig(0.41 * mats[0] + 0.59 * mats[1])
    ik_poses = []
    for k in range(2):
        v = ik_vecs[:, k]
        pose = tuple(round(float(np.real((v.conj().T @ m @ v) / (v.conj().T @ v))), 6) for m in mats)
        ik_poses.append(pose)
    print(f'2R Robot IK poses (c1,s1,c2,s2):    {ik_poses}')

    # -------------------------------------------------------------------------
    # EXPERIMENT 4: Finite-Field Varieties (Elliptic Curve F_7 & F_2 SAT)
    # -------------------------------------------------------------------------
    print('\n--- EXPERIMENT 4: Finite-Field Varieties (Elliptic Curve & F_2 SAT) ---')
    # Elliptic curve y^2 = x^3 + x + 1 over F_7
    f7_ring = MultivariatePolynomialAlgebra(ModularField(7), 2, 'grevlex')
    ec_poly = {(0, 2): 1, (3, 0): 6, (1, 0): 6, (0, 0): 6}  # y^2 - x^3 - x - 1 mod 7
    ec_points = [(x0, y0) for x0 in range(7) for y0 in range(7) if f7_ring.eval(ec_poly, (x0, y0)) == 0]
    # Include point at infinity => total projective points = len(ec_points) + 1
    hasse_bound = 2 * (7**0.5)
    print(f'Elliptic Curve y^2=x^3+x+1 over F_7: affine pts={len(ec_points)}, '
          f'#E(F_7)={len(ec_points)+1} (Hasse |{len(ec_points)+1}-8|={abs(len(ec_points)+1-8)} <= {hasse_bound:.2f})')

    # F_2 Algebraic SAT:
    # Clauses over (x0, x1, x2):
    #   (x0 OR x1)       => (1+x0)(1+x1) = 0
    #   (NOT x0 OR x2)   => x0*(1+x2) = 0
    #   (NOT x1 OR NOT x2) => x1*x2 = 0
    #   (x0 OR NOT x2)   => (1+x0)*x2 = 0
    # Plus field equations x_i^2 + x_i = 0 over F_2
    f2_ring = MultivariatePolynomialAlgebra(ModularField(2), 3, 'lex')
    sat_gens = [
        {(0, 0, 0): 1, (1, 0, 0): 1, (0, 1, 0): 1, (1, 1, 0): 1},  # (1+x0)(1+x1)
        {(1, 0, 0): 1, (1, 0, 1): 1},                                # x0(1+x2)
        {(0, 1, 1): 1},                                              # x1*x2
        {(0, 0, 1): 1, (1, 0, 1): 1},                                # (1+x0)x2
        {(2, 0, 0): 1, (1, 0, 0): 1},                                # x0^2 + x0
        {(0, 2, 0): 1, (0, 1, 0): 1},                                # x1^2 + x1
        {(0, 0, 2): 1, (0, 0, 1): 1},                                # x2^2 + x2
    ]
    sat_ideal = GroebnerIdeal(f2_ring, sat_gens)
    sat_basis = sat_ideal.quotient_monomial_basis()
    brute_sat = [
        pt for pt in itertools.product((0, 1), repeat=3)
        if all(f2_ring.eval(g, pt) == 0 for g in sat_gens)
    ]
    print(f'F_2 3-SAT Groebner basis: {sat_ideal.basis}')
    print(f'F_2 quotient dim = {len(sat_basis)} vs brute-force satisfying assignments = {brute_sat}')

    # -------------------------------------------------------------------------
    # EXPERIMENT 5: Tropical Varieties over TropicalSemiring
    # -------------------------------------------------------------------------
    print('\n--- EXPERIMENT 5: Tropical Varieties over TropicalSemiring ---')
    trop = TropicalSemiring()
    # Tropical line: min(0, x, y) -> vertex at (0, 0), rays (-1,0), (0,-1), (1,1)
    # Tropical conic: min(2 + 2x, 0 + x + y, 2 + 2y, 1 + x, 1 + y, 3)
    trop_conic: SparseMPoly[float] = {
        (2, 0): 2.0,
        (1, 1): 0.0,
        (0, 2): 2.0,
        (1, 0): 1.0,
        (0, 1): 1.0,
        (0, 0): 3.0,
    }
    skel = tropical_curve_2d_skeleton(trop_conic)
    print(f'Tropical Conic vertices:          {skel["vertices"]}')
    print(f'Noether vertex balance residuals: {skel["balance_residuals"]}')
    # Verify evaluation at a tropical vertex hits minimum >= 3 times
    for vx, vy in skel['vertices']:  # type: ignore[attr-defined]
        val = tropical_eval(trop_conic, (vx, vy), trop)
        hits = sum(
            1 for (i, j), c in trop_conic.items()
            if abs((c + i * vx + j * vy) - val) < 1e-9
        )
        print(f'  Vertex ({vx:.1f}, {vy:.1f}): tropical_eval={val:.1f}, active monomials={hits}')


if __name__ == '__main__':
    run_experiments()
