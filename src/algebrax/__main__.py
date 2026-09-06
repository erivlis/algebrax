"""
AlgebraX Command-Line Interface (CLI).

Entry point for `python -m algebrax`.
Provides tools for inspecting sparse matrices, viewing the semiring catalog,
and verifying algebraic laws.
"""

import argparse
import importlib.metadata
import json
import sys
from typing import Any

import algebrax as ax
from algebrax.verification import get_semiring_samples, verify_semiring_laws


def get_version() -> str:
    """Return algebrax package version."""
    try:
        return importlib.metadata.version('algebrax')
    except importlib.metadata.PackageNotFoundError:
        return getattr(ax, '__version__', '0.8.0')


def cmd_catalog(args: argparse.Namespace) -> int:
    """Print catalog of built-in semirings."""
    catalog = ax.semiring.Semiring.catalog()
    domain_filter = (args.domain or 'all').lower()

    # Classification by module namespace
    domains: dict[str, list[str]] = {
        'arithmetic': ['Standard', 'Modular'],
        'optimization': ['Tropical', 'Arctic', 'Viterbi', 'Reliability', 'Bottleneck', 'MinTimes'],
        'logic': ['Boolean', 'Digital', 'Lukasiewicz', 'String', 'KCollapsed'],
        'statistical': [
            'Log',
            'Expectation',
            'Variance',
            'BivariateVariance',
            'BivariateCovariance',
            'Skewness',
            'Kurtosis',
            'StatisticalMoment',
            'MultivariateMoment',
        ],
        'algebraic': [
            'DualNumber',
            'BinomialConvolution',
            'MultivariateBinomialConvolution',
            'MonoidAlgebra',
            'Polynomial',
            'Provenance',
            'Knot',
            'QuotientMonoidAlgebra',
            'Clifford',
            'GeneralizedClifford',
            'QuantumClifford',
            'GaloisField',
        ],
    }

    print(f'\n{"=" * 80}')
    print(f' AlgebraX Semiring Catalog (v{get_version()})')
    print(f'{"=" * 80}')
    print(f' {"Name":<32} | {"Domain":<14} | {"Zero (⊕)":<12} | {"One (⊗)":<12}')
    print(f'{"-" * 80}')

    for domain_name, sem_names in domains.items():
        if domain_filter != 'all' and domain_filter != domain_name:
            continue
        for name in sem_names:
            if name in catalog:
                try:
                    sem_cls = catalog[name]
                    # Attempt default instantiation
                    sem_inst = sem_cls()
                    zero_s = str(sem_inst.zero)[:10]
                    one_s = str(sem_inst.one)[:10]
                except Exception:
                    zero_s = 'N/A'
                    one_s = 'N/A'
                print(f' {name:<32} | {domain_name.capitalize():<14} | {zero_s:<12} | {one_s:<12}')

    print(f'{"=" * 80}\n')
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify algebraic axioms for semirings."""
    semiring_name = args.semiring
    verify_all = args.all

    if verify_all:
        names_to_test = [
            'Standard',
            'Modular',
            'Tropical',
            'Arctic',
            'Viterbi',
            'Reliability',
            'Bottleneck',
            'Boolean',
            'Log',
            'Expectation',
            'Variance',
            'BinomialConvolution',
        ]
    else:
        names_to_test = [semiring_name]

    overall_pass = True
    for name in names_to_test:
        try:
            sem_inst, samples = get_semiring_samples(name)
        except Exception as e:
            print(f"Error loading semiring '{name}': {e}", file=sys.stderr)
            overall_pass = False
            continue

        results = verify_semiring_laws(sem_inst, samples)
        print(f'\n{"=" * 70}')
        print(f' Algebraic Axiom Verification: {name}Semiring')
        print(f'{"=" * 70}')

        passed_count = 0
        total_count = len(results)
        for axiom, status in results.items():
            icon = '[PASS]' if status else '[FAIL]'
            label = axiom.replace('_', ' ').title()
            print(f'  {icon} {label:<38}: {"PASSED" if status else "FAILED"}')
            if status:
                passed_count += 1
            else:
                overall_pass = False

        print(f'{"-" * 70}')
        print(f' Result: {passed_count}/{total_count} Axioms Verified')

    print()
    return 0 if overall_pass else 1


def _parse_matrix_dict(raw: dict[str, Any]) -> dict[Any, dict[Any, Any]]:
    """Convert JSON object to a typed sparse matrix, restoring int keys if appropriate."""
    mat: dict[Any, dict[Any, Any]] = {}
    for r_k, row in raw.items():
        row_key: Any = int(r_k) if r_k.isdigit() or (r_k.startswith('-') and r_k[1:].isdigit()) else r_k
        mat[row_key] = {}
        if isinstance(row, dict):
            for c_k, v in row.items():
                col_key: Any = int(c_k) if c_k.isdigit() or (c_k.startswith('-') and c_k[1:].isdigit()) else c_k
                mat[row_key][col_key] = v
        else:
            mat[row_key] = row
    return mat


def cmd_inspect(args: argparse.Namespace) -> int:
    """Inspect and operate on sparse matrices from files or stdin."""
    # Load primary matrix
    if args.file == '-':
        data = json.load(sys.stdin)
    else:
        with open(args.file, encoding='utf-8') as f:
            data = json.load(f)

    if not isinstance(data, dict):
        print('Error: Input file must contain a JSON object representing a SparseMatrix.', file=sys.stderr)
        return 1

    matrix = _parse_matrix_dict(data)

    # Resolve semiring
    sem = None
    if args.semiring:
        catalog = ax.semiring.Semiring.catalog()
        key_matched = None
        for k in catalog:
            if k.lower() == args.semiring.lower() or f'{k.lower()}semiring' == args.semiring.lower():
                key_matched = k
                break
        if not key_matched:
            print(f"Error: Unknown semiring '{args.semiring}'. Run 'python -m algebrax catalog'.", file=sys.stderr)
            return 1
        sem_cls = catalog[key_matched]
        try:
            sem = sem_cls()
        except Exception:
            sem = None

    # Apply operation
    if args.power is not None:
        matrix = ax.matrix.power(matrix, args.power, semiring=sem)

    if args.dot is not None:
        with open(args.dot, encoding='utf-8') as f:
            dot_data = json.load(f)
        mat2 = _parse_matrix_dict(dot_data)
        matrix = ax.matrix.dot(matrix, mat2, semiring=sem)

    # Compute metrics
    rows = len(matrix)
    cols = len({c for r in matrix.values() if isinstance(r, dict) for c in r})
    nnz = sum(len(r) for r in matrix.values() if isinstance(r, dict))

    # Format output
    if args.format == 'json':
        print(json.dumps(matrix, indent=2))
    elif args.format == 'html':
        print(ax.display.display_matrix(matrix, title=f'Matrix ({rows}x{cols}, nnz={nnz})'))
    else:
        print(f'\nSparse Matrix Inspector ({rows} rows, {cols} cols, {nnz} non-zero entries)')
        print(f'{"-" * 60}')
        for r, row_entries in sorted(matrix.items(), key=str):
            if isinstance(row_entries, dict):
                entries_str = ', '.join(f'{c}: {v}' for c, v in sorted(row_entries.items(), key=str))
                print(f'  Row {r}: {{{entries_str}}}')
            else:
                print(f'  Row {r}: {row_entries}')
        print()

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entrypoint for algebrax CLI."""
    parser = argparse.ArgumentParser(
        prog='algebrax',
        description='AlgebraX Command-Line Interface (CLI)',
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'AlgebraX {get_version()}',
    )

    subparsers = parser.add_subparsers(dest='command', help='Available subcommands')

    # Subcommand: catalog
    cat_parser = subparsers.add_parser('catalog', help='List all available built-in semirings')
    cat_parser.add_argument(
        '--domain',
        choices=['arithmetic', 'optimization', 'logic', 'statistical', 'algebraic', 'all'],
        default='all',
        help='Filter semirings by mathematical domain',
    )
    cat_parser.set_defaults(func=cmd_catalog)

    # Subcommand: verify
    ver_parser = subparsers.add_parser('verify', help='Verify algebraic semiring axioms')
    ver_parser.add_argument(
        '--semiring',
        default='Standard',
        help='Name of semiring to verify (default: Standard)',
    )
    ver_parser.add_argument(
        '--all',
        action='store_true',
        help='Run verification on all core semirings',
    )
    ver_parser.set_defaults(func=cmd_verify)

    # Subcommand: inspect
    ins_parser = subparsers.add_parser('inspect', help='Inspect a sparse matrix file or compute operations')
    ins_parser.add_argument('file', help="Path to JSON matrix file, or '-' for stdin")
    ins_parser.add_argument('--semiring', default=None, help='Semiring to use for operations (e.g. tropical, boolean)')
    ins_parser.add_argument('--power', type=int, default=None, help='Raise matrix to integer power n')
    ins_parser.add_argument('--dot', default=None, help='Multiply with a second JSON matrix file')
    ins_parser.add_argument(
        '--format',
        choices=['text', 'json', 'html'],
        default='text',
        help='Output format (default: text)',
    )
    ins_parser.set_defaults(func=cmd_inspect)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
