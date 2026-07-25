from algebrax.converters import (
    dense_to_sparse_matrix,
    dense_to_sparse_tensor,
    dense_to_sparse_vector,
    flat_to_nested,
    nested_to_flat,
    sample,
    sample_tensor,
    sparse_to_dense_matrix,
    sparse_to_dense_tensor,
    sparse_to_dense_vector,
)


def test_dense_to_sparse_vector():
    dense = [0, 1, 0, 2]
    sparse = dense_to_sparse_vector(dense)
    assert sparse == {1: 1, 3: 2}


def test_sparse_to_dense_vector():
    sparse = {1: 1, 3: 2}
    dense = sparse_to_dense_vector(sparse, size=4)
    assert dense == [0, 1, 0, 2]


def test_sparse_to_dense_vector_inferred_size():
    sparse = {1: 1, 3: 2}
    dense = sparse_to_dense_vector(sparse)
    assert dense == [0, 1, 0, 2]


def test_dense_to_sparse_matrix():
    dense = [[0, 1], [2, 0]]
    sparse = dense_to_sparse_matrix(dense)
    assert sparse == {0: {1: 1}, 1: {0: 2}}


def test_dense_to_sparse_matrix_all_defaults():
    # Row 1 is all zeros -> should be skipped in sparse result
    dense = [[0, 1], [0, 0]]
    sparse = dense_to_sparse_matrix(dense)
    assert sparse == {0: {1: 1}}


def test_sparse_to_dense_matrix():
    sparse = {0: {1: 1}, 1: {0: 2}}
    dense = sparse_to_dense_matrix(sparse, shape=(2, 2))
    assert dense == [[0, 1], [2, 0]]


def test_sparse_to_dense_matrix_inferred_shape():
    sparse = {0: {1: 1}, 1: {0: 2}}
    dense = sparse_to_dense_matrix(sparse)
    assert dense == [[0, 1], [2, 0]]


def test_converters_empty():
    assert dense_to_sparse_vector([]) == {}
    assert sparse_to_dense_vector({}) == []
    assert dense_to_sparse_matrix([]) == {}
    assert sparse_to_dense_matrix({}) == []


def test_sparse_to_dense_vector_out_of_bounds():
    # Key 5 is outside size 4 -> Ignored
    sparse = {1: 1, 5: 5}
    dense = sparse_to_dense_vector(sparse, size=4)
    assert dense == [0, 1, 0, 0]


def test_sparse_to_dense_matrix_empty_with_shape():
    # Empty matrix but explicit shape -> Returns zero matrix
    dense = sparse_to_dense_matrix({}, shape=(2, 2))
    assert dense == [[0, 0], [0, 0]]


def test_sparse_to_dense_matrix_empty_rows():
    # Matrix has rows, but some are empty/None
    # {0: {}, 1: {0: 1}}
    sparse = {0: {}, 1: {0: 1}}
    dense = sparse_to_dense_matrix(sparse)
    # Max row 1, max col 0 -> 2x1
    assert dense == [[0], [1]]


def test_sparse_to_dense_matrix_out_of_bounds():
    # Shape 1x1
    # 0: {0: 1} -> In bounds
    # 0: {5: 5} -> Col out of bounds
    # 5: {0: 5} -> Row out of bounds
    sparse = {0: {0: 1, 5: 5}, 5: {0: 5}}
    dense = sparse_to_dense_matrix(sparse, shape=(1, 1))
    # Only (0,0) fits
    assert dense == [[1]]


def test_dense_to_sparse_tensor():
    # 3D Tensor: 2x2x2
    # [ [[0, 1], [0, 0]], [[2, 0], [0, 3]] ]
    dense = [[[0, 1], [0, 0]], [[2, 0], [0, 3]]]
    sparse = dense_to_sparse_tensor(dense)
    # 0 -> 0 -> 1: 1
    # 1 -> 0 -> 0: 2
    # 1 -> 1 -> 1: 3
    expected = {0: {0: {1: 1}}, 1: {0: {0: 2}, 1: {1: 3}}}
    assert sparse == expected


def test_sparse_to_dense_tensor():
    sparse = {0: {0: {1: 1}}, 1: {0: {0: 2}, 1: {1: 3}}}
    # Inferred shape: (2, 2, 2)
    dense = sparse_to_dense_tensor(sparse)
    expected = [[[0, 1], [0, 0]], [[2, 0], [0, 3]]]
    assert dense == expected


def test_sparse_to_dense_tensor_explicit_shape():
    sparse = {0: {0: {0: 1}}}
    # Shape 1x1x2 -> [[1, 0]]
    dense = sparse_to_dense_tensor(sparse, shape=(1, 1, 2))
    assert dense == [[[1, 0]]]


def test_sparse_to_dense_tensor_1d():
    # 1D Tensor (Vector)
    sparse = {0: 1, 2: 3}
    # Inferred shape: (3,)
    dense = sparse_to_dense_tensor(sparse)
    assert dense == [1, 0, 3]


def test_sparse_to_dense_tensor_deep():
    # Force recursion in get_shape
    # 2D Tensor: {0: {0: 1}}
    sparse = {0: {0: 1}}
    # get_shape({0: {0: 1}}) -> calls get_shape({0: 1}) -> calls get_shape(1)
    dense = sparse_to_dense_tensor(sparse)
    assert dense == [[1]]


def test_sample():
    # f(x) = x^2
    # domain = [-1, 0, 1, 2]
    # default = 0
    # f(-1)=1, f(0)=0 (skip), f(1)=1, f(2)=4

    def func(x):
        return x**2

    domain = [-1, 0, 1, 2]
    sparse = sample(func, domain, default=0)

    assert sparse == {-1: 1, 1: 1, 2: 4}
    assert 0 not in sparse


def test_flat_to_nested():
    # {(0, 0): 1, (0, 1): 2, (1, 0): 3}
    flat = {(0, 0): 1, (0, 1): 2, (1, 0): 3}
    nested = flat_to_nested(flat)
    expected = {0: {0: 1, 1: 2}, 1: {0: 3}}
    assert nested == expected


def test_flat_to_nested_scalar_keys():
    # Test with scalar keys (depth 1)
    flat = {0: 1, 1: 2}
    nested = flat_to_nested(flat)
    assert nested == {0: 1, 1: 2}


def test_nested_to_flat():
    nested = {0: {0: 1, 1: 2}, 1: {0: 3}}
    flat = nested_to_flat(nested)
    expected = {(0, 0): 1, (0, 1): 2, (1, 0): 3}
    assert flat == expected


def test_sample_tensor():
    # f(x, y) = x + y
    # x in [0, 1], y in [0, 1]
    # (0,0)->0 (skip), (0,1)->1, (1,0)->1, (1,1)->2

    def func(p):
        return p[0] + p[1]

    ranges = [range(2), range(2)]

    tensor = sample_tensor(func, ranges, default=0)

    # Expected nested structure
    expected = {0: {1: 1}, 1: {0: 1, 1: 2}}
    assert tensor == expected


def test_dense_to_sparse_tensor_base_case():
    # Scalar input
    assert dense_to_sparse_tensor(5) == 5
    # String input (treated as scalar)
    assert dense_to_sparse_tensor('hello') == 'hello'


def test_flat_to_nested_conflict():
    # Conflict: (0,) -> 1 vs (0, 1) -> 2
    # 0 is both a leaf and a branch.
    # Our implementation overwrites the leaf with the branch (or vice versa depending on order).
    # Order is not guaranteed in dicts (though insertion order is preserved in modern Python).

    # Case 1: Leaf first
    flat = {(0,): 1, (0, 1): 2}
    # (0,) sets result[0] = 1.
    # (0, 1) sees result[0] is not dict. Overwrites with {}.
    # result[0][1] = 2.
    # Final: {0: {1: 2}}
    nested = flat_to_nested(flat)
    assert nested == {0: {1: 2}}

    # Case 2: Branch first
    flat2 = {(0, 1): 2, (0,): 1}
    # (0, 1) sets result[0] = {1: 2}.
    # (0,) sets result[0] = 1.
    # Final: {0: 1}
    nested2 = flat_to_nested(flat2)
    assert nested2 == {0: 1}
