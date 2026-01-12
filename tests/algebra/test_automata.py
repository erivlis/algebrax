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

    assert simulate_dfa(0, "ab", trans) == 2
    assert simulate_dfa(0, "ac", trans) is None

def test_nfa():
    # 0 --a--> 0 (0.5)
    # 0 --a--> 1 (0.5)
    trans = {0: {'a': {0: 0.5, 1: 0.5}}}

    start = {0: 1.0}
    next_state = nfa_step(start, 'a', trans)
    assert next_state == {0: 0.5, 1: 0.5}

    # Simulate
    final = simulate_nfa(start, "a", trans)
    assert final == {0: 0.5, 1: 0.5}
