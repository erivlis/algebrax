"""
Tests for the Algebraic Law Verification Engine and CLI Auditor (`algebrax.verify`).
"""

from __future__ import annotations

import pytest

from algebrax import verify as verify_cli
from algebrax.semiring import Semiring
from algebrax.verification import (
    get_semiring_samples,
    semiring_elements_equal,
    verify_semiring_laws,
)


def test_semiring_elements_equal_basic() -> None:
    """Test element equality comparison across diverse types and edge cases."""
    assert semiring_elements_equal(1.0, 1.0)
    assert semiring_elements_equal(float('inf'), float('inf'))
    assert semiring_elements_equal(float('-inf'), float('-inf'))
    assert not semiring_elements_equal(float('inf'), float('-inf'))
    assert semiring_elements_equal(float('nan'), float('nan'))
    assert semiring_elements_equal(1.0 + 2.0j, 1.0 + 2.0j + 1e-12j)
    assert not semiring_elements_equal(1.0 + 2.0j, 1.0 - 2.0j)
    assert semiring_elements_equal((1.0, 2.0), (1.0, 2.0))
    assert not semiring_elements_equal((1.0, 2.0), (1.0, 2.0, 3.0))
    assert semiring_elements_equal({'a': 1.0}, {'a': 1.0})
    assert not semiring_elements_equal({'a': 1.0}, {'a': 2.0})
    assert not semiring_elements_equal({'a': 1.0}, {'b': 1.0})
    assert not semiring_elements_equal(1.0, 'not_a_float')


@pytest.mark.parametrize('semiring_name', sorted(Semiring.catalog().keys()))
def test_all_catalog_semirings_satisfy_laws(semiring_name: str) -> None:
    """Parametrized test verifying all 34 built-in semirings satisfy the 9 algebraic axioms."""
    semiring, samples = get_semiring_samples(semiring_name)
    results = verify_semiring_laws(semiring, samples)

    for axiom_name, passed in results.items():
        assert passed, f"Semiring '{semiring_name}' failed axiom '{axiom_name}'"


def test_get_semiring_samples_unknown_raises() -> None:
    """Verify get_semiring_samples raises ValueError for unknown semiring names."""
    with pytest.raises(ValueError, match='Unknown semiring'):
        get_semiring_samples('NonExistentSemiring')


def test_verify_semiring_laws_detects_broken_semiring() -> None:
    """Verify that verify_semiring_laws falsifies a broken semiring across all 9 axioms."""

    class BrokenSemiring(Semiring[float]):
        @property
        def zero(self) -> float:
            return 99.0  # Wrong additive identity & non-annihilating

        @property
        def one(self) -> float:
            return -77.0  # Wrong multiplicative identity

        def add(self, a: float, b: float) -> float:
            return a - 2.0 * b + 1.0  # Non-commutative & non-associative

        def mul(self, a: float, b: float) -> float:
            return (a + 1.0) / (abs(b) + 2.0)  # Non-associative & non-distributive

    broken = BrokenSemiring()
    res = verify_semiring_laws(broken, [0.0, 1.0, 2.0, 3.0])
    assert all(not passed for passed in res.values()), f'Expected all 9 axioms to fail, got: {res}'


def test_verify_cli_main_success_and_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify the CLI auditor (`python -m algebrax.verify`) for single semiring, all semirings, and failure cases."""
    # 1. Single valid semiring
    monkeypatch.setattr('sys.argv', ['algebrax.verify', '--semiring', 'Tropical'])
    assert verify_cli.main() == 0
    out_single = capsys.readouterr().out
    assert '[PASSED] Tropical' in out_single
    assert '1/1 semirings verified successfully' in out_single

    # 2. All semirings
    monkeypatch.setattr('sys.argv', ['algebrax.verify', '--semiring', 'all'])
    assert verify_cli.main() == 0
    out_all = capsys.readouterr().out
    assert '34/34 semirings verified successfully' in out_all

    # 3. Unknown semiring returns exit code 1
    monkeypatch.setattr('sys.argv', ['algebrax.verify', '--semiring', 'UnknownBogus'])
    assert verify_cli.main() == 1
    out_err = capsys.readouterr().out
    assert 'ERROR:' in out_err

    # 4. Simulated axiom failure prints FAILED details and returns exit code 1
    monkeypatch.setattr(
        verify_cli,
        'verify_semiring_laws',
        lambda _sr, _samples: {'add_commutativity': False, 'add_associativity': True},
    )
    monkeypatch.setattr('sys.argv', ['algebrax.verify', '--semiring', 'Tropical'])
    assert verify_cli.main() == 1
    out_fail = capsys.readouterr().out
    assert '[FAILED] Tropical' in out_fail
    assert '-> FAILED: add_commutativity' in out_fail
