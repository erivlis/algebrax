from algebrax.lattice import (
    average,
    combine,
    difference,
    exclude,
    exclusive,
    geometric_mean,
    harmonic_mean,
    join,
    mask,
    meet,
    product,
    ratio,
    symmetric_difference,
)


def test_combine_union():
    m1 = {"a": 1, "b": 2}
    m2 = {"b": 3, "c": 4}
    # Default op: max (join)
    res = join(m1, m2)
    assert res == {"a": 1, "b": 3, "c": 4}


def test_combine_intersection():
    m1 = {"a": 1, "b": 2}
    m2 = {"b": 3, "c": 4}
    # meet (min on intersection)
    res = meet(m1, m2)
    assert res == {"b": 2}

    # Test swap args path (len m1 > len m2)
    res2 = meet(m2, m1)
    assert res2 == {"b": 2}


def test_combine_generic_callable():
    m1 = {"a": 1}
    m2 = {"b": 2}
    # Custom domain: only 'a'
    res = combine(m1, m2, lambda a, b: a + b, domain=lambda s1, s2: s1)
    assert res == {"a": 1}


def test_combine_generic_iterable():
    m1 = {"a": 1}
    m2 = {"b": 2}
    res = combine(m1, m2, lambda a, b: a + b, domain=["a"])
    assert res == {"a": 1}


def test_combine_generic_empty():
    m1 = {"a": 1}
    m2 = {"b": 2}
    res = combine(m1, m2, lambda a, b: a + b, domain=[])
    assert res == {}


def test_combine_generic_zero_result():
    m1 = {"a": 1}
    m2 = {"a": -1}
    # Custom domain to force fallback
    # Op: sum. 1 + (-1) = 0. Should be dropped.
    res = combine(m1, m2, lambda a, b: a + b, domain=["a"])
    assert res == {}


def test_difference():
    m1 = {"a": 10, "b": 20}
    m2 = {"b": 5, "c": 1}
    # a: 10-0=10, b: 20-5=15, c: 0-1=-1
    res = difference(m1, m2)
    assert res == {"a": 10, "b": 15, "c": -1}


def test_symmetric_difference():
    m1 = {"a": 10, "b": 20}
    m2 = {"b": 25, "c": 1}
    # |a-b|
    res = symmetric_difference(m1, m2)
    assert res == {"a": 10, "b": 5, "c": 1}


def test_product():
    m1 = {"a": 2, "b": 3}
    m2 = {"b": 4, "c": 5}
    # a*0=0 (sparse), b: 3*4=12, c*0=0
    res = product(m1, m2)
    assert res == {"b": 12}


def test_ratio():
    m1 = {"a": 10, "b": 20}
    m2 = {"a": 2, "b": 0, "c": 5}
    # a: 10/2=5, b: 20/0 -> 0 (safe div), c: 0/5=0
    res = ratio(m1, m2)
    assert res == {"a": 5.0}


def test_averages():
    m1 = {"a": 2}
    m2 = {"a": 8}

    assert average(m1, m2) == {"a": 5.0}
    assert geometric_mean(m1, m2) == {"a": 4.0}
    # Harmonic: 2*2*8 / (2+8) = 32/10 = 3.2
    assert harmonic_mean(m1, m2) == {"a": 3.2}


def test_harmonic_mean_zero():
    m1 = {"a": 0}
    m2 = {"a": 5}
    # Harmonic mean is 0. Sparse dict drops 0.
    assert harmonic_mean(m1, m2) == {}


def test_mask():
    data = {"a": 1, "b": 2, "c": 3}
    schema = {"a": 0, "c": 99}  # Values don't matter
    res = mask(data, schema)
    assert res == {"a": 1, "c": 3}

    # Test swap args path
    # mask(schema, data) -> keys in schema AND data.
    # Values come from schema.
    # 'a': schema['a'] = 0 -> Dropped (sparse)
    # 'c': schema['c'] = 99 -> Kept
    res2 = mask(schema, data)
    assert res2 == {"c": 99}


def test_exclude():
    data = {"a": 1, "b": 2, "c": 3}
    blacklist = {"b": 0}
    res = exclude(data, blacklist)
    assert res == {"a": 1, "c": 3}


def test_exclusive():
    m1 = {"a": 1, "b": 2}
    m2 = {"b": 3, "c": 4}
    # XOR keys: a, c. Values preserved.
    res = exclusive(m1, m2)
    assert res == {"a": 1, "c": 4}
