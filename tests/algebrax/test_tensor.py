import pytest

from algebrax.semiring import StandardSemiring, TropicalSemiring
from algebrax.tensor import (
    einsum,
    flatten_tensor,
    outer_product,
    tensordot,
    unflatten_tensor,
    unpermute_tensor,
)
from algebrax.transforms import permute_tensor
from algebrax.trie import AlgebraicTrie


def test_einsum_matrix_mul():
    # Matrix A: 2x2, Matrix B: 2x2
    a = AlgebraicTrie()
    a[(0, 0)] = 1.0
    a[(0, 1)] = 2.0
    a[(1, 0)] = 3.0
    a[(1, 1)] = 4.0

    b = AlgebraicTrie()
    b[(0, 0)] = 2.0
    b[(0, 1)] = 0.0
    b[(1, 0)] = 1.0
    b[(1, 1)] = 2.0

    # C = A * B
    c = einsum('ij,jk->ik', a, b)
    assert c[(0, 0)] == 4.0  # 1*2 + 2*1 = 4
    assert c[(0, 1)] == 4.0  # 1*0 + 2*2 = 4
    assert c[(1, 0)] == 10.0  # 3*2 + 4*1 = 10
    assert c[(1, 1)] == 8.0  # 3*0 + 4*2 = 8

    # Implicit output notation "ij,jk" -> "ik"
    c_implicit = einsum('ij,jk', a, b)
    assert c_implicit[(0, 0)] == 4.0


def test_einsum_tropical():
    # Tropical semiring max-plus matrix multiplication
    a = AlgebraicTrie(semiring=TropicalSemiring)
    a[(0, 0)] = 1.0
    a[(0, 1)] = 5.0
    a[(1, 0)] = 3.0

    b = AlgebraicTrie(semiring=TropicalSemiring)
    b[(0, 0)] = 2.0
    b[(1, 0)] = 4.0

    c = einsum('ij,jk->ik', a, b, semiring=TropicalSemiring())
    # Tropical mul is +, add is min: min(1+2, 5+4) = min(3, 9) = 3
    assert c[(0, 0)] == 3.0

    # Test plain dict with explicit semiring
    dict_a = {(0, 0): 1.0, (0, 1): 5.0}
    dict_b = {(0, 0): 2.0, (1, 0): 4.0}
    res_dict = einsum('ij,jk->ik', dict_a, dict_b, semiring=TropicalSemiring())
    assert res_dict[(0, 0)] == 3.0


def test_einsum_dot_and_trace():
    # Vector dot product
    v1 = {(0,): 3.0, (1,): 4.0}
    v2 = {(0,): 2.0, (1,): 5.0}
    res = einsum('i,i->', v1, v2)
    assert res[()] == 26.0  # 3*2 + 4*5 = 26

    # Matrix trace
    mat = {(0, 0): 10.0, (1, 1): 20.0, (0, 1): 5.0}
    trace_res = einsum('ii->', mat)
    assert trace_res[()] == 30.0


def test_outer_product():
    v1 = AlgebraicTrie()
    v1[(0,)] = 2.0
    v1[(1,)] = 3.0

    v2 = AlgebraicTrie()
    v2[(0,)] = 4.0
    v2[(1,)] = 5.0

    out = outer_product(v1, v2)
    assert out[(0, 0)] == 8.0
    assert out[(0, 1)] == 10.0
    assert out[(1, 0)] == 12.0
    assert out[(1, 1)] == 15.0

    # Test plain dicts with scalar key non-tuples
    dict_v1 = {0: 2.0, 1: 3.0}
    dict_v2 = {0: 4.0, 1: 5.0}
    out_dict = outer_product(dict_v1, dict_v2, semiring=StandardSemiring())
    assert out_dict[(0, 0)] == 8.0


def test_tensordot():
    a = {(0, 0): 1.0, (0, 1): 2.0}
    b = {(0, 0): 3.0, (1, 0): 4.0}

    # Contract last axis of A (axis 1) with first axis of B (axis 0)
    c = tensordot(a, b, axes=1)
    assert c[(0, 0)] == 11.0  # 1*3 + 2*4 = 11

    # Contract using explicit axis lists tuple ([1], [0]) and explicit semiring
    c_explicit = tensordot(a, b, axes=([1], [0]), semiring=StandardSemiring())
    assert c_explicit[(0, 0)] == 11.0

    # Tensordot with AlgebraicTrie
    t_a = AlgebraicTrie()
    t_a[(0, 0)] = 1.0
    t_b = AlgebraicTrie()
    t_b[(0, 0)] = 3.0
    c_trie = tensordot(t_a, t_b, axes=1)
    assert c_trie[(0, 0)] == 3.0


def test_flatten_unflatten_roundtrip():
    nested = {
        'a': {'x': 10, 'y': 20},
        'b': {'x': 30},
    }

    flat = flatten_tensor(nested)
    assert flat[('a', 'x')] == 10
    assert flat[('a', 'y')] == 20
    assert flat[('b', 'x')] == 30

    reconstructed = unflatten_tensor(flat)
    assert reconstructed == nested

    # Unflatten with single non-tuple key
    flat_single = {0: 10, 1: 20}
    reconstruct_single = unflatten_tensor(flat_single)
    assert reconstruct_single == {0: 10, 1: 20}


def test_einsum_error_handling():
    with pytest.raises(ValueError, match='at least one tensor'):
        einsum('i->i')

    with pytest.raises(ValueError, match='must match number of tensors'):
        einsum('i,j->ij', {(0,): 1.0})

    with pytest.raises(TypeError, match='Expected AlgebraicTrie or Mapping'):
        einsum('i->i', 12345)  # Invalid type


def test_unpermute_tensor():
    """Verify unpermute_tensor(permute_tensor(T, p), p) == T."""
    tensor = {(0, 1, 2): 5.0, (1, 0, 3): 2.5}
    perm = (2, 0, 1)

    permuted = permute_tensor(tensor, perm)
    unpermuted = unpermute_tensor(permuted, perm)

    assert unpermuted == tensor

