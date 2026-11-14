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
# # Topological K-Theory, Grothendieck Rings & Quantized Chern Classes
#
# ## Virtual Vector Bundles & Characteristic Invariants
# **Topological K-Theory** $K^0(X)$ transforms the commutative semiring of vector bundles under Whitney direct sum
# ($\oplus$) and tensor product ($\otimes$) into a commutative ring via **Grothendieck completion**, introducing virtual
# bundle differences $[E] - [F]$.
#
# In this recipe, we demonstrate:
# 1. **Discrete $SO(2) \cong U(1)$ Line Bundles** over a closed oriented triangulated sphere $S^2$ (a tetrahedron).
# 2. **Dirac Monopole Flux Quantization**: Computing face holonomy curvature angles and verifying integer
#    quantization of the first Chern number $\int_{S^2} c_1(E) \in \mathbb{Z}$.
# 3. **Whitney Direct Sum & Chern Character Additivity**: Proving
#    $\mathrm{ch}_1(E_1 \oplus E_2) = \mathrm{ch}_1(E_1) + \mathrm{ch}_1(E_2)$.
# 4. **The Virtual Bundle Ring $K^0(S^2)$**: Embedding and subtracting bundles inside `TopologicalKTheoryRing`.

# %%
from __future__ import annotations

import math

from algebrax.topology import (
    DiscreteOrthogonalConnection,
    TopologicalKTheoryRing,
    bundle_direct_sum,
    bundle_tensor_product,
    chern_character,
    first_chern_number,
    trivial_bundle,
)
from algebrax.verification import (
    verify_chern_character_additivity,
    verify_chern_number_integrality,
)

# %% [markdown]
# ## 1. Closed Oriented Sphere $S^2$ & Quantized Dirac Monopole Bundles
#
# Consider the outward-oriented boundary 2-cycle of a tetrahedron $\{0, 1, 2, 3\}$:
# $$\partial [0, 1, 2, 3] = [1, 2, 3] - [0, 2, 3] + [0, 1, 3] - [0, 1, 2]$$
# Reversing negatively signed triangles produces four coherently oriented faces.

# %%
def rot2d(theta: float) -> dict[int, dict[int, float]]:
    """Construct a sparse 2x2 SO(2) planar rotation matrix."""
    c, s = math.cos(theta), math.sin(theta)
    return {0: {0: c, 1: -s}, 1: {0: s, 1: c}}


edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
oriented_s2 = [(1, 2, 3), (0, 3, 2), (0, 1, 3), (0, 2, 1)]

# Bundle E_flat: Smooth connection with zero net topological charge (c_1 = 0)
e_flat = DiscreteOrthogonalConnection(fiber_dim=2)
for edge, angle in zip(edges, [0.4, -0.3, 0.2, 0.5, -0.4, 0.3], strict=True):
    e_flat.set_transport(edge[0], edge[1], rot2d(angle))

# Bundle E_monopole: Discrete Dirac monopole carrying topological charge c_1 = -1 (-2*pi total flux)
e_monopole = DiscreteOrthogonalConnection(fiber_dim=2)
monopole_angles = {
    (0, 1): 0.0,
    (0, 2): 0.0,
    (0, 3): 0.0,
    (1, 2): 2.2,
    (2, 3): 2.2,
    (1, 3): -2.2,
}
for (u, v), angle in monopole_angles.items():
    e_monopole.set_transport(u, v, rot2d(angle))

# Anti-monopole E_anti with reversed twist (c_1 = +1)
e_anti = DiscreteOrthogonalConnection(fiber_dim=2)
for (u, v), angle in monopole_angles.items():
    e_anti.set_transport(u, v, rot2d(-angle))

c1_flat = first_chern_number(e_flat, oriented_s2)
c1_mono = first_chern_number(e_monopole, oriented_s2)
c1_anti = first_chern_number(e_anti, oriented_s2)

print(f'First Chern number c_1(E_flat)     = {c1_flat:.6f}')
print(f'First Chern number c_1(E_monopole) = {c1_mono:.6f}')
print(f'First Chern number c_1(E_anti)     = {c1_anti:.6f}')

assert verify_chern_number_integrality(e_flat, oriented_s2)
assert verify_chern_number_integrality(e_monopole, oriented_s2)
assert verify_chern_number_integrality(e_anti, oriented_s2)

# %% [markdown]
# ## 2. Whitney Direct Sums, Tensor Products & Chern Character Additivity
#
# Forming the Whitney sum $E_{\mathrm{monopole}} \oplus E_{\mathrm{anti}}$ embeds both $SO(2)$ connections
# block-diagonally into an $SO(4)$ vector bundle of complex rank $\mathrm{ch}_0 = 2$ whose net first Chern number
# cancels: $c_1(E_{\mathrm{monopole}} \oplus E_{\mathrm{anti}}) = (-1) + (+1) = 0$.

# %%
whitney_sum = bundle_direct_sum(e_monopole, e_anti, edges)
tensor_prod = bundle_tensor_product(e_monopole, e_anti, edges)

ch0, ch1, ch2 = chern_character(whitney_sum, oriented_s2)
print(f'\nWhitney sum complex rank ch_0     = {ch0} (fiber_dim = {whitney_sum.fiber_dim})')
print(f'Tensor product fiber_dim          = {tensor_prod.fiber_dim}')
print(f'Net Chern number of sum c_1       = {sum(ch1.values()):.6f}')
print(f'Total second Chern density ch_2   = {sum(ch2.values()):.6f}')

additivity_checks = verify_chern_character_additivity(e_monopole, e_anti, oriented_s2)
print('Chern character additivity laws:', additivity_checks)
assert all(additivity_checks.values())

# Double monopole: E_monopole (+) E_monopole carries topological charge -2
double_mono = bundle_direct_sum(e_monopole, e_monopole, edges)
c1_double = first_chern_number(double_mono, oriented_s2)
print(f'First Chern number c_1(E_mono (+) E_mono) = {c1_double:.6f}')
assert math.isclose(c1_double, -2.0, abs_tol=1e-9)

# %% [markdown]
# ## 3. Virtual Bundle Arithmetic in $K^0(S^2)$
#
# In `TopologicalKTheoryRing`, bundles can be freely subtracted as formal differences $[E] - [F]$, tracking virtual
# rank $\mathrm{rank}(E) - \mathrm{rank}(F)$ and virtual characteristic classes $\mathrm{ch}_1([E] - [F])$.

# %%
k_ring = TopologicalKTheoryRing(edges)
triv_2 = trivial_bundle(2, edges)

cls_anti = k_ring.embed(e_anti)
cls_mono = k_ring.embed(e_monopole)
cls_triv = k_ring.embed(triv_2)

# Virtual difference [E_anti] - [E_monopole]: virtual rank 0, virtual Chern number (+1) - (-1) = +2
virtual_diff = k_ring.sub(cls_anti, cls_mono)
virt_rank = k_ring.virtual_rank(virtual_diff)
virt_ch1 = k_ring.virtual_chern_1(virtual_diff, oriented_s2)
virt_c1_total = sum(virt_ch1.values())

print('\nVirtual class [E_anti] - [E_monopole]:')
print(f'  Virtual fiber dimension = {virt_rank}')
print(f'  Virtual first Chern #   = {virt_c1_total:.6f}')
assert virt_rank == 0
assert math.isclose(virt_c1_total, 2.0, abs_tol=1e-9)

# Stabilized subtraction against trivial bundle: [E_anti] - [R^2] preserves c_1 = +1 while zeroing rank
reduced_anti = k_ring.sub(cls_anti, cls_triv)
assert k_ring.virtual_rank(reduced_anti) == 0
assert math.isclose(sum(k_ring.virtual_chern_1(reduced_anti, oriented_s2).values()), 1.0, abs_tol=1e-9)
print('Reduced K-theory class [E_anti] - [R^2] has rank 0 and c_1 = +1.0!')
