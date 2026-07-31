# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
#     "dearpygui",
#     "pillow",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

import json
import math
import os
import random
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import Any

import dearpygui.dearpygui as dpg

from algebrax.analysis import forman_ricci_curvature
from algebrax.automata import dfa_step, nfa_step
from algebrax.probability import (
    cross_entropy,
    entropy,
    kl_divergence,
    markov_steady_state,
    markov_step,
    mutual_information,
)
from algebrax.semiring import ArcticSemiring, Semiring, StandardSemiring, TropicalSemiring
from algebrax.transforms import convolve, dft, hilbert, idft, legendre_fenchel, z_transform

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

TEXTURE_WIDTH: int = 64
TEXTURE_HEIGHT: int = 64

# --- Global State for Curvature Visualization Presets ---
current_nodes: list[int | str] = []
current_edges: list[tuple[int | str, int | str]] = []
current_curvatures: dict[tuple[int | str, int | str], float] = {}
pos: dict[int | str, list[float]] = {}
vel: dict[int | str, list[float]] = {}
dragged_node: int | str | None = None


# --- UI Helper Utilities ---
def create_bordered_table(
        tag: str,
        width: int | None = None,
        height: int | None = None,
        parent: str | int | None = None,
) -> int | str:
    """Helper to create a standard bordered table in DearPyGui."""
    kwargs: dict[str, Any] = {
        'header_row': True,
        'tag': tag,
        'borders_innerH': True,
        'borders_innerV': True,
        'borders_outerH': True,
        'borders_outerV': True,
    }
    if parent:
        kwargs['parent'] = parent
    if width is not None:
        kwargs['width'] = width
    if height is not None:
        kwargs['height'] = height
    return dpg.table(**kwargs)


# Global helper to display matrix in a DearPyGui table
def display_matrix_in_table(matrix: Mapping[Any, Mapping[Any, Any]], table_tag: str) -> None:
    if dpg.does_item_exist(table_tag):
        dpg.delete_item(table_tag, children_only=True)

    if not matrix:
        return

    rows: list[Any] = list(matrix.keys())
    cols: set[Any] = set()
    for r in rows:
        cols.update(matrix[r].keys())
    sorted_cols: list[Any] = sorted(cols)

    dpg.add_table_column(parent=table_tag, label='Row/Col')
    for col in sorted_cols:
        dpg.add_table_column(parent=table_tag, label=str(col))

    for r in sorted(rows):
        with dpg.table_row(parent=table_tag):
            dpg.add_text(str(r))
            for c in sorted_cols:
                val: Any = matrix[r].get(c, '.')
                if isinstance(val, float):
                    val_str = f'{val:.4f}'.rstrip('0').rstrip('.')
                elif isinstance(val, set):
                    sorted_set = sorted(val)
                    val_str = '{' + ', '.join(sorted_set) + '}' if val else '{}'
                elif isinstance(val, tuple) and len(val) == 2:
                    val_str = f'[{val[0]}, {val[1]}]'
                elif isinstance(val, complex):
                    val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                else:
                    val_str = str(val)
                dpg.add_text(val_str)


# --- Custom Semiring for CYK Parsing ---
class GrammarSemiring(Semiring[set[str]]):
    def __init__(self, rules: dict[tuple[str, str], set[str]]) -> None:
        self._rules = rules

    @property
    def zero(self) -> set[str]:
        return set()

    @property
    def one(self) -> set[str]:
        return set()

    def add(self, a: set[str], b: set[str]) -> set[str]:
        return a | b

    def mul(self, a: set[str], b: set[str]) -> set[str]:
        res: set[str] = set()
        for lhs in a:
            for rhs in b:
                if (lhs, rhs) in self._rules:
                    res.update(self._rules[(lhs, rhs)])
        return res


# --- Custom Semiring for Convex Hull (Intervals) ---
class IntervalSemiring(Semiring[tuple[float, float]]):
    @property
    def zero(self) -> tuple[float, float]:
        return (float('inf'), float('-inf'))

    @property
    def one(self) -> tuple[float, float]:
        return (0.0, 0.0)

    def add(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        return (min(a[0], b[0]), max(a[1], b[1]))

    def mul(self, a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
        return (a[0] + b[0], a[1] + b[1])


# --- Callbacks ---


def semiring_change_callback(sender: int | str, app_data: str) -> None:
    semiring_name: str = app_data
    if semiring_name in ('Tropical', 'Arctic'):
        val = '{\n  "0": {"1": 2.0, "2": 8.0},\n  "1": {"2": 3.0},\n  "2": {"0": 1.0}\n}'
    elif semiring_name == 'Viterbi':
        val = '{\n  "0": {"1": 0.5, "2": 0.1},\n  "1": {"2": 0.5},\n  "2": {"0": 0.9}\n}'
    elif semiring_name == 'String':
        val = '{\n  "0": {"1": ["cd"], "2": ["ab"]},\n  "1": {"2": ["bd"]},\n  "2": {"0": ["da"], "1": ["dc"]}\n}'
    elif semiring_name == 'Expectation':
        val = '{\n  "0": {"1": [0.5, 1.0], "2": [0.1, 1.0]},\n  "1": {"2": [0.5, 1.5]},\n  "2": {"0": [0.9, 0.9]}\n}'
    elif semiring_name == 'Provenance':
        val = '{\n  "0": {"1": {"x": 1}, "2": {"z": 1}},\n  "1": {"2": {"y": 1}},\n  "2": {"0": {"w": 1}}\n}'
    elif semiring_name == 'Variance':
        val = '{\n  "0": {"1": [0.5, 1.0, 1.0, 2.0]},\n  "1": {"2": [1.0, 8.0, 8.0, 64.0]}\n}'
    elif semiring_name == 'Digital':
        val = '{\n  "0": {"0": 123, "1": 456},\n  "1": {"0": 789, "1": 12}\n}'
    elif semiring_name == 'Interval (Convex Hull)':
        val = '{\n  "0": {"1": [1.0, 2.0], "2": [3.0, 4.0]},\n  "1": {"2": [5.0, 6.0]}\n}'
    else:  # Standard
        val = '{\n  "0": {"1": 0.5, "2": 0.1},\n  "1": {"2": 0.5},\n  "2": {"0": 0.9}\n}'

    dpg.set_value('semiring_graph_input', val)


def run_semiring_power() -> None:
    semiring_name: str = dpg.get_value('semiring_select')
    power_val: int = dpg.get_value('semiring_power')
    graph_str: str = dpg.get_value('semiring_graph_input')

    try:
        custom_g: dict[str, dict[str, Any]] = json.loads(graph_str)
        parsed_g: dict[Any, dict[Any, Any]] = {}

        if semiring_name == 'Tropical':
            from algebrax.semiring import TropicalSemiring

            semiring: Semiring[Any] = TropicalSemiring()
            parser = float
        elif semiring_name == 'Arctic':
            from algebrax.semiring import ArcticSemiring

            semiring = ArcticSemiring()
            parser = float
        elif semiring_name == 'Viterbi':
            from algebrax.semiring import ViterbiSemiring

            semiring = ViterbiSemiring()
            parser = float
        elif semiring_name == 'String':
            from algebrax.semiring import StringSemiring

            semiring = StringSemiring()
            parser = set
        elif semiring_name == 'Expectation':
            from algebrax.semiring import ExpectationSemiring

            semiring = ExpectationSemiring()

            def parse_expectation(x: list[Any]) -> tuple[float, float]:
                return (float(x[0]), float(x[1]))

            parser = parse_expectation
        elif semiring_name == 'Provenance':
            from algebrax.semiring import ProvenanceSemiring

            semiring = ProvenanceSemiring()

            def parse_provenance(d: dict[str, int]) -> dict[tuple[str, ...], int]:
                return {tuple(k.split(',')) if isinstance(k, str) else tuple(k): int(v) for k, v in d.items()}

            parser = parse_provenance
        elif semiring_name == 'Variance':
            from algebrax.semiring import VarianceSemiring

            semiring = VarianceSemiring()

            def parse_variance(x: list[Any]) -> tuple[float, float, float, float]:
                return (float(x[0]), float(x[1]), float(x[2]), float(x[3]))

            parser = parse_variance
        elif semiring_name == 'Digital':
            from algebrax.semiring import DigitalSemiring

            semiring = DigitalSemiring()
            parser = int
        elif semiring_name == 'Interval (Convex Hull)':
            semiring = IntervalSemiring()

            def parse_interval(x: list[Any]) -> tuple[float, float]:
                return (float(x[0]), float(x[1]))

            parser = parse_interval
        else:
            from algebrax.semiring import StandardSemiring

            semiring = StandardSemiring()
            parser = float

        for u, neighbors in custom_g.items():
            u_key = int(u) if u.isdigit() else u
            row: dict[Any, Any] = {}
            for v, w in neighbors.items():
                v_key = int(v) if v.isdigit() else v
                row[v_key] = parser(w)
            parsed_g[u_key] = row

        from algebrax.matrix.core import power

        res = power(parsed_g, power_val, semiring=semiring)

        display_matrix_in_table(res, 'table_semiring_res')
        dpg.set_value('semiring_status', f'Computed {semiring_name} power {power_val} successfully.')
    except Exception as e:
        dpg.set_value('semiring_status', f'Error: {e}')


def run_curvature() -> None:
    graph_str: str = dpg.get_value('curvature_graph_input')
    is_weighted: bool = dpg.get_value('curvature_weighted')
    is_augmented: bool = dpg.get_value('curvature_augmented')

    try:
        raw_g: dict[str, Any] = json.loads(graph_str)
        graph: dict[Any, dict[Any, float]] = {}
        for u, neighbors in raw_g.items():
            u_key = int(u) if u.isdigit() else u
            if isinstance(neighbors, dict):
                graph[u_key] = {
                    int(v) if v.isdigit() else v: float(w) if is_weighted else 1.0 for v, w in neighbors.items()
                }
            elif isinstance(neighbors, list):
                graph[u_key] = {int(v) if str(v).isdigit() else v: 1.0 for v in neighbors}

        res = forman_ricci_curvature(graph, augmented=is_augmented)

        if dpg.does_item_exist('table_curvature'):
            dpg.delete_item('table_curvature', children_only=True)

        dpg.add_table_column(parent='table_curvature', label='Edge (u, v)')
        dpg.add_table_column(parent='table_curvature', label='Forman-Ricci Curvature')
        dpg.add_table_column(parent='table_curvature', label='Geometry Type')

        for (u, v), k_val in sorted(res.items()):
            if k_val < -1e-5:
                k_type = 'Hyperbolic (K < 0)'
            elif k_val > 1e-5:
                k_type = 'Spherical (K > 0)'
            else:
                k_type = 'Flat / Euclidean (K = 0)'

            with dpg.table_row(parent='table_curvature'):
                dpg.add_text(f'({u}, {v})')
                dpg.add_text(f'{k_val:.4f}')
                dpg.add_text(k_type)

        dpg.set_value('curvature_status', 'Successfully computed Forman-Ricci curvature.')
    except Exception as e:
        dpg.set_value('curvature_status', f'Error: {e}')


def run_crypto_exchange() -> None:
    from algebrax.matrix.core import dot
    from algebrax.semiring import DigitalSemiring

    try:
        s_semiring = DigitalSemiring()
        a1: int = int(dpg.get_value('crypto_a1'))
        a2: int = int(dpg.get_value('crypto_a2'))
        b1: int = int(dpg.get_value('crypto_b1'))
        b2: int = int(dpg.get_value('crypto_b2'))

        m_mat: dict[int, dict[int, int]] = {0: {0: 123, 1: 456}, 1: {0: 789, 1: 12}}
        a_mat: dict[int, dict[int, int]] = {0: {0: a1, 1: a2}, 1: {0: a2, 1: a1}}
        b_mat: dict[int, dict[int, int]] = {0: {0: b1, 1: b2}, 1: {0: b2, 1: b1}}

        am_mat = dot(a_mat, m_mat, s_semiring)
        u_mat = dot(am_mat, a_mat, s_semiring)

        bm_mat = dot(b_mat, m_mat, s_semiring)
        v_mat = dot(bm_mat, b_mat, s_semiring)

        av_mat = dot(a_mat, v_mat, s_semiring)
        ka_mat = dot(av_mat, a_mat, s_semiring)

        bu_mat = dot(b_mat, u_mat, s_semiring)
        kb_mat = dot(bu_mat, b_mat, s_semiring)

        display_matrix_in_table(u_mat, 'table_crypto_u')
        display_matrix_in_table(v_mat, 'table_crypto_v')
        display_matrix_in_table(ka_mat, 'table_crypto_ka')
        display_matrix_in_table(kb_mat, 'table_crypto_kb')

        match: bool = ka_mat == kb_mat
        dpg.set_value('crypto_match_text', f'Keys Match: {match}')
        dpg.set_value('crypto_status', 'Successfully performed key exchange simulation.')
    except Exception as e:
        dpg.set_value('crypto_status', f'Error: {e}')


def run_trie_operations() -> None:
    from algebrax.semiring import StandardSemiring
    from algebrax.trie import AlgebraicTrie

    try:
        trie: AlgebraicTrie[Any, float] = AlgebraicTrie(semiring=StandardSemiring)
        points_str: str = dpg.get_value('trie_points_input')
        points: list[tuple[list[Any], float]] = json.loads(points_str)

        for coord, val in points:
            trie.add(tuple(coord), float(val))

        contract_dim_str: str = dpg.get_value('trie_contract_dims')
        contract_dims: tuple[int, ...] = tuple(json.loads(contract_dim_str))

        res = trie.contract(contract_dims)

        trie_lines: list[str] = []
        for path in sorted(trie):
            trie_lines.append(f'  Path {path}: {trie[path]}')

        dpg.set_value('trie_contents_text', '\n'.join(trie_lines))
        dpg.set_value('trie_result_text', f'Contracted Result at {contract_dims}: {res}')
        dpg.set_value('trie_status', 'Successfully performed trie operations.')
    except Exception as e:
        dpg.set_value('trie_status', f'Error: {e}')


def run_pagerank() -> None:
    graph_str: str = dpg.get_value('pagerank_graph')
    alpha: float = dpg.get_value('pagerank_alpha')
    iterations: int = dpg.get_value('pagerank_iterations')

    try:
        graph: dict[str, dict[str, float]] = json.loads(graph_str)

        m_matrix: dict[str, dict[str, float]] = {}
        nodes: set[str] = set(graph.keys())
        for u, neighbors in graph.items():
            nodes.update(neighbors.keys())
            degree = len(neighbors)
            if degree > 0:
                m_matrix[u] = dict.fromkeys(neighbors, 1.0 / degree)
            else:
                m_matrix[u] = {u: 1.0}

        all_nodes: list[str] = sorted(nodes)
        n_nodes: int = len(all_nodes)

        v_vec: dict[str, float] = dict.fromkeys(all_nodes, 1.0 / n_nodes)

        from algebrax.matrix.core import dot
        from algebrax.semiring import StandardSemiring

        semiring = StandardSemiring()

        for _ in range(iterations):
            v_matrix = {0: v_vec}
            res_matrix = dot(v_matrix, m_matrix, semiring=semiring)
            v_next_raw: dict[str, float] = res_matrix.get(0, {})

            v_next: dict[str, float] = {}
            teleport = (1.0 - alpha) / n_nodes
            for node in all_nodes:
                val = v_next_raw.get(node, 0.0)
                v_next[node] = alpha * val + teleport
            v_vec = v_next

        if dpg.does_item_exist('table_pagerank'):
            dpg.delete_item('table_pagerank', children_only=True)

        dpg.add_table_column(parent='table_pagerank', label='Node')
        dpg.add_table_column(parent='table_pagerank', label='Rank')

        sorted_ranks = sorted(v_vec.items(), key=lambda x: x[1], reverse=True)
        for node, rank in sorted_ranks:
            with dpg.table_row(parent='table_pagerank'):
                dpg.add_text(str(node))
                dpg.add_text(f'{rank:.6f}')

        dpg.set_value('pagerank_status', 'Successfully computed PageRank.')
    except Exception as e:
        dpg.set_value('pagerank_status', f'Error: {e}')


def run_cyk_parsing() -> None:
    sentence_str: str = dpg.get_value('cyk_sentence')
    lexicon_str: str = dpg.get_value('cyk_lexicon')
    rules_str: str = dpg.get_value('cyk_rules')

    try:
        sentence: list[str] = sentence_str.strip().split()
        parsed_lexicon: dict[str, list[str]] = json.loads(lexicon_str)
        parsed_rules: dict[str, list[str]] = json.loads(rules_str)

        lexicon: dict[str, set[str]] = {k: set(v) for k, v in parsed_lexicon.items()}
        rules: dict[tuple[str, ...], set[str]] = {tuple(k.split(',')): set(v) for k, v in parsed_rules.items()}

        n_len: int = len(sentence)
        chart: dict[int, dict[int, set[str]]] = {}
        for i, word in enumerate(sentence):
            if i not in chart:
                chart[i] = {}
            chart[i][i + 1] = lexicon.get(word, set())

        from algebrax.matrix.core import dot

        semiring = GrammarSemiring(rules)

        for _ in range(n_len):
            new_spans = dot(chart, chart, semiring=semiring)
            for r, row in new_spans.items():
                if r not in chart:
                    chart[r] = {}
                for c, val in row.items():
                    current = chart[r].get(c, set())
                    chart[r][c] = current | val

        final_tags = chart.get(0, {}).get(n_len, set())

        dpg.set_value('cyk_result_text', f'Sentence parses as final non-terminals: {list(final_tags)}')
        display_matrix_in_table(chart, 'table_cyk_chart')
        dpg.set_value('cyk_status', 'Successfully parsed sentence.')
    except Exception as e:
        dpg.set_value('cyk_status', f'Error: {e}')


def run_legendre_fenchel() -> None:
    signal_str: str = dpg.get_value('fenchel_signal')
    slopes_str: str = dpg.get_value('fenchel_slopes')

    try:
        signal: dict[str, float] = json.loads(signal_str)
        parsed_signal: dict[int | float, float] = {
            float(k) if '.' in k else int(k): float(v) for k, v in signal.items()
        }
        slopes: list[float] = json.loads(slopes_str)

        if dpg.does_item_exist('table_fenchel'):
            dpg.delete_item('table_fenchel', children_only=True)

        dpg.add_table_column(parent='table_fenchel', label='Slope (s)')
        dpg.add_table_column(parent='table_fenchel', label='Convex Conjugate f*(s)')

        for s in sorted(slopes):
            val = legendre_fenchel(parsed_signal, s)
            with dpg.table_row(parent='table_fenchel'):
                dpg.add_text(f'{s:.2f}'.rstrip('0').rstrip('.'))
                dpg.add_text(f'{val:.4f}'.rstrip('0').rstrip('.'))

        dpg.set_value('fenchel_status', 'Successfully computed Fenchel-Legendre Transform.')
    except Exception as e:
        dpg.set_value('fenchel_status', f'Error: {e}')


def automata_type_callback(sender: int | str, app_data: str) -> None:
    m_type: str = app_data
    if m_type == 'DFA':
        dpg.set_value(
            'automata_transitions',
            '{\n  "q0": {"0": "q0", "1": "q1"},\n  "q1": {"0": "q2", "1": "q0"},\n  "q2": {"0": "q1", "1": "q2"}\n}',
        )
        dpg.set_value('automata_start', '"q0"')
        dpg.set_value('automata_accept', '["q1"]')
        dpg.set_value('automata_input', '1010')
    else:  # NFA
        dpg.set_value(
            'automata_transitions',
            '{\n  "q0": {\n    "0": {"q0": 0.5, "q1": 0.5},\n    "1": {"q1": 1.0}\n  },\n'
            '  "q1": {\n    "0": {"q2": 1.0},\n    "1": {"q0": 0.5, "q2": 0.5}\n  },\n'
            '  "q2": {\n    "0": {"q2": 1.0},\n    "1": {"q2": 1.0}\n  }\n}',
        )
        dpg.set_value('automata_start', '{"q0": 1.0}')
        dpg.set_value('automata_accept', '["q2"]')
        dpg.set_value('automata_input', '01')


def _simulate_dfa_step_by_step(
        seq: list[str],
        start_str: str,
        accept_states: list[Any],
        transitions: dict[Any, dict[Any, Any]],
) -> tuple[list[str], str, tuple[int, int, int]]:
    start_state: Any = start_str.strip().strip('"').strip("'")
    if isinstance(start_state, str) and start_state.isdigit():
        start_state = int(start_state)

    normalized_transitions: dict[Any, dict[Any, Any]] = {}
    for s, trans in transitions.items():
        s_key = int(s) if str(s).isdigit() else s
        normalized_transitions[s_key] = {}
        for sym, ns in trans.items():
            sym_key = int(sym) if str(sym).isdigit() else sym
            ns_val = int(ns) if isinstance(ns, str) and ns.isdigit() else ns
            normalized_transitions[s_key][sym_key] = ns_val

    normalized_accept: set[Any] = {int(ac) if isinstance(ac, str) and ac.isdigit() else ac for ac in accept_states}

    current: Any = start_state
    steps_log: list[str] = [f'Start state: {current}']

    for idx, symbol in enumerate(seq):
        sym_key = int(symbol) if symbol.isdigit() else symbol
        next_state = dfa_step(current, sym_key, normalized_transitions)
        if next_state is None:
            steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> No transition defined from '{current}' (Crashed)")
            current = None
            break
        steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> {current} to {next_state}")
        current = next_state

    if current is not None and current in normalized_accept:
        status = f'ACCEPTED (Final state: {current})'
        status_color = (100, 255, 100)
    else:
        status = f'REJECTED (Final state: {current})'
        status_color = (255, 100, 100)
    return steps_log, status, status_color


def _simulate_nfa_step_by_step(
        seq: list[str],
        start_str: str,
        accept_states: list[Any],
        transitions: dict[Any, dict[Any, Any]],
) -> tuple[list[str], str, tuple[int, int, int]]:
    start_states: Any = json.loads(start_str)
    if isinstance(start_states, str):
        s_val = int(start_states) if start_states.isdigit() else start_states
        start_dist: dict[Any, float] = {s_val: 1.0}
    elif isinstance(start_states, list):
        start_dist = {int(s) if str(s).isdigit() else s: 1.0 for s in start_states}
    elif isinstance(start_states, dict):
        start_dist = {int(k) if str(k).isdigit() else k: float(v) for k, v in start_states.items()}
    else:
        start_dist = {}

    if not start_dist:
        return (
            ['Error: Invalid format for start states.'],
            'REJECTED (Error)',
            (255, 100, 100),
        )

    normalized_transitions: dict[Any, dict[Any, dict[Any, float]]] = {}
    for s, trans in transitions.items():
        s_key = int(s) if str(s).isdigit() else s
        normalized_transitions[s_key] = {}
        for sym, nexts in trans.items():
            sym_key = int(sym) if str(sym).isdigit() else sym
            normalized_transitions[s_key][sym_key] = {}
            if isinstance(nexts, list):
                for ns in nexts:
                    ns_key = int(ns) if str(ns).isdigit() else ns
                    normalized_transitions[s_key][sym_key][ns_key] = 1.0
            elif isinstance(nexts, dict):
                for ns, w in nexts.items():
                    ns_key = int(ns) if str(ns).isdigit() else ns
                    normalized_transitions[s_key][sym_key][ns_key] = float(w)
            else:
                ns_key = int(nexts) if str(nexts).isdigit() else nexts
                normalized_transitions[s_key][sym_key][ns_key] = 1.0

    normalized_accept = {int(ac) if isinstance(ac, str) and ac.isdigit() else ac for ac in accept_states}

    current = start_dist
    steps_log = [f'Start states distribution: {current}']

    for idx, symbol in enumerate(seq):
        sym_key = int(symbol) if symbol.isdigit() else symbol
        next_states = nfa_step(current, sym_key, normalized_transitions)
        if not next_states:
            steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> No active transitions (Crashed)")
            current = {}
            break
        steps_log.append(f"Step {idx + 1}: Symbol '{symbol}' -> Distribution: {next_states}")
        current = next_states

    accept_weight = sum(w for s, w in current.items() if s in normalized_accept)
    if accept_weight > 1e-9:
        status = f'ACCEPTED (Accepting Weight: {accept_weight:.4f})'
        status_color = (100, 255, 100)
    else:
        status = 'REJECTED (No accepting weight)'
        status_color = (255, 100, 100)
    return steps_log, status, status_color


def run_automata_sim() -> None:
    auto_type: str = dpg.get_value('automata_type')
    start_str: str = dpg.get_value('automata_start')
    accept_str: str = dpg.get_value('automata_accept')
    input_str: str = dpg.get_value('automata_input')
    trans_str: str = dpg.get_value('automata_transitions')

    try:
        accept_states: list[Any] = json.loads(accept_str)
        transitions: dict[Any, dict[Any, Any]] = json.loads(trans_str)

        seq: list[str] = (
            [s.strip() for s in input_str.split(',') if s.strip()] if ',' in input_str else list(input_str.strip())
        )

        if auto_type == 'DFA':
            steps_log, status, status_color = _simulate_dfa_step_by_step(seq, start_str, accept_states, transitions)
        else:
            steps_log, status, status_color = _simulate_nfa_step_by_step(seq, start_str, accept_states, transitions)

        dpg.set_value('automata_result_text', status)
        dpg.configure_item('automata_result_text', color=status_color)
        dpg.set_value('automata_log_text', '\n'.join(steps_log))
        dpg.set_value('automata_status', f'Successfully simulated {auto_type}.')
    except Exception as e:
        dpg.set_value('automata_status', f'Error: {e}')


def run_markov_simulation() -> None:
    matrix_str: str = dpg.get_value('markov_matrix')
    state_str: str = dpg.get_value('markov_state')
    steps: int = dpg.get_value('markov_steps')

    try:
        raw_matrix: dict[str, dict[str, float]] = json.loads(matrix_str)
        raw_state: dict[str, float] = json.loads(state_str)

        matrix: dict[Any, dict[Any, float]] = {
            int(u) if u.isdigit() else u: {int(v) if v.isdigit() else v: float(w) for v, w in n.items()}
            for u, n in raw_matrix.items()
        }
        state: dict[Any, float] = {int(k) if k.isdigit() else k: float(v) for k, v in raw_state.items()}

        curr_state = state
        for _ in range(steps):
            curr_state = markov_step(curr_state, matrix)

        steady = markov_steady_state(matrix)

        if dpg.does_item_exist('table_markov_steps'):
            dpg.delete_item('table_markov_steps', children_only=True)
        if dpg.does_item_exist('table_markov_steady'):
            dpg.delete_item('table_markov_steady', children_only=True)

        dpg.add_table_column(parent='table_markov_steps', label='State')
        dpg.add_table_column(parent='table_markov_steps', label='Prob')
        for s_key, prob in sorted(curr_state.items()):
            with dpg.table_row(parent='table_markov_steps'):
                dpg.add_text(str(s_key))
                dpg.add_text(f'{prob:.4f}')

        dpg.add_table_column(parent='table_markov_steady', label='State')
        dpg.add_table_column(parent='table_markov_steady', label='Steady Prob')
        for s_key, prob in sorted(steady.items()):
            with dpg.table_row(parent='table_markov_steady'):
                dpg.add_text(str(s_key))
                dpg.add_text(f'{prob:.4f}')

        dpg.set_value('markov_status', f'Successfully computed {steps} Markov step(s) & steady state.')
    except Exception as e:
        dpg.set_value('markov_status', f'Error: {e}')


def run_info_theory() -> None:
    p_str: str = dpg.get_value('info_p')
    q_str: str = dpg.get_value('info_q')
    joint_str: str = dpg.get_value('info_joint')

    try:
        p_dist: dict[Any, float] = {int(k) if k.isdigit() else k: float(v) for k, v in json.loads(p_str).items()}
        q_dist: dict[Any, float] = {int(k) if k.isdigit() else k: float(v) for k, v in json.loads(q_str).items()}

        raw_joint: dict[str, dict[str, float]] = json.loads(joint_str)
        joint_dist: dict[Any, dict[Any, float]] = {
            int(u) if u.isdigit() else u: {int(v) if v.isdigit() else v: float(w) for v, w in n.items()}
            for u, n in raw_joint.items()
        }

        h_p = entropy(p_dist)
        h_q = entropy(q_dist)
        h_cross = cross_entropy(p_dist, q_dist)
        kl_div = kl_divergence(p_dist, q_dist)
        mi_val = mutual_information(joint_dist)

        dpg.set_value('info_hp_val', f'{h_p:.4f} bits')
        dpg.set_value('info_hq_val', f'{h_q:.4f} bits')
        dpg.set_value('info_hcross_val', f'{h_cross:.4f} bits')
        dpg.set_value('info_kl_val', f'{kl_div:.4f} bits')
        dpg.set_value('info_mi_val', f'{mi_val:.4f} bits')

        dpg.set_value('info_status', 'Successfully computed information metrics.')
    except Exception as e:
        dpg.set_value('info_status', f'Error: {e}')


def signal_op_change_callback(sender: int | str, app_data: str) -> None:
    op: str = app_data
    dpg.show_item('signal_g_group') if op == 'Convolution' else dpg.hide_item('signal_g_group')
    dpg.show_item('signal_z_group') if op == 'Z-Transform' else dpg.hide_item('signal_z_group')


def run_signal_transforms() -> None:
    op: str = dpg.get_value('signal_op_select')
    f_str: str = dpg.get_value('signal_f')

    try:
        raw_f: dict[str, Any] = json.loads(f_str)
        f_vec: dict[int, Any] = {int(k): complex(v) if isinstance(v, str) else float(v) for k, v in raw_f.items()}

        if op == 'DFT':
            res = dft(f_vec)
        elif op == 'IDFT':
            res = idft(f_vec)
        elif op == 'Hilbert Transform':
            res = hilbert(f_vec)
        elif op == 'Convolution':
            g_str: str = dpg.get_value('signal_g')
            raw_g: dict[str, Any] = json.loads(g_str)
            g_vec = {int(k): float(v) for k, v in raw_g.items()}
            res = convolve(f_vec, g_vec)
        elif op == 'Z-Transform':
            z_str: str = dpg.get_value('signal_z_input')
            z_val = complex(z_str)
            res_val = z_transform(f_vec, z_val)
            res = {0: res_val}
        else:
            res = {}

        if dpg.does_item_exist('table_signal_res'):
            dpg.delete_item('table_signal_res', children_only=True)

        dpg.add_table_column(parent='table_signal_res', label='Index (k/t)')
        dpg.add_table_column(parent='table_signal_res', label='Value / Coefficient')

        for k in sorted(res.keys()):
            val = res[k]
            with dpg.table_row(parent='table_signal_res'):
                dpg.add_text(str(k))
                if isinstance(val, complex):
                    val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                else:
                    val_str = f'{val:.4f}'
                dpg.add_text(val_str)

        dpg.set_value('signal_status', f'Successfully evaluated {op}.')
    except Exception as e:
        dpg.set_value('signal_status', f'Error: {e}')


# --- Image Convolution Helpers ---
IMAGE_PRESETS: dict[str, str] = {
    'Cross Pattern (8x8)': (
        '{\n'
        '  "0,3": 1.0, "1,3": 1.0, "2,3": 1.0, "3,3": 1.0, "4,3": 1.0, "5,3": 1.0, "6,3": 1.0, "7,3": 1.0,\n'
        '  "3,0": 1.0, "3,1": 1.0, "3,2": 1.0, "3,4": 1.0, "3,5": 1.0, "3,6": 1.0, "3,7": 1.0\n'
        '}'
    ),
    'Diagonal Line (8x8)': (
        '{\n  "0,0": 1.0, "1,1": 1.0, "2,2": 1.0, "3,3": 1.0,\n  "4,4": 1.0, "5,5": 1.0, "6,6": 1.0, "7,7": 1.0\n}'
    ),
    'Box Square (8x8)': (
        '{\n'
        '  "2,2": 1.0, "2,3": 1.0, "2,4": 1.0, "2,5": 1.0,\n'
        '  "3,2": 1.0, "3,5": 1.0, "4,2": 1.0, "4,5": 1.0,\n'
        '  "5,2": 1.0, "5,3": 1.0, "5,4": 1.0, "5,5": 1.0\n'
        '}'
    ),
}

KERNEL_PRESETS: dict[str, str] = {
    'Sobel Horizontal (Edge)': (
        '{\n  "-1,-1": -1.0, "-1,0": -2.0, "-1,1": -1.0,\n  "1,-1": 1.0, "1,0": 2.0, "1,1": 1.0\n}'
    ),
    'Sobel Vertical (Edge)': (
        '{\n  "-1,-1": -1.0, "0,-1": -2.0, "1,-1": -1.0,\n  "-1,1": 1.0, "0,1": 2.0, "1,1": 1.0\n}'
    ),
    'Gaussian Blur (3x3)': (
        '{\n'
        '  "-1,-1": 0.0625, "-1,0": 0.125, "-1,1": 0.0625,\n'
        '  "0,-1": 0.125, "0,0": 0.25, "0,1": 0.125,\n'
        '  "1,-1": 0.0625, "1,0": 0.125, "1,1": 0.0625\n'
        '}'
    ),
    'Sharpen Kernel': '{\n  "0,-1": -1.0, "-1,0": -1.0, "0,0": 5.0, "1,0": -1.0, "0,1": -1.0\n}',
    'Morphological Dilation (Max-Plus)': '{\n  "0,-1": 0.0, "-1,0": 0.0, "0,0": 0.0, "1,0": 0.0, "0,1": 0.0\n}',
}


def image_preset_change_callback(sender: int | str, app_data: str) -> None:
    if app_data in IMAGE_PRESETS:
        dpg.set_value('img_conv_image_input', IMAGE_PRESETS[app_data])


def kernel_preset_change_callback(sender: int | str, app_data: str) -> None:
    if app_data in KERNEL_PRESETS:
        dpg.set_value('img_conv_kernel_input', KERNEL_PRESETS[app_data])


def open_file_dialog_callback(sender: int | str, app_data: Any) -> None:
    def file_selected_callback(sender: int | str, app_data: dict[str, Any]) -> None:
        if 'file_path_name' in app_data:
            filepath: str = app_data['file_path_name']
            dpg.set_value('img_conv_filepath_input', filepath)
            load_image_file_into_lab(filepath)

    with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=file_selected_callback,
            width=700,
            height=400,
            modal=True,
    ):
        dpg.add_file_extension('.*', color=(255, 255, 255, 255))
        dpg.add_file_extension('.png', color=(0, 255, 0, 255))
        dpg.add_file_extension('.jpg', color=(0, 255, 0, 255))
        dpg.add_file_extension('.bmp', color=(0, 255, 0, 255))


def load_image_file_into_lab(filepath: str) -> None:
    if not HAS_PILLOW:
        dpg.set_value('img_conv_status', 'Error: Pillow library is not installed.')
        return

    try:
        img = Image.open(filepath).convert('L')
        img = img.resize((TEXTURE_WIDTH, TEXTURE_HEIGHT), Image.Resampling.BILINEAR)

        dict_image: dict[str, float] = {}
        texture_data: list[float] = []
        for r in range(TEXTURE_HEIGHT):
            for c in range(TEXTURE_WIDTH):
                pixel: int = img.getpixel((c, r))
                norm_val: float = pixel / 255.0
                if norm_val > 1e-4:
                    dict_image[f'{r},{c}'] = round(norm_val, 4)
                texture_data.extend([norm_val, norm_val, norm_val, 1.0])

        dpg.set_value('img_conv_image_input', json.dumps(dict_image, indent=2))
        dpg.set_value('texture_img_input', texture_data)
        dpg.set_value('img_conv_status', f'Successfully loaded and downsampled image: {filepath}')
    except Exception as e:
        dpg.set_value('img_conv_status', f'Error loading image: {e}')


def _update_texture_from_2d_dict(data_dict: Mapping[tuple[int, int], float], texture_tag: str) -> None:
    texture_data: list[float] = []
    max_val: float = max(data_dict.values(), default=1.0)
    min_val: float = min(data_dict.values(), default=0.0)
    val_range: float = max_val - min_val if max_val != min_val else 1.0

    for r in range(TEXTURE_HEIGHT):
        for c in range(TEXTURE_WIDTH):
            val = data_dict.get((r, c), 0.0)
            norm = (val - min_val) / val_range
            texture_data.extend([norm, norm, norm, 1.0])

    dpg.set_value(texture_tag, texture_data)


def run_image_convolution_2d() -> None:
    img_str: str = dpg.get_value('img_conv_image_input')
    kernel_str: str = dpg.get_value('img_conv_kernel_input')
    semiring_name: str = dpg.get_value('img_conv_semiring_select')

    try:
        raw_img: dict[str, float] = json.loads(img_str)
        raw_kernel: dict[str, float] = json.loads(kernel_str)

        image_2d: dict[tuple[int, int], float] = {}
        for k, v in raw_img.items():
            r, c = map(int, k.split(','))
            image_2d[(r, c)] = float(v)

        kernel_2d: dict[tuple[int, int], float] = {}
        for k, v in raw_kernel.items():
            r, c = map(int, k.split(','))
            kernel_2d[(r, c)] = float(v)

        if 'Arctic' in semiring_name:
            semiring: Semiring[float] = ArcticSemiring()
        elif 'Tropical' in semiring_name:
            semiring = TropicalSemiring()
        else:
            semiring = StandardSemiring()

        def add_2d(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
            return (p1[0] + p2[0], p1[1] + p2[1])

        convolved_2d = convolve(image_2d, kernel_2d, key_op=add_2d, semiring=semiring)

        _update_texture_from_2d_dict(image_2d, 'texture_img_input')
        _update_texture_from_2d_dict(convolved_2d, 'texture_img_output')

        rows = [r for r, c in convolved_2d]
        cols = [c for r, c in convolved_2d]
        min_r, max_r = (min(rows), max(rows)) if rows else (0, 7)
        min_c, max_c = (min(cols), max(cols)) if cols else (0, 7)

        ascii_lines: list[str] = []
        density_chars = ' .:-=+*#%@'
        for r in range(min_r, min(max_r + 1, min_r + 16)):
            line = ''
            for c in range(min_c, min(max_c + 1, min_c + 16)):
                val = convolved_2d.get((r, c), 0.0)
                char_idx = int(max(0.0, min(1.0, val)) * (len(density_chars) - 1))
                line += density_chars[char_idx] + ' '
            ascii_lines.append(line)

        dpg.set_value('img_conv_ascii_preview', '\n'.join(ascii_lines))

        display_matrix: dict[int, dict[int, float]] = {}
        for (r, c), val in convolved_2d.items():
            if r not in display_matrix:
                display_matrix[r] = {}
            display_matrix[r][c] = val
        display_matrix_in_table(display_matrix, 'table_img_conv_res')

        dpg.set_value('img_conv_status', 'Successfully evaluated 2D spatial convolution!')
    except Exception as e:
        dpg.set_value('img_conv_status', f'Error: {e}')


# --- Network Curvature Physics Simulator Callbacks ---


def _all_node_pairs(nodes: list[int | str]) -> Iterator[tuple[int | str, int | str]]:
    for i, u in enumerate(nodes):
        for v in nodes[i + 1:]:
            yield u, v


def _apply_pairwise_forces(
        pairs: Iterable[tuple[int | str, int | str]],
        force_func: Callable[[float], float],
        forces: dict[int | str, list[float]],
        epsilon: float = 1e-4,
) -> None:
    for u, v in pairs:
        dx = pos[u][0] - pos[v][0]
        dy = pos[u][1] - pos[v][1]
        dist = math.sqrt(dx * dx + dy * dy) + epsilon
        f_mag = force_func(dist)
        fx = (dx / dist) * f_mag
        fy = (dy / dist) * f_mag
        forces[u][0] += fx
        forces[u][1] += fy
        forces[v][0] -= fx
        forces[v][1] -= fy


def _qcd_force(dist: float, k_repulsion: float = 6000.0) -> float:
    return k_repulsion / (dist * dist + 1.0) * (1.0 if dist > 0 else -1.0)


def _coulomb_force(dist: float, k_repulsion: float = 6000.0) -> float:
    return k_repulsion / (dist * dist + 1.0)


def _hooke_force(dist: float, k_spring: float = 0.08, l_rest: float = 120.0) -> float:
    return -k_spring * (dist - l_rest)


def _compute_physics_forces() -> None:
    damping = 0.85
    forces: dict[int | str, list[float]] = {u: [0.0, 0.0] for u in current_nodes}

    # Coulomb Repulsion across all node pairs
    _apply_pairwise_forces(_all_node_pairs(current_nodes), _coulomb_force, forces)

    # Hooke Spring Attraction along graph edges
    _apply_pairwise_forces(current_edges, _hooke_force, forces)

    # Center Gravity Pull
    center_x, center_y = 350.0, 225.0
    for u in current_nodes:
        forces[u][0] += (center_x - pos[u][0]) * 0.005
        forces[u][1] += (center_y - pos[u][1]) * 0.005

    # Update Positions
    for u in current_nodes:
        if u == dragged_node:
            vel[u] = [0.0, 0.0]
            continue
        vel[u][0] = (vel[u][0] + forces[u][0] * 0.1) * damping
        vel[u][1] = (vel[u][1] + forces[u][1] * 0.1) * damping
        pos[u][0] = max(30.0, min(670.0, pos[u][0] + vel[u][0]))
        pos[u][1] = max(30.0, min(420.0, pos[u][1] + vel[u][1]))


def _handle_mouse_dragging() -> None:
    global dragged_node
    if not pos:
        return

    mouse_pos: list[float] = dpg.get_drawing_mouse_pos()
    is_left_down: bool = dpg.is_mouse_button_down(dpg.mvMouseButton_Left)

    if is_left_down:
        if dragged_node is None:
            for u in current_nodes:
                p = pos[u]
                dx = mouse_pos[0] - p[0]
                dy = mouse_pos[1] - p[1]
                if math.sqrt(dx * dx + dy * dy) <= 18.0:
                    dragged_node = u
                    break
        else:
            pos[dragged_node][0] = max(30.0, min(670.0, mouse_pos[0]))
            pos[dragged_node][1] = max(30.0, min(420.0, mouse_pos[1]))
    else:
        dragged_node = None


def recalculate_and_reset_layout() -> None:
    global current_nodes, current_edges, current_curvatures, pos, vel
    preset: str = dpg.get_value('vis_preset')
    is_augmented: bool = dpg.get_value('vis_augmented')

    graph: dict[int | str, dict[int | str, float]] = {}
    if preset == 'Barbell Graph':
        graph = {
            1: {2: 1, 3: 1},
            2: {1: 1, 3: 1},
            3: {1: 1, 2: 1, 4: 1},
            4: {3: 1, 5: 1, 6: 1},
            5: {4: 1, 6: 1},
            6: {4: 1, 5: 1},
        }
    elif preset == 'Star Graph':
        graph = {1: {2: 1, 3: 1, 4: 1, 5: 1, 6: 1}, 2: {1: 1}, 3: {1: 1}, 4: {1: 1}, 5: {1: 1}, 6: {1: 1}}
    elif preset == 'Cycle Graph':
        graph = {1: {2: 1, 6: 1}, 2: {1: 1, 3: 1}, 3: {2: 1, 4: 1}, 4: {3: 1, 5: 1}, 5: {4: 1, 6: 1}, 6: {5: 1, 1: 1}}
    elif preset == 'Tree Graph':
        graph = {1: {2: 1, 3: 1}, 2: {1: 1, 4: 1, 5: 1}, 3: {1: 1, 6: 1}, 4: {2: 1}, 5: {2: 1}, 6: {3: 1}}
    elif preset == 'Grid Graph':
        graph = {
            1: {2: 1, 4: 1},
            2: {1: 1, 3: 1, 5: 1},
            3: {2: 1, 6: 1},
            4: {1: 1, 5: 1},
            5: {2: 1, 4: 1, 6: 1},
            6: {3: 1, 5: 1},
        }

    current_nodes = sorted(graph.keys())  # type: ignore
    edges_set: set[tuple[int | str, int | str]] = set()
    for u, neighbors in graph.items():
        for v in neighbors:
            if u < v:  # type: ignore
                edges_set.add((u, v))
            elif v < u:  # type: ignore
                edges_set.add((v, u))
    current_edges = sorted(edges_set)

    current_curvatures = forman_ricci_curvature(graph, augmented=is_augmented)

    # Reset positions
    random.seed(42)
    pos = {}
    vel = {}
    for i, u in enumerate(current_nodes):
        angle = (2 * math.pi * i) / len(current_nodes)
        radius = 140.0
        pos[u] = [350.0 + radius * math.cos(angle), 225.0 + radius * math.sin(angle)]
        vel[u] = [0.0, 0.0]

    # Update Chart Plot
    if dpg.does_item_exist('curvature_plot_series'):
        dpg.delete_item('curvature_plot_series')

    x_data = list(range(1, len(current_edges) + 1))
    y_data = [current_curvatures.get(edge, 0.0) for edge in current_edges]

    dpg.add_line_series(
        x_data,
        y_data,
        label='Forman-Ricci Curvature K',
        parent='curvature_y_axis',
        tag='curvature_plot_series',
    )
    dpg.set_value('vis_status', f'Loaded {preset} ({len(current_nodes)} nodes, {len(current_edges)} edges).')


def jostle_graph_callback() -> None:
    for u in current_nodes:
        vel[u] = [random.uniform(-15.0, 15.0), random.uniform(-15.0, 15.0)]


def _redraw_canvas() -> None:
    if not dpg.does_item_exist('vis_canvas'):
        return
    dpg.delete_item('vis_canvas', children_only=True)

    # Draw Edges
    for u, v in current_edges:
        p1 = pos[u]
        p2 = pos[v]
        k_val = current_curvatures.get((u, v), current_curvatures.get((v, u), 0.0))

        if k_val < -1e-5:
            color = (255, 80, 80, 220)
            thickness = max(1.5, min(8.0, 1.5 - 3.0 * k_val))
        elif k_val > 1e-5:
            color = (80, 180, 255, 220)
            thickness = max(1.5, min(8.0, 1.5 + 3.0 * k_val))
        else:
            color = (200, 200, 200, 128)
            thickness = 1.5

        dpg.draw_line(p1, p2, color=color, thickness=thickness, parent='vis_canvas')
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        dpg.draw_text((mid_x - 12, mid_y - 8), f'{k_val:.2f}', color=(220, 220, 220), size=12, parent='vis_canvas')

    # Draw Nodes
    for u in current_nodes:
        p = pos[u]
        dpg.draw_circle(p, radius=14, color=(140, 140, 180), fill=(48, 48, 72), thickness=2, parent='vis_canvas')
        dpg.draw_text((p[0] - 6, p[1] - 9), str(u), color=(255, 255, 255), size=14, parent='vis_canvas')


def update_graph_simulation() -> None:
    run_physics: bool = dpg.get_value('vis_run_physics')
    if run_physics and pos:
        _compute_physics_forces()
    _handle_mouse_dragging()
    _redraw_canvas()


# --- View Builder Functions ---


def build_view_semiring() -> None:
    with dpg.group(tag='view_semiring_matrix_power_group', show=True):
        dpg.add_text(
            'Evaluate matrix multiplication and powers over various algebraic semirings.', color=(180, 180, 180)
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Select Semiring:')
            dpg.add_combo(
                [
                    'Standard',
                    'Tropical',
                    'Arctic',
                    'Viterbi',
                    'String',
                    'Expectation',
                    'Provenance',
                    'Variance',
                    'Digital',
                    'Interval (Convex Hull)',
                ],
                default_value='Standard',
                callback=semiring_change_callback,
                tag='semiring_select',
                width=200,
            )
            dpg.add_text('Matrix Power:')
            dpg.add_input_int(default_value=2, min_value=1, tag='semiring_power', width=100)

        dpg.add_text('Adjacency Graph (JSON format):')
        default_graph = '{\n  "0": {"1": 0.5, "2": 0.1},\n  "1": {"2": 0.5},\n  "2": {"0": 0.9}\n}'
        dpg.add_input_text(
            default_value=default_graph, multiline=True, tag='semiring_graph_input', height=150, width=800
        )
        dpg.add_button(label='Compute Matrix Power', callback=run_semiring_power)
        dpg.add_text('', tag='semiring_status', color=(255, 200, 100))
        dpg.add_text('Result Matrix:')
        create_bordered_table(tag='table_semiring_res')


def build_view_curvature() -> None:
    with dpg.group(tag='view_forman_ricci_curvature_group', show=False):
        dpg.add_text('Compute discrete Forman-Ricci curvature on weighted/unweighted networks.', color=(180, 180, 180))
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label='Weighted Graph', default_value=False, tag='curvature_weighted')
            dpg.add_checkbox(label='Augmented Curvature (Triangles)', default_value=True, tag='curvature_augmented')

        dpg.add_text('Adjacency Graph (JSON format):')
        default_curv_graph = (
            '{\n  "0": {"1": 1, "2": 1},\n  "1": {"0": 1, "2": 1},\n  "2": {"0": 1, "1": 1, "3": 1},\n'
            '  "3": {"2": 1, "4": 1, "5": 1},\n  "4": {"3": 1},\n  "5": {"3": 1}\n}'
        )
        dpg.add_input_text(
            default_value=default_curv_graph, multiline=True, tag='curvature_graph_input', height=150, width=800
        )
        dpg.add_button(label='Analyze Graph Curvature', callback=run_curvature)
        dpg.add_text('', tag='curvature_status', color=(255, 200, 100))
        dpg.add_text('Calculated Edge Curvatures:')
        create_bordered_table(tag='table_curvature')


def build_view_crypto() -> None:
    with dpg.group(tag='view_pq_key_exchange_group', show=False):
        dpg.add_text('Simulation of Diffie-Hellman key exchange over the Digital Semiring.', color=(180, 180, 180))
        with dpg.group(horizontal=True):
            dpg.add_text('Alice Private Key (a1, a2):')
            dpg.add_input_int(default_value=12, tag='crypto_a1', width=100)
            dpg.add_input_int(default_value=34, tag='crypto_a2', width=100)
        with dpg.group(horizontal=True):
            dpg.add_text('Bob Private Key (b1, b2):')
            dpg.add_input_int(default_value=56, tag='crypto_b1', width=100)
            dpg.add_input_int(default_value=78, tag='crypto_b2', width=100)

        dpg.add_button(label='Execute Key Exchange', callback=run_crypto_exchange)
        dpg.add_text('', tag='crypto_status', color=(255, 200, 100))
        dpg.add_text('Keys Match: Not Run', tag='crypto_match_text', color=(100, 255, 100))

        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text('Alice Public U:')
                create_bordered_table(tag='table_crypto_u', width=180)
            with dpg.group():
                dpg.add_text('Bob Public V:')
                create_bordered_table(tag='table_crypto_v', width=180)
            with dpg.group():
                dpg.add_text('Alice Shared Key K_A:')
                create_bordered_table(tag='table_crypto_ka', width=180)
            with dpg.group():
                dpg.add_text('Bob Shared Key K_B:')
                create_bordered_table(tag='table_crypto_kb', width=180)


def build_view_trie() -> None:
    with dpg.group(tag='view_algebraic_trie_group', show=False):
        dpg.add_text(
            'Algebraic Tries represent nested sparse tensors capable of contracting/marginalizing dimensions.',
            color=(180, 180, 180),
        )
        dpg.add_text('Tensor Points [[coordinate_tuple, value], ...]:')
        default_points = '[\n  [[0, 0, 0], 1.0],\n  [[0, 0, 0], 2.0],\n  [[0, 1, 0], 5.0],\n  [[1, 0, 0], 10.0]\n]'
        dpg.add_input_text(default_value=default_points, multiline=True, tag='trie_points_input', height=120, width=800)
        dpg.add_text('Contract Dimensions (JSON list of indices, e.g. [0] or [0, 0]):')
        dpg.add_input_text(default_value='[0]', tag='trie_contract_dims', width=300)
        dpg.add_button(label='Contract Sparse Tensor', callback=run_trie_operations)
        dpg.add_text('', tag='trie_status', color=(255, 200, 100))
        dpg.add_text('Trie Contents:')
        dpg.add_text('  (No data populated yet)', tag='trie_contents_text', color=(160, 160, 160))
        dpg.add_text('Contracted Result: None', tag='trie_result_text', color=(100, 255, 100))


def build_view_pagerank() -> None:
    with dpg.group(tag='view_pagerank_group', show=False):
        dpg.add_text('Compute PageRank (algebraic stationary distribution of a random walk).', color=(180, 180, 180))
        with dpg.group(horizontal=True):
            dpg.add_text('Damping (alpha):')
            dpg.add_input_float(default_value=0.85, tag='pagerank_alpha', width=120)
            dpg.add_text('Iterations:')
            dpg.add_input_int(default_value=20, tag='pagerank_iterations', width=100)

        dpg.add_text('Web Graph Adjacency List (JSON format):')
        default_web = '{\n  "A": {"B": 1, "C": 1},\n  "B": {"C": 1},\n  "C": {"A": 1}\n}'
        dpg.add_input_text(default_value=default_web, multiline=True, tag='pagerank_graph', height=120, width=800)
        dpg.add_button(label='Compute PageRank', callback=run_pagerank)
        dpg.add_text('', tag='pagerank_status', color=(255, 200, 100))
        dpg.add_text('Resulting Ranks:')
        create_bordered_table(tag='table_pagerank', width=300)


def build_view_cyk() -> None:
    with dpg.group(tag='view_cyk_parser_group', show=False):
        dpg.add_text(
            'Grammar syntax parsing representing CYK chart combination as a matrix multiplication closure.',
            color=(180, 180, 180),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Sentence to Parse:')
            dpg.add_input_text(default_value='I love Python', tag='cyk_sentence', width=400)

        dpg.add_text('Lexicon Grammar Mapping (JSON format):')
        default_cyk_lexicon = '{\n  "I": ["NP"],\n  "love": ["V"],\n  "Python": ["NP"]\n}'
        dpg.add_input_text(default_value=default_cyk_lexicon, multiline=True, tag='cyk_lexicon', height=100, width=800)
        dpg.add_text('Chomsky Normal Form Grammar Rules (comma-separated inputs, JSON format):')
        default_cyk_rules = '{\n  "NP,VP": ["S"],\n  "V,NP": ["VP"]\n}'
        dpg.add_input_text(default_value=default_cyk_rules, multiline=True, tag='cyk_rules', height=100, width=800)
        dpg.add_button(label='Parse Sentence', callback=run_cyk_parsing)
        dpg.add_text('', tag='cyk_status', color=(255, 200, 100))
        dpg.add_text('Parses as: None', tag='cyk_result_text', color=(100, 255, 100))
        dpg.add_text('Parsing Chart Spans:')
        create_bordered_table(tag='table_cyk_chart')


def build_view_slope() -> None:
    with dpg.group(tag='view_slope_transform_group', show=False):
        dpg.add_text(
            'Evaluate the Fenchel-Legendre Transform (Tropical/Idempotent Fourier analog) of a signal.',
            color=(180, 180, 180),
        )
        dpg.add_text('Signal Vector f(x) (JSON format):')
        default_signal = '{\n  "0": 0.0,\n  "1": 1.0,\n  "2": 4.0,\n  "3": 9.0\n}'
        dpg.add_input_text(default_value=default_signal, multiline=True, tag='fenchel_signal', height=100, width=800)
        dpg.add_text('Slopes to Evaluate (s) (JSON list):')
        default_slopes = '[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]'
        dpg.add_input_text(default_value=default_slopes, tag='fenchel_slopes', width=400)
        dpg.add_button(label='Compute Convex Conjugates', callback=run_legendre_fenchel)
        dpg.add_text('', tag='fenchel_status', color=(255, 200, 100))
        dpg.add_text('Convex Conjugate Values f*(s) = sup_x (s*x - f(x)):')
        create_bordered_table(tag='table_fenchel', width=350)


def build_view_automata() -> None:
    with dpg.group(tag='view_automata_simulator_group', show=False):
        dpg.add_text(
            'Simulate Deterministic and Nondeterministic/Probabilistic Finite Automata.', color=(180, 180, 180)
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Automaton Type:')
            dpg.add_combo(
                ['DFA', 'NFA / Probabilistic'],
                default_value='DFA',
                callback=automata_type_callback,
                tag='automata_type',
                width=200,
            )
            dpg.add_text('Start State(s):')
            dpg.add_input_text(default_value='"q0"', tag='automata_start', width=150)
        with dpg.group(horizontal=True):
            dpg.add_text('Accept States (JSON list):')
            dpg.add_input_text(default_value='["q1"]', tag='automata_accept', width=250)
            dpg.add_text('Input Symbols (string or comma-separated):')
            dpg.add_input_text(default_value='1010', tag='automata_input', width=250)

        dpg.add_text('Transition Table (JSON format):')
        default_dfa_trans = (
            '{\n  "q0": {"0": "q0", "1": "q1"},\n  "q1": {"0": "q2", "1": "q0"},\n  "q2": {"0": "q1", "1": "q2"}\n}'
        )
        dpg.add_input_text(
            default_value=default_dfa_trans, multiline=True, tag='automata_transitions', height=150, width=800
        )
        dpg.add_button(label='Simulate Automaton', callback=run_automata_sim)
        dpg.add_text('', tag='automata_status', color=(255, 200, 100))
        dpg.add_text('Result: Not Run', tag='automata_result_text', color=(100, 255, 100))
        dpg.add_text('Simulation Trajectory Log:')
        dpg.add_input_text(multiline=True, tag='automata_log_text', readonly=True, height=150, width=800)


def build_view_markov_info() -> None:
    with dpg.group(tag='view_markov_info_theory_group', show=False):
        dpg.add_text(
            'Simulate Markov chain steps, find stationary states, and compute information theory metrics.',
            color=(180, 180, 180),
        )
        with dpg.group(horizontal=True):
            with dpg.group(width=390):
                dpg.add_text('MARKOV CHAIN SIMULATOR', color=(150, 180, 255))
                dpg.add_separator()
                dpg.add_text('Transition Matrix (Row Stochastic JSON):')
                default_markov_matrix = '{\n  "A": {"A": 0.1, "B": 0.9},\n  "B": {"A": 0.5, "B": 0.5}\n}'
                dpg.add_input_text(
                    default_value=default_markov_matrix, multiline=True, tag='markov_matrix', height=100, width=380
                )
                dpg.add_text('Initial Distribution State:')
                dpg.add_input_text(default_value='{"A": 1.0, "B": 0.0}', tag='markov_state', width=380)
                with dpg.group(horizontal=True):
                    dpg.add_text('Steps (N):')
                    dpg.add_input_int(default_value=5, min_value=1, tag='markov_steps', width=120)

                dpg.add_button(label='Compute Markov Simulation', callback=run_markov_simulation)
                dpg.add_text('', tag='markov_status', color=(255, 200, 100))
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text('Distribution after N steps:')
                        create_bordered_table(tag='table_markov_steps', width=180)
                    with dpg.group():
                        dpg.add_text('Analytical Steady State:')
                        create_bordered_table(tag='table_markov_steady', width=180)

            with dpg.group(width=390):
                dpg.add_text('INFORMATION THEORY LAB', color=(150, 180, 255))
                dpg.add_separator()
                dpg.add_text('Distribution P (True):')
                dpg.add_input_text(default_value='{"A": 0.5, "B": 0.25, "C": 0.25}', tag='info_p', width=380)
                dpg.add_text('Distribution Q (Reference/Model):')
                dpg.add_input_text(default_value='{"A": 0.4, "B": 0.3, "C": 0.3}', tag='info_q', width=380)
                dpg.add_text('Joint Distribution P(X, Y) (JSON matrix):')
                default_joint = '{\n  "X1": {"Y1": 0.25, "Y2": 0.25},\n  "X2": {"Y1": 0.25, "Y2": 0.25}\n}'
                dpg.add_input_text(default_value=default_joint, multiline=True, tag='info_joint', height=80, width=380)
                dpg.add_button(label='Compute Information Metrics', callback=run_info_theory)
                dpg.add_text('', tag='info_status', color=(255, 200, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Entropy H(P):')
                    dpg.add_text('0.0', tag='info_hp_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Entropy H(Q):')
                    dpg.add_text('0.0', tag='info_hq_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Cross Entropy H(P, Q):')
                    dpg.add_text('0.0', tag='info_hcross_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('KL Divergence D_KL(P||Q):')
                    dpg.add_text('0.0', tag='info_kl_val', color=(100, 255, 100))
                with dpg.group(horizontal=True):
                    dpg.add_text('Mutual Info I(X; Y):')
                    dpg.add_text('0.0', tag='info_mi_val', color=(100, 255, 100))


def build_view_signal_transforms() -> None:
    with dpg.group(tag='view_signal_transforms_group', show=False):
        dpg.add_text(
            'Apply Discrete Fourier, Hilbert, Convolution, or Z-Transforms to sparse signal vectors.',
            color=(180, 180, 180),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Select Operation:')
            dpg.add_combo(
                ['DFT', 'IDFT', 'Hilbert Transform', 'Convolution', 'Z-Transform'],
                default_value='DFT',
                callback=signal_op_change_callback,
                tag='signal_op_select',
                width=200,
            )

        dpg.add_text('Signal Vector f(t) (JSON format with integer keys):')
        default_f = '{\n  "0": 1.0,\n  "1": 0.0,\n  "2": -1.0,\n  "3": 0.0\n}'
        dpg.add_input_text(default_value=default_f, multiline=True, tag='signal_f', height=100, width=800)

        with dpg.group(tag='signal_g_group', show=False):
            dpg.add_text('Kernel Vector g(t) (JSON format with integer keys, for Convolution):')
            default_g = '{\n  "0": 0.5,\n  "1": 0.5\n}'
            dpg.add_input_text(default_value=default_g, multiline=True, tag='signal_g', height=80, width=800)

        with dpg.group(tag='signal_z_group', show=False):
            dpg.add_text('Complex z coordinate (for Z-Transform):')
            dpg.add_input_text(default_value='0.5+0.5j', tag='signal_z_input', width=200)

        dpg.add_button(label='Process Signal Transform', callback=run_signal_transforms)
        dpg.add_text('', tag='signal_status', color=(255, 200, 100))
        dpg.add_text('Resulting Signal Coefficients:')
        create_bordered_table(tag='table_signal_res')


def build_view_image_conv() -> None:
    with dpg.group(tag='view_image_convolution_2d_group', show=False):
        dpg.add_text(
            'Perform 2D Image & Grid Convolution via algebrax.transforms.convolve using 2D vector key addition.',
            color=(180, 180, 180),
        )
        with dpg.group(horizontal=True):
            dpg.add_text('Load Real Image File:')
            dpg.add_input_text(tag='img_conv_filepath_input', hint='Path to PNG, JPG, BMP image file...', width=380)
            dpg.add_button(label='Browse...', callback=open_file_dialog_callback)
            dpg.add_button(
                label='Load Image', callback=lambda: load_image_file_into_lab(dpg.get_value('img_conv_filepath_input'))
            )

        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_text('Image Preset:')
            dpg.add_combo(
                list(IMAGE_PRESETS.keys()),
                default_value='Cross Pattern (8x8)',
                callback=image_preset_change_callback,
                tag='img_conv_image_preset',
                width=180,
            )
            dpg.add_spacer(width=10)
            dpg.add_text('Kernel Preset:')
            dpg.add_combo(
                list(KERNEL_PRESETS.keys()),
                default_value='Sobel Horizontal (Edge)',
                callback=kernel_preset_change_callback,
                tag='img_conv_kernel_preset',
                width=180,
            )
            dpg.add_spacer(width=10)
            dpg.add_text('Semiring:')
            dpg.add_combo(
                [
                    'Standard (+, *)',
                    'Arctic / Max-Plus (Dilation)',
                    'Tropical / Min-Plus (Erosion)',
                ],
                default_value='Standard (+, *)',
                tag='img_conv_semiring_select',
                width=200,
            )

        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text('Image Mapping JSON {"r,c": intensity}:')
                dpg.add_input_text(
                    default_value=IMAGE_PRESETS['Cross Pattern (8x8)'],
                    multiline=True,
                    tag='img_conv_image_input',
                    height=120,
                    width=380,
                )
            with dpg.group():
                dpg.add_text('Kernel Mapping JSON {"dr,dc": weight}:')
                dpg.add_input_text(
                    default_value=KERNEL_PRESETS['Sobel Horizontal (Edge)'],
                    multiline=True,
                    tag='img_conv_kernel_input',
                    height=120,
                    width=380,
                )

        dpg.add_button(label='Compute 2D Image Convolution', callback=run_image_convolution_2d)
        dpg.add_text('', tag='img_conv_status', color=(255, 200, 100))

        with dpg.group(horizontal=True):
            with dpg.group():
                dpg.add_text('Input Image Texture (64x64):')
                dpg.add_image('texture_img_input', width=160, height=160)
            with dpg.group():
                dpg.add_text('Output Convolved Texture (64x64):')
                dpg.add_image('texture_img_output', width=160, height=160)
            with dpg.group():
                dpg.add_text('ASCII Grid Preview:')
                dpg.add_input_text(
                    default_value='',
                    multiline=True,
                    tag='img_conv_ascii_preview',
                    height=160,
                    width=220,
                    readonly=True,
                )
            with dpg.group():
                dpg.add_text('Result Table:')
                create_bordered_table(tag='table_img_conv_res', width=220, height=160)


def build_view_network_vis() -> None:
    with dpg.group(tag='view_network_curvature_vis_group', show=False):
        dpg.add_text('Interactive Force-Directed Layout & Forman-Ricci Curvature Visualization', color=(150, 180, 255))
        with dpg.group(horizontal=True):
            with dpg.group(width=280):
                dpg.add_text('GRAPH SETTINGS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_text('Graph Preset:')
                dpg.add_combo(
                    ['Barbell Graph', 'Star Graph', 'Cycle Graph', 'Tree Graph', 'Grid Graph'],
                    default_value='Barbell Graph',
                    tag='vis_preset',
                    callback=recalculate_and_reset_layout,
                )
                dpg.add_checkbox(
                    label='Weighted Graph',
                    default_value=False,
                    tag='vis_weighted',
                    callback=recalculate_and_reset_layout,
                )
                dpg.add_checkbox(
                    label='Augmented Curvature (Triangles)',
                    default_value=True,
                    tag='vis_augmented',
                    callback=recalculate_and_reset_layout,
                )

                dpg.add_spacer(height=10)
                dpg.add_text('PHYSICS SIMULATION', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_checkbox(label='Run Physics Layout', default_value=True, tag='vis_run_physics')
                with dpg.group(horizontal=True):
                    dpg.add_button(label='Jostle Graph', callback=jostle_graph_callback)
                    dpg.add_button(label='Reset Positions', callback=recalculate_and_reset_layout)

                dpg.add_spacer(height=10)
                dpg.add_text('STATUS', color=(100, 255, 100))
                dpg.add_separator()
                dpg.add_text('Initializing...', tag='vis_status', color=(255, 200, 100))

                dpg.add_spacer(height=10)
                dpg.add_text('CURVATURE CHART', color=(100, 255, 100))
                dpg.add_separator()
                with dpg.plot(label='Curvature Profile', height=180, width=270):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label='Edge Index', tag='curvature_x_axis')
                    dpg.add_plot_axis(dpg.mvYAxis, label='Curvature', tag='curvature_y_axis')

            with dpg.group():
                dpg.add_text('Force-Directed Canvas (Drag nodes to interact!):', color=(180, 180, 180))
                with dpg.drawlist(width=700, height=450, tag='vis_canvas'):
                    pass
                with dpg.group(horizontal=True):
                    dpg.add_text('Legend: ')
                    dpg.add_text('Red (Hyperbolic / K < 0)', color=(255, 80, 80))
                    dpg.add_text(' | ')
                    dpg.add_text('Gray (Flat / K = 0)', color=(200, 200, 200))
                    dpg.add_text(' | ')
                    dpg.add_text('Blue (Spherical / K > 0)', color=(80, 180, 255))


# --- Navigation Sidebar Builder ---
VIEWS: list[str] = [
    'semiring_matrix_power',
    'forman_ricci_curvature',
    'pq_key_exchange',
    'algebraic_trie',
    'pagerank',
    'cyk_parser',
    'slope_transform',
    'automata_simulator',
    'markov_info_theory',
    'signal_transforms',
    'image_convolution_2d',
    'network_curvature_vis',
]


def change_view(sender: int | str, app_data: Any, user_data: str) -> None:
    selected_view: str = user_data
    for v in VIEWS:
        dpg.set_value(f'sel_{v}', (v == selected_view))
        if v == selected_view:
            dpg.show_item(f'view_{v}_group')
        else:
            dpg.hide_item(f'view_{v}_group')


def build_navigation_sidebar() -> None:
    with dpg.child_window(width=280, height=-1, border=True):
        dpg.add_text('ALGEBRAIC EXPLORER', color=(100, 255, 100))
        dpg.add_separator()
        dpg.add_spacer(height=5)

        with dpg.tree_node(label='Matrix & Graph Algorithms', default_open=True):
            dpg.add_selectable(
                label='Semiring Matrix Power',
                tag='sel_semiring_matrix_power',
                callback=change_view,
                user_data='semiring_matrix_power',
                default_value=True,
            )
            dpg.add_selectable(
                label='Forman-Ricci Curvature',
                tag='sel_forman_ricci_curvature',
                callback=change_view,
                user_data='forman_ricci_curvature',
            )
            dpg.add_selectable(
                label='PageRank Algorithm',
                tag='sel_pagerank',
                callback=change_view,
                user_data='pagerank',
            )
            dpg.add_selectable(
                label='Network Curvature Vis',
                tag='sel_network_curvature_vis',
                callback=change_view,
                user_data='network_curvature_vis',
            )

        with dpg.tree_node(label='Automata & Parsing', default_open=True):
            dpg.add_selectable(
                label='Automata Simulator',
                tag='sel_automata_simulator',
                callback=change_view,
                user_data='automata_simulator',
            )
            dpg.add_selectable(
                label='CYK Grammar Parser',
                tag='sel_cyk_parser',
                callback=change_view,
                user_data='cyk_parser',
            )

        with dpg.tree_node(label='Transforms & Signals', default_open=True):
            dpg.add_selectable(
                label='Slope Transform',
                tag='sel_slope_transform',
                callback=change_view,
                user_data='slope_transform',
            )
            dpg.add_selectable(
                label='Signal Transforms',
                tag='sel_signal_transforms',
                callback=change_view,
                user_data='signal_transforms',
            )
            dpg.add_selectable(
                label='2D Image Convolution',
                tag='sel_image_convolution_2d',
                callback=change_view,
                user_data='image_convolution_2d',
            )

        with dpg.tree_node(label='Algebra & Information', default_open=True):
            dpg.add_selectable(
                label='Algebraic Trie / Tensor',
                tag='sel_algebraic_trie',
                callback=change_view,
                user_data='algebraic_trie',
            )
            dpg.add_selectable(
                label='Markov & Info Theory',
                tag='sel_markov_info_theory',
                callback=change_view,
                user_data='markov_info_theory',
            )
            dpg.add_selectable(
                label='Post-Quantum Key Exchange',
                tag='sel_pq_key_exchange',
                callback=change_view,
                user_data='pq_key_exchange',
            )


# --- Dear PyGui Context & Theme Initialization ---

dpg.create_context()

init_texture_data: list[float] = [0.1, 0.1, 0.1, 1.0] * (TEXTURE_WIDTH * TEXTURE_HEIGHT)
with dpg.texture_registry(show=False):
    dpg.add_dynamic_texture(
        width=TEXTURE_WIDTH, height=TEXTURE_HEIGHT, default_value=init_texture_data, tag='texture_img_input'
    )
    dpg.add_dynamic_texture(
        width=TEXTURE_WIDTH, height=TEXTURE_HEIGHT, default_value=init_texture_data, tag='texture_img_output'
    )

dpg.create_viewport(title='AlgebraX Graphical Laboratory', width=1200, height=900)


def setup_window_icon() -> None:
    png_path = 'site/assets/images/favicon.png'
    ico_path = 'reciepes/logo.ico'

    if not os.path.exists(ico_path) and os.path.exists(png_path):
        try:
            img = Image.open(png_path)
            img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        except Exception:
            pass

    if os.path.exists(ico_path):
        try:
            dpg.set_viewport_small_icon(ico_path)
            dpg.set_viewport_large_icon(ico_path)
        except Exception:
            pass


setup_window_icon()

with dpg.theme() as global_theme, dpg.theme_component(dpg.mvAll):
    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (23, 23, 27))
    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (45, 45, 55))
    dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 80))
    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 110))
    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 140))
    dpg.add_theme_color(dpg.mvThemeCol_Header, (40, 40, 50))
    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (32, 32, 40))
    dpg.add_theme_color(dpg.mvThemeCol_Tab, (40, 40, 50))
    dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (60, 60, 80))
    dpg.add_theme_color(dpg.mvThemeCol_TabActive, (80, 80, 100))

dpg.bind_theme(global_theme)


# --- Main Window Builder ---
def main() -> None:
    with dpg.window(
            label='AlgebraX Graphical Lab',
            width=1180,
            height=860,
            no_title_bar=True,
            no_move=True,
            no_resize=True,
    ) as main_window:
        dpg.add_text('ALGEBRAX GRAPHICAL LABORATORY', color=(150, 180, 255))
        dpg.add_separator()

        with dpg.group(horizontal=True):
            build_navigation_sidebar()
            with dpg.child_window(width=-1, height=-1, border=False):
                build_view_semiring()
                build_view_curvature()
                build_view_crypto()
                build_view_trie()
                build_view_pagerank()
                build_view_cyk()
                build_view_slope()
                build_view_automata()
                build_view_markov_info()
                build_view_signal_transforms()
                build_view_image_conv()
                build_view_network_vis()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window(main_window, True)

    recalculate_and_reset_layout()

    while dpg.is_dearpygui_running():
        update_graph_simulation()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == '__main__':
    main()
