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

import cmath
import json
import math
import random

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

TEXTURE_WIDTH = 64
TEXTURE_HEIGHT = 64

# --- Global State for Curvature Visualization Presets ---
current_nodes = []
current_edges = []
current_curvatures = {}
pos = {}
vel = {}
dragged_node = None


# Global helper to display matrix in a DearPyGui table
def display_matrix_in_table(matrix, table_tag):
    if dpg.does_item_exist(table_tag):
        dpg.delete_item(table_tag, children_only=True)

    if not matrix:
        return

    rows = list(matrix.keys())
    cols = set()
    for r in rows:
        cols.update(matrix[r].keys())
    sorted_cols = sorted(cols)

    dpg.add_table_column(parent=table_tag, label='Row/Col')
    for col in sorted_cols:
        dpg.add_table_column(parent=table_tag, label=str(col))

    for r in sorted(rows):
        with dpg.table_row(parent=table_tag):
            dpg.add_text(str(r))
            for c in sorted_cols:
                val = matrix[r].get(c, '.')
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
class GrammarSemiring(Semiring):
    def __init__(self, rules):
        self._rules = rules

    @property
    def zero(self):
        return set()

    @property
    def one(self):
        return set()

    def add(self, a, b):
        return a | b

    def mul(self, a, b):
        res = set()
        for lhs in a:
            for rhs in b:
                if (lhs, rhs) in self._rules:
                    res.update(self._rules[(lhs, rhs)])
        return res


# --- Custom Semiring for Convex Hull (Intervals) ---
class IntervalSemiring(Semiring):
    @property
    def zero(self):
        return (float('inf'), float('-inf'))

    @property
    def one(self):
        return (0.0, 0.0)

    def add(self, a, b):
        return (min(a[0], b[0]), max(a[1], b[1]))

    def mul(self, a, b):
        return (a[0] + b[0], a[1] + b[1])


# --- Callbacks ---


def semiring_change_callback(sender, app_data):
    semiring_name = app_data
    if semiring_name == 'Tropical' or semiring_name == 'Arctic':
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


def run_semiring_power():
    semiring_name = dpg.get_value('semiring_select')
    power_val = dpg.get_value('semiring_power')
    graph_str = dpg.get_value('semiring_graph_input')

    try:
        custom_g = json.loads(graph_str)
        parsed_g = {}

        if semiring_name == 'Tropical':
            from algebrax.semiring import TropicalSemiring

            semiring = TropicalSemiring()
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

            def parse_expectation(x):
                return (float(x[0]), float(x[1]))

            parser = parse_expectation
        elif semiring_name == 'Provenance':
            from algebrax.semiring import ProvenanceSemiring

            semiring = ProvenanceSemiring()

            def parse_provenance(d):
                return {tuple(k.split(',')) if isinstance(k, str) else tuple(k): int(v) for k, v in d.items()}

            parser = parse_provenance
        elif semiring_name == 'Variance':
            from algebrax.semiring import VarianceSemiring

            semiring = VarianceSemiring()

            def parse_variance(x):
                return (float(x[0]), float(x[1]), float(x[2]), float(x[3]))

            parser = parse_variance
        elif semiring_name == 'Digital':
            from algebrax.semiring import DigitalSemiring

            semiring = DigitalSemiring()
            parser = int
        elif semiring_name == 'Interval (Convex Hull)':
            semiring = IntervalSemiring()

            def parse_interval(x):
                return (float(x[0]), float(x[1]))

            parser = parse_interval
        else:
            from algebrax.semiring import StandardSemiring

            semiring = StandardSemiring()
            parser = float

        for u, neighbors in custom_g.items():
            u_key = int(u) if u.isdigit() else u
            row = {}
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


def run_curvature():
    graph_str = dpg.get_value('curvature_graph_input')
    weighted = dpg.get_value('curvature_weighted')
    augmented = dpg.get_value('curvature_augmented')

    try:
        custom_g = json.loads(graph_str)
        g_parsed = {}
        for u, neighbors in custom_g.items():
            u_key = int(u) if u.isdigit() else u
            neighbors_parsed = {}
            for v, w in neighbors.items():
                v_key = int(v) if v.isdigit() else v
                neighbors_parsed[v_key] = float(w)
            g_parsed[u_key] = neighbors_parsed

        curv = forman_ricci_curvature(g_parsed, weighted=weighted, augmented=augmented)

        if dpg.does_item_exist('table_curvature'):
            dpg.delete_item('table_curvature', children_only=True)

        dpg.add_table_column(parent='table_curvature', label='Edge (u, v)')
        dpg.add_table_column(parent='table_curvature', label='Curvature')
        dpg.add_table_column(parent='table_curvature', label='Type')

        for (u, v), k in sorted(curv.items()):
            k_type = 'Euclidean'
            if k > 0:
                k_type = 'Spherical'
            elif k < 0:
                k_type = 'Hyperbolic'

            with dpg.table_row(parent='table_curvature'):
                dpg.add_text(f'({u}, {v})')
                dpg.add_text(f'{k:.4f}'.rstrip('0').rstrip('.'))
                dpg.add_text(k_type)

        dpg.set_value('curvature_status', 'Computed curvatures successfully.')
    except Exception as e:
        dpg.set_value('curvature_status', f'Error: {e}')


def run_crypto_exchange():
    from algebrax.matrix.core import dot
    from algebrax.semiring import DigitalSemiring

    s_semiring = DigitalSemiring()

    try:
        a1 = int(dpg.get_value('crypto_a1'))
        a2 = int(dpg.get_value('crypto_a2'))
        b1 = int(dpg.get_value('crypto_b1'))
        b2 = int(dpg.get_value('crypto_b2'))

        m_mat = {0: {0: 123, 1: 456}, 1: {0: 789, 1: 12}}
        a_mat = {0: {0: a1, 1: a2}, 1: {0: a2, 1: a1}}
        b_mat = {0: {0: b1, 1: b2}, 1: {0: b2, 1: b1}}

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

        match = ka_mat == kb_mat
        dpg.set_value('crypto_match_text', f'Keys Match: {match}')
        dpg.set_value('crypto_status', 'Successfully performed key exchange simulation.')
    except Exception as e:
        dpg.set_value('crypto_status', f'Error: {e}')


def run_trie_operations():
    from algebrax.semiring import StandardSemiring
    from algebrax.trie import AlgebraicTrie

    try:
        trie = AlgebraicTrie(StandardSemiring)
        points_str = dpg.get_value('trie_points_input')
        points = json.loads(points_str)

        for coord, val in points:
            trie.add(tuple(coord), float(val))

        contract_dim_str = dpg.get_value('trie_contract_dims')
        contract_dims = tuple(json.loads(contract_dim_str))

        res = trie.contract(contract_dims)

        trie_lines = []
        for path in sorted(trie):
            trie_lines.append(f'  Path {path}: {trie[path]}')

        dpg.set_value('trie_contents_text', '\n'.join(trie_lines))
        dpg.set_value('trie_result_text', f'Contracted Result at {contract_dims}: {res}')
        dpg.set_value('trie_status', 'Successfully performed trie operations.')
    except Exception as e:
        dpg.set_value('trie_status', f'Error: {e}')


def run_pagerank():
    graph_str = dpg.get_value('pagerank_graph')
    alpha = dpg.get_value('pagerank_alpha')
    iterations = dpg.get_value('pagerank_iterations')

    try:
        graph = json.loads(graph_str)

        m_matrix = {}
        nodes = set(graph.keys())
        for u, neighbors in graph.items():
            nodes.update(neighbors.keys())
            degree = len(neighbors)
            if degree > 0:
                m_matrix[u] = dict.fromkeys(neighbors, 1.0 / degree)
            else:
                m_matrix[u] = {u: 1.0}

        all_nodes = sorted(nodes)
        n_nodes = len(all_nodes)

        v_vec = dict.fromkeys(all_nodes, 1.0 / n_nodes)

        from algebrax.matrix.core import dot
        from algebrax.semiring import StandardSemiring

        semiring = StandardSemiring()

        for _ in range(iterations):
            v_matrix = {0: v_vec}
            res_matrix = dot(v_matrix, m_matrix, semiring=semiring)
            v_next_raw = res_matrix.get(0, {})

            v_next = {}
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


def run_cyk_parsing():
    sentence_str = dpg.get_value('cyk_sentence')
    lexicon_str = dpg.get_value('cyk_lexicon')
    rules_str = dpg.get_value('cyk_rules')

    try:
        sentence = sentence_str.strip().split()
        parsed_lexicon = json.loads(lexicon_str)
        parsed_rules = json.loads(rules_str)

        lexicon = {k: set(v) for k, v in parsed_lexicon.items()}
        rules = {tuple(k.split(',')): set(v) for k, v in parsed_rules.items()}

        n_len = len(sentence)
        chart = {}
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


def run_legendre_fenchel():
    signal_str = dpg.get_value('fenchel_signal')
    slopes_str = dpg.get_value('fenchel_slopes')

    try:
        signal = json.loads(signal_str)
        parsed_signal = {float(k) if '.' in k else int(k): float(v) for k, v in signal.items()}
        slopes = json.loads(slopes_str)

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


def automata_type_callback(sender, app_data):
    m_type = app_data
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


def _simulate_dfa_step_by_step(seq, start_str, accept_states, transitions):
    start_state = start_str.strip().strip('"').strip("'")
    if start_state.isdigit():
        start_state = int(start_state)

    # Normalize transitions
    normalized_transitions = {}
    for s, trans in transitions.items():
        s_key = int(s) if s.isdigit() else s
        normalized_transitions[s_key] = {}
        for sym, ns in trans.items():
            sym_key = int(sym) if sym.isdigit() else sym
            ns_val = int(ns) if isinstance(ns, str) and ns.isdigit() else ns
            normalized_transitions[s_key][sym_key] = ns_val

    # Also normalize accept states
    normalized_accept = {int(ac) if isinstance(ac, str) and ac.isdigit() else ac for ac in accept_states}

    current = start_state
    steps_log = [f'Start state: {current}']

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


def _simulate_nfa_step_by_step(seq, start_str, accept_states, transitions):
    start_states = json.loads(start_str)
    if isinstance(start_states, str):
        s_val = int(start_states) if start_states.isdigit() else start_states
        start_dist = {s_val: 1.0}
    elif isinstance(start_states, list):
        start_dist = {int(s) if str(s).isdigit() else s: 1.0 for s in start_states}
    elif isinstance(start_states, dict):
        start_dist = {int(k) if k.isdigit() else k: float(v) for k, v in start_states.items()}
    else:
        start_dist = {}

    if not start_dist:
        return (
            ['Error: Invalid format for start states.'],
            'REJECTED (Error)',
            (255, 100, 100),
        )

    # Normalize NFA transitions
    normalized_transitions = {}
    for s, trans in transitions.items():
        s_key = int(s) if s.isdigit() else s
        normalized_transitions[s_key] = {}
        for sym, nexts in trans.items():
            sym_key = int(sym) if sym.isdigit() else sym
            normalized_transitions[s_key][sym_key] = {}
            if isinstance(nexts, list):
                for ns in nexts:
                    ns_key = int(ns) if str(ns).isdigit() else ns
                    normalized_transitions[s_key][sym_key][ns_key] = 1.0
            elif isinstance(nexts, dict):
                for ns, w in nexts.items():
                    ns_key = int(ns) if ns.isdigit() else ns
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
    if accept_weight > 0:
        status = f'ACCEPTED (Total Accept Weight: {accept_weight:.4f})'
        status_color = (100, 255, 100)
    else:
        status = 'REJECTED (No active state is an accept state)'
        status_color = (255, 100, 100)
    return steps_log, status, status_color


def run_automata_sim():
    machine_type = dpg.get_value('automata_type')
    transitions_str = dpg.get_value('automata_transitions')
    start_str = dpg.get_value('automata_start')
    accept_str = dpg.get_value('automata_accept')
    input_str = dpg.get_value('automata_input')

    try:
        transitions = json.loads(transitions_str)
        accept_states = set(json.loads(accept_str))

        seq = [s.strip() for s in input_str.split(',') if s.strip()] if ',' in input_str else list(input_str)

        if machine_type == 'DFA':
            steps_log, status, status_color = _simulate_dfa_step_by_step(seq, start_str, accept_states, transitions)
        else:  # NFA
            steps_log, status, status_color = _simulate_nfa_step_by_step(seq, start_str, accept_states, transitions)

        dpg.set_value('automata_log_text', '\n'.join(steps_log))
        dpg.set_value('automata_result_text', status)
        dpg.configure_item('automata_result_text', color=status_color)
        dpg.set_value('automata_status', 'Simulation completed successfully.')
    except Exception as e:
        dpg.set_value('automata_status', f'Error: {e}')


def run_markov_simulation():
    matrix_str = dpg.get_value('markov_matrix')
    state_str = dpg.get_value('markov_state')
    steps = dpg.get_value('markov_steps')

    try:
        matrix = json.loads(matrix_str)
        parsed_matrix = {}
        for u, neighbors in matrix.items():
            u_key = int(u) if u.isdigit() else u
            parsed_matrix[u_key] = {}
            for v, w in neighbors.items():
                v_key = int(v) if v.isdigit() else v
                parsed_matrix[u_key][v_key] = float(w)

        state = json.loads(state_str)
        parsed_state = {int(k) if k.isdigit() else k: float(v) for k, v in state.items()}

        # 1. Compute state after N steps
        after_n = markov_step(parsed_state, parsed_matrix, steps)

        # 2. Compute steady state
        steady = markov_steady_state(parsed_matrix)

        # Display in tables
        if dpg.does_item_exist('table_markov_steps'):
            dpg.delete_item('table_markov_steps', children_only=True)
        dpg.add_table_column(parent='table_markov_steps', label='State')
        dpg.add_table_column(parent='table_markov_steps', label='Probability')
        for k, v in sorted(after_n.items()):
            with dpg.table_row(parent='table_markov_steps'):
                dpg.add_text(str(k))
                dpg.add_text(f'{v:.6f}')

        if dpg.does_item_exist('table_markov_steady'):
            dpg.delete_item('table_markov_steady', children_only=True)
        dpg.add_table_column(parent='table_markov_steady', label='State')
        dpg.add_table_column(parent='table_markov_steady', label='Steady Prob')
        for k, v in sorted(steady.items()):
            with dpg.table_row(parent='table_markov_steady'):
                dpg.add_text(str(k))
                dpg.add_text(f'{v:.6f}')

        dpg.set_value('markov_status', 'Successfully computed Markov steps and steady state.')
    except Exception as e:
        dpg.set_value('markov_status', f'Error: {e}')


def run_info_theory():
    dist_p_str = dpg.get_value('info_p')
    dist_q_str = dpg.get_value('info_q')
    joint_str = dpg.get_value('info_joint')

    try:
        p = json.loads(dist_p_str)
        parsed_p = {int(k) if k.isdigit() else k: float(v) for k, v in p.items()}

        q = json.loads(dist_q_str)
        parsed_q = {int(k) if k.isdigit() else k: float(v) for k, v in q.items()}

        joint = json.loads(joint_str)
        parsed_joint = {}
        for x, row in joint.items():
            x_key = int(x) if x.isdigit() else x
            parsed_joint[x_key] = {}
            for y, val in row.items():
                y_key = int(y) if y.isdigit() else y
                parsed_joint[x_key][y_key] = float(val)

        hp = entropy(parsed_p)
        hq = entropy(parsed_q)
        h_cross = cross_entropy(parsed_p, parsed_q)
        kl = kl_divergence(parsed_p, parsed_q)
        mi = mutual_information(parsed_joint)

        dpg.set_value('info_hp_val', f'{hp:.6f} bits')
        dpg.set_value('info_hq_val', f'{hq:.6f} bits')
        dpg.set_value('info_hcross_val', f'{h_cross:.6f} bits')
        if kl == float('inf'):
            dpg.set_value('info_kl_val', 'Infinity')
        else:
            dpg.set_value('info_kl_val', f'{kl:.6f} bits')
        dpg.set_value('info_mi_val', f'{mi:.6f} bits')

        dpg.set_value('info_status', 'Successfully computed Information Theory metrics.')
    except Exception as e:
        dpg.set_value('info_status', f'Error: {e}')


def signal_op_change_callback(sender, app_data):
    op = app_data
    if op == 'Convolution':
        dpg.show_item('signal_g_group')
        dpg.hide_item('signal_z_group')
    elif op == 'Z-Transform':
        dpg.hide_item('signal_g_group')
        dpg.show_item('signal_z_group')
    else:
        dpg.hide_item('signal_g_group')
        dpg.hide_item('signal_z_group')


def run_signal_transforms():
    op = dpg.get_value('signal_op_select')
    f_str = dpg.get_value('signal_f')
    g_str = dpg.get_value('signal_g')
    z_val_str = dpg.get_value('signal_z_input')

    try:
        f = json.loads(f_str)

        def parse_complex(val):
            if isinstance(val, list) and len(val) == 2:
                return complex(val[0], val[1])
            if isinstance(val, str):
                return complex(val.replace(' ', ''))
            return complex(val)

        parsed_f = {int(k): parse_complex(v) for k, v in f.items()}

        if dpg.does_item_exist('table_signal_res'):
            dpg.delete_item('table_signal_res', children_only=True)

        dpg.add_table_column(parent='table_signal_res', label='Index')
        dpg.add_table_column(parent='table_signal_res', label='Value (Complex / Real)')
        dpg.add_table_column(parent='table_signal_res', label='Magnitude')
        dpg.add_table_column(parent='table_signal_res', label='Phase (Rad)')

        if op == 'DFT':
            res = dft(parsed_f)
            for k, val in sorted(res.items()):
                mag, phase = cmath.polar(val)
                val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                with dpg.table_row(parent='table_signal_res'):
                    dpg.add_text(str(k))
                    dpg.add_text(val_str)
                    dpg.add_text(f'{mag:.4f}')
                    dpg.add_text(f'{phase:.4f}')
            dpg.set_value('signal_status', 'Computed DFT successfully.')

        elif op == 'IDFT':
            res = idft(parsed_f)
            for k, val in sorted(res.items()):
                mag, phase = cmath.polar(val)
                val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                with dpg.table_row(parent='table_signal_res'):
                    dpg.add_text(str(k))
                    dpg.add_text(val_str)
                    dpg.add_text(f'{mag:.4f}')
                    dpg.add_text(f'{phase:.4f}')
            dpg.set_value('signal_status', 'Computed IDFT successfully.')

        elif op == 'Hilbert Transform':
            real_f = {k: v.real for k, v in parsed_f.items()}
            res = hilbert(real_f)
            for k, val in sorted(res.items()):
                mag, phase = cmath.polar(val)
                val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                with dpg.table_row(parent='table_signal_res'):
                    dpg.add_text(str(k))
                    dpg.add_text(val_str)
                    dpg.add_text(f'{mag:.4f}')
                    dpg.add_text(f'{phase:.4f}')
            dpg.set_value('signal_status', 'Computed Hilbert Transform successfully.')

        elif op == 'Convolution':
            g = json.loads(g_str)
            parsed_g = {int(k): parse_complex(v) for k, v in g.items()}
            res = convolve(parsed_f, parsed_g)
            for k, val in sorted(res.items()):
                mag, phase = cmath.polar(val)
                val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
                with dpg.table_row(parent='table_signal_res'):
                    dpg.add_text(str(k))
                    dpg.add_text(val_str)
                    dpg.add_text(f'{mag:.4f}')
                    dpg.add_text(f'{phase:.4f}')
            dpg.set_value('signal_status', 'Computed Convolution successfully.')

        elif op == 'Z-Transform':
            z_complex = complex(z_val_str.replace(' ', ''))
            val = z_transform(parsed_f, z_complex)
            mag, phase = cmath.polar(val)
            val_str = f'{val.real:.4f} + {val.imag:.4f}j' if abs(val.imag) > 1e-9 else f'{val.real:.4f}'
            with dpg.table_row(parent='table_signal_res'):
                dpg.add_text(f'Z = {z_complex}')
                dpg.add_text(val_str)
                dpg.add_text(f'{mag:.4f}')
                dpg.add_text(f'{phase:.4f}')
            dpg.set_value('signal_status', f'Computed Z-Transform at {z_complex} successfully.')

    except Exception as e:
        dpg.set_value('signal_status', f'Error: {e}')


# --- 2D Image Convolution Helpers & Callbacks ---
def parse_2d_sparse_vector(json_str: str) -> dict[tuple[int, int], float]:
    raw = json.loads(json_str)
    result = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            r = int(k)
            for c_str, val in v.items():
                result[(r, int(c_str))] = float(val)
        else:
            clean_k = str(k).strip('()[] ')
            parts = [int(x.strip()) for x in clean_k.split(',')]
            if len(parts) == 2:
                result[(parts[0], parts[1])] = float(v)
    return result


IMAGE_PRESETS = {
    'Cross Pattern (8x8)': json.dumps(
        {
            '3,3': 1.0,
            '3,4': 1.0,
            '4,3': 1.0,
            '4,4': 1.0,
            '0,3': 0.8,
            '1,3': 0.8,
            '2,3': 0.8,
            '5,3': 0.8,
            '6,3': 0.8,
            '7,3': 0.8,
            '3,0': 0.8,
            '3,1': 0.8,
            '3,2': 0.8,
            '3,5': 0.8,
            '3,6': 0.8,
            '3,7': 0.8,
        },
        indent=2,
    ),
    'Square Box (8x8)': json.dumps({f'{r},{c}': 1.0 for r in range(2, 6) for c in range(2, 6)}, indent=2),
    'Single Impulse (Center)': json.dumps({'4,4': 1.0}, indent=2),
}

KERNEL_PRESETS = {
    'Sobel Horizontal (Edge)': json.dumps(
        {
            '-1,-1': -1.0,
            '-1,0': 0.0,
            '-1,1': 1.0,
            '0,-1': -2.0,
            '0,0': 0.0,
            '0,1': 2.0,
            '1,-1': -1.0,
            '1,0': 0.0,
            '1,1': 1.0,
        },
        indent=2,
    ),
    'Sobel Vertical (Edge)': json.dumps(
        {
            '-1,-1': -1.0,
            '-1,0': -2.0,
            '-1,1': -1.0,
            '0,-1': 0.0,
            '0,0': 0.0,
            '0,1': 0.0,
            '1,-1': 1.0,
            '1,0': 2.0,
            '1,1': 1.0,
        },
        indent=2,
    ),
    'Sharpen Filter': json.dumps(
        {
            '-1,0': -1.0,
            '0,-1': -1.0,
            '0,0': 5.0,
            '0,1': -1.0,
            '1,0': -1.0,
        },
        indent=2,
    ),
    'Box Blur (3x3)': json.dumps(
        {f'{dr},{dc}': 0.1111 for dr in range(-1, 2) for dc in range(-1, 2)},
        indent=2,
    ),
    'Dilation Cross (3x3)': json.dumps(
        {
            '-1,0': 0.0,
            '0,-1': 0.0,
            '0,0': 0.0,
            '0,1': 0.0,
            '1,0': 0.0,
        },
        indent=2,
    ),
}


def image_preset_change_callback(sender, app_data, user_data):
    if app_data in IMAGE_PRESETS:
        dpg.set_value('img_conv_image_input', IMAGE_PRESETS[app_data])


def kernel_preset_change_callback(sender, app_data, user_data):
    if app_data in KERNEL_PRESETS:
        dpg.set_value('img_conv_kernel_input', KERNEL_PRESETS[app_data])


def run_image_convolution_2d(sender=None, app_data=None):
    try:
        img_str = dpg.get_value('img_conv_image_input')
        kernel_str = dpg.get_value('img_conv_kernel_input')
        semiring_name = dpg.get_value('img_conv_semiring_select')

        parsed_img = parse_2d_sparse_vector(img_str)
        parsed_kernel = parse_2d_sparse_vector(kernel_str)

        if 'Arctic' in semiring_name or 'Dilation' in semiring_name:
            semiring = ArcticSemiring()
        elif 'Tropical' in semiring_name or 'Erosion' in semiring_name:
            semiring = TropicalSemiring()
        else:
            semiring = StandardSemiring()

        res = convolve(
            parsed_img,
            parsed_kernel,
            key_op=lambda p1, p2: (p1[0] + p2[0], p1[1] + p2[1]),
            semiring=semiring,
        )

        if dpg.does_item_exist('table_img_conv_res'):
            dpg.delete_item('table_img_conv_res', children_only=True)

        dpg.add_table_column(parent='table_img_conv_res', label='(Row, Col)')
        dpg.add_table_column(parent='table_img_conv_res', label='Convolved Intensity')

        for (r, c), val in sorted(res.items()):
            with dpg.table_row(parent='table_img_conv_res'):
                dpg.add_text(f'({r}, {c})')
                dpg.add_text(f'{val:.4f}')

        # ASCII Grid Preview
        min_r = min([r for r, _ in res] + [0])
        max_r = max([r for r, _ in res] + [7])
        min_c = min([c for _, c in res] + [0])
        max_c = max([c for _, c in res] + [7])

        ascii_rows = []
        for r in range(min_r, max_r + 1):
            line = []
            for c in range(min_c, max_c + 1):
                v = res.get((r, c), 0.0)
                if v > 0.7:
                    line.append('##')
                elif v > 0.2:
                    line.append('::')
                elif v < -0.2:
                    line.append('--')
                else:
                    line.append('  ')
            ascii_rows.append(''.join(line))

        preview_text = '\n'.join(ascii_rows)
        dpg.set_value('img_conv_ascii_preview', preview_text)

        # Update Input and Output Texture Previews
        rgba_input = []
        for r in range(TEXTURE_HEIGHT):
            for c in range(TEXTURE_WIDTH):
                v = parsed_img.get((r, c), 0.0)
                rgba_input.extend([v, v, v, 1.0])
        if dpg.does_item_exist('texture_img_input'):
            dpg.set_value('texture_img_input', rgba_input)

        max_v = max((abs(v) for v in res.values()), default=1.0)
        if max_v == 0:
            max_v = 1.0

        rgba_output = []
        for r in range(TEXTURE_HEIGHT):
            for c in range(TEXTURE_WIDTH):
                v = res.get((r, c), 0.0)
                if v >= 0:
                    norm = min(1.0, v / max_v)
                    rgba_output.extend([norm, norm, norm, 1.0])
                else:
                    norm = min(1.0, abs(v) / max_v)
                    rgba_output.extend([norm, 0.0, 0.0, 1.0])
        if dpg.does_item_exist('texture_img_output'):
            dpg.set_value('texture_img_output', rgba_output)

        msg = (
            f'Convolved {len(parsed_img)} image pixels with {len(parsed_kernel)} kernel entries '
            f'-> {len(res)} result pixels.'
        )
        dpg.set_value('img_conv_status', msg)

    except Exception as e:
        dpg.set_value('img_conv_status', f'Error: {e}')


def file_selected_callback(sender, app_data, user_data):
    file_path = app_data.get('file_path_name', '')
    if file_path:
        dpg.set_value('img_conv_filepath_input', file_path)
        load_image_file_into_lab(file_path)


def open_file_dialog_callback(sender, app_data, user_data):
    if not dpg.does_item_exist('image_file_dialog'):
        with dpg.file_dialog(
            directory_selector=False,
            show=False,
            callback=file_selected_callback,
            tag='image_file_dialog',
            width=700,
            height=400,
        ):
            dpg.add_file_extension('.png', color=(0, 255, 0, 255))
            dpg.add_file_extension('.jpg', color=(0, 255, 0, 255))
            dpg.add_file_extension('.jpeg', color=(0, 255, 0, 255))
            dpg.add_file_extension('.bmp', color=(0, 255, 0, 255))
            dpg.add_file_extension('.webp', color=(0, 255, 0, 255))
            dpg.add_file_extension('.*')
    dpg.show_item('image_file_dialog')


def load_image_file_into_lab(file_path: str):
    if not HAS_PILLOW:
        dpg.set_value('img_conv_status', 'Error: Pillow (PIL) library is required to load image files.')
        return

    try:
        im = Image.open(file_path).convert('L')
        im = im.resize((TEXTURE_WIDTH, TEXTURE_HEIGHT))

        sparse_img = {}
        rgba_input = []

        for r in range(TEXTURE_HEIGHT):
            for c in range(TEXTURE_WIDTH):
                val_norm = float(im.getpixel((c, r))) / 255.0
                if val_norm > 0:
                    sparse_img[(r, c)] = val_norm
                rgba_input.extend([val_norm, val_norm, val_norm, 1.0])

        if dpg.does_item_exist('texture_img_input'):
            dpg.set_value('texture_img_input', rgba_input)

        sparse_json = json.dumps({f'{r},{c}': round(v, 3) for (r, c), v in sparse_img.items()}, indent=2)
        dpg.set_value('img_conv_image_input', sparse_json)
        dpg.set_value(
            'img_conv_status',
            f"Loaded '{file_path}' ({TEXTURE_WIDTH}x{TEXTURE_HEIGHT}, {len(sparse_img)} active pixels).",
        )
        run_image_convolution_2d()

    except Exception as e:
        dpg.set_value('img_conv_status', f'Failed to load image file: {e}')


# --- Tab 11 Preset Graph Builders ---
def _get_preset_graph(name):
    if name == 'Star Graph':
        nodes = [0, 1, 2, 3, 4, 5, 6, 7]
        edges = [(0, i) for i in range(1, 8)]
    elif name == 'Cycle Graph':
        nodes = list(range(8))
        edges = [(i, (i + 1) % 8) for i in range(8)]
    elif name == 'Tree Graph':
        nodes = list(range(7))
        edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
    elif name == 'Grid Graph':
        nodes = list(range(9))
        edges = []
        for r in range(3):
            for c in range(3):
                u = r * 3 + c
                if c < 2:
                    edges.append((u, u + 1))
                if r < 2:
                    edges.append((u, u + 3))
    else:  # Barbell Graph
        nodes = list(range(6))
        edges = [
            (0, 1),
            (1, 2),
            (2, 0),  # Clique 1
            (3, 4),
            (4, 5),
            (5, 3),  # Clique 2
            (2, 3),  # Bridge
        ]

    adj = {n: {} for n in nodes}
    for u, v in edges:
        adj[u][v] = 1.0
        adj[v][u] = 1.0
    return adj, nodes, edges


def update_curvature_plot():
    if not current_edges:
        return

    x_values = []
    y_values = []

    for idx, (u, v) in enumerate(sorted(current_edges)):
        k_val = current_curvatures.get((u, v), current_curvatures.get((v, u), 0.0))
        x_values.append(float(idx))
        y_values.append(float(k_val))

    if dpg.does_item_exist('curvature_bar_series'):
        dpg.delete_item('curvature_bar_series')

    dpg.add_bar_series(
        x_values, y_values, weight=0.6, parent='curvature_y_axis', tag='curvature_bar_series', label='Edge Curvatures'
    )
    dpg.fit_axis_data('curvature_x_axis')
    dpg.fit_axis_data('curvature_y_axis')


def recalculate_and_reset_layout(sender=None, app_data=None):
    global current_nodes, current_edges, current_curvatures, pos, vel
    preset = dpg.get_value('vis_preset')
    weighted = dpg.get_value('vis_weighted')
    augmented = dpg.get_value('vis_augmented')

    adj, nodes, edges = _get_preset_graph(preset)

    if weighted:
        for u, v in edges:
            weight = 1.8 if (u + v) % 2 == 0 else 0.6
            adj[u][v] = weight
            adj[v][u] = weight

    current_nodes = nodes
    current_edges = edges

    try:
        current_curvatures = forman_ricci_curvature(adj, weighted=weighted, augmented=augmented)
    except Exception as e:
        current_curvatures = {}
        dpg.set_value('vis_status', f'Error: {e}')
        return

    n_nodes = len(nodes)
    pos = {}
    vel = {}
    for idx, node in enumerate(nodes):
        angle = (2 * math.pi * idx) / n_nodes
        ox = random.uniform(-6.0, 6.0)
        oy = random.uniform(-6.0, 6.0)
        pos[node] = [350.0 + 160.0 * math.cos(angle) + ox, 225.0 + 160.0 * math.sin(angle) + oy]
        vel[node] = [0.0, 0.0]

    update_curvature_plot()
    dpg.set_value('vis_status', f'Loaded {preset}. Calculated curvatures for {len(edges)} edges.')


def jostle_graph_callback():
    for u in current_nodes:
        vel[u][0] += random.uniform(-25.0, 25.0)
        vel[u][1] += random.uniform(-25.0, 25.0)


# --- Tab 11 Physics Animation Helpers ---
def _compute_physics_forces():
    global pos, vel, dragged_node
    k_rep = 1200.0
    k_spring = 0.08
    rest_l = 90.0
    k_grav = 0.015
    damping = 0.85
    dt = 0.4
    cx, cy = 350.0, 225.0

    forces = {n: [0.0, 0.0] for n in current_nodes}

    # Repulsion
    for i in range(len(current_nodes)):
        u = current_nodes[i]
        for j in range(i + 1, len(current_nodes)):
            v = current_nodes[j]
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            dist = math.hypot(dx, dy)
            if dist < 1.0:
                dist = 1.0
            f = k_rep / (dist * dist)
            fx = f * (dx / dist)
            fy = f * (dy / dist)
            forces[u][0] += fx
            forces[u][1] += fy
            forces[v][0] -= fx
            forces[v][1] -= fy

    # Spring forces along edges
    for u, v in current_edges:
        dx = pos[u][0] - pos[v][0]
        dy = pos[u][1] - pos[v][1]
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            dist = 1.0
        displacement = dist - rest_l
        f = -k_spring * displacement
        fx = f * (dx / dist)
        fy = f * (dy / dist)
        forces[u][0] += fx
        forces[u][1] += fy
        forces[v][0] -= fx
        forces[v][1] -= fy

    # Gravity towards center
    for u in current_nodes:
        dx = cx - pos[u][0]
        dy = cy - pos[u][1]
        forces[u][0] += k_grav * dx
        forces[u][1] += k_grav * dy

    # Update velocities and positions
    for u in current_nodes:
        if u == dragged_node:
            continue
        vel[u][0] = (vel[u][0] + forces[u][0] * dt) * damping
        vel[u][1] = (vel[u][1] + forces[u][1] * dt) * damping
        pos[u][0] += vel[u][0] * dt
        pos[u][1] += vel[u][1] * dt

        pos[u][0] = max(15.0, min(685.0, pos[u][0]))
        pos[u][1] = max(15.0, min(435.0, pos[u][1]))


def _handle_mouse_dragging():
    global dragged_node, pos, vel
    if dpg.is_mouse_button_down(dpg.mvMouseButton_Left) and pos:
        mx, my = dpg.get_mouse_pos(local=False)
        c_min = dpg.get_item_rect_min('vis_canvas')
        if c_min and c_min[0] > 0:
            lx = mx - c_min[0]
            ly = my - c_min[1]

            if dragged_node is None:
                closest = None
                min_d = 25.0
                for node in current_nodes:
                    d = math.hypot(pos[node][0] - lx, pos[node][1] - ly)
                    if d < min_d:
                        min_d = d
                        closest = node
                dragged_node = closest

            if dragged_node is not None:
                pos[dragged_node] = [lx, ly]
                vel[dragged_node] = [0.0, 0.0]
    else:
        dragged_node = None


def _redraw_canvas():
    if dpg.does_item_exist('vis_canvas') and pos:
        dpg.delete_item('vis_canvas', children_only=True)
        # Background
        dpg.draw_rectangle((0, 0), (700, 450), color=(40, 40, 48), fill=(24, 24, 28), thickness=1, parent='vis_canvas')

        # Edges
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

        # Nodes
        for u in current_nodes:
            p = pos[u]
            dpg.draw_circle(p, radius=14, color=(140, 140, 180), fill=(48, 48, 72), thickness=2, parent='vis_canvas')
            dpg.draw_text((p[0] - 6, p[1] - 9), str(u), color=(255, 255, 255), size=14, parent='vis_canvas')


def update_graph_simulation():
    run_physics = dpg.get_value('vis_run_physics')
    if run_physics and pos:
        _compute_physics_forces()
    _handle_mouse_dragging()
    _redraw_canvas()


# --- Dear PyGui Window Layout Setup ---

dpg.create_context()

# Initialize 64x64 Dynamic Image Textures
init_texture_data = [0.1, 0.1, 0.1, 1.0] * (TEXTURE_WIDTH * TEXTURE_HEIGHT)
with dpg.texture_registry(show=False):
    dpg.add_dynamic_texture(
        width=TEXTURE_WIDTH, height=TEXTURE_HEIGHT, default_value=init_texture_data, tag='texture_img_input'
    )
    dpg.add_dynamic_texture(
        width=TEXTURE_WIDTH, height=TEXTURE_HEIGHT, default_value=init_texture_data, tag='texture_img_output'
    )

dpg.create_viewport(title='AlgebraX Graphical Laboratory', width=1200, height=900)


def setup_window_icon():
    import os

    from PIL import Image

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

# Configure elegant Dark Theme
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


# Views list for navigation
VIEWS = [
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


def change_view(sender, app_data, user_data):
    selected_view = user_data
    for v in VIEWS:
        dpg.set_value(f'sel_{v}', (v == selected_view))
        if v == selected_view:
            dpg.show_item(f'view_{v}_group')
        else:
            dpg.hide_item(f'view_{v}_group')


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
        # --- LEFT PANE: EXPLORER SIDEBAR ---
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

        # --- RIGHT PANE: DETAIL VIEW ---
        with dpg.child_window(width=-1, height=-1, border=False):
            # --- VIEW 1: SEMIRINGS ---
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
                with dpg.table(
                    header_row=True,
                    tag='table_semiring_res',
                    borders_innerH=True,
                    borders_innerV=True,
                    borders_outerH=True,
                    borders_outerV=True,
                ):
                    pass

            # --- VIEW 2: CURVATURE ---
            with dpg.group(tag='view_forman_ricci_curvature_group', show=False):
                dpg.add_text(
                    'Compute discrete Forman-Ricci curvature on weighted/unweighted networks.', color=(180, 180, 180)
                )

                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label='Weighted Graph', default_value=False, tag='curvature_weighted')
                    dpg.add_checkbox(
                        label='Augmented Curvature (Triangles)', default_value=True, tag='curvature_augmented'
                    )

                dpg.add_text('Adjacency Graph (JSON format):')
                default_curv_graph = (
                    '{\n  "0": {"1": 1, "2": 1},\n'
                    '  "1": {"0": 1, "2": 1},\n'
                    '  "2": {"0": 1, "1": 1, "3": 1},\n'
                    '  "3": {"2": 1, "4": 1, "5": 1},\n'
                    '  "4": {"3": 1},\n'
                    '  "5": {"3": 1}\n}'
                )
                dpg.add_input_text(
                    default_value=default_curv_graph, multiline=True, tag='curvature_graph_input', height=150, width=800
                )

                dpg.add_button(label='Analyze Graph Curvature', callback=run_curvature)
                dpg.add_text('', tag='curvature_status', color=(255, 200, 100))

                dpg.add_text('Calculated Edge Curvatures:')
                with dpg.table(
                    header_row=True,
                    tag='table_curvature',
                    borders_innerH=True,
                    borders_innerV=True,
                    borders_outerH=True,
                    borders_outerV=True,
                ):
                    pass

            # --- VIEW 3: CRYPTO ---
            with dpg.group(tag='view_pq_key_exchange_group', show=False):
                dpg.add_text(
                    'Simulation of diffie-hellman key exchange over the Digital Semiring.', color=(180, 180, 180)
                )

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
                        with dpg.table(
                            header_row=True,
                            tag='table_crypto_u',
                            width=180,
                            borders_innerH=True,
                            borders_innerV=True,
                            borders_outerH=True,
                            borders_outerV=True,
                        ):
                            pass
                    with dpg.group():
                        dpg.add_text('Bob Public V:')
                        with dpg.table(
                            header_row=True,
                            tag='table_crypto_v',
                            width=180,
                            borders_innerH=True,
                            borders_innerV=True,
                            borders_outerH=True,
                            borders_outerV=True,
                        ):
                            pass
                    with dpg.group():
                        dpg.add_text('Alice Shared Key K_A:')
                        with dpg.table(
                            header_row=True,
                            tag='table_crypto_ka',
                            width=180,
                            borders_innerH=True,
                            borders_innerV=True,
                            borders_outerH=True,
                            borders_outerV=True,
                        ):
                            pass
                    with dpg.group():
                        dpg.add_text('Bob Shared Key K_B:')
                        with dpg.table(
                            header_row=True,
                            tag='table_crypto_kb',
                            width=180,
                            borders_innerH=True,
                            borders_innerV=True,
                            borders_outerH=True,
                            borders_outerV=True,
                        ):
                            pass

            # --- VIEW 4: TRIE / TENSOR ---
            with dpg.group(tag='view_algebraic_trie_group', show=False):
                dpg.add_text(
                    'Algebraic Tries represent nested sparse tensors capable of contracting/marginalizing dimensions.',
                    color=(180, 180, 180),
                )

                dpg.add_text('Tensor Points [[coordinate_tuple, value], ...]:')
                default_points = (
                    '[\n  [[0, 0, 0], 1.0],\n  [[0, 0, 0], 2.0],\n  [[0, 1, 0], 5.0],\n  [[1, 0, 0], 10.0]\n]'
                )
                dpg.add_input_text(
                    default_value=default_points, multiline=True, tag='trie_points_input', height=120, width=800
                )

                dpg.add_text('Contract Dimensions (JSON list of indices, e.g. [0] or [0, 0]):')
                dpg.add_input_text(default_value='[0]', tag='trie_contract_dims', width=300)

                dpg.add_button(label='Contract Sparse Tensor', callback=run_trie_operations)
                dpg.add_text('', tag='trie_status', color=(255, 200, 100))

                dpg.add_text('Trie Contents:')
                dpg.add_text('  (No data populated yet)', tag='trie_contents_text', color=(160, 160, 160))
                dpg.add_text('Contracted Result: None', tag='trie_result_text', color=(100, 255, 100))

            # --- VIEW 5: PAGERANK ---
            with dpg.group(tag='view_pagerank_group', show=False):
                dpg.add_text(
                    'Compute PageRank (algebraic stationary distribution of a random walk).', color=(180, 180, 180)
                )

                with dpg.group(horizontal=True):
                    dpg.add_text('Damping (alpha):')
                    dpg.add_input_float(default_value=0.85, tag='pagerank_alpha', width=120)
                    dpg.add_text('Iterations:')
                    dpg.add_input_int(default_value=20, tag='pagerank_iterations', width=100)

                dpg.add_text('Web Graph Adjacency List (JSON format):')
                default_web = '{\n  "A": {"B": 1, "C": 1},\n  "B": {"C": 1},\n  "C": {"A": 1}\n}'
                dpg.add_input_text(
                    default_value=default_web, multiline=True, tag='pagerank_graph', height=120, width=800
                )

                dpg.add_button(label='Compute PageRank', callback=run_pagerank)
                dpg.add_text('', tag='pagerank_status', color=(255, 200, 100))

                dpg.add_text('Resulting Ranks:')
                with dpg.table(
                    header_row=True,
                    tag='table_pagerank',
                    width=300,
                    borders_innerH=True,
                    borders_innerV=True,
                    borders_outerH=True,
                    borders_outerV=True,
                ):
                    pass

            # --- VIEW 6: CYK PARSING ---
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
                dpg.add_input_text(
                    default_value=default_cyk_lexicon, multiline=True, tag='cyk_lexicon', height=100, width=800
                )

                dpg.add_text('Chomsky Normal Form Grammar Rules (comma-separated inputs, JSON format):')
                default_cyk_rules = '{\n  "NP,VP": ["S"],\n  "V,NP": ["VP"]\n}'
                dpg.add_input_text(
                    default_value=default_cyk_rules, multiline=True, tag='cyk_rules', height=100, width=800
                )

                dpg.add_button(label='Parse Sentence', callback=run_cyk_parsing)
                dpg.add_text('', tag='cyk_status', color=(255, 200, 100))
                dpg.add_text('Parses as: None', tag='cyk_result_text', color=(100, 255, 100))

                dpg.add_text('Parsing Chart Spans:')
                with dpg.table(
                    header_row=True,
                    tag='table_cyk_chart',
                    borders_innerH=True,
                    borders_innerV=True,
                    borders_outerH=True,
                    borders_outerV=True,
                ):
                    pass

            # --- VIEW 7: SLOPE TRANSFORM ---
            with dpg.group(tag='view_slope_transform_group', show=False):
                dpg.add_text(
                    'Evaluate the Fenchel-Legendre Transform (Tropical/Idempotent Fourier analog) of a signal.',
                    color=(180, 180, 180),
                )

                dpg.add_text('Signal Vector f(x) (JSON format):')
                default_signal = '{\n  "0": 0.0,\n  "1": 1.0,\n  "2": 4.0,\n  "3": 9.0\n}'
                dpg.add_input_text(
                    default_value=default_signal, multiline=True, tag='fenchel_signal', height=100, width=800
                )

                dpg.add_text('Slopes to Evaluate (s) (JSON list):')
                default_slopes = '[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]'
                dpg.add_input_text(default_value=default_slopes, tag='fenchel_slopes', width=400)

                dpg.add_button(label='Compute Convex Conjugates', callback=run_legendre_fenchel)
                dpg.add_text('', tag='fenchel_status', color=(255, 200, 100))

                dpg.add_text('Convex Conjugate Values f*(s) = sup_x (s*x - f(x)):')
                with dpg.table(
                    header_row=True,
                    tag='table_fenchel',
                    width=350,
                    borders_innerH=True,
                    borders_innerV=True,
                    borders_outerH=True,
                    borders_outerV=True,
                ):
                    pass

            # --- VIEW 8: AUTOMATA SIMULATOR ---
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
                    '{\n  "q0": {"0": "q0", "1": "q1"},\n'
                    '  "q1": {"0": "q2", "1": "q0"},\n'
                    '  "q2": {"0": "q1", "1": "q2"}\n}'
                )
                dpg.add_input_text(
                    default_value=default_dfa_trans, multiline=True, tag='automata_transitions', height=150, width=800
                )

                dpg.add_button(label='Simulate Automaton', callback=run_automata_sim)
                dpg.add_text('', tag='automata_status', color=(255, 200, 100))
                dpg.add_text('Result: Not Run', tag='automata_result_text', color=(100, 255, 100))

                dpg.add_text('Simulation Trajectory Log:')
                dpg.add_input_text(multiline=True, tag='automata_log_text', readonly=True, height=150, width=800)

            # --- VIEW 9: MARKOV & INFO THEORY ---
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
                            default_value=default_markov_matrix,
                            multiline=True,
                            tag='markov_matrix',
                            height=100,
                            width=380,
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
                                with dpg.table(
                                    header_row=True,
                                    tag='table_markov_steps',
                                    width=180,
                                    borders_innerH=True,
                                    borders_innerV=True,
                                    borders_outerH=True,
                                    borders_outerV=True,
                                ):
                                    pass
                            with dpg.group():
                                dpg.add_text('Analytical Steady State:')
                                with dpg.table(
                                    header_row=True,
                                    tag='table_markov_steady',
                                    width=180,
                                    borders_innerH=True,
                                    borders_innerV=True,
                                    borders_outerH=True,
                                    borders_outerV=True,
                                ):
                                    pass

                    with dpg.group(width=390):
                        dpg.add_text('INFORMATION THEORY LAB', color=(150, 180, 255))
                        dpg.add_separator()

                        dpg.add_text('Distribution P (True):')
                        dpg.add_input_text(default_value='{"A": 0.5, "B": 0.25, "C": 0.25}', tag='info_p', width=380)

                        dpg.add_text('Distribution Q (Reference/Model):')
                        dpg.add_input_text(default_value='{"A": 0.4, "B": 0.3, "C": 0.3}', tag='info_q', width=380)

                        dpg.add_text('Joint Distribution P(X, Y) (JSON matrix):')
                        default_joint = '{\n  "X1": {"Y1": 0.25, "Y2": 0.25},\n  "X2": {"Y1": 0.25, "Y2": 0.25}\n}'
                        dpg.add_input_text(
                            default_value=default_joint, multiline=True, tag='info_joint', height=80, width=380
                        )

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

            # --- VIEW 10: SIGNAL TRANSFORMS ---
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
                with dpg.table(
                    header_row=True,
                    tag='table_signal_res',
                    borders_innerH=True,
                    borders_innerV=True,
                    borders_outerH=True,
                    borders_outerV=True,
                ):
                    pass

            # --- VIEW 11: 2D IMAGE CONVOLUTION ---
            with dpg.group(tag='view_image_convolution_2d_group', show=False):
                dpg.add_text(
                    'Perform 2D Image & Grid Convolution via algebrax.transforms.convolve '
                    'using 2D vector key addition.',
                    color=(180, 180, 180),
                )

                # Real File Loader Row
                with dpg.group(horizontal=True):
                    dpg.add_text('Load Real Image File:')
                    dpg.add_input_text(
                        tag='img_conv_filepath_input', hint='Path to PNG, JPG, BMP image file...', width=380
                    )
                    dpg.add_button(label='Browse...', callback=open_file_dialog_callback)
                    dpg.add_button(
                        label='Load Image',
                        callback=lambda: load_image_file_into_lab(dpg.get_value('img_conv_filepath_input')),
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

                # Textures and Result Preview Row
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
                        with dpg.table(
                            header_row=True,
                            tag='table_img_conv_res',
                            borders_innerH=True,
                            borders_innerV=True,
                            borders_outerH=True,
                            borders_outerV=True,
                            height=160,
                            width=220,
                        ):
                            pass

            # --- VIEW 12: NETWORK CURVATURE VIS ---
            with dpg.group(tag='view_network_curvature_vis_group', show=False):
                dpg.add_text(
                    'Interactive Force-Directed Layout & Forman-Ricci Curvature Visualization', color=(150, 180, 255)
                )

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


dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window(main_window, True)

# Initialize the visualization preset
recalculate_and_reset_layout()

# Render loop
while dpg.is_dearpygui_running():
    update_graph_simulation()
    dpg.render_dearpygui_frame()

dpg.destroy_context()
