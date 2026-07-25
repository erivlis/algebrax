"""
This module provides utility functions for analyzing and working with
nested structures and collections. These functions calculate metrics
such as depth, sparsity, density, uniformness, and wideness, primarily
focused on nested mappings or sparse data representations.

The exported functions allow detailed analysis of collection structures,
providing insights for various applications such as data structure
optimization or performance analysis for sparse objects.
"""

import math
from collections.abc import Mapping, Sized
from typing import Any

__all__ = [
    'box_counting_dimension',
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


def box_counting_dimension(
        points: Mapping[tuple[int, ...], float | int],
        min_box_size: int = 1,
        max_box_size: int | None = None,
) -> float | int:
    """
    Estimate the Box-Counting Dimension (Minkowski-Bouligand dimension) of a sparse set of points.
    D = - lim (log N(e) / log e) as e -> 0.

    Here, we compute the slope of log(N(s)) vs log(1/s) for a range of box sizes s.

    Args:
        points: A mapping where keys are coordinates (tuples of ints). Values are ignored.
        min_box_size: Minimum box size to consider.
        max_box_size: Maximum box size to consider. If None, defaults to extent // 2.

    Returns:
        The estimated fractal dimension (slope of the linear regression).
    """
    if not points:
        return 0.0

    # Extract coordinates
    coords = list(points.keys())

    # Determine dimensionality and extent
    dim = len(coords[0])
    mins = [min(c[d] for c in coords) for d in range(dim)]
    maxs = [max(c[d] for c in coords) for d in range(dim)]
    extent = max(maxs[d] - mins[d] for d in range(dim))

    if max_box_size is None:
        max_box_size = max(1, extent // 2)

    # Collect (log(1/s), log(N(s))) pairs
    # We use box sizes that are powers of 2 or just linear steps?
    # Powers of 2 are standard for efficiency.

    sizes = []
    s = min_box_size
    while s <= max_box_size:
        sizes.append(s)
        s *= 2

    if len(sizes) < 2:
        return 0.0  # Not enough data points for regression

    log_inv_s = []
    log_n = []

    for s in sizes:
        # Count occupied boxes
        boxes = set()
        for c in coords:
            # Map coordinate to box index
            box_idx = tuple((c[d] - mins[d]) // s for d in range(dim))
            boxes.add(box_idx)

        count = len(boxes)
        # count is always > 0 because points is not empty
        log_inv_s.append(math.log(1.0 / s))
        log_n.append(math.log(count))

    # Linear Regression to find slope D
    # D = Cov(X, Y) / Var(X)
    n_points = len(log_inv_s)

    mean_x = sum(log_inv_s) / n_points
    mean_y = sum(log_n) / n_points

    cov_xy = sum((log_inv_s[i] - mean_x) * (log_n[i] - mean_y) for i in range(n_points))
    var_x = sum((log_inv_s[i] - mean_x) ** 2 for i in range(n_points))

    # var_x cannot be 0 because sizes are distinct powers of 2
    return cov_xy / var_x


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
