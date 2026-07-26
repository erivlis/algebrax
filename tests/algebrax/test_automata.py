from algebrax.automata import (
    dfa_step,
    nfa_step,
    simulate_dfa,
    simulate_nfa,
)


def test_dfa():
    # 0 --a--> 1 --b--> 2
    trans = {0: {'a': 1}, 1: {'b': 2}}

    assert dfa_step(0, 'a', trans) == 1
    assert dfa_step(0, 'b', trans) is None

    assert simulate_dfa(0, 'ab', trans) == 2
    assert simulate_dfa(0, 'ac', trans) is None


def test_nfa():
    # 0 --a--> 0 (0.5)
    # 0 --a--> 1 (0.5)
    trans = {0: {'a': {0: 0.5, 1: 0.5}}}

    start = {0: 1.0}
    next_state = nfa_step(start, 'a', trans)
    assert next_state == {0: 0.5, 1: 0.5}

    # Simulate
    final = simulate_nfa(start, 'a', trans)
    assert final == {0: 0.5, 1: 0.5}


def test_dfa_step_missing():
    assert dfa_step('q0', 'a', {}) is None


def test_nfa_step_missing():
    assert nfa_step({'q0': 1.0}, 'a', {}) == {}


def test_simulate_dfa_list_input():
    trans = {0: {'a': 1}}
    assert simulate_dfa(0, ['a'], trans) == 1


def test_simulate_dfa_mapping_input():
    trans = {0: {'a': 1, 'b': 2}, 1: {'b': 2}}
    seq = {0: 'a', 10: 'b'}
    assert simulate_dfa(0, seq, trans) == 2


def test_simulate_nfa_list_input():
    trans = {0: {'a': {1: 1.0}}}
    assert simulate_nfa({0: 1.0}, ['a'], trans) == {1: 1.0}


def test_simulate_nfa_mapping_input():
    trans = {0: {'a': {1: 1.0}}}
    seq = {5: 'a'}
    assert simulate_nfa({0: 1.0}, seq, trans) == {1: 1.0}


def test_simulate_nfa_break():
    trans = {0: {'a': {1: 1.0}}}
    res = simulate_nfa({0: 1.0}, ['b', 'a'], trans)
    assert res == {}
