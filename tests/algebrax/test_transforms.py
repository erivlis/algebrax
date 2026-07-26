import pytest

from algebrax.transforms import (
    convolve,
    dft,
    gelfand_transform,
    hilbert,
    idft,
    legendre_fenchel,
    lorentz_boost,
    permute_tensor,
    walsh_hadamard,
    z_transform,
)


def test_convolve():
    from algebrax.semiring import TropicalSemiring

    # Standard polynomial-style convolution (default key_op: x + y)
    f = {0: 1, 1: 2}
    g = {0: 1, 1: 1}
    h = convolve(f, g)
    assert h == {0: 1, 1: 3, 2: 2}

    # Custom key_op (e.g. string concatenation)
    f_str = {'a': 2, 'b': 3}
    g_str = {'x': 1, 'y': 4}
    h_str = convolve(f_str, g_str, key_op=lambda k1, k2: k1 + k2)
    assert h_str == {'ax': 2, 'ay': 8, 'bx': 3, 'by': 12}

    # Group / modular key_op with TropicalSemiring (Min-Plus)
    # f[x] + g[y] combined via min
    h_trop = convolve(f, g, semiring=TropicalSemiring())
    # 0+0=0 (1+1=2), 0+1=1 (1+1=2), 1+0=1 (2+1=3), 1+1=2 (2+1=3)
    # min at 0: 2
    # min at 1: min(2, 3) = 2
    # min at 2: 3
    assert h_trop == {0: 2.0, 1: 2.0, 2: 3.0}


def test_dft_idft():
    # Impulse [1, 0, 0, 0] -> Spectrum [1, 1, 1, 1]
    sig = {0: 1}
    spec = dft(sig, n=4)
    assert len(spec) == 4
    for k in range(4):
        assert spec[k] == 1 + 0j

    recon = idft(spec, n=4)
    assert recon[0].real == pytest.approx(1.0)
    assert abs(recon.get(1, 0)) < 1e-9


def test_dft_empty():
    assert dft({}) == {}
    assert idft({}) == {}


def test_hilbert():
    # Impulse -> Analytic Signal
    # sig = [1, 0, 0, 0]
    # Analytic = [1, 0.5j, 0, -0.5j] (approx)
    # Real part is original signal. Imaginary part is Hilbert transform.
    # H(delta) = 1/pi*t (discrete version is cot(pi*t/2) or similar)

    sig = {0: 1}
    h = hilbert(sig, n=4)

    # n=0: Should be 1+0j (Original signal is 1, H(0)=0)
    assert h[0] == 1 + 0j

    # n=1: Should be 0 + 0.5j
    # Calculation: 1/4 * (1 + 2j - 1) = 0.5j
    assert h[1] == pytest.approx(0.5j)


def test_hilbert_empty():
    assert hilbert({}) == {}


def test_z_transform():
    from algebrax.semiring import ArcticSemiring, StandardSemiring, TropicalSemiring

    # Standard Z-transform (no semiring / StandardSemiring)
    # X(z) = sum_{n=0}^{inf} x[n] * z^-n
    # sig = {0: 1, 1: 2} at z=2
    # 1 + 2*(1/2) = 2.0
    sig = {0: 1.0, 1: 2.0}
    val = z_transform(sig, z=2.0)
    assert val == pytest.approx(2.0)

    val_std = z_transform(sig, z=2.0, semiring=StandardSemiring())
    assert val_std == pytest.approx(2.0)

    # Tropical Z-transform (Min-Plus semiring)
    # X(z) = min_n (x[n] - n * z)
    # sig = {0: 5.0, 1: 3.0} at z=1.0
    # n=0: 5.0 - 0*1.0 = 5.0
    # n=1: 3.0 - 1*1.0 = 2.0
    # min(5.0, 2.0) = 2.0
    sig_trop = {0: 5.0, 1: 3.0}
    val_trop = z_transform(sig_trop, z=1.0, semiring=TropicalSemiring())
    assert val_trop == 2.0

    # Arctic Z-transform (Max-Plus semiring)
    # X(z) = max_n (x[n] - n * z)
    # sig = {0: 5.0, 1: 3.0} at z=1.0
    # n=0: 5.0 - 0*1.0 = 5.0
    # n=1: 3.0 - 1*1.0 = 2.0
    # max(5.0, 2.0) = 5.0
    val_arc = z_transform(sig_trop, z=1.0, semiring=ArcticSemiring())
    assert val_arc == 5.0


def test_walsh_hadamard_transform():
    # Size 2 WHT:
    # H = [[1, 1], [1, -1]]
    # x = [4, 2]
    # H * x = [6, 2]
    sig = {0: 4.0, 1: 2.0}
    out = walsh_hadamard(sig, n=2)
    assert out[0] == pytest.approx(6.0)
    assert out[1] == pytest.approx(2.0)

    # Size 4 WHT:
    # H = [[1, 1, 1, 1], [1, -1, 1, -1], [1, 1, -1, -1], [1, -1, -1, 1]]
    # x = [1, 0, 1, 0]
    # H * x = [2, 2, 0, 0] (0 elements should be omitted to maintain sparsity)
    sig2 = {0: 1.0, 2: 1.0}
    out2 = walsh_hadamard(sig2, n=4)
    assert out2[0] == pytest.approx(2.0)
    assert out2[1] == pytest.approx(2.0)
    assert 2 not in out2
    assert 3 not in out2

    # Error for non-power-of-2 size
    with pytest.raises(ValueError):
        walsh_hadamard(sig2, n=3)


def test_lorentz():
    # Rest frame (t=1, x=0)
    # Boost beta=0.6 (gamma=1.25)
    # t' = 1.25 * (1 - 0) = 1.25
    # x' = 1.25 * (0 - 0.6*1) = -0.75
    vec = {0: 1.0, 1: 0.0}
    boosted = lorentz_boost(vec, beta=0.6)
    assert boosted[0] == pytest.approx(1.25)
    assert boosted[1] == pytest.approx(-0.75)


def test_lorentz_invalid_beta():
    with pytest.raises(ValueError):
        lorentz_boost({}, beta=1.0)


def test_lorentz_sparse_removal():
    # If result is 0, key should be removed
    # t=0, x=0 -> t'=0, x'=0. Result should be empty.
    vec = {0: 0.0, 1: 0.0}
    boosted = lorentz_boost(vec, beta=0.5)
    assert 0 not in boosted
    assert 1 not in boosted


def test_lorentz_cancellation():
    # Test exact cancellation of components
    # t' = gamma * (t - beta * x)
    # x' = gamma * (x - beta * t)

    # Case 1: t' becomes 0
    # Let beta = 0.5. gamma = 1.1547
    # We need t = beta * x. Let x = 2, t = 1.
    # t' = gamma * (1 - 0.5 * 2) = 0
    # x' = gamma * (2 - 0.5 * 1) = gamma * 1.5 != 0
    vec = {0: 1.0, 1: 2.0}
    boosted = lorentz_boost(vec, beta=0.5)
    assert 0 not in boosted
    assert 1 in boosted

    # Case 2: x' becomes 0
    # We need x = beta * t. Let t = 2, x = 1.
    # x' = gamma * (1 - 0.5 * 2) = 0
    # t' = gamma * (2 - 0.5 * 1) = gamma * 1.5 != 0
    vec2 = {0: 2.0, 1: 1.0}
    boosted2 = lorentz_boost(vec2, beta=0.5)
    assert 1 not in boosted2
    assert 0 in boosted2


def test_lorentz_cancellation_missing_key():
    # Test cancellation when the key was NOT in the original vector
    # This hits the 'elif 0 in result' -> False branch
    vec = {}
    boosted = lorentz_boost(vec, beta=0.5)
    assert 0 not in boosted
    assert 1 not in boosted


def test_permute_tensor():
    # Tensor T[x, y, z]
    # T[0, 1, 2] = 5
    t = {(0, 1, 2): 5}

    # Permute to [z, x, y] -> (2, 0, 1)
    # New key should be (2, 0, 1)
    p = permute_tensor(t, (2, 0, 1))
    assert p == {(2, 0, 1): 5}


def test_legendre_fenchel_transform():
    from algebrax.semiring import ArcticSemiring, StandardSemiring, TropicalSemiring

    # f(x) = x^2
    signal = {0: 0.0, 1: 1.0, 2: 4.0, 3: 9.0}

    # Standard / None semiring (fallback)
    # f*(s) = sup_x (s*x - f(x))
    # s = 2: max(2*0-0, 2*1-1, 2*2-4, 2*3-9) = max(0, 1, 0, -3) = 1.0
    val_none = legendre_fenchel(signal, slope=2.0)
    assert val_none == pytest.approx(1.0)

    val_std = legendre_fenchel(signal, slope=2.0, semiring=StandardSemiring())
    assert val_std == pytest.approx(1.0)

    # Tropical (Min-Plus):
    # f*(s) = min_x (s + x - f(x))
    # s = 2: min(2+0-0, 2+1-1, 2+2-4, 2+3-9) = min(2, 2, 0, -4) = -4.0
    val_trop = legendre_fenchel(signal, slope=2.0, semiring=TropicalSemiring())
    assert val_trop == pytest.approx(-4.0)

    # Arctic (Max-Plus):
    # f*(s) = max_x (s + x - f(x))
    # s = 2: max(2+0-0, 2+1-1, 2+2-4, 2+3-9) = max(2, 2, 0, -4) = 2.0
    val_arc = legendre_fenchel(signal, slope=2.0, semiring=ArcticSemiring())
    assert val_arc == pytest.approx(2.0)


def test_gelfand_transform():
    from algebrax.semiring import TropicalSemiring

    # Cyclic group of order 2 characters (standard field):
    # chi_0(x) = 1
    # chi_1(x) = (-1)^x
    signal = {0: 1.0, 1: 2.0}
    characters = {
        'chi_0': lambda x: 1.0,
        'chi_1': lambda x: -1.0 if x % 2 == 1 else 1.0,
    }

    out = gelfand_transform(signal, characters)
    assert out['chi_0'] == pytest.approx(3.0)
    assert out['chi_1'] == pytest.approx(-1.0)

    # Tropical Gelfand transform (Min-Plus semiring):
    # Signal: {0: 5.0, 1: 3.0}
    # chi_0(x) = 0.0
    # chi_1(x) = 2.0 * x
    signal_trop = {0: 5.0, 1: 3.0}
    characters_trop = {
        'chi_0': lambda x: 0.0,
        'chi_1': lambda x: 2.0 * x,
    }

    out_trop = gelfand_transform(signal_trop, characters_trop, semiring=TropicalSemiring())
    assert out_trop['chi_0'] == 3.0
    assert out_trop['chi_1'] == 5.0

    # Empty inputs
    assert gelfand_transform({}, characters) == {}
    assert gelfand_transform(signal, {}) == {}


def test_convolve_empty():
    assert convolve({}, {}) == {}


def test_dft_threshold():
    sig = {0: 1e-10}
    assert dft(sig) == {}


def test_idft_threshold():
    spec = {0: 1e-10}
    assert idft(spec) == {}


def test_hilbert_threshold():
    sig = {0: 1e-10}
    assert hilbert(sig) == {}


def test_lorentz_zero_result():
    vec = {0: 0.0, 1: 0.0}
    res = lorentz_boost(vec, beta=0.5)
    assert res == {}


def test_z_transform_negative_n():
    sig = {-1: 1}
    assert z_transform(sig, 1) == 0j


def test_z_transform_mixed_n():
    sig = {-1: 1, 0: 1}
    assert z_transform(sig, 1) == pytest.approx(1.0)


def test_z_transform_empty():
    assert z_transform({}, 1) == 0j


def test_transforms_edge_cases():
    from algebrax.semiring import StandardSemiring, TropicalSemiring

    assert legendre_fenchel({}, slope=2.0, semiring=TropicalSemiring()) == float('inf')
    assert legendre_fenchel({'non_num': 1}, slope=2.0) == float('-inf')
    assert legendre_fenchel({1: 2.0}, slope=2.0, semiring=TropicalSemiring()) == 1.0

    assert walsh_hadamard({}) == {}
    assert walsh_hadamard({1: 2.0}) == {0: 2.0, 1: -2.0}
    with pytest.raises(ValueError, match='power of 2'):
        walsh_hadamard({1: 2.0}, n=3)

    signal = {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0}
    freq = dft(signal, n=4)
    rec = idft(freq, n=4)
    assert rec[0] == pytest.approx(1.0)

    h = hilbert(signal, n=4)
    assert len(h) == 4

    v = {0: 1.0, 1: 0.0}
    v_boosted = lorentz_boost(v, beta=0.5)
    assert 0 in v_boosted
    assert 1 in v_boosted

    tensor = {(0, 1): 5.0, (1, 2): 10.0}
    permuted = permute_tensor(tensor, permutation=(1, 0))
    assert permuted == {(1, 0): 5.0, (2, 1): 10.0}

    f = {'a': 2.0, 'b': 3.0}
    characters = {'c1': lambda k: 1.0, 'c2': lambda k: -1.0 if k == 'b' else 1.0}
    gt = gelfand_transform(f, characters)
    assert len(gt) == 2

    gt_semiring = gelfand_transform(f, characters, semiring=TropicalSemiring())
    assert len(gt_semiring) == 2

    assert z_transform({}, z=1.0, semiring=TropicalSemiring()) == float('inf')
    z_res = z_transform(signal, z=2.0)
    assert isinstance(z_res, (int, float, complex))
    z_res_trop = z_transform({1: 2.0, 2: 3.0}, z=1.0, semiring=TropicalSemiring())
    assert z_res_trop == 1.0

    lf = legendre_fenchel({1: 2.0}, slope=2.0, semiring=StandardSemiring(float))
    assert lf == pytest.approx(0.0)

    gt_zero = gelfand_transform({'a': 1.0}, {'c1': lambda k: 0.0}, semiring=StandardSemiring(float))
    assert gt_zero == {}

    zt_std = z_transform({1: 2.0}, z=2.0, semiring=StandardSemiring(float))
    assert zt_std == pytest.approx(1.0)


def test_transforms_branch_coverage():
    from algebrax.semiring import BooleanSemiring, Semiring, StandardSemiring, TropicalSemiring
    from algebrax.transforms import gelfand_transform, legendre_fenchel, z_transform

    assert legendre_fenchel({}, slope=2.0) == float('-inf')
    assert legendre_fenchel({'non_num': 1}, slope=2.0, semiring=BooleanSemiring()) is False

    class NonFloat:
        def __mul__(self, other):
            return self

        def __rmul__(self, other):
            return self

        def __radd__(self, other):
            return self

        def __abs__(self):
            raise TypeError()

        def __eq__(self, other):
            return True

    gt_nonfloat = gelfand_transform({'a': 1}, {'c': lambda k: NonFloat()}, semiring=StandardSemiring())
    assert gt_nonfloat == {}

    gt_zero = gelfand_transform({'a': True}, {'c': lambda k: False}, semiring=BooleanSemiring())
    assert gt_zero == {}

    class CustomSlopeSemiring(Semiring[float]):
        @property
        def zero(self):
            return 0.0

        @property
        def one(self):
            return 1.0

        def add(self, a, b):
            return a + b

        def mul(self, a, b):
            if isinstance(b, int):
                raise TypeError()
            if b == 0.5:
                raise TypeError()
            return float(a) * float(b)

        def power(self, a, n):
            raise RuntimeError()

    assert legendre_fenchel({1: 2.0}, slope=2.0, semiring=CustomSlopeSemiring()) == 0.0
    assert z_transform({1: 2.0}, z=2.0, semiring=CustomSlopeSemiring()) == pytest.approx(1.0)

    class NonDivisibleZSemiring(Semiring[str]):
        @property
        def zero(self):
            return ''

        @property
        def one(self):
            return '1'

        def add(self, a, b):
            return a + b

        def mul(self, a, b):
            return a + b

    assert z_transform({1: 'a'}, z='z', semiring=NonDivisibleZSemiring()) == 'a1z'
    assert z_transform({-1: 1.0}, z=2.0, semiring=TropicalSemiring()) == float('inf')
