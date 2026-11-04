"""
Tests for EP-0192: Unifying Domain Objects with the Pure Algebraic Hierarchy.

Verifies that Lie algebras, Clifford algebras, polynomial rings, dual numbers, and cochains
conform to the Lean 4 Mathlib-aligned algebraic protocol hierarchy.
"""

from __future__ import annotations

import pytest

from algebrax.algebra import (
    Algebra,
    CommRing,
    Module,
    NonAssocAlgebra,
    NonAssocRing,
    Ring,
    StandardField,
)
from algebrax.algebra import (
    DualNumberAlgebra as DirectDualNumberAlgebra,
)
from algebrax.algebra import (
    PolynomialAlgebra as DirectPolynomialAlgebra,
)
from algebrax.clifford import CliffordAlgebra as DirectCliffordAlgebra
from algebrax.lie import so_n
from algebrax.lie.core import LieAlgebra
from algebrax.semiring import (
    CliffordAlgebra,
    DualNumberAlgebra,
    PolynomialAlgebra,
    StandardSemiring,
)
from algebrax.topology import Cochain, CochainAlgebra, SimplicialComplex
from algebrax.verification import (
    verify_algebra_laws,
    verify_lie_algebra_laws,
    verify_non_assoc_algebra_laws,
)


def test_lie_algebra_protocol_conformance() -> None:
    """Verify LieAlgebra conforms to NonAssocAlgebra, Module, and NonAssocRing."""
    g = so_n(3)
    assert isinstance(g, LieAlgebra)
    assert isinstance(g, NonAssocAlgebra)
    assert isinstance(g, Module)
    assert isinstance(g, NonAssocRing)
    # Lie algebra is non-associative and non-unital, so it is NOT a Ring or unital Algebra
    assert not isinstance(g, Ring)
    assert not isinstance(g, Algebra)


def test_lie_algebra_arithmetic_methods() -> None:
    """Verify vector arithmetic methods on LieAlgebra."""
    g = so_n(3)
    v1 = {0: 1.0, 1: 2.0}
    v2 = {1: 3.0, 2: -1.0}

    # zero
    assert g.zero == {}

    # add
    assert g.add(v1, v2) == {0: 1.0, 1: 5.0, 2: -1.0}

    # neg
    assert g.neg(v1) == {0: -1.0, 1: -2.0}

    # sub
    assert g.sub(v1, v2) == {0: 1.0, 1: -1.0, 2: 1.0}

    # smul
    assert g.smul(2.5, v1) == {0: 2.5, 1: 5.0}

    # mul is bracket
    assert g.mul(v1, v2) == g.bracket(v1, v2)


def test_lie_algebra_law_verification() -> None:
    """Verify that so3 passes verify_lie_algebra_laws and verify_non_assoc_algebra_laws."""
    g = so_n(3)
    ring = StandardField(float)
    r_samples = [-2.0, -1.0, 0.0, 0.5, 1.0, 2.0]
    m_samples = [
        {},
        {0: 1.0},
        {1: 1.0},
        {2: 1.0},
        {0: 1.0, 1: -1.0},
        {0: 0.5, 2: 2.0},
    ]

    res_non_assoc = verify_non_assoc_algebra_laws(g, ring, r_samples, m_samples)
    assert all(res_non_assoc.values()), f'Failed non-assoc algebra laws: {res_non_assoc}'

    res_lie = verify_lie_algebra_laws(g, ring, r_samples, m_samples)
    assert all(res_lie.values()), f'Failed Lie algebra laws: {res_lie}'


def test_clifford_algebra_protocol_conformance() -> None:
    """Verify CliffordAlgebra conforms to Algebra, Ring, and Semiring."""
    assert DirectCliffordAlgebra is CliffordAlgebra
    cl = CliffordAlgebra(3, 0, 0)
    assert isinstance(cl, Algebra)
    assert isinstance(cl, Ring)

    # Arithmetic
    a = {(1,): 2.0, (1, 2): 3.0}
    b = {(1,): 1.0, (2,): 4.0}

    # neg
    assert cl.neg(a) == {(1,): -2.0, (1, 2): -3.0}

    # sub
    assert cl.sub(a, b) == {(1,): 1.0, (2,): -4.0, (1, 2): 3.0}

    # smul
    assert cl.smul(2.0, a) == {(1,): 4.0, (1, 2): 6.0}
    assert cl.smul(0.0, a) == {}


def test_clifford_algebra_law_verification() -> None:
    """Verify CliffordAlgebra satisfies full associative algebra laws."""
    cl = CliffordAlgebra(2, 0, 0)
    ring = StandardField(float)
    r_samples = [-1.0, 0.0, 1.0, 2.0]
    m_samples = [
        {},
        {(): 1.0},
        {(1,): 1.0},
        {(2,): 1.0},
        {(1, 2): 1.0},
        {(): 1.0, (1,): -2.0},
    ]
    res = verify_algebra_laws(cl, ring, r_samples, m_samples)
    assert all(res.values()), f'Failed Clifford algebra laws: {res}'


def test_polynomial_algebra_protocol_conformance() -> None:
    """Verify PolynomialAlgebra conforms to CommRing, Ring, and Algebra."""
    assert DirectPolynomialAlgebra is PolynomialAlgebra
    p_alg = PolynomialAlgebra(StandardSemiring(float))
    assert isinstance(p_alg, CommRing)
    assert isinstance(p_alg, Ring)
    assert isinstance(p_alg, Algebra)

    p1 = {0: 1.0, 1: 2.0}  # 1 + 2x
    p2 = {1: 3.0, 2: 4.0}  # 3x + 4x^2

    # neg
    assert p_alg.neg(p1) == {0: -1.0, 1: -2.0}

    # sub
    assert p_alg.sub(p1, p2) == {0: 1.0, 1: -1.0, 2: -4.0}

    # smul
    assert p_alg.smul(3.0, p1) == {0: 3.0, 1: 6.0}
    assert p_alg.smul(0.0, p1) == {}


def test_dual_number_algebra_protocol_conformance() -> None:
    """Verify DualNumberAlgebra conforms to CommRing and Algebra."""
    assert DirectDualNumberAlgebra is DualNumberAlgebra
    d_alg = DualNumberAlgebra()
    assert isinstance(d_alg, CommRing)
    assert isinstance(d_alg, Ring)
    assert isinstance(d_alg, Algebra)

    d1 = (2.0, 3.0)
    d2 = (1.0, -1.0)

    # neg
    assert d_alg.neg(d1) == (-2.0, -3.0)

    # sub
    assert d_alg.sub(d1, d2) == (1.0, 4.0)

    # smul
    assert d_alg.smul(2.5, d1) == (5.0, 7.5)


def test_cochain_algebra_protocol_conformance() -> None:
    """Verify CochainAlgebra over a simplicial complex forms an Algebra."""
    k = SimplicialComplex([(0, 1), (1, 2), (2, 0)])
    ring = StandardField(float)
    c_alg = CochainAlgebra(k, ring)

    assert isinstance(c_alg, Algebra)
    assert isinstance(c_alg, Ring)

    # Unit is 0-cochain assigning 1.0 to all vertices
    one = c_alg.one
    assert one[(0,)] == 1.0
    assert one[(1,)] == 1.0
    assert one[(2,)] == 1.0

    # Arithmetic
    c1 = Cochain({(0, 1): 2.0})
    c2 = Cochain({(0, 1): 1.0, (1, 2): 3.0})

    assert c_alg.add(c1, c2) == c1 + c2
    assert c_alg.sub(c1, c2) == c1 - c2
    assert c_alg.neg(c1) == -c1
    assert c_alg.smul(4.0, c1) == c1 * 4.0
