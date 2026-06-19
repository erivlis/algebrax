---
title: Digital Semiring
---

# Digital Semiring (Post-Quantum Cryptography)

The **Digital Semiring** uses the sum of decimal digits to determine order.
It is used in cryptographic protocols (Huang et al., 2024).

* **Add:** Larger digit sum wins.
* **Mul:** Smaller digit sum wins.

<!-- name: test_digital_semiring -->

```python linenums="1"
from algebrax.semiring import DigitalSemiring

S = DigitalSemiring()

# (123) = 6, (45) = 9
# Add: 9 > 6 -> 45
print(S.add(123, 45))
# output: 45

# Mul: 6 < 9 -> 123
print(S.mul(123, 45))
# output: 123
```
