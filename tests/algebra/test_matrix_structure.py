from algebrax.matrix.core import (
    block,
    block_diag,
    hstack,
    slice_matrix,
    vstack,
)


def test_block():
    # 0 1 2
    # 3 4 5
    # 6 7 8
    m = {
        0: {0: 0, 1: 1, 2: 2},
        1: {0: 3, 1: 4, 2: 5},
        2: {0: 6, 1: 7, 2: 8},
    }

    # Extract center block (1,1) -> 4
    # rows=1:2, cols=1:2
    b = block(m, rows=slice(1, 2), cols=slice(1, 2))
    assert b == {0: {0: 4}}

    # Extract top-left 2x2
    # 0 1
    # 3 4
    b2 = block(m, rows=range(2), cols=range(2))
    assert b2 == {0: {0: 0, 1: 1}, 1: {0: 3, 1: 4}}

    # Extract with step
    # rows=0:3:2 (0, 2), cols=0:3:2 (0, 2)
    # 0 2
    # 6 8
    b3 = block(m, rows=slice(0, 3, 2), cols=slice(0, 3, 2))
    assert b3 == {0: {0: 0, 1: 2}, 1: {0: 6, 1: 8}}


def test_slice_matrix():
    # 0 1
    # 2 3
    m = {0: {0: 0, 1: 1}, 1: {0: 2, 1: 3}}

    # Keep row 1, col 0 -> {1: {0: 2}}
    # Indices are NOT rebased
    s = slice_matrix(m, rows=[1], cols=[0])
    assert s == {1: {0: 2}}


def test_slice_matrix_empty_intersection():
    # Row 0 exists, but col 5 does not.
    # Result should be empty (row 0 is skipped because new_row is empty)
    m = {0: {0: 1}}
    s = slice_matrix(m, rows=[0], cols=[5])
    assert s == {}


def test_hstack():
    # [1]  [2] -> [1 2]
    m1 = {0: {0: 1}}
    m2 = {0: {0: 2}}

    h = hstack([m1, m2])
    # m1 is col 0. m2 starts at col 1.
    assert h == {0: {0: 1, 1: 2}}

    # Empty inputs
    assert hstack([]) == {}
    assert hstack([{}, {}]) == {}


def test_vstack():
    # [1]
    # [2] -> [1]
    #        [2]
    m1 = {0: {0: 1}}
    m2 = {0: {0: 2}}

    v = vstack([m1, m2])
    # m1 is row 0. m2 starts at row 1.
    assert v == {0: {0: 1}, 1: {0: 2}}


def test_vstack_empty_input():
    # [1]
    # []  -> [1]
    # [2]    [2]
    m1 = {0: {0: 1}}
    m2 = {0: {0: 2}}
    v = vstack([m1, {}, m2])
    # m1 is row 0. Empty skipped. m2 starts at row 1.
    assert v == {0: {0: 1}, 1: {0: 2}}


def test_block_diag():
    # [1] (+) [2] -> [1 0]
    #                [0 2]
    m1 = {0: {0: 1}}
    m2 = {0: {0: 2}}

    b = block_diag([m1, m2])
    assert b == {0: {0: 1}, 1: {1: 2}}

    # 2x2 (+) 1x1
    # 1 1   0
    # 1 1   0
    # 0 0   2
    m3 = {0: {0: 1, 1: 1}, 1: {0: 1, 1: 1}}
    m4 = {0: {0: 2}}

    b2 = block_diag([m3, m4])
    # m3 is 0..1, 0..1
    # m4 starts at row 2, col 2
    assert b2[0] == {0: 1, 1: 1}
    assert b2[1] == {0: 1, 1: 1}
    assert b2[2] == {2: 2}


def test_block_diag_empty_input():
    # [1] (+) [] (+) [2] -> [1 0]
    #                       [0 2]
    m1 = {0: {0: 1}}
    m2 = {0: {0: 2}}
    b = block_diag([m1, {}, m2])
    assert b == {0: {0: 1}, 1: {1: 2}}
