import pytest

from algebrax.group import compose, invert, signature


def test_compose():
    # f(x) = x+1 (mod 3)
    # g(x) = 2x (mod 3)
    # f: {0:1, 1:2, 2:0}
    # g: {0:0, 1:2, 2:1}
    # g(f(0)) = g(1) = 2
    # g(f(1)) = g(2) = 1
    # g(f(2)) = g(0) = 0
    f = {0: 1, 1: 2, 2: 0}
    g = {0: 0, 1: 2, 2: 1}
    h = compose(f, g)
    assert h == {0: 2, 1: 1, 2: 0}

def test_invert():
    f = {0: 1, 1: 2, 2: 0}
    inv = invert(f)
    assert inv == {1: 0, 2: 1, 0: 2}

def test_signature():
    # Identity: (0)(1)(2) -> 3 cycles. N=3. 3-3=0 even.
    assert signature({0: 0, 1: 1, 2: 2}) == 1

    # Swap (0 1): (0 1)(2) -> 2 cycles. N=3. 3-2=1 odd.
    assert signature({0: 1, 1: 0, 2: 2}) == -1

    # Cycle (0 1 2): (0 1 2) -> 1 cycle. N=3. 3-1=2 even.
    assert signature({0: 1, 1: 2, 2: 0}) == 1

def test_signature_broken():
    # Not a permutation (0->1, 1->None)
    with pytest.raises(ValueError):
        signature({0: 1})
