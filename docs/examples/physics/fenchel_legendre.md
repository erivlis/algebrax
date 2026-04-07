# Fenchel-Legendre Transform (Tropical Fourier)

The "Fourier Transform" for the Min-Plus semiring. It analyzes the "slope content" of a signal.

<!-- name: test_fenchel_transform -->

```python linenums="1"
from algebrax.analysis import fenchel_legendre_transform

# A convex signal (like a potential well)
signal = {0: 0, 1: 1, 2: 4, 3: 9}  # f(x) = x^2

# Analyze slope at s=2
# f*(s) = sup(s*x - f(x))
# at s=2: max(2*0-0, 2*1-1, 2*2-4, 2*3-9) = max(0, 1, 0, -3) = 1
val = fenchel_legendre_transform(signal, slope=2)
print(f"Convex Conjugate at slope 2: {val}")
```
