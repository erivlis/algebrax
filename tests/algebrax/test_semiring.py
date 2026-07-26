import math

import pytest

from algebrax.matrix.core import dot, power
from algebrax.semiring import (
    BooleanSemiring,
    BottleneckSemiring,
    KnotSemiring,
    LogSemiring,
    MonoidAlgebraSemiring,
    PolynomialSemiring,
    ProvenanceSemiring,
    ReliabilitySemiring,
    StandardSemiring,
    StringSemiring,
    TropicalSemiring,
)


def test_tropical_shortest_path():
    # Graph: 0 -> 1 (weight 1), 1 -> 2 (weight 2), 0 -> 2 (weight 10)
    # Shortest path 0->2 is 0->1->2 (cost 1+2=3). Direct is 10.

    # Adjacency matrix (weights)
    # Missing edge = infinity
    adj = {0: {1: 1.0, 2: 10.0}, 1: {2: 2.0}, 2: {}}

    # Tropical Semiring: (min, +)
    # A^2 gives shortest path of length exactly 2 (or <= 2 if we add I?)
    # Standard power gives length exactly k.

    semiring = TropicalSemiring()

    # Step 1: A^1 = adj

    # Step 2: A^2 = A . A
    # (0, 2) = min( (0,0)+(0,2), (0,1)+(1,2), (0,2)+(2,2) )
    #        = min( inf+10, 1+2, 10+inf ) = 3.

    adj2 = dot(adj, adj, semiring=semiring)
    assert adj2[0][2] == pytest.approx(3.0)

    # Step 3: Power
    # Shortest path with exactly 2 edges
    adj_pow2 = power(adj, 2, semiring=semiring)
    assert adj_pow2[0][2] == pytest.approx(3.0)


def test_boolean_reachability():
    # Graph: 0 -> 1 -> 2
    # 0 can reach 2?

    adj = {0: {1: True}, 1: {2: True}, 2: {}}

    semiring = BooleanSemiring()

    # Reachability in exactly 2 steps
    reach2 = power(adj, 2, semiring=semiring)
    assert reach2[0][2] is True

    # Can't reach 1 in exactly 2 steps (unless loop)
    # Sparse matrix: missing key means False (zero)
    assert reach2[0].get(1, False) is False

    # Transitive closure usually involves (I + A)^N
    # Let's manually add I
    identity_matrix = {0: {0: True}, 1: {1: True}, 2: {2: True}}

    # Manual union of A and I (element-wise OR)
    adj_plus_identity = {}
    keys = set(adj.keys()) | set(identity_matrix.keys())
    for k in keys:
        row_a = adj.get(k, {})
        row_i = identity_matrix.get(k, {})
        # Union of rows
        new_row = row_a.copy()
        new_row.update(row_i)
        adj_plus_identity[k] = new_row

    # (I+A)^2 covers paths of length 0, 1, 2
    reach_all = power(adj_plus_identity, 2, semiring=semiring)
    assert reach_all[0][2] is True
    assert reach_all[0][1] is True
    assert reach_all[0][0] is True


def test_bottleneck_capacity():
    # Graph: 0 -> 1 (cap 10), 1 -> 2 (cap 5)
    # Path capacity = min(10, 5) = 5.
    # Max capacity path = max over all paths.

    adj = {0: {1: 10.0}, 1: {2: 5.0}, 2: {}}

    semiring = BottleneckSemiring()

    # Capacity of path length 2
    # (0, 2) = max( min(10, 5) ) = 5
    res = power(adj, 2, semiring=semiring)
    assert res[0][2] == pytest.approx(5.0)


def test_log_semiring():
    # Probabilities: 0->1 (0.5), 1->2 (0.5)
    # Path prob = 0.25.
    # Log probs: log(0.5) approx -0.693
    # Path log prob = -0.693 + -0.693 = -1.386

    lp = math.log(0.5)
    adj = {0: {1: lp}, 1: {2: lp}, 2: {}}

    semiring = LogSemiring()

    res = power(adj, 2, semiring=semiring)
    assert res[0][2] == pytest.approx(2 * lp)

    # Addition in LogSemiring is logaddexp
    # log(exp(a) + exp(b))
    # If we have two paths 0->2 with log probs a and b
    # Total prob = exp(a) + exp(b)
    # Total log prob = log(exp(a) + exp(b))

    # Graph: 0->1 (p=0.5), 0->2 (p=0.1)
    #        1->3 (p=0.5), 2->3 (p=0.5)
    # Path 1: 0->1->3 (p=0.25)
    # Path 2: 0->2->3 (p=0.05)
    # Total p = 0.30. Log(0.30) approx -1.204

    lp1 = math.log(0.5)
    lp2 = math.log(0.1)

    adj_multi = {0: {1: lp1, 2: lp2}, 1: {3: lp1}, 2: {3: lp1}, 3: {}}

    res_multi = power(adj_multi, 2, semiring=semiring)
    expected = math.log(0.25 + 0.05)
    assert res_multi[0][3] == pytest.approx(expected)


def test_log_semiring_edge_cases():
    semiring = LogSemiring()
    neg_inf = float('-inf')

    # add(-inf, x) = x
    assert semiring.add(neg_inf, 5.0) == pytest.approx(5.0)
    assert semiring.add(5.0, neg_inf) == pytest.approx(5.0)
    assert semiring.add(neg_inf, neg_inf) == neg_inf


def test_string_semiring():
    # Graph: 0 -a-> 1 -b-> 2
    #        0 -c-> 1
    # Paths 0->2: "ab", "cb"

    adj = {0: {1: {'a', 'c'}}, 1: {2: {'b'}}, 2: {}}

    semiring = StringSemiring()

    res = power(adj, 2, semiring=semiring)
    assert res[0][2] == {'ab', 'cb'}


def test_string_semiring_empty():
    semiring = StringSemiring()
    # mul(empty, x) = empty
    assert semiring.mul(set(), {'a'}) == set()
    assert semiring.mul({'a'}, set()) == set()


def test_reliability_semiring():
    # Same as Viterbi
    semiring = ReliabilitySemiring()
    assert semiring.add(0.5, 0.8) == pytest.approx(0.8)  # max
    assert semiring.mul(0.5, 0.5) == pytest.approx(0.25)  # mul
    assert semiring.zero == pytest.approx(0.0)
    assert semiring.one == pytest.approx(1.0)


def test_polynomial_semiring():
    poly_semiring = PolynomialSemiring(StandardSemiring[int]())

    # P1(x) = 1 + 2x  -> {0: 1, 1: 2}
    # P2(x) = 3 + 4x  -> {0: 3, 1: 4}
    # Addition: 4 + 6x -> {0: 4, 1: 6}
    # Multiplication: (1+2x)(3+4x) = 3 + 10x + 8x^2 -> {0: 3, 1: 10, 2: 8}
    p1 = {0: 1, 1: 2}
    p2 = {0: 3, 1: 4}

    assert poly_semiring.add(p1, p2) == {0: 4, 1: 6}
    assert poly_semiring.mul(p1, p2) == {0: 3, 1: 10, 2: 8}
    assert poly_semiring.zero == {}
    assert poly_semiring.one == {0: 1}

    # Generalized MonoidAlgebraSemiring over custom string key_op
    poly_str = MonoidAlgebraSemiring(StandardSemiring[int](), key_op=lambda a, b: a + b, zero_key='')
    assert poly_str.mul({'a': 2}, {'b': 3}) == {'ab': 6}
    assert poly_str.one == {'': 1}


def test_knot_semiring():
    knot_semiring = KnotSemiring(StandardSemiring[int]())

    # K1 = 2 * '3_1' + 'U'
    # K2 = '4_1'
    # Connected sum K1 # K2 = 2 * '3_1#4_1' + '4_1'
    k1 = {'3_1': 2, 'U': 1}
    k2 = {'4_1': 1}

    res_mul = knot_semiring.mul(k1, k2)
    assert res_mul == {'3_1#4_1': 2, '4_1': 1}

    res_add = knot_semiring.add(k1, k2)
    assert res_add == {'3_1': 2, 'U': 1, '4_1': 1}
    assert knot_semiring.zero == {}
    assert knot_semiring.one == {'U': 1}


def test_provenance_semiring():
    prov = ProvenanceSemiring()

    # Expression 1: 2*x*y + z -> {('x', 'y'): 2, ('z',): 1}
    # Expression 2: 3*w       -> {('w',): 3}
    # Multiplication: (2xy + z) * 3w = 6wxyz + 3wz -> {('w', 'x', 'y'): 6, ('w', 'z'): 3}
    e1 = {('x', 'y'): 2, ('z',): 1}
    e2 = {('w',): 3}

    res_mul = prov.mul(e1, e2)
    assert res_mul == {('w', 'x', 'y'): 6, ('w', 'z'): 3}
    assert prov.zero == {}
    assert prov.one == {(): 1}


def test_monoid_algebra_nsum():
    poly = PolynomialSemiring(StandardSemiring[int]())
    p = {0: 1, 1: 2}
    assert poly.nsum(p, 0) == {}
    assert poly.nsum(p, 3) == {0: 3, 1: 6}


def test_top_level_reexports_completeness():
    import algebrax
    import algebrax.analysis
    import algebrax.automata
    import algebrax.converters
    import algebrax.group
    import algebrax.matrix
    import algebrax.metrics
    import algebrax.semiring
    import algebrax.transforms
    import algebrax.trie
    import algebrax.typing

    submodules = [
        algebrax.analysis,
        algebrax.automata,
        algebrax.converters,
        algebrax.group,
        algebrax.matrix,
        algebrax.metrics,
        algebrax.semiring,
        algebrax.transforms,
        algebrax.trie,
        algebrax.typing,
    ]

    all_exported = set(algebrax.__all__)
    for mod in submodules:
        if hasattr(mod, '__all__'):
            for symbol in mod.__all__:
                if mod is algebrax.typing and (len(symbol) == 1 or symbol == 'T_num'):
                    continue
                assert symbol in all_exported, f"Symbol '{symbol}' from {mod.__name__} is missing in algebrax.__all__"


def test_semiring_protocol_default_implementations():
    from algebrax.semiring import Semiring

    class DummySemiring(Semiring[int]):
        @property
        def zero(self) -> int:
            return 0

        @property
        def one(self) -> int:
            return 1

        def add(self, a: int, b: int) -> int:
            return a + b

        def mul(self, a: int, b: int) -> int:
            return a * b

    s = DummySemiring()
    with pytest.raises(ValueError, match='nsum requires non-negative n'):
        s.nsum(5, -1)
    assert s.nsum(5, 0) == 0
    assert s.nsum(5, 1) == 5
    assert s.nsum(3, 4) == 12

    with pytest.raises(ValueError, match='power requires non-negative n'):
        s.power(5, -1)
    assert s.power(5, 0) == 1
    assert s.power(5, 1) == 5
    assert s.power(2, 4) == 16


def test_standard_semiring_methods():
    s_int = StandardSemiring(int)
    assert s_int.nsum(5, 0) == 0
    assert s_int.nsum(5, 3) == 15
    assert s_int.nsum(5, -2) == -10
    assert s_int.power(3, 2) == 9
    assert s_int.star(0) == 1
    with pytest.raises(ValueError):
        s_int.star(1)

    s_float = StandardSemiring(float)
    assert s_float.star(0.5) == pytest.approx(2.0)
    assert s_float.star(1.5) == float('inf')


def test_tropical_semiring_methods():
    s = TropicalSemiring()
    with pytest.raises(ValueError):
        s.nsum(5.0, -1)
    assert s.nsum(5.0, 0) == float('inf')
    assert s.nsum(5.0, 3) == 5.0
    assert s.power(2.0, 4) == 8.0
    assert s.star(-1.0) == float('-inf')
    assert s.star(1.0) == 0.0


def test_arctic_semiring_methods():
    from algebrax.semiring import ArcticSemiring

    s = ArcticSemiring()
    with pytest.raises(ValueError):
        s.nsum(5.0, -1)
    assert s.nsum(5.0, 0) == float('-inf')
    assert s.nsum(5.0, 3) == 5.0
    assert s.power(2.0, 4) == 8.0
    assert s.star(1.0) == float('inf')
    assert s.star(-1.0) == 0.0


def test_viterbi_semiring_methods():
    from algebrax.semiring import ViterbiSemiring

    s = ViterbiSemiring()
    with pytest.raises(ValueError):
        s.nsum(0.5, -1)
    assert s.nsum(0.5, 0) == 0.0
    assert s.nsum(0.5, 3) == 0.5
    assert s.power(0.5, 3) == pytest.approx(0.125)
    assert s.star(0.5) == 1.0


def test_all_specialized_semirings_coverage():
    from algebrax.semiring import (
        ArcticSemiring,
        DigitalSemiring,
        DualNumberSemiring,
        ExpectationSemiring,
        KCollapsedSemiring,
        LukasiewiczSemiring,
        MinTimesSemiring,
        VarianceSemiring,
    )

    log_s = LogSemiring()
    assert log_s.zero == float('-inf')
    assert log_s.one == 0.0
    assert log_s.add(0.0, 0.0) > 0.0
    assert log_s.mul(2.0, 3.0) == 5.0
    with pytest.raises(ValueError):
        log_s.nsum(1.0, -1)
    assert log_s.nsum(1.0, 0) == float('-inf')
    assert log_s.nsum(float('-inf'), 2) == float('-inf')
    assert log_s.nsum(1.0, 2) > 1.0
    assert log_s.power(2.0, 3) == 6.0
    assert log_s.star(1.0) == float('inf')
    assert log_s.star(-1.0) == pytest.approx(-math.log1p(-math.exp(-1.0)))

    b_s = BooleanSemiring()
    assert b_s.zero is False
    assert b_s.one is True
    assert b_s.add(True, False) is True
    assert b_s.mul(True, False) is False
    with pytest.raises(ValueError):
        b_s.nsum(True, -1)
    assert b_s.nsum(True, 0) is False
    assert b_s.nsum(True, 2) is True
    assert b_s.power(True, 0) is True
    assert b_s.power(True, 2) is True
    assert b_s.star(False) is True

    bot_s = BottleneckSemiring()
    assert bot_s.zero == float('-inf')
    assert bot_s.one == float('inf')
    assert bot_s.add(3.0, 5.0) == 5.0
    assert bot_s.mul(3.0, 5.0) == 3.0
    with pytest.raises(ValueError):
        bot_s.nsum(3.0, -1)
    assert bot_s.nsum(3.0, 0) == float('-inf')
    assert bot_s.nsum(3.0, 2) == 3.0
    assert bot_s.power(3.0, 0) == float('inf')
    assert bot_s.power(3.0, 2) == 3.0
    assert bot_s.star(3.0) == float('inf')

    dig_s = DigitalSemiring()
    assert dig_s.zero == 0
    assert dig_s.one == float('inf')
    assert dig_s.add(12, 34) == 34
    assert dig_s.add(34, 12) == 34
    assert dig_s.add(12, 21) == 21
    assert dig_s.add(float('inf'), 12) == float('inf')
    assert dig_s.mul(12, 34) == 12
    assert dig_s.mul(34, 12) == 12
    assert dig_s.mul(12, 21) == 12
    assert dig_s.mul(float('inf'), 12) == 12
    assert dig_s.nsum(5, 0) == 0
    assert dig_s.nsum(5, 2) == 5
    assert dig_s.power(5, 0) == float('inf')
    assert dig_s.power(5, 1) == 5
    assert dig_s.power(5, 2) == 5
    with pytest.raises(NotImplementedError):
        dig_s.star(5)

    str_s = StringSemiring()
    assert str_s.zero == set()
    assert str_s.one == {''}
    assert str_s.add({'a'}, {'b'}) == {'a', 'b'}
    assert str_s.mul({'a'}, {'b'}) == {'ab'}
    with pytest.raises(ValueError):
        str_s.nsum({'a'}, -1)
    assert str_s.nsum({'a'}, 0) == set()
    assert str_s.nsum({'a'}, 2) == {'a'}
    assert str_s.power({'a'}, 0) == {''}
    assert str_s.power({'a'}, 1) == {'a'}
    assert str_s.power({'a'}, 2) == {'aa'}
    with pytest.raises(NotImplementedError):
        str_s.star({'a'})

    dual_s = DualNumberSemiring()
    assert dual_s.zero == (0.0, 0.0)
    assert dual_s.one == (1.0, 0.0)
    assert dual_s.add((1.0, 2.0), (3.0, 4.0)) == (4.0, 6.0)
    assert dual_s.mul((1.0, 2.0), (3.0, 4.0)) == (3.0, 10.0)
    assert dual_s.nsum((1.0, 2.0), -1) == (-1.0, -2.0)
    assert dual_s.nsum((1.0, 2.0), 0) == (0.0, 0.0)
    assert dual_s.nsum((1.0, 2.0), 2) == (2.0, 4.0)
    assert dual_s.power((2.0, 3.0), 2) == (4.0, 12.0)
    assert dual_s.star((0.5, 1.0)) == (2.0, 4.0)

    exp_s = ExpectationSemiring()
    assert exp_s.zero == (0.0, 0.0)
    assert exp_s.one == (1.0, 0.0)
    assert exp_s.add((1.0, 2.0), (3.0, 4.0)) == (4.0, 6.0)
    assert exp_s.mul((2.0, 3.0), (4.0, 5.0)) == (8.0, 22.0)
    assert exp_s.nsum((1.0, 2.0), 0) == (0.0, 0.0)
    assert exp_s.nsum((1.0, 2.0), 3) == (3.0, 6.0)
    assert exp_s.power((2.0, 3.0), 0) == (1.0, 0.0)
    assert exp_s.power((2.0, 3.0), 2) == (4.0, 12.0)
    assert exp_s.star((0.5, 1.0)) == (2.0, 4.0)
    assert exp_s.star((1.5, 1.0)) == (float('inf'), float('inf'))

    var_s = VarianceSemiring()
    assert var_s.zero == (0.0, 0.0, 0.0, 0.0)
    assert var_s.one == (1.0, 0.0, 0.0, 0.0)
    assert var_s.add((1.0, 2.0, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0)) == (6.0, 8.0, 10.0, 12.0)
    assert var_s.mul((1.0, 2.0, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0))[0] == 5.0
    assert var_s.nsum((1.0, 2.0, 3.0, 4.0), 0) == (0.0, 0.0, 0.0, 0.0)
    assert var_s.nsum((1.0, 2.0, 3.0, 4.0), 2) == (2.0, 4.0, 6.0, 8.0)
    assert var_s.power((2.0, 1.0, 1.0, 1.0), 0) == (1.0, 0.0, 0.0, 0.0)
    assert var_s.power((2.0, 1.0, 1.0, 1.0), 2)[0] == 4.0
    with pytest.raises(NotImplementedError):
        var_s.star((1.0, 1.0, 1.0, 1.0))

    luk_s = LukasiewiczSemiring()
    assert luk_s.zero == 0.0
    assert luk_s.one == 1.0
    assert luk_s.add(0.4, 0.7) == 0.7
    assert luk_s.mul(0.6, 0.7) == pytest.approx(0.3)
    with pytest.raises(ValueError):
        luk_s.nsum(0.5, -1)
    assert luk_s.nsum(0.5, 0) == 0.0
    assert luk_s.nsum(0.5, 2) == 0.5
    assert luk_s.power(0.5, 0) == 1.0
    assert luk_s.power(0.5, 2) == 0.0
    assert luk_s.star(0.5) == 1.0

    mt_s = MinTimesSemiring()
    assert mt_s.zero == float('inf')
    assert mt_s.one == 1.0
    assert mt_s.add(3.0, 5.0) == 3.0
    assert mt_s.mul(3.0, 5.0) == 15.0
    with pytest.raises(ValueError):
        mt_s.nsum(3.0, -1)
    assert mt_s.nsum(3.0, 0) == float('inf')
    assert mt_s.nsum(3.0, 2) == 3.0
    assert mt_s.power(3.0, 2) == 9.0
    assert mt_s.star(0.5) == 0.0
    assert mt_s.star(1.5) == 1.0

    k_s = KCollapsedSemiring(k=5)
    assert k_s.zero == 0
    assert k_s.one == 1
    assert k_s.add(3, 4) == 5
    assert k_s.mul(2, 3) == 5
    with pytest.raises(ValueError):
        k_s.nsum(2, -1)
    assert k_s.nsum(2, 0) == 0
    assert k_s.nsum(2, 3) == 5
    assert k_s.power(2, 0) == 1
    assert k_s.power(2, 3) == 5
    assert k_s.star(0) == 1
    assert k_s.star(2) == 5

    mon_s = MonoidAlgebraSemiring(StandardSemiring(int))
    with pytest.raises(NotImplementedError):
        mon_s.star({})
    a = {'x': 5}
    b = {'x': -5}
    assert mon_s.add(a, b) == {}
    assert mon_s.mul(a, {'y': 0}) == {}


def test_semiring_edge_branches():
    from algebrax.semiring import ArcticSemiring, DigitalSemiring, KnotSemiring

    assert ArcticSemiring().nsum(5.0, 3) == 5.0
    assert DigitalSemiring._digit_sum(0) == 0

    knot = KnotSemiring(StandardSemiring[int]())
    assert knot._combine_knots('U', 'U') == 'U'
    assert knot._combine_knots('U', '3_1') == '3_1'
    assert knot._combine_knots('3_1', 'U') == '3_1'


def test_semiring_branch_coverage():
    from algebrax.semiring import ArcticSemiring, PolynomialSemiring, ProvenanceSemiring, StandardSemiring

    assert ArcticSemiring().one == 0.0
    poly = PolynomialSemiring(StandardSemiring(int))
    assert poly.nsum({0: 0}, 2) == {}

    prov = ProvenanceSemiring()
    assert prov.mul({}, {('x',): 1}) == {}
    assert prov.mul({('x',): 1}, {}) == {}
    assert prov.mul({('x',): 1}, {('x',): 0}) == {}
    assert ProvenanceSemiring._combine_monomials(('a',), ('b',)) == ('a', 'b')
