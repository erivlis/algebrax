# Catalan Numbers (Dyck Paths)

This example demonstrates how to calculate **Catalan Numbers** using the `algebrax` library.
Catalan numbers ($C_n$) appear in many combinatorial problems, such as counting valid parenthesis sequences or **Dyck Paths**.

## The Problem: Dyck Paths

A **Dyck Path** of length $2n$ is a path from $(0, 0)$ to $(2n, 0)$ that:
1.  Uses steps $U = (1, 1)$ (Up) and $D = (1, -1)$ (Down).
2.  Never goes below the x-axis ($y \ge 0$).

The number of such paths is the $n$-th Catalan number $C_n$.

## Algebraic Formulation

We can model this as a **Graph Walk** problem on a 1D grid (the y-axis heights $0, 1, 2, \dots$).

*   **Nodes**: Integer heights $h \in \{0, 1, \dots, n\}$.
*   **Edges**:
    *   $h \to h+1$ (Up step)
    *   $h \to h-1$ (Down step)
*   **Constraint**: We cannot go below 0.

We want to find the number of paths from node $0$ to node $0$ in exactly $2n$ steps.
This is equivalent to $(A^{2n})_{0,0}$ where $A$ is the adjacency matrix of the line graph.

<!-- name: test_catalan_dyck_paths -->

```python linenums="1"
from algebrax.semiring import StandardSemiring
from algebrax.matrix import dot, power

def catalan_via_matrix(n: int) -> int:
    """
    Calculates the n-th Catalan number by counting Dyck paths.
    
    A Dyck path of semi-length n has 2n steps.
    We model this as a walk on the integer line [0, n].
    """
    if n == 0: return 1
    
    # 1. Construct the Adjacency Matrix for heights 0 to n
    # We only need heights up to n because a path of length 2n 
    # starting at 0 cannot go higher than n and return to 0.
    size = n + 1
    adjacency = {}
    
    for h in range(size):
        adjacency[h] = {}
        # Up step (h -> h+1)
        if h + 1 < size:
            adjacency[h][h+1] = 1
        # Down step (h -> h-1)
        if h - 1 >= 0:
            adjacency[h][h-1] = 1
            
    # 2. Compute A^(2n) using the Standard Semiring (+, *)
    # This counts the number of walks of length 2n.
    # We use binary exponentiation (matrix power) for efficiency.
    semiring = StandardSemiring()
    
    # We need 2n steps
    steps = 2 * n
    
    # Result matrix M = A^(2n)
    M = power(adjacency, steps, semiring)
    
    # 3. The answer is the number of paths from 0 to 0
    # We use .get(0, {}).get(0, 0) to handle sparsity safely
    return int(M.get(0, {}).get(0, 0))

# Verify the first few Catalan numbers: 1, 1, 2, 5, 14, 42
expected = [1, 1, 2, 5, 14, 42]
calculated = [catalan_via_matrix(i) for i in range(6)]

print(f"Expected:   {expected}")
print(f"Calculated: {calculated}")

assert expected == calculated
```

## Alternative: Segner's Recurrence (Convolution)

Catalan numbers also satisfy the recurrence:
$$C_{n+1} = \sum_{i=0}^{n} C_i C_{n-i}$$

This is a **Convolution**. In the `algebrax` context, this looks like polynomial multiplication.
If we define a polynomial $P(x) = \sum C_i x^i$, then $P(x) = 1 + x P(x)^2$.

We can use the `Cauchy Product` (Discrete Convolution) to compute this iteratively.

<!-- name: test_catalan_convolution -->

```python linenums="1"
from algebrax.semiring import StandardSemiring

def catalan_via_convolution(n: int) -> int:
    if n == 0: return 1
    
    # C[0] = 1
    catalan = [1]
    
    for k in range(1, n + 1):
        # C_k = sum(C_i * C_{k-1-i}) for i from 0 to k-1
        # This is the dot product of the list with its reverse
        c_k = 0
        for i in range(k):
            c_k += catalan[i] * catalan[k - 1 - i]
        catalan.append(c_k)
        
    return catalan[n]

print(f"C_5 (Convolution): {catalan_via_convolution(5)}")
# output: 42
```
