from collections.abc import Mapping
from typing import Any

from algebrax.typing import K, V

__all__ = ['compose', 'invert', 'signature']


def compose(m1: Mapping[K, V], m2: Mapping[V, Any]) -> dict[K, Any]:
    """
    Compose two mappings (permutations): result[k] = m2[m1[k]].

    Args:
        m1: The first mapping (inner function).
        m2: The second mapping (outer function).

    Returns:
        A new dictionary representing the composition m2(m1(x)).
    """
    return {k: m2[v] for k, v in m1.items() if v in m2}


def invert(mapping: Mapping[K, V]) -> dict[V, K]:
    """
    Invert a mapping (swap keys and values).
    Useful for finding the inverse of a permutation.
    If the mapping is not injective, keys will be overwritten.

    Args:
        mapping: The input mapping.

    Returns:
        A new dictionary with keys and values swapped.
    """
    return {v: k for k, v in mapping.items()}


def signature(mapping: Mapping[K, K]) -> int:
    """
    Compute the signature (parity) of a permutation.

    Args:
        mapping: A mapping representing a permutation (must be bijective on its domain).

    Returns:
        1 if the permutation is even, -1 if it is odd.

    Raises:
        ValueError: If the mapping is not a valid permutation.
    """
    visited = set()
    cycles = 0
    elements = set(mapping.keys()) | set(mapping.values())

    for k in elements:
        if k in visited:
            continue

        cycles += 1
        curr = k
        while curr not in visited:
            visited.add(curr)
            curr = mapping.get(curr)
            if curr is None:
                # This happens if the mapping is not a complete permutation on the set of keys
                # For a sparse mapping, we might assume fixed points for missing keys?
                # But here we strictly check the cycle.
                raise ValueError(f'Mapping is not a complete permutation: broken cycle at {curr}')

    n = len(elements)
    return -1 if (n - cycles) % 2 else 1
