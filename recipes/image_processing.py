# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
#     "pillow",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
2D Image & Grid Convolution Recipe using algebrax.transforms.convolve

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Spatial 2D Mappings:
   In `algebrax`, an image is represented as a 2D sparse vector mapping 2D coordinate
   tuples to intensity levels: `f[(r, c)] = intensity`.
   A convolution kernel is a 2D sparse vector mapping relative offset tuples to weights:
   `g[(dr, dc)] = weight`.

2. Key Addition (2D Offset Shift):
   By passing `key_op = lambda p1, p2: (p1[0] + p2[0], p1[1] + p2[1])`, 2D vector
   addition shifts pixel coordinates by kernel offsets: (r, c) + (dr, dc) = (r + dr, c + dc).

3. ax.semiring.Semiring Generalization:
   - Standard ax.semiring.Semiring (+, *): Linear Spatial Filtering (Edge detection, Blur, Sharpen)
     h[r, c] = sum_{dr, dc} f[r - dr, c - dc] * g[dr, dc]
   - Arctic / Max-Plus ax.semiring.Semiring (max, +): Morphological Dilation / Max-Pooling
     h[r, c] = max_{dr, dc} (f[r - dr, c - dc] + g[dr, dc])
   - Tropical / Min-Plus ax.semiring.Semiring (min, +): Morphological Erosion / Min-Pooling
     h[r, c] = min_{dr, dc} (f[r - dr, c - dc] + g[dr, dc])
================================================================================
"""

import sys
from collections.abc import Mapping

import algebrax as ax


def add_2d(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
    """2D Spatial Coordinate Addition Key Operator."""
    return (p1[0] + p2[0], p1[1] + p2[1])


# --- 2D Filter Kernels ---
SOBEL_HORIZONTAL = {
    (-1, -1): -1.0,
    (-1, 0): 0.0,
    (-1, 1): 1.0,
    (0, -1): -2.0,
    (0, 0): 0.0,
    (0, 1): 2.0,
    (1, -1): -1.0,
    (1, 0): 0.0,
    (1, 1): 1.0,
}

SOBEL_VERTICAL = {
    (-1, -1): -1.0,
    (-1, 0): -2.0,
    (-1, 1): -1.0,
    (0, -1): 0.0,
    (0, 0): 0.0,
    (0, 1): 0.0,
    (1, -1): 1.0,
    (1, 0): 2.0,
    (1, 1): 1.0,
}

SHARPEN = {
    (-1, 0): -1.0,
    (0, -1): -1.0,
    (0, 0): 5.0,
    (0, 1): -1.0,
    (1, 0): -1.0,
}

BOX_BLUR_3X3 = {(dr, dc): 1.0 / 9.0 for dr in range(-1, 2) for dc in range(-1, 2)}

DILATION_CROSS_3X3 = {
    (-1, 0): 0.0,
    (0, -1): 0.0,
    (0, 0): 0.0,
    (0, 1): 0.0,
    (1, 0): 0.0,
}


def print_sparse_image_2d(img: Mapping[tuple[int, int], float], title: str, rows: int = 8, cols: int = 8) -> None:
    """Helper to display a 2D sparse image mapping as an ASCII intensity grid."""
    print(f'\n--- {title} ---')
    min_r = min((r for r, _ in img), default=0)
    max_r = max((r for r, _ in img), default=rows - 1)
    min_c = min((c for _, c in img), default=0)
    max_c = max((c for _, c in img), default=cols - 1)

    for r in range(min_r, max_r + 1):
        line = []
        for c in range(min_c, max_c + 1):
            val = img.get((r, c), 0.0)
            if val > 0.7:
                char = '██'
            elif val > 0.3:
                char = '▒▒'
            elif val > 0.05:
                char = '░░'
            elif val < -0.3:
                char = '--'
            else:
                char = '  '
            line.append(char)
        print(''.join(line))


def main() -> None:
    print('==========================================================================')
    print('Recipe: 2D Image Filtering & Mathematical Morphology via ax.semiring.Semiring Convolve')
    print('==========================================================================')
    print('Goal: Demonstrate linear 2D convolution (Sobel/Sharpen/Blur) and non-linear')
    print('      mathematical morphology (Dilation/Erosion) using algebrax.transforms.convolve.')

    # 1. Create a Synthetic 8x8 Grayscale Image with a Cross Pattern
    print('\n[Step 1] Constructing Synthetic 8x8 Sparse Image (Cross Pattern)...')
    synthetic_image: dict[tuple[int, int], float] = {}
    for r in range(8):
        for c in range(8):
            if r in (3, 4) or c in (3, 4):
                synthetic_image[(r, c)] = 1.0

    print_sparse_image_2d(synthetic_image, 'Original Synthetic 8x8 Image (Cross Pattern)')
    print(f'Total non-zero active pixels: {len(synthetic_image)}')

    # 2. Linear Edge Detection via 2D Convolution (Standard ax.semiring.Semiring)
    print('\n[Step 2] Applying 2D Sobel Horizontal Edge Detection (+, *)...')
    print('Explanation: Computes weighted sum sum_{dr,dc} f(r-dr, c-dc) * g(dr, dc).')
    print('             Horizontal gradients highlight vertical edges in the image.')
    sobel_h_result = ax.transforms.convolve(
        synthetic_image,
        SOBEL_HORIZONTAL,
        key_op=add_2d,
        semiring=ax.semiring.StandardSemiring(),
    )
    print_sparse_image_2d(sobel_h_result, 'Sobel Horizontal Edge Response (+, *)')
    print(f'Output pixels generated: {len(sobel_h_result)}')

    # 3. Morphological Dilation via 2D Convolution (Max-Plus / Arctic ax.semiring.Semiring)
    print('\n[Step 3] Applying Morphological Dilation (Max-Plus / Arctic ax.semiring.Semiring)...')
    print('Explanation: Replaces addition (+) with max and multiplication (*) with addition (+).')
    print('             Each pixel becomes max_{dr,dc} (f(r-dr, c-dc) + g(dr, dc)), expanding shape boundaries.')
    dilated_result = ax.transforms.convolve(
        synthetic_image,
        DILATION_CROSS_3X3,
        key_op=add_2d,
        semiring=ax.semiring.ArcticSemiring(),
    )
    print_sparse_image_2d(dilated_result, 'Morphological Dilation Output (Max-Plus)')
    print(f'Expanded active pixel count: {len(dilated_result)} (vs original {len(synthetic_image)})')

    # 4. Pillow Image File Demonstration
    print('\n[Step 4] Real Image File Ingestion & Sharpening (Pillow Integration)...')
    try:
        from PIL import Image

        print('Pillow (PIL) detected. Creating a 16x16 synthetic PIL Image with a centered square...')
        im = Image.new('L', (16, 16), color=0)
        for r in range(4, 12):
            for c in range(4, 12):
                im.putpixel((c, r), 255)

        # Convert Pillow Image -> AlgebraX Sparse Vector {(r, c): intensity}
        sparse_img: dict[tuple[int, int], float] = {}
        width, height = im.size
        for r in range(height):
            for c in range(width):
                pixel_val = im.getpixel((c, r)) / 255.0
                if pixel_val > 0:
                    sparse_img[(r, c)] = pixel_val

        print(f'Ingested {width}x{height} image with {len(sparse_img)} active non-zero pixels.')

        # Apply 2D Sharpening via AlgebraX ax.transforms.convolve
        sharpened_img = ax.transforms.convolve(
            sparse_img,
            SHARPEN,
            key_op=add_2d,
            semiring=ax.semiring.StandardSemiring(),
        )

        print_sparse_image_2d(sparse_img, 'Pillow 16x16 Input Square Image', rows=16, cols=16)
        print_sparse_image_2d(sharpened_img, 'AlgebraX Convolved (Sharpen Filter)', rows=16, cols=16)

    except ImportError:
        print('(Install Pillow to run real PIL Image file conversion demo)')

    print('\n==========================================================================')
    print('Recipe Completed: 2D Image Convolution & Morphology Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
