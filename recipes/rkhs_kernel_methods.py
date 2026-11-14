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
# # Functional Analysis, Gram-Schmidt & Reproducing Kernel Hilbert Spaces (RKHS)
#
# ## Hilbert Feature Spaces over Unboxed Sparse Dictionaries
# In functional analysis, every positive semi-definite Mercer kernel $k : \mathcal{X} \times \mathcal{X} \to \mathbb{R}$
# uniquely induces a **Reproducing Kernel Hilbert Space (RKHS)** $\mathcal{H}$ where evaluation is an inner product:
# $$f(x) = \langle f, k(\cdot, x) \rangle_{\mathcal{H}}$$
#
# In this recipe, we demonstrate:
# 1. **Finite-Dimensional Hilbert Geometry (`EuclideanSpace`, `gram_schmidt`)**: Constructing orthonormal bases
#    over unboxed sparse vectors `dict[K, float]` and verifying Cauchy-Schwarz & parallelogram axioms.
# 2. **Mercer Kernels & Induced Feature Metrics**: Evaluating `rbf_kernel`, `polynomial_kernel`, and `cosine_kernel`
#    distances $d_{\mathcal{H}}(u, v) = \sqrt{k(u,u) - 2k(u,v) + k(v,v)}$ without explicit feature maps.
# 3. **Non-Linear Kernel Ridge Regression**: Solving $(K + \alpha I) w = y$ purely in sparse Python dictionaries to
#    learn a non-linear XOR-like radial decision surface.

# %%
from __future__ import annotations

import math

from algebrax.analysis import (
    EuclideanSpace,
    ReproducingKernelHilbertSpace,
    cosine_kernel,
    gram_schmidt,
    polynomial_kernel,
    rbf_kernel,
)
from algebrax.verification import (
    verify_cauchy_schwarz,
    verify_inner_product_space_laws,
    verify_parallelogram_law,
)

# %% [markdown]
# ## 1. Sparse Euclidean Space & Gram-Schmidt Orthonormalization
#
# `EuclideanSpace` implements the `InnerProductSpace[float, dict[K, float]]` protocol over sparse dicts with
# symbolic string feature keys (`'x'`, `'y'`, `'z'`).

# %%
hilbert = EuclideanSpace[str]()

basis_raw = [
    {'x': 1.0, 'y': 1.0},
    {'x': 1.0, 'z': 1.0},
    {'y': 1.0, 'z': 1.0},
]
orthonormal = gram_schmidt(basis_raw)

print('Gram-Schmidt Orthonormal Basis:')
for idx, vec in enumerate(orthonormal):
    print(f'  e_{idx} = {{' + ', '.join(f'{k!r}: {v:.4f}' for k, v in sorted(vec.items())) + '}')
    assert math.isclose(hilbert.norm(vec), 1.0, abs_tol=1e-9)

for i in range(len(orthonormal)):
    for j in range(i + 1, len(orthonormal)):
        assert math.isclose(hilbert.inner(orthonormal[i], orthonormal[j]), 0.0, abs_tol=1e-9)

assert verify_cauchy_schwarz(hilbert, basis_raw[0], basis_raw[1])
assert verify_parallelogram_law(hilbert, basis_raw[0], basis_raw[1])
ip_checks = verify_inner_product_space_laws(hilbert, r_samples=[0.5, -2.0, 3.0], v_samples=basis_raw)
print('InnerProductSpace axioms:', ip_checks)
assert all(ip_checks.values())

# %% [markdown]
# ## 2. Mercer Kernels, Feature Distances & Sparse Gram Matrices
#
# Notice how `ReproducingKernelHilbertSpace` lifts sparse dict inputs into infinite-dimensional RBF feature space
# or degree-$d$ polynomial feature spaces using only kernel evaluations.

# %%
rkhs_rbf = ReproducingKernelHilbertSpace(lambda u, v: rbf_kernel(u, v, gamma=1.5))
rkhs_poly = ReproducingKernelHilbertSpace(lambda u, v: polynomial_kernel(u, v, degree=2.0, c=1.0))
rkhs_cos = ReproducingKernelHilbertSpace(cosine_kernel)

pts = [{'x': 0.0, 'y': 0.0}, {'x': 1.0, 'y': 0.0}, {'x': 0.0, 'y': 1.0}, {'x': 1.0, 'y': 1.0}]
gram_rbf = rkhs_rbf.build_gram_matrix(pts)

print(f'\nRBF Gram matrix diagonal (k(x_i, x_i))   = {[round(gram_rbf[i][i], 4) for i in range(4)]}')
print(f'RBF feature distance d_H((0,0), (1,1))   = {rkhs_rbf.distance(pts[0], pts[3]):.4f}')
print(f'Poly kernel k((1,0), (0,1))              = {rkhs_poly(pts[1], pts[2]):.4f}')
print(f'Cosine kernel k((1,0), (1,1))            = {rkhs_cos(pts[1], pts[3]):.4f}')

# Verify Gram matrix symmetry
for i, row in gram_rbf.items():
    for j, val in row.items():
        assert math.isclose(val, gram_rbf[j][i], abs_tol=1e-12)

# %% [markdown]
# ## 3. Non-Linear Kernel Ridge Regression (Smooth XOR & Radial Surface)
#
# Linear models fail on non-linearly separable XOR targets:
# $(0,0) \to -1,\; (1,1) \to -1,\; (1,0) \to +1,\; (0,1) \to +1$.
# Solving $(K + \alpha I)w = y$ in `rkhs_rbf` separates the four corners cleanly.

# %%
xor_targets = [-1.0, 1.0, 1.0, -1.0]
predictor = rkhs_rbf.kernel_ridge_regression(pts, xor_targets, alpha=1e-3)

print('\nKernel Ridge Regression on XOR:')
for x_pt, y_true in zip(pts, xor_targets, strict=True):
    y_hat = predictor(x_pt)
    print(f'  x={x_pt} | target={y_true:+.1f} | pred={y_hat:+.4f}')
    assert abs(y_hat - y_true) < 0.05

# Test midpoint interpolation symmetry at (0.5, 0.5): balanced between +1 and -1 corners -> ~0.0
mid_pred = predictor({'x': 0.5, 'y': 0.5})
print(f'  Midpoint (0.5, 0.5) pred = {mid_pred:+.6f}')
assert abs(mid_pred) < 1e-6
