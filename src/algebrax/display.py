"""
Jupyter Notebook Rich Display utilities for algebrax structures.
"""

from typing import Any

from algebrax.typing import SparseMatrix, SparseVector

__all__ = [
    'display_matrix',
    'display_trie',
    'display_vector',
]


def display_matrix(matrix: SparseMatrix[Any, Any], title: str = '') -> str:
    """
    Return HTML table representation of a sparse matrix for Jupyter Notebooks.

    Args:
        matrix: Sparse matrix (nested dict).
        title: Optional table caption/header title.

    Returns:
        HTML string containing standard table elements.
    """
    if not matrix:
        caption = f"<caption><b>{title}</b> (empty)</caption>" if title else ''
        return f'<table>{caption}<tbody><tr><td><i>empty matrix</i></td></tr></tbody></table>'

    col_keys = sorted({c for row in matrix.values() for c in row}, key=str)
    row_keys = sorted(matrix.keys(), key=str)

    html_parts = ["<table border='1' style='border-collapse: collapse; font-family: monospace;'>"]
    if title:
        html_parts.append(f'<caption><b>{title}</b></caption>')

    # Header row
    html_parts.append("<tr style='background-color: #f2f2f2;'><th>r \\ c</th>")
    for c in col_keys:
        html_parts.append(f'<th>{c}</th>')
    html_parts.append('</tr>')

    # Data rows
    for r in row_keys:
        html_parts.append(f"<tr><th style='background-color: #f2f2f2;'>{r}</th>")
        row = matrix.get(r, {})
        for c in col_keys:
            val = row.get(c, '')
            cell_str = str(val) if val != '' else '&middot;'
            style = 'padding: 4px 8px; text-align: center;'
            if val != '':
                style += ' font-weight: bold; background-color: #e6f2ff;'
            html_parts.append(f"<td style='{style}'>{cell_str}</td>")
        html_parts.append('</tr>')

    html_parts.append('</table>')
    return ''.join(html_parts)


def display_vector(vector: SparseVector[Any, Any], title: str = '') -> str:
    """
    Return HTML representation of a sparse vector for Jupyter Notebooks.

    Args:
        vector: Sparse vector (dict).
        title: Optional title string.

    Returns:
        HTML string.
    """
    if not vector:
        caption = f'<b>{title}: </b>' if title else ''
        return f'<div>{caption}<i>empty vector</i></div>'

    keys = sorted(vector.keys(), key=str)
    html_parts = ["<table border='1' style='border-collapse: collapse; font-family: monospace;'>"]
    if title:
        html_parts.append(f'<caption><b>{title}</b></caption>')

    html_parts.append("<tr style='background-color: #f2f2f2;'><th>Key</th><th>Value</th></tr>")
    for k in keys:
        cell_val = vector[k]
        html_parts.append(
            f"<tr><td style='padding: 4px 8px;'>{k}</td>"
            f"<td style='padding: 4px 8px; font-weight: bold;'>{cell_val}</td></tr>"
        )
    html_parts.append('</table>')
    return ''.join(html_parts)


def display_trie(trie: Any, max_depth: int = 4) -> str:
    """
    Return HTML tree representation of an AlgebraicTrie.

    Args:
        trie: AlgebraicTrie instance.
        max_depth: Maximum recursion depth.

    Returns:
        HTML string representation.
    """
    items = list(trie.items()) if hasattr(trie, 'items') else []
    if not items:
        return '<div><i>empty AlgebraicTrie</i></div>'

    html_parts = ["<div style='font-family: monospace;'><b>AlgebraicTrie</b><ul>"]
    for path, val in items[:50]:
        path_str = ' &rarr; '.join(str(p) for p in path)
        html_parts.append(f'<li><code>({path_str})</code> &rArr; <b>{val}</b></li>')
    html_parts.append('</ul></div>')
    return ''.join(html_parts)
