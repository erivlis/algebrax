from algebrax.matrix.core import (
    add,
    commutator,
    dot,
    element_wise_binary_op,
    hstack,
    inner,
    kronecker_delta,
    laplacian_matrix,
    mat_vec,
    subtract,
    trace,
    transpose,
    vec_mat,
    vstack,
)


def test_add():
    m1 = {0: {0: 1, 1: 2}}
    m2 = {0: {1: 3, 2: 4}, 1: {0: 5}}
    # 0,0: 1+0=1
    # 0,1: 2+3=5
    # 0,2: 0+4=4
    # 1,0: 0+5=5
    res = add(m1, m2)
    assert res == {0: {0: 1, 1: 5, 2: 4}, 1: {0: 5}}


def test_add_cancellation():
    m1 = {0: {0: 1}}
    m2 = {0: {0: -1}}
    # Result should be empty (0 is removed)
    assert add(m1, m2) == {}


def test_dot():
    # [1 2] . [5 6] = [1*5+2*7, 1*6+2*8] = [19, 22]
    # [3 4]   [7 8]   [3*5+4*7, 3*6+4*8]   [43, 50]
    m1 = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
    m2 = {0: {0: 5, 1: 6}, 1: {0: 7, 1: 8}}
    res = dot(m1, m2)
    assert res == {0: {0: 19, 1: 22}, 1: {0: 43, 1: 50}}


def test_dot_cancellation():
    # m1 = [1 1], m2 = [ 1 ]
    #                  [-1 ]
    # result = 1*1 + 1*(-1) = 0
    m1 = {0: {0: 1, 1: 1}}
    m2 = {0: {0: 1}, 1: {0: -1}}
    assert dot(m1, m2) == {}


def test_transpose():
    m = {0: {1: 2}, 2: {3: 4}}
    t = transpose(m)
    assert t == {1: {0: 2}, 3: {2: 4}}


def test_trace():
    m = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}, 2: {2: 5}}
    assert trace(m) == 1 + 4 + 5


def test_inner():
    v1 = {'a': 2, 'b': 3}
    v2 = {'b': 4, 'c': 5}
    # 2*0 + 3*4 + 0*5 = 12
    assert inner(v1, v2) == 12


def test_mat_vec():
    # [1 2] [1] = [1*1 + 2*2] = [5]
    # [3 4] [2]   [3*1 + 4*2]   [11]
    m = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
    v = {0: 1, 1: 2}
    res = mat_vec(m, v)
    assert res == {0: 5, 1: 11}


def test_mat_vec_cancellation():
    # [1 1] [ 1] = [1*1 + 1*(-1)] = [0]
    #       [-1]
    m = {0: {0: 1, 1: 1}}
    v = {0: 1, 1: -1}
    res = mat_vec(m, v)
    assert res == {}


def test_vec_mat():
    # [1 2] [1 2] = [1*1+2*3, 1*2+2*4] = [7, 10]
    #       [3 4]
    v = {0: 1, 1: 2}
    m = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
    res = vec_mat(v, m)
    assert res == {0: 7, 1: 10}


def test_vec_mat_cancellation():
    # v = [1, 1]
    # M = [ 1 ]
    #     [-1 ]
    # res = 1*1 + 1*(-1) = 0
    v = {0: 1, 1: 1}
    M = {0: {0: 1}, 1: {0: -1}}  # noqa: N806
    assert vec_mat(v, M) == {}


def test_kronecker():
    assert kronecker_delta(1, 1) == 1
    assert kronecker_delta(1, 2) == 0


def test_add_empty():
    assert add({}, {}) == {}


def test_add_empty_rows():
    m1 = {0: {}}
    m2 = {0: {}}
    assert add(m1, m2) == {}


def test_dot_empty():
    assert dot({}, {}) == {}


def test_dot_empty_rows():
    m1 = {0: {}}
    m2 = {0: {}}
    assert dot(m1, m2) == {}


def test_vec_mat_empty():
    assert vec_mat({}, {}) == {}


def test_power_zero():
    from algebrax.matrix.core import power

    assert power({0: {0: 2.0}}, 0) == {0: {0: 1.0}}


def test_matrix_core_branch_coverage():
    from algebrax.matrix.core import block, block_diag, mat_vec, slice_matrix, vec_mat
    from algebrax.semiring import TropicalSemiring

    assert mat_vec({0: {0: 2.0}}, {0: 1.0}, semiring=TropicalSemiring()) == {0: 3.0}
    assert vec_mat({0: 1.0}, {0: {0: 2.0}}, semiring=TropicalSemiring()) == {0: 3.0}
    assert vec_mat({0: 1.0}, {99: {0: 1.0}}) == {}
    assert slice_matrix({0: {1: 2}}, rows=[99], cols=[1]) == {}
    assert block({0: {10: 1.0}}, slice(0, 1), slice(0, 5)) == {}
    assert block_diag([{0: {}}]) == {0: {}}


def test_subtract():
    m1 = {0: {0: 5, 1: 3}, 1: {0: 2}}
    m2 = {0: {0: 2, 1: 3}, 1: {1: 4}}
    # 0,0: 5 - 2 = 3
    # 0,1: 3 - 3 = 0 (pruned)
    # 1,0: 2 - 0 = 2
    # 1,1: 0 - 4 = -4
    res = subtract(m1, m2)
    assert res == {0: {0: 3}, 1: {0: 2, 1: -4}}


def test_subtract_cancellation():
    m = {0: {0: 10, 1: -5}, 1: {2: 7}}
    assert subtract(m, m) == {}


def test_subtract_empty():
    assert subtract({}, {}) == {}
    assert subtract({0: {}}, {0: {}}) == {}


def test_element_wise_binary_op():
    import operator

    m1 = {0: {0: 3, 1: 4}}
    m2 = {0: {0: 2, 1: 0}}
    res = element_wise_binary_op(m1, m2, operator.mul)
    assert res == {0: {0: 6}}


def test_commutator():
    # Commuting matrices: [A, A] == {}
    a = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
    assert commutator(a, a) == {}

    # Diagonal matrices commute
    d1 = {0: {0: 2}, 1: {1: 5}}
    d2 = {0: {0: 3}, 1: {1: 7}}
    assert commutator(d1, d2) == {}

    # Non-commuting standard generators:
    # X = [[0, 1], [0, 0]], Y = [[0, 0], [1, 0]]
    # XY = [[1, 0], [0, 0]], YX = [[0, 0], [0, 1]]
    # [X, Y] = [[1, 0], [0, -1]]
    x = {0: {1: 1}}
    y = {1: {0: 1}}
    xy_comm = commutator(x, y)
    assert xy_comm == {0: {0: 1}, 1: {1: -1}}

    # Anti-symmetry: [Y, X] = -[X, Y] => [X, Y] + [Y, X] == {}
    yx_comm = commutator(y, x)
    assert yx_comm == {0: {0: -1}, 1: {1: 1}}
    assert add(xy_comm, yx_comm) == {}


def test_commutator_jacobi_identity():
    # Jacobi identity: [A, [B, C]] + [B, [C, A]] + [C, [A, B]] == 0
    a = {0: {1: 1}, 1: {0: 1}}  # sigma_x
    b = {0: {1: -1}, 1: {0: 1}}  # roughly i * sigma_y
    c = {0: {0: 1}, 1: {1: -1}}  # sigma_z

    term1 = commutator(a, commutator(b, c))
    term2 = commutator(b, commutator(c, a))
    term3 = commutator(c, commutator(a, b))

    jacobi_sum = add(add(term1, term2), term3)
    assert jacobi_sum == {}


def test_hstack_and_vstack():
    m1 = {0: {0: 1, 1: 2}}
    m2 = {0: {0: 3}, 1: {0: 4}}

    # hstack shifts column indices
    h = hstack([m1, m2])
    # m1 has columns 0, 1 -> max_c = 1 -> offset 2 for m2
    assert h[0] == {0: 1, 1: 2, 2: 3}
    assert h[1] == {2: 4}

    # vstack shifts row indices
    v = vstack([m1, m2])
    # m1 has row 0 -> max_r = 0 -> offset 1 for m2
    assert v[0] == {0: 1, 1: 2}
    assert v[1] == {0: 3}
    assert v[2] == {0: 4}

    # Empty inputs
    assert hstack([]) == {}
    assert vstack([]) == {}


def test_matrix_core_untested_branches():
    from algebrax.semiring import Semiring

    # 1. Semiring with zero is None to cover branch 223->225
    class ZeroNoneSemiring(Semiring[int]):
        zero = None
        one = 1

        def add(self, a: int, b: int) -> int:
            return a + b

        def mul(self, a: int, b: int) -> int:
            return a * b

    res = dot({0: {0: 2}}, {0: {0: 3}}, semiring=ZeroNoneSemiring())
    assert res == {0: {0: 6}}

    # 2. Laplacian symmetrize with canceling weights: avg_w == 0 (branch 316)
    canceling = {0: {1: 3.0}, 1: {0: -3.0}}
    lap_cancel = laplacian_matrix(canceling, symmetrize=True)
    assert lap_cancel == {}

    # 3. Laplacian normalized='sym' with isolated node (degrees[u] == 0 and val == 0)
    graph_isolated = {0: {1: 1.0}, 1: {0: 1.0}, 2: {}}
    lap_sym = laplacian_matrix(graph_isolated, normalized='sym')
    assert lap_sym[0][0] == 1.0
    assert lap_sym[1][1] == 1.0
    assert 2 not in lap_sym  # Isolated node has empty row and is pruned

    # 4. Laplacian normalized='rw' with isolated node (d == 0)
    lap_rw = laplacian_matrix(graph_isolated, normalized='rw')
    assert lap_rw[0][0] == 1.0
    assert lap_rw[1][1] == 1.0
    assert 2 not in lap_rw

    # 5. Asymmetric normalized='sym' with sink node (degree[v] == 0 -> val == 0)
    directed_sink = {0: {1: 1.0}, 1: {}}
    lap_directed_sym = laplacian_matrix(directed_sink, symmetrize=False, normalized='sym')
    assert lap_directed_sym[0] == {0: 1.0}
    assert 1 not in lap_directed_sym

