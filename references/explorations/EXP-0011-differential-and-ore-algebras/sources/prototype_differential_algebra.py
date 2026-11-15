"""Executable Prototype & Empirical Benchmark Suite for EXP-0011: Differential & Ore Algebras.

Validates nine foundational pillars of Differential & Ore Algebra in AlgebraX:
1. Experiment 1: Unboxed Non-Commutative Weyl Algebra A_n(k) ([d_i, x_j] = delta_{ij}) & Heisenberg Commutators.
2. Experiment 2: Unified Ore Skew-Polynomial Algebra R[D; sigma, delta] (ODEs, Shifts, q-Difference) & D-Finite
   Closure (LCLM / GCRD).
3. Experiment 3: Exact Hermite Reduction & Rational Integration over StandardField(Fraction) vs. SymPy Oracle.
4. Experiment 4: Exact Arbitrary-Order Taylor Jet Algebra k[x]/<x^{r+1}> & Algebraic Nonlinear ODE Solver
   (Riccati y' = 1 + y^2).
5. Experiment 5: Non-Commutative Left Grobner Reduction & Creative Annihilators in the Weyl Algebra A_1(Q).
6. Experiment 6: Difference Ore Algebra (Delta = S - 1), Gosper Summation & Frobenius Indicial Equations.
7. Experiment 7: Multivariate Taylor Jets k[x,y]/m^4, Characteristic Varieties & Kahler 1-Forms.
8. Experiment 8: Differential Galois Theory — Symmetric Powers Sym^k(L), Wronskian Abel Identity,
   Kovacic Case 1 Factorization & Non-Liouvillian SL_2 Obstruction Proofs.
9. Experiment 9: DifferentialPolynomialRing k{u} & Euler-Lagrange Complex, Rota-Baxter Identities,
   Differential Newton Polygons & D-Finite Pade Guessing.
10. Experiment 10: Algebraic Hamiltonian Mechanics — CanonicalPoissonAlgebra, Hamiltonian Derivations X_H,
    Algebraic Legendre Transform (L <-> H), Weyl-Poisson Ehrenfest Correspondence & Exact Symplectic Jets.
11. Experiment 11: Algebraic de Rham / Kahler Exterior Complex — Graded Wedge Product, Exterior Derivative d_k,
    Interior Product i_X, Cartan Magic Formula (L_X = d i_X + i_X d), Symplectic Cartan-Liouville & Poincare Homotopy.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from fractions import Fraction
from typing import Generic, TypeVar

import sympy as sp

from algebrax.algebra import (
    Field,
    PolynomialAlgebra,
    PolynomialTruncationIdeal,
    QuotientRing,
    StandardField,
)

V = TypeVar("V")
Monomial = tuple[int, ...]
# WeylMonomial = (x_exponents, d_exponents), e.g. ((2, 0), (0, 1)) represents x_0^2 * d_1
WeylMonomial = tuple[Monomial, Monomial]
WeylPoly = dict[WeylMonomial, V]
UniPoly = dict[int, Fraction]


# =============================================================================
# Core Exact Univariate Rational Polynomial Helpers (Fraction Field)
# =============================================================================


def poly_clean(p: dict[int, Fraction]) -> UniPoly:
    return {k: v for k, v in p.items() if v != 0}


def poly_deg(p: UniPoly) -> int:
    return max(p.keys()) if p else -1


def poly_add(a: UniPoly, b: UniPoly) -> UniPoly:
    out = dict(a)
    for k, v in b.items():
        nv = out.get(k, Fraction(0)) + v
        if nv == 0:
            out.pop(k, None)
        else:
            out[k] = nv
    return out


def poly_sub(a: UniPoly, b: UniPoly) -> UniPoly:
    out = dict(a)
    for k, v in b.items():
        nv = out.get(k, Fraction(0)) - v
        if nv == 0:
            out.pop(k, None)
        else:
            out[k] = nv
    return out


def poly_mul(a: UniPoly, b: UniPoly) -> UniPoly:
    out: dict[int, Fraction] = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            k = ka + kb
            out[k] = out.get(k, Fraction(0)) + va * vb
    return poly_clean(out)


def poly_diff(p: UniPoly) -> UniPoly:
    return {k - 1: k * v for k, v in p.items() if k > 0}


def poly_shift_plus_one(p: UniPoly) -> UniPoly:
    """Apply shift sigma(p(n)) = p(n + 1) via binomial expansion."""
    out: UniPoly = {}
    for deg, coeff in p.items():
        for j in range(deg + 1):
            term = coeff * Fraction(math.comb(deg, j))
            out[j] = out.get(j, Fraction(0)) + term
    return poly_clean(out)


def poly_q_dilate(p: UniPoly, q: Fraction) -> UniPoly:
    """Apply q-dilation sigma(p(x)) = p(q * x)."""
    return {k: v * (q ** k) for k, v in p.items() if v != 0}


def poly_divmod(a: UniPoly, b: UniPoly) -> tuple[UniPoly, UniPoly]:
    if not b:
        raise ZeroDivisionError("Division by zero polynomial.")
    rem = dict(a)
    quot: dict[int, Fraction] = {}
    db = poly_deg(b)
    lcb = b[db]
    while rem and poly_deg(rem) >= db:
        dr = poly_deg(rem)
        shift = dr - db
        fac = rem[dr] / lcb
        quot[shift] = quot.get(shift, Fraction(0)) + fac
        for k, v in b.items():
            tk = k + shift
            nv = rem.get(tk, Fraction(0)) - fac * v
            if nv == 0:
                rem.pop(tk, None)
            else:
                rem[tk] = nv
    return poly_clean(quot), poly_clean(rem)


def poly_make_monic(p: UniPoly) -> UniPoly:
    if not p:
        return {}
    lc = p[poly_deg(p)]
    return {k: v / lc for k, v in p.items()}


def poly_xgcd(a: UniPoly, b: UniPoly) -> tuple[UniPoly, UniPoly, UniPoly]:
    """Extended Euclidean algorithm returning monic (g, s, t) with s*a + t*b == g."""
    old_r, r = dict(a), dict(b)
    old_s, s = {0: Fraction(1)}, {}
    old_t, t = {}, {0: Fraction(1)}
    while r:
        q, rem = poly_divmod(old_r, r)
        old_r, r = r, rem
        old_s, s = s, poly_sub(old_s, poly_mul(q, s))
        old_t, t = t, poly_sub(old_t, poly_mul(q, t))
    if not old_r:
        return {}, {}, {}
    lc = old_r[poly_deg(old_r)]
    return (
        {k: v / lc for k, v in old_r.items()},
        {k: v / lc for k, v in old_s.items()},
        {k: v / lc for k, v in old_t.items()},
    )


def poly_eval(p: UniPoly, x: Fraction) -> Fraction:
    acc = Fraction(0)
    for k, v in p.items():
        acc += v * (x ** k)
    return acc


def poly_to_sympy(p: UniPoly, var: sp.Symbol) -> sp.Expr:
    return sum((sp.Rational(v.numerator, v.denominator) * var ** k for k, v in p.items()), sp.Integer(0))


# =============================================================================
# Experiment 1: Non-Commutative Weyl Algebra A_n(k) ([d_i, x_j] = delta_{ij})
# =============================================================================


class WeylAlgebra(Generic[V]):
    """Normal-ordered Weyl Algebra A_n(k) = k<x_1,...,x_n, d_1,...,d_n> / <[d_i, x_j] - delta_{ij}>.

    Carrier: dict[tuple[Monomial, Monomial], V] representing sum c_{a,b} x^a d^b.
    """

    def __init__(self, field: Field[V], n_vars: int) -> None:
        self.field = field
        self.n_vars = n_vars

    @property
    def zero(self) -> WeylPoly[V]:
        return {}

    @property
    def one(self) -> WeylPoly[V]:
        z = (0,) * self.n_vars
        return {(z, z): self.field.one}

    def x(self, i: int) -> WeylPoly[V]:
        ax = tuple(1 if idx == i else 0 for idx in range(self.n_vars))
        zd = (0,) * self.n_vars
        return {(ax, zd): self.field.one}

    def d(self, i: int) -> WeylPoly[V]:
        zx = (0,) * self.n_vars
        bd = tuple(1 if idx == i else 0 for idx in range(self.n_vars))
        return {(zx, bd): self.field.one}

    def add(self, p: WeylPoly[V], q: WeylPoly[V]) -> WeylPoly[V]:
        out = dict(p)
        for k, v in q.items():
            nv = self.field.add(out.get(k, self.field.zero), v)
            if self.field.is_zero(nv):
                out.pop(k, None)
            else:
                out[k] = nv
        return out

    def sub(self, p: WeylPoly[V], q: WeylPoly[V]) -> WeylPoly[V]:
        out = dict(p)
        for k, v in q.items():
            nv = self.field.sub(out.get(k, self.field.zero), v)
            if self.field.is_zero(nv):
                out.pop(k, None)
            else:
                out[k] = nv
        return out

    def mul(self, p: WeylPoly[V], q: WeylPoly[V]) -> WeylPoly[V]:
        """Normal-ordered Leibniz Weyl multiplication:
        (x^a d^b) * (x^u d^v) = sum_{k <= min(b, u)} binom(b,k)*binom(u,k)*k! x^{a+u-k} d^{b+v-k}.
        """
        out: WeylPoly[V] = {}
        for (ax, bd), cp in p.items():
            for (ux, vd), cq in q.items():
                base_c = self.field.mul(cp, cq)
                if self.field.is_zero(base_c):
                    continue
                # Expand per coordinate
                terms: list[tuple[list[int], list[int], int]] = [([0] * self.n_vars, [0] * self.n_vars, 1)]
                for idx in range(self.n_vars):
                    b_i, u_i = bd[idx], ux[idx]
                    a_i, v_i = ax[idx], vd[idx]
                    next_terms: list[tuple[list[int], list[int], int]] = []
                    for k in range(min(b_i, u_i) + 1):
                        mult = math.comb(b_i, k) * math.comb(u_i, k) * math.factorial(k)
                        nx = a_i + u_i - k
                        nd = b_i + v_i - k
                        for px, pd, pm in terms:
                            cx = list(px)
                            cd = list(pd)
                            cx[idx] = nx
                            cd[idx] = nd
                            next_terms.append((cx, cd, pm * mult))
                    terms = next_terms

                for tx, td, mult in terms:
                    key = (tuple(tx), tuple(td))
                    # Convert integer combinatorial factor into field element
                    f_mult = self.field.zero
                    for _ in range(mult):
                        f_mult = self.field.add(f_mult, self.field.one)
                    contrib = self.field.mul(base_c, f_mult)
                    nv = self.field.add(out.get(key, self.field.zero), contrib)
                    if self.field.is_zero(nv):
                        out.pop(key, None)
                    else:
                        out[key] = nv
        return out

    def commutator(self, p: WeylPoly[V], q: WeylPoly[V]) -> WeylPoly[V]:
        return self.sub(self.mul(p, q), self.mul(q, p))

    def apply_to_poly(self, op: WeylPoly[V], state: dict[Monomial, V]) -> dict[Monomial, V]:
        """Apply differential operator L to commutative polynomial f(x) in k[x_1, ..., x_n]."""
        out: dict[Monomial, V] = {}
        for (ax, bd), c_op in op.items():
            for mx, c_st in state.items():
                # Differentiate x^mx by d^bd
                if any(mx[i] < bd[i] for i in range(self.n_vars)):
                    continue
                fall_fact = 1
                new_exp: list[int] = []
                for i in range(self.n_vars):
                    m_i, b_i, a_i = mx[i], bd[i], ax[i]
                    for j in range(b_i):
                        fall_fact *= m_i - j
                    new_exp.append(m_i - b_i + a_i)
                f_fact = self.field.zero
                for _ in range(fall_fact):
                    f_fact = self.field.add(f_fact, self.field.one)
                val = self.field.mul(self.field.mul(c_op, c_st), f_fact)
                k = tuple(new_exp)
                nv = self.field.add(out.get(k, self.field.zero), val)
                if self.field.is_zero(nv):
                    out.pop(k, None)
                else:
                    out[k] = nv
        return out


def run_experiment_1() -> None:
    print("=" * 80)
    print("EXPERIMENT 1: NON-COMMUTATIVE WEYL ALGEBRA A_n(Q) & HEISENBERG COMMUTATION")
    print("=" * 80)
    field = StandardField(Fraction)
    weyl = WeylAlgebra(field, n_vars=2)
    x0, d0 = weyl.x(0), weyl.d(0)
    x1, d1 = weyl.x(1), weyl.d(1)

    comm_00 = weyl.commutator(d0, x0)
    comm_01 = weyl.commutator(d0, x1)
    print(f"[d_0, x_0] == 1: {comm_00 == weyl.one}")
    print(f"[d_0, x_1] == 0: {comm_01 == weyl.zero}")

    # Ladder / Creation-Annihilation operators: a = d_0 + x_0, a_dag = -d_0 + x_0 -> [a, a_dag] = 2
    a = weyl.add(d0, x0)
    a_dag = weyl.sub(x0, d0)
    print(f"[d + x, x - d] == 2: {weyl.commutator(a, a_dag) == weyl.add(weyl.one, weyl.one)}")

    # Verify Weyl associativity on nontrivial degree-3 operators: (L1 * L2) * L3 == L1 * (L2 * L3)
    l1 = weyl.add(weyl.mul(d0, d0), x0)
    l2 = weyl.add(weyl.mul(x0, d1), weyl.one)
    l3 = weyl.sub(d1, weyl.mul(x1, d0))
    assoc_ok = weyl.mul(weyl.mul(l1, l2), l3) == weyl.mul(l1, weyl.mul(l2, l3))
    print(f"Weyl Algebra Associativity (L1*L2)*L3 == L1*(L2*L3): {assoc_ok}")

    # Verify representation axiom: (L1 * L2)(f) == L1(L2(f)) on polynomial f(x0, x1) = 3 x0^2 x1 + x1^2
    f = {(2, 1): Fraction(3), (0, 2): Fraction(1)}
    lhs = weyl.apply_to_poly(weyl.mul(l1, l2), f)
    rhs = weyl.apply_to_poly(l1, weyl.apply_to_poly(l2, f))
    print(f"D-Module Action Homomorphism (L1*L2)(f) == L1(L2(f)): {lhs == rhs}")
    print()


# =============================================================================
# Experiment 2: Unified Ore Skew-Polynomial Algebra R[D; sigma, delta]
# =============================================================================


class OreAlgebra:
    """Ore Skew-Polynomial Ring k(x)[D; sigma, delta] where D * r = sigma(r)*D + delta(r).

    Carrier for an Ore operator: dict[int, tuple[UniPoly, UniPoly]] mapping D^k -> rational function P_k/Q_k.
    For polynomial coefficients over Q[x], carrier simplifies to dict[int, UniPoly].
    """

    def __init__(
            self,
            sigma: Callable[[UniPoly], UniPoly],
            delta: Callable[[UniPoly], UniPoly],
            name: str,
    ) -> None:
        self.sigma = sigma
        self.delta = delta
        self.name = name

    @staticmethod
    def clean(op: dict[int, UniPoly]) -> dict[int, UniPoly]:
        return {k: v for k, v in op.items() if v}

    @staticmethod
    def deg(op: dict[int, UniPoly]) -> int:
        return max(op.keys()) if op else -1

    def add(self, a: dict[int, UniPoly], b: dict[int, UniPoly]) -> dict[int, UniPoly]:
        out = dict(a)
        for k, v in b.items():
            nv = poly_add(out.get(k, {}), v)
            if nv:
                out[k] = nv
            else:
                out.pop(k, None)
        return out

    def sub(self, a: dict[int, UniPoly], b: dict[int, UniPoly]) -> dict[int, UniPoly]:
        out = dict(a)
        for k, v in b.items():
            nv = poly_sub(out.get(k, {}), v)
            if nv:
                out[k] = nv
            else:
                out.pop(k, None)
        return out

    def mul_left_poly(self, p: UniPoly, op: dict[int, UniPoly]) -> dict[int, UniPoly]:
        return self.clean({k: poly_mul(p, v) for k, v in op.items()})

    def mul_d_left(self, op: dict[int, UniPoly]) -> dict[int, UniPoly]:
        """Multiply D * op using D * c = sigma(c)*D + delta(c)."""
        out: dict[int, UniPoly] = {}
        for k, coeff in op.items():
            s_c = self.sigma(coeff)
            d_c = self.delta(coeff)
            if s_c:
                out[k + 1] = poly_add(out.get(k + 1, {}), s_c)
            if d_c:
                out[k] = poly_add(out.get(k, {}), d_c)
        return self.clean(out)

    def mul(self, a: dict[int, UniPoly], b: dict[int, UniPoly]) -> dict[int, UniPoly]:
        """Skew-polynomial multiplication a(D) * b(D)."""
        out: dict[int, UniPoly] = {}
        for deg_a, coeff_a in a.items():
            shifted = dict(b)
            for _ in range(deg_a):
                shifted = self.mul_d_left(shifted)
            out = self.add(out, self.mul_left_poly(coeff_a, shifted))
        return self.clean(out)

    def right_divmod_pseudo(
            self,
            a: dict[int, UniPoly],
            b: dict[int, UniPoly],
    ) -> tuple[dict[int, UniPoly], dict[int, UniPoly], UniPoly]:
        """Pseudo-right division over Q[x][D]: factor * a = q * b + r with deg_D(r) < deg_D(b)."""
        rem = dict(a)
        quot: dict[int, UniPoly] = {}
        factor: UniPoly = {0: Fraction(1)}
        db = self.deg(b)
        lcb = b[db]

        while rem and self.deg(rem) >= db:
            dr = self.deg(rem)
            lcr = rem[dr]
            # Need leading coeff * D^{dr-db} * b to cancel lcr * D^{dr}.
            # Leading coeff of D^{s} * b is sigma^s(lcb).
            s = dr - db
            sig_lcb = lcb
            for _ in range(s):
                sig_lcb = self.sigma(sig_lcb)

            # Scale rem, quot, factor by sig_lcb so division stays in Q[x][D]
            rem = self.mul_left_poly(sig_lcb, rem)
            quot = self.mul_left_poly(sig_lcb, quot)
            factor = poly_mul(sig_lcb, factor)

            term_q = {s: lcr}
            quot = self.add(quot, term_q)
            sub_prod = self.mul(term_q, b)
            rem = self.sub(rem, sub_prod)

        # Normalize primitive part (divide out integer GCD / LC content if needed)
        return quot, rem, factor

    def lclm(self, a: dict[int, UniPoly], b: dict[int, UniPoly]) -> dict[int, UniPoly]:
        """Least Common Left Multiple (LCLM): annihilates f + g when a(f)=0 and b(g)=0!"""
        # Solve linear dependencies among right remainders of D^k * a? Actually simple Ore intersection via linear
        # algebra on D-remainders modulo b, or standard non-commutative extended Euclidean on b:
        # Express D^k = q_k * a + r_k for k=0..deg(a)+deg(b) and find relation over Q(x), OR use direct ansatz.
        # Here we build exact Sylvester-Ore matrix over Q(x) (small order <= 4) via Fraction polynomial evaluation
        # or symbolic!
        # Even simpler and exact: right Euclidean GCRD + cross-relation in Q[x][D] via pseudo-division!
        _da, db = self.deg(a), self.deg(b)
        # Extended right Euclidean in pseudo-polynomial form:
        r0, r1 = dict(a), dict(b)
        u0, u1 = {0: {0: Fraction(1)}}, {}
        v0, v1 = {}, {0: {0: Fraction(1)}}
        while r1:
            q, r2, fac = self.right_divmod_pseudo(r0, r1)
            u2 = self.sub(self.mul_left_poly(fac, u0), self.mul(q, u1))
            v2 = self.sub(self.mul_left_poly(fac, v0), self.mul(q, v1))
            r0, r1 = r1, r2
            u0, u1 = u1, u2
            v0, v1 = v1, v2
        # When r1 == 0, u1 * a + v1 * b == 0, so LCLM = u1 * a = -v1 * b!
        assert self.deg(u1) == db - self.deg(r0)
        return self.mul(u1, a)


def run_experiment_2() -> None:
    print("=" * 80)
    print("EXPERIMENT 2: UNIFIED ORE SKEW-POLYNOMIAL ALGEBRA (ODEs, SHIFTS & q-DILATION)")
    print("=" * 80)

    # 1. Differential Ore Algebra: D = d/dx (sigma = id, delta = poly_diff)
    diff_ore = OreAlgebra(sigma=lambda p: p, delta=poly_diff, name="Differential(Q[x][Dx])")
    # Annihilator of exp(x): Dx - 1; Annihilator of cos(x): Dx^2 + 1
    l_exp = {1: {0: Fraction(1)}, 0: {0: Fraction(-1)}}
    l_cos = {2: {0: Fraction(1)}, 0: {0: Fraction(1)}}
    # D-finite closure: annihilator of f(x) = exp(x) + cos(x) must be LCLM(Dx - 1, Dx^2 + 1) = (Dx^3 - Dx^2 + Dx - 1)
    l_sum = diff_ore.lclm(l_exp, l_cos)
    # Check both l_exp and l_cos right-divide l_sum!
    _, rem1, _ = diff_ore.right_divmod_pseudo(l_sum, l_exp)
    _, rem2, _ = diff_ore.right_divmod_pseudo(l_sum, l_cos)
    print(f"ODE LCLM(Dx - 1, Dx^2 + 1) order={diff_ore.deg(l_sum)}: right-divisible by both={not rem1 and not rem2}")
    # Evaluate on Taylor series of exp(x) + cos(x) up to x^10
    series = {k: Fraction(1, math.factorial(k)) + (
        Fraction((-1) ** (k // 2), math.factorial(k)) if k % 2 == 0 else Fraction(0)) for k in range(12)}

    # Apply l_sum to series up to x^7
    def apply_diff_ore(op: dict[int, UniPoly], f: UniPoly) -> UniPoly:
        out: UniPoly = {}
        for d_ord, c_poly in op.items():
            df = dict(f)
            for _ in range(d_ord):
                df = poly_diff(df)
            out = poly_add(out, poly_mul(c_poly, df))
        return out

    res_series = {k: v for k, v in apply_diff_ore(l_sum, series).items() if k <= 8}
    print(f"LCLM annihilates Taylor series of exp(x)+cos(x) through x^8: {not res_series}")

    # 2. Shift Ore Algebra: S f(n) = f(n+1) (sigma(p) = p(n+1), delta = 0)
    shift_ore = OreAlgebra(sigma=poly_shift_plus_one, delta=lambda _: {}, name="Shift(Q[n][Sn])")
    # Fibonacci: S^2 - S - 1; Sequence n: (n)*S - (n+1)
    l_fib = {2: {0: Fraction(1)}, 1: {0: Fraction(-1)}, 0: {0: Fraction(-1)}}
    l_lin = {1: {1: Fraction(1)}, 0: {0: Fraction(-1), 1: Fraction(-1)}}
    l_fib_plus_n = shift_ore.lclm(l_fib, l_lin)
    _, r_fib, _ = shift_ore.right_divmod_pseudo(l_fib_plus_n, l_fib)
    _, r_lin, _ = shift_ore.right_divmod_pseudo(l_fib_plus_n, l_lin)
    print(f"Shift LCLM(Fib, n) order={shift_ore.deg(l_fib_plus_n)}: right-divisible by both={not r_fib and not r_lin}")
    # Verify sequence a_n = Fib(n) + n satisfies LCLM!
    fibs = [0, 1]
    for _ in range(12):
        fibs.append(fibs[-1] + fibs[-2])
    seq = [Fraction(fibs[n] + n) for n in range(12)]
    max_shift_res = Fraction(0)
    for n in range(7):
        val = Fraction(0)
        for s_ord, c_poly in l_fib_plus_n.items():
            val += poly_eval(c_poly, Fraction(n)) * seq[n + s_ord]
        if abs(val) > max_shift_res:
            max_shift_res = abs(val)
    print(f"Shift LCLM annihilates a_n = Fib(n) + n exactly (max residual={max_shift_res})")

    # 3. q-Difference Ore Algebra: Q_q f(x) = f(q*x) with q = 2
    q_ore = OreAlgebra(sigma=lambda p: poly_q_dilate(p, Fraction(2)), delta=lambda _: {}, name="q-Shift(q=2)")
    # Verify commutation rule: D_q * x = 2*x * D_q
    lhs = q_ore.mul({1: {0: Fraction(1)}}, {0: {1: Fraction(1)}})
    rhs = {1: {1: Fraction(2)}}
    print(f"q-Ore Skew Rule (D_q * x == 2x * D_q): {lhs == rhs}")
    print()


# =============================================================================
# Experiment 3: Exact Rational Integration via Hermite Reduction (Bronstein)
# =============================================================================


def square_free_factors(p: UniPoly) -> list[UniPoly]:
    """Yun's square-free factorization p = prod_{k=1}^m A_k^k for deg(p) > 0."""
    if poly_deg(p) <= 0:
        return []
    p = poly_make_monic(p)
    dp = poly_diff(p)
    g, _, _ = poly_xgcd(p, dp)
    w, _ = poly_divmod(p, g)
    y, _ = poly_divmod(dp, g)
    z = poly_sub(y, poly_diff(w))
    factors: list[UniPoly] = []
    while poly_deg(w) > 0:
        a_i, _, _ = poly_xgcd(w, z)
        factors.append(a_i)
        w, _ = poly_divmod(w, a_i)
        if poly_deg(w) == 0:
            break
        y, rem_y = poly_divmod(z, a_i)
        assert not rem_y
        z = poly_sub(y, poly_diff(w))
    return factors


def hermite_reduce(num: UniPoly, den: UniPoly) -> tuple[UniPoly, UniPoly, UniPoly, UniPoly, UniPoly]:
    r"""Hermite reduction of rational function A(x)/D(x) in Q(x):
    Computes (poly_integral, herm_num, herm_den, log_num, log_den) such that:
        \int (num/den) dx = poly_integral + herm_num/herm_den + \int (log_num/log_den) dx
    where `log_den` is completely SQUARE-FREE!
    """
    poly_part, rem = poly_divmod(num, den)
    # Integrate polynomial part
    poly_int = {k + 1: v / (k + 1) for k, v in poly_part.items()}

    def add_rat(n1: UniPoly, d1: UniPoly, n2: UniPoly, d2: UniPoly) -> tuple[UniPoly, UniPoly]:
        top = poly_add(poly_mul(n1, d2), poly_mul(n2, d1))
        bot = poly_mul(d1, d2)
        if not top:
            return {}, {0: Fraction(1)}
        g, _, _ = poly_xgcd(top, bot)
        if poly_deg(g) > 0:
            top, _ = poly_divmod(top, g)
            bot, _ = poly_divmod(bot, g)
        return top, poly_make_monic(bot)

    a = rem
    d = poly_make_monic(den)
    g_num: UniPoly = {}
    g_den: UniPoly = {0: Fraction(1)}
    while True:
        v, _, _ = poly_xgcd(d, poly_diff(d))
        if poly_deg(v) <= 0:
            break
        sqf = square_free_factors(d)
        # Iterate from highest multiplicity k = len(sqf) down to 2:
        # Actually let's compute partial fraction / Bezout step cleanly over all multiplicities!
        # Let q_m = sqf[-1] (irreducible/square-free with multiplicity m = len(sqf) >= 2).
        # Let d_rest = d / q_m^m. Write d = q_m^m * d_rest.
        m = len(sqf)
        if m <= 1:
            break
        qm = sqf[-1]
        if poly_deg(qm) == 0:
            # Find highest k >= 2 with deg(sqf[k-1]) > 0
            while len(sqf) > 1 and poly_deg(sqf[-1]) == 0:
                sqf.pop()
            m = len(sqf)
            if m <= 1:
                break
            qm = sqf[-1]
        # Reduce multiplicity m -> m - 1 for qm:
        # Write d = qm^m * rest, where gcd(qm, rest) == 1.
        qm_pow_m = {0: Fraction(1)}
        for _ in range(m):
            qm_pow_m = poly_mul(qm_pow_m, qm)
        rest, check = poly_divmod(d, qm_pow_m)
        assert not check
        # Compute (b / qm^{m-1})' = (b' qm - (m-1) b qm') / qm^m.
        # Want A / (qm^m * rest) - (b / qm^{m-1})' = (c * qm) / (qm^m * rest) = c / (qm^{m-1} * rest)
        # => A - rest * (b' qm - (m-1) b qm') == 0 (mod qm)
        # => -(m - 1) * rest * qm' * b == A (mod qm)!
        # Since gcd(qm, rest) == 1 and gcd(qm, qm') == 1, invert -(m - 1) * rest * qm' mod qm!
        factor_mod = poly_mul({0: Fraction(-(m - 1))}, poly_mul(rest, poly_diff(qm)))
        g_inv, s_inv, _ = poly_xgcd(factor_mod, qm)
        assert poly_deg(g_inv) == 0
        _, b = poly_divmod(poly_mul(a, s_inv), qm)

        qm_pow_m_minus_1 = {0: Fraction(1)}
        for _ in range(m - 1):
            qm_pow_m_minus_1 = poly_mul(qm_pow_m_minus_1, qm)
        g_num, g_den = add_rat(g_num, g_den, b, qm_pow_m_minus_1)

        # New numerator: (A - rest * (b' qm - (m-1) b qm')) / qm
        deriv_num = poly_sub(poly_mul(poly_diff(b), qm), poly_mul({0: Fraction(m - 1)}, poly_mul(b, poly_diff(qm))))
        rem_num = poly_sub(a, poly_mul(rest, deriv_num))
        a, rem_chk = poly_divmod(rem_num, qm)
        assert not rem_chk
        d, _ = poly_divmod(d, qm)

    # Reduce logarithmic part a / d to lowest terms
    if not a:
        return poly_int, g_num, g_den, {}, {0: Fraction(1)}
    g_fin, _, _ = poly_xgcd(a, d)
    if poly_deg(g_fin) > 0:
        a, _ = poly_divmod(a, g_fin)
        d, _ = poly_divmod(d, g_fin)
    return poly_int, g_num, poly_make_monic(g_den), a, poly_make_monic(d)


def run_experiment_3() -> None:
    print("=" * 80)
    print("EXPERIMENT 3: EXACT HERMITE REDUCTION & INTEGRABILITY VERIFICATION")
    print("=" * 80)
    x = sp.Symbol("x")

    # Tricky rational function with multiple roots (x - 1)^3 * (x^2 + 1)^2 and degree > den
    # Test: (x^7 - 2 x^4 + 3 x^2 + 5 x - 1) / ((x - 1)^3 * (x^2 + 1)^2)
    den = poly_mul(
        poly_mul({0: Fraction(-1), 1: Fraction(1)},
                 poly_mul({0: Fraction(-1), 1: Fraction(1)}, {0: Fraction(-1), 1: Fraction(1)})),
        poly_mul({0: Fraction(1), 2: Fraction(1)}, {0: Fraction(1), 2: Fraction(1)}),
    )
    num = {7: Fraction(1), 4: Fraction(-2), 2: Fraction(3), 1: Fraction(5), 0: Fraction(-1)}

    t0 = time.perf_counter()
    p_int, g_num, g_den, log_num, log_den = hermite_reduce(num, den)
    t_alg = (time.perf_counter() - t0) * 1e3

    # Verify algebraically via SymPy: diff(p_int + g_num/g_den) + log_num/log_den == num/den
    expr_alg_rat = poly_to_sympy(p_int, x) + poly_to_sympy(g_num, x) / poly_to_sympy(g_den, x)
    expr_alg_log_integrand = poly_to_sympy(log_num, x) / poly_to_sympy(log_den, x)
    reconstructed = sp.simplify(sp.diff(expr_alg_rat, x) + expr_alg_log_integrand)
    target = poly_to_sympy(num, x) / poly_to_sympy(den, x)
    diff_check = sp.simplify(reconstructed - target)

    # Also compare full integral with SymPy integrate!
    t0 = time.perf_counter()
    sympy_int = sp.integrate(target, x)
    t_sym = (time.perf_counter() - t0) * 1e3

    # Check whether log_den is strictly square-free (deg gcd(log_den, log_den') == 0)
    g_sqf, _, _ = poly_xgcd(log_den, poly_diff(log_den))
    print(f"Hermite Reduction runtime: {t_alg:.2f} ms vs SymPy integrate: {t_sym:.2f} ms")
    print(f"Logarithmic denominator strictly square-free (deg gcd == 0): {poly_deg(g_sqf) == 0}")
    print(f"Derivative check d/dx(P + G_num/G_den) + H/S - Num/Den == 0: {diff_check == 0}")
    print(
        f"AlgebraX pure-Fraction vs SymPy full integral diff check:"
        f" {sp.simplify(sp.diff(sympy_int, x) - reconstructed) == 0}"
    )
    print()


# =============================================================================
# Experiment 4: Exact Higher-Order Taylor Jet Algebra & Algebraic ODE Solver
# =============================================================================


def run_experiment_4() -> None:
    print("=" * 80)
    print("EXPERIMENT 4: EXACT TAYLOR JET ALGEBRA k[x]/<x^{r+1}> & NONLINEAR RICCATI ODE")
    print("=" * 80)
    field = StandardField(Fraction)
    order = 12
    poly_ring = PolynomialAlgebra(field)
    jet_ideal = PolynomialTruncationIdeal(order + 1, field.zero)
    jet_ring = QuotientRing(poly_ring, jet_ideal)

    def jet_integrate(p: UniPoly) -> UniPoly:
        return {k + 1: v / Fraction(k + 1) for k, v in p.items() if k + 1 <= order}

    # Solve nonlinear Riccati / tan(x) ODE: y'(x) = 1 + y(x)^2, y(0) = 0
    # Exact Newton/Picard fixed-point iteration in Jet Algebra Q[x]/<x^{13}>:
    # Each iteration doubles exact precision order (1 -> 2 -> 4 -> 8 -> 16 >= 12)!
    y: UniPoly = {}
    for _ in range(order + 1):
        y_sq = jet_ring.mul(y, y)
        rhs = poly_add({0: Fraction(1)}, y_sq)
        y = jet_integrate(rhs)

    # Check exact ODE residual: y'(x) - (1 + y(x)^2) == 0 mod x^order
    y_prime = poly_diff(y)
    ode_residual = poly_sub(y_prime, poly_add({0: Fraction(1)}, jet_ring.mul(y, y)))
    # Mod x^order (since y is valid up to deg order, y' is valid up to deg order-1)
    ode_res_mod = {k: v for k, v in ode_residual.items() if k < order}

    # Verify against SymPy exact Taylor series of tan(x)
    x = sp.Symbol("x")
    tan_series = sp.series(sp.tan(x), x, 0, order + 1).removeO()
    y_sym = poly_to_sympy(y, x)
    print(f"Solved nonlinear ODE y' = 1 + y^2, y(0) = 0 in Jet Algebra Q[x]/<x^{order + 1}>")
    print(f"Exact Taylor coefficients matched SymPy series(tan(x), 13): {sp.expand(y_sym - tan_series) == 0}")
    print(f"Exact ODE residual (y' - (1 + y^2)) mod x^{order} == 0: {not ode_res_mod}")
    print(f"tan(x) Jet sample: x^1={y[1]}, x^3={y[3]}, x^5={y[5]}, x^7={y[7]}, x^9={y[9]}")
    print()


# =============================================================================
# Experiment 5: Non-Commutative Left Weyl Grobner Elimination & Identity Certification
# =============================================================================


def weyl_lm(op: WeylPoly[Fraction]) -> WeylMonomial:
    """Graded-lex ordering on (x, d) with Bernstein weight (1, 1)."""
    return max(op.keys(), key=lambda m: (sum(m[0]) + sum(m[1]), m[1], m[0]))


def weyl_reduce_left(weyl: WeylAlgebra[Fraction],
                     f: WeylPoly[Fraction],
                     basis: list[WeylPoly[Fraction]]) -> WeylPoly[Fraction]:
    """Left reduction of f modulo a finite Weyl left ideal basis."""
    p = dict(f)
    rem: WeylPoly[Fraction] = {}
    while p:
        lmp = weyl_lm(p)
        reduced = False
        for g in basis:
            lmg = weyl_lm(g)
            # Check componentwise divisibility of both x-exp and d-exp
            if all(lmg[0][i] <= lmp[0][i] for i in range(weyl.n_vars)) and all(
                    lmg[1][i] <= lmp[1][i] for i in range(weyl.n_vars)
            ):
                shift_x = tuple(lmp[0][i] - lmg[0][i] for i in range(weyl.n_vars))
                shift_d = tuple(lmp[1][i] - lmg[1][i] for i in range(weyl.n_vars))
                scale = p[lmp] / g[lmg]
                # Multiply on the LEFT by scale * x^{shift_x} * d^{shift_d}
                left_mon: WeylPoly[Fraction] = {(shift_x, shift_d): scale}
                p = weyl.sub(p, weyl.mul(left_mon, g))
                reduced = True
                break
        if not reduced:
            rem[lmp] = p.pop(lmp)
    return rem


def run_experiment_5() -> None:
    print("=" * 80)
    print("EXPERIMENT 5: NON-COMMUTATIVE WEYL LEFT IDEAL REDUCTION & D-FINITE VERIFICATION")
    print("=" * 80)
    field = StandardField(Fraction)
    weyl = WeylAlgebra(field, n_vars=1)
    x, d = weyl.x(0), weyl.d(0)

    # Annihilator of f(x) = exp(x^2): f'(x) - 2x f(x) = 0 -> L = d - 2x
    two_x = weyl.add(x, x)
    ann_gauss = weyl.sub(d, two_x)

    # Second-order operator L2 = d^2 - 4 x^2 - 2 MUST belong to the LEFT ideal D * (d - 2x)!
    # Check: (d + 2x) * (d - 2x) = d^2 - 2 d x + 2 x d - 4 x^2 = d^2 - 2(x d + 1) + 2 x d - 4 x^2 = d^2 - 4 x^2 - 2!
    x2 = weyl.mul(x, x)
    d2 = weyl.mul(d, d)
    four_x2 = {k: 4 * v for k, v in x2.items()}
    two_one = {((0,), (0,)): Fraction(2)}
    l2 = weyl.sub(weyl.sub(d2, four_x2), two_one)

    # Left reduction modulo [d - 2x] certifies whether L2 annihilates exp(x^2)!
    rem = weyl_reduce_left(weyl, l2, [ann_gauss])
    print("Gaussian Annihilator L1 = d - 2x")
    print("Target ODE L2 = d^2 - 4x^2 - 2")
    print(f"Non-commutative Weyl left reduction rem(L2, [L1]) == {{}}: {rem == {} }")
    print(f"Direct Leibniz identity check (d + 2x)*(d - 2x) == L2: {weyl.mul(weyl.add(d, two_x), ann_gauss) == l2}")
    print()


# =============================================================================
# Experiment 6: Difference Ore Algebra, Gosper Summation & Euler Indicial Roots
# =============================================================================


def poly_shift_k(p: UniPoly, k: int) -> UniPoly:
    """Compute p(n + k) via exact binomial expansion."""
    out: UniPoly = {}
    for deg, coeff in p.items():
        for j in range(deg + 1):
            term = coeff * Fraction(math.comb(deg, j)) * (Fraction(k) ** (deg - j))
            if term != 0:
                out[j] = out.get(j, Fraction(0)) + term
    return poly_clean(out)


def poly_resultant(a: UniPoly, b: UniPoly) -> Fraction:
    """Exact polynomial resultant Res(a, b) via Euclidean pseudo-remainder recursion."""
    da, db = poly_deg(a), poly_deg(b)
    if da < 0 or db < 0:
        return Fraction(0)
    if da == 0:
        return a[0] ** db
    if db == 0:
        return b[0] ** da
    if da < db:
        sign = Fraction(-1) if (da * db) % 2 == 1 else Fraction(1)
        return sign * poly_resultant(b, a)
    _, r = poly_divmod(a, b)
    if not r:
        return Fraction(0)
    dr = poly_deg(r)
    lcb = b[db]
    sign = Fraction(-1) if (da * db) % 2 == 1 else Fraction(1)
    # Res(a, b) = (-1)^{da*db} * lc(b)^{da - dr} * Res(b, r)
    return sign * (lcb ** (da - dr)) * poly_resultant(b, r)


def solve_fraction_linear(mat: list[list[Fraction]], rhs: list[Fraction]) -> list[Fraction] | None:
    """Exact Gaussian elimination over Q (returns unique/particular solution or None)."""
    m = len(mat)
    n = len(mat[0]) if m else 0
    aug = [[*list(mat[i]), rhs[i]] for i in range(m)]
    pivots: list[int] = []
    row = 0
    for col in range(n):
        piv = None
        for r in range(row, m):
            if aug[r][col] != 0:
                piv = r
                break
        if piv is None:
            continue
        aug[row], aug[piv] = aug[piv], aug[row]
        pv = aug[row][col]
        aug[row] = [v / pv for v in aug[row]]
        for r in range(m):
            if r != row and aug[r][col] != 0:
                fac = aug[r][col]
                aug[r] = [aug[r][c] - fac * aug[row][c] for c in range(n + 1)]
        pivots.append(col)
        row += 1
    for r in range(row, m):
        if aug[r][n] != 0:
            return None
    sol = [Fraction(0)] * n
    for r, col in enumerate(pivots):
        sol[col] = aug[r][n]
    return sol


def gosper_rational_sum(f_num: UniPoly, g_den: UniPoly) -> tuple[UniPoly, UniPoly] | None:  # noqa: C901
    """Exact Gosper indefinite hypergeometric summation algorithm over Q(n).

    Given ratio t_{n+1}/t_n = f_num(n) / g_den(n), finds rational certificate r(n) = R_num/R_den
    such that S(n) = r(n) * t_n satisfies S(n+1) - S(n) = t_n, or returns None if non-summable.
    """
    g_common, _, _ = poly_xgcd(f_num, g_den)
    a, _ = poly_divmod(f_num, g_common)
    b, _ = poly_divmod(g_den, g_common)
    c: UniPoly = {0: Fraction(1)}

    # Compute resultant R(h) = Res_n(a(n), b(n + h)) via Lagrange interpolation
    max_deg_r = max(0, poly_deg(a) * poly_deg(b))
    pts = [(Fraction(i), poly_resultant(a, poly_shift_k(b, i))) for i in range(max_deg_r + 1)]
    r_poly: UniPoly = {}
    for i, (xi, yi) in enumerate(pts):
        if yi == 0:
            continue
        basis: UniPoly = {0: yi}
        denom = Fraction(1)
        for j, (xj, _) in enumerate(pts):
            if i != j:
                basis = poly_mul(basis, {0: -xj, 1: Fraction(1)})
                denom *= xi - xj
        r_poly = poly_add(r_poly, {k: v / denom for k, v in basis.items()})

    # Extract all non-negative integer roots h >= 0 of R(h)
    roots_h: list[int] = []
    if r_poly:
        # Clear denominators to find integer divisors of constant term (after factoring out h^k)
        min_pow = min(r_poly.keys())
        if min_pow > 0:
            roots_h.append(0)
        shifted_r = {k - min_pow: v for k, v in r_poly.items()}
        lcm_den = 1
        for v in shifted_r.values():
            lcm_den = math.lcm(lcm_den, v.denominator)
        int_c0 = abs(int((shifted_r[0] * lcm_den).numerator))
        if int_c0 > 0:
            for d_cand in range(1, int_c0 + 1):
                if int_c0 % d_cand == 0 and poly_eval(shifted_r, Fraction(d_cand)) == 0:
                    roots_h.append(d_cand)

    for h in sorted(roots_h):
        g_h, _, _ = poly_xgcd(a, poly_shift_k(b, h))
        if poly_deg(g_h) > 0:
            a, _ = poly_divmod(a, g_h)
            b, _ = poly_divmod(b, poly_shift_k(g_h, -h))
            for j in range(1, h + 1):
                c = poly_mul(c, poly_shift_k(g_h, -j))

    b_prev = poly_shift_k(b, -1)
    p_diff = poly_sub(a, b_prev)
    da, dp, dc = poly_deg(a), poly_deg(p_diff), poly_deg(c)

    # Candidate degree bound for x(n) in a(n)*x(n+1) - b(n-1)*x(n) = c(n)
    cands: list[int] = []
    if dp >= da:
        cands.append(dc - dp)
    elif dp < da - 1:
        cands.append(dc - da + 1)
    else:
        cands.append(dc - dp)
        ratio = -p_diff[dp] / a[da]
        if ratio.denominator == 1 and ratio.numerator >= 0:
            cands.append(int(ratio.numerator))
    deg_x = max([k for k in cands if k >= 0], default=-1)
    if deg_x < 0:
        return None

    # Build linear system for x(n) = sum_{k=0}^{deg_x} x_k n^k
    max_lhs_deg = max(dc, max(da, poly_deg(b_prev)) + deg_x)
    cols: list[UniPoly] = []
    for k in range(deg_x + 1):
        xk = {k: Fraction(1)}
        col_poly = poly_sub(poly_mul(a, poly_shift_k(xk, 1)), poly_mul(b_prev, xk))
        cols.append(col_poly)
    mat = [[cols[col].get(row, Fraction(0)) for col in range(deg_x + 1)] for row in range(max_lhs_deg + 1)]
    rhs = [c.get(row, Fraction(0)) for row in range(max_lhs_deg + 1)]
    sol = solve_fraction_linear(mat, rhs)
    if sol is None:
        return None
    x_poly = poly_clean(dict(enumerate(sol)))
    r_num = poly_mul(b_prev, x_poly)
    g_out, _, _ = poly_xgcd(r_num, c)
    if poly_deg(g_out) > 0:
        r_num, _ = poly_divmod(r_num, g_out)
        c, _ = poly_divmod(c, g_out)
    lc_c = c[poly_deg(c)]
    return {k: v / lc_c for k, v in r_num.items()}, {k: v / lc_c for k, v in c.items()}


def run_experiment_6() -> None:
    print("=" * 80)
    print("EXPERIMENT 6: DIFFERENCE ORE ALGEBRA, GOSPER SUMMATION & EULER INDICIAL ROOTS")
    print("=" * 80)

    # 1. Forward Difference Ore Algebra: Delta = S - 1, sigma(p) = p(n+1), delta(p) = p(n+1) - p(n)
    delta_ore = OreAlgebra(
        sigma=poly_shift_plus_one,
        delta=lambda p: poly_sub(poly_shift_plus_one(p), p),
        name="Difference(Q[n][Delta])",
    )
    p_test = {2: Fraction(1), 1: Fraction(3)}  # n^2 + 3n
    lhs = delta_ore.mul({1: {0: Fraction(1)}}, {0: p_test})
    rhs = {1: poly_shift_plus_one(p_test), 0: poly_sub(poly_shift_plus_one(p_test), p_test)}
    print(f"Difference Skew Rule (Delta * p == S(p)*Delta + Delta(p)): {lhs == rhs}")

    # 2. Gosper Summation Test A: t_n = n * n! -> ratio = (n+1)^2 / n -> cert r(n) = 1 / n
    cert_fac = gosper_rational_sum({2: Fraction(1), 1: Fraction(2), 0: Fraction(1)}, {1: Fraction(1)})
    assert cert_fac is not None
    print(
        f"Gosper sum(n * n!): r(n) = {cert_fac[0]} / {cert_fac[1]}"
        f" (expected 1/n: {cert_fac == ({0: Fraction(1)}, {1: Fraction(1)})})"
    )

    # 3. Gosper Summation Test B: t_n = (2n + 1) / (n^2 * (n+1)^2) (non-trivial dispersion h = 1!)
    # ratio = n^2 * (2n + 3) / ((n + 2)^2 * (2n + 1))
    f_tel = poly_mul({2: Fraction(1)}, {1: Fraction(2), 0: Fraction(3)})
    g_tel = poly_mul(poly_mul({1: Fraction(1), 0: Fraction(2)}, {1: Fraction(1), 0: Fraction(2)}),
                     {1: Fraction(2), 0: Fraction(1)})
    cert_tel = gosper_rational_sum(f_tel, g_tel)
    assert cert_tel is not None
    # Verify exact telescoping identity r(n+1)*(f/g) - r(n) == 1 against SymPy
    n_sym = sp.Symbol("n")
    r_sym = poly_to_sympy(cert_tel[0], n_sym) / poly_to_sympy(cert_tel[1], n_sym)
    ratio_sym = poly_to_sympy(f_tel, n_sym) / poly_to_sympy(g_tel, n_sym)
    tel_ok = sp.simplify(r_sym.subs(n_sym, n_sym + 1) * ratio_sym - r_sym - 1) == 0
    from sympy.concrete.gosper import gosper_sum as sp_gosper_sum

    sympy_gosper = sp.simplify(sp_gosper_sum((2 * n_sym + 1) / (n_sym ** 2 * (n_sym + 1) ** 2), n_sym))
    print(
        f"Gosper sum((2n+1)/(n^2*(n+1)^2)) dispersion h=1:"
        f" exact identity={tel_ok}, r(n)={r_sym},"
        f" SymPy oracle={sympy_gosper}"
    )

    # 4. Gosper Summation Test C (Negative Proof): Harmonic t_n = 1 / n -> ratio = n / (n + 1) -> None
    cert_harm = gosper_rational_sum({1: Fraction(1)}, {1: Fraction(1), 0: Fraction(1)})
    print(f"Gosper non-summability proof for 1/n: returns None={cert_harm is None}")

    # 5. Euler Operator theta = x*d/dx & Bessel Indicial Polynomial (nu = 1/2):
    # Bessel ODE: (theta^2 - 1/4 + x^2) y = 0 -> rewrite in theta = x*dx via theta * x^k = x^k * (theta + k)
    euler_ore = OreAlgebra(
        sigma=lambda p: p,  # Here coefficients live in Q[theta] and x acts? Wait: theta * x = x * (theta + 1)!
        delta=lambda _: {},
        name="EulerCheck",
    )
    _ = euler_ore
    # Represent Bessel operator in Weyl Algebra A_1(Q): x^2 d^2 + x d + (x^2 - 1/4)
    field = StandardField(Fraction)
    weyl = WeylAlgebra(field, n_vars=1)
    x, d = weyl.x(0), weyl.d(0)
    theta = weyl.mul(x, d)
    bessel = weyl.add(weyl.sub(weyl.mul(theta, theta), {((0,), (0,)): Fraction(1, 4)}), weyl.mul(x, x))
    # Verify exact Frobenius identity: x^2 d^2 + x d == (x d)^2 in A_1(Q)!
    x2_d2 = weyl.mul(weyl.mul(x, x), weyl.mul(d, d))
    canonical_bessel = weyl.add(weyl.add(x2_d2, theta), weyl.sub(weyl.mul(x, x), {((0,), (0,)): Fraction(1, 4)}))
    print(f"Weyl Bessel Identity x^2 d^2 + x d + (x^2 - 1/4) == theta^2 - 1/4 + x^2: {bessel == canonical_bessel}")
    # Extract indicial polynomial I(rho) by evaluating on x^rho: shift-invariant x-degree 0 terms (|alpha| == |beta|)
    # For x^a d^b acting on x^rho -> x^{rho + a - b} * prod_{j=0}^{b-1} (rho - j); degree shift a - b == 0 gives I(rho)!
    indicial: UniPoly = {}
    for (ax, bd), c_val in canonical_bessel.items():
        if ax[0] == bd[0]:
            falling: UniPoly = {0: c_val}
            for j in range(bd[0]):
                falling = poly_mul(falling, {1: Fraction(1), 0: Fraction(-j)})
            indicial = poly_add(indicial, falling)
    print(f"Bessel(nu=1/2) Indicial Polynomial I(rho) = {indicial}, roots rho = +/-1/2 check: "
          f"{poly_eval(indicial, Fraction(1, 2)) == 0 and poly_eval(indicial, Fraction(-1, 2)) == 0}")
    print()


# =============================================================================
# Experiment 7: Multivariate Taylor Jets, Characteristic Variety & Kahler 1-Forms
# =============================================================================


def run_experiment_7() -> None:
    print("=" * 80)
    print("EXPERIMENT 7: MULTIVARIATE TAYLOR JETS, CHARACTERISTIC VARIETY & KAHLER 1-FORMS")
    print("=" * 80)

    # 1. Multivariate Taylor Jet Ring Q[x, y] / <x, y>^4 (total degree <= 3, unifying DualNumberAlgebra)
    max_tot_deg = 3

    def jet2_mul(a: dict[tuple[int, int], Fraction], b: dict[tuple[int, int], Fraction]) -> dict[
        tuple[int, int], Fraction]:
        out: dict[tuple[int, int], Fraction] = {}
        for (ax, ay), va in a.items():
            for (bx, by), vb in b.items():
                nx, ny = ax + bx, ay + by
                if nx + ny <= max_tot_deg:
                    nv = out.get((nx, ny), Fraction(0)) + va * vb
                    if nv == 0:
                        out.pop((nx, ny), None)
                    else:
                        out[(nx, ny)] = nv
        return out

    def jet2_add(a: dict[tuple[int, int], Fraction], b: dict[tuple[int, int], Fraction]) -> dict[
        tuple[int, int], Fraction]:
        out = dict(a)
        for k, v in b.items():
            nv = out.get(k, Fraction(0)) + v
            if nv == 0:
                out.pop(k, None)
            else:
                out[k] = nv
        return out

    # Evaluate f(x, y) = exp(x * y) + x^2 * y in Q[x, y] / m^4
    x_jet = {(1, 0): Fraction(1)}
    y_jet = {(0, 1): Fraction(1)}
    u = jet2_mul(x_jet, y_jet)
    # exp(u) up to degree 3 (u has total deg 2, so u^2 has deg 4 -> vanishes mod m^4!)
    exp_u = {(0, 0): Fraction(1)}
    u_pow = {(0, 0): Fraction(1)}
    for k in range(1, max_tot_deg + 1):
        u_pow = jet2_mul(u_pow, u)
        if not u_pow:
            break
        exp_u = jet2_add(exp_u, {m: v / Fraction(math.factorial(k)) for m, v in u_pow.items()})
    f_jet = jet2_add(exp_u, jet2_mul(jet2_mul(x_jet, x_jet), y_jet))

    # Extract exact derivatives at (0, 0): d^{i+j} f / (dx^i dy^j) = i! * j! * coeff[(i, j)]
    xs, ys = sp.symbols("x y")
    f_sym = sp.exp(xs * ys) + xs ** 2 * ys
    jet_matches = True
    for i in range(max_tot_deg + 1):
        for j in range(max_tot_deg + 1 - i):
            jet_deriv = Fraction(math.factorial(i) * math.factorial(j)) * f_jet.get((i, j), Fraction(0))
            sym_deriv = sp.diff(f_sym, xs, i, ys, j).subs({xs: 0, ys: 0})
            if sp.Rational(jet_deriv.numerator, jet_deriv.denominator) != sym_deriv:
                jet_matches = False
    print(f"Multivariate Jet Q[x,y]/m^4 exact partials (up to order 3) match SymPy: {jet_matches}")
    print(
        f"Exact mixed derivatives: d^2f/dxdy(0,0)={f_jet.get((1, 1), 0)}, d^3f/dx^2dy(0,0)={2 * f_jet.get((2, 1), 0)}")

    # 2. Weyl Characteristic Variety Char(I) for 2D Gaussian I = <d_0 - 2x_0, d_1 - 2x_1> in A_2(Q)
    weyl2 = WeylAlgebra(StandardField(Fraction), n_vars=2)
    g0 = weyl2.sub(weyl2.d(0), weyl2.add(weyl2.x(0), weyl2.x(0)))
    g1 = weyl2.sub(weyl2.d(1), weyl2.add(weyl2.x(1), weyl2.x(1)))

    # Order-filtration principal symbols (max sum(beta)):
    def principal_symbol(op: WeylPoly[Fraction]) -> set[tuple[Monomial, Monomial]]:
        max_ord = max(sum(m[1]) for m in op)
        return {m for m in op if sum(m[1]) == max_ord}

    sym_ideal = [principal_symbol(g0), principal_symbol(g1)]
    # Symbols are {((0,0),(1,0))} = xi_0
    # and {((0,0),(0,1))} = xi_1 -> Char(I) = V(xi_0, xi_1) in Q^4 has dim = 2 == n_vars!
    char_gens = [next(iter(s))[1] for s in sym_ideal]
    is_holonomic = len(char_gens) == 2 and char_gens == [(1, 0), (0, 1)]
    print(
        f"Weyl 2D Gaussian Principal Symbols Char(I)=V(xi_0, xi_1), dim(Char)=2 == n_vars (holonomic): {is_holonomic}")

    # 3. Kahler Differential Pairing df(X) == 0 on Circle Variety V(x^2 + y^2 - 1):
    # f = x^2 + y^2 - 1 -> df = (2x) dx + (2y) dy; Tangent vector field X = (-y) d/dx + (x) d/dy
    # Verify contraction <df, X> == (2x)(-y) + (2y)(x) == 0 identically!
    df_dx = {(1, 0): Fraction(2)}
    df_dy = {(0, 1): Fraction(2)}
    x_comp = {(0, 1): Fraction(-1)}
    y_comp = {(1, 0): Fraction(1)}
    pairing = jet2_add(jet2_mul(df_dx, x_comp), jet2_mul(df_dy, y_comp))
    print(f"Kahler Differential contraction <d(x^2+y^2-1), -y dx + x dy> == 0: {pairing == {} }")
    print()


# =============================================================================
# Experiment 8: Differential Galois Theory (Sym^k, Wronskian, Kovacic & SL_2)
# =============================================================================

Rat = tuple[UniPoly, UniPoly]
RAT_ZERO: Rat = ({}, {0: Fraction(1)})
RAT_ONE: Rat = ({0: Fraction(1)}, {0: Fraction(1)})


def rat_const(c: Fraction) -> Rat:
    if c == 0:
        return RAT_ZERO
    return {0: c}, {0: Fraction(1)}


def rat_norm(num: UniPoly, den: UniPoly) -> Rat:
    if not den:
        raise ZeroDivisionError("Zero denominator in Q(x).")
    if not num:
        return RAT_ZERO
    g, _, _ = poly_xgcd(num, den)
    if poly_deg(g) > 0:
        num, _ = poly_divmod(num, g)
        den, _ = poly_divmod(den, g)
    lc = den[poly_deg(den)]
    return {k: v / lc for k, v in num.items()}, {k: v / lc for k, v in den.items()}


def rat_add(a: Rat, b: Rat) -> Rat:
    return rat_norm(poly_add(poly_mul(a[0], b[1]), poly_mul(b[0], a[1])), poly_mul(a[1], b[1]))


def rat_sub(a: Rat, b: Rat) -> Rat:
    return rat_norm(poly_sub(poly_mul(a[0], b[1]), poly_mul(b[0], a[1])), poly_mul(a[1], b[1]))


def rat_mul(a: Rat, b: Rat) -> Rat:
    return rat_norm(poly_mul(a[0], b[0]), poly_mul(a[1], b[1]))


def rat_div(a: Rat, b: Rat) -> Rat:
    if not b[0]:
        raise ZeroDivisionError("Division by zero rational function.")
    return rat_norm(poly_mul(a[0], b[1]), poly_mul(a[1], b[0]))


def rat_diff(a: Rat) -> Rat:
    n, d = a
    if not n:
        return RAT_ZERO
    return rat_norm(poly_sub(poly_mul(poly_diff(n), d), poly_mul(n, poly_diff(d))), poly_mul(d, d))


def rat_nullspace_vector(cols: list[list[Rat]]) -> list[Rat]:
    """Find minimal non-trivial linear dependence sum_{j} c_j * cols[j] == 0 over Q(x)."""
    n_cols = len(cols)
    n_rows = len(cols[0])
    mat = [[cols[c][r] for c in range(n_cols)] for r in range(n_rows)]
    pivots: list[tuple[int, int]] = []
    for row, col in enumerate(range(n_cols)):
        piv = None
        for r in range(row, n_rows):
            if mat[r][col][0]:
                piv = r
                break
        if piv is None:
            # First dependent column! Back-substitute to express cols[col] in terms of prior pivot columns
            sol = [RAT_ZERO] * n_cols
            sol[col] = RAT_ONE
            for pr, pc in reversed(pivots):
                acc = RAT_ZERO
                for j in range(pc + 1, col + 1):
                    acc = rat_add(acc, rat_mul(mat[pr][j], sol[j]))
                sol[pc] = ({k: -v for k, v in acc[0].items()}, acc[1])
            return sol
        mat[row], mat[piv] = mat[piv], mat[row]
        pv = mat[row][col]
        mat[row] = [rat_div(v, pv) for v in mat[row]]
        for r in range(n_rows):
            if r != row and mat[r][col][0]:
                fac = mat[r][col]
                mat[r] = [rat_sub(mat[r][c], rat_mul(fac, mat[row][c])) for c in range(n_cols)]
        pivots.append((row, col))
    raise ValueError("Columns are linearly independent.")


def symmetric_power_order2(a1: Rat, a0: Rat, k: int) -> list[UniPoly]:
    """Compute minimal differential operator Sym^k(L) in Q[x][D] for L = D^2 + a1 D + a0.

    Represents z = y^k in the (k+1)-dimensional basis M_j = y^{k-j} (y')^j, using exact
    derivation D(M_j) = (k-j) M_{j+1} - j*a1*M_j - j*a0*M_{j-1} and RREF over Q(x).
    Returns primitive polynomial coefficients [c_0(x), ..., c_r(x)] of sum c_m D^m (z) == 0.
    """
    vecs: list[list[Rat]] = [[RAT_ONE if j == 0 else RAT_ZERO for j in range(k + 1)]]
    for _ in range(k + 1):
        cur = vecs[-1]
        nxt = [rat_diff(c) for c in cur]
        for j, cj in enumerate(cur):
            if not cj[0]:
                continue
            if j < k:
                nxt[j + 1] = rat_add(nxt[j + 1], rat_mul(cj, rat_const(Fraction(k - j))))
            if j > 0:
                jf = rat_const(Fraction(j))
                nxt[j] = rat_sub(nxt[j], rat_mul(cj, rat_mul(jf, a1)))
                nxt[j - 1] = rat_sub(nxt[j - 1], rat_mul(cj, rat_mul(jf, a0)))
        vecs.append(nxt)

    rel_rat = rat_nullspace_vector(vecs)
    while rel_rat and not rel_rat[-1][0]:
        rel_rat.pop()
    # Clear polynomial denominators via LCM
    lcm_den: UniPoly = {0: Fraction(1)}
    for _, d in rel_rat:
        g, _, _ = poly_xgcd(lcm_den, d)
        q, _ = poly_divmod(d, g)
        lcm_den = poly_make_monic(poly_mul(lcm_den, q))
    poly_coeffs = [rat_mul(c, (lcm_den, {0: Fraction(1)}))[0] for c in rel_rat]
    # Remove common polynomial content and make leading coefficient monic/clean
    content_g: UniPoly = {}
    for p in poly_coeffs:
        if p:
            content_g = p if not content_g else poly_xgcd(content_g, p)[0]
    if poly_deg(content_g) > 0:
        poly_coeffs = [poly_divmod(p, content_g)[0] if p else {} for p in poly_coeffs]
    lc_lead = poly_coeffs[-1][poly_deg(poly_coeffs[-1])]
    return [{deg: val / lc_lead for deg, val in p.items()} for p in poly_coeffs]


def sqrt_fraction(q: Fraction) -> Fraction | None:
    if q < 0:
        return None
    if q == 0:
        return Fraction(0)
    sn, sd = math.isqrt(q.numerator), math.isqrt(q.denominator)
    if sn * sn == q.numerator and sd * sd == q.denominator:
        return Fraction(sn, sd)
    return None


def kovacic_classify(r_num: UniPoly, r_den: UniPoly) -> dict[str, object]:
    """Kovacic order-2 Liouvillian admissibility classifier for u'' = (r_num / r_den) u."""
    r_num, r_den = rat_norm(r_num, r_den)
    sqf = square_free_factors(r_den)
    pole_muls = [(idx + 1, poly_deg(q)) for idx, q in enumerate(sqf) if poly_deg(q) > 0]
    val_inf = poly_deg(r_den) - poly_deg(r_num)

    case1 = (val_inf >= 2 or (val_inf <= 0 and val_inf % 2 == 0)) and all(
        m == 1 or m % 2 == 0 for m, _ in pole_muls
    )
    has_c2_pole = any(m == 2 or (m >= 3 and m % 2 == 1) for m, _ in pole_muls)
    # Without finite poles, Case 2 requires val_inf >= 2 or (val_inf <= 0 even for d = val_inf/2 >= 0? Wait: d >= 0!)
    case2 = has_c2_pole or (not pole_muls and val_inf >= 2 and val_inf % 2 == 0)
    case3 = all(m <= 2 for m, _ in pole_muls) and val_inf >= 2
    return {
        "pole_multiplicities": pole_muls,
        "val_inf": val_inf,
        "case1_admissible": case1,
        "case2_admissible": case2,
        "case3_admissible": case3,
        "liouvillian_possible": case1 or case2 or case3,
    }


def kovacic_case1_poly_riccati(r_poly: UniPoly) -> Rat | None:
    """Exact Kovacic Case 1 rational Riccati solver w' + w^2 = r_poly for polynomial r_poly in Q[x]."""
    deg_r = poly_deg(r_poly)
    if deg_r < 0:
        return RAT_ZERO
    if deg_r % 2 != 0:
        return None
    nu = deg_r // 2
    s0 = sqrt_fraction(r_poly[deg_r])
    if s0 is None:
        return None
    # Reverse coefficients: r(1/z) * z^{2*nu} = sum_{j=0}^{2*nu} r_{2*nu - j} z^j
    r_rev = {deg_r - k: v for k, v in r_poly.items()}
    # Newton sqrt mod z^{nu + 1}: s_{k+1} = 1/2 (s_k + r_rev / s_k)
    s_rev: UniPoly = {0: s0}
    trunc = nu + 1
    for _ in range(nu.bit_length() + 2):
        # Compute r_rev / s_rev mod z^trunc by power series inversion of s_rev
        inv_s: UniPoly = {0: Fraction(1) / s_rev[0]}
        for deg in range(1, trunc):
            acc = Fraction(0)
            for j in range(1, deg + 1):
                acc += s_rev.get(j, Fraction(0)) * inv_s.get(deg - j, Fraction(0))
            val = -acc / s_rev[0]
            if val != 0:
                inv_s[deg] = val
        quot = {k: v for k, v in poly_mul(r_rev, inv_s).items() if k < trunc}
        s_rev = {k: v / Fraction(2) for k, v in poly_add(s_rev, quot).items() if k < trunc}
    sqrt_inf = poly_clean({nu - j: v for j, v in s_rev.items()})

    for sign in (Fraction(1), Fraction(-1)):
        a_poly = {k: sign * v for k, v in sqrt_inf.items()}
        b_poly = poly_sub(poly_add(poly_diff(a_poly), poly_mul(a_poly, a_poly)), r_poly)
        if nu == 0:
            if not b_poly:
                return (a_poly, {0: Fraction(1)})
            continue
        lc_a = a_poly[nu]
        b_coeff = b_poly.get(nu - 1, Fraction(0))
        d_cand = -b_coeff / (Fraction(2) * lc_a)
        if d_cand.denominator != 1 or d_cand.numerator < 0:
            continue
        d = int(d_cand.numerator)
        # Solve P'' + 2*A*P' + B*P == 0 for monic P(x) = x^d + sum_{j=0}^{d-1} p_j x^j
        cols: list[UniPoly] = []
        for j in range(d + 1):
            xj = {j: Fraction(1)}
            lhs_j = poly_add(
                poly_diff(poly_diff(xj)),
                poly_add(poly_mul({0: Fraction(2)}, poly_mul(a_poly, poly_diff(xj))), poly_mul(b_poly, xj)),
            )
            cols.append(lhs_j)
        if d == 0:
            if not cols[0]:
                return (a_poly, {0: Fraction(1)})
            continue
        max_row = max((poly_deg(c) for c in cols), default=-1)
        mat = [[cols[col].get(row, Fraction(0)) for col in range(d)] for row in range(max_row + 1)]
        rhs = [-cols[d].get(row, Fraction(0)) for row in range(max_row + 1)]
        sol = solve_fraction_linear(mat, rhs)
        if sol is not None:
            p_poly = poly_clean({**dict(enumerate(sol)), d: Fraction(1)})
            return rat_add((a_poly, {0: Fraction(1)}), rat_norm(poly_diff(p_poly), p_poly))
    return None


def run_experiment_8() -> None:
    print("=" * 80)
    print("EXPERIMENT 8: DIFFERENTIAL GALOIS THEORY (SYM^K, KOVACIC & SL_2 OBSTRUCTION)")
    print("=" * 80)
    x_sym = sp.Symbol("x")

    # 1. Symmetric Powers Sym^2 and Sym^3 on Harmonic Oscillator y'' + y = 0
    sym2_harm = symmetric_power_order2(RAT_ZERO, RAT_ONE, k=2)
    sym3_harm = symmetric_power_order2(RAT_ZERO, RAT_ONE, k=3)
    # Expected Sym^2(D^2 + 1) = D^3 + 4 D; Sym^3(D^2 + 1) = D^4 + 10 D^2 + 9
    print(f"Sym^2(D^2 + 1) == D^3 + 4D: {sym2_harm == [{}, {0: Fraction(4)}, {}, {0: Fraction(1)}]}")
    print(
        f"Sym^3(D^2 + 1) == D^4 + 10D^2 + 9:"
        f" {sym3_harm == [{0: Fraction(9)}, {}, {0: Fraction(10)}, {}, {0: Fraction(1)}]}")

    # 2. Symmetric Power Sym^2 on non-constant-coeff Airy ODE y'' - x y = 0
    sym2_airy = symmetric_power_order2(RAT_ZERO, ({1: Fraction(-1)}, {0: Fraction(1)}), k=2)
    # Expected: D^3 - 4x D - 2 -> [-2, -4x, 0, 1]
    airy_ok = sym2_airy == [{0: Fraction(-2)}, {1: Fraction(-4)}, {}, {0: Fraction(1)}]
    # Verify with SymPy symbolic Airy functions Ai(x)*Bi(x) and Ai(x)^2
    z_airy = sp.airyai(x_sym) * sp.airybi(x_sym)
    airy_sym_res = sp.simplify(sp.diff(z_airy, x_sym, 3) - 4 * x_sym * sp.diff(z_airy, x_sym) - 2 * z_airy)
    print(f"Sym^2(Airy: D^2 - x) == D^3 - 4x D - 2: {airy_ok}, SymPy Ai*Bi residual == 0: {airy_sym_res == 0}")

    # 3. Abel-Liouville Wronskian Identity W' + a1 W == 0 on y'' + (1/x) y' + (1 - 1/(4x^2)) y = 0
    y1 = x_sym ** (-sp.Rational(1, 2)) * sp.cos(x_sym)
    y2 = x_sym ** (-sp.Rational(1, 2)) * sp.sin(x_sym)
    wronskian = sp.simplify(y1 * sp.diff(y2, x_sym) - sp.diff(y1, x_sym) * y2)
    abel_res = sp.simplify(sp.diff(wronskian, x_sym) + (1 / x_sym) * wronskian)
    print(f"Abel-Liouville Wronskian W(y1, y2) = {wronskian}, W' + (1/x)*W == 0: {abel_res == 0}")

    # 4. Kovacic Obstruction Certificate on Airy y'' - x y = 0 -> Gal_d = SL_2 (Non-Liouvillian!)
    airy_cls = kovacic_classify({1: Fraction(1)}, {0: Fraction(1)})
    print(f"Kovacic Airy(r=x) classification: {airy_cls}")
    assert not airy_cls["liouvillian_possible"]

    # 5. Kovacic Case 1 Apparent-Singularity Riccati Factorization on y'' - (x^2 + 3) y = 0
    r_quad = {2: Fraction(1), 0: Fraction(3)}
    cls_quad = kovacic_classify(r_quad, {0: Fraction(1)})
    w1 = kovacic_case1_poly_riccati(r_quad)
    assert cls_quad["case1_admissible"]
    assert w1 is not None
    w2 = ({k: -v for k, v in w1[0].items()}, w1[1])
    # Verify exact operator factorization (D - w2)(D - w1) = D^2 - (w1 + w2)D + (w1*w2 - w1') == D^2 - (x^2 + 3)
    d1_coeff = rat_add(w1, w2)
    d0_coeff = rat_sub(rat_mul(w1, w2), rat_diff(w1))
    fact_ok = d1_coeff == RAT_ZERO and d0_coeff == ({2: Fraction(-1), 0: Fraction(-3)}, {0: Fraction(1)})

    # Compare against SymPy checkodesol & observe SymPy solve_riccati / dsolve limits!
    y_fn = sp.Function("y")
    w1_sym = poly_to_sympy(w1[0], x_sym) / poly_to_sympy(w1[1], x_sym)
    chk_ric = sp.checkodesol(y_fn(x_sym).diff(x_sym) + y_fn(x_sym) ** 2 - (x_sym ** 2 + 3), w1_sym)
    chk_ode = sp.checkodesol(y_fn(x_sym).diff(x_sym, 2) - (x_sym ** 2 + 3) * y_fn(x_sym),
                             x_sym * sp.exp(x_sym ** 2 / 2))
    from sympy.solvers.ode.riccati import solve_riccati

    sp_ric = solve_riccati(y_fn(x_sym), x_sym, -(x_sym ** 2 + 3), sp.Integer(0), sp.Integer(1))
    print(f"Kovacic Case 1 y''-(x^2+3)y=0 -> omega_1 = {w1_sym}, exact (D+w1)(D-w1)==D^2-(x^2+3): {fact_ok}")
    print(
        f"SymPy checkodesol(Riccati, w1)={chk_ric},"
        f" checkodesol(ODE, x*exp(x^2/2))={chk_ode},"
        f" SymPy solve_riccati={sp_ric}"
    )

    # 6. Cauchy-Euler Rational Pole Case 1 Verification: y'' - (2/x^2) y = 0 against SymPy solve_riccati
    ce_cls = kovacic_classify({0: Fraction(2)}, {2: Fraction(1)})
    w_ce = ({0: Fraction(2)}, {1: Fraction(1)})  # 2/x
    ce_ric_check = rat_add(rat_diff(w_ce), rat_mul(w_ce, w_ce)) == ({0: Fraction(2)}, {2: Fraction(1)})
    sp_ce = solve_riccati(y_fn(x_sym), x_sym, -2 / x_sym ** 2, sp.Integer(0), sp.Integer(1))
    print(
        f"Cauchy-Euler y''-(2/x^2)y=0:"
        f" poles={ce_cls['pole_multiplicities']},"
        f" w=2/x valid={ce_ric_check},"
        f" SymPy riccati={sp_ce}")
    print()


# =============================================================================
# Experiment 9: DifferentialPolynomialRing, Rota-Baxter, Newton Polygons & Guessing
# =============================================================================

JetMonomial = tuple[int, ...]  # Exponent tuple (e_0, e_1, ..., e_r) for prod (u^{(j)})^{e_j}
DiffPoly = dict[JetMonomial, Fraction]


def jmon_clean(exp: tuple[int, ...] | list[int]) -> JetMonomial:
    lst = list(exp)
    while lst and lst[-1] == 0:
        lst.pop()
    return tuple(lst)


class DifferentialPolynomialRing:
    """Differential polynomial ring Q{u} = Q[u, u', u'', ...] with total derivative D."""

    @staticmethod
    def clean(p: DiffPoly) -> DiffPoly:
        return {k: v for k, v in p.items() if v != 0}

    @staticmethod
    def var(order: int, coeff: Fraction = Fraction(1)) -> DiffPoly:
        if coeff == 0:
            return {}
        exp = [0] * (order + 1)
        exp[order] = 1
        return {tuple(exp): coeff}

    def add(self, a: DiffPoly, b: DiffPoly) -> DiffPoly:
        out = dict(a)
        for k, v in b.items():
            nv = out.get(k, Fraction(0)) + v
            if nv == 0:
                out.pop(k, None)
            else:
                out[k] = nv
        return out

    def sub(self, a: DiffPoly, b: DiffPoly) -> DiffPoly:
        return self.add(a, {k: -v for k, v in b.items()})

    def mul(self, a: DiffPoly, b: DiffPoly) -> DiffPoly:
        out: DiffPoly = {}
        for ma, va in a.items():
            for mb, vb in b.items():
                n = max(len(ma), len(mb))
                mc = jmon_clean([
                    (ma[i] if i < len(ma) else 0) + (mb[i] if i < len(mb) else 0)
                    for i in range(n)
                ])
                nv = out.get(mc, Fraction(0)) + va * vb
                if nv == 0:
                    out.pop(mc, None)
                else:
                    out[mc] = nv
        return out

    def partial_jet(self, p: DiffPoly, j: int) -> DiffPoly:
        out: DiffPoly = {}
        for m, v in p.items():
            if j < len(m) and m[j] > 0:
                nm = list(m)
                nm[j] -= 1
                key = jmon_clean(nm)
                nv = out.get(key, Fraction(0)) + v * Fraction(m[j])
                if nv == 0:
                    out.pop(key, None)
                else:
                    out[key] = nv
        return out

    def total_diff(self, p: DiffPoly) -> DiffPoly:
        out: DiffPoly = {}
        for m, v in p.items():
            for j, ej in enumerate(m):
                if ej == 0:
                    continue
                nm = list(m) + ([0] if j + 1 >= len(m) else [])
                nm[j] -= 1
                nm[j + 1] += 1
                key = jmon_clean(nm)
                nv = out.get(key, Fraction(0)) + v * Fraction(ej)
                if nv == 0:
                    out.pop(key, None)
                else:
                    out[key] = nv
        return out

    def euler_lagrange(self, lagrangian: DiffPoly) -> DiffPoly:
        """Variational derivative sum_{k >= 0} (-D)^k (dL / du^{(k)})."""
        max_ord = max((len(m) - 1 for m in lagrangian if m), default=-1)
        out: DiffPoly = {}
        for k in range(max_ord + 1):
            term = self.partial_jet(lagrangian, k)
            for _ in range(k):
                term = self.total_diff(term)
            if k % 2 == 1:
                term = {m: -v for m, v in term.items()}
            out = self.add(out, term)
        return out


def differential_newton_polygon(op: dict[int, UniPoly]) -> tuple[list[tuple[int, int]], list[Fraction]]:
    """Compute lower convex hull of (k, val_0(c_k) - k) and Katz irregularity slopes >= 0."""
    pts: list[tuple[int, int]] = []
    for k in sorted(op):
        c_k = op[k]
        if not c_k:
            continue
        val0 = min(c_k.keys())
        pts.append((k, val0 - k))

    # Andrew's monotone chain for lower convex hull
    hull: list[tuple[int, int]] = []
    for p in pts:
        while len(hull) >= 2:
            x1, y1 = hull[-2]
            x2, y2 = hull[-1]
            x3, y3 = p
            # Remove collinear or clockwise turns: (x2-x1)*(y3-y1) - (y2-y1)*(x3-x1) <= 0
            if (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1) <= 0:
                hull.pop()
            else:
                break
        hull.append(p)

    slopes: list[Fraction] = []
    for i in range(len(hull) - 1):
        x1, y1 = hull[i]
        x2, y2 = hull[i + 1]
        slopes.append(Fraction(y2 - y1, x2 - x1))
    return hull, slopes


def fraction_nullspace(mat: list[list[Fraction]]) -> list[Fraction] | None:
    """Return a non-zero rational nullspace vector x with mat @ x == 0, or None if full column rank."""
    m = len(mat)
    n = len(mat[0]) if m else 0
    aug = [list(row) for row in mat]
    pivots: list[tuple[int, int]] = []
    for row, col in enumerate(range(n)):
        piv = None
        for r in range(row, m):
            if aug[r][col] != 0:
                piv = r
                break
        if piv is None:
            sol = [Fraction(0)] * n
            sol[col] = Fraction(1)
            for pr, pc in reversed(pivots):
                acc = Fraction(0)
                for j in range(pc + 1, col + 1):
                    acc += aug[pr][j] * sol[j]
                sol[pc] = -acc
            return sol
        aug[row], aug[piv] = aug[piv], aug[row]
        pv = aug[row][col]
        aug[row] = [v / pv for v in aug[row]]
        for r in range(m):
            if r != row and aug[r][col] != 0:
                fac = aug[r][col]
                aug[r] = [aug[r][c] - fac * aug[row][c] for c in range(n)]
        pivots.append((row, col))
    return None


def guess_diff_ore(series: list[Fraction], max_order: int, max_poly_deg: int) -> dict[int, UniPoly] | None:
    """D-finite differential Pade guessing: find minimal L = sum_{k=0}^r p_k(x) D^k annihilating truncated series."""
    n_terms = len(series)
    # Precompute derivatives f^{(k)} as coefficient lists
    derivs: list[list[Fraction]] = [list(series)]
    for _ in range(max_order):
        prev = derivs[-1]
        derivs.append([Fraction(j) * prev[j] for j in range(1, len(prev))])

    for order in range(1, max_order + 1):
        for pdeg in range(max_poly_deg + 1):
            n_vars = (order + 1) * (pdeg + 1)
            valid_rows = n_terms - order
            if valid_rows <= n_vars:
                continue
            mat: list[list[Fraction]] = []
            for row_m in range(valid_rows):
                row_vec: list[Fraction] = []
                for k in range(order + 1):
                    dk = derivs[k]
                    for j in range(pdeg + 1):
                        idx = row_m - j
                        row_vec.append(dk[idx] if 0 <= idx < len(dk) else Fraction(0))
                mat.append(row_vec)
            sol = fraction_nullspace(mat)
            if sol is not None:
                op: dict[int, UniPoly] = {}
                for k in range(order + 1):
                    poly_k = poly_clean({j: sol[k * (pdeg + 1) + j] for j in range(pdeg + 1)})
                    if poly_k:
                        op[k] = poly_k
                if max(op.keys(), default=-1) == order:
                    lc = op[order][poly_deg(op[order])]
                    return {k: {d: v / lc for d, v in p.items()} for k, p in op.items()}
    return None


def guess_shift_ore(seq: list[Fraction], max_order: int, max_poly_deg: int) -> dict[int, UniPoly] | None:
    """Recurrence guessing: find minimal L = sum_{k=0}^r p_k(n) S_n^k annihilating sequence."""
    n_terms = len(seq)
    for order in range(1, max_order + 1):
        for pdeg in range(max_poly_deg + 1):
            n_vars = (order + 1) * (pdeg + 1)
            valid_rows = n_terms - order
            if valid_rows <= n_vars:
                continue
            mat: list[list[Fraction]] = []
            for n_idx in range(valid_rows):
                row_vec: list[Fraction] = []
                for k in range(order + 1):
                    val = seq[n_idx + k]
                    for j in range(pdeg + 1):
                        row_vec.append((Fraction(n_idx) ** j) * val)
                mat.append(row_vec)
            sol = fraction_nullspace(mat)
            if sol is not None:
                op: dict[int, UniPoly] = {}
                for k in range(order + 1):
                    poly_k = poly_clean({j: sol[k * (pdeg + 1) + j] for j in range(pdeg + 1)})
                    if poly_k:
                        op[k] = poly_k
                if max(op.keys(), default=-1) == order:
                    lc = op[order][poly_deg(op[order])]
                    return {k: {d: v / lc for d, v in p.items()} for k, p in op.items()}
    return None


def run_experiment_9() -> None:
    print("=" * 80)
    print("EXPERIMENT 9: VARIATIONAL COMPLEX, ROTA-BAXTER, NEWTON POLYGONS & D-FINITE GUESSING")
    print("=" * 80)

    # 1. DifferentialPolynomialRing Q{u} & Euler-Lagrange Complex (delta/delta_u o D == 0)
    dring = DifferentialPolynomialRing()
    u0, u1, u2 = dring.var(0), dring.var(1), dring.var(2)
    # Null Lagrangian test: F = u^2 * u'' + (u')^3 -> D(F) MUST vanish under Euler-Lagrange!
    f_jet = dring.add(dring.mul(dring.mul(u0, u0), u2), dring.mul(u1, dring.mul(u1, u1)))
    null_lag = dring.total_diff(f_jet)
    el_null = dring.euler_lagrange(null_lag)
    # Harmonic oscillator Lagrangian L = 1/2 (u')^2 - 1/2 u^2 -> delta L / delta u = -u'' - u
    half = Fraction(1, 2)
    lag_harm = dring.sub(
        {m: half * v for m, v in dring.mul(u1, u1).items()},
        {m: half * v for m, v in dring.mul(u0, u0).items()},
    )
    el_harm = dring.euler_lagrange(lag_harm)
    expected_harm = dring.sub({}, dring.add(u2, u0))
    # Higher-order Lagrangian L = 1/2 (u'')^2 + u * (u')^2 -> delta L / delta u = u^(4) - (u')^2 - 2 u u''
    lag_ho = dring.add(
        {m: half * v for m, v in dring.mul(u2, u2).items()},
        dring.mul(u0, dring.mul(u1, u1)),
    )
    el_ho = dring.euler_lagrange(lag_ho)
    u4 = dring.var(4)
    expected_ho = dring.sub(u4, dring.add(dring.mul(u1, u1), dring.mul({(): Fraction(2)}, dring.mul(u0, u2))))
    print(f"DifferentialPolynomialRing Null-Lagrangian delta(D(F))/delta u == 0: {el_null == {} }")
    print(
        f"Harmonic Euler-Lagrange == -u'' - u: {el_harm == expected_harm},"
        f" 2nd-order Jet EL == u^(4) - (u')^2 - 2uu'': {el_ho == expected_ho}"
    )

    # 2. Rota-Baxter Identity R(a)*R(b) == R(R(a)*b + a*R(b) + weight * a * b)
    def poly_int_zero(p: UniPoly) -> UniPoly:
        return {k + 1: v / Fraction(k + 1) for k, v in p.items()}

    f_rb = {2: Fraction(3), 1: Fraction(-1), 0: Fraction(2)}
    g_rb = {3: Fraction(1), 0: Fraction(5)}
    rb_int_ok = poly_mul(poly_int_zero(f_rb), poly_int_zero(g_rb)) == poly_int_zero(
        poly_add(poly_mul(poly_int_zero(f_rb), g_rb), poly_mul(f_rb, poly_int_zero(g_rb)))
    )
    # Weight +1 strict partial sum R^-(a)[n] = sum_{k=0}^{n-1} a_k
    a_seq = [Fraction(k + 1, k + 2) for k in range(8)]
    b_seq = [Fraction((-1) ** k * (k + 1)) for k in range(8)]

    def strict_psum(seq: list[Fraction]) -> list[Fraction]:
        out, acc = [], Fraction(0)
        for v in seq:
            out.append(acc)
            acc += v
        return out

    ra, rb = strict_psum(a_seq), strict_psum(b_seq)
    lhs_sum = [ra[i] * rb[i] for i in range(len(a_seq))]
    rhs_sum = strict_psum([ra[i] * b_seq[i] + a_seq[i] * rb[i] + a_seq[i] * b_seq[i] for i in range(len(a_seq))])
    print(
        f"Rota-Baxter weight 0 (integration by parts): {rb_int_ok},"
        f" weight +1 (summation by parts): {lhs_sum == rhs_sum}"
    )

    # 3. Differential Newton Polygons & Katz Irregularity Slopes
    # Bessel at x=0: x^2 D^2 + x D + (x^2 - 1/4) -> slopes [0] (Fuchsian)
    op_bessel = {2: {2: Fraction(1)}, 1: {1: Fraction(1)}, 0: {2: Fraction(1), 0: Fraction(-1, 4)}}
    hull_b, slopes_b = differential_newton_polygon(op_bessel)
    # Mixed-slope irregular at x=0: x^3 D^2 + x D - 1 -> slopes [0, 1]
    op_mixed = {2: {3: Fraction(1)}, 1: {1: Fraction(1)}, 0: {0: Fraction(-1)}}
    hull_m, slopes_m = differential_newton_polygon(op_mixed)
    # Airy at infinity (z = 1/x): z^5 D_z^2 + 2 z^4 D_z - 1 -> slope 3/2!
    op_airy_inf = {2: {5: Fraction(1)}, 1: {4: Fraction(2)}, 0: {0: Fraction(-1)}}
    hull_a, slopes_a = differential_newton_polygon(op_airy_inf)
    print(f"Newton Polygon Bessel(x=0): hull={hull_b}, slopes={slopes_b} (Fuchsian={all(s <= 0 for s in slopes_b)})")
    print(
        f"Newton Polygon Mixed(x=0): hull={hull_m}, slopes={slopes_m}; Airy(inf): hull={hull_a}, Katz slope={slopes_a}")

    # 4. D-Finite Guessing (Differential & Recurrence Pade)
    # 4a. Recover LCLM(Dx - 1, Dx^2 + 1) = D^3 - D^2 + D - 1 purely from Taylor jet of exp(x) + cos(x)
    exp_cos_series = [
        Fraction(1, math.factorial(k)) + (Fraction((-1) ** (k // 2), math.factorial(k)) if k % 2 == 0 else Fraction(0))
        for k in range(10)
    ]
    guessed_exp_cos = guess_diff_ore(exp_cos_series, max_order=4, max_poly_deg=1)
    expected_exp_cos = {3: {0: Fraction(1)}, 2: {0: Fraction(-1)}, 1: {0: Fraction(1)}, 0: {0: Fraction(-1)}}
    print(f"D-Finite Guessing exp(x)+cos(x) -> {guessed_exp_cos} (matches LCLM: {guessed_exp_cos == expected_exp_cos})")

    # 4b. Recover Catalan ODE from Taylor coefficients of C(x) = (1 - sqrt(1 - 4x))/(2x)
    cat_series = [Fraction(math.comb(2 * n, n), n + 1) for n in range(12)]
    guessed_cat_ode = guess_diff_ore(cat_series, max_order=2, max_poly_deg=2)
    # Verify guessed ODE annihilates Catalan series through x^9!
    assert guessed_cat_ode is not None
    cat_poly = dict(enumerate(cat_series))
    res_cat: UniPoly = {}
    for k, pk in guessed_cat_ode.items():
        dk = dict(cat_poly)
        for _ in range(k):
            dk = poly_diff(dk)
        res_cat = poly_add(res_cat, poly_mul(pk, dk))
    res_cat_trunc = {deg: val for deg, val in res_cat.items() if deg <= 9}

    # 4c. Recover Catalan Shift Recurrence (n + 2) S_n - (4n + 2) from first 8 Catalan numbers!
    guessed_cat_rec = guess_shift_ore(cat_series[:8], max_order=2, max_poly_deg=2)
    assert guessed_cat_rec is not None
    # Predict C_8 and C_9 using the guessed recurrence!
    p0, p1 = guessed_cat_rec[0], guessed_cat_rec[1]
    c8_pred = -(poly_eval(p0, Fraction(7)) * cat_series[7]) / poly_eval(p1, Fraction(7))
    c9_pred = -(poly_eval(p0, Fraction(8)) * c8_pred) / poly_eval(p1, Fraction(8))
    print(f"D-Finite Catalan ODE guessed={guessed_cat_ode}, residual<=x^9==0: {not res_cat_trunc}")
    print(
        f"Recurrence Catalan guessed={guessed_cat_rec},"
        f" predicts C_8={c8_pred} (actual {cat_series[8]}),"
        f" C_9={c9_pred} (actual {cat_series[9]})")
    print()


# =============================================================================
# Experiment 10: Algebraic Hamiltonian Mechanics (Poisson, Legendre, Weyl & Jets)
# =============================================================================

MPoly = dict[tuple[int, ...], Fraction]


class CanonicalPoissonAlgebra:
    """Canonical phase-space Poisson algebra Q[q_1..q_m, p_1..p_m] (EP-0204 / EP-0220)."""

    def __init__(self, n_dof: int) -> None:
        self.m = n_dof
        self.n_vars = 2 * n_dof

    def var(self, idx: int) -> MPoly:
        exp = [0] * self.n_vars
        exp[idx] = 1
        return {tuple(exp): Fraction(1)}

    def q(self, i: int) -> MPoly:
        return self.var(i)

    def p(self, i: int) -> MPoly:
        return self.var(self.m + i)

    @staticmethod
    def add(a: MPoly, b: MPoly) -> MPoly:
        out = dict(a)
        for k, v in b.items():
            nv = out.get(k, Fraction(0)) + v
            if nv == 0:
                out.pop(k, None)
            else:
                out[k] = nv
        return out

    @staticmethod
    def sub(a: MPoly, b: MPoly) -> MPoly:
        return CanonicalPoissonAlgebra.add(a, {k: -v for k, v in b.items()})

    @staticmethod
    def scale(c: Fraction, a: MPoly) -> MPoly:
        if c == 0:
            return {}
        return {k: c * v for k, v in a.items() if c * v != 0}

    def mul(self, a: MPoly, b: MPoly) -> MPoly:
        out: MPoly = {}
        n = self.n_vars
        for ma, va in a.items():
            for mb, vb in b.items():
                mc = tuple(ma[i] + mb[i] for i in range(n))
                nv = out.get(mc, Fraction(0)) + va * vb
                if nv == 0:
                    out.pop(mc, None)
                else:
                    out[mc] = nv
        return out

    def diff(self, a: MPoly, idx: int) -> MPoly:
        out: MPoly = {}
        for m, v in a.items():
            if m[idx] > 0:
                nm = list(m)
                nm[idx] -= 1
                key = tuple(nm)
                nv = out.get(key, Fraction(0)) + v * Fraction(m[idx])
                if nv == 0:
                    out.pop(key, None)
                else:
                    out[key] = nv
        return out

    def poisson_bracket(self, f: MPoly, g: MPoly) -> MPoly:
        """Canonical symplectic bracket {f, g} = sum_i (df/dq_i dg/dp_i - df/dp_i dg/dq_i)."""
        out: MPoly = {}
        for i in range(self.m):
            term1 = self.mul(self.diff(f, i), self.diff(g, self.m + i))
            term2 = self.mul(self.diff(f, self.m + i), self.diff(g, i))
            out = self.add(out, self.sub(term1, term2))
        return out

    def hamiltonian_derivation(self, h: MPoly) -> Callable[[MPoly], MPoly]:
        """Return Hamiltonian vector field X_H(f) = {f, H} (a HasDerivation on phase space)."""
        return lambda f: self.poisson_bracket(f, h)

    def is_first_integral(self, invariant: MPoly, h: MPoly) -> bool:
        """Certify exact conservation law {I, H} == 0."""
        return not self.poisson_bracket(invariant, h)


def invert_fraction_matrix(mat: list[list[Fraction]]) -> list[list[Fraction]] | None:
    """Exact Gauss-Jordan matrix inversion over Q; returns None when singular."""
    n = len(mat)
    aug = [list(mat[i]) + [Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]
    for col in range(n):
        piv = next((r for r in range(col, n) if aug[r][col] != 0), None)
        if piv is None:
            return None
        aug[col], aug[piv] = aug[piv], aug[col]
        pv = aug[col][col]
        aug[col] = [v / pv for v in aug[col]]
        for r in range(n):
            if r != col and aug[r][col] != 0:
                fac = aug[r][col]
                aug[r] = [aug[r][c] - fac * aug[col][c] for c in range(2 * n)]
    return [row[n:] for row in aug]


def legendre_transform_quadratic(
        alg: CanonicalPoissonAlgebra,
        expr: MPoly,
        forward: bool = True,
) -> MPoly:
    """Exact algebraic Legendre transform between regular quadratic L(q, qdot) and H(q, p).

    Variables are ordered (q_0..q_{m-1}, v_0..v_{m-1}) where v_i is qdot_i (forward=True)
    or p_i (forward=False). Supports L = 1/2 v^T M v + b(q)^T v - V(q) with constant
    invertible Hessian M in GL_m(Q). Rejects singular Hessians (det M == 0).
    """
    m = alg.m
    n = alg.n_vars
    # Check at most quadratic in velocity/momentum vars and build Hessian M_ij = d^2 expr / dv_i dv_j
    hessian: list[list[Fraction]] = [[Fraction(0)] * m for _ in range(m)]
    for mon, coeff in expr.items():
        vel_deg = sum(mon[m:])
        if vel_deg > 2:
            raise ValueError("Legendre transform requires quadratic velocity/momentum dependence.")
    for i in range(m):
        di = alg.diff(expr, m + i)
        for j in range(m):
            dij = alg.diff(di, m + j)
            if any(any(exp != 0 for exp in mon) for mon in dij):
                raise ValueError("Non-constant velocity Hessian in prototype Legendre transform.")
            hessian[i][j] = dij.get((0,) * n, Fraction(0))

    inv_hess = invert_fraction_matrix(hessian)
    if inv_hess is None:
        raise ValueError("Singular Lagrangian/Hamiltonian Hessian (det M == 0); Dirac constraints required.")

    # Linear coefficient vector B_i(q) = (d expr / dv_i)|_{v=0}
    b_vec: list[MPoly] = []
    for i in range(m):
        di = alg.diff(expr, m + i)
        b_vec.append({mon: val for mon, val in di.items() if sum(mon[m:]) == 0})
    # Pure coordinate term C(q) = expr|_{v=0}
    c_q: MPoly = {mon: val for mon, val in expr.items() if sum(mon[m:]) == 0}

    # Dual variables u_i = p_i (or qdot_i): solve M v = u - B(q) => v_i = sum_j M^{-1}_{ij} (u_j - B_j(q))
    rhs_u = [alg.sub(alg.var(m + j), b_vec[j]) for j in range(m)]
    v_of_u: list[MPoly] = []
    for i in range(m):
        vi: MPoly = {}
        for j in range(m):
            vi = alg.add(vi, alg.scale(inv_hess[i][j], rhs_u[j]))
        v_of_u.append(vi)

    # Evaluate quadratic form 1/2 v^T M v + B^T v + C(q) and subtract from sum_i u_i v_i
    # Since B^T v + 1/2 v^T M v and sum u_i v_i = (M v + B)^T v, dual = 1/2 v^T M v - C(q)
    # Wait: compute explicitly via substitution sum_i u_i v_i - expr(q, v(u)) to guarantee 100% generality!
    uv_dot: MPoly = {}
    for i in range(m):
        uv_dot = alg.add(uv_dot, alg.mul(alg.var(m + i), v_of_u[i]))

    # Direct polynomial substitution of v_i -> v_of_u[i] into expr
    subst_expr: MPoly = dict(c_q)
    for i in range(m):
        subst_expr = alg.add(subst_expr, alg.mul(b_vec[i], v_of_u[i]))
    for i in range(m):
        for j in range(m):
            if hessian[i][j] != 0:
                term = alg.scale(Fraction(1, 2) * hessian[i][j], alg.mul(v_of_u[i], v_of_u[j]))
                subst_expr = alg.add(subst_expr, term)

    _ = forward
    return alg.sub(uv_dot, subst_expr)


def jet_mul(a: UniPoly, b: UniPoly, order: int) -> UniPoly:
    out: dict[int, Fraction] = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            k = ka + kb
            if k <= order:
                out[k] = out.get(k, Fraction(0)) + va * vb
    return poly_clean(out)


def jet_integrate(a: UniPoly, c0: Fraction, order: int) -> UniPoly:
    out: UniPoly = {}
    if c0 != 0:
        out[0] = c0
    for k, v in a.items():
        if k + 1 <= order:
            out[k + 1] = v / Fraction(k + 1)
    return out


def eval_mpoly_in_jets(poly: MPoly, coords: list[UniPoly], order: int) -> UniPoly:
    out: UniPoly = {}
    for mon, coeff in poly.items():
        term: UniPoly = {0: coeff}
        for var_idx, exp in enumerate(mon):
            for _ in range(exp):
                term = jet_mul(term, coords[var_idx], order)
        out = poly_add(out, term)
    return out


def solve_hamiltonian_jet(
        alg: CanonicalPoissonAlgebra,
        hamiltonian: MPoly,
        q0: list[Fraction],
        p0: list[Fraction],
        order: int,
) -> tuple[list[UniPoly], list[UniPoly]]:
    """Solve Hamilton's equations qdot = dH/dp, pdot = -dH/dq exactly mod t^{order+1} via Picard iteration."""
    m = alg.m
    dq_rhs = [alg.diff(hamiltonian, m + i) for i in range(m)]
    dp_rhs = [alg.scale(Fraction(-1), alg.diff(hamiltonian, i)) for i in range(m)]

    q_jets: list[UniPoly] = [{0: v} if v != 0 else {} for v in q0]
    p_jets: list[UniPoly] = [{0: v} if v != 0 else {} for v in p0]
    for step in range(1, order + 1):
        state = q_jets + p_jets
        q_jets = [jet_integrate(eval_mpoly_in_jets(dq_rhs[i], state, step), q0[i], step) for i in range(m)]
        p_jets = [jet_integrate(eval_mpoly_in_jets(dp_rhs[i], state, step), p0[i], step) for i in range(m)]
    return q_jets, p_jets


def run_experiment_10() -> None:
    print("=" * 80)
    print("EXPERIMENT 10: HAMILTONIAN MECHANICS (POISSON, LEGENDRE, WEYL & SYMPLECTIC JETS)")
    print("=" * 80)

    # 1. CanonicalPoissonAlgebra (2 DOF): Poisson laws, Hamiltonian derivation X_H & Noether L_z conservation
    pa2 = CanonicalPoissonAlgebra(n_dof=2)
    q0, q1, p0, p1 = pa2.q(0), pa2.q(1), pa2.p(0), pa2.p(1)
    half = Fraction(1, 2)
    h_2d = pa2.scale(
        half,
        pa2.add(
            pa2.add(pa2.mul(p0, p0), pa2.mul(p1, p1)),
            pa2.add(pa2.mul(q0, q0), pa2.mul(q1, q1)),
        ),
    )
    # Angular momentum L_z = q_0 p_1 - q_1 p_0 -> conserved {L_z, H} == 0!
    l_z = pa2.sub(pa2.mul(q0, p1), pa2.mul(q1, p0))
    lz_conserved = pa2.is_first_integral(l_z, h_2d)

    # Verify Poisson Leibniz & Jacobi + Lie homomorphism [X_F, X_G](K) == -X_{F,G}(K)
    f_test = pa2.add(pa2.mul(q0, pa2.mul(q0, p1)), p0)
    g_test = pa2.add(pa2.mul(q1, p0), pa2.mul(p1, p1))
    k_test = pa2.add(pa2.mul(q0, p0), q1)
    jac = pa2.add(
        pa2.add(
            pa2.poisson_bracket(f_test, pa2.poisson_bracket(g_test, k_test)),
            pa2.poisson_bracket(g_test, pa2.poisson_bracket(k_test, f_test)),
        ),
        pa2.poisson_bracket(k_test, pa2.poisson_bracket(f_test, g_test)),
    )
    leib = pa2.sub(
        pa2.poisson_bracket(f_test, pa2.mul(g_test, k_test)),
        pa2.add(pa2.mul(pa2.poisson_bracket(f_test, g_test), k_test),
                pa2.mul(g_test, pa2.poisson_bracket(f_test, k_test))),
    )
    xf = pa2.hamiltonian_derivation(f_test)
    xg = pa2.hamiltonian_derivation(g_test)
    xfg = pa2.hamiltonian_derivation(pa2.poisson_bracket(f_test, g_test))
    lie_hom_ok = pa2.sub(xf(xg(k_test)), xg(xf(k_test))) == pa2.scale(Fraction(-1), xfg(k_test))
    print(f"2D Oscillator Noether Integral {{L_z, H}} == 0: {lz_conserved}")
    print(
        f"Poisson Jacobi == 0: {jac == {} }, Leibniz == 0: {leib == {} },"
        f" Lie Hom [X_F, X_G] == -X_{{F,G}}: {lie_hom_ok}")

    # 2. Algebraic Legendre Transform: L(q, qdot) <-> H(q, p) & Euler-Lagrange consistency
    # 2a. Coupled 2-DOF Lagrangian with non-diagonal mass matrix M = [[1, 1], [1, 3]]
    lag_2d = pa2.sub(
        pa2.add(
            pa2.scale(half, pa2.mul(p0, p0)),
            pa2.add(pa2.mul(p0, p1), pa2.scale(Fraction(3, 2), pa2.mul(p1, p1))),
        ),
        pa2.scale(half, pa2.add(pa2.mul(q0, q0), pa2.mul(q1, q1))),
    )
    ham_2d = legendre_transform_quadratic(pa2, lag_2d, forward=True)
    lag_back = legendre_transform_quadratic(pa2, ham_2d, forward=False)
    # Inverse of [[1, 1], [1, 3]] is [[3/2, -1/2], [-1/2, 1/2]] -> T(p) = 3/4 p0^2 - 1/2 p0 p1 + 1/4 p1^2
    expected_ham_2d = pa2.add(
        pa2.add(
            pa2.scale(Fraction(3, 4), pa2.mul(p0, p0)),
            pa2.sub(pa2.scale(Fraction(1, 4), pa2.mul(p1, p1)), pa2.scale(half, pa2.mul(p0, p1))),
        ),
        pa2.scale(half, pa2.add(pa2.mul(q0, q0), pa2.mul(q1, q1))),
    )
    # Singular Chern-Simons-like Lagrangian L = q0*qdot1 - q1*qdot0 has det M == 0 -> must reject!
    lag_singular = pa2.sub(pa2.mul(q0, p1), pa2.mul(q1, p0))
    singular_rejected = False
    try:
        legendre_transform_quadratic(pa2, lag_singular, forward=True)
    except ValueError:
        singular_rejected = True
    print(f"Coupled 2-DOF Legendre L -> H -> L involution: {ham_2d == expected_ham_2d and lag_back == lag_2d}")
    print(f"Singular Lagrangian (det M == 0) rejected: {singular_rejected}")

    # 2b. 1-DOF Anharmonic Oscillator: DifferentialPolynomialRing EL vs Hamilton X_H
    pa1 = CanonicalPoissonAlgebra(n_dof=1)
    q, p = pa1.q(0), pa1.p(0)
    # L = 1/2 qdot^2 - 1/2 q^2 - 1/4 q^4
    q4 = pa1.mul(pa1.mul(q, q), pa1.mul(q, q))
    lag_anh = pa1.sub(pa1.scale(half, pa1.mul(p, p)),
                      pa1.add(pa1.scale(half, pa1.mul(q, q)), pa1.scale(Fraction(1, 4), q4)))
    ham_anh = legendre_transform_quadratic(pa1, lag_anh, forward=True)
    dp_dt_ham = pa1.poisson_bracket(p, ham_anh)  # -q - q^3
    dring = DifferentialPolynomialRing()
    u0, u1 = dring.var(0), dring.var(1)
    u0_4 = dring.mul(dring.mul(u0, u0), dring.mul(u0, u0))
    lag_jet = dring.sub(
        {m: half * v for m, v in dring.mul(u1, u1).items()},
        dring.add({m: half * v for m, v in dring.mul(u0, u0).items()},
                  {m: Fraction(1, 4) * v for m, v in u0_4.items()}),
    )
    el_anh = dring.euler_lagrange(lag_jet)  # -u'' - u - u^3
    u2 = dring.var(2)
    el_minus_ham = dring.sub(el_anh, dring.sub(dring.sub({}, u2), dring.add(u0, dring.mul(u0, dring.mul(u0, u0)))))
    print(f"Anharmonic EL(L) == -(u'' + u + u^3) matching Hamilton dp/dt={dp_dt_ham}: {el_minus_ham == {} }")

    # 3. Weyl <-> Poisson Quantization / Ehrenfest Principal-Symbol Correspondence
    weyl2 = WeylAlgebra(StandardField(Fraction), n_vars=2)
    x0, x1, d0, d1 = weyl2.x(0), weyl2.x(1), weyl2.d(0), weyl2.d(1)
    # Quantum 2D oscillator & angular momentum: [L_hat, H_hat] == 0
    h_hat = weyl2.add(
        weyl2.add(weyl2.mul(d0, d0), weyl2.mul(d1, d1)),
        weyl2.add(weyl2.mul(x0, x0), weyl2.mul(x1, x1)),
    )
    lz_hat = weyl2.sub(weyl2.mul(x0, d1), weyl2.mul(x1, d0))
    quantum_lz_commutes = not weyl2.commutator(lz_hat, h_hat)

    # Non-trivial Ehrenfest principal-symbol check: sigma_top([A, B]) == -{sigma_top(A), sigma_top(B)}_{q,p}
    # ([d_i, x_i] = +1 while {p_i, q_i} = -1, so sigma_top([A,B]) == -{sigma_top(A), sigma_top(B)}_{q,p})
    a_hat = weyl2.add(weyl2.mul(weyl2.mul(x0, x0), d1), weyl2.mul(x1, weyl2.mul(d0, d0)))
    b_hat = weyl2.add(weyl2.mul(x0, weyl2.mul(d0, d1)), weyl2.mul(weyl2.mul(x1, x1), d0))
    comm_ab = weyl2.commutator(a_hat, b_hat)

    def bernstein_top_symbol(op: WeylPoly[Fraction]) -> MPoly:
        """Convert Weyl operator's Bernstein top-total-degree symbol (x^alpha d^beta -> q^alpha p^beta)."""
        max_tot = max((sum(m[0]) + sum(m[1]) for m in op), default=-1)
        return {m[0] + m[1]: v for m, v in op.items() if sum(m[0]) + sum(m[1]) == max_tot}

    sym_a = bernstein_top_symbol(a_hat)
    sym_b = bernstein_top_symbol(b_hat)
    ehrenfest_ok = bernstein_top_symbol(comm_ab) == pa2.scale(Fraction(-1), pa2.poisson_bracket(sym_a, sym_b))
    print(
        f"Weyl 2D Quantum [L_z, H] == 0: {quantum_lz_commutes},"
        f" Ehrenfest sigma_top([A,B]) == -{{sigma_top(A),sigma_top(B)}}: {ehrenfest_ok}")

    # 4. Exact Energy Conservation & Symplectic Jacobian in Taylor Jets (Anharmonic Oscillator)
    order = 10
    q_sol, p_sol = solve_hamiltonian_jet(pa1, ham_anh, [Fraction(1)], [Fraction(0)], order=order)
    energy_jet = eval_mpoly_in_jets(ham_anh, [q_sol[0], p_sol[0]], order=order)
    energy_conserved = energy_jet == {0: Fraction(3, 4)}

    # Variational symplectic Jacobian M(t) = D Phi_t solving dM/dt = A(t) M(t), M(0) = I_2
    # A(t) = [[0, 1], [-(1 + 3 q(t)^2), 0]]
    q_sq = jet_mul(q_sol[0], q_sol[0], order)
    a21 = poly_sub({0: Fraction(-1)}, {k: Fraction(3) * v for k, v in q_sq.items()})
    # Columns c=0,1: (dq, dp)
    m_cols: list[tuple[UniPoly, UniPoly]] = [({0: Fraction(1)}, {}), ({}, {0: Fraction(1)})]
    for step in range(1, order + 1):
        new_cols: list[tuple[UniPoly, UniPoly]] = []
        for c_idx, (c_q, c_p) in enumerate(m_cols):
            init_q = Fraction(1 if c_idx == 0 else 0)
            init_p = Fraction(1 if c_idx == 1 else 0)
            nq = jet_integrate(c_p, init_q, step)
            np_ = jet_integrate(jet_mul(a21, c_q, step), init_p, step)
            new_cols.append((nq, np_))
        m_cols = new_cols

    # Symplectic condition M^T J M == J <=> det(M(t)) = m00*m11 - m01*m10 == 1 mod t^{order+1}!
    det_m = poly_sub(jet_mul(m_cols[0][0], m_cols[1][1], order), jet_mul(m_cols[1][0], m_cols[0][1], order))
    symplectic_ok = det_m == {0: Fraction(1)}

    # Cross-check q(t), p(t) ODE residual mod t^{order} via SymPy .removeO()
    t_sym = sp.Symbol("t")
    q_poly_sym = poly_to_sympy(q_sol[0], t_sym)
    p_poly_sym = poly_to_sympy(p_sol[0], t_sym)
    dq_res = sp.series(sp.diff(q_poly_sym, t_sym) - p_poly_sym, t_sym, 0, order).removeO()
    dp_res = sp.series(sp.diff(p_poly_sym, t_sym) + q_poly_sym + q_poly_sym ** 3, t_sym, 0, order).removeO()
    sympy_ham_ok = dq_res == 0 and dp_res == 0
    print(f"Anharmonic Taylor Jet (mod t^{order + 1}) exact energy H(q(t),p(t))==3/4: {energy_conserved}")
    print(
        f"Symplectic Jacobian M(t)^T J M(t) == J (det D Phi_t == 1 mod t^{order + 1}):"
        f" {symplectic_ok}, SymPy ODE residual==0: {sympy_ham_ok}")
    print()


# =============================================================================
# Experiment 11: Algebraic de Rham Complex, Exterior Derivative & Cartan Calculus
# =============================================================================

Blade = tuple[int, ...]  # Strictly sorted indices 0 <= i_0 < ... < i_{k-1} < n_vars
DiffFormKey = tuple[Monomial, Blade]
DiffForm = dict[DiffFormKey, Fraction]


def wedge_blades(b1: Blade, b2: Blade) -> tuple[Blade, int] | None:
    """Multiply basis blades dx^b1 ^ dx^b2; returns (sorted_blade, sign) or None if overlapping."""
    if not b1:
        return b2, 1
    if not b2:
        return b1, 1
    if set(b1) & set(b2):
        return None
    seq = list(b1) + list(b2)
    swaps = 0
    for i in range(1, len(seq)):
        key = seq[i]
        j = i - 1
        while j >= 0 and seq[j] > key:
            seq[j + 1] = seq[j]
            swaps += 1
            j -= 1
        seq[j + 1] = key
    return tuple(seq), (-1 if swaps % 2 else 1)


class AlgebraicDeRhamComplex:
    r"""Unboxed graded differential algebra
     $\Omega^\bullet = \mathbb{Q}[x_0,\dots,x_{n-1}] \otimes \bigwedge^\bullet(dx_i)$.

    Carrier:
        `dict[tuple[Monomial, Blade], Fraction]` with sorted Grassmann blades (`tuple[int, ...]`).
    """

    def __init__(self, n_vars: int) -> None:
        self.n_vars = n_vars

    def form0(self, poly: MPoly) -> DiffForm:
        return {(m, ()): v for m, v in poly.items() if v != 0}

    def dx(self, idx: int) -> DiffForm:
        return {((0,) * self.n_vars, (idx,)): Fraction(1)}

    def var(self, idx: int) -> MPoly:
        exp = [0] * self.n_vars
        exp[idx] = 1
        return {tuple(exp): Fraction(1)}

    @staticmethod
    def add(a: DiffForm, b: DiffForm) -> DiffForm:
        out = dict(a)
        for k, v in b.items():
            nv = out.get(k, Fraction(0)) + v
            if nv == 0:
                out.pop(k, None)
            else:
                out[k] = nv
        return out

    @staticmethod
    def sub(a: DiffForm, b: DiffForm) -> DiffForm:
        return AlgebraicDeRhamComplex.add(a, {k: -v for k, v in b.items()})

    @staticmethod
    def scale(c: Fraction, a: DiffForm) -> DiffForm:
        if c == 0:
            return {}
        return {k: c * v for k, v in a.items() if c * v != 0}

    def wedge(self, a: DiffForm, b: DiffForm) -> DiffForm:
        out: DiffForm = {}
        n = self.n_vars
        for (ma, ba), va in a.items():
            for (mb, bb), vb in b.items():
                wb = wedge_blades(ba, bb)
                if wb is None:
                    continue
                blade, sign = wb
                mc = tuple(ma[i] + mb[i] for i in range(n))
                key = (mc, blade)
                nv = out.get(key, Fraction(0)) + Fraction(sign) * va * vb
                if nv == 0:
                    out.pop(key, None)
                else:
                    out[key] = nv
        return out

    def exterior_derivative(self, alpha: DiffForm) -> DiffForm:
        r"""Graded exterior derivative $d_k: \Omega^k \to \Omega^{k+1}$ satisfying $d^2 = 0$ and graded Leibniz."""
        out: DiffForm = {}
        n = self.n_vars
        for (mon, blade), val in alpha.items():
            for j in range(n):
                if mon[j] == 0:
                    continue
                wb = wedge_blades((j,), blade)
                if wb is None:
                    continue
                new_blade, sign = wb
                nm = list(mon)
                nm[j] -= 1
                key = (tuple(nm), new_blade)
                nv = out.get(key, Fraction(0)) + Fraction(sign * mon[j]) * val
                if nv == 0:
                    out.pop(key, None)
                else:
                    out[key] = nv
        return out

    def interior_product(self, vec_field: list[MPoly], alpha: DiffForm) -> DiffForm:
        r"""Interior contraction $\iota_X: \Omega^k \to \Omega^{k-1}$ for vector field $X = \sum_j X_j \partial_j$."""
        if len(vec_field) != self.n_vars:
            raise ValueError("Vector field dimension mismatch.")
        out: DiffForm = {}
        n = self.n_vars
        for (mon, blade), val in alpha.items():
            if not blade:
                continue
            for pos, j in enumerate(blade):
                xj = vec_field[j]
                if not xj:
                    continue
                sub_blade = blade[:pos] + blade[pos + 1:]
                sign = Fraction(-1 if pos % 2 else 1)
                for xm, xv in xj.items():
                    mc = tuple(mon[idx] + xm[idx] for idx in range(n))
                    key = (mc, sub_blade)
                    nv = out.get(key, Fraction(0)) + sign * val * xv
                    if nv == 0:
                        out.pop(key, None)
                    else:
                        out[key] = nv
        return out

    def lie_derivative(self, vec_field: list[MPoly], alpha: DiffForm) -> DiffForm:
        r"""Cartan's magic formula $\mathcal{L}_X(\alpha) = d(\iota_X \alpha) + \iota_X(d\alpha)$."""
        return self.add(
            self.exterior_derivative(self.interior_product(vec_field, alpha)),
            self.interior_product(vec_field, self.exterior_derivative(alpha)),
        )

    def poincare_homotopy(self, alpha: DiffForm) -> DiffForm:
        r"""Exact algebraic Poincare chain homotopy $h_k: \Omega^k \to \Omega^{k-1}$ ($d h + h d = \mathrm{id}$)."""
        euler = [self.var(j) for j in range(self.n_vars)]
        scaled_alpha: DiffForm = {}
        for (mon, blade), val in alpha.items():
            k = len(blade)
            if k == 0:
                continue
            factor = Fraction(1, sum(mon) + k)
            scaled_alpha[(mon, blade)] = val * factor
        return self.interior_product(euler, scaled_alpha)


def run_experiment_11() -> None:
    print("=" * 80)
    print("EXPERIMENT 11: ALGEBRAIC DE RHAM COMPLEX, EXTERIOR DERIVATIVE & CARTAN CALCULUS")
    print("=" * 80)

    # 1. Graded Algebra, Nilpotency d^2 == 0 & Graded Leibniz Rule in 3D (x, y, z)
    dr3 = AlgebraicDeRhamComplex(n_vars=3)
    pa3_alg = CanonicalPoissonAlgebra(n_dof=1)  # reuse static MPoly helpers or use dr3 directly
    _ = pa3_alg
    x, y, z = dr3.var(0), dr3.var(1), dr3.var(2)
    dx, dy, dz = dr3.dx(0), dr3.dx(1), dr3.dx(2)

    def mpoly_mul3(a: MPoly, b: MPoly) -> MPoly:
        out: MPoly = {}
        for ma, va in a.items():
            for mb, vb in b.items():
                mc = (ma[0] + mb[0], ma[1] + mb[1], ma[2] + mb[2])
                nv = out.get(mc, Fraction(0)) + va * vb
                if nv == 0:
                    out.pop(mc, None)
                else:
                    out[mc] = nv
        return out

    def mpoly_add3(a: MPoly, b: MPoly) -> MPoly:
        out = dict(a)
        for k, v in b.items():
            nv = out.get(k, Fraction(0)) + v
            if nv == 0:
                out.pop(k, None)
            else:
                out[k] = nv
        return out

    # Non-trivial 1-form alpha = (x^2 y) dx + (y z^2) dy + (x z) dz
    alpha1 = dr3.add(
        dr3.wedge(dr3.form0(mpoly_mul3(mpoly_mul3(x, x), y)), dx),
        dr3.add(
            dr3.wedge(dr3.form0(mpoly_mul3(y, mpoly_mul3(z, z))), dy),
            dr3.wedge(dr3.form0(mpoly_mul3(x, z)), dz),
        ),
    )
    # Non-trivial 1-form beta1 and 2-form beta2 = d(alpha1) + (x + y) dx ^ dz
    beta1 = dr3.add(
        dr3.wedge(dr3.form0(mpoly_add3(x, z)), dy),
        dr3.wedge(dr3.form0(mpoly_mul3(x, y)), dz),
    )
    d_alpha1 = dr3.exterior_derivative(alpha1)
    d2_alpha1 = dr3.exterior_derivative(d_alpha1)  # curl(grad) / d^2 == 0!
    # Graded Leibniz on p=1 form: d(alpha1 ^ beta1) == d(alpha1)^beta1 - alpha1^d(beta1)
    d_wedge_lhs = dr3.exterior_derivative(dr3.wedge(alpha1, beta1))
    d_wedge_rhs = dr3.sub(
        dr3.wedge(dr3.exterior_derivative(alpha1), beta1),
        dr3.wedge(alpha1, dr3.exterior_derivative(beta1)),
    )
    graded_comm_ok = dr3.wedge(alpha1, beta1) == dr3.scale(Fraction(-1), dr3.wedge(beta1, alpha1))
    print(f"3D Exterior Derivative nilpotency d(d(alpha1)) == 0: {d2_alpha1 == {} }")
    print(
        f"Graded commutativity a^b == -b^a: {graded_comm_ok},"
        f" Graded Leibniz d(a^b)==da^b - a^db: {d_wedge_lhs == d_wedge_rhs}")

    # 2. Exact Poincare Chain Homotopy (d o h + h o d == id) & Potential Recovery
    # 2a. General non-closed 2-form test
    nonclosed_2form = dr3.add(
        dr3.wedge(dr3.form0(mpoly_mul3(x, mpoly_mul3(y, z))), dr3.wedge(dx, dy)),
        dr3.wedge(dr3.form0(mpoly_add3(mpoly_mul3(x, x), z)), dr3.wedge(dy, dz)),
    )
    homotopy_check = dr3.add(
        dr3.exterior_derivative(dr3.poincare_homotopy(nonclosed_2form)),
        dr3.poincare_homotopy(dr3.exterior_derivative(nonclosed_2form)),
    )
    # 2b. Constructive vector potential recovery: B = d(alpha1) is closed (dB == 0) -> A_rec = h(B) obeys d(A_rec) == B!
    a_rec = dr3.poincare_homotopy(d_alpha1)
    vec_potential_ok = dr3.exterior_derivative(a_rec) == d_alpha1
    # 2c. Constructive scalar potential recovery: phi = x^2 y z + 3 y^2 - z -> F = d(phi) -> h(F) recovers phi!
    phi_poly = mpoly_add3(mpoly_mul3(mpoly_mul3(x, x), mpoly_mul3(y, z)),
                          mpoly_mul3({(0, 0, 0): Fraction(3)}, mpoly_mul3(y, y)))
    phi0 = dr3.form0(phi_poly)
    grad_phi = dr3.exterior_derivative(phi0)
    phi_rec = dr3.poincare_homotopy(grad_phi)
    scalar_potential_ok = phi_rec == phi0 and dr3.exterior_derivative(phi_rec) == grad_phi
    print(f"Poincare homotopy (d h + h d)(omega2) == omega2: {homotopy_check == nonclosed_2form}")
    print(
        f"Constructive potentials: curl-free scalar phi recovered={scalar_potential_ok},"
        f" div-free vector potential B=d(A_rec)={vec_potential_ok}")

    # 3. Symplectic Cartan-Liouville Bridge on 4D Phase Space (Henon-Heiles Hamiltonian)
    pa2 = CanonicalPoissonAlgebra(n_dof=2)
    dr4 = AlgebraicDeRhamComplex(n_vars=4)
    q0, q1, p0, p1 = pa2.q(0), pa2.q(1), pa2.p(0), pa2.p(1)
    half = Fraction(1, 2)
    # H = 1/2(p0^2 + p1^2 + q0^2 + q1^2) + q0^2*q1 - 1/3 q1^3
    hh_ham = pa2.add(
        pa2.scale(half, pa2.add(pa2.add(pa2.mul(p0, p0), pa2.mul(p1, p1)), pa2.add(pa2.mul(q0, q0), pa2.mul(q1, q1)))),
        pa2.sub(pa2.mul(pa2.mul(q0, q0), q1), pa2.scale(Fraction(1, 3), pa2.mul(q1, pa2.mul(q1, q1)))),
    )
    # Canonical symplectic 2-form omega = dq0 ^ dp0 + dq1 ^ dp1
    omega = dr4.add(dr4.wedge(dr4.dx(0), dr4.dx(2)), dr4.wedge(dr4.dx(1), dr4.dx(3)))
    omega_closed = dr4.exterior_derivative(omega) == {}
    # Hamiltonian vector field X_H = (dH/dp0, dH/dp1, -dH/dq0, -dH/dq1)
    x_h = [
        pa2.diff(hh_ham, 2),
        pa2.diff(hh_ham, 3),
        pa2.scale(Fraction(-1), pa2.diff(hh_ham, 0)),
        pa2.scale(Fraction(-1), pa2.diff(hh_ham, 1))
    ]
    ix_omega = dr4.interior_product(x_h, omega)
    d_ham = dr4.exterior_derivative(dr4.form0(hh_ham))
    cartan_hamilton_ok = ix_omega == d_ham  # i_{X_H}(omega) == dH!
    liouville_ok = dr4.lie_derivative(x_h, omega) == {}  # L_{X_H}(omega) == 0!
    ix_squared_ok = dr4.interior_product(x_h, ix_omega) == {}  # i_X^2 == 0!
    print(f"Symplectic 2-form d(omega)==0: {omega_closed}, Cartan Hamilton i_{{X_H}}(omega)==dH: {cartan_hamilton_ok}")
    print(f"Cartan-Liouville L_{{X_H}}(omega)==0: {liouville_ok}, i_X^2==0: {ix_squared_ok}")

    # 4. Kahler Quotient Complex Omega^bullet_{k[V]/k} on Circle V(x^2 + y^2 - 1)
    # Any 2-form dx ^ dy vanishes modulo d(x^2 + y^2 - 1) = 2x dx + 2y dy on V(x^2 + y^2 - 1):
    # Specifically, verify that (x dx + y dy) ^ (anything) reduces to 0 when dx_0 ^ dx_1 relations hold:
    # (2x dx + 2y dy) ^ (-y dx + x dy) = 2(x^2 + y^2) dx ^ dy == 2 dx ^ dy mod (x^2 + y^2 - 1)!
    dr2 = AlgebraicDeRhamComplex(n_vars=2)
    f_circle = {(2, 0): Fraction(1), (0, 2): Fraction(1), (0, 0): Fraction(-1)}
    df_circle = dr2.exterior_derivative(dr2.form0(f_circle))  # 2x dx + 2y dy
    eta_circle = dr2.add(
        dr2.wedge(dr2.form0({(0, 1): Fraction(-1)}), dr2.dx(0)),
        dr2.wedge(dr2.form0({(1, 0): Fraction(1)}), dr2.dx(1)),
    )  # -y dx + x dy
    top_wedge = dr2.wedge(df_circle, eta_circle)  # 2(x^2 + y^2) dx ^ dy
    # Modulo <x^2 + y^2 - 1>, 2(x^2 + y^2) dx^dy - 2(x^2 + y^2 - 1) dx^dy == 2 dx^dy
    circle_rel = dr2.wedge(dr2.form0(f_circle), dr2.scale(Fraction(2), dr2.wedge(dr2.dx(0), dr2.dx(1))))
    kahler_2form_match = dr2.sub(top_wedge, circle_rel) == dr2.scale(Fraction(2), dr2.wedge(dr2.dx(0), dr2.dx(1)))
    print(f"Kahler Circle Relation df ^ (-y dx + x dy) == 2 dx^dy mod (x^2+y^2-1): {kahler_2form_match}")
    print()


if __name__ == "__main__":
    run_experiment_1()
    run_experiment_2()
    run_experiment_3()
    run_experiment_4()
    run_experiment_5()
    run_experiment_6()
    run_experiment_7()
    run_experiment_8()
    run_experiment_9()
    run_experiment_10()
    run_experiment_11()
