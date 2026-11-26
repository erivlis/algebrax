---
title: "EP-0231: Algebraic Signal Processing, Exact Finite-Field NTT & Poset Möbius Transforms"
description: "Formalize Püschel-Moura polynomial quotient signal models (DCT/DST/Variety FT), exact Number-Theoretic Transforms (NTT) over ModularField(p), and Rota Fast Zeta/Möbius lattice transforms."
icon: lucide/cpu
status: draft
---

# EP-0231: Algebraic Signal Processing, Exact Finite-Field NTT & Poset Möbius Transforms

| Field             | Value                                                                                           |
|:------------------|:------------------------------------------------------------------------------------------------|
| **EP**            | 0231                                                                                            |
| **Title**         | Algebraic Signal Processing, Exact Finite-Field NTT & Poset Möbius Transforms                   |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                     |
| **Sponsor**       | Core Maintainers                                                                                |
| **Delegate**      | 🧩 Russell (Signal Algebras), 🔬 Popper (Bit-Exact NTT) & ⚡ Shannon (Fast Zeta/Möbius)         |
| **Status**        | Draft                                                                                           |
| **Type**          | Standards Track                                                                                 |
| **Created**       | 2026-11-14                                                                                      |
| **Updated**       | 2026-11-26                                                                                      |
| **Replaces**      | —                                                                                               |
| **Superseded-By** | —                                                                                               |

---

## Abstract

This proposal unifies three exact algebraic transform frameworks across [`algebrax.algebra`](https://github.com/erivlis/algebrax/tree/main/src/algebrax/algebra) (which canonically hosts `ModularField`, `GaloisField`, `PolynomialAlgebra`, and `CommQuotientRing`), [`algebrax.variety`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md), and [`algebrax.lattice`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/lattice.py):

1. **General Principal Polynomial Modulus Ideals (`PolynomialModulusIdeal`) & Püschel–Moura Algebraic Signal Models (`AlgebraicSignalModel`)**:
   Generalizes `PolynomialTruncationIdeal` ($\langle x^d \rangle$) to arbitrary monic modulus polynomials $\langle P(x) \rangle \triangleleft k[x]$ and connects Püschel–Moura's Algebraic Signal Processing triple $(\mathcal{A} = k[X]/I, \mathcal{M}, \Phi)$ directly to Stickelberger companion matrices (`EP-0221`), deriving the Discrete Cosine Transform (`dct` / `idct` via Chebyshev ideals $\langle T_N(x) \rangle$), Discrete Sine Transform (`dst` / `idst` via $\langle U_N(x) \rangle$), and multivariate Variety Fourier Transforms.
2. **Exact Number-Theoretic Transforms (`ntt`, `intt`, `ntt_convolve`)**:
   Performs bit-exact cyclic and negacyclic transforms over `ModularField(p)` (`p` prime with $N \mid p - 1$), completely eliminating IEEE-754 floating-point mantissa overflow on large integer, polynomial, and cryptographic ring-LWE convolutions.
3. **Rota Incidence Algebras & Fast Poset Zeta/Möbius Transforms (`poset_zeta_transform`, `poset_mobius_transform`, `fast_zeta_transform`, `fast_mobius_transform`)**:
   Implements Rota's Zeta and Möbius inversion on general finite posets $(P, \le)$ and $O(n 2^n)$ Yates/SOS Fast Zeta and Möbius transforms on Boolean/subset lattices $2^{[n]}$, turning $O(4^n)$ join/meet convolutions into pointwise products.

---

## Motivation

1. **`PolynomialTruncationIdeal` Limitation Discovered in `EXP-0010`**:
   In `src/algebrax/algebra/_ideals.py`, `PolynomialTruncationIdeal` only accepts an integer `max_degree` (reducing modulo $x^d$). It cannot represent circular shift models $k[x]/\langle x^N - 1 \rangle$ (DFT), negacyclic models $k[x]/\langle x^N + 1 \rangle$ (DCT-IV / Ring-LWE), or Chebyshev boundary models $k[x]/\langle T_N(x) \rangle$ (DCT).
2. **IEEE-754 Float64 Corruption on Large Integer Convolutions ([`EXP-0010`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/README.md) Experiment 3)**:
   When convolving 9-digit integer polynomials modulo $p = 998244353$, `dft` and `idft` overflow IEEE-754's 53-bit precision ($2^{53} \approx 9 \times 10^{15}$) and corrupt **100% (7/7)** of the modular coefficients. An exact `ModularField(p)` Number-Theoretic Transform (`ntt` / `intt`) achieves **0/7 errors** using pure integer arithmetic.
3. **Missing Spectral Transform for `algebrax.lattice`**:
   While `algebrax.transforms` provides transforms for groups and rings, `algebrax.lattice` has no spectral transform to diagonalize join ($\vee$) or meet ($\wedge$) convolutions over posets and subset lattices.

---

## Rationale

Validated in [**EXP-0010**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/README.md) (Experiments 2, 3, and 5) and aligned with the Grand Council and **Phase 8.5 (`EP-0250`–`EP-0254`)**:

- **🧩 Bertrand Russell (Püschel–Moura Unification & Phase 8.5 Field/Quotient Soundness)**:
  Formalizes Püschel & Moura's theorem ([PUSCHEL-2006]): a linear signal model is simply a commutative polynomial quotient `CommQuotientRing` $k[x_1, \dots, x_n]/I$ (distinct from general non-commutative `QuotientRing` under [`EP-0250`](EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md)), its shift operator is the Stickelberger companion matrix $M_{x_i}$ from [`EP-0221`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md), and its spectral transform evaluates polynomials at the variety points $V(I)$ ($\mathbb{C}[x]/\langle x^N - 1 \rangle \to \text{DFT}$, $\mathbb{R}[x]/\langle T_N(x) \rangle \to \text{DCT}$ with `9.99e-16` node accuracy in `EXP-0010`). Exact NTT builds directly on `EP-0250`'s primality-checked `ModularField(p)` and irreducibility-validated `GaloisField`.
- **🔬 Karl Popper (Zero-Drift Bit-Exact NTT & Non-Vacuous Oracles)**:
  Eliminates floating-point approximation from modular and integer polynomial convolution via exact roots of unity $\omega \in \mathbb{F}_p^\times$. Verification routines follow `EP-0253`'s non-vacuous sample contracts (`_materialize_samples`, `NaN != NaN` equality guard).
- **⚡ Claude Shannon ($O(n 2^n)$ Fast Möbius Transform vs. $O(4^n)$ Naive Join Convolution)**:
  In `EXP-0010` Experiment 5, the Yates/SOS Fast Zeta and Möbius transforms achieved a **14.3x speedup** at $n = 9$ (`1.38 ms` vs. `19.82 ms`) with `0.00e+00` error. Exact rational/modular signal models align with `EP-0252`'s widened `typing.N` (`Fraction`) and parameterized `AlgebraicTrie` where prefix-indexed signal tables are used.
- **🛡️ The Golem (Defensive Transform & Lattice Bounds)**:
  Enforces `EP-0254`'s defensive boundary validation across `transforms.py` and `lattice.py` (`n > 0`, `n_bits >= 0`, non-negative index keys, safe lattice joins over signed weights, and public-only imports).
- **💡 Richard Feynman (The Freshman Test)**:
  *"Why does the Discrete Cosine Transform use cosines instead of complex exponentials? Because at the boundary of an image you reflect the signal instead of wrapping around a circle—so the shift operator obeys the Chebyshev polynomial $T_N(x) = 0$ instead of $x^N - 1 = 0$!"*

---

## Specification

### 1. `PolynomialModulusIdeal` & Püschel–Moura Signal Models (`src/algebrax/algebra/_ideals.py` & `src/algebrax/transforms.py`)

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from algebrax.algebra import CommQuotientRing, PolynomialAlgebra, PrincipalIdeal
from algebrax.typing import SparseMatrix, SparseVector

V = TypeVar("V")


class PolynomialModulusIdeal(PrincipalIdeal[dict[int, V]], Generic[V]):
    r"""Principal polynomial ideal $\langle P(x) \rangle \triangleleft k[x]$ reducing modulo a non-zero polynomial $P(x)$.

    Generalizes `PolynomialTruncationIdeal` from monomials $x^d$ to arbitrary shift polynomials
    ($x^N - 1$, $x^N + 1$, Chebyshev $T_N(x)$, cyclotomic $\Phi_n(x)$).
    """

    def __init__(self, ring: PolynomialAlgebra[V], modulus: dict[int, V]) -> None: ...
    @property
    def generator(self) -> dict[int, V]: ...
    def reduce(self, element: dict[int, V]) -> dict[int, V]: ...
    def contains(self, element: dict[int, V]) -> bool: ...


class AlgebraicSignalModel(Generic[V]):
    r"""Püschel–Moura Algebraic Signal Model $(\mathcal{A} = k[x]/\langle P(x) \rangle, M_x)$ (`EP-0221` bridge)."""

    def __init__(self, ring: PolynomialAlgebra[V], modulus: dict[int, V]) -> None:
        self.ideal = PolynomialModulusIdeal(ring, modulus)
        self.filter_algebra = CommQuotientRing(ring, self.ideal)

    def shift_matrix(self) -> SparseMatrix[int, V]:
        """Return the Stickelberger shift companion matrix M_x on basis {1, x, ..., x^{N-1}}."""
        ...

    def filter_signal(self, filter_poly: dict[int, V], signal: dict[int, V]) -> dict[int, V]:
        """Apply polynomial filter h(M_x) * s via CommQuotientRing multiplication."""
        return self.filter_algebra.mul(filter_poly, signal)


def dct(signal: SparseVector[int, float], n: int | None = None) -> dict[int, float]:
    r"""Compute the orthonormal Type-II Discrete Cosine Transform (DCT-II)."""
    ...


def idct(spectrum: SparseVector[int, float], n: int | None = None) -> dict[int, float]:
    r"""Compute the orthonormal Inverse Discrete Cosine Transform (DCT-III)."""
    ...
```

### 2. Exact Number-Theoretic Transforms over `ModularField(p)` (`src/algebrax/transforms.py`)

```python
def find_primitive_root_of_unity(prime: int, n: int) -> int:
    r"""Find an exact primitive $n$-th root of unity $\omega \in \mathbb{F}_p^\times$ (requires $n \mid (p - 1)$)."""
    ...


def ntt(
    signal: SparseVector[int, int],
    n: int,
    prime: int,
    omega: int | None = None,
) -> dict[int, int]:
    r"""Compute the exact Number-Theoretic Transform $X[k] = \sum_{j=0}^{n-1} x[j]\,\omega^{jk} \bmod p$."""
    ...


def intt(
    spectrum: SparseVector[int, int],
    n: int,
    prime: int,
    omega: int | None = None,
) -> dict[int, int]:
    r"""Compute the exact Inverse Number-Theoretic Transform $x[j] = n^{-1} \sum_{k=0}^{n-1} X[k]\,\omega^{-jk} \bmod p$."""
    ...


def ntt_convolve(
    a: SparseVector[int, int],
    b: SparseVector[int, int],
    n: int,
    prime: int = 998244353,
) -> dict[int, int]:
    r"""Compute exact cyclic convolution in $\mathbb{F}_p[x]/\langle x^n - 1 \rangle$ via NTT."""
    ...
```

### 3. Poset & Lattice Zeta / Möbius Harmonic Analysis (`src/algebrax/transforms.py` & `src/algebrax/lattice.py`)

```python
def fast_zeta_transform(
    signal: SparseVector[int, V],
    n_bits: int,
) -> dict[int, V]:
    r"""Compute the $O(n 2^n)$ Fast Zeta Transform $(Zf)(S) = \sum_{A \subseteq S} f(A)$ on Boolean lattice $2^{[n]}$."""
    ...


def fast_mobius_transform(
    zeta_spectrum: SparseVector[int, V],
    n_bits: int,
) -> dict[int, V]:
    r"""Compute the $O(n 2^n)$ Fast Möbius Transform $(\mu g)(S) = \sum_{A \subseteq S} (-1)^{|S \setminus A|} g(A)$."""
    ...


def lattice_join_convolve(
    f: SparseVector[int, V],
    g: SparseVector[int, V],
    n_bits: int,
) -> dict[int, V]:
    r"""Compute subset union (join) convolution $(f *_\vee g)(S) = \sum_{A \cup B = S} f(A)g(B)$ via FZT/FMT."""
    ...
```

### 4. Verification Oracles (`src/algebrax/verification/`)

Exported publicly via `algebrax.verification` (complying with Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts):

- `verify_ntt_laws(a, b, n, prime)`:
  1. Verifies `intt(ntt(a, n, prime), n, prime) == a`.
  2. Verifies `ntt_convolve(a, b, n, prime)` matches `CommQuotientRing(PolynomialAlgebra(ModularField(prime)), PolynomialModulusIdeal(..., x^n - 1)).mul(a, b)`.
- `verify_mobius_inversion_laws(f, g, n_bits)`:
  1. Verifies Rota inversion `fast_mobius_transform(fast_zeta_transform(f, n_bits), n_bits) == f`.
  2. Verifies join-convolution theorem `lattice_join_convolve(f, g, n_bits)` against direct subset union sum.

---

## Backwards Compatibility

100% backwards compatible. `PolynomialModulusIdeal` is a strict generalization alongside `PolynomialTruncationIdeal`, and `dct`, `idct`, `ntt`, `intt`, `fast_zeta_transform`, and `fast_mobius_transform` are additive exports in `algebrax.transforms`.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add sections in `docs/guide/transforms/spectral.md` covering Püschel–Moura polynomial signal models, exact modular NTT vs. floating-point FFT, and Rota Möbius inversion on lattices.
- **Recipe**: Add `recipes/exact_ntt_and_algebraic_signal_models.py` (and synced `.ipynb`).

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0010-generalized-harmonic-analysis/sources/prototype_harmonic_analysis.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0010-generalized-harmonic-analysis/sources/prototype_harmonic_analysis.py) (Experiments 2, 3, and 5).

---

## Rejected Ideas

1. **Using Float64 `dft` with Rounding for `ModularField(p)` Convolution**:
   - *Rejected*: Empirically falsified in `EXP-0010` Experiment 3 (7/7 coefficients corrupted at $p = 998244353$ due to 53-bit float64 overflow).

---

## Open Questions

- [ ] Adding multi-prime Chinese Remainder Theorem (`crt_ntt_convolve`) for arbitrary-precision $\mathbb{Z}[x]$ multiplication beyond a single 30-bit NTT prime.

---

## Change Log

* **2026-11-14:**
  * Initial Draft authored for Phase 10 from `EXP-0010`.
* **2026-11-26:**
  * Aligned with Phase 8.5 (`EP-0250`–`EP-0254`): switched private `algebra._*` imports to public `algebrax.algebra`, aligned `CommQuotientRing` and primality-checked `ModularField`/`GaloisField`, updated verification path to `src/algebrax/verification/`, and fixed user guide path to `docs/guide/transforms/spectral.md`.
