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
    # [1, 2] * [1, 1] = [1, 3, 2]
    # 0: 1*1=1
    # 1: 1*1 + 2*1 = 3
    # 2: 2*1 = 2
    f = {0: 1, 1: 2}
    g = {0: 1, 1: 1}
    h = convolve(f, g)
    assert h == {0: 1, 1: 3, 2: 2}


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
