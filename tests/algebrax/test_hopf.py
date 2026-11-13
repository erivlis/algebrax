"""
Unit and Property Tests for Coalgebras, Bialgebras, and Hopf Algebras (EP-0206).

Tests:
- Runtime Protocol checkability (Coalgebra, Bialgebra, HopfAlgebra)
- GroupHopfAlgebra (coproduct, counit, antipode, axioms)
- DividedPowerCoalgebra (divided power sequence coproduct, counit, axioms)
- SimplicialChainCoalgebra (Alexander-Whitney diagonal approximation, counit, axioms)
- Popperian Falsification cases (broken coproduct, counit, antipode)
"""

from __future__ import annotations

import pytest

from algebrax.algebra import (
    Bialgebra,
    Coalgebra,
    DividedPowerCoalgebra,
    Group,
    GroupHopfAlgebra,
    HopfAlgebra,
)
from algebrax.topology import SimplicialChainCoalgebra
from algebrax.verification import (
    verify_antipode_axiom,
    verify_bialgebra_laws,
    verify_coalgebra_laws,
    verify_coassociativity,
    verify_counitality,
    verify_hopf_algebra_laws,
)


class Klein4Group(Group[str]):
    """Klein four-group V = {e, a, b, c} where every non-identity element has order 2."""

    ELEMENTS = ('e', 'a', 'b', 'c')

    @property
    def zero(self) -> str:
        return 'e'

    @property
    def one(self) -> str:
        return 'e'

    def mul(self, x: str, y: str) -> str:
        if x == 'e':
            return y
        if y == 'e':
            return x
        if x == y:
            return 'e'
        # Distinct non-identity elements multiply to the third
        rem = set(self.ELEMENTS[1:]) - {x, y}
        return rem.pop()

    def inv(self, x: str) -> str:
        return x  # All elements are self-inverse

    def div(self, x: str, y: str) -> str:
        return self.mul(x, self.inv(y))


class CyclicGroup4(Group[int]):
    """Cyclic group Z/4Z under addition modulo 4 (order 4, non-involutive generators)."""

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 0

    def mul(self, x: int, y: int) -> int:
        return (x + y) % 4

    def inv(self, x: int) -> int:
        return (-x) % 4

    def div(self, x: int, y: int) -> int:
        return (x - y) % 4


def test_protocol_conformance() -> None:
    """Verify nominal MRO inheritance and runtime checkability of Coalgebra, Bialgebra, and HopfAlgebra protocols."""
    # 1. Nominal MRO inheritance: GroupHopfAlgebra directly inherits HopfAlgebra
    assert HopfAlgebra in GroupHopfAlgebra.__mro__
    assert Coalgebra in DividedPowerCoalgebra.__mro__
    assert Coalgebra in SimplicialChainCoalgebra.__mro__

    # 2. Instance runtime checkability (PEP 544 structural subtyping)
    z4 = CyclicGroup4()
    gh = GroupHopfAlgebra(z4)
    dpc = DividedPowerCoalgebra()
    scc = SimplicialChainCoalgebra()

    assert isinstance(gh, Coalgebra)
    assert isinstance(gh, Bialgebra)
    assert isinstance(gh, HopfAlgebra)

    assert isinstance(dpc, Coalgebra)
    assert not isinstance(dpc, HopfAlgebra)

    assert isinstance(scc, Coalgebra)
    assert not isinstance(scc, HopfAlgebra)


def test_group_hopf_algebra_operations() -> None:
    """Test group Hopf algebra coproduct, counit, and antipode on Klein 4 and Z_4."""
    z4 = CyclicGroup4()
    gh = GroupHopfAlgebra(z4)

    # 1. Coproduct: Delta(g) = g (x) g
    c1 = {1: 2.0, 3: 5.0}
    coprod = gh.coproduct(c1)
    assert coprod == {(1, 1): 2.0, (3, 3): 5.0}

    # 2. Counit: epsilon(sum c_g g) = sum c_g
    assert gh.counit(c1) == 7.0

    # 3. Antipode: S(1) = 3, S(3) = 1 in Z_4
    anti = gh.antipode(c1)
    assert anti == {3: 2.0, 1: 5.0}

    # 4. Multiplication and Subtraction
    c2 = {1: 1.0, 0: 2.0}
    sub_res = gh.sub(c1, c2)
    assert sub_res == {0: -2.0, 1: 1.0, 3: 5.0}


def test_group_hopf_algebra_axioms_cyclic4() -> None:
    """Verify all Hopf algebra laws on Z_4."""
    z4 = CyclicGroup4()
    gh = GroupHopfAlgebra(z4)

    r_samples = [0.0, 1.0, -2.0, 0.5]
    c_samples = [
        gh.zero,
        gh.one,
        {0: 1.0},
        {1: 1.0},
        {2: 1.0},
        {3: 1.0},
        {0: 2.0, 1: -1.0},
        {1: 0.5, 2: 1.5, 3: -0.5},
    ]

    res = verify_hopf_algebra_laws(gh, r_samples, c_samples)
    for law, ok in res.items():
        assert ok, f"Hopf algebra law '{law}' failed on GroupHopfAlgebra(Z4)"


def test_group_hopf_algebra_axioms_klein4() -> None:
    """Verify all Hopf algebra laws on Klein-4 group."""
    k4 = Klein4Group()
    gh = GroupHopfAlgebra(k4)

    r_samples = [1.0, -1.0, 2.5]
    c_samples = [
        gh.zero,
        gh.one,
        {'e': 1.0},
        {'a': 1.0},
        {'b': 1.0},
        {'c': 1.0},
        {'a': 1.5, 'b': -0.5},
        {'e': 1.0, 'a': 2.0, 'c': -1.0},
    ]

    res = verify_hopf_algebra_laws(gh, r_samples, c_samples)
    assert all(res.values()), f"Hopf laws failed on Klein4: {res}"


def test_divided_power_coalgebra() -> None:
    """Test DividedPowerCoalgebra comultiplication and counit."""
    dpc = DividedPowerCoalgebra()

    # Degree 0: Delta(x^[0]) = x^[0] (x) x^[0]
    x0 = {0: 1.0}
    assert dpc.coproduct(x0) == {(0, 0): 1.0}
    assert dpc.counit(x0) == 1.0

    # Degree 1: Delta(x^[1]) = x^[0] (x) x^[1] + x^[1] (x) x^[0]
    x1 = {1: 1.0}
    assert dpc.coproduct(x1) == {(0, 1): 1.0, (1, 0): 1.0}
    assert dpc.counit(x1) == 0.0

    # Degree 2: Delta(x^[2]) = x^[0] (x) x^[2] + x^[1] (x) x^[1] + x^[2] (x) x^[0]
    x2 = {2: 1.0}
    assert dpc.coproduct(x2) == {(0, 2): 1.0, (1, 1): 1.0, (2, 0): 1.0}
    assert dpc.counit(x2) == 0.0

    # Linear combination
    combo = {0: 3.0, 1: 2.0, 2: -1.0}
    expected_coprod = {
        (0, 0): 3.0,
        (0, 1): 2.0,
        (1, 0): 2.0,
        (0, 2): -1.0,
        (1, 1): -1.0,
        (2, 0): -1.0,
    }
    assert dpc.coproduct(combo) == expected_coprod
    assert dpc.counit(combo) == 3.0

    # Axiom verification
    r_samples = [0.0, 1.0, -1.5, 3.0]
    c_samples = [
        dpc.zero,
        {0: 1.0},
        {1: 1.0},
        {2: 1.0},
        {3: 1.0},
        combo,
        {1: 0.5, 3: 2.0},
    ]
    laws = verify_coalgebra_laws(dpc, r_samples, c_samples)
    for law, ok in laws.items():
        assert ok, f"Coalgebra law '{law}' failed on DividedPowerCoalgebra"


def test_simplicial_chain_coalgebra() -> None:
    """Test SimplicialChainCoalgebra Alexander-Whitney coproduct and vertex counit."""
    scc = SimplicialChainCoalgebra()

    # 0-simplex: Delta([v]) = [v] (x) [v]
    v0 = {(0,): 1.0}
    assert scc.coproduct(v0) == {((0,), (0,)): 1.0}
    assert scc.counit(v0) == 1.0

    # 1-simplex: Delta([0, 1]) = [0] (x) [0, 1] + [0, 1] (x) [1]
    e01 = {(0, 1): 1.0}
    assert scc.coproduct(e01) == {
        ((0,), (0, 1)): 1.0,
        ((0, 1), (1,)): 1.0,
    }
    assert scc.counit(e01) == 0.0

    # 2-simplex: Delta([0, 1, 2]) = [0] (x) [0, 1, 2] + [0, 1] (x) [1, 2] + [0, 1, 2] (x) [2]
    t012 = {(0, 1, 2): 1.0}
    assert scc.coproduct(t012) == {
        ((0,), (0, 1, 2)): 1.0,
        ((0, 1), (1, 2)): 1.0,
        ((0, 1, 2), (2,)): 1.0,
    }
    assert scc.counit(t012) == 0.0

    # Coassociativity and Counitality verification
    r_samples = [0.0, 1.0, -2.0, 0.5]
    c_samples = [
        scc.zero,
        {(0,): 1.0},
        {(1,): 2.0},
        {(0, 1): 1.0},
        {(1, 2): -1.0},
        {(0, 1, 2): 1.0},
        {(0, 1, 2, 3): 1.0},
        {(0,): 1.0, (0, 1): 2.0, (1, 2): -1.0},
    ]

    assert verify_coassociativity(scc, c_samples)
    assert verify_counitality(scc, c_samples)

    laws = verify_coalgebra_laws(scc, r_samples, c_samples)
    for law, ok in laws.items():
        assert ok, f"Coalgebra law '{law}' failed on SimplicialChainCoalgebra"


def test_falsification_broken_coproduct() -> None:
    """Popperian test: verify_coassociativity detects non-coassociative comultiplication."""
    class BrokenCoalgebra(DividedPowerCoalgebra):
        def coproduct(self, c: dict[int, float]) -> dict[tuple[int, int], float]:
            # Always produce an asymmetric tensor violating coassociativity
            return {(0, 1): 1.0}

    broken = BrokenCoalgebra()
    samples = [{0: 1.0}, {1: 1.0}]
    assert not verify_coassociativity(broken, samples)


def test_falsification_broken_counit() -> None:
    """Popperian test: verify_counitality detects broken counit."""
    class BrokenCounitCoalgebra(DividedPowerCoalgebra):
        def counit(self, c: dict[int, float]) -> float:
            return 0.0  # Fails epsilon(x^[0]) == 1

    broken = BrokenCounitCoalgebra()
    samples = [{0: 1.0}]
    assert not verify_counitality(broken, samples)


def test_falsification_broken_antipode() -> None:
    """Popperian test: verify_antipode_axiom detects incorrect antipode."""
    z4 = CyclicGroup4()

    class BrokenHopf(GroupHopfAlgebra):
        def antipode(self, x: dict[int, float]) -> dict[int, float]:
            return x  # Identity instead of inverse (fails for element of order 4)

    broken = BrokenHopf(z4)
    samples = [{1: 1.0}]  # 1 has inverse 3 != 1 in Z/4Z
    assert not verify_antipode_axiom(broken, samples)
