"""
Edge-case test suite for empty inputs, 1x1 matrices, singular inputs, non-PD matrices, and trie serialization.
"""

import copy
import pickle

import pytest

from algebrax.automata import dfa_step, nfa_step, simulate_dfa, simulate_nfa
from algebrax.matrix.academic import determinant, inverse
from algebrax.matrix.decompose import (
    cholesky,
    lu,
    qr,
    recompose_cholesky,
    recompose_lu,
    recompose_qr,
    recompose_svd,
    svd,
)
from algebrax.trie import AlgebraicTrie


def test_empty_matrix_decompositions():
    """Verify decompose and recompose functions handle empty matrix {} gracefully."""
    p, l_mat, u = lu({})
    assert p == {}
    assert l_mat == {}
    assert u == {}
    assert recompose_lu(p, l_mat, u) == {}

    q, r = qr({})
    assert q == {}
    assert r == {}
    assert recompose_qr(q, r) == {}

    u_svd, s, v_t = svd({})
    assert u_svd == {}
    assert s == {}
    assert v_t == {}
    assert recompose_svd(u_svd, s, v_t) == {}

    l_chol = cholesky({})
    assert l_chol == {}
    assert recompose_cholesky(l_chol) == {}


def test_empty_matrix_academic():
    """Verify determinant and inverse on empty matrix {}."""
    assert determinant({}) == 1
    assert inverse({}) == {}


def test_one_by_one_matrix_decompositions():
    """Verify 1x1 matrix factorizations across all decomposition methods."""
    mat = {0: {0: 4.0}}

    p, l_mat, u = lu(mat)
    rec_lu = recompose_lu(p, l_mat, u)
    assert rec_lu[0][0] == pytest.approx(4.0)

    q, r = qr(mat)
    rec_qr = recompose_qr(q, r)
    assert rec_qr[0][0] == pytest.approx(4.0)

    u_svd, s, v_t = svd(mat)
    rec_svd = recompose_svd(u_svd, s, v_t)
    assert rec_svd[0][0] == pytest.approx(4.0)

    l_chol = cholesky(mat)
    rec_chol = recompose_cholesky(l_chol)
    assert rec_chol[0][0] == pytest.approx(4.0)


def test_singular_and_non_pd_matrix_errors():
    """Verify appropriate exceptions for singular and non-positive-definite inputs."""
    singular_mat = {0: {0: 1.0, 1: 2.0}, 1: {0: 2.0, 1: 4.0}}
    with pytest.raises(ValueError, match="singular"):
        inverse(singular_mat)

    non_pd_mat = {0: {0: -4.0}}
    with pytest.raises(ValueError, match="positive-definite"):
        cholesky(non_pd_mat)


def test_trie_serialization_and_copy():
    """Verify AlgebraicTrie pickle and deepcopy round-trips."""
    trie = AlgebraicTrie()
    trie[(0, 1)] = 5.0
    trie[(1, 2)] = 10.0

    # Pickle round-trip
    dumped = pickle.dumps(trie)
    loaded = pickle.loads(dumped)
    assert loaded[(0, 1)] == 5.0
    assert loaded[(1, 2)] == 10.0

    # Deepcopy round-trip
    copied = copy.deepcopy(trie)
    assert copied[(0, 1)] == 5.0
    assert copied[(1, 2)] == 10.0
