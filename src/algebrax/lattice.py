from collections.abc import Callable, Iterable, Mapping, MutableMapping
from typing import Any

from algebrax.typing import K, N, V

__all__ = [
    'average',
    'combine',
    'difference',
    'exclude',
    'exclusive',
    'geometric_mean',
    'harmonic_mean',
    'join',
    'mask',
    'meet',
    'product',
    'ratio',
    'symmetric_difference',
]


def average(
    m1: Mapping[K, N],
    m2: Mapping[K, N],
    default: N = 0,
) -> dict[K, float]:
    """
    Compute the element-wise arithmetic mean of two mappings.

    Args:
        m1: The first mapping.
        m2: The second mapping.
        default: The default value to use for missing keys (default: 0).

    Returns:
        A new dictionary with the arithmetic mean for each key.
    """
    return combine(m1, m2, lambda a, b: (a + b) / 2, default=default)


def combine(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    op: Callable[[V, V], V],
    default: Any = 0,
    domain: Iterable[K] | Callable[[set[K], set[K]], Iterable[K]] | None = None,
) -> dict[K, V]:
    """
    Combine two mappings using an element-wise binary operation.
    Automatically handles sparsity by removing zero results.
    Optimized to avoid set creation for standard set operations.

    Note on `default`:
        The default value for missing keys is `0`. This aligns with the library's
        focus on sparse algebra where missing elements are treated as the additive
        identity. If you are using `combine` for non-numeric types (e.g., strings
        or objects), you should explicitly pass `default=None` or another appropriate
        value to avoid TypeErrors or unexpected behavior.

    Args:
        m1: The first mapping.
        m2: The second mapping.
        op: The binary operation to apply (e.g., operator.add, max).
        default: The default value to use for missing keys (default: 0).
        domain: The set of keys to iterate over.
                If None or set.union, uses the union of keys.
                If set.intersection, uses the intersection.
                If set.difference, uses keys in m1 but not m2.
                If set.symmetric_difference, uses keys in m1 XOR m2.
                Otherwise, if callable, it is called with (set(m1), set(m2)).
                If an iterable, it is used directly.

    Returns:
        A new dictionary with the result of the operation for each key.
    """
    if domain is None or domain == set.union:
        return _combine_union(m1, m2, op, default)

    if domain == set.intersection:
        return _combine_intersection(m1, m2, op)

    if domain == set.difference:
        return _combine_difference(m1, m2, op, default)

    if domain == set.symmetric_difference:
        return _combine_symmetric_difference(m1, m2, op, default)

    # Fallback: Generic Domain
    keys = domain(set(m1.keys()), set(m2.keys())) if callable(domain) else domain

    result = {}
    for k in keys:
        val = op(m1.get(k, default), m2.get(k, default))
        if val != 0 and val is not None:
            result[k] = val
    return result


def _combine_union(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    op: Callable[[V, V], V],
    default: V,
) -> dict[K, V]:
    """Helper for union combination strategy."""
    result = {}
    _update_union_left(result, m1, m2, op, default)
    _update_difference(result, m2, m1, op, default, swap_args=True)
    return result


def _combine_intersection(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    op: Callable[[V, V], V],
) -> dict[K, V]:
    """Helper for intersection combination strategy."""
    result = {}
    if len(m1) <= len(m2):
        _update_intersection(result, m1, m2, op, swap_args=False)
    else:
        _update_intersection(result, m2, m1, op, swap_args=True)
    return result


def _combine_difference(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    op: Callable[[V, V], V],
    default: V,
) -> dict[K, V]:
    """Helper for difference combination strategy."""
    result = {}
    _update_difference(result, m1, m2, op, default, swap_args=False)
    return result


def _combine_symmetric_difference(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    op: Callable[[V, V], V],
    default: V,
) -> dict[K, V]:
    """Helper for symmetric difference combination strategy."""
    result = {}
    _update_difference(result, m1, m2, op, default, swap_args=False)
    _update_difference(result, m2, m1, op, default, swap_args=True)
    return result


def _update_difference(
    result: MutableMapping[K, V],
    source: Mapping[K, V],
    exclude: Mapping[K, V],
    op: Callable[[V, V], V],
    default: V,
    swap_args: bool,
) -> None:
    """Update result with keys from source that are NOT in exclude."""
    for k, v in source.items():
        if k not in exclude:
            val = op(default, v) if swap_args else op(v, default)
            if val != 0 and val is not None:
                result[k] = val


def _update_intersection(
    result: MutableMapping[K, V],
    source: Mapping[K, V],
    target: Mapping[K, V],
    op: Callable[[V, V], V],
    swap_args: bool,
) -> None:
    """Update result with keys from source that ARE in target."""
    for k, v in source.items():
        if k in target:
            val = op(target[k], v) if swap_args else op(v, target[k])
            if val != 0 and val is not None:
                result[k] = val


def _update_union_left(
    result: MutableMapping[K, V],
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    op: Callable[[V, V], V],
    default: V,
) -> None:
    """Update result with all keys from m1, combining with m2 if present."""
    for k, v1 in m1.items():
        val = op(v1, m2.get(k, default))
        if val != 0 and val is not None:
            result[k] = val


def difference(
    m1: Mapping[K, N],
    m2: Mapping[K, N],
    default: N = 0,
) -> dict[K, N]:
    """
    Compute the element-wise difference (m1 - m2) of two mappings.

    Args:
        m1: The first mapping.
        m2: The second mapping.
        default: The default value to use for missing keys (default: 0).

    Returns:
        A new dictionary with the difference for each key.
    """
    return combine(m1, m2, lambda a, b: a - b, default=default)


def exclude(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    default: Any = 0,
) -> dict[K, V]:
    """
    Return m1 restricted to keys NOT in m2 (Set Difference).
    Values from m1 are preserved.

    Args:
        m1: The first mapping (source).
        m2: The second mapping (exclusion filter).
        default: The default value (unused for m2, used for m1 if needed).

    Returns:
        A new dictionary with keys from m1 that are not in m2.
    """
    return combine(m1, m2, lambda a, b: a, default=default, domain=set.difference)


def exclusive(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    default: Any = 0,
) -> dict[K, V]:
    """
    Return the union of m1 and m2 restricted to keys NOT in both (Symmetric Difference).
    Values are preserved from whichever mapping has the key.

    Args:
        m1: The first mapping.
        m2: The second mapping.
        default: The default value to use for missing keys.

    Returns:
        A new dictionary with keys in m1 XOR m2.
    """
    # Since keys are mutually exclusive, one value is always 'default'.
    # We return the non-default value.
    return combine(m1, m2, lambda a, b: a if b == default else b, default=default, domain=set.symmetric_difference)


def geometric_mean(
    m1: Mapping[K, N],
    m2: Mapping[K, N],
    default: N = 0,
) -> dict[K, float]:
    """
    Compute the element-wise geometric mean of two mappings.

    Args:
        m1: The first mapping.
        m2: The second mapping.
        default: The default value to use for missing keys (default: 0).

    Returns:
        A new dictionary with the geometric mean for each key.
    """
    return combine(m1, m2, lambda a, b: (a * b) ** 0.5, default=default)


def harmonic_mean(
    m1: Mapping[K, N],
    m2: Mapping[K, N],
    default: N = 0,
) -> dict[K, float]:
    """
    Compute the element-wise harmonic mean of two mappings.
    H = 2 / (1/a + 1/b) = 2ab / (a + b)

    Args:
        m1: The first mapping.
        m2: The second mapping.
        default: The default value to use for missing keys (default: 0).

    Returns:
        A new dictionary with the harmonic mean for each key.
    """

    def _harmonic(a, b):
        if a == 0 or b == 0:
            return 0
        return 2 * a * b / (a + b)

    return combine(m1, m2, _harmonic, default=default)


def join(m1: Mapping[K, V], m2: Mapping[K, V]) -> dict[K, V]:
    """
    Compute the join (element-wise maximum) of two mappings.
    Useful for fuzzy union.

    Args:
        m1: The first mapping.
        m2: The second mapping.

    Returns:
        A new dictionary with the maximum value for each key.
    """
    return combine(m1, m2, max)


def mask(
    m1: Mapping[K, V],
    m2: Mapping[K, V],
    default: Any = 0,
) -> dict[K, V]:
    """
    Return m1 restricted to keys IN m2 (Set Intersection).
    Values from m1 are preserved.

    Args:
        m1: The first mapping (source).
        m2: The second mapping (inclusion filter).
        default: The default value (unused for m2, used for m1 if needed).

    Returns:
        A new dictionary with keys from m1 that are also in m2.
    """
    return combine(m1, m2, lambda a, b: a, default=default, domain=set.intersection)


def meet(m1: Mapping[K, V], m2: Mapping[K, V]) -> dict[K, V]:
    """
    Compute the meet (element-wise minimum) of two mappings.
    Useful for fuzzy intersection.

    Args:
        m1: The first mapping.
        m2: The second mapping.

    Returns:
        A new dictionary with the minimum value for each key in the intersection.
    """
    return combine(m1, m2, min, domain=set.intersection)


def product(
    m1: Mapping[K, N],
    m2: Mapping[K, N],
    default: N = 0,
) -> dict[K, N]:
    """
    Compute the element-wise product (Hadamard product) of two mappings.

    Args:
        m1: The first mapping.
        m2: The second mapping.
        default: The default value to use for missing keys (default: 0).

    Returns:
        A new dictionary with the product for each key.
    """
    return combine(m1, m2, lambda a, b: a * b, default=default)


def ratio(
    m1: Mapping[K, N],
    m2: Mapping[K, N],
    default: N = 0,
) -> dict[K, float]:
    """
    Compute the element-wise ratio (m1 / m2) of two mappings.
    Handles division by zero by returning 0.

    Args:
        m1: The first mapping (numerator).
        m2: The second mapping (denominator).
        default: The default value to use for missing keys (default: 0).

    Returns:
        A new dictionary with the ratio for each key.
    """
    return combine(m1, m2, lambda a, b: a / b if b != 0 else 0, default=default)


def symmetric_difference(
    m1: Mapping[K, N],
    m2: Mapping[K, N],
    default: N = 0,
) -> dict[K, N]:
    """
    Compute the element-wise symmetric difference (absolute difference) of two mappings.
    |m1 - m2|

    Args:
        m1: The first mapping.
        m2: The second mapping.
        default: The default value to use for missing keys (default: 0).

    Returns:
        A new dictionary with the absolute difference for each key.
    """
    return combine(m1, m2, lambda a, b: abs(a - b), default=default)
