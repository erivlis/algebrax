---
title: Walsh-Hadamard Transform
description: Discrete Walsh-Hadamard Transform over boolean hypercube parity.
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
