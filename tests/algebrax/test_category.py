"""
Tests for Categorical Morphisms and Kleisli Composition.
"""

from algebrax.category import kleisli_compose
from algebrax.semiring import TropicalSemiring, ViterbiSemiring


def test_kleisli_probabilistic_composition():
    """
    Test Kleisli composition of probabilistic transition morphisms over ViterbiSemiring.
    """
    f = {'A': {'B': 0.8, 'C': 0.2}}
    g = {'B': {'D': 0.9}, 'C': {'D': 0.5}}

    res = kleisli_compose(f, g, semiring=ViterbiSemiring())
    # Expected max path to D: max(0.8*0.9=0.72, 0.2*0.5=0.10) = 0.72
    assert abs(res['A']['D'] - 0.72) < 1e-6


def test_kleisli_cost_lawvere_composition():
    """
    Test Kleisli composition in Lawvere Metric Category over TropicalSemiring.
    """
    f = {'A': {'B': 3.0, 'C': 7.0}}
    g = {'B': {'D': 2.0}, 'C': {'D': 1.0}}

    res = kleisli_compose(f, g, semiring=TropicalSemiring())
    # Expected min cost to D: min(3+2, 7+1) = 5.0
    assert abs(res['A']['D'] - 5.0) < 1e-6
