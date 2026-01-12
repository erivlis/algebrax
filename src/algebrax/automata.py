from collections import defaultdict
from collections.abc import Mapping

from algebrax.typing import A, S

__all__ = [
    'dfa_step',
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
    current_states: Mapping[S, float],
    symbol: A,
    transitions: Mapping[S, Mapping[A, Mapping[S, float]]],
) -> dict[S, float]:
    """
    Perform a single step in a Nondeterministic Finite Automaton (NFA) or Probabilistic Automaton.
    delta: S x A -> P(S)

    This handles both standard NFAs (where values are 1.0) and Probabilistic Automata
    (where values are probabilities).

    Args:
        current_states: A mapping of current states to their weights/probabilities.
        symbol: The input symbol.
        transitions: The transition function {state: {symbol: {next_state: weight}}}.

    Returns:
        A mapping of next states to their accumulated weights.
    """
    next_states = defaultdict(float)

    for state, weight in current_states.items():
        if state in transitions:
            symbol_transitions = transitions[state].get(symbol)
            if symbol_transitions:
                for next_state, trans_weight in symbol_transitions.items():
                    next_states[next_state] += weight * trans_weight

    return dict(next_states)


def simulate_dfa(
    start_state: S,
    input_sequence: Mapping[int, A],
    transitions: Mapping[S, Mapping[A, S]],
) -> S | None:
    """
    Simulate a DFA on an input sequence.

    Args:
        start_state: The initial state.
        input_sequence: A mapping {time_step: symbol} or list of symbols.
        transitions: The transition function.

    Returns:
        The final state, or None if the machine crashed.
    """
    current = start_state

    # Handle both dicts (sparse sequence) and lists/iterables
    if isinstance(input_sequence, Mapping):
        # Sort by time index
        steps = sorted(input_sequence.keys())
        sequence = (input_sequence[k] for k in steps)
    else:
        sequence = input_sequence

    for symbol in sequence:
        current = dfa_step(current, symbol, transitions)
        if current is None:
            return None

    return current


def simulate_nfa(
    start_states: Mapping[S, float],
    input_sequence: Mapping[int, A],
    transitions: Mapping[S, Mapping[A, Mapping[S, float]]],
) -> dict[S, float]:
    """
    Simulate an NFA or Probabilistic Automaton on an input sequence.

    Args:
        start_states: Initial distribution of states.
        input_sequence: A mapping {time_step: symbol} or list of symbols.
        transitions: The transition function.

    Returns:
        The final distribution of states.
    """
    current = start_states

    if isinstance(input_sequence, Mapping):
        steps = sorted(input_sequence.keys())
        sequence = (input_sequence[k] for k in steps)
    else:
        sequence = input_sequence

    for symbol in sequence:
        current = nfa_step(current, symbol, transitions)
        if not current:
            break

    return current
