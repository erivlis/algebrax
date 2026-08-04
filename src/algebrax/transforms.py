"""
Mathematical and signal-processing utilities, including transformations and convolutions.

This module provides a variety of mathematical functions and transformations
for discrete signal processing and geometry analysis, such as Fourier
transforms, Lorentz boosts, and discrete convolutions.

### Algebraic Properties Summary

```markdown
| Transform / Operation | Morphism / Type                                    | What it Preserves                      | Operations Mapped                         |
|:----------------------|:---------------------------------------------------|:---------------------------------------|:------------------------------------------|
| `dft` / `idft`        | Linear Isomorphism                                 | Vector addition, scalar multiplication | Linear combinations                       |
| `hilbert`             | Linear Operator / Filter                           | Inner product projection / geometry    | Frequency phase shift                     |
| `walsh_hadamard`      | Unitary / Symmetric Isomorphism                    | Inner products, norms, vector addition | Orthogonal parity mappings                |
| `z_transform`         | Discrete Algebraic Isomorphism / Ring Homomorphism | Polynomial structure, sequence scaling | Discrete convolution $\to$ multiplication |
| `legendre_fenchel`    | Legendre-Fenchel / Convex Conjugate                | Convexity, tropical semiring geometry  | Infimal convolution $\to$ addition        |
| `gelfand_transform`   | Character Evaluation / Isomorphism                 | Abstract algebra / spectrum            | Generalized homomorphism                  |
| `convolve`            | Bilinear Mapping                                   | Vector space linearity                 | Direct tensor / group product keys        |
```
"""  # noqa: E501

import cmath
import math
import operator
from collections.abc import Callable, Mapping
from typing import TypeVar

from algebrax.semiring import (
    ArcticSemiring,
    LogSemiring,
    MonoidAlgebraSemiring,
    Semiring,
    StandardSemiring,
    TropicalSemiring,
)
from algebrax.typing import K, N, SparseVector

C = TypeVar('C')  # Character key type

__all__ = [
    'convolve',
    'deconvolve',
    'dft',
    'gelfand_transform',
    'hilbert',
    'idft',
    'iwalsh_hadamard',
    'iz_transform',
    'legendre_fenchel',
    'lorentz_boost',
    'walsh_hadamard',
    'z_transform',
]


# region Bilinear Operations & Convolution


def convolve(
        f: SparseVector[K, N],
        g: SparseVector[K, N],
        key_op: Callable[[K, K], K] = operator.add,
        semiring: Semiring[N] | None = None,
) -> SparseVector[K, N]:
    """
    Compute the discrete convolution of two sparse signals/mappings using MonoidAlgebraSemiring.
    h[z] = \\bigoplus f[x] \\otimes g[y] where key_op(x, y) == z.

    By default, assumes keys are additive (e.g., integers, vectors).
    This generalizes to Group Convolution if key_op is the group operation.
    If semiring is None (or StandardSemiring), standard coefficient arithmetic is used.

    Args:
        f: First mapping (signal).
        g: Second mapping (kernel).
        key_op: Function to combine keys (default: addition).
        semiring: Semiring for coefficient arithmetic (default: StandardSemiring).

    Returns:
        The convolved mapping.
    """
    if semiring is None:
        semiring = StandardSemiring[float]()

    monoid_semiring = MonoidAlgebraSemiring(semiring, key_op=key_op)
    return monoid_semiring.mul(f, g)


def deconvolve(
    signal: SparseVector[int, float | complex],
    kernel: SparseVector[int, float | complex],
) -> dict[int, complex]:
    """
    Perform spectral deconvolution to recover original signal f from convolved signal g = f * kernel
    via DFT division: F[k] = G[k] / K[k].

    Args:
        signal: Convolved output signal g.
        kernel: Convolution kernel k.

    Returns:
        Recovered original signal mapping index -> complex value.
    """
    if not signal or not kernel:
        return {}

    n = max(max(signal.keys(), default=0), max(kernel.keys(), default=0)) + 1
    g_spec = dft(signal, n)
    k_spec = dft(kernel, n)

    f_spec = {}
    for i in range(n):
        g_val = g_spec.get(i, 0j)
        k_val = k_spec.get(i, 0j)
        if abs(k_val) > 1e-12:
            f_spec[i] = g_val / k_val
        else:
            f_spec[i] = 0j

    return idft(f_spec, n)



# endregion


# region Algebraic & Signal Transforms


def dft(
        signal: SparseVector[int, N],
        n: int | None = None,
) -> dict[int, complex]:
    """
    Compute the Discrete Fourier Transform (DFT) of a sparse signal.
    X[k] = sum_{m=0}^{N-1} x[m] * exp(-2j * pi * k * m / N)

    Morphism Type: Linear Isomorphism / Automorphism (on periodic sequences).

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
    items = list(signal.items())

    for k in range(n):
        val = sum(x_m * cmath.exp(coef * k * m) for m, x_m in items)
        if not math.isclose(abs(val), 0, abs_tol=1e-9):
            result[k] = val

    return result


def idft(
        spectrum: Mapping[int, complex],
        n: int | None = None,
) -> dict[int, complex]:
    """
    Compute the Inverse Discrete Fourier Transform (IDFT).
    x[m] = (1/N) * sum_{k=0}^{N-1} X[k] * exp(2j * pi * k * m / N)

    Morphism Type: Inverse Linear Isomorphism.

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
    items = list(spectrum.items())

    for m in range(n):
        val = sum(X_k * cmath.exp(coef * k * m) for k, X_k in items) * norm
        if not math.isclose(abs(val), 0, abs_tol=1e-9):
            result[m] = val

    return result


def hilbert(
        signal: SparseVector[int, float],
        n: int | None = None,
) -> dict[int, complex]:
    """
    Compute the analytic signal using the Hilbert transform.
    Analytic signal = x(t) + j * H(x(t))

    Morphism Type: Linear Operator / Filter.

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


def legendre_fenchel(
        signal: SparseVector[K, N],
        slope: N,
        semiring: Semiring[N] | None = None,
) -> N:
    """
    Compute the discrete Fenchel-Legendre transform (Slope Transform) of a signal at a specific slope.
    This is the Tropical/Idempotent analog of the Fourier Transform.

    Morphism Type: Legendre-Fenchel Transform / Convex Conjugate (tropical analogue of the Fourier transform).

    If semiring is None (or StandardSemiring), we fall back to the standard convex conjugate:
        f*(s) = sup_x { s * x - f(x) }

    If a general semiring is provided, we compute the generalized Legendre-Fenchel transform:
        f*(s) = \\bigoplus_x { s \\otimes x \\otimes f(x)^{-1} }
    where \\bigoplus is semiring.add, \\otimes is semiring.mul, and f(x)^{-1} is the multiplicative inverse
    of f(x) under the semiring's multiplication.

    Args:
        signal: The input signal (mapping from index/position to value).
        slope: The slope parameter (dual variable).
        semiring: The algebraic structure.

    Returns:
        The value of the transform at the given slope.
    """
    if not signal:
        if semiring is not None:
            return semiring.zero
        return float('-inf')

    if semiring is None or isinstance(semiring, StandardSemiring):
        max_val = float('-inf')
        for x, fx in signal.items():
            if not isinstance(x, (int, float)):
                continue
            val = slope * x - fx
            if val > max_val:
                max_val = val
        if max_val == float('-inf'):
            return semiring.zero if semiring is not None else float('-inf')
        return max_val

    total = semiring.zero
    first = True
    for x, fx in signal.items():
        if not isinstance(x, (int, float)):
            continue

        try:
            sx = semiring.mul(slope, x)
        except Exception:
            sx = semiring.mul(slope, type(slope)(x))

        if isinstance(semiring, (TropicalSemiring, ArcticSemiring, LogSemiring)):
            # Multiplication is addition (+), so multiplicative inverse is negation (-fx).
            inv_fx = -fx
            term = semiring.mul(sx, inv_fx)
        else:
            try:
                inv_fx = 1.0 / fx if fx != 0 else float('inf')
                term = semiring.mul(sx, inv_fx)
            except Exception:
                term = sx - fx

        if first:
            total = term
            first = False
        else:
            total = semiring.add(total, term)

    return total


def walsh_hadamard(
        signal: SparseVector[int, N],
        n: int | None = None,
) -> dict[int, float]:
    """
    Compute the Discrete Walsh-Hadamard Transform (WHT) of a sparse signal.
    X[k] = sum_{m=0}^{N-1} x[m] * (-1)**popcount(k AND m)

    Morphism Type: Unitary/Symmetric Isomorphism.

    Args:
        signal: Mapping with integer keys (time/space indices).
        n: The size of the transform (N). Must be a power of 2.
           If None, defaults to the smallest power of 2 greater than max(keys).

    Returns:
        A mapping representing the transformed coefficients.
    """
    if not signal:
        return {}

    if n is None:
        max_key = max(signal.keys())
        n = 1
        while n <= max_key:
            n *= 2

    # Verify n is a power of 2
    if n & (n - 1) != 0 or n <= 0:
        raise ValueError('WHT size n must be a power of 2.')

    result = {}
    for k in range(n):
        val = 0.0
        for m, x_m in signal.items():
            popcount = (k & m).bit_count()
            sign = -1 if popcount % 2 == 1 else 1
            val += x_m * sign

        if not math.isclose(val, 0.0, abs_tol=1e-9):
            result[k] = val

    return result


def iwalsh_hadamard(
    signal: SparseVector[int, N],
    n: int | None = None,
) -> dict[int, float]:
    """
    Compute the Inverse Discrete Walsh-Hadamard Transform (IWHT).
    x[m] = (1/N) * sum_{k=0}^{N-1} X[k] * (-1)**popcount(k AND m)

    Morphism Type: Inverse Unitary/Symmetric Isomorphism.

    Args:
        signal: Mapping with integer keys (frequency indices).
        n: The size of the transform (N). Must be a power of 2.

    Returns:
        A mapping representing original signal values.
    """
    if not signal:
        return {}

    if n is None:
        max_key = max(signal.keys())
        n = 1
        while n <= max_key:
            n *= 2

    if n & (n - 1) != 0 or n <= 0:
        raise ValueError('IWHT size n must be a power of 2.')

    raw = walsh_hadamard(signal, n)
    norm = 1.0 / n
    result = {}
    for k, val in raw.items():
        v = val * norm
        if not math.isclose(v, 0.0, abs_tol=1e-9):
            result[k] = v
    return result



def gelfand_transform(
        signal: Mapping[K, N],
        characters: Mapping[C, Callable[[K], N]],
        semiring: Semiring[N] | None = None,
) -> dict[C, N]:
    """
    Compute the generalized Gelfand transform of a sparse signal over a set of characters.
    X[phi] = \\bigoplus_{g} signal[g] \\otimes phi(g)

    Morphism Type: Gelfand Transform / Character Evaluation (the general class for DFT, WHT).

    Args:
        signal: The input sparse mapping (keys to values).
        characters: A dictionary mapping character identifiers to character functions.
                    Each character function maps a key K to a value N.
        semiring: The algebraic structure to use. Defaults to StandardSemiring.

    Returns:
        A mapping from character identifiers to their transformed values.
    """
    if not signal or not characters:
        return {}

    if semiring is None or isinstance(semiring, StandardSemiring):
        result = {}
        for char_id, phi in characters.items():
            val = 0.0
            for g, f_g in signal.items():
                val += f_g * phi(g)
            try:
                close = math.isclose(abs(val), 0.0, abs_tol=1e-9)
            except Exception:
                close = val == 0
            if not close:
                result[char_id] = val
        return result

    result = {}
    for char_id, phi in characters.items():
        val = semiring.zero
        for g, f_g in signal.items():
            term = semiring.mul(f_g, phi(g))
            val = semiring.add(val, term)
        if val != semiring.zero:
            result[char_id] = val
    return result


def z_transform(
        signal: SparseVector[int, N],
        z: N,
        semiring: Semiring[N] | None = None,
) -> N:
    """
    Compute the unilateral Z-transform at a specific point z.
    X(z) = sum_{n=0}^{inf} x[n] * z^{-n}

    Morphism Type: Discrete Algebraic Isomorphism / Ring Homomorphism (when generalized).

    If semiring is None (or StandardSemiring), standard complex Z-transform is computed.
    Otherwise, the generalized semiring Z-transform is evaluated:
    X(z) = \\bigoplus_{n >= 0} x[n] \\otimes (z^{-1})^{\\otimes n}

    Args:
        signal: Mapping with integer keys (discrete time indices).
        z: The number at which to evaluate the transform.
        semiring: The algebraic structure to use for computation.

    Returns:
        The value of the Z-transform at z.
    """
    if not signal:
        if semiring is not None:
            return semiring.zero
        return 0j

    if semiring is None or isinstance(semiring, StandardSemiring):
        result = 0j
        for n, val in signal.items():
            if n >= 0:
                result += val * (z ** -n)
        return result

    if isinstance(semiring, (TropicalSemiring, ArcticSemiring, LogSemiring)):
        # Multiplication is addition (+), so the multiplicative inverse is negation (-z).
        z_inv = -z
    else:
        try:
            z_inv = 1.0 / z if z != 0 else float('inf')
        except Exception:
            z_inv = z

    total = semiring.zero
    for n, val in signal.items():
        if n >= 0:
            try:
                z_pow = semiring.power(z_inv, n)
                term = semiring.mul(val, z_pow)
            except Exception:
                z_pow = z_inv ** n
                term = val * z_pow

            total = semiring.add(total, term)

    return total


def iz_transform(
    x_transform: Callable[[complex], complex],
    signal_length: int,
    radius: float = 1.0,
) -> dict[int, complex]:
    """
    Compute the Inverse Z-transform of a function X(z) via discrete contour evaluation
    on a circle of radius r:
        x[n] = (1/N) * sum_{k=0}^{N-1} X(r * exp(2j * pi * k / N)) * (r * exp(2j * pi * k / N))^n

    Args:
        x_transform: Function mapping complex z -> complex value X(z).
        signal_length: Length N of the reconstructed discrete-time sequence.
        radius: Radius of contour circle |z| = r (default 1.0).

    Returns:
        Reconstructed sparse signal mapping time index n -> complex value x[n].
    """
    if signal_length <= 0:
        return {}

    n = signal_length
    samples = {}
    coef = 2j * cmath.pi / n

    for k in range(n):
        zk = radius * cmath.exp(coef * k)
        samples[k] = x_transform(zk)

    result = {}
    for m in range(n):
        val = 0j
        for k, X_k in samples.items():  # noqa: N806
            zk = radius * cmath.exp(coef * k)
            val += X_k * (zk ** m)
        val /= n
        if not math.isclose(abs(val), 0, abs_tol=1e-9):
            result[m] = val

    return result


# endregion


# region Physical & Space Transformations


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

    gamma = 1.0 / (1.0 - beta ** 2) ** 0.5

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

# endregion



