r"""
Real-World Use Case: Categorical Morphisms, Kleisli Composition & Monadic Pipelines.

Theoretical Foundations & Physics:
1. Kleisli Category: Morphisms f: A -> T(B) ax.group.compose via Kleisli matrix multiplication (g o_T f).
2. ax.semiring.Semiring Monad Enrichment: Swapping semirings defines probability (Viterbi),
   cost (Tropical), and reachability (Boolean).
3. Kan Extensions: Optimal functorial extensions over sparse category graphs.
"""

import algebrax as ax


def main() -> None:
    print('--- Categorical Morphisms & Kleisli Composition ---')

    # Morphisms A -> B and B -> C
    f_prob = {'A': {'B': 0.8, 'C': 0.2}}
    g_prob = {'B': {'D': 0.9}, 'C': {'D': 0.5}}

    print('\n[1] Probabilistic Monad Composition (ax.semiring.ViterbiSemiring):')
    res_viterbi = ax.category.kleisli_compose(f_prob, g_prob, semiring=ax.semiring.ViterbiSemiring())
    print('  (g o_Viterbi f)(A, D) =', res_viterbi['A']['D'])
    assert abs(res_viterbi['A']['D'] - 0.72) < 1e-6

    f_cost = {'A': {'B': 3.0, 'C': 7.0}}
    g_cost = {'B': {'D': 2.0}, 'C': {'D': 1.0}}

    print('\n[2] Lawvere Metric Category Composition (ax.semiring.TropicalSemiring):')
    res_tropical = ax.category.kleisli_compose(f_cost, g_cost, semiring=ax.semiring.TropicalSemiring())
    print('  (g o_Tropical f)(A, D) =', res_tropical['A']['D'])
    assert abs(res_tropical['A']['D'] - 5.0) < 1e-6

    f_bool = {'A': {'B': True, 'C': False}}
    g_bool = {'B': {'D': True}, 'C': {'D': True}}

    print('\n[3] Poset Category Composition (ax.semiring.BooleanSemiring):')
    res_bool = ax.category.kleisli_compose(f_bool, g_bool, semiring=ax.semiring.BooleanSemiring())
    print('  (g o_Bool f)(A, D) =', res_bool['A']['D'])
    assert res_bool['A']['D'] is True

    print('\nSuccessfully verified Categorical Morphisms & Kleisli Composition!')


if __name__ == '__main__':
    main()
