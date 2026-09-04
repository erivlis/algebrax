"""
Jupyter Notebook Rich Display utilities for algebrax structures.
"""

from typing import Any

from algebrax.typing import SparseMatrix, SparseVector

__all__ = [
    'display_matrix',
    'display_trie',
    'display_vector',
    'semiring_card',
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
        return f"<table>{caption}<tbody><tr><td><i>empty matrix</i></td></tr></tbody></table>"

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


def semiring_card(semiring: Any) -> str:
    """
    Return HTML card summarizing a semiring's properties for Jupyter Notebooks.

    Args:
        semiring: An instance of a Semiring.

    Returns:
        HTML string representation of the semiring card.
    """
    name = getattr(semiring, '__class__', type(semiring)).__name__
    doc = getattr(semiring, '__doc__', '') or ''
    first_doc = doc.strip().split('\n')[0] if doc else 'Algebraic Semiring structure.'
    zero_val = getattr(semiring, 'zero', 'N/A')
    one_val = getattr(semiring, 'one', 'N/A')

    card = (
        f"<div style='border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; "
        f'font-family: system-ui, -apple-system, sans-serif; max-width: 480px; '
        f"background-color: #f8fafc; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>"
        f"<div style='font-size: 16px; font-weight: bold; color: #0f172a; margin-bottom: 4px;'>{name}</div>"
        f"<div style='font-size: 13px; color: #475569; margin-bottom: 12px;'>{first_doc}</div>"
        f"<table style='width: 100%; border-collapse: collapse; font-family: monospace; font-size: 13px;'>"
        f"<tr><td style='color: #64748b; padding: 2px 0;'>Identity &oplus; (zero):</td>"
        f"<td style='font-weight: bold; color: #0369a1;'><code>{zero_val}</code></td></tr>"
        f"<tr><td style='color: #64748b; padding: 2px 0;'>Identity &otimes; (one):</td>"
        f"<td style='font-weight: bold; color: #15803d;'><code>{one_val}</code></td></tr>"
        f'</table>'
        f'</div>'
    )
    return card
