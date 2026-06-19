---
title: Standard Semiring
---

# Standard Semiring (Linear Algebra)

The default semiring uses standard arithmetic ($+, \times$).

<!-- name: test_standard_semiring -->

```python linenums="1"
from algebrax.semiring import StandardSemiring
from algebrax.matrix import dot

# Sparse Matrices
A = {0: {0: 1, 1: 2}, 1: {0: 3, 1: 4}}
B = {0: {0: 5, 1: 6}, 1: {0: 7, 1: 8}}

# Standard Matrix Multiplication
C = dot(A, B, semiring=StandardSemiring())
print(C)
# output: {0: {0: 19.0, 1: 22.0}, 1: {0: 43.0, 1: 50.0}}
```
