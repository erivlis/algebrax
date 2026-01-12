import math
from collections.abc import Mapping, Sized
from typing import Any

__all__ = [
    'count_elements',
    'deepness',
    'density',
    'is_sparse',
    'sparsity',
    'uniformness',
    'wideness',
]


def _get_leaf_depths(obj: Any, current_depth: int = 0, accumulator: list[int] | None = None) -> list[int]:
    """Recursively find the depth of all leaf nodes using an accumulator."""
    if accumulator is None:
        accumulator = []

    if isinstance(obj, Mapping):
        if not obj:
            accumulator.append(current_depth)
        else:
            for v in obj.values():
                _get_leaf_depths(v, current_depth + 1, accumulator)
    else:
        accumulator.append(current_depth)

    return accumulator


def count_elements(obj: Sized) -> int:
    """
    Recursively count the number of non-container elements in a structure.

    Args:
        obj: The object to count.

    Returns:
        The total count of leaf elements.
    """
    if isinstance(obj, Mapping):
        return sum(count_elements(v) for v in obj.values())
    # We treat strings/bytes as atomic values, not containers of characters
    if isinstance(obj, (str, bytes)):
        return 1
    return 1


def deepness(obj: Any) -> int:
    """
    Calculate the maximum depth of a nested structure.

    Args:
        obj: The nested object.

    Returns:
        The maximum depth.
    """
    if not isinstance(obj, Mapping) or not obj:
        return 0
    return 1 + max(deepness(v) for v in obj.values())


def density(obj: Sized, capacity: int | None = None) -> float:
    """
    Calculate the density of a sparse object.
    Density = Number of stored elements / Total capacity.

    If the object is a nested Mapping (like a SparseMatrix), it counts
    all leaf elements recursively.

    Args:
        obj: The sparse object (e.g., dict).
        capacity: The total possible size (e.g., vector length, matrix N*M).
                  If None, density is undefined (or 1.0 relative to itself).

    Returns:
        Float between 0.0 and 1.0.
    """
    if capacity is None or capacity == 0:
        return 1.0 if len(obj) > 0 else 0.0

    # Use recursive count for Mappings to handle matrices correctly
    count = count_elements(obj) if isinstance(obj, Mapping) else len(obj)

    return count / capacity


def is_sparse(obj: Sized, capacity: int | None = None, threshold: float = 0.5) -> bool:
    """
    Check if an object is considered "sparse" based on a threshold.

    Args:
        obj: The object.
        capacity: Total capacity.
        threshold: Sparsity threshold (default 0.5).
                   If sparsity > threshold, returns True.

    Returns:
        True if sparse, False otherwise.
    """
    return sparsity(obj, capacity) > threshold


def sparsity(obj: Sized, capacity: int | None = None) -> float:
    """
    Calculate the sparsity of an object.
    Sparsity = 1 - Density.

    Args:
        obj: The sparse object.
        capacity: The total possible size.

    Returns:
        Float between 0.0 and 1.0.
    """
    return 1.0 - density(obj, capacity)


def uniformness(obj: Mapping) -> float:
    """
    Calculate the uniformness (balance) of a nested mapping (0.0 to 1.0).
    1.0 means all leaves are at the same depth.
    0.0 means highly unbalanced.

    Calculated as 1 - (std_dev_of_leaf_depths / mean_leaf_depth).

    Args:
        obj: The nested mapping.

    Returns:
        A float between 0.0 and 1.0.
    """
    if not isinstance(obj, Mapping) or not obj:
        return 1.0

    depths = _get_leaf_depths(obj)
    if len(depths) < 2:
        return 1.0

    mean = sum(depths) / len(depths)
    # mean is always >= 1 because depths start at 1 for non-empty Mapping

    variance = sum((d - mean) ** 2 for d in depths) / len(depths)
    std_dev = math.sqrt(variance)

    # Normalize by mean depth to get a relative measure
    return max(0.0, 1.0 - (std_dev / mean))


def wideness(obj: Any) -> int:
    """
    Calculate the maximum width (number of keys) at any level of a nested mapping.

    Args:
        obj: The nested object.

    Returns:
        The maximum width.
    """
    if not isinstance(obj, Mapping):
        return 0
    if not obj:
        return 0

    max_w = len(obj)
    for v in obj.values():
        max_w = max(max_w, wideness(v))
    return max_w
