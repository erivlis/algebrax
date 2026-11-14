"""Executable Prototype & Empirical Benchmark Suite for EXP-0010: Generalized Harmonic Analysis.

Validates five foundational pillars of Generalized Harmonic Analysis in AlgebraX:
1. Experiment 1: Non-Abelian Group Fourier Transform (Peter-Weyl on S_3) vs. 1D Gelfand Character Collapse.
2. Experiment 2: Puschel-Moura Algebraic Signal Processing (Polynomial QuotientRing Shift Models -> DFT & Chebyshev DCT).
3. Experiment 3: Exact Finite-Field Number-Theoretic Transform (NTT over ModularField(p)) vs. Float64 FFT Drift.
4. Experiment 4: Graph & Hodge Simplicial Spectral Filtering via Fast Chebyshev Recurrence (Hammond-Vandergheynst-Gribonval).
5. Experiment 5: Poset & Lattice Harmonic Analysis (Rota Incidence Algebra & Fast Zeta/Mobius Transform on 2^[n]).
"""

from __future__ import annotations

import cmath
import math
import time
from typing import Any

import numpy as np

from algebrax.algebra import (
    ModularField,
    MonoidAlgebra,
    PolynomialAlgebra,
    PolynomialTruncationIdeal,
    QuotientRing,
    StandardField,
)
from algebrax.transforms import dft, gelfand_transform, idft

Perm = tuple[int, ...]
DenseMatrix = list[list[complex]]


def compose_perm(p: Perm, q: Perm) -> Perm:
    """Multiply permutations p * q: (p * q)(i) = p[q[i]]."""
    return tuple(p[q[i]] for i in range(len(p)))


def invert_perm(p: Perm) -> Perm:
    """Inverse permutation p^{-1}."""
    inv = [0] * len(p)
    for i, pi in enumerate(p):
        inv[pi] = i
    return tuple(inv)


def mat_add(a: DenseMatrix, b: DenseMatrix) -> DenseMatrix:
    d = len(a)
    return [[a[i][j] + b[i][j] for j in range(d)] for i in range(d)]


def mat_scale(scalar: complex, a: DenseMatrix) -> DenseMatrix:
    d = len(a)
    return [[scalar * a[i][j] for j in range(d)] for i in range(d)]


def mat_mul(a: DenseMatrix, b: DenseMatrix) -> DenseMatrix:
    d = len(a)
    return [[sum(a[i][k] * b[k][j] for k in range(d)) for j in range(d)] for i in range(d)]


def mat_trace(a: DenseMatrix) -> complex:
    return sum(a[i][i] for i in range(len(a)))


def mat_frob_norm_sq(a: DenseMatrix) -> float:
    return sum(abs(a[i][j]) ** 2 for i in range(len(a)) for j in range(len(a)))


# =============================================================================
# Experiment 1: Non-Abelian Group Fourier Transform on S_3 (Peter-Weyl)
# =============================================================================


def build_s3_irreps() -> tuple[list[Perm], dict[str, dict[Perm, DenseMatrix]]]:
    """Construct S_3 and its complete unitary irreducible representations (1 + 1 + 2)."""
    e: Perm = (0, 1, 2)
    t01: Perm = (1, 0, 2)
    t12: Perm = (0, 2, 1)
    t02: Perm = (2, 1, 0)
    c1: Perm = (1, 2, 0)
    c2: Perm = (2, 0, 1)
    s3 = [e, t01, t12, t02, c1, c2]

    # 1. Trivial irrep (dim 1)
    rho_triv = {g: [[1.0 + 0j]] for g in s3}

    # 2. Sign irrep (dim 1)
    rho_sign = {
        e: [[1.0 + 0j]],
        c1: [[1.0 + 0j]],
        c2: [[1.0 + 0j]],
        t01: [[-1.0 + 0j]],
        t12: [[-1.0 + 0j]],
        t02: [[-1.0 + 0j]],
    }

    # 3. Standard 2D orthogonal irrep (symmetries of equilateral triangle)
    s3_half = math.sqrt(3.0) / 2.0
    rho_std: dict[Perm, DenseMatrix] = {
        e: [[1.0, 0.0], [0.0, 1.0]],
        c1: [[-0.5, -s3_half], [s3_half, -0.5]],
        c2: [[-0.5, s3_half], [-s3_half, -0.5]],
        t01: [[-1.0, 0.0], [0.0, 1.0]],
        t12: [[0.5, s3_half], [s3_half, -0.5]],
        t02: [[0.5, -s3_half], [-s3_half, -0.5]],
    }

    return s3, {"triv": rho_triv, "sign": rho_sign, "std": rho_std}


def group_fourier_transform(
    signal: dict[Perm, complex],
    irreps: dict[str, dict[Perm, DenseMatrix]],
) -> dict[str, DenseMatrix]:
    r"""Non-Abelian Fourier Transform: \hat{f}(\rho) = \sum_{g \in G} f(g) \rho(g)."""
    hat: dict[str, DenseMatrix] = {}
    for name, rho in irreps.items():
        sample_mat = next(iter(rho.values()))
        d = len(sample_mat)
        acc: DenseMatrix = [[0j for _ in range(d)] for _ in range(d)]
        for g, val in signal.items():
            acc = mat_add(acc, mat_scale(val, rho[g]))
        hat[name] = acc
    return hat


def inverse_group_fourier_transform(
    hat: dict[str, DenseMatrix],
    group: list[Perm],
    irreps: dict[str, dict[Perm, DenseMatrix]],
) -> dict[Perm, complex]:
    r"""Peter-Weyl Inversion: f(g) = (1/|G|) \sum_\lambda d_\lambda Tr(\hat{f}(\rho_\lambda) \rho_\lambda(g^{-1}))."""
    order = len(group)
    reconstructed: dict[Perm, complex] = {}
    for g in group:
        g_inv = invert_perm(g)
        total = 0j
        for name, rho in irreps.items():
            d = len(hat[name])
            prod = mat_mul(hat[name], rho[g_inv])
            total += d * mat_trace(prod)
        val = total / order
        if abs(val) > 1e-12:
            reconstructed[g] = val
    return reconstructed


def run_experiment_1() -> None:
    print("=" * 80)
    print("EXPERIMENT 1: NON-ABELIAN PETER-WEYL FOURIER TRANSFORM vs. 1D GELFAND COLLAPSE")
    print("=" * 80)
    s3, irreps = build_s3_irreps()

    # Two distinct signals concentrated on different transpositions (1,0,2) vs (0,2,1)
    f1: dict[Perm, complex] = {(0, 1, 2): 1.0, (1, 0, 2): 2.0, (1, 2, 0): -0.5}
    f2: dict[Perm, complex] = {(0, 1, 2): 1.0, (0, 2, 1): 2.0, (1, 2, 0): -0.5}

    # 1D Scalar Characters (traces of irreps) used by gelfand_transform
    characters = {
        name: (lambda g, r=rho: mat_trace(r[g]))
        for name, rho in irreps.items()
    }
    gelfand_f1 = gelfand_transform(f1, characters)
    gelfand_f2 = gelfand_transform(f2, characters)
    print(f"Signal f1 != f2: {f1 != f2}")
    print(f"1D Gelfand character spectrum of f1: {gelfand_f1}")
    print(f"1D Gelfand character spectrum of f2: {gelfand_f2}")
    print(
        f"-> FALSE COLLISION (Gelfand(f1) == Gelfand(f2)): {gelfand_f1 == gelfand_f2} "
        "(1D characters cannot distinguish non-central group signals!)"
    )

    # Non-Abelian Matrix Fourier Transform
    hat_f1 = group_fourier_transform(f1, irreps)
    hat_f2 = group_fourier_transform(f2, irreps)
    rec_f1 = inverse_group_fourier_transform(hat_f1, s3, irreps)
    max_inv_err = max(abs(f1.get(g, 0j) - rec_f1.get(g, 0j)) for g in s3)
    print(f"Peter-Weyl Matrix FT separates f1 and f2: {hat_f1['std'] != hat_f2['std']}")
    print(f"Peter-Weyl Inversion max error ||f1 - IFT(FT(f1))||_inf: {max_inv_err:.2e}")

    # Convolution Theorem over MonoidAlgebra(S_3)
    group_alg = MonoidAlgebra(StandardField(complex), key_op=compose_perm, zero_key=(0, 1, 2))
    conv_direct = group_alg.mul(f1, f2)
    hat_conv = {name: mat_mul(hat_f1[name], hat_f2[name]) for name in irreps}
    conv_spectral = inverse_group_fourier_transform(hat_conv, s3, irreps)
    max_conv_err = max(abs(conv_direct.get(g, 0j) - conv_spectral.get(g, 0j)) for g in s3)
    print(f"Non-Abelian Convolution Theorem max error: {max_conv_err:.2e}")

    # Plancherel / Parseval Identity
    lhs_energy = sum(abs(v) ** 2 for v in f1.values())
    rhs_energy = sum(len(hat_f1[name]) * mat_frob_norm_sq(hat_f1[name]) for name in irreps) / len(s3)
    print(f"Plancherel Energy: spatial={lhs_energy:.6f}, spectral={rhs_energy:.6f}, diff={abs(lhs_energy - rhs_energy):.2e}")

    # Diaconis random transposition walk convergence to uniform distribution on S_3
    # Walk: stay at identity with prob 1/4, or apply one of 3 transpositions with prob 1/4 each
    walk_step: dict[Perm, complex] = {
        (0, 1, 2): 0.25,
        (1, 0, 2): 0.25,
        (0, 2, 1): 0.25,
        (2, 1, 0): 0.25,
    }
    hat_walk = group_fourier_transform(walk_step, irreps)
    # 8 steps via matrix powers in Fourier space
    hat_walk_8: dict[str, DenseMatrix] = {}
    for name, m in hat_walk.items():
        acc = m
        for _ in range(7):
            acc = mat_mul(acc, m)
        hat_walk_8[name] = acc
    dist_8 = inverse_group_fourier_transform(hat_walk_8, s3, irreps)
    tv_dist = 0.5 * sum(abs(dist_8.get(g, 0j).real - 1.0 / 6.0) for g in s3)
    print(f"Diaconis Transposition Walk (k=8 steps) Total Variation distance to Uniform: {tv_dist:.2e}")
    print()


# =============================================================================
# Experiment 2: Puschel-Moura Algebraic Signal Processing (QuotientRing Models)
# =============================================================================


class UnivariateModulusIdeal:
    """Principal polynomial ideal <P(x)> in k[x] reducing modulo an arbitrary monic polynomial P(x)."""

    def __init__(self, ring: PolynomialAlgebra[complex], modulus: dict[int, complex]) -> None:
        self.ring = ring
        self.modulus = dict(modulus)
        self.deg_m = max(modulus.keys())
        self.lc_m = modulus[self.deg_m]

    @property
    def generator(self) -> dict[int, complex]:
        return self.modulus

    def reduce(self, poly: dict[int, complex]) -> dict[int, complex]:
        rem = {k: v for k, v in poly.items() if abs(v) > 1e-14}
        while rem:
            deg_r = max(rem.keys())
            if deg_r < self.deg_m:
                break
            factor = rem[deg_r] / self.lc_m
            shift = deg_r - self.deg_m
            for k, v in self.modulus.items():
                target = k + shift
                new_val = rem.get(target, 0j) - factor * v
                if abs(new_val) <= 1e-14:
                    rem.pop(target, None)
                else:
                    rem[target] = new_val
        return rem

    def contains(self, poly: dict[int, complex]) -> bool:
        return len(self.reduce(poly)) == 0


def run_experiment_2() -> None:
    print("=" * 80)
    print("EXPERIMENT 2: PUSCHEL-MOURA ALGEBRAIC SIGNAL PROCESSING (QUOTIENT RING MODELS)")
    print("=" * 80)
    field = StandardField(complex)
    poly_ring = PolynomialAlgebra(field)

    # Model A: Circular Shift Algebra C[x] / <x^4 - 1> -> DFT
    n = 4
    mod_dft = {0: -1.0 + 0j, n: 1.0 + 0j}  # x^4 - 1
    ideal_dft = UnivariateModulusIdeal(poly_ring, mod_dft)
    quot_dft = QuotientRing(poly_ring, ideal_dft)

    sig_a = {0: 1.0 + 0j, 1: 2.0 + 0j, 2: -1.0 + 0j, 3: 0.5 + 0j}
    sig_b = {0: 0.5 + 0j, 1: -1.0 + 0j, 2: 1.5 + 0j}

    # Filter multiplication in C[x]/<x^4 - 1> vs spectral DFT pointwise product
    prod_quot = quot_dft.mul(sig_a, sig_b)
    dft_a = dft(sig_a, n)
    dft_b = dft(sig_b, n)
    dft_prod = {k: dft_a.get(k, 0j) * dft_b.get(k, 0j) for k in range(n)}
    idft_prod = idft(dft_prod, n)
    dft_err = max(abs(prod_quot.get(k, 0j) - idft_prod.get(k, 0j)) for k in range(n))
    print(f"Model A (C[x]/<x^4 - 1> <-> DFT): QuotientRing.mul vs IDFT(DFT(a)*DFT(b)) error = {dft_err:.2e}")

    # Model B: Chebyshev Polynomial Algebra R[x] / <T_4(x)> -> DCT
    # T_4(x) = 8 x^4 - 8 x^2 + 1 => monic x^4 - x^2 + 1/8
    mod_cheb = {0: 0.125 + 0j, 2: -1.0 + 0j, 4: 1.0 + 0j}
    ideal_cheb = UnivariateModulusIdeal(poly_ring, mod_cheb)
    quot_cheb = QuotientRing(poly_ring, ideal_cheb)

    # Build Stickelberger shift companion matrix M_x on basis {1, x, x^2, x^3}
    m_x = np.zeros((n, n), dtype=float)
    x_poly = {1: 1.0 + 0j}
    for col in range(n):
        basis_vec = {col: 1.0 + 0j}
        shifted = quot_cheb.mul(x_poly, basis_vec)
        for row, val in shifted.items():
            m_x[row, col] = val.real

    eigvals = sorted(np.linalg.eigvals(m_x).real)
    cheb_nodes = sorted(math.cos((2 * k + 1) * math.pi / (2 * n)) for k in range(n))
    node_err = max(abs(a - b) for a, b in zip(eigvals, cheb_nodes, strict=True))
    print(f"Model B (R[x]/<T_4(x)> <-> DCT): Stickelberger eigenvalues = {[round(v, 6) for v in eigvals]}")
    print(f"Exact Chebyshev DCT nodes cos((2k+1)pi/8)               = {[round(v, 6) for v in cheb_nodes]}")
    print(f"Max eigenvalue vs Chebyshev DCT node error: {node_err:.2e}")
    print()


# =============================================================================
# Experiment 3: Exact Finite-Field Number-Theoretic Transform (NTT) vs Float64
# =============================================================================


def find_primitive_nth_root(p: int, n: int) -> int:
    """Find a primitive n-th root of unity in F_p^* (requires n | (p - 1))."""
    assert (p - 1) % n == 0
    # Find generator g of F_p^*
    phi = p - 1
    factors: list[int] = []
    temp = phi
    d = 2
    while d * d <= temp:
        if temp % d == 0:
            factors.append(d)
            while temp % d == 0:
                temp //= d
        d += 1
    if temp > 1:
        factors.append(temp)

    for g in range(2, p):
        if all(pow(g, phi // q, p) != 1 for q in factors):
            return pow(g, phi // n, p)
    raise ValueError("No primitive root found.")


def ntt(signal: dict[int, int], n: int, p: int, omega: int) -> dict[int, int]:
    """Exact Number-Theoretic Transform over ModularField(p)."""
    field = ModularField(p)
    out: dict[int, int] = {}
    for k in range(n):
        acc = 0
        w_k = pow(omega, k, p)
        for j, val in signal.items():
            term = field.mul(val % p, pow(w_k, j, p))
            acc = field.add(acc, term)
        if acc != 0:
            out[k] = acc
    return out


def intt(spectrum: dict[int, int], n: int, p: int, omega: int) -> dict[int, int]:
    """Exact Inverse Number-Theoretic Transform over ModularField(p)."""
    field = ModularField(p)
    omega_inv = field.inv(omega)
    n_inv = field.inv(n % p)
    raw = ntt(spectrum, n, p, omega_inv)
    return {j: field.mul(val, n_inv) for j, val in raw.items() if field.mul(val, n_inv) != 0}


def run_experiment_3() -> None:
    print("=" * 80)
    print("EXPERIMENT 3: EXACT FINITE-FIELD NTT (ModularField) vs. FLOAT64 DFT DRIFT")
    print("=" * 80)
    # Prime p = 998244353 = 119 * 2^23 + 1 (canonical NTT prime)
    p = 998244353
    n = 8
    omega = find_primitive_nth_root(p, n)
    field = ModularField(p)

    # Large integer signals whose product exceeds IEEE-754 float64 53-bit exact integer precision (2^53 ~ 9e15)
    a = {0: 812345678, 1: 923456789, 2: 734567891, 3: 645678912}
    b = {0: 987654321, 1: 876543219, 2: 765432198, 3: 654321987}

    # Exact cyclic convolution in Z[x]/<x^8 - 1>
    exact_int_conv: dict[int, int] = {}
    for i, va in a.items():
        for j, vb in b.items():
            idx = (i + j) % n
            exact_int_conv[idx] = exact_int_conv.get(idx, 0) + va * vb
    exact_mod_p = {k: v % p for k, v in exact_int_conv.items()}

    # Float64 DFT/IDFT convolution
    dft_a = dft({k: float(v) for k, v in a.items()}, n)
    dft_b = dft({k: float(v) for k, v in b.items()}, n)
    float_conv = idft({k: dft_a.get(k, 0j) * dft_b.get(k, 0j) for k in range(n)}, n)
    float_rounded_mod_p = {k: int(round(float_conv.get(k, 0j).real)) % p for k in exact_int_conv}
    float_mismatches = sum(1 for k in exact_mod_p if float_rounded_mod_p[k] != exact_mod_p[k])

    # Exact NTT convolution over ModularField(p)
    ntt_a = ntt(a, n, p, omega)
    ntt_b = ntt(b, n, p, omega)
    ntt_prod = {k: field.mul(ntt_a.get(k, 0), ntt_b.get(k, 0)) for k in range(n)}
    ntt_conv = intt(ntt_prod, n, p, omega)
    ntt_mismatches = sum(1 for k in exact_mod_p if ntt_conv.get(k, 0) != exact_mod_p[k])

    print(f"NTT Prime p = {p}, N = {n}, primitive {n}-th root omega = {omega}")
    print(f"Float64 DFT/IDFT wrong modular coefficients: {float_mismatches}/{len(exact_mod_p)} (53-bit precision overflow!)")
    print(f"Exact ModularField(p) NTT wrong coefficients: {ntt_mismatches}/{len(exact_mod_p)} (100% bit-exact!)")
    print()


# =============================================================================
# Experiment 4: Spectral Graph & Hodge Wavelets via Fast Chebyshev Polynomials
# =============================================================================


def chebyshev_spectral_filter(
    laplacian: np.ndarray,
    signal: np.ndarray,
    kernel_fn: Any,
    lambda_max: float,
    order: int = 12,
) -> np.ndarray:
    """Fast Hammond-Vandergheynst-Gribonval Chebyshev polynomial spectral filter g(L) * signal."""
    # Rescale spectrum [0, lambda_max] -> [-1, 1]: L_tilde = (2 / lambda_max) * L - I
    n = laplacian.shape[0]
    ident = np.eye(n)
    l_tilde = (2.0 / lambda_max) * laplacian - ident

    # Compute Chebyshev expansion coefficients c_k via Gauss-Chebyshev quadrature
    m_quad = order + 1
    c = np.zeros(order + 1)
    for k in range(order + 1):
        acc = 0.0
        for j in range(1, m_quad + 1):
            theta_j = math.pi * (j - 0.5) / m_quad
            x_j = math.cos(theta_j)
            # Map [-1, 1] back to [0, lambda_max]
            lam_j = 0.5 * lambda_max * (x_j + 1.0)
            acc += kernel_fn(lam_j) * math.cos(k * theta_j)
        c[k] = (2.0 / m_quad) * acc

    # Clenshaw / 3-term Chebyshev recurrence using ONLY matrix-vector products
    t_prev = signal.copy()
    t_curr = l_tilde @ signal
    result = 0.5 * c[0] * t_prev + c[1] * t_curr
    for k in range(2, order + 1):
        t_next = 2.0 * (l_tilde @ t_curr) - t_prev
        result = result + c[k] * t_next
        t_prev, t_curr = t_curr, t_next
    return result


def run_experiment_4() -> None:
    print("=" * 80)
    print("EXPERIMENT 4: GRAPH & HODGE SPECTRAL WAVELETS VIA FAST CHEBYSHEV RECURRENCE")
    print("=" * 80)
    # 1. Cycle graph C_64 heat/wavelet filtering: Exact Eigendecomposition vs Chebyshev K=14
    n = 64
    lap = np.zeros((n, n))
    for i in range(n):
        lap[i, i] = 2.0
        lap[i, (i - 1) % n] = -1.0
        lap[i, (i + 1) % n] = -1.0

    signal = np.zeros(n)
    signal[0] = 1.0  # Dirac impulse at vertex 0
    kernel = lambda lam: lam * math.exp(-1.5 * lam)  # Mexican-hat spectral graph wavelet

    t0 = time.perf_counter()
    eigvals, eigvecs = np.linalg.eigh(lap)
    exact_filtered = eigvecs @ (np.array([kernel(v) for v in eigvals]) * (eigvecs.T @ signal))
    t_eig = (time.perf_counter() - t0) * 1e3

    t0 = time.perf_counter()
    cheb_filtered = chebyshev_spectral_filter(lap, signal, kernel, lambda_max=4.0, order=14)
    t_cheb = (time.perf_counter() - t0) * 1e3

    rel_err = np.linalg.norm(exact_filtered - cheb_filtered) / np.linalg.norm(exact_filtered)
    print(
        f"Spectral Graph Wavelet (N={n}, K=14): Chebyshev rel_error = {rel_err:.2e} "
        f"(Eig={t_eig:.2f}ms, Cheb={t_cheb:.2f}ms)"
    )

    # 2. Simplicial Hodge 1-Laplacian L_1 = B_1^T B_1 + B_2 B_2^T on a 4-vertex square with 1 filled triangle
    # Vertices: 0,1,2,3; Edges: e0=(0,1), e1=(1,2), e2=(2,3), e3=(0,3), e4=(0,2); Face: f0=(0,1,2)
    b1 = np.array(
        [
            [-1, 0, 0, -1, -1],
            [1, -1, 0, 0, 0],
            [0, 1, -1, 0, 1],
            [0, 0, 1, 1, 0],
        ],
        dtype=float,
    )
    b2 = np.array([[1], [1], [0], [0], [-1]], dtype=float)
    l1_down = b1.T @ b1
    l1_up = b2 @ b2.T
    l1 = l1_down + l1_up

    # Harmonic projector via low-pass Chebyshev filter (1 - L_1 / lambda_max)^K or exact eigenspace
    evals_1, evecs_1 = np.linalg.eigh(l1)
    harm_mask = np.abs(evals_1) < 1e-9
    edge_flow = np.array([1.0, 1.0, -1.0, 1.0, 0.5])
    f_harm = evecs_1[:, harm_mask] @ (evecs_1[:, harm_mask].T @ edge_flow)
    print(
        f"Hodge 1-Laplacian Spectral Decomposition (Betti b_1 = {int(np.sum(harm_mask))}): "
        f"||L_1 f_harm|| = {np.linalg.norm(l1 @ f_harm):.2e}"
    )
    print()


# =============================================================================
# Experiment 5: Poset & Lattice Harmonic Analysis (Fast Zeta / Mobius Transform)
# =============================================================================


def fast_zeta_transform(vec: list[float], n_bits: int) -> list[float]:
    """O(n 2^n) Fast Zeta Transform (Sum Over Subsets) on Boolean Lattice 2^[n]."""
    out = list(vec)
    for i in range(n_bits):
        bit = 1 << i
        for mask in range(1 << n_bits):
            if mask & bit:
                out[mask] += out[mask ^ bit]
    return out


def fast_mobius_transform(vec: list[float], n_bits: int) -> list[float]:
    """O(n 2^n) Fast Mobius Transform (Inclusion-Exclusion Inverse) on Boolean Lattice 2^[n]."""
    out = list(vec)
    for i in range(n_bits):
        bit = 1 << i
        for mask in range(1 << n_bits):
            if mask & bit:
                out[mask] -= out[mask ^ bit]
    return out


def run_experiment_5() -> None:
    print("=" * 80)
    print("EXPERIMENT 5: LATTICE HARMONIC ANALYSIS (ROTA FAST ZETA / MOBIUS TRANSFORM)")
    print("=" * 80)
    n_bits = 9  # 2^9 = 512 lattice elements
    size = 1 << n_bits
    f = [float((i * 17 + 3) % 11) for i in range(size)]
    g = [float((i * 7 + 5) % 13) for i in range(size)]

    # 1. Naive Join Convolution: (f *_{join} g)(S) = \sum_{A | B == S} f(A) g(B)
    t0 = time.perf_counter()
    naive_conv = [0.0] * size
    for a in range(size):
        fa = f[a]
        for b in range(size):
            naive_conv[a | b] += fa * g[b]
    t_naive = (time.perf_counter() - t0) * 1e3

    # 2. Spectral Lattice Convolution via FZT + Pointwise Product + FMT
    t0 = time.perf_counter()
    zf = fast_zeta_transform(f, n_bits)
    zg = fast_zeta_transform(g, n_bits)
    z_prod = [zf[i] * zg[i] for i in range(size)]
    fast_conv = fast_mobius_transform(z_prod, n_bits)
    t_fast = (time.perf_counter() - t0) * 1e3

    max_err = max(abs(naive_conv[i] - fast_conv[i]) for i in range(size))
    rec_f = fast_mobius_transform(zf, n_bits)
    inv_err = max(abs(f[i] - rec_f[i]) for i in range(size))

    print(f"Boolean Lattice 2^[{n_bits}] ({size} elements):")
    print(f"  Rota Mobius Inversion error ||f - FMT(FZT(f))||_inf: {inv_err:.2e}")
    print(f"  Join-Convolution error ||Naive - Spectral||_inf:     {max_err:.2e}")
    print(f"  Runtime: Naive O(4^n) = {t_naive:.2f} ms vs. Fast Mobius O(n 2^n) = {t_fast:.2f} ms ({t_naive / t_fast:.1f}x speedup!)")
    print()


if __name__ == "__main__":
    run_experiment_1()
    run_experiment_2()
    run_experiment_3()
    run_experiment_4()
    run_experiment_5()
