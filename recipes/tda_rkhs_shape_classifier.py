# %%
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Topological ML Pipeline: Persistent Homology to RKHS Shape Classification
#
# ## End-to-End Pure-Python Topological Machine Learning
# This recipe combines **Phase 4 Persistent Homology** (`algebrax.topology`) with **Phase 7 Hilbert Space Kernel
# Methods** (`algebrax.analysis`) to classify noisy 2D point clouds purely from their topological shape—with **zero
# NumPy or scikit-learn dependencies**:
#
# 1. **Point-Cloud Filtration (`FilteredSimplicialComplex.from_vietoris_rips`)**: Builds Vietoris-Rips simplicial
#    filtrations over pairwise sparse Euclidean distances.
# 2. **Topological Feature Extraction (`persistent_homology`, `betti_curve`)**: Summarizes connected components
#    ($\beta_0$) and 1D loops ($\beta_1$) across filtration scales into sparse `dict[tuple[str, int], float]` vectors.
# 3. **Mercer Kernel Classification (`ReproducingKernelHilbertSpace`)**: Trains one-vs-rest RBF kernel ridge
#    classifiers over Betti signatures to separate **Clusters** ($\beta_1=0$), **Single Rings** ($\beta_1=1$), and
#    **Figure-Eight Double Loops** ($\beta_1=2$).

# %%
from __future__ import annotations

import math
import random

from algebrax.analysis import (
    EuclideanSpace,
    ReproducingKernelHilbertSpace,
    rbf_kernel,
)
from algebrax.topology import (
    FilteredSimplicialComplex,
    betti_curve,
    persistent_homology,
)

# %% [markdown]
# ## 1. Synthetic Point-Cloud Generators (Clusters vs. Rings vs. Figure-Eights)
#
# Each sample consists of 12 noisy 2D points drawn from one of three distinct topological manifolds:
# - **Class `'cluster'`**: Gaussian-like blob ($\beta_1 = 0$).
# - **Class `'ring'`**: Single circle $S^1$ of radius $1.0$ ($\beta_1 = 1$).
# - **Class `'figure8'`**: Two tangent circles $S^1 \vee S^1$ ($\beta_1 = 2$).

# %%
def generate_cloud(shape: str, rng: random.Random, n_pts: int = 12) -> list[tuple[float, float]]:
    """Generate a noisy 2D point cloud for 'cluster', 'ring', or 'figure8'."""
    pts: list[tuple[float, float]] = []
    if shape == 'cluster':
        for _ in range(n_pts):
            pts.append((rng.gauss(0.0, 0.22), rng.gauss(0.0, 0.22)))
    elif shape == 'ring':
        for i in range(n_pts):
            theta = (2.0 * math.pi * i) / n_pts + rng.uniform(-0.08, 0.08)
            r = 1.0 + rng.uniform(-0.06, 0.06)
            pts.append((r * math.cos(theta), r * math.sin(theta)))
    elif shape == 'figure8':
        half = n_pts // 2
        for i in range(half):
            theta = (2.0 * math.pi * i) / half + rng.uniform(-0.07, 0.07)
            r = 0.85 + rng.uniform(-0.05, 0.05)
            pts.append((-0.9 + r * math.cos(theta), r * math.sin(theta)))
        for i in range(n_pts - half):
            theta = (2.0 * math.pi * i) / (n_pts - half) + rng.uniform(-0.07, 0.07)
            r = 0.85 + rng.uniform(-0.05, 0.05)
            pts.append((0.9 + r * math.cos(theta), r * math.sin(theta)))
    else:
        raise ValueError(f'Unknown shape: {shape}')
    return pts


def pairwise_sparse_dist(pts: list[tuple[float, float]]) -> dict[int, dict[int, float]]:
    """Build upper-triangular sparse distance matrix for Vietoris-Rips construction."""
    mat: dict[int, dict[int, float]] = {}
    for i, (xi, yi) in enumerate(pts):
        row: dict[int, float] = {}
        for j in range(i + 1, len(pts)):
            xj, yj = pts[j]
            row[j] = math.hypot(xi - xj, yi - yj)
        if row:
            mat[i] = row
    return mat


# %% [markdown]
# ## 2. Persistent Homology & Sparse Betti Curve Vectorization
#
# For each point cloud, we compute $H_0$ and $H_1$ persistence intervals and evaluate $\beta_0(t)$ and $\beta_1(t)$
# across 10 filtration radii $t \in [0.2, 2.0]$, storing non-zero values in a sparse `dict[tuple[str, int], float]`.

# %%
GRID = [0.2 * (k + 1) for k in range(10)]


def extract_betti_features(pts: list[tuple[float, float]]) -> dict[tuple[str, int], float]:
    """Convert a 2D point cloud into a sparse Betti curve signature vector."""
    dist_mat = pairwise_sparse_dist(pts)
    fsc = FilteredSimplicialComplex.from_vietoris_rips(dist_mat, max_dim=2, max_edge_length=2.2)
    intervals = persistent_homology(fsc)
    b0 = betti_curve(intervals, thresholds=GRID, dimension=0)
    b1 = betti_curve(intervals, thresholds=GRID, dimension=1)

    features: dict[tuple[str, int], float] = {}
    for idx, val in enumerate(b0):
        if val > 0:
            features[('b0', idx)] = float(val) / 4.0
    for idx, val in enumerate(b1):
        if val > 0:
            features[('b1', idx)] = float(val)
    return features


rng = random.Random(2026)
classes = ['cluster', 'ring', 'figure8']

train_x: list[dict[tuple[str, int], float]] = []
train_y: list[str] = []
for cls_name in classes:
    for _ in range(5):
        cloud = generate_cloud(cls_name, rng)
        train_x.append(extract_betti_features(cloud))
        train_y.append(cls_name)

hilbert = EuclideanSpace[tuple[str, int]]()
print('Sample Sparse Betti Signature (ring):', {k: v for k, v in sorted(train_x[5].items()) if k[0] == 'b1'})
print('Sample Sparse Betti Signature (fig8):', {k: v for k, v in sorted(train_x[10].items()) if k[0] == 'b1'})
print(f'Feature norms: cluster={hilbert.norm(train_x[0]):.2f}, fig8={hilbert.norm(train_x[10]):.2f}')

# %% [markdown]
# ## 3. Training Pure-Python RKHS Classifiers over Topological Signatures
#
# We equip the Betti signature space with an RBF Mercer kernel $k(u, v) = \exp(-\gamma \|u - v\|_2^2)$ inside
# `ReproducingKernelHilbertSpace` and fit three one-vs-rest kernel ridge regression scores $(K + \alpha I) w_c = y_c$.

# %%
rkhs = ReproducingKernelHilbertSpace(lambda u, v: rbf_kernel(u, v, gamma=0.15))

predictors = {
    cls_name: rkhs.kernel_ridge_regression(
        train_x,
        [1.0 if label == cls_name else -1.0 for label in train_y],
        alpha=1e-2,
    )
    for cls_name in classes
}


def predict_shape(feat: dict[tuple[str, int], float]) -> tuple[str, dict[str, float]]:
    scores = {cls_name: fn(feat) for cls_name, fn in predictors.items()}
    best = max(scores, key=lambda name: scores[name])
    return best, scores


# Evaluate on unseen held-out test point clouds
test_rng = random.Random(999)
correct = 0
total = 0
print('\nHeld-Out Topological Classification Results:')
for true_shape in classes:
    for sample_idx in range(4):
        cloud = generate_cloud(true_shape, test_rng)
        feat = extract_betti_features(cloud)
        pred_shape, scores = predict_shape(feat)
        is_hit = pred_shape == true_shape
        correct += int(is_hit)
        total += 1
        if sample_idx == 0:
            score_str = ', '.join(f'{k}:{v:+.2f}' for k, v in scores.items())
            print(f'  true={true_shape:7s} -> pred={pred_shape:7s} ({score_str})')

accuracy = correct / total
print(f'\nHeld-out TDA + RKHS Accuracy: {correct}/{total} ({100.0 * accuracy:.1f}%)')
assert accuracy == 1.0
