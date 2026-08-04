"""
Numerical stability, automata edge cases, and cross-semiring stress test suite.
"""

import math

import pytest

from algebrax.automata import dfa_step, nfa_step, simulate_dfa, simulate_nfa
from algebrax.matrix.core import dot, power
from algebrax.matrix.decompose import lu, qr, recompose_lu, recompose_qr, recompose_svd, svd
from algebrax.semiring import BooleanSemiring, TropicalSemiring


def create_hilbert_matrix(dim: int) -> dict[int, dict[int, float]]:
    """Create a dim x dim Hilbert matrix H_ij = 1 / (i + j + 1)."""
    return {i: {j: 1.0 / (i + j + 1.0) for j in range(dim)} for i in range(dim)}


def test_hilbert_matrix_decompositions():
    """Verify LU, QR, and SVD numerical accuracy on ill-conditioned Hilbert matrices."""
    for dim in (3, 5):
        h_mat = create_hilbert_matrix(dim)

        # LU
        p, l_mat, u = lu(h_mat)
        rec_lu = recompose_lu(p, l_mat, u)
        for i in range(dim):
            for j in range(dim):
                assert math.isclose(rec_lu[i][j], h_mat[i][j], abs_tol=1e-5)

        # QR
        q, r = qr(h_mat)
        rec_qr = recompose_qr(q, r)
        for i in range(dim):
            for j in range(dim):
                assert math.isclose(rec_qr[i][j], h_mat[i][j], abs_tol=1e-5)

        # SVD
        u_svd, s, v_t = svd(h_mat)
        rec_svd = recompose_svd(u_svd, s, v_t)
        for i in range(dim):
            for j in range(dim):
                assert math.isclose(rec_svd[i][j], h_mat[i][j], abs_tol=1e-5)


def test_automata_edge_cases():
    """Verify automata behavior with unreachable states, empty transitions, and single-state machines."""
    # Single-state accepting machine
    transitions = {'q0': {'a': 'q0'}}
    assert dfa_step('q0', 'a', transitions) == 'q0'
    assert simulate_dfa('q0', 'aaa', transitions) == 'q0'
    assert simulate_dfa('q0', '', transitions) == 'q0'

    # Unreachable state & empty input string
    empty_trans = {}
    assert dfa_step('q0', 'a', empty_trans) is None
    assert simulate_dfa('q0', '', empty_trans) == 'q0'
    assert simulate_dfa('q0', 'a', empty_trans) is None

    # NFA with empty input string
    nfa_trans = {'q0': {'a': {'q1': 1.0}}}
    assert simulate_nfa({'q0': 1.0}, '', nfa_trans) == {'q0': 1.0}
    assert simulate_nfa({'q0': 1.0}, 'a', nfa_trans) == {'q1': 1.0}


def test_tropical_semiring_matrix_stress():
    """Verify TropicalSemiring matrix dot product on 10x10 and 30x30 sparse graphs."""
    for dim in (10, 30):
        # Create line graph with weights
        graph = {i: {i + 1: float(i + 1)} for i in range(dim - 1)}
        prod = dot(graph, graph, semiring=TropicalSemiring())
        for i in range(dim - 2):
            assert prod[i][i + 2] == float(i + 1) + float(i + 2)


def test_boolean_transitive_closure_convergence():
    """Verify BooleanSemiring power() convergence (transitive closure with self-loops)."""
    # 5-node graph with self-loops (I | A) and cycle 0 -> 1 -> 2 -> 3 -> 4 -> 0
    graph = {i: {i: True, (i + 1) % 5: True} for i in range(5)}
    closure = power(graph, 5, semiring=BooleanSemiring())
    for r in range(5):
        for c in range(5):
            assert closure[r][c] is True
