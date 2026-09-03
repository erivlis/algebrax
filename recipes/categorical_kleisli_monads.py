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
# # Categorical Morphisms, Kleisli Composition & Monadic Pipelines
#
# ## Theoretical Foundations & Physics
# 1. **Kleisli Category**: Morphisms $f: A \to T(B)$ compose via Kleisli matrix multiplication $(g \circ_T f)$.
# 2. **Semiring Monad Enrichment**: Swapping semirings defines probability
#    (`ViterbiSemiring`), cost (`TropicalSemiring`), and reachability (`BooleanSemiring`).
# 3. **Kan Extensions**: Optimal functorial extensions over sparse category graphs.

# %%
import algebrax as ax

# %% [markdown]
# ## Step 1: Probabilistic Monad Composition (`ViterbiSemiring`)

# %%
f_prob = {'A': {'B': 0.8, 'C': 0.2}}
g_prob = {'B': {'D': 0.9}, 'C': {'D': 0.5}}

res_viterbi = ax.category.kleisli_compose(f_prob, g_prob, semiring=ax.semiring.ViterbiSemiring())
print('  (g o_Viterbi f)(A, D) =', res_viterbi['A']['D'])
assert abs(res_viterbi['A']['D'] - 0.72) < 1e-6

# %% [markdown]
# ## Step 2: Lawvere Metric Category Composition (`TropicalSemiring`)

# %%
f_cost = {'A': {'B': 3.0, 'C': 7.0}}
g_cost = {'B': {'D': 2.0}, 'C': {'D': 1.0}}

res_tropical = ax.category.kleisli_compose(f_cost, g_cost, semiring=ax.semiring.TropicalSemiring())
print('  (g o_Tropical f)(A, D) =', res_tropical['A']['D'])
assert abs(res_tropical['A']['D'] - 5.0) < 1e-6

# %% [markdown]
# ## Step 3: Poset Category Composition (`BooleanSemiring`)

# %%
f_bool = {'A': {'B': True, 'C': False}}
g_bool = {'B': {'D': True}, 'C': {'D': True}}

res_bool = ax.category.kleisli_compose(f_bool, g_bool, semiring=ax.semiring.BooleanSemiring())
print('  (g o_Bool f)(A, D) =', res_bool['A']['D'])
assert res_bool['A']['D'] is True


def main() -> None:
    """Entry point for CLI execution."""
    print('==========================================================================')
    print('Recipe: Categorical Morphisms & Kleisli Composition Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
