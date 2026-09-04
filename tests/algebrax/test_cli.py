"""
Unit tests for the AlgebraX Command-Line Interface (python -m algebrax).
"""

import json

from algebrax.__main__ import main


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
