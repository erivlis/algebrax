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
# # Cartesian Closed Categories, Semiring Coeffects & Simplicial Path Groupoids
#
# ## Categorical Type Theory & Homotopy Topologies
# This recipe connects three foundational categorical abstractions across `algebrax.category` and `algebrax.topology`:
#
# 1. **Cartesian Closed Categories (`FiniteSetCCC`)**: Implements the Curry-Howard-Lambek correspondence
#    between finite sets, products $A \times B$, internal function spaces $C^B = \mathrm{Hom}(B, C)$, evaluation
#    $\mathrm{eval}$, and the $\beta/\eta$-currying bijection $\mathrm{Hom}(A \times B, C) \cong \mathrm{Hom}(A, C^B)$.
# 2. **Semiring-Graded Coeffects (`CoeffectContext`, `SemiringCoeffectTracker`)**: Models static resource and privacy
#    typing contexts $\Gamma : V \to \mathcal{S}$ as left $\mathcal{S}$-semimodules over integer reuse counts,
#    Boolean liveness, and Tropical latency budgets.
# 3. **Simplicial Homotopy Path Groupoids $\Pi_1(K)$**: Composes and inverts edge paths on simplicial complexes, proving
#    path homotopy equivalence modulo backtracking spurs and 2-simplex face shortcuts—detecting topological holes!

# %%
from __future__ import annotations

import algebrax as ax
from algebrax.category import (
    CartesianClosedCategory,
    CoeffectContext,
    FiniteSetCCC,
    SemiringCoeffectTracker,
)
from algebrax.topology import SimplicialComplex, SimplicialPathGroupoid
from algebrax.verification import (
    verify_coeffect_grading,
    verify_exponential_adjunction,
    verify_path_groupoid_laws,
)

# %% [markdown]
# ## 1. Curry-Howard-Lambek Adjunction in `FiniteSetCCC`
#
# Given finite sets $A = \{\text{"r"}, \text{"w"}\}$, $B = \{0, 1\}$, and $C = \{\text{"allow"}, \text{"deny"}\}$,
# any 2-argument policy $f: A \times B \to C$ can be curried into $\lambda f: A \to C^B$ and restored cleanly via
# $\mathrm{eval}_{C, B} \circ (\lambda f \times \mathrm{id}_B) = f$.

# %%
ccc = FiniteSetCCC()
assert CartesianClosedCategory in FiniteSetCCC.__mro__

obj_a = frozenset({'r', 'w'})
obj_b = frozenset({0, 1})
obj_c = frozenset({'allow', 'deny'})

ab = ccc.product(obj_a, obj_b)
f_map = {
    ('r', 0): 'allow',
    ('r', 1): 'allow',
    ('w', 0): 'deny',
    ('w', 1): 'allow',
}
f_mor = (ab, obj_c, f_map)

curried_f = ccc.curry(f_mor, obj_a, obj_b)
uncurried_f = ccc.uncurry(curried_f, obj_a, obj_b, obj_c)

print(f'Terminal object 1          = {ccc.terminal}')
print(f'|C^B| function space size  = {len(ccc.exponential(obj_c, obj_b))}')
print(f'Curried closure for "w"    = {curried_f[2]["w"]}')
assert uncurried_f == f_mor

adj_checks = verify_exponential_adjunction(ccc, obj_a, obj_b, obj_c, [f_mor])
print('CCC beta/eta adjunction laws:', adj_checks)
assert all(adj_checks.values())

# %% [markdown]
# ## 2. Semiring-Graded Coeffects: Liveness, Counts & Latency Budgets
#
# By swapping the semiring parameterizing `CoeffectContext[str, S]`, the exact same context algebra computes:
# - **Variable Use Counts** over $(\mathbb{N}, +, \times)$
# - **Dead-Code Liveness** over `BooleanSemiring` $(\lor, \land)$
# - **Best-Case Execution Budgets** over `TropicalSemiring` $(\min, +)$

# %%
# 2a. Integer resource counting (e.g., GPU buffer accesses across nested loops)
count_ctx: CoeffectContext[str, int] = CoeffectContext(ax.semiring.StandardSemiring(int))
gamma_read = count_ctx.singleton('weights', 1)
gamma_grad = count_ctx.singleton('weights', 2)
gamma_step = count_ctx.add(gamma_read, gamma_grad)  # 1 + 2 = 3 accesses per iteration
gamma_epoch = count_ctx.scale(10, gamma_step)  # 10 * 3 = 30 accesses per epoch
print(f'\nCount coeffect (10 epochs): {gamma_epoch}')
assert count_ctx.grade_of(gamma_epoch, 'weights') == 30

coeffect_checks = verify_coeffect_grading(
    count_ctx,
    grade_samples=[0, 1, 3],
    context_samples=[count_ctx.zero, gamma_read, gamma_grad],
)
assert all(coeffect_checks.values())

# 2b. Tropical latency budget tracker: parallel branches combine via min, sequential stages via +
tracker: SemiringCoeffectTracker[str, float] = SemiringCoeffectTracker(ax.semiring.TropicalSemiring())
tracker.record_cost('fast_cache', 2.0)
tracker.record_cost('db_query', 15.0)
best_branch = tracker.compose_parallel('fast_cache', 'db_query')
sequential_pipeline = tracker.compose_sequence('fast_cache', 'db_query')
print(f'Tropical parallel min(cache, db) = {best_branch} ms | sequential = {sequential_pipeline} ms')
assert best_branch == 2.0
assert sequential_pipeline == 17.0

# %% [markdown]
# ## 3. Simplicial Homotopy Path Groupoids $\Pi_1(K)$: Filled vs. Punctured Topology
#
# On a 1-skeleton triangle $0 - 1 - 2 - 0$:
# - If the 2-simplex $\{0, 1, 2\}$ is **filled**, path $(0, 1, 2)$ can continuously contract across the face
#   to $(0, 2)$.
# - If the 2-simplex is **missing** (a topological hole!), $(0, 1, 2)$ and $(0, 2)$ are **not homotopic**!

# %%
sc_filled = SimplicialComplex([[0, 1, 2]])
pi1_filled = SimplicialPathGroupoid.from_simplicial_complex(sc_filled)

sc_punctured = SimplicialComplex([[0, 1], [1, 2], [0, 2]])
pi1_punctured = SimplicialPathGroupoid.from_simplicial_complex(sc_punctured)

detour = (0, 1, 2)
direct = (0, 2)
backtrack_loop = pi1_punctured.compose(pi1_punctured.invert_path(detour), detour)  # (0, 1, 2, 1, 0)

print(f'\nFilled triangle homotopic (0,1,2) ~ (0,2)?    {pi1_filled.are_homotopic(detour, direct)}')
print(f'Punctured triangle homotopic (0,1,2) ~ (0,2)? {pi1_punctured.are_homotopic(detour, direct)}')
print(f'Backtracking loop (0,1,2,1,0) ~ (0,)?         {pi1_punctured.are_homotopic(backtrack_loop, (0,))}')

assert pi1_filled.are_homotopic(detour, direct)
assert not pi1_punctured.are_homotopic(detour, direct)
assert pi1_punctured.are_homotopic(backtrack_loop, (0,))

groupoid_checks = verify_path_groupoid_laws(pi1_filled, [(0,), (0, 1), (1, 2), (0, 1, 2), (0, 2)])
print('Path groupoid laws:', groupoid_checks)
assert all(groupoid_checks.values())
