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
# # Quantum Spin Coupling, Anyon Braiding & Knotted Polymer Fingerprinting
#
# ## Clebsch-Gordan Recoupling, Higher Casimirs & $U_q(\mathfrak{sl}_2)$ Jones Invariants
# Continuous Lie symmetries and their $q$-deformed quantum group counterparts govern spin spectroscopy, quark-antiquark
# multiplet classification, topological quantum gates, and knotted biopolymer topology:
#
# 1. **Heisenberg Spin-Exchange Diagonalization (`spin_representation`, `clebsch_gordan_matrix`, `quadratic_casimir`)**:
#    Couples multi-particle spins via exact Condon-Shortley Clebsch-Gordan intertwiners to diagonalize the isotropic
#    Heisenberg exchange Hamiltonian into singlet ($J=0$) and triplet ($J=1$) energy levels.
# 2. **Conjugate Multiplet Separation (`sl_n`, `cubic_casimir_operator`)**: Distinguishes the fundamental quark
#    representation $\mathbf{3}$ from its conjugate antiquark representation $\bar{\mathbf{3}}$ in $\mathfrak{sl}_3$,
#    where the quadratic Casimir $C_2$ is blind (degenerate) while the cubic Casimir $C_3$ flips sign.
# 3. **Braided Gates & DNA Knots (`QuantumSL2`, `universal_r_matrix_sl2_fundamental`, `jones_polynomial_eval`)**:
#    Verifies the Quantum Yang-Baxter Equation on $U_q(\mathfrak{sl}_2)$ anyon braiding operators and classifies
#    circular DNA/polymer ring topologies—detecting trefoil chirality ($3_1$ vs. $\overline{3_1}$) and figure-eight
#    amphicheirality ($4_1$).

# %%
from __future__ import annotations

import cmath
import math

import algebrax as ax
from algebrax.lie import sl_n
from algebrax.rep import (
    QuantumSL2,
    braid_to_matrix,
    clebsch_gordan_matrix,
    cubic_casimir_operator,
    defining_representation,
    jones_polynomial_eval,
    quadratic_casimir,
    spin_representation,
    universal_r_matrix_sl2_fundamental,
)
from algebrax.verification import (
    verify_casimir_commutativity,
    verify_clebsch_gordan_coupling,
    verify_cubic_casimir_invariance,
    verify_quantum_sl2_relations,
    verify_yang_baxter_equation,
)

# %% [markdown]
# ## 1. Two-Electron Heisenberg Spin Exchange via Clebsch-Gordan Coupling
#
# Two coupled spin-$\frac{1}{2}$ electrons evolve under the isotropic Heisenberg exchange Hamiltonian
# $H_{\text{ex}} = J_{\text{ex}} (\mathbf{S}_1 \cdot \mathbf{S}_2) =
# \frac{J_{\text{ex}}}{2} (J_{\text{tot}}^2 - S_1^2 - S_2^2)$.
# Using skew-Hermitian $\mathfrak{su}(2)$ generators ($X_k = -i S_k$), the physical angular-momentum Casimir $J^2$
# corresponds to the negative Euclidean metric $g^{ij} = -\delta^{ij}$. Transforming $H_{\text{ex}}$ by the orthogonal
# Clebsch-Gordan matrix $U$ (`clebsch_gordan_matrix(1, 1)`) decouples the 4-state Hilbert space into a triplet ($J=1$,
# energy $+\frac{1}{4} J_{\text{ex}}$) and a singlet ($J=0$, energy $-\frac{3}{4} J_{\text{ex}}$).

# %%
spin_half = spin_representation(1, form='su2')
two_spin = spin_half.tensor_product(spin_half)
phys_metric_inv = {0: {0: -1.0}, 1: {1: -1.0}, 2: {2: -1.0}}

assert all(
    verify_casimir_commutativity(
        spin_half,
        killing_metric_inv=phys_metric_inv,
        expected_eigenvalue=0.75,
    ).values()
)
assert all(verify_clebsch_gordan_coupling(1, 1).values())
assert all(verify_clebsch_gordan_coupling(2, 1).values())

j_tot_sq = quadratic_casimir(two_spin, killing_metric_inv=phys_metric_inv)
j_exchange = 2.0  # Antiferromagnetic exchange coupling in meV

# H_ex = 0.5 * J_ex * (J_tot^2 - 2 * (3/4) I_4)
neg_offset = {i: {i: -1.5} for i in range(4)}
s1_dot_s2 = {
    r: {c: 0.5 * float(val.real) for c, val in row.items()}
    for r, row in ax.matrix.add(j_tot_sq, neg_offset).items()
}
h_ex_uncoupled = {
    r: {c: j_exchange * val for c, val in row.items()} for r, row in s1_dot_s2.items()
}

u_cg, coupled_labels = clebsch_gordan_matrix(1, 1)
h_ex_coupled = ax.matrix.dot(ax.matrix.dot(ax.matrix.transpose(u_cg), h_ex_uncoupled), u_cg)

print('Heisenberg Two-Spin Exchange Spectrum in Clebsch-Gordan Basis |(J, M)>:')
for idx, (j_halves, m_halves) in enumerate(coupled_labels):
    energy = h_ex_coupled.get(idx, {}).get(idx, 0.0)
    off_diag = sum(abs(v) for col, v in h_ex_coupled.get(idx, {}).items() if col != idx)
    assert off_diag < 1e-12
    print(f'  State |J={j_halves // 2}, M={m_halves // 2:+d}> : E = {energy:+.4f} meV')

singlet_energy = h_ex_coupled[3][3]
triplet_energy = h_ex_coupled[0][0]
assert math.isclose(triplet_energy, 0.25 * j_exchange, abs_tol=1e-12)
assert math.isclose(singlet_energy, -0.75 * j_exchange, abs_tol=1e-12)
assert math.isclose(triplet_energy - singlet_energy, j_exchange, abs_tol=1e-12)

# %% [markdown]
# ## 2. Separating $\mathfrak{sl}_3$ Quark ($\mathbf{3}$) vs. Antiquark ($\bar{\mathbf{3}}$) Sectors via Cubic Casimir
#
# In $\mathfrak{sl}_3$ color/flavor symmetry, the fundamental quark representation $\mathbf{3}$ and its contragredient
# dual antiquark representation $\bar{\mathbf{3}}$ (`quark_rep.dual()`,
# $\rho_{\bar{\mathbf{3}}}(X) = -\rho_{\mathbf{3}}(X)^T$) share the exact same dimension ($3$) and Killing quadratic
# Casimir eigenvalue ($C_2 = \frac{4}{9} I_3$). Only the degree-3 symmetric invariant tensor $d_{ijk}$
# (`cubic_casimir_operator`) breaks conjugation symmetry with opposite scalar eigenvalues $\pm\lambda_3 I_3$.

# %%
sl3 = sl_n(3)
assert all(verify_cubic_casimir_invariance(sl3).values())

quark_rep = defining_representation(sl3)
antiquark_rep = quark_rep.dual()

c2_quark = quadratic_casimir(quark_rep)[0][0].real
c2_antiquark = quadratic_casimir(antiquark_rep)[0][0].real
c3_quark = cubic_casimir_operator(quark_rep)[0][0].real
c3_antiquark = cubic_casimir_operator(antiquark_rep)[0][0].real

print('\nsl_3 Conjugate Irrep Classification (Quark 3 vs. Antiquark 3-bar):')
print(f'  Quadratic Casimir C_2:  quark = {c2_quark:+.6f} | antiquark = {c2_antiquark:+.6f}  (degenerate)')
print(f'  Cubic Casimir     C_3:  quark = {c3_quark:+.6f} | antiquark = {c3_antiquark:+.6f}  (chirally separated!)')

assert math.isclose(c2_quark, 4.0 / 9.0, abs_tol=1e-12)
assert math.isclose(c2_antiquark, 4.0 / 9.0, abs_tol=1e-12)
assert math.isclose(c3_quark, 5.0 / 243.0, abs_tol=1e-12)
assert math.isclose(c3_antiquark, -5.0 / 243.0, abs_tol=1e-12)

# %% [markdown]
# ## 3. $U_q(\mathfrak{sl}_2)$ Anyon Braiding & Topological Fingerprinting of Circular DNA Knots
#
# During site-specific DNA recombination, enzymes tangle circular plasmid rings into knots and catenanes whose
# electrophoretic gel mobility depends on topological type. Evaluating the Reshetikhin-Turaev quantum trace on
# $U_q(\mathfrak{sl}_2)$ braid representations (`jones_polynomial_eval` at $t = q^{-2}$) distinguishes:
# - **Unknot** ($\widehat{\sigma_1}$ on 2 strands) vs. **Hopf Catenane** ($\widehat{\sigma_1^2}$),
# - **Right-handed ($3_1$)** vs. **Left-handed ($\overline{3_1}$)** trefoil chirality
#   ($V_{3_1}(t) \neq V_{\overline{3_1}}(t)$),
# - **Figure-eight knot ($4_1$)** amphicheirality ($V_{4_1}(t) \in \mathbb{R}$ for $|t| = 1$).

# %%
q = cmath.exp(1j * math.pi / 7.0)
t = q ** (-2)

uq = QuantumSL2(q)
q_spin_half = uq.spin_representation(1)
r_mat = universal_r_matrix_sl2_fundamental(q)

assert all(verify_quantum_sl2_relations(q, q_spin_half).values())
assert all(verify_yang_baxter_equation(r_mat, dim=2).values())

# Non-involutive quantum antipode check: S^2(E) = q^{-2} E != E
s2_e = uq.antipode(uq.antipode(uq.E))
assert cmath.isclose(s2_e[(1, 0, 0)], q ** (-2), abs_tol=1e-12)

polymer_topologies: list[tuple[str, list[int], int]] = [
    ('Unknot (twisted ring)', [1], 2),
    ('Hopf Link (2-ring catenane)', [1, 1], 2),
    ('Right-Handed Trefoil 3_1', [1, 1, 1], 2),
    ('Left-Handed Trefoil 3_1*', [-1, -1, -1], 2),
    ('Figure-Eight Knot 4_1', [1, -2, 1, -2], 3),
]

scores: dict[str, complex] = {}
print('\nCircular Biopolymer Jones Topological Fingerprints at q = exp(i*pi/7) (|t|=1):')
for label, word, strands in polymer_topologies:
    gate = braid_to_matrix(word, strands, q)
    nnz = sum(len(row) for row in gate.values())
    val = jones_polynomial_eval(word, strands, q)
    scores[label] = val
    print(f'  {label:<28} | strands={strands}, gate_nnz={nnz:2d} | V(t) = {val.real:+.5f} {val.imag:+.5f}j')

# Verify exact closed-form knot identities at t = q^{-2}
assert cmath.isclose(scores['Unknot (twisted ring)'], 1.0 + 0.0j, abs_tol=1e-11)
assert cmath.isclose(scores['Hopf Link (2-ring catenane)'], -(q ** (-1) + q ** (-5)), abs_tol=1e-11)
assert cmath.isclose(scores['Right-Handed Trefoil 3_1'], t + t**3 - t**4, abs_tol=1e-11)
assert cmath.isclose(scores['Left-Handed Trefoil 3_1*'], t ** (-1) + t ** (-3) - t ** (-4), abs_tol=1e-11)

# Right- and left-handed trefoils have non-zero opposite imaginary parts on the unit circle (chiral!)
assert abs(scores['Right-Handed Trefoil 3_1'] - scores['Left-Handed Trefoil 3_1*']) > 0.5
assert cmath.isclose(
    scores['Left-Handed Trefoil 3_1*'],
    scores['Right-Handed Trefoil 3_1'].conjugate(),
    abs_tol=1e-11,
)

# Figure-eight knot 4_1 is amphicheiral: V(t) = t^-2 - t^-1 + 1 - t + t^2 is strictly real on |t|=1
assert abs(scores['Figure-Eight Knot 4_1'].imag) < 1e-11
assert cmath.isclose(
    scores['Figure-Eight Knot 4_1'],
    t ** (-2) - t ** (-1) + 1.0 - t + t**2,
    abs_tol=1e-11,
)
