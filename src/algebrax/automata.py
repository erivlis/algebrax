"""
Formal languages operations and simulation functions.

This module provides utility functions for simulating Deterministic and
Nondeterministic Finite Automata, as well as performing individual transitions
for each.

Functions:
- dfa_step: Handle a single transition step in a Deterministic Finite Automaton.
- nfa_step: Handle a single transition step in a Nondeterministic Finite
  Automaton or Probabilistic Automaton.
- simulate_dfa: Simulate a DFA for a given input sequence.
- simulate_nfa: Simulate an NFA or Probabilistic Automaton for a given input
  sequence.

"""

from collections import defaultdict
from collections.abc import Iterable, Mapping

from algebrax.algebra import HasStar, Semiring, StarSemiring
from algebrax.converters import canonical_sort_keys, make_zero_predicate
from algebrax.matrix.closure import matrix_star
from algebrax.semiring import BooleanSemiring
from algebrax.typing import A, S, SparseMatrix, V

__all__ = [
    'dfa_step',
    'nfa_closure',
    'nfa_step',
    'simulate_dfa',
    'simulate_nfa',
]


def dfa_step(
    current_state: S,
    symbol: A,
    transitions: Mapping[S, Mapping[A, S]],
) -> S | None:
    """
    Perform a single step in a Deterministic Finite Automaton (DFA).
    delta: S x A -> S

    Args:
        current_state: The current state.
        symbol: The input symbol.
        transitions: The transition function {state: {symbol: next_state}}.

    Returns:
        The next state, or None if the transition is undefined (implicit sink state).
    """
    if current_state in transitions:
        return transitions[current_state].get(symbol)
    return None


def nfa_step(
    current_states: Mapping[S, V],
    symbol: A,
    transitions: Mapping[S, Mapping[A, Mapping[S, V]]],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> dict[S, V]:
    """
    Perform a single step in a Nondeterministic or Weighted Finite Automaton (WFA).
    delta: S x A -> (S -> V)

    Supports standard probabilistic NFAs (fast native float path when `semiring is None`)
    as well as arbitrary semiring-weighted automata (`BooleanSemiring`, `TropicalSemiring`,
    `ViterbiSemiring`, `StringSemiring`, etc.).

    Args:
        current_states: A mapping of current states to their weights/probabilities.
        symbol: The input symbol.
        transitions: The transition function {state: {symbol: {next_state: weight}}}.
        semiring: Optional semiring instance, class, or catalog name. When `None`, uses
            fast native Python float arithmetic.

    Returns:
        A mapping of next states to their accumulated weights.
    """
    if semiring is None:
        next_states_f: defaultdict[S, float] = defaultdict(float)
        for state, weight in current_states.items():
            if weight == 0.0 or state not in transitions:
                continue
            symbol_transitions = transitions[state].get(symbol)
            if symbol_transitions:
                for next_state, trans_weight in symbol_transitions.items():
                    if trans_weight == 0.0:
                        continue
                    next_states_f[next_state] += weight * trans_weight  # type: ignore[operator]
        return {s: w for s, w in next_states_f.items() if w != 0.0}  # type: ignore[return-value]

    sr = Semiring.normalize(semiring)
    is_zero = make_zero_predicate(sr)
    add_op = sr.add
    mul_op = sr.mul

    next_states: dict[S, V] = {}
    for state, weight in current_states.items():
        if is_zero(weight) or state not in transitions:
            continue
        symbol_transitions = transitions[state].get(symbol)
        if not symbol_transitions:
            continue
        for next_state, trans_weight in symbol_transitions.items():
            if is_zero(trans_weight):
                continue
            prod = mul_op(weight, trans_weight)
            if is_zero(prod):
                continue
            if next_state in next_states:
                combined = add_op(next_states[next_state], prod)
                if is_zero(combined):
                    del next_states[next_state]
                else:
                    next_states[next_state] = combined
            else:
                next_states[next_state] = prod

    return next_states


def simulate_dfa(
    start_state: S,
    input_sequence: Mapping[int, A] | Iterable[A],
    transitions: Mapping[S, Mapping[A, S]],
) -> S | None:
    """
    Simulate a DFA on an input sequence.

    Args:
        start_state: The initial state.
        input_sequence: A mapping {time_step: symbol} or iterable of symbols.
        transitions: The transition function.

    Returns:
        The final state, or None if the machine crashed.
    """
    current: S | None = start_state

    # Handle both dicts (sparse sequence) and lists/iterables
    if isinstance(input_sequence, Mapping):
        steps = sorted(input_sequence.keys())
        sequence: Iterable[A] = (input_sequence[k] for k in steps)
    else:
        sequence = input_sequence

    for symbol in sequence:
        current = dfa_step(current, symbol, transitions)
        if current is None:
            return None

    return current


def simulate_nfa(
    start_states: Mapping[S, V],
    input_sequence: Mapping[int, A] | Iterable[A],
    transitions: Mapping[S, Mapping[A, Mapping[S, V]]],
    semiring: Semiring[V] | type[Semiring[V]] | str | None = None,
) -> dict[S, V]:
    """
    Simulate an NFA, Probabilistic Automaton, or Weighted Finite Automaton on an input sequence.

    Always returns a fresh dictionary copy (including on empty input sequences).

    Args:
        start_states: Initial distribution of states.
        input_sequence: A mapping {time_step: symbol} or iterable of symbols.
        transitions: The transition function `{state: {symbol: {next_state: weight}}}`.
        semiring: Optional semiring instance, class, or catalog name.

    Returns:
        The final distribution of states as a fresh dictionary.
    """
    sr = Semiring.normalize(semiring) if semiring is not None else None
    current: dict[S, V] = dict(start_states)

    if isinstance(input_sequence, Mapping):
        steps = sorted(input_sequence.keys())
        sequence: Iterable[A] = (input_sequence[k] for k in steps)
    else:
        sequence = input_sequence

    for symbol in sequence:
        current = nfa_step(current, symbol, transitions, semiring=sr)
        if not current:
            break

    return current


def nfa_closure(
    transitions: Mapping[S, Mapping[A, Mapping[S, V]]],
    *,
    symbol: A | None = None,
    semiring: StarSemiring[V] | type[StarSemiring[V]] | str = BooleanSemiring,
) -> SparseMatrix[S, V]:
    r"""Compute all-path (`symbol=None`) or single-symbol/epsilon Kleene closure via `matrix_star`.

    Algebraic Signature:
        $\delta^* = \left(\bigoplus_{a \in \Sigma} M_a\right)^* \quad \text{or} \quad M_a^*$

    Projects the 3-level NFA transition tensor `{src: {sym: {dst: weight}}}` into a
    2-level sparse transition matrix over `semiring`, then delegates to Conway's block
    Kleene star (`algebrax.matrix.closure.matrix_star`).

    Args:
        transitions: 3-level transition tensor `{state: {symbol: {next_state: weight}}}`.
        symbol: If provided, computes closure strictly along transitions labeled with `symbol`
            (e.g., epsilon-closure). If `None`, sums across all symbols in the alphabet.
        semiring: `StarSemiring` instance, class, or catalog name (default: `BooleanSemiring`).

    Returns:
        Sparse reachability / all-pairs Kleene closure matrix `{src: {dst: weight}}`.

    Raises:
        TypeError: If `semiring` does not satisfy `HasStar` (e.g., `StringSemiring`).
    """
    sr = Semiring.normalize(semiring)  # type: ignore[arg-type]
    if not isinstance(sr, HasStar):
        raise TypeError(
            f"nfa_closure requires a StarSemiring implementing HasStar, got '{type(sr).__name__}'."
        )

    is_zero = make_zero_predicate(sr)
    add_op = sr.add
    nodes: set[S] = set(transitions.keys())
    mat: dict[S, dict[S, V]] = {}

    for src, sym_map in transitions.items():
        for sym, targets in sym_map.items():
            nodes.update(targets.keys())
            if symbol is not None and sym != symbol:
                continue
            row = mat.setdefault(src, {})
            for dst, weight in targets.items():
                if is_zero(weight):
                    continue
                if dst in row:
                    combined = add_op(row[dst], weight)
                    if is_zero(combined):
                        del row[dst]
                    else:
                        row[dst] = combined
                else:
                    row[dst] = weight

    mat = {src: row for src, row in mat.items() if row}
    if not nodes:
        return {}
    return matrix_star(mat, semiring=sr, nodes=canonical_sort_keys(nodes))
