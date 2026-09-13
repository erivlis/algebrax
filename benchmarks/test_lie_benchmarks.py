"""Benchmarks for continuous symmetries, Lie algebras, root systems, and BCH dynamics."""

import sys

import pytest

sys.path.insert(0, 'src')
sys.path.insert(0, '.')

import algebrax as ax
from algebrax.lie import (
    RootSystem,
    StructureConstants,
    chevalley_lie_algebra,
    clifford_lie_algebra,
    e6,
    f4,
    g2,
    se_n,
    sl_n,
    so_n,
    sp_n,
    su_n,
)

# region 1. Classical Algebra Construction


@pytest.mark.benchmark(group='lie-algebra-construction')
@pytest.mark.parametrize(
    ('algebra_fn', 'arg'),
    [
        (so_n, 3),
        (so_n, 5),
        (su_n, 2),
        (su_n, 3),
        (sl_n, 2),
        (sl_n, 3),
        (se_n, 3),
        (sp_n, 2),
    ],
)
def test_benchmark_lie_algebra_construction(benchmark, algebra_fn, arg):
    """Cost of assembling the basis, commutator table, and structure constants tensor."""
    result = benchmark(algebra_fn, arg)
    assert result.dim > 0


@pytest.mark.benchmark(group='lie-clifford-construction')
def test_benchmark_clifford_lie_construction(benchmark):
    """Cost of extracting bivector commutators from a Clifford algebra into a Lie algebra."""
    result = benchmark(clifford_lie_algebra, 3, 0)
    assert result.dim == 3


# endregion


# region 2. Bracket Evaluation


@pytest.mark.benchmark(group='lie-bracket-eval')
@pytest.mark.parametrize('name', ['so3', 'sl3', 'se3'])
def test_benchmark_lie_bracket(benchmark, name: str):
    """Raw sparse bracket evaluation [X, Y] over structure constants."""
    if name == 'so3':
        alg = so_n(3)
        x = {0: 1.0, 1: 0.5}
        y = {1: 0.5, 2: 1.0}
    elif name == 'sl3':
        alg = sl_n(3)
        x = {0: 1.0, 3: -0.5, 7: 0.8}
        y = {1: 0.5, 4: 1.0, 6: -0.2}
    else:
        alg = se_n(3)
        x = {0: 0.3, 1: 0.4, 3: 1.0}
        y = {2: 0.5, 4: -1.0, 5: 0.2}

    result = benchmark(alg.bracket, x, y)
    assert result is not None


# endregion


# region 3. Structure Constants & Jacobi Verification


@pytest.mark.benchmark(group='lie-jacobi-verification')
@pytest.mark.parametrize('dim', [3, 4])
def test_benchmark_jacobi_verification(benchmark, dim: int):
    """Cost of verifying the Jacobi identity via sparse rank-3 einsum tensor contraction."""
    alg = so_n(dim)
    sc = alg.structure_constants
    result = benchmark(sc.verify_jacobi)
    assert result is True


# endregion


# region 4. Adjoint Representation & Killing Metric


@pytest.mark.benchmark(group='lie-adjoint-matrix')
def test_benchmark_adjoint_matrix(benchmark):
    """Assembling the adjoint matrix ad_X for an element."""
    alg = so_n(4)
    x = {i: 0.2 * (i + 1) for i in range(alg.dim)}
    result = benchmark(alg.adjoint_matrix, x)
    assert len(result) > 0


@pytest.mark.benchmark(group='lie-killing-matrix')
@pytest.mark.parametrize(('name', 'n'), [('so', 3), ('sl', 3)])
def test_benchmark_killing_matrix(benchmark, name: str, n: int):
    """Cost of building the full Killing metric matrix B(T_a, T_b)."""
    alg = so_n(n) if name == 'so' else sl_n(n)
    result = benchmark(alg.killing_matrix)
    assert len(result) == alg.dim


# endregion


# region 5. Baker-Campbell-Hausdorff (BCH) Formula


@pytest.mark.benchmark(group='lie-bch-orders')
@pytest.mark.parametrize('order', [1, 2, 3, 4])
def test_benchmark_bch_series(benchmark, order: int):
    """Evaluating the truncated BCH series log(exp(X)exp(Y)) up to order 1, 2, 3, 4."""
    alg = so_n(3)
    x = {0: 0.05, 1: 0.02}
    y = {1: 0.03, 2: 0.04}
    result = benchmark(alg.bch, x, y, order=order)
    assert result is not None


# endregion


# region 6. Root Systems & Weyl Group


@pytest.mark.benchmark(group='lie-root-systems')
@pytest.mark.parametrize(('cartan_type', 'rank'), [('A', 3), ('B', 3), ('G', 2)])
def test_benchmark_root_system_generation(benchmark, cartan_type: str, rank: int):
    """Instantiating a crystallographic root system and computing positive roots."""

    def run():
        rs = RootSystem.from_dynkin(cartan_type, rank)
        return rs.positive_roots

    result = benchmark(run)
    assert len(result) > 0


@pytest.mark.benchmark(group='lie-weyl-reflection')
def test_benchmark_weyl_reflection(benchmark):
    """Evaluating a Weyl reflection s_i(alpha)."""
    rs = RootSystem.from_dynkin('A', 4)
    beta = rs.simple_roots[1]
    result = benchmark(rs.weyl_reflect, beta, 0)
    assert result is not None


# endregion


# region 7. Exceptional & Chevalley Construction


@pytest.mark.benchmark(group='lie-exceptional-construction')
@pytest.mark.parametrize('factory', [g2, f4])
def test_benchmark_exceptional_construction(benchmark, factory):
    """Assembling exceptional Lie algebras G2 and F4."""
    result = benchmark(factory)
    assert result.dim in (14, 52)


@pytest.mark.benchmark(group='lie-chevalley-construction')
def test_benchmark_chevalley_construction(benchmark):
    """Constructing a Lie algebra from a root system via the Chevalley basis."""
    rs = RootSystem.from_dynkin('G', 2)
    result = benchmark(chevalley_lie_algebra, rs)
    assert result.dim == 14

# endregion
