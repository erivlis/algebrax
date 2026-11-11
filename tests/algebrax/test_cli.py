"""
Unit tests for the AlgebraX Command-Line Interface (python -m algebrax).
"""

import json

from algebrax.__main__ import main

VERSION = '0.13.0'


def test_cli_catalog_all(capsys):
    """Test `algebrax catalog` lists semirings."""
    ret = main(['catalog'])
    assert ret == 0
    captured = capsys.readouterr()
    assert 'AlgebraX Semiring Catalog' in captured.out
    assert 'Tropical' in captured.out
    assert 'Boolean' in captured.out


def test_cli_catalog_domain(capsys):
    """Test `algebrax catalog --domain optimization` filters appropriately."""
    ret = main(['catalog', '--domain', 'optimization'])
    assert ret == 0
    captured = capsys.readouterr()
    assert 'Tropical' in captured.out
    assert 'Viterbi' in captured.out


def test_cli_verify_single(capsys):
    """Test `algebrax verify --semiring Tropical` verifies axioms."""
    ret = main(['verify', '--semiring', 'Tropical'])
    assert ret == 0
    captured = capsys.readouterr()
    assert 'TropicalSemiring' in captured.out
    assert 'Axioms Verified' in captured.out
    assert '[PASS]' in captured.out


def test_cli_inspect_file(tmp_path, capsys):
    """Test `algebrax inspect` with file and power operation."""
    mat_file = tmp_path / 'matrix.json'
    mat_data = {'0': {'1': 2.0}, '1': {'2': 3.0}}
    mat_file.write_text(json.dumps(mat_data), encoding='utf-8')

    ret = main(['inspect', str(mat_file), '--semiring', 'tropical', '--power', '2'])
    assert ret == 0
    captured = capsys.readouterr()
    assert 'Sparse Matrix Inspector' in captured.out
    assert 'Row 0: {2: 5.0}' in captured.out


def test_cli_inspect_format_json(tmp_path, capsys):
    """Test `algebrax inspect --format json` outputs valid JSON."""
    mat_file = tmp_path / 'matrix.json'
    mat_data = {'0': {'1': 4.0}}
    mat_file.write_text(json.dumps(mat_data), encoding='utf-8')

    ret = main(['inspect', str(mat_file), '--format', 'json'])
    assert ret == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == {'0': {'1': 4.0}}


def test_cli_inspect_format_html(tmp_path, capsys):
    """Test `algebrax inspect --format html` outputs HTML table."""
    mat_file = tmp_path / 'matrix.json'
    mat_data = {'0': {'1': 4.0}}
    mat_file.write_text(json.dumps(mat_data), encoding='utf-8')

    ret = main(['inspect', str(mat_file), '--format', 'html'])
    assert ret == 0
    captured = capsys.readouterr()
    assert '<table' in captured.out
    assert '4.0' in captured.out


def test_cli_inspect_dot(tmp_path, capsys):
    """Test `algebrax inspect --dot other.json` computes matrix multiplication."""
    m1_file = tmp_path / 'm1.json'
    m2_file = tmp_path / 'm2.json'
    m1_file.write_text(json.dumps({'0': {'0': 2.0}}), encoding='utf-8')
    m2_file.write_text(json.dumps({'0': {'0': 3.0}}), encoding='utf-8')

    ret = main(['inspect', str(m1_file), '--dot', str(m2_file)])
    assert ret == 0
    captured = capsys.readouterr()
    assert 'Row 0: {0: 6.0}' in captured.out


def test_version_attribute_and_cli():
    """Verify algebrax exposes valid semantic version and get_version() resolves correctly."""
    import importlib.metadata
    from unittest.mock import patch

    import algebrax as ax
    from algebrax.__main__ import get_version

    assert hasattr(ax, '__version__')
    assert ax.__version__ == VERSION
    assert get_version() == VERSION

    # Test fallback when PackageNotFoundError is raised
    with patch('importlib.metadata.version', side_effect=importlib.metadata.PackageNotFoundError):
        assert get_version() == VERSION


def test_cli_verify_all_and_errors(capsys, tmp_path, monkeypatch):
    """Test `algebrax verify --all`, invalid semiring, stdin inspect, and help fallback."""
    import io

    # 1. No args -> prints help and returns 0
    assert main([]) == 0
    captured = capsys.readouterr()
    assert 'usage: algebrax' in captured.out

    # 2. verify --all
    assert main(['verify', '--all']) == 0
    captured = capsys.readouterr()
    assert 'StandardSemiring' in captured.out
    assert 'TropicalSemiring' in captured.out

    # 3. verify with unknown semiring -> returns 1
    assert main(['verify', '--semiring', 'UnknownSemiringXYZ']) == 1
    captured = capsys.readouterr()
    assert 'Error loading semiring' in captured.err

    # 4. inspect from stdin ('-') with negative integer keys and non-dict row
    stdin_json = json.dumps({'-1': {'0': 5.0}, '2': 9.0})
    monkeypatch.setattr('sys.stdin', io.StringIO(stdin_json))
    assert main(['inspect', '-']) == 0
    captured = capsys.readouterr()
    assert 'Row -1: {0: 5.0}' in captured.out
    assert 'Row 2: 9.0' in captured.out

    # 5. inspect with non-dict JSON root -> returns 1
    bad_file = tmp_path / 'bad.json'
    bad_file.write_text('[1, 2, 3]', encoding='utf-8')
    assert main(['inspect', str(bad_file)]) == 1
    captured = capsys.readouterr()
    assert 'must contain a JSON object' in captured.err

    # 6. inspect with unknown semiring -> returns 1
    good_file = tmp_path / 'good.json'
    good_file.write_text('{"0": {"1": 1.0}}', encoding='utf-8')
    assert main(['inspect', str(good_file), '--semiring', 'NoSuchSemiring']) == 1
    captured = capsys.readouterr()
    assert 'Unknown semiring' in captured.err

