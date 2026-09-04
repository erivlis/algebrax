---
title: Transforms & Spectral Analysis
description: Discrete Fourier, Walsh-Hadamard, Hilbert, Z-Transform, Fenchel-Legendre, and Spatial Convolutions.
---

# Transforms & Spectral Analysis (`algebrax.transforms`)

The `transforms` namespace provides discrete spectral, time-frequency, and convex analysis tools:

* **`dft` & `idft`**: Discrete Fourier Transform and inverse for spatial frequency spectra.
* **`walsh_hadamard`**: Orthogonal Hadamard-Walsh dyadic spectral decomposition.
* **`hilbert`**: Hilbert transform for analytical signal envelope extraction.
* **`z_transform`**: Complex frequency $Z$-plane transfer function evaluation.
* **`convolve`**: Generalized 2D spatial convolution over arbitrary semirings.
* **`legendre_fenchel`**: Convex dual conjugate transformation.

---

# Walsh-Hadamard Transform (Boolean Hypercube Parity)

The **Walsh-Hadamard Transform (WHT)** computes orthogonal hypercube transformations over $\mathbb{Z}_2^n$ using bitwise XOR parity.

It maps a discrete signal $x[m]$ to frequency Walsh coefficients:

$$X[k] = \sum_{m=0}^{N-1} x[m] \cdot (-1)^{\text{popcount}(k \wedge m)}$$

where $\text{popcount}(k \wedge m)$ is the bitwise XOR parity count.

---

## Example Usage

<!-- name: test_walsh_hadamard_transform -->

```python linenums="1"
import algebrax as ax

# Signal on 2-bit hypercube (Z_2^2)
f = {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0}
wht = ax.transforms.walsh_hadamard(f, n=4)

print("Walsh-Hadamard Spectrum:", wht)
# Output: {0: 10.0, 1: -4.0, 2: -2.0, 3: 0.0}

# Dual Self-Inverse Property: WHT(WHT(f)) / N = f
reconstructed = {k: v / 4.0 for k, v in ax.transforms.walsh_hadamard(wht, n=4).items()}
print("Reconstructed Signal:   ", reconstructed)
# Output: {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0}
```

---

## 2. Morphological Operations (Tropical & Arctic Semirings)

By swapping the underlying algebraic semiring, `convolve` performs non-linear **Mathematical Morphology**:

- **Morphological Dilation** (Max-Plus / Arctic Semiring $(\max, +)$): Computes max-pooling over the kernel footprint.
- **Morphological Erosion** (Min-Plus / Tropical Semiring $(\min, +)$): Computes min-pooling over the kernel footprint.

<!-- name: test_image_convolution_morphology -->

```python linenums="1"
import algebrax as ax

def add_2d(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
    return (p1[0] + p2[0], p1[1] + p2[1])

image = {(3, 3): 1.0, (3, 4): 1.0, (4, 3): 1.0, (4, 4): 1.0}

# 3x3 Cross Footprint Kernel
cross_kernel = {
    (-1, 0): 0.0,
    (0, -1): 0.0, (0, 0): 0.0, (0, 1): 0.0,
    (1, 0): 0.0,
}

# Morphological Dilation
dilated = ax.transforms.convolve(
    image,
    cross_kernel,
    key_op=add_2d,
    semiring=ax.semiring.ArcticSemiring(),
)

print(f"Dilated image contains {len(dilated)} non-zero pixels (expanded footprint).")
assert len(dilated) == 12
```

---

# Fenchel-Legendre Transform (Tropical Fourier)

The "Fourier Transform" for the Min-Plus semiring. It analyzes the "slope content" of a signal.

<!-- name: test_fenchel_transform -->

```python linenums="1"
import algebrax as ax


# A convex signal (like a potential well)
signal = {0: 0, 1: 1, 2: 4, 3: 9}  # f(x) = x^2

# Analyze slope at s=2
# f*(s) = sup(s*x - f(x))
# at s=2: max(2*0-0, 2*1-1, 2*2-4, 2*3-9) = max(0, 1, 0, -3) = 1
val = ax.transforms.legendre_fenchel(signal, slope=2)
print(f"Convex Conjugate at slope 2: {val}")
```

---

## Related Recipes & Applications

* [Optical Holography Simulation](../../recipes.md) — Diffraction via `dft` & `idft`.
* [Telecommunications & Fractal Networks](../../recipes.md) — Orthogonal multiplexing via `walsh_hadamard`.
* [Vibration Structural Analysis](../../recipes.md) — Fatigue envelope detection via `hilbert`.
* [Quantum Convex Optimization](../../recipes.md) — Dual loss evaluation via `legendre_fenchel`.
