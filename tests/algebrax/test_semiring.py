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

    submodule_names = [
        'analysis',
        'automata',
        'category',
        'clifford',
        'converters',
        'display',
        'galois',
        'group',
        'homology',
        'lattice',
        'matrix',
        'metrics',
        'probability',
        'semiring',
        'tensor',
        'transforms',
        'trie',
        'verification',
    ]

    all_exported = set(algebrax.__all__)
    for sub in submodule_names:
        assert sub in all_exported, f"Submodule namespace '{sub}' is missing in algebrax.__all__"
        assert hasattr(algebrax, sub), f"Submodule namespace '{sub}' is not accessible on algebrax root"


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
        BivariateVarianceSemiring,
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

    bivar_s = BivariateVarianceSemiring()
    assert bivar_s.zero == (0.0, 0.0, 0.0, 0.0)
    assert bivar_s.one == (1.0, 0.0, 0.0, 0.0)
    assert bivar_s.add((1.0, 2.0, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0)) == (6.0, 8.0, 10.0, 12.0)
    assert bivar_s.mul((1.0, 2.0, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0))[0] == 5.0
    assert bivar_s.nsum((1.0, 2.0, 3.0, 4.0), 0) == (0.0, 0.0, 0.0, 0.0)
    assert bivar_s.nsum((1.0, 2.0, 3.0, 4.0), 2) == (2.0, 4.0, 6.0, 8.0)
    assert bivar_s.power((2.0, 1.0, 1.0, 1.0), 0) == (1.0, 0.0, 0.0, 0.0)
    assert bivar_s.power((2.0, 1.0, 1.0, 1.0), 2)[0] == 4.0
    with pytest.raises(NotImplementedError):
        bivar_s.star((1.0, 1.0, 1.0, 1.0))

    var_s = VarianceSemiring()
    assert var_s.order == 2
    assert var_s.zero == (0.0, 0.0, 0.0)
    assert var_s.one == (1.0, 0.0, 0.0)
    assert var_s.add((1.0, 2.0, 4.0), (3.0, 6.0, 12.0)) == (4.0, 8.0, 16.0)
    assert var_s.variance((1.0, 2.0, 5.0)) == pytest.approx(1.0)

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
    assert ProvenanceSemiring._combine_monomials(('a',), ('b',)) == ('a', 'b')


def test_skewness_semiring():
    from algebrax.semiring import SkewnessSemiring

    s = SkewnessSemiring()

    assert s.zero == (0.0, 0.0, 0.0, 0.0)
    assert s.one == (1.0, 0.0, 0.0, 0.0)

    # Edge 1: Prob 1.0, Value 2.0 -> (p=1, m1=2, m2=4, m3=8)
    e1 = (1.0, 2.0, 4.0, 8.0)
    # Edge 2: Prob 1.0, Value 3.0 -> (p=1, m1=3, m2=9, m3=27)
    e2 = (1.0, 3.0, 9.0, 27.0)

    # Sequential composition: Total value = 2 + 3 = 5
    # (p=1, m1=5, m2=25, m3=125)
    seq = s.mul(e1, e2)
    assert seq[0] == pytest.approx(1.0)
    assert seq[1] == pytest.approx(5.0)
    assert seq[2] == pytest.approx(25.0)
    assert seq[3] == pytest.approx(125.0)

    # Parallel branching: 50% chance of Edge 1, 50% chance of Edge 2
    b1 = (0.5, 0.5 * 2.0, 0.5 * 4.0, 0.5 * 8.0)
    b2 = (0.5, 0.5 * 3.0, 0.5 * 9.0, 0.5 * 27.0)
    par = s.add(b1, b2)
    assert par[0] == pytest.approx(1.0)
    assert par[1] == pytest.approx(2.5)  # E[X] = 0.5*2 + 0.5*3 = 2.5
    assert par[2] == pytest.approx(6.5)  # E[X^2] = 0.5*4 + 0.5*9 = 6.5
    assert par[3] == pytest.approx(17.5)  # E[X^3] = 0.5*8 + 0.5*27 = 17.5

    # Variance and Skewness via built-in decoders
    assert s.mean(par) == pytest.approx(2.5)
    assert s.variance(par) == pytest.approx(0.25)
    assert s.skewness(par) == pytest.approx(0.0)  # Symmetric distribution -> skewness is 0

    # Power and nsum
    pow3 = s.power(e1, 3)
    assert pow3[0] == pytest.approx(1.0)
    assert pow3[1] == pytest.approx(6.0)
    assert pow3[2] == pytest.approx(36.0)
    assert pow3[3] == pytest.approx(216.0)

    assert s.power(e1, 0) == s.one
    assert s.nsum(e1, 0) == s.zero
    assert s.nsum(e1, 3) == (3.0, 6.0, 12.0, 24.0)


def test_binomial_convolution_semiring_1d():
    from algebrax.semiring import BinomialConvolutionSemiring

    s1 = BinomialConvolutionSemiring(order=1)
    assert s1.zero == (0.0, 0.0)
    assert s1.one == (1.0, 0.0)
    assert s1.add((1.0, 2.0), (3.0, 4.0)) == (4.0, 6.0)
    # Leibniz rule: (u*v, u*v' + v*u') -> (2*3, 2*4 + 3*1) = (6, 11)
    assert s1.mul((2.0, 1.0), (3.0, 4.0)) == (6.0, 11.0)
    assert s1.power((2.0, 1.0), 3) == (8.0, 12.0)  # (x^3)' = 3*x^2 = 12

    # Star on prob 0.5, value 1.0
    p_star, v_star = s1.star((0.5, 1.0))
    assert p_star == pytest.approx(2.0)
    assert v_star == pytest.approx(4.0)

    # Order 0
    s0 = BinomialConvolutionSemiring(order=0)
    assert s0.zero == (0.0,)
    assert s0.one == (1.0,)
    assert s0.mul((2.0,), (3.0,)) == (6.0,)
    assert s0.star((0.5,)) == (2.0,)

    # Order 4 (Kurtosis)
    s4 = BinomialConvolutionSemiring(order=4)
    assert len(s4.zero) == 5
    assert len(s4.one) == 5
    # Value 2.0 deterministically: (1, 2, 4, 8, 16)
    v2 = (1.0, 2.0, 4.0, 8.0, 16.0)
    # Value 3.0 deterministically: (1, 3, 9, 27, 81)
    v3 = (1.0, 3.0, 9.0, 27.0, 81.0)
    # Sum: value 5.0 -> (1, 5, 25, 125, 625)
    v5 = s4.mul(v2, v3)
    assert v5[0] == pytest.approx(1.0)
    assert v5[1] == pytest.approx(5.0)
    assert v5[2] == pytest.approx(25.0)
    assert v5[3] == pytest.approx(125.0)
    assert v5[4] == pytest.approx(625.0)

    # Star for order > 1
    star4 = s4.star((0.5, 0.0, 0.0, 0.0, 0.0))
    assert star4[0] == pytest.approx(2.0)


def test_statistical_moment_semiring_and_decoders():
    import math

    from algebrax.semiring import KurtosisSemiring, StatisticalMomentSemiring, VarianceSemiring

    sem = StatisticalMomentSemiring(order=4)

    # Path 1: 50% chance, value 2.0
    p1 = (0.5, 0.5 * 2.0, 0.5 * 4.0, 0.5 * 8.0, 0.5 * 16.0)
    # Path 2: 50% chance, value 4.0
    p2 = (0.5, 0.5 * 4.0, 0.5 * 16.0, 0.5 * 64.0, 0.5 * 256.0)

    bundle = sem.add(p1, p2)
    assert sem.mean(bundle) == pytest.approx(3.0)
    assert sem.variance(bundle) == pytest.approx(1.0)  # Var = 0.5*4 + 0.5*16 - 9 = 10 - 9 = 1
    assert sem.skewness(bundle) == pytest.approx(0.0)  # Symmetric
    assert sem.kurtosis(bundle) == pytest.approx(1.0)  # mu4 = 1, Var^2 = 1 -> kurt = 1

    # Zero mass edge case
    z = sem.zero
    assert math.isnan(sem.mean(z))
    assert math.isnan(sem.skewness(z))
    assert math.isnan(sem.kurtosis(z))
    assert all(math.isnan(x) for x in sem.raw_moments(z))
    assert all(math.isnan(x) for x in sem.central_moments(z))

    # VarianceSemiring (order=2) and KurtosisSemiring (order=4) aliases
    vm = VarianceSemiring()
    assert vm.order == 2
    assert vm.variance(vm.add((0.5, 1.0, 2.0), (0.5, 2.0, 8.0))) == pytest.approx(1.0)

    ks = KurtosisSemiring()
    assert ks.order == 4


def test_multivariate_moment_semiring_and_covariance():
    from algebrax.semiring import MultivariateBinomialConvolutionSemiring, MultivariateMomentSemiring

    msem = MultivariateMomentSemiring(num_vars=2, order=2)
    assert msem.zero == {}
    assert msem.one == {(0, 0): 1.0}

    # Step 1: Feature 1 = 2.0, Feature 2 = 3.0
    # Representation in MGF: m_{(1,0)} = 2.0, m_{(0,1)} = 3.0, m_{(2,0)} = 4.0, m_{(0,2)} = 9.0, m_{(1,1)} = 6.0
    s1 = {(0, 0): 1.0, (1, 0): 2.0, (0, 1): 3.0, (2, 0): 4.0, (0, 2): 9.0, (1, 1): 6.0}

    # Step 2: Feature 1 = 1.0, Feature 2 = 5.0
    s2 = {(0, 0): 1.0, (1, 0): 1.0, (0, 1): 5.0, (2, 0): 1.0, (0, 2): 25.0, (1, 1): 5.0}

    # Sequence of two steps: Features add -> (3.0, 8.0)
    seq = msem.mul(s1, s2)
    assert seq[(0, 0)] == pytest.approx(1.0)
    assert seq[(1, 0)] == pytest.approx(3.0)  # 2 + 1
    assert seq[(0, 1)] == pytest.approx(8.0)  # 3 + 5
    assert seq[(2, 0)] == pytest.approx(9.0)  # 3^2
    assert seq[(0, 2)] == pytest.approx(64.0)  # 8^2
    assert seq[(1, 1)] == pytest.approx(24.0)  # 3 * 8

    means = msem.mean_vector(seq)
    assert means[0] == pytest.approx(3.0)
    assert means[1] == pytest.approx(8.0)

    # Covariance of deterministic path is 0
    cov = msem.covariance_matrix(seq)
    assert cov[0][0] == pytest.approx(0.0)
    assert cov[1][1] == pytest.approx(0.0)
    assert cov[0][1] == pytest.approx(0.0)
    assert cov[1][0] == pytest.approx(0.0)

    # Branching paths: Path A (1, 2) prob 0.5, Path B (3, 6) prob 0.5
    pa = {(0, 0): 0.5, (1, 0): 0.5 * 1.0, (0, 1): 0.5 * 2.0, (2, 0): 0.5 * 1.0, (0, 2): 0.5 * 4.0, (1, 1): 0.5 * 2.0}
    pb = {
        (0, 0): 0.5,
        (1, 0): 0.5 * 3.0,
        (0, 1): 0.5 * 6.0,
        (2, 0): 0.5 * 9.0,
        (0, 2): 0.5 * 36.0,
        (1, 1): 0.5 * 18.0,
    }

    bundle = msem.add(pa, pb)
    b_means = msem.mean_vector(bundle)
    assert b_means[0] == pytest.approx(2.0)
    assert b_means[1] == pytest.approx(4.0)

    b_cov = msem.covariance_matrix(bundle)
    assert b_cov[0][0] == pytest.approx(1.0)  # Var(X) = 0.5*1 + 0.5*9 - 4 = 5 - 4 = 1
    assert b_cov[1][1] == pytest.approx(4.0)  # Var(Y) = 0.5*4 + 0.5*36 - 16 = 20 - 16 = 4
    assert b_cov[0][1] == pytest.approx(2.0)  # Cov(X, Y) = 0.5*2 + 0.5*18 - 8 = 10 - 8 = 2
    assert b_cov[1][0] == pytest.approx(2.0)

    # Power and Star
    pow2 = msem.power(s1, 2)
    assert pow2[(1, 0)] == pytest.approx(4.0)

    star = msem.star({(0, 0): 0.5})
    assert star[(0, 0)] == pytest.approx(2.0)


def test_moment_semirings_validation_and_errors():
    from algebrax.semiring import (
        BinomialConvolutionSemiring,
        MultivariateBinomialConvolutionSemiring,
        MultivariateMomentSemiring,
    )

    with pytest.raises(ValueError, match='order must be a non-negative integer'):
        BinomialConvolutionSemiring(order=-1)

    with pytest.raises(ValueError, match='num_vars must be >= 1'):
        MultivariateBinomialConvolutionSemiring(num_vars=0)

    with pytest.raises(ValueError, match='order must be >= 0'):
        MultivariateBinomialConvolutionSemiring(num_vars=2, order=-1)

    # Covariance guard on order < 2
    m1 = MultivariateMomentSemiring(num_vars=2, order=1)
    with pytest.raises(ValueError, match='Covariance matrix calculation requires order >= 2'):
        m1.covariance_matrix({(0, 0): 1.0, (1, 0): 2.0})

    # Length checks in 1D
    b1 = BinomialConvolutionSemiring(order=1)
    with pytest.raises(ValueError, match='Operands must have length 2'):
        b1.add((1.0,), (1.0, 2.0))

    with pytest.raises(ValueError, match='Operands must have length 2'):
        b1.mul((1.0,), (1.0, 2.0))
