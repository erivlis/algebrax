# Custom Semiring: Convex Hull

You can define your own semiring to solve specialized problems.

Here is an example of the **Convex Hull Semiring** (Dyer, 2013, http://arxiv.org/pdf/1307.3675.pdf),
used for multi-objective optimization.

* **Values:** Sets of points (polytopes).
* **Add:** Convex Hull of Union.
* **Mul:** Minkowski Sum ($A + B = \{a+b \mid a \in A, b \in B\}$).

<!-- name: test_convex_hull_semiring -->

```python linenums="1"
from typing import Set
from algebrax.semiring import Semiring

# Simple 1D Convex Hull (Intervals)
# Value is a tuple (min, max) representing the interval [min, max]
Interval = tuple[float, float]


class IntervalSemiring:
    @property
    def zero(self) -> Interval:
        return (float('inf'), float('-inf'))  # Empty set

    @property
    def one(self) -> Interval:
        return (0.0, 0.0)  # The point {0}

    def add(self, a: Interval, b: Interval) -> Interval:
        # Convex Hull of Union: [min(a_min, b_min), max(a_max, b_max)]
        return (min(a[0], b[0]), max(a[1], b[1]))

    def mul(self, a: Interval, b: Interval) -> Interval:
        # Minkowski Sum: [a_min + b_min, a_max + b_max]
        return (a[0] + b[0], a[1] + b[1])


# Usage
semiring = IntervalSemiring()

# Set A: Interval [1, 2]
A = (1.0, 2.0)
# Set B: Interval [3, 4]
B = (3.0, 4.0)

# Union (Hull): [1, 4]
print(semiring.add(A, B))
# output: (1.0, 4.0)

# Sum: [1+3, 2+4] = [4, 6]
print(semiring.mul(A, B))
# output: (4.0, 6.0)
```
