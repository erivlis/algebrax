# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Coalgebras, Bialgebras & Hopf Algebras — Duality & Quantum Symmetries (EP-0206)
#
# ## Theoretical Foundations & Duality
# In classical abstract algebra, an *algebra* combines elements via multiplication $\mu: A \otimes A \to A$
# and an identity unit $\eta: K \to A$.
#
# By reversing the arrows in category theory, a *coalgebra* decomposes elements via comultiplication
# $\Delta: C \to C \otimes C$ and a counit $\epsilon: C \to K$.
#
# Combining both structures yields a **Bialgebra**, where $\Delta$ and $\epsilon$ are algebra homomorphisms.
# Equipping a bialgebra with an **Antipode** $S: H \to H$ (the algebraic "quantum inverse") yields a **Hopf Algebra**,
# satisfying the fundamental axiom:
# $$\mu \circ (S \otimes \mathrm{id}) \circ \Delta = \eta \circ \epsilon$$
# $$\mu \circ (\mathrm{id} \otimes S) \circ \Delta = \eta \circ \epsilon$$
#
# In this recipe, we explore:
# 1. **Group Hopf Algebras** $K[G]$ with group-like coproduct $\Delta(g) = g \otimes g$ and antipode $S(g) = g^{-1}$.
# 2. **Divided Power Coalgebras** $\Gamma(x)$ governing binomial moments and differential splitting.
# 3. **Alexander-Whitney Simplicial Chain Coalgebras** $C_*(K)$, establishing the categorical dual of the cohomology
#    cup product $\smile$.

# %%
from __future__ import annotations

import math
from typing import Any

from algebrax.algebra import (
    Bialgebra,
    Coalgebra,
    DividedPowerCoalgebra,
    Group,
    GroupHopfAlgebra,
    HopfAlgebra,
)
from algebrax.topology import SimplicialChainCoalgebra, cup_product
from algebrax.verification import (
    verify_antipode_axiom,
    verify_bialgebra_laws,
    verify_coalgebra_laws,
    verify_coassociativity,
    verify_counitality,
    verify_hopf_algebra_laws,
)

# %% [markdown]
# ## 1. Group Hopf Algebras & The Quantum Inverse (Antipode)
#
# For any group $G$, the group algebra $K[G]$ is canonically a Hopf algebra where:
# - Coproduct: $\Delta(g) = g \otimes g$
# - Counit: $\epsilon(g) = 1$
# - Antipode: $S(g) = g^{-1}$


# %%
class CyclicGroup4(Group[int]):
    """Cyclic group Z/4Z under addition modulo 4."""

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 0

    def mul(self, x: int, y: int) -> int:
        return (x + y) % 4

    def inv(self, x: int) -> int:
        return (-x) % 4

    def div(self, x: int, y: int) -> int:
        return (x - y) % 4


z4 = CyclicGroup4()
gh = GroupHopfAlgebra(z4)

print(f"Is GroupHopfAlgebra a Coalgebra? {isinstance(gh, Coalgebra)}")
print(f"Is GroupHopfAlgebra a Bialgebra? {isinstance(gh, Bialgebra)}")
print(f"Is GroupHopfAlgebra a HopfAlgebra? {isinstance(gh, HopfAlgebra)}")

# Sample group algebra element: 2*g_1 + 3*g_2
x = {1: 2.0, 2: 3.0}
delta_x = gh.coproduct(x)
eps_x = gh.counit(x)
s_x = gh.antipode(x)

print(f"\nx = {x}")
print(f"Coproduct Delta(x) = {delta_x}")
print(f"Counit epsilon(x)  = {eps_x}")
print(f"Antipode S(x)      = {s_x}")

# Verify the Hopf antipode axiom
hopf_laws = verify_hopf_algebra_laws(
    gh,
    r_samples=[1.0, -1.0, 2.0],
    c_samples=[gh.zero, gh.one, {0: 1.0}, {1: 1.0}, {2: 1.0}, {3: 1.0}, x],
)
print("\nHopf Algebra Axiom Verifications:")
for law, passed in hopf_laws.items():
    print(f"  {law:30s}: {'PASSED' if passed else 'FAILED'}")

# %% [markdown]
# ## 2. Divided Power Coalgebra: Binomial Moment Decomposition
#
# In divided power coalgebras $\Gamma(x) = \bigoplus_{n \ge 0} K \cdot x^{[n]}$, the coproduct splits
# degrees binomially:
# $$\Delta(x^{[n]}) = \sum_{k=0}^n x^{[k]} \otimes x^{[n-k]}$$
# and the counit evaluates degree zero: $\epsilon(x^{[n]}) = \delta_{n, 0}$.

# %%
dpc = DividedPowerCoalgebra()

for deg in range(4):
    basis_elem = {deg: 1.0}
    coprod = dpc.coproduct(basis_elem)
    eps = dpc.counit(basis_elem)
    print(f"Degree {deg} (x^[{deg}]):")
    print(f"  Delta(x^[{deg}]) = {coprod}")
    print(f"  epsilon(x^[{deg}]) = {eps}")

# Verify coassociativity & counitality
dpc_samples = [dpc.zero, {0: 1.0}, {1: 1.0}, {2: 1.0}, {3: 1.0}, {1: 2.0, 2: -1.0}]
print(f"\nDivided power coassociativity: {verify_coassociativity(dpc, dpc_samples)}")
print(f"Divided power counitality:     {verify_counitality(dpc, dpc_samples)}")

# %% [markdown]
# ## 3. Alexander-Whitney Simplicial Chain Coalgebra & Cohomological Duality
#
# On simplicial chains $C_*(K)$, the Alexander-Whitney coproduct is the fundamental diagonal approximation:
# $$\Delta([v_0, \dots, v_n]) = \sum_{i=1}^{n+1} [v_0, \dots, v_{i-1}] \otimes [v_{i-1}, \dots, v_n]$$
#
# Its linear dual evaluation directly produces the simplicial cohomology cup product:
# $$\langle \alpha \smile \beta, \sigma \rangle = \langle \alpha \otimes \beta, \Delta(\sigma) \rangle$$

# %%
scc = SimplicialChainCoalgebra()

triangle = (0, 1, 2)  # Standard 2-simplex
chain = {triangle: 1.0}
aw_delta = scc.coproduct(chain)

print(f"2-Simplex sigma = {triangle}")
print("Alexander-Whitney Coproduct Delta(sigma):")
for (front_face, back_face), coeff in aw_delta.items():
    print(f"  {coeff} * ({front_face} (x) {back_face})")

# Evaluate dual pairing with 1-cochains alpha and beta
alpha_1 = {(0, 1): 3.0}
beta_1 = {(1, 2): 5.0}

cup_res = cup_product(alpha_1, beta_1)
eval_cup = cup_res.get(triangle, 0.0)

eval_dual = sum(
    coeff * alpha_1.get(front, 0.0) * beta_1.get(back, 0.0)
    for (front, back), coeff in aw_delta.items()
)

print(f"\nCohomology Cup Product (alpha smile beta)(sigma) = {eval_cup}")
print(f"Coalgebra Dual Contraction <alpha (x) beta, Delta(sigma)> = {eval_dual}")
assert math.isclose(eval_cup, eval_dual, rel_tol=1e-12)
print("Exact Duality Confirmed: <alpha smile beta, sigma> == <alpha (x) beta, Delta(sigma)>!")
