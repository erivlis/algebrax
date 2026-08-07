# 2D Image & Grid Convolution

This guide demonstrates how to perform **2D Image Filtering** and **Morphological Operations** using `algebrax.transforms.convolve`.

By defining keys as 2D spatial coordinate tuples `(r, c)` and providing a 2D vector addition key operator (`lambda p1, p2: (p1[0] + p2[0], p1[1] + p2[1])`), the generic `convolve` function seamlessly scales from 1D signals to 2D image grids and multi-dimensional spatial arrays.

---

## 1. Linear Image Filtering (Standard Semiring)

In linear image processing, convolution is defined as:

$$h[r, c] = \sum_{dr, dc} f[r - dr, c - dc] \cdot g[dr, dc]$$

Using the **Standard Semiring** $(\mathbb{R}, +, \times)$, `convolve` supports all standard linear 2D spatial filters such as Sobel edge detection, sharpening, and Gaussian blur.

<!-- name: test_image_convolution_linear -->

```python linenums="1"
import algebrax as ax

def add_2d(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
    return (p1[0] + p2[0], p1[1] + p2[1])

# 1. Define a 2D Sparse Image (8x8 Grid with a Center Square)
image = {
    (r, c): 1.0
    for r in range(2, 6)
    for c in range(2, 6)
}

# 2. Define a 3x3 Sobel Horizontal Edge Filter
sobel_h = {
    (-1, -1): -1.0, (-1, 0): 0.0, (-1, 1): 1.0,
    (0, -1): -2.0,  (0, 0): 0.0,  (0, 1): 2.0,
    (1, -1): -1.0,  (1, 0): 0.0,  (1, 1): 1.0,
}

# 3. Compute 2D Convolution
filtered = ax.transforms.convolve(
    image,
    sobel_h,
    key_op=add_2d,
    semiring=ax.semiring.StandardSemiring(),
)

print(f"Original pixels: {len(image)}, Filtered pixels: {len(filtered)}")
assert len(filtered) > 0
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
