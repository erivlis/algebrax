"""
CLI Auditor for verifying algebraic laws across semirings (EP-0131).

Usage:
    python -m algebrax.verify
    python -m algebrax.verify --semiring Tropical
"""

import argparse
import sys

from algebrax.semiring import Semiring
from algebrax.verification import get_semiring_samples, verify_semiring_laws


def main() -> int:
    parser = argparse.ArgumentParser(description='Audit algebraic laws for algebrax semirings.')
    parser.add_argument(
        '--semiring',
        type=str,
        default='all',
        help='Semiring name to audit (default: all)',
    )
    args = parser.parse_args()

    catalog = Semiring.catalog()
    names = sorted(catalog.keys()) if args.semiring == 'all' else [args.semiring]

    total = 0
    passed_count = 0

    print('==================================================')
    print('      algebrax Algebraic Law Verification Engine   ')
    print('==================================================')

    for name in names:
        try:
            semiring, samples = get_semiring_samples(name)
        except ValueError as err:
            print(f'ERROR: {err}')
            return 1

        results = verify_semiring_laws(semiring, samples)
        all_passed = all(results.values())
        total += 1
        if all_passed:
            passed_count += 1
            status = 'PASSED'
        else:
            status = 'FAILED'

        print(f'[{status}] {name:22s} (9/9 Axioms Checked)')
        if not all_passed:
            for axiom, passed in results.items():
                if not passed:
                    print(f'   -> FAILED: {axiom}')

    print('--------------------------------------------------')
    print(f'Summary: {passed_count}/{total} semirings verified successfully.')
    return 0 if passed_count == total else 1


if __name__ == '__main__':
    sys.exit(main())
