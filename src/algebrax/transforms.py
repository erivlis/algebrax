import cmath
import math
from collections import defaultdict
from collections.abc import Callable, Mapping

from algebrax.typing import K, N, SparseVector

__all__ = [
    'box_counting_dimension',
    'convolve',
    'dft',
    'hilbert',
    'idft',
    'lorentz_boost',
    'permute_tensor',
    'z_transform',
]


def box_counting_dimension(
    points: Mapping[tuple[int, ...], float],
    min_box_size: int = 1,
    max_box_size: int | None = None,
) -> float:
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


def convolve(
    f: Mapping[K, N],
    g: Mapping[K, N],
    key_op: Callable[[K, K], K] = lambda x, y: x + y,
) -> dict[K, N]:
    """
    Compute the discrete convolution of two mappings.
    h[z] = sum(f[x] * g[y]) where key_op(x, y) == z.

    By default, assumes keys are additive (e.g., integers, vectors).
    This generalizes to Group Convolution if key_op is the group operation.

    Args:
        f: First mapping (signal).
        g: Second mapping (kernel).
        key_op: Function to combine keys (default: addition).

    Returns:
        The convolved mapping.
    """
    result = defaultdict(int)
    for k1, v1 in f.items():
        for k2, v2 in g.items():
            new_key = key_op(k1, k2)
            result[new_key] += v1 * v2

    # Remove zeros to maintain sparsity
    return {k: v for k, v in result.items() if v != 0}


def dft(
    signal: SparseVector[int, N],
    n: int | None = None,
) -> dict[int, complex]:
    """
    Compute the Discrete Fourier Transform (DFT) of a sparse signal.
    X[k] = sum_{m=0}^{N-1} x[m] * exp(-2j * pi * k * m / N)

    Args:
        signal: Mapping with integer keys (time/space indices).
        n: The size of the transform (N). If None, defaults to max(keys) + 1.

    Returns:
        A mapping representing the frequency domain signal (complex values).
    """
    if not signal:
        return {}

    if n is None:
        n = max(signal.keys()) + 1

    result = {}
    # We only need to compute output coefficients k where the result is non-zero.
    # However, DFT usually produces dense output from sparse input.
    # We will compute all k from 0 to N-1.
    # Optimization: Iterate only over present input samples.

    coef = -2j * cmath.pi / n

    for k in range(n):
        val = 0j
        for m, x_m in signal.items():
            # exp is expensive, but unavoidable for DFT
            val += x_m * cmath.exp(coef * k * m)

        if not math.isclose(abs(val), 0, abs_tol=1e-9):
            result[k] = val

    return result


def hilbert(
    signal: SparseVector[int, float],
    n: int | None = None,
) -> dict[int, complex]:
    """
    Compute the analytic signal using the Hilbert transform.
    Analytic signal = x(t) + j * H(x(t))

    Implemented via DFT:
    1. Compute DFT(x) -> X
    2. Zero out negative frequencies (and double positive ones).
    3. Compute IDFT -> Analytic Signal.

    Args:
        signal: Mapping with integer keys.
        n: The size of the transform.

    Returns:
        A mapping representing the analytic signal (complex).
        The imaginary part is the Hilbert transform of the input.
    """
    if not signal:
        return {}

    if n is None:
        n = max(signal.keys()) + 1

    # 1. DFT
    spectrum = dft(signal, n)

    # 2. Filter frequencies
    # H(w) = 1 for w=0, 2 for w>0, 0 for w<0 (relative to Nyquist)
    # In discrete domain 0..N-1:
    # k=0: DC component (keep as is, or 0? Standard is keep 1x or 0x depending on def. SciPy keeps 1x)
    # 1..N/2-1: Positive freq (multiply by 2)
    # N/2: Nyquist (keep 1x)
    # N/2+1..N-1: Negative freq (multiply by 0)

    new_spectrum = {}

    # Correct logic for both even and odd N
    # Positive frequencies are 1 ... ceil(N/2) - 1
    # Nyquist is N/2 (only if N is even)

    limit = (n + 1) // 2

    for k, val in spectrum.items():
        if k == 0 or (n % 2 == 0 and k == n // 2):
            new_spectrum[k] = val
        elif 0 < k < limit:
            # Positive frequencies
            new_spectrum[k] = val * 2
        # else: Negative frequencies (dropped)

    # 3. IDFT
    return idft(new_spectrum, n)


def idft(
    spectrum: Mapping[int, complex],
    n: int | None = None,
) -> dict[int, complex]:
    """
    Compute the Inverse Discrete Fourier Transform (IDFT).
    x[m] = (1/N) * sum_{k=0}^{N-1} X[k] * exp(2j * pi * k * m / N)

    Args:
        spectrum: Mapping with integer keys (frequency indices).
        n: The size of the transform (N). If None, defaults to max(keys) + 1.

    Returns:
        A mapping representing the time/space domain signal.
    """
    if not spectrum:
        return {}

    if n is None:
        n = max(spectrum.keys()) + 1

    result = {}
    coef = 2j * cmath.pi / n
    norm = 1.0 / n

    for m in range(n):
        val = 0j
        for k, X_k in spectrum.items():  # noqa: N806
            val += X_k * cmath.exp(coef * k * m)

        val *= norm
        if not math.isclose(abs(val), 0, abs_tol=1e-9):
            result[m] = val

    return result


def lorentz_boost(
    vector: SparseVector[int, float],
    beta: float,
    axis: int = 1,
) -> SparseVector[int, float]:
    """
    Apply a Lorentz boost to a 4-vector (or D-vector).
    Assumes index 0 is time (t), and indices 1, 2, 3... are spatial.

    Args:
        vector: The input vector {0: t, 1: x, 2: y, ...}.
        beta: Velocity as a fraction of c (v/c).
        axis: The spatial axis to boost along (default 1 for x).

    Returns:
        The transformed vector.
    """
    if abs(beta) >= 1:
        raise ValueError('Beta must be less than 1 (speed of light).')

    gamma = 1.0 / (1.0 - beta**2) ** 0.5

    t = vector.get(0, 0.0)
    x = vector.get(axis, 0.0)

    t_prime = gamma * (t - beta * x)
    x_prime = gamma * (x - beta * t)

    result = dict(vector)

    if not math.isclose(t_prime, 0, abs_tol=1e-9):
        result[0] = t_prime
    elif 0 in result:
        del result[0]

    if not math.isclose(x_prime, 0, abs_tol=1e-9):
        result[axis] = x_prime
    elif axis in result:
        del result[axis]

    return result


def permute_tensor(
    tensor: Mapping[tuple, N],
    permutation: tuple[int, ...],
) -> Mapping[tuple, N]:
    """
    Permute the dimensions of a sparse tensor.
    The tensor is represented as a mapping from coordinate tuples to values.

    Args:
        tensor: The input sparse tensor, e.g., {(0, 1, 0): val}.
        permutation: A tuple specifying the new order of axes, e.g., (2, 0, 1).

    Returns:
        A new sparse tensor with permuted dimensions.
    """
    result = {}
    for coords, val in tensor.items():
        new_coords = tuple(coords[i] for i in permutation)
        result[new_coords] = val
    return result


def z_transform(
    signal: SparseVector[int, N],
    z: complex,
) -> complex:
    """
    Compute the unilateral Z-transform at a specific point z.
    X(z) = sum_{n=0}^{inf} x[n] * z^{-n}

    Args:
        signal: Mapping with integer keys (discrete time indices).
        z: The complex number at which to evaluate the transform.

    Returns:
        The value of the Z-transform at z.
    """
    result = 0j
    for n, val in signal.items():
        if n >= 0:
            result += val * (z**-n)
    return result
