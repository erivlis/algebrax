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
# 1. **Kleisli Category**: Morphisms $f: A \\to T(B)$ compose via Kleisli matrix multiplication $(g \\circ_T f)$.
# 2. **Semiring Monad Enrichment**: Swapping semirings defines probability
#    (`ViterbiSemiring`), cost (`TropicalSemiring`), and reachability (`BooleanSemiring`).

# %%
from typing import Any

import algebrax as ax


def compose_kleisli_arrows(
    f: dict[Any, dict[Any, Any]],
    g: dict[Any, dict[Any, Any]],
    semiring: ax.semiring.Semiring[Any],
) -> dict[Any, dict[Any, Any]]:
    """Compose monadic morphisms (g o_T f) via enriched Kleisli convolution."""
    return ax.category.kleisli_compose(f, g, semiring=semiring)

# %% [markdown]
# ## Step 1: Probabilistic Monad Composition (`ViterbiSemiring`)
#
# ## Step 2: Lawvere Metric Category Composition (`TropicalSemiring`)
#
# ## Step 3: Poset Category Composition (`BooleanSemiring`)


def run_demo() -> None:
    """Run enriched categorical Kleisli compositions across semirings."""
    f_prob = {'A': {'B': 0.8, 'C': 0.2}}
    g_prob = {'B': {'D': 0.9}, 'C': {'D': 0.5}}
    res_viterbi = compose_kleisli_arrows(f_prob, g_prob, semiring=ax.semiring.ViterbiSemiring())
    print('  (g o_Viterbi f)(A, D) =', res_viterbi['A']['D'])
    assert abs(res_viterbi['A']['D'] - 0.72) < 1e-6

    f_cost = {'A': {'B': 3.0, 'C': 7.0}}
    g_cost = {'B': {'D': 2.0}, 'C': {'D': 1.0}}
    res_tropical = compose_kleisli_arrows(f_cost, g_cost, semiring=ax.semiring.TropicalSemiring())
    print('  (g o_Tropical f)(A, D) =', res_tropical['A']['D'])
    assert abs(res_tropical['A']['D'] - 5.0) < 1e-6

    f_bool = {'A': {'B': True, 'C': False}}
    g_bool = {'B': {'D': True}, 'C': {'D': True}}
    res_bool = compose_kleisli_arrows(f_bool, g_bool, semiring=ax.semiring.BooleanSemiring())
    print('  (g o_Bool f)(A, D) =', res_bool['A']['D'])
    assert res_bool['A']['D'] is True


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Categorical Morphisms & Kleisli Composition Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
