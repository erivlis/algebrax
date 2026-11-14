# %%
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Zero-Drift Computing: Shamir Secret Sharing, Exact Rationals & Taylor Quotients
#
# ## Eliminating Roundoff & Encoding Secrets via Phase 6 Fields, Ideals & Quotients
# This recipe combines **Phase 1 Sparse Linear Solvers** (`algebrax.matrix`) with **Phase 6 Exact Fields,
# Ideals & Quotient Rings** (`algebrax.algebra`) across three high-value engineering applications:
#
# 1. **Ill-Conditioned Rational Linear Systems (`StandardField(Fraction)`)**: Contrasts IEEE-754 float error
#    on a $6 \times 6$ Hilbert matrix ($\kappa \approx 1.5 \times 10^7$) against exact $\mathbb{Q}$ solving.
# 2. **Shamir $(k, n)$ Threshold Secret Sharing (`ModularField(p)`)**: Splits a master secret across $n=5$ servers
#    so that *any* $k=3$ shares recover the secret via finite-field Vandermonde solving, while $k-1$ reveal nothing.
# 3. **Truncated Taylor Series Algebra via Ideals (`PolynomialTruncationIdeal`, `QuotientRing`)**: Solves polynomial
#    series inversion $\frac{1}{1 - x}$ and $\exp(x)$ canonically in $\mathbb{Q}[x]/(x^6)$.

# %%
from __future__ import annotations

from fractions import Fraction

import algebrax as ax
from algebrax.algebra import (
    ModularField,
    PolynomialAlgebra,
    PolynomialTruncationIdeal,
    QuotientRing,
    StandardField,
)
from algebrax.verification import verify_field_laws, verify_quotient_ring_laws

# %% [markdown]
# ## 1. Ill-Conditioned Linear Systems: IEEE-754 Float vs. Exact Rational $\mathbb{Q}$
#
# The $n \times n$ Hilbert matrix $H_{ij} = \frac{1}{i + j + 1}$ is notoriously ill-conditioned.
# Solving $H_6 x = H_6 x_{\text{true}}$ over `float` loses up to 7 digits of accuracy, while `StandardField(Fraction)`
# delivers bit-exact rational solutions with $\epsilon = 0$.

# %%
n_hilb = 6
q_field = StandardField(Fraction)

hilb_q = {i: {j: Fraction(1, i + j + 1) for j in range(n_hilb)} for i in range(n_hilb)}
hilb_f = {i: {j: 1.0 / (i + j + 1) for j in range(n_hilb)} for i in range(n_hilb)}

x_true_q = {i: Fraction(i + 1, 1) for i in range(n_hilb)}
rhs_q = ax.matrix.mat_vec(hilb_q, x_true_q, semiring=q_field)
rhs_f = {i: float(v) for i, v in rhs_q.items()}

x_float = ax.matrix.solve(hilb_f, rhs_f)
x_exact = ax.matrix.solve(hilb_q, rhs_q, field=q_field)

float_max_err = max(abs(x_float[i] - float(x_true_q[i])) for i in range(n_hilb))
det_exact = ax.matrix.det(hilb_q, field=q_field)

print(f'Hilbert H_6 exact det      = {det_exact} (~{float(det_exact):.3e})')
print(f'IEEE-754 max solve error   = {float_max_err:.3e}')
print(f'Exact Rational solve match = {x_exact == x_true_q}')
assert x_exact == x_true_q
assert float_max_err > 1e-10

# %% [markdown]
# ## 2. Shamir $(3, 5)$ Threshold Secret Sharing over $\mathbb{F}_{65521}$
#
# To guard a cryptographic key $S = 4219$, we encode it as the constant term of a degree-2 polynomial over
# $\mathbb{F}_{65521}$: $P(x) = S + a_1 x + a_2 x^2 \pmod{65521}$. Any 3 shares $(x_i, P(x_i))$ yield an
# invertible $3 \times 3$ Vandermonde linear system over `ModularField(65521)`.

# %%
PRIME = 65521
fp = ModularField(PRIME)
assert all(verify_field_laws(fp, [0, 1, 7, 123, 50000]).values())

SECRET = 4219
a1, a2 = 18371, 51904


def eval_shamir(x: int) -> int:
    return (SECRET + a1 * x + a2 * x * x) % PRIME


shares = [(x, eval_shamir(x)) for x in range(1, 6)]
print('\nDistributed Shamir (3, 5) Shares over F_65521:', shares)


def recover_secret(subset: list[tuple[int, int]]) -> int:
    """Recover polynomial coefficients (c0, c1, c2) via exact F_p Vandermonde solve."""
    vandermonde = {
        idx: {0: 1, 1: x_val % PRIME, 2: (x_val * x_val) % PRIME}
        for idx, (x_val, _) in enumerate(subset)
    }
    y_vec = {idx: y_val for idx, (_, y_val) in enumerate(subset)}
    coeffs = ax.matrix.solve(vandermonde, y_vec, field=fp)
    return coeffs[0]


# Verify reconstruction from disjoint 3-share quorums
quorum_a = [shares[0], shares[2], shares[4]]
quorum_b = [shares[1], shares[3], shares[4]]
rec_a = recover_secret(quorum_a)
rec_b = recover_secret(quorum_b)
print(f'Recovered from shares {quorum_a}: secret = {rec_a}')
print(f'Recovered from shares {quorum_b}: secret = {rec_b}')
assert rec_a == SECRET
assert rec_b == SECRET

# %% [markdown]
# ## 3. Truncated Taylor Series Arithmetic in $\mathbb{Q}[x] / (x^6)$
#
# By quotienting `PolynomialAlgebra(StandardField(Fraction))` by `PolynomialTruncationIdeal(6)`, monomials of
# degree $\ge 6$ vanish automatically. Let us compute exact series inverses and verify $\exp(x)\exp(-x) \equiv 1$.

# %%
poly_q = PolynomialAlgebra(q_field)
ideal_x6 = PolynomialTruncationIdeal(max_degree=6, zero_coeff=Fraction(0))
taylor_ring = QuotientRing(poly_q, ideal_x6)

# Exponential Taylor polynomials exp(x) and exp(-x) mod x^6
fact = 1
exp_pos: dict[int, Fraction] = {0: Fraction(1, 1)}
exp_neg: dict[int, Fraction] = {0: Fraction(1, 1)}
for k in range(1, 6):
    fact *= k
    exp_pos[k] = Fraction(1, fact)
    exp_neg[k] = Fraction((-1) ** k, fact)

identity_check = taylor_ring.mul(exp_pos, exp_neg)
print(f'\nexp(x) * exp(-x) mod x^6  = {identity_check}')
assert identity_check == taylor_ring.one

# Geometric series inverse: (1 - x) * (1 + x + x^2 + ... + x^5) == 1 mod x^6
one_minus_x = {0: Fraction(1), 1: Fraction(-1)}
geom_series = {k: Fraction(1) for k in range(6)}
assert taylor_ring.mul(one_minus_x, geom_series) == taylor_ring.one
print('(1 - x) * sum_{k=0..5} x^k = 1 mod x^6 verified!')

q_checks = verify_quotient_ring_laws(
    taylor_ring,
    ring_samples=[taylor_ring.zero, taylor_ring.one, one_minus_x, exp_pos],
    ideal_samples=[{6: Fraction(1)}, {7: Fraction(2)}, {8: Fraction(-3)}],
)
print('QuotientRing Q[x]/(x^6) laws:', q_checks)
assert all(q_checks.values())
