"""
Tests for algebrax.display HTML rendering utilities.
"""

from algebrax.display import display_matrix, display_trie, display_vector
from algebrax.trie import AlgebraicTrie


def test_display_matrix_html_output():
    """Verify display_matrix produces valid HTML table tags for non-empty and empty matrices."""
    mat = {0: {1: 2.5}, 1: {0: 1.5, 2: 4.0}}
    html = display_matrix(mat, title="Sample Matrix")
    assert "Sample Matrix" in html
    assert "<table" in html
    assert "2.5" in html

    empty_html = display_matrix({}, title="Empty")
    assert "empty matrix" in empty_html


def test_display_vector_html_output():
    """Verify display_vector produces HTML table markup for non-empty and empty vectors."""
    vec = {"a": 1.0, "b": 2.0}
    html = display_vector(vec, title="Vector A")
    assert "Vector A" in html
    assert "1.0" in html

    empty_html = display_vector({}, title="Empty Vector")
    assert "empty vector" in empty_html


def test_display_trie_html_output():
    """Verify display_trie produces HTML tree representation for AlgebraicTrie."""
    trie = AlgebraicTrie()
    trie[("a", "b")] = 10
    html = display_trie(trie)
    assert "AlgebraicTrie" in html
    assert "10" in html

    empty_trie = AlgebraicTrie()
    empty_html = display_trie(empty_trie)
    assert "empty AlgebraicTrie" in empty_html
