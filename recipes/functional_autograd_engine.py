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
# # Functional Reverse-Mode Automatic Differentiation & Computational Graph Engine
#
# ## Abstract
# This recipe implements a clean, purely functional **Reverse-Mode Automatic Differentiation (Autograd) Engine**
# built directly upon Python primitives and AlgebraX data structures.
#
# While **Forward-Mode AD** (via `DualNumber`) computes directional derivatives forward along computation,
# **Reverse-Mode AD** constructs a dynamically built Directed Acyclic Graph (DAG) during the forward pass
# and executes a reverse topological sweep via Vector-Jacobian Products (VJPs) during `.backward()`.
#
# This recipe proves how a full backpropagation autograd engine can be implemented in fewer than 100 lines
# of pure Python, demonstrating exact gradient backpropagation for scalar expressions, sparse vector/matrix
# models, and non-linear parameter optimization.
#
# ---
#
# ## Theoretical Foundations & Algebraic Rigor
#
# ### 1. The Adjoint Sensitivity & Chain Rule Pullback
# For a scalar objective loss $L(y_1, y_2, \dots, y_m)$, every intermediate node $u$ in the computation
# graph is assigned an **adjoint sensitivity** $\bar{u}$:
# $$\bar{u} = \frac{\partial L}{\partial u}$$
#
# For any binary operation $z = f(u, v)$, when the upstream adjoint
# $\bar{z} = \frac{\partial L}{\partial z}$ is known, the local Vector-Jacobian
# Product (VJP) pulls the adjoint back to the parent inputs:
# $$\bar{u} \mathrel{+}= \bar{z} \cdot \frac{\partial f}{\partial u}$$
# $$\bar{v} \mathrel{+}= \bar{z} \cdot \frac{\partial f}{\partial v}$$
#
# ### 2. Reverse Topological Sorting
# Because a node $u$ may contribute to multiple downstream branches (e.g. $z = u \cdot v + u^2$),
# $\bar{u}$ must accumulate the sum of sensitivities from **all** its children before it propagates its
# own gradient further upstream:
# $$\bar{u} = \sum_{c \in \text{Children}(u)} \bar{c} \cdot \frac{\partial c}{\partial u}$$
#
# The engine resolves this dependency order by performing a post-order Depth-First Search (DFS) or
# Kahn's topological sort, guaranteeing that every node is visited strictly after all its dependents.

# %%
import math
from collections.abc import Callable
from typing import Self

import algebrax as ax
from algebrax.typing import SparseMatrix, SparseVector

# %% [markdown]
# ## Step 1: Definition of the `Value` Autograd Computational Node


# %%
class Value:
    r"""A computational scalar node tracking values, children, and local adjoint pullback closures (VJPs)."""

    __slots__ = ('_backward', '_prev', 'data', 'grad', 'label')

    def __init__(
        self,
        data: float | int,
        _children: tuple['Value', ...] = (),
        label: str = '',
    ) -> None:
        self.data = float(data)
        self.grad = 0.0
        self._backward: Callable[[], None] = lambda: None
        self._prev = set(_children)
        self.label = label

    def __repr__(self) -> str:
        name_str = f"'{self.label}', " if self.label else ''
        return f'Value({name_str}data={self.data:.4f}, grad={self.grad:.4f})'

    # --- Elementary Arithmetic Operations with Local VJP Pullbacks ---

    def __add__(self, other: Self | float | int) -> 'Value':
        o = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + o.data, (self, o))

        def _backward() -> None:
            # d(u + v)/du = 1.0, d(u + v)/dv = 1.0
            self.grad += 1.0 * out.grad
            o.grad += 1.0 * out.grad

        out._backward = _backward
        return out

    def __radd__(self, other: Self | float | int) -> 'Value':
        return self.__add__(other)

    def __neg__(self) -> 'Value':
        return self * -1.0

    def __sub__(self, other: Self | float | int) -> 'Value':
        return self + (-other)

    def __rsub__(self, other: Self | float | int) -> 'Value':
        return Value(other) - self

    def __mul__(self, other: Self | float | int) -> 'Value':
        o = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * o.data, (self, o))

        def _backward() -> None:
            # Product rule: d(u*v)/du = v, d(u*v)/dv = u
            self.grad += o.data * out.grad
            o.grad += self.data * out.grad

        out._backward = _backward
        return out

    def __rmul__(self, other: Self | float | int) -> 'Value':
        return self.__mul__(other)

    def __truediv__(self, other: Self | float | int) -> 'Value':
        o = other if isinstance(other, Value) else Value(other)
        return self * (o**-1.0)

    def __rtruediv__(self, other: Self | float | int) -> 'Value':
        return Value(other) / self

    def __pow__(self, power: float | int) -> 'Value':
        p = float(power)
        out = Value(self.data**p, (self,))

        def _backward() -> None:
            # Power rule: d(u^p)/du = p * u^(p-1)
            self.grad += (p * (self.data ** (p - 1.0))) * out.grad

        out._backward = _backward
        return out

    # --- Transcendental Functions & Non-Linearities ---

    def exp(self) -> 'Value':
        e = math.exp(self.data)
        out = Value(e, (self,))

        def _backward() -> None:
            # d(exp(u))/du = exp(u)
            self.grad += e * out.grad

        out._backward = _backward
        return out

    def log(self) -> 'Value':
        if self.data <= 0.0:
            raise ValueError('Logarithm undefined for non-positive values.')
        out = Value(math.log(self.data), (self,))

        def _backward() -> None:
            # d(ln(u))/du = 1/u
            self.grad += (1.0 / self.data) * out.grad

        out._backward = _backward
        return out

    def sin(self) -> 'Value':
        out = Value(math.sin(self.data), (self,))

        def _backward() -> None:
            # d(sin(u))/du = cos(u)
            self.grad += math.cos(self.data) * out.grad

        out._backward = _backward
        return out

    def cos(self) -> 'Value':
        out = Value(math.cos(self.data), (self,))

        def _backward() -> None:
            # d(cos(u))/du = -sin(u)
            self.grad += -math.sin(self.data) * out.grad

        out._backward = _backward
        return out

    def tanh(self) -> 'Value':
        t = math.tanh(self.data)
        out = Value(t, (self,))

        def _backward() -> None:
            # d(tanh(u))/du = 1 - tanh^2(u)
            self.grad += (1.0 - t**2) * out.grad

        out._backward = _backward
        return out

    def sigmoid(self) -> 'Value':
        s = 1.0 / (1.0 + math.exp(-self.data)) if self.data >= 0 else math.exp(self.data) / (1.0 + math.exp(self.data))
        out = Value(s, (self,))

        def _backward() -> None:
            # d(sigmoid(u))/du = s * (1 - s)
            self.grad += (s * (1.0 - s)) * out.grad

        out._backward = _backward
        return out

    def relu(self) -> 'Value':
        out = Value(max(0.0, self.data), (self,))

        def _backward() -> None:
            self.grad += (1.0 if self.data > 0.0 else 0.0) * out.grad

        out._backward = _backward
        return out

    # --- Topological Sorting & Reverse Backpropagation Pass ---

    def backward(self) -> None:
        r"""Executes reverse-mode backpropagation starting from this scalar root node."""
        topo: list[Value] = []
        visited: set[Value] = set()

        def build_topo(node: Value) -> None:
            if node not in visited:
                visited.add(node)
                for child in node._prev:
                    build_topo(child)
                topo.append(node)

        build_topo(self)

        # Initialize root adjoint sensitivity dL/dL = 1.0
        self.grad = 1.0

        # Traverse DAG in reverse topological order (Output -> Leaves)
        for node in reversed(topo):
            node._backward()


# %% [markdown]
# ## Step 2: Verification on a Multi-Branch Non-Linear Expression
#
# Consider the expression with shared sub-graphs and multiple branches:
# $$f(x, y) = \frac{x^2 \cdot y + \sin(x)}{y + \exp(x)}$$
# Evaluated at $x = 1.5, y = 2.0$.


# %%
def build_and_evaluate_dag(
    expr_type: str,
    vx: float,
    vy: float,
    vz: float,
) -> tuple[Value, Value, Value, Value, str]:
    """Constructs an autograd DAG from continuous inputs, executes backward VJPs, and returns nodes."""
    x = Value(vx, label='x')
    y = Value(vy, label='y')
    z = Value(vz, label='z')

    if '(x^2*y + sin(x)) / (y + exp(x))' in expr_type:
        num = (x**2) * y + x.sin()
        den = y + x.exp()
        out = num / den
        out.label = 'f(x, y)'
        desc = 'Quotient rule DAG: (x^2*y + sin(x)) / (y + exp(x))'
    elif 'Loss = (w1*x1 + w2*x2)^2 + tanh(y)' in expr_type:
        w1 = Value(0.8, label='w1')
        w2 = Value(-0.5, label='w2')
        y_lin = w1 * x + w2 * z
        out = (y_lin**2) + y.tanh()
        out.label = 'Loss'
        desc = 'Quadratic loss + tanh activation over linear combination'
    else:
        out = x * y * z + (x * z).exp() + y.log()
        out.label = 'g(x, y, z)'
        desc = 'Multi-variable composite: x*y*z + exp(x*z) + ln(y)'

    out.backward()
    return out, x, y, z, desc


def optimize_polynomial_regression(
    train_data: list[tuple[float, float]],
    iterations: int = 600,
    learning_rate: float = 0.02,
) -> tuple[Value, Value, Value, float]:
    """Fits polynomial w1*x^2 + w2*x + b using autograd gradient descent."""
    w1 = Value(0.5, label='w1')
    w2 = Value(-0.5, label='w2')
    b = Value(0.0, label='b')
    params = [w1, w2, b]

    total_loss = Value(0.0)
    for _ in range(iterations):
        total_loss = Value(0.0)
        for x_val, y_true in train_data:
            x_node = Value(x_val)
            y_pred = w1 * (x_node**2) + w2 * x_node + b
            diff = y_pred - y_true
            total_loss = total_loss + (diff**2)

        total_loss = total_loss / len(train_data)
        for p in params:
            p.grad = 0.0

        total_loss.backward()
        for p in params:
            p.data -= learning_rate * p.grad

    return w1, w2, b, total_loss.data


def run_demo() -> None:
    """Executes autograd DAG evaluation and polynomial regression demonstrations."""
    # Step 2 demo: Quotient rule DAG
    f, x, y, _, _ = build_and_evaluate_dag('(x^2*y + sin(x)) / (y + exp(x))', 1.5, 2.0, 1.0)
    print('Reverse-Mode Automatic Differentiation on f(x, y):')
    print(f'  f(1.5, 2.0) = {f.data:.6f}')
    print(f'  df/dx (Backprop) = {x.grad:.8f}')
    print(f'  df/dy (Backprop) = {y.grad:.8f}')

    num_val = (1.5**2) * 2.0 + math.sin(1.5)
    den_val = 2.0 + math.exp(1.5)
    dnum_dx = 2.0 * 1.5 * 2.0 + math.cos(1.5)
    dden_dx = math.exp(1.5)
    expected_df_dx = (dnum_dx * den_val - num_val * dden_dx) / (den_val**2)
    dnum_dy = 1.5**2
    dden_dy = 1.0
    expected_df_dy = (dnum_dy * den_val - num_val * dden_dy) / (den_val**2)

    assert math.isclose(f.data, num_val / den_val, rel_tol=1e-9)
    assert math.isclose(x.grad, expected_df_dx, rel_tol=1e-7)
    assert math.isclose(y.grad, expected_df_dy, rel_tol=1e-7)

    # Step 3 demo: Sparse Matrix Vector Contraction over Value nodes
    w_mat = {
        0: {0: Value(0.5, label='W00'), 1: Value(-0.2, label='W01'), 2: Value(0.8, label='W02')},
        1: {0: Value(1.2, label='W10'), 1: Value(0.3, label='W11'), 2: Value(-0.5, label='W12')},
    }
    x_vec = {
        0: {0: Value(1.0, label='x0')},
        1: {0: Value(2.0, label='x1')},
        2: {0: Value(-1.0, label='x2')},
    }
    y_vec = ax.matrix.dot(w_mat, x_vec)
    y0 = y_vec[0][0]
    y1 = y_vec[1][0]
    loss = (y0**2) + y1.tanh()
    loss.backward()

    print('\nSparse Matrix Contraction Loss & Adjoint Gradients:')
    print(f'  Loss = {loss.data:.6f}')
    print(f'  dL/dW00 = {w_mat[0][0].grad:.4f}')
    print(f'  dL/dW01 = {w_mat[0][1].grad:.4f}')
    assert math.isclose(w_mat[0][0].grad, 2.0 * y0.data * 1.0, rel_tol=1e-7)
    assert math.isclose(w_mat[0][1].grad, 2.0 * y0.data * 2.0, rel_tol=1e-7)

    # Step 4 demo: Polynomial regression fitting
    def ground_truth_fn(x_val: float) -> float:
        return 2.0 * (x_val**2) + 0.5 * x_val + 1.0

    sample_points = [-2.0, -1.0, 0.0, 1.0, 2.0]
    train_data = [(x_val, ground_truth_fn(x_val)) for x_val in sample_points]
    w1, w2, b, final_mse = optimize_polynomial_regression(train_data, iterations=600, learning_rate=0.02)

    print('\nOptimization Results after 600 iterations:')
    print(f'  Trained w1 = {w1.data:.4f} (target: 2.0000)')
    print(f'  Trained w2 = {w2.data:.4f} (target: 0.5000)')
    print(f'  Trained b  = {b.data:.4f} (target: 1.0000)')
    print(f'  Final MSE Loss = {final_mse:.6f}')
    assert final_mse < 0.001
    assert math.isclose(w1.data, 2.0, abs_tol=0.05)
    assert math.isclose(w2.data, 0.5, abs_tol=0.05)
    assert math.isclose(b.data, 1.0, abs_tol=0.05)


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print('==========================================================================')
    print('Recipe: Functional Autograd Engine Finished Successfully!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
