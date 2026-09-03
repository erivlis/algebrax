# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Reverse-Mode Backpropagation via Sparse Matrix Transpose & Adjoint Pullback
#
# ## Abstract
# This recipe reveals the fundamental mathematical connection between **Deep Learning Backpropagation**
# and **Sparse Linear Algebra**: the backward pass is fundamentally a sequence of **transposed matrix
# multiplications ($W^T \cdot \bar{\mathbf{y}}$)** interleaved with Hadamard activation differentials.
#
# Using purely native Python dictionaries and AlgebraX's polymorphic matrix operations (`ax.matrix.dot`
# and `ax.matrix.transpose`), we construct a complete, tape-free Multi-Layer Sparse Neural Network (`SparseMLP`).
# We derive and execute the exact Vector-Jacobian Products (VJPs), train on a non-linear classification
# problem (XOR) using gradient descent, and analytically verify the backpropagation gradients against
# finite-difference approximations.
#
# ---
#
# ## Theoretical Foundations & Algebraic Rigor
#
# ### 1. Forward Pushforward vs. Backward Adjoint Pullback
# In any neural layer parameterized by weight matrix $W \in \mathbb{R}^{M \times N}$ and activation
# function $\sigma$:
# * **Forward Pass (Linear Pushforward):**
#   $$\mathbf{z} = W \cdot \mathbf{x}, \quad \mathbf{a} = \sigma(\mathbf{z})$$
#
# * **Backward Pass (Adjoint Pullback via Transpose $W^T$):**
#   Given the upstream sensitivity / adjoint vector
#   $\bar{\mathbf{a}} = \frac{\partial L}{\partial \mathbf{a}} \in \mathbb{R}^M$,
#   the local pre-activation adjoint $\bar{\mathbf{z}} = \frac{\partial L}{\partial \mathbf{z}}$ is:
#   $$\bar{\mathbf{z}} = \bar{\mathbf{a}} \odot \sigma'(\mathbf{z})$$
#   The adjoint pulled back to the layer's input
#   $\bar{\mathbf{x}} = \frac{\partial L}{\partial \mathbf{x}} \in \mathbb{R}^N$ is:
#   $$\bar{\mathbf{x}} = W^T \cdot \bar{\mathbf{z}}$$
# ### 2. Weight Gradients as Outer Products
# The exact gradient of the scalar loss $L$ with respect to each weight matrix entry $W_{ij}$ is:
# $$\frac{\partial L}{\partial W_{ij}} = \bar{z}_i \cdot x_j$$
# $$\nabla_W L = \bar{\mathbf{z}} \otimes \mathbf{x}^T$$
# In AlgebraX, this is computed as a sparse dictionary outer product without dense matrix allocation.
#
# ### 3. Why This Scales ($O(1)$ Reverse Pass)
# Regardless of whether the network has 10 weights or 100,000 weights, propagating a single scalar loss
# gradient backward requires **exactly one traversal** of the transposed layer matrices.

# %%
import math
import random
from collections.abc import Callable
from typing import Self

import algebrax as ax
from algebrax.typing import SparseMatrix, SparseVector

# %% [markdown]
# ## Step 1: Activation Functions and Their Exact Derivatives


# %%
def sigmoid(x: float) -> float:
    r"""Logistic sigmoid activation: \sigma(x) = 1 / (1 + \exp(-x))."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    # Numerically stable formulation for negative inputs
    z = math.exp(x)
    return z / (1.0 + z)


def sigmoid_derivative(a: float) -> float:
    r"""Exact derivative of sigmoid given output a = \sigma(x): \sigma'(x) = a(1 - a)."""
    return a * (1.0 - a)


def relu(x: float) -> float:
    r"""Rectified Linear Unit (ReLU)."""
    return max(0.0, x)


def relu_derivative(x: float) -> float:
    r"""Derivative of ReLU."""
    return 1.0 if x > 0.0 else 0.0


# %% [markdown]
# ## Step 2: Definition of the Sparse Linear Layer with Transposed Backprop


# %%
class SparseLinearLayer:
    r"""A fully connected sparse neural network layer Wx + b with transposed adjoint backprop."""

    def __init__(self, in_features: int, out_features: int, seed: int = 42) -> None:
        self.in_features = in_features
        self.out_features = out_features
        rng = random.Random(seed)

        # Xavier / Glorot weight initialization
        scale = math.sqrt(2.0 / (in_features + out_features))
        self.W: dict[int, dict[int, float]] = {
            i: {j: rng.gauss(0.0, scale) for j in range(in_features)} for i in range(out_features)
        }
        self.b: dict[int, float] = dict.fromkeys(range(out_features), 0.0)

        # Cached activations for the backward pass
        self._last_x: dict[int, float] = {}
        self._last_z: dict[int, float] = {}
        self._last_a: dict[int, float] = {}

    def forward(self, x: dict[int, float], activation: str = 'sigmoid') -> dict[int, float]:
        r"""Forward pass: z = Wx + b, a = \sigma(z)."""
        self._last_x = dict(x)

        # 1. Linear contraction: z_lin = W \cdot x (represented as a 1-column matrix product)
        # Convert vector x into 1-column matrix: {node: {0: val}}
        x_col = {i: {0: val} for i, val in x.items()}
        z_col = ax.matrix.dot(self.W, x_col)

        # Extract pre-activations and add bias: z = Wx + b
        self._last_z = {i: z_col.get(i, {}).get(0, 0.0) + self.b.get(i, 0.0) for i in range(self.out_features)}

        # 2. Non-linear activation: a = \sigma(z)
        if activation == 'sigmoid':
            self._last_a = {i: sigmoid(zi) for i, zi in self._last_z.items()}
        elif activation == 'relu':
            self._last_a = {i: relu(zi) for i, zi in self._last_z.items()}
        else:
            self._last_a = dict(self._last_z)  # Linear / identity

        return self._last_a

    def backward(
        self,
        grad_output: dict[int, float],
        activation: str = 'sigmoid',
    ) -> tuple[dict[int, float], dict[int, dict[int, float]], dict[int, float]]:
        r"""Backward pass: Computes grad_input = W^T \cdot \bar{z} and \nabla_W L = \bar{z} \otimes x^T.

        Args:
            grad_output: Adjoint sensitivity vector \bar{a} = \partial L / \partial a.
            activation: Activation function used during forward pass.

        Returns:
            Tuple of (grad_input, grad_W, grad_b).
        """
        # 1. Elementwise activation derivative: \bar{z} = \bar{a} \odot \sigma'(z)
        if activation == 'sigmoid':
            grad_z = {
                i: grad_output.get(i, 0.0) * sigmoid_derivative(self._last_a[i]) for i in range(self.out_features)
            }
        elif activation == 'relu':
            grad_z = {i: grad_output.get(i, 0.0) * relu_derivative(self._last_z[i]) for i in range(self.out_features)}
        else:
            grad_z = dict(grad_output)

        # 2. Pullback to inputs via Transposed Matrix Multiplication: \bar{x} = W^T \cdot \bar{z}
        w_transpose = ax.matrix.transpose(self.W)
        grad_z_col = {i: {0: val} for i, val in grad_z.items()}
        grad_x_col = ax.matrix.dot(w_transpose, grad_z_col)
        grad_input = {j: grad_x_col.get(j, {}).get(0, 0.0) for j in range(self.in_features)}

        # 3. Outer product weight gradients: \nabla W = \bar{z} \otimes x^T
        grad_w = {
            i: {j: grad_z[i] * self._last_x.get(j, 0.0) for j in range(self.in_features)}
            for i in range(self.out_features)
        }

        # 4. Bias gradients: \nabla b = \bar{z}
        grad_b = dict(grad_z)

        return grad_input, grad_w, grad_b

    def step(
        self,
        grad_w: dict[int, dict[int, float]],
        grad_b: dict[int, float],
        learning_rate: float,
    ) -> None:
        r"""Gradient descent parameter update: W \leftarrow W - \eta \nabla W, b \leftarrow b - \eta \nabla b."""
        for i in self.W:
            for j in self.W[i]:
                self.W[i][j] -= learning_rate * grad_w.get(i, {}).get(j, 0.0)
        for i in self.b:
            self.b[i] -= learning_rate * grad_b.get(i, 0.0)


# %% [markdown]
# ## Step 3: Multi-Layer Sparse Neural Network (`SparseMLP`)


# %%
class SparseMLP:
    """Multi-layer perceptron constructed entirely from sparse matrix layers."""

    def __init__(self, layer_sizes: list[int], seed: int = 42) -> None:
        self.layers: list[SparseLinearLayer] = [
            SparseLinearLayer(layer_sizes[i], layer_sizes[i + 1], seed=seed + i) for i in range(len(layer_sizes) - 1)
        ]

    def forward(self, x: dict[int, float]) -> dict[int, float]:
        r"""Forward pass through all layers."""
        curr = x
        for layer in self.layers:
            # Use sigmoid for hidden layers and output
            curr = layer.forward(curr, activation='sigmoid')
        return curr

    def backward(
        self,
        loss_grad: dict[int, float],
    ) -> list[tuple[dict[int, dict[int, float]], dict[int, float]]]:
        r"""Reverse-mode backpropagation through all layers in topological reverse order."""
        grads = []
        curr_grad = loss_grad

        # Traverse layers in reverse: Output -> Hidden -> Input
        for layer in reversed(self.layers):
            curr_grad, grad_w, grad_b = layer.backward(curr_grad, activation='sigmoid')
            grads.append((grad_w, grad_b))

        grads.reverse()
        return grads

    def update(
        self,
        grads: list[tuple[dict[int, dict[int, float]], dict[int, float]]],
        learning_rate: float,
    ) -> None:
        r"""Apply gradient descent updates to all layers."""
        for layer, (grad_w, grad_b) in zip(self.layers, grads):
            layer.step(grad_w, grad_b, learning_rate)


# %% [markdown]
# ## Step 4: Training SparseMLP on the Non-Linear XOR Problem
#
# The XOR problem is the canonical benchmark for non-linear multi-layer backpropagation:
# * Inputs: $(0,0) 	o 0, \quad (0,1) 	o 1, \quad (1,0) 	o 1, \quad (1,1) 	o 0$


# %%
def train_sparse_mlp(
    mlp: SparseMLP,
    data: list[tuple[dict[int, float], dict[int, float]]],
    epochs: int = 1000,
    learning_rate: float = 2.0,
) -> float:
    r"""Trains a SparseMLP on dataset using backprop gradient descent and returns final MSE loss."""
    total_epoch_loss = 0.0
    for _ in range(epochs):
        total_epoch_loss = 0.0
        for x_in, y_target in data:
            y_pred = mlp.forward(x_in)
            error = y_pred[0] - y_target[0]
            total_epoch_loss += 0.5 * (error**2)
            loss_grad = {0: error}
            grads = mlp.backward(loss_grad)
            mlp.update(grads, learning_rate)
    return total_epoch_loss


def verify_gradient_finite_difference(
    mlp: SparseMLP,
    x_sample: dict[int, float],
    y_sample: dict[int, float],
    layer_idx: int = 0,
    target_i: int = 1,
    target_j: int = 0,
    h: float = 1e-5,
) -> tuple[float, float]:
    """Verifies backprop analytical gradient against central numerical finite difference."""
    y_pred = mlp.forward(x_sample)
    loss_grad = {0: y_pred[0] - y_sample[0]}
    analytical_grads = mlp.backward(loss_grad)
    backprop_grad = analytical_grads[layer_idx][0][target_i][target_j]

    layer = mlp.layers[layer_idx]
    orig_w = layer.W[target_i][target_j]

    layer.W[target_i][target_j] = orig_w + h
    y_plus = mlp.forward(x_sample)
    loss_plus = 0.5 * ((y_plus[0] - y_sample[0]) ** 2)

    layer.W[target_i][target_j] = orig_w - h
    y_minus = mlp.forward(x_sample)
    loss_minus = 0.5 * ((y_minus[0] - y_sample[0]) ** 2)

    layer.W[target_i][target_j] = orig_w
    numerical_grad = (loss_plus - loss_minus) / (2.0 * h)
    return backprop_grad, numerical_grad


def run_demo() -> None:
    """Executes XOR training demonstration and finite difference validation."""
    dataset = [
        ({0: 0.0, 1: 0.0}, {0: 0.0}),
        ({0: 0.0, 1: 1.0}, {0: 1.0}),
        ({0: 1.0, 1: 0.0}, {0: 1.0}),
        ({0: 1.0, 1: 1.0}, {0: 0.0}),
    ]
    mlp = SparseMLP(layer_sizes=[2, 4, 1], seed=101)

    initial_loss = 0.0
    for x_in, y_target in dataset:
        y_pred = mlp.forward(x_in)
        initial_loss += 0.5 * ((y_pred[0] - y_target[0]) ** 2)
    print(f'Initial Untrained MSE Loss: {initial_loss:.4f}')

    final_loss = train_sparse_mlp(mlp, dataset, epochs=3000, learning_rate=2.0)
    print(f'Final Trained MSE Loss after 3000 epochs: {final_loss:.6f}')
    assert final_loss < 0.01

    print('\nXOR Predictions after Training:')
    for x_in, y_target in dataset:
        y_pred = mlp.forward(x_in)
        print(f'  Input: ({x_in[0]:.0f}, {x_in[1]:.0f}) -> Target: {y_target[0]:.0f}, Predicted: {y_pred[0]:.4f}')
        assert abs(y_pred[0] - y_target[0]) < 0.15

    # Gradient verification
    test_mlp = SparseMLP(layer_sizes=[2, 3, 1], seed=77)
    bp_grad, num_grad = verify_gradient_finite_difference(test_mlp, dataset[1][0], dataset[1][1])
    print('\nGradient Verification for Layer 0 Weight W[1][0]:')
    print(f'  Analytical Backprop Gradient: {bp_grad:.8f}')
    print(f'  Numerical Finite Difference:  {num_grad:.8f}')
    print(f'  Absolute Discrepancy:         {abs(bp_grad - num_grad):.2e}')
    assert math.isclose(bp_grad, num_grad, rel_tol=1e-5, abs_tol=1e-5)


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Sparse Neural Backpropagation Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
