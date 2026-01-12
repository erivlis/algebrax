import pytest

from algebrax.sparsity import (
    deepness,
    density,
    is_sparse,
    sparsity,
    uniformness,
    wideness,
)


def test_density_vector():
    # 2 items, capacity 10 -> 0.2
    obj = {1: 1, 5: 1}
    assert density(obj, capacity=10) == pytest.approx(0.2)

    # Capacity None -> 1.0 (if not empty)
    assert density(obj) == pytest.approx(1.0)
    assert density({}) == pytest.approx(0.0)


def test_density_matrix():
    # 2x2 matrix with 2 elements
    # {0: {0: 1}, 1: {1: 1}}
    # Total elements = 2. Capacity = 4. Density = 0.5.
    # Old behavior (len) would be 2/4 = 0.5 (coincidentally correct).
    # Let's try 2x2 with 3 elements.
    # {0: {0: 1, 1: 1}, 1: {0: 1}}
    # Total = 3. Capacity = 4. Density = 0.75.
    # Old behavior: len=2. 2/4 = 0.5. Incorrect.

    obj = {0: {0: 1, 1: 1}, 1: {0: 1}}
    assert density(obj, capacity=4) == pytest.approx(0.75)


def test_sparsity():
    # 2 items, capacity 10 -> density 0.2 -> sparsity 0.8
    obj = {1: 1, 5: 1}
    assert sparsity(obj, capacity=10) == pytest.approx(0.8)


def test_is_sparse():
    # 2/10 = 0.2 density -> 0.8 sparsity. > 0.5 -> True
    obj = {1: 1, 5: 1}
    assert is_sparse(obj, capacity=10) is True

    # 8/10 = 0.8 density -> 0.2 sparsity. < 0.5 -> False
    # Dense vector
    dense_obj = dict.fromkeys(range(8), 1)
    assert is_sparse(dense_obj, capacity=10) is False


def test_sparsity_string_value():
    # Test that strings inside a mapping are treated as atomic values (count=1)
    # rather than containers of characters.
    # {0: "hello"} -> 1 element.
    obj = {0: 'hello'}
    assert density(obj, capacity=10) == pytest.approx(0.1)

    # Bytes
    obj_bytes = {0: b'hello'}
    assert density(obj_bytes, capacity=10) == pytest.approx(0.1)


def test_deepness():
    # Depth 0 (empty)
    assert deepness({}) == 0
    # Depth 1 (flat)
    assert deepness({1: 1}) == 1
    # Depth 2 (nested)
    assert deepness({1: {2: 2}}) == 2
    # Depth 3
    assert deepness({1: {2: {3: 3}}}) == 3
    # Mixed depth (max wins)
    assert deepness({1: 1, 2: {3: 3}}) == 2


def test_wideness():
    # Width 0
    assert wideness({}) == 0
    # Width 2
    assert wideness({1: 1, 2: 2}) == 2
    # Nested width
    # Root has 1 child. Child has 3 children. Max width is 3.
    assert wideness({1: {2: 2, 3: 3, 4: 4}}) == 3
    # Mixed
    assert wideness({1: {2: 2}, 3: {4: 4, 5: 5}}) == 2


def test_uniformness():
    # Perfectly balanced (all leaves at depth 1)
    assert uniformness({1: 1, 2: 2}) == pytest.approx(1.0)

    # Perfectly balanced (all leaves at depth 2)
    assert uniformness({1: {2: 2}, 3: {4: 4}}) == pytest.approx(1.0)

    # Unbalanced
    # Leaf 1 at depth 1. Leaf 3 at depth 2.
    # Depths: [1, 2]. Mean: 1.5.
    # Variance: ((1-1.5)^2 + (2-1.5)^2) / 2 = (0.25 + 0.25) / 2 = 0.25.
    # StdDev: 0.5.
    # Balanceness: 1 - (0.5 / 1.5) = 1 - 0.333 = 0.666
    obj = {1: 1, 2: {3: 3}}
    b = uniformness(obj)
    assert 0.6 < b < 0.7

    # Empty or single leaf -> 1.0
    assert uniformness({}) == pytest.approx(1.0)
    assert uniformness({1: 1}) == pytest.approx(1.0)


def test_uniformness_empty_nested():
    # Test case for empty nested dict (hits Line 23)
    # {1: {}} -> Leaf at depth 1 (the empty dict itself is a leaf)
    # {2: 2} -> Leaf at depth 1
    # Depths: [1, 1]. Mean: 1. Uniformness: 1.0
    obj = {1: {}, 2: 2}
    assert uniformness(obj) == pytest.approx(1.0)

    # Unbalanced empty nested
    # {1: {2: {}}} -> Leaf at depth 2
    # {3: 3} -> Leaf at depth 1
    # Depths: [2, 1]. Mean: 1.5.
    obj2 = {1: {2: {}}, 3: 3}
    assert uniformness(obj2) < 1.0
