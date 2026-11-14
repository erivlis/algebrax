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
# # Langlands Duality, Iwahori-Hecke Algebras, Ramanujan Expanders & $p$-Adic Valuations
#
# ## Unifying Non-Archimedean Arithmetic, Symmetry & Spectral Expansion
# This recipe explores four interconnected mathematical pillars of `algebrax`:
#
# 1. **Langlands Root System Duality ($B_n \leftrightarrow C_n$)**: Transposing Cartan matrices $A^\vee = A^T$
#    exchanges orthogonal ($B_n$) and symplectic ($C_n$) root systems while preserving simply-laced types
#    ($A_n, D_n, E_6, E_7, E_8$) and mapping roots $\alpha$ to coroots
#    $\alpha^\vee = \frac{2\alpha}{\langle \alpha, \alpha \rangle}$.
# 2. **Iwahori-Hecke Algebras $\mathcal{H}_q(W)$**: Deforms Weyl group algebras $\mathbb{R}[W]$ with parameter $q$,
#    satisfying the quadratic relation $(T_i - q)(T_i + 1) = 0$ and the Artin-Tits braid relations.
# 3. **Ramanujan Expander Graphs & Discrete Hecke Walk Operators**: Verifies whether $d$-regular networks
#    achieve the optimal Alon-Boppana / Hasse-Weil spectral gap $\max_{|\lambda_i| < d} |\lambda_i| \le 2\sqrt{d - 1}$
#    and constructs the commutative Hecke algebra $T_k$ of non-backtracking graph walks.
# 4. **Non-Archimedean $p$-Adic Fields $\mathbb{Q}_p$ & Tropical Valuation Bridge**: Performs carry-propagated Hensel
#    arithmetic on sparse expansions `dict[int, int]` and bridges multiplication directly to `TropicalSemiring`
#    via $v_p(x \cdot y) = v_p(x) + v_p(y)$ and $v_p(x + y) \ge \min(v_p(x), v_p(y))$.

# %%
from __future__ import annotations

import math

import algebrax as ax
from algebrax.algebra import PAdicField
from algebrax.analysis import (
    adjacency_spectrum,
    hecke_graph_operator,
    is_ramanujan_graph,
)
from algebrax.lie import (
    IwahoriHeckeAlgebra,
    RootSystem,
    coroot_in_dual,
    langlands_dual_root_system,
    root_inner_product,
)
from algebrax.verification import (
    verify_algebra_laws,
    verify_cartan_duality,
    verify_field_laws,
    verify_padic_ultrametric_inequality,
    verify_ramanujan_spectral_gap,
)

# %% [markdown]
# ## 1. Langlands Dual Root Systems ($B_3 \leftrightarrow C_3$) & Coroots
#
# For crystallographic root systems, the Langlands dual root system $\Phi^\vee$ has Cartan matrix $A^\vee = A^T$.
# Taking the dual exchanges long and short simple roots, sending $B_3$ ($\mathfrak{so}_7$) to $C_3$ ($\mathfrak{sp}_6$).

# %%
b3 = RootSystem.from_dynkin('B', 3)
c3 = b3.langlands_dual()
b3_double_dual = langlands_dual_root_system(c3)

print(f'Primal root system : {b3.dynkin_type} (|Phi+| = {len(b3.positive_roots)})')
print(f'Langlands dual     : {c3.dynkin_type} (|Phi+| = {len(c3.positive_roots)})')
print(f'B3 Cartan matrix   : {b3.cartan_matrix}')
print(f'C3 Cartan matrix   : {c3.cartan_matrix}')
print(f'Involution holds?  : {b3_double_dual.cartan_matrix == b3.cartan_matrix}')

# Map a B_3 positive root to its coroot in C_3
alpha = (1, 1, 1)
alpha_coroot = coroot_in_dual(b3, alpha)
norm_sq = root_inner_product(b3, alpha, alpha)
print(f'Root alpha = {alpha}, <alpha, alpha> = {norm_sq}, coroot alpha^v = {alpha_coroot}')

duality_checks = verify_cartan_duality(b3)
print('Cartan duality laws:', duality_checks)
assert all(duality_checks.values())

# %% [markdown]
# ## 2. Iwahori-Hecke Algebra $\mathcal{H}_q(A_2)$
#
# In $\mathcal{H}_q(W)$, each simple reflection generator $T_i$ satisfies the quadratic Hecke equation
# $T_i^2 = (q - 1) T_i + q \mathbf{1}$ alongside the Artin braid relation $T_0 T_1 T_0 = T_1 T_0 T_1$.

# %%
a2 = RootSystem.from_dynkin('A', 2)
q_param = 2.5
hecke = IwahoriHeckeAlgebra(a2, q=q_param)

t0 = hecke.generator(0)
t1 = hecke.generator(1)

# 1. Quadratic Hecke relation: T_0^2 == (q - 1) * T_0 + q * 1
t0_sq = hecke.mul(t0, t0)
rhs_quad = hecke.add(hecke.scale(q_param - 1.0, t0), hecke.scale(q_param, hecke.one))
assert t0_sq == rhs_quad
print(f'Quadratic relation T_0^2 = (q-1)T_0 + q*1 verified for q={q_param}!')

# 2. Artin-Tits Braid relation: T_0 T_1 T_0 == T_1 T_0 T_1
braid_left = hecke.mul(hecke.mul(t0, t1), t0)
braid_right = hecke.mul(hecke.mul(t1, t0), t1)
assert braid_left == braid_right
print(f'Braid relation T_0 T_1 T_0 = T_1 T_0 T_1 verified (keys: {list(braid_left.keys())})!')

# 3. Verify Algebra[float, dict] axioms
alg_checks = verify_algebra_laws(
    hecke,
    ring=ax.algebra.StandardField(float),
    r_samples=[0.5, -1.0, 2.0],
    m_samples=[hecke.zero, hecke.one, t0, t1],
)
assert all(alg_checks.values())
print('Iwahori-Hecke algebra laws:', all(alg_checks.values()))

# %% [markdown]
# ## 3. Ramanujan Expander Verification & Non-Backtracking Hecke Operators
#
# A connected $d$-regular graph is a **Ramanujan expander** if every non-trivial eigenvalue $|\lambda_i| < d$
# satisfies $|\lambda_i| \le 2\sqrt{d - 1}$. On any regular graph, the Hecke operators $T_k$ form a commutative
# ring ($T_m T_n = T_n T_m$). Let us test the classic 10-vertex **Petersen Graph** ($d = 3$).

# %%
# Construct the 10-vertex 3-regular Petersen graph: outer 5-cycle (0..4) + inner 5-star (5..9)
petersen: dict[int, dict[int, float]] = {i: {} for i in range(10)}
for i in range(5):
    u, v = i, (i + 1) % 5
    petersen[u][v] = petersen[v][u] = 1.0
    petersen[i][i + 5] = petersen[i + 5][i] = 1.0
    s_u, s_v = 5 + i, 5 + ((i + 2) % 5)
    petersen[s_u][s_v] = petersen[s_v][s_u] = 1.0

spec = adjacency_spectrum(petersen)
is_ram, max_nontrivial, threshold = is_ramanujan_graph(petersen, degree=3)
print('Petersen spectrum:', [round(x, 3) for x in spec])
print(f'Ramanujan? {is_ram} | max|lambda_nontrivial| = {max_nontrivial:.4f} <= 2*sqrt(2) = {threshold:.4f}')
assert is_ram
assert math.isclose(max_nontrivial, 2.0, abs_tol=1e-6)

# Discrete Hecke walk operators T_1, T_2, T_3 commute
t1_op = hecke_graph_operator(petersen, 1, degree=3)
t2_op = hecke_graph_operator(petersen, 2, degree=3)
t3_op = hecke_graph_operator(petersen, 3, degree=3)
assert ax.matrix.dot(t1_op, t2_op) == ax.matrix.dot(t2_op, t1_op)
assert ax.matrix.dot(t2_op, t3_op) == ax.matrix.dot(t3_op, t2_op)

# The Petersen graph has girth 5, so there are zero closed non-backtracking walks of length <= 4
assert all(t2_op.get(u, {}).get(u, 0.0) == 0.0 for u in range(10))
assert all(t3_op.get(u, {}).get(u, 0.0) == 0.0 for u in range(10))

ram_checks = verify_ramanujan_spectral_gap(petersen, degree=3)
print('Ramanujan verification suite:', ram_checks)
assert all(ram_checks.values())

# %% [markdown]
# ## 4. Non-Archimedean $p$-Adic Field $\mathbb{Q}_5$ & Tropical Valuation Bridge
#
# In $\mathbb{Q}_p$, every element has a base-$p$ Laurent expansion stored as an unboxed sparse dictionary
# `dict[int, int]`. The $p$-adic valuation $v_p(x)$ maps field multiplication directly to addition in
# `TropicalSemiring`, and induces the ultrametric norm $|x|_p = p^{-v_p(x)}$.

# %%
q5 = PAdicField(p=5, precision=12)
tropical = ax.semiring.TropicalSemiring()

x = q5.from_int(75)  # 75 = 3 * 5^2 -> v_5(75) = 2, |75|_5 = 1/25 = 0.04
y = q5.from_rational(1, 3)  # 1/3 is a 5-adic unit -> v_5(1/3) = 0, |1/3|_5 = 1.0
z = q5.from_rational(5, 7)  # v_5(5/7) = 1

print(f'75 in Q_5  = {x} | v_5 = {q5.valuation(x)} | |75|_5 = {q5.norm(x)}')
print(f'1/3 in Q_5 = {y} | v_5 = {q5.valuation(y)} | |1/3|_5 = {q5.norm(y)}')

# Verify Hensel multiplicative inverse: (1/3) * 3 == 1
assert q5.mul(y, q5.from_int(3)) == q5.one
# Verify exact 5-adic inverse of 5: 5 * 5^{-1} == 1
five = q5.from_int(5)
assert q5.mul(five, q5.inv(five)) == q5.one

# Tropical Homomorphism: v_5(x * z) == v_5(x) (+)tropical v_5(z)
xz = q5.mul(x, z)
assert q5.valuation(xz) == tropical.mul(q5.valuation(x), q5.valuation(z))
# Ultrametric Isosceles Principle: since |x|_5 != |z|_5, |x + z|_5 == max(|x|_5, |z|_5)
assert math.isclose(q5.norm(q5.add(x, z)), max(q5.norm(x), q5.norm(z)))

padic_samples = [q5.zero, q5.one, x, y, z, q5.from_int(12)]
assert all(verify_field_laws(q5, padic_samples).values())
ultrametric_checks = verify_padic_ultrametric_inequality(q5, padic_samples)
print('Q_5 ultrametric & tropical bridge checks:', ultrametric_checks)
assert all(ultrametric_checks.values())
