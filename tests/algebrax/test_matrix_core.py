from algebrax.matrix.core import (
    add,
    dot,
    inner,
    kronecker_delta,
    mat_vec,
    trace,
    transpose,
    vec_mat,
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
    v1 = {"a": 2, "b": 3}
    v2 = {"b": 4, "c": 5}
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
