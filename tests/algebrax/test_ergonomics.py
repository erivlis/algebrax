"""
Tests for developer ergonomics, submodule namespaces, Jupyter display, and optional NumPy/SciPy converters.
"""

import sys

import pytest

import algebrax as ax
from algebrax.display import display_matrix, display_trie, display_vector
from algebrax.trie import AlgebraicTrie


def test_submodule_qualified_namespaces():
    """Verify idiomatic import algebrax as ax; ax.matrix.dot(...) works."""
    m1 = {0: {0: 2.0}}
    m2 = {0: {0: 3.0}}

    res = ax.matrix.dot(m1, m2, semiring=ax.semiring.StandardSemiring())
    assert res == {0: {0: 6.0}}

    assert hasattr(ax, "homology")
    assert hasattr(ax, "category")
    assert hasattr(ax, "display")


def test_jupyter_display_html():
    """Verify display functions return valid HTML markup."""
    m = {0: {1: 5.0}}
    v = {0: 10.0}
    trie = AlgebraicTrie()
    trie[(0, 1)] = 42.0

    html_m = display_matrix(m, title="Test Matrix")
    assert "<table" in html_m
    assert "Test Matrix" in html_m
    assert "5.0" in html_m

    html_v = display_vector(v, title="Test Vector")
    assert "<table" in html_v
    assert "10.0" in html_v

    html_t = display_trie(trie)
    assert "AlgebraicTrie" in html_t
    assert "42.0" in html_t


def test_numpy_roundtrip_if_installed():
    """Verify NumPy to_numpy and from_numpy round-trip identity."""
    try:
        import numpy as np
    except ImportError:
        pytest.skip("numpy is not installed")

    m = {0: {0: 1.0, 2: 5.0}, 1: {1: 3.0}}
    arr = ax.converters.to_numpy(m)
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (2, 3)

    m_rec = ax.converters.from_numpy(arr)
    assert m_rec == m


def test_scipy_roundtrip_if_installed():
    """Verify SciPy to_scipy and from_scipy round-trip identity."""
    try:
        import scipy.sparse as sp
    except ImportError:
        pytest.skip("scipy is not installed")

    m = {0: {0: 1.0, 2: 5.0}, 1: {1: 3.0}}
    sp_mat = ax.converters.to_scipy(m, format="csr")
    assert sp.issparse(sp_mat)

    m_rec = ax.converters.from_scipy(sp_mat)
    assert m_rec == m


def test_ecosystem_import_error_message(monkeypatch):
    """Verify clear ImportError messages when numpy/scipy are missing."""
    monkeypatch.setitem(sys.modules, "numpy", None)
    monkeypatch.setitem(sys.modules, "scipy.sparse", None)

    with pytest.raises(ImportError, match="requires numpy"):
        ax.converters.to_numpy({0: {0: 1.0}})

    with pytest.raises(ImportError, match="requires numpy"):
        ax.converters.from_numpy(None)

    with pytest.raises(ImportError, match="requires scipy"):
        ax.converters.to_scipy({0: {0: 1.0}})

    with pytest.raises(ImportError, match="requires scipy"):
        ax.converters.from_scipy(None)


def test_top_level_typing_exports():
    """Verify ax.typing is accessible and core type aliases are re-exported at top-level."""
    assert hasattr(ax, "typing")
    assert ax.typing.SparseMatrix is ax.SparseMatrix
    assert ax.typing.SparseVector is ax.SparseVector
    assert ax.typing.SparseTensor is ax.SparseTensor
    assert ax.typing.DenseMatrix is ax.DenseMatrix
    assert ax.typing.DenseVector is ax.DenseVector

    from algebrax import DenseMatrix, DenseVector, SparseMatrix, SparseTensor, SparseVector

    assert SparseMatrix is ax.typing.SparseMatrix
    assert SparseVector is ax.typing.SparseVector
    assert SparseTensor is ax.typing.SparseTensor
    assert DenseMatrix is ax.typing.DenseMatrix
    assert DenseVector is ax.typing.DenseVector
