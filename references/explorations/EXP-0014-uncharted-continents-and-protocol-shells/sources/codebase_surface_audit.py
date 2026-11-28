"""Empirical surface audit for EXP-0014: protocol-only shells, live protocol isomers, and thin modules."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from algebrax.algebra import (
    AddCommMonoid,
    AddMagma,
    AddMonoid,
    AddSemigroup,
    Band,
    CommMonoid,
    DistributiveLattice,
    Lattice,
    Magma,
    Module,
    Monoid,
    OpCommMonoid,
    OpMagma,
    OpMonoid,
    OpSemigroup,
    Semigroup,
    VectorSpace,
)


class _NonAssocNonIdemMagma:
    """Deliberately non-associative, non-idempotent magma (subtraction on ints)."""

    def mul(self, a: int, b: int) -> int:
        return a - b


class _NonCommMonoid:
    """Deliberately non-commutative monoid (string concatenation)."""

    @property
    def one(self) -> str:
        return ''

    def mul(self, a: str, b: str) -> str:
        return a + b


class _NonCommAddMonoid:
    """Deliberately non-commutative additive monoid (string concatenation)."""

    @property
    def zero(self) -> str:
        return ''

    def add(self, a: str, b: str) -> str:
        return a + b


class _NonCommOpMonoid:
    """Deliberately non-commutative domain-agnostic monoid."""

    @property
    def identity(self) -> str:
        return ''

    def op(self, a: str, b: str) -> str:
        return a + b


class _ZModuleNotVectorSpace:
    """Z-module over integers (ring, not a field) to test Module vs VectorSpace separation."""

    @property
    def zero(self) -> int:
        return 0

    def add(self, a: int, b: int) -> int:
        return a + b

    def neg(self, a: int) -> int:
        return -a

    def sub(self, a: int, b: int) -> int:
        return a - b

    def smul(self, r: int, m: int) -> int:
        return r * m


class _PentagonN5:
    """Non-modular pentagon N_5 stub to test Lattice vs DistributiveLattice separation."""

    def join(self, a: str, b: str) -> str:
        return a

    def meet(self, a: str, b: str) -> str:
        return b


def audit_module_shells(src_root: Path) -> list[dict[str, Any]]:
    """Inspect thin/protocol-only modules across src/algebrax/."""
    targets = [
        'algebra/_magma.py',
        'algebra/_monoid.py',
        'algebra/_module.py',
        'algebra/_lattice.py',
        'algebra/_action.py',
        'algebra/_padic.py',
        'galois.py',
        'automata.py',
        'probability.py',
        'category/core.py',
        'category/ccc.py',
        'category/enriched.py',
        'category/matrix.py',
        'category/poset.py',
    ]
    rows: list[dict[str, Any]] = []
    for rel in targets:
        path = src_root / rel
        text = path.read_text(encoding='utf-8')
        tree = ast.parse(text)
        protocols: list[str] = []
        concrete_classes: list[str] = []
        functions: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                is_proto = any(
                    (isinstance(b, ast.Name) and b.id == 'Protocol')
                    or (isinstance(b, ast.Subscript) and isinstance(b.value, ast.Name) and b.value.id == 'Protocol')
                    for b in node.bases
                )
                if is_proto:
                    protocols.append(node.name)
                else:
                    concrete_classes.append(node.name)
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                functions.append(node.name)
        rows.append(
            {
                'module': rel,
                'lines': len(text.splitlines()),
                'protocols': protocols,
                'concrete_classes': concrete_classes,
                'public_functions': functions,
            }
        )
    return rows


def audit_protocol_isomers() -> list[dict[str, Any]]:
    """Run live isinstance checks confirming un-witnessed protocol isomers."""
    magma = _NonAssocNonIdemMagma()
    monoid = _NonCommMonoid()
    add_monoid = _NonCommAddMonoid()
    op_monoid = _NonCommOpMonoid()
    z_mod = _ZModuleNotVectorSpace()
    n5 = _PentagonN5()

    checks = [
        ('Magma vs Semigroup', magma, Magma, Semigroup),
        ('Magma vs Band', magma, Magma, Band),
        ('AddMagma vs AddSemigroup', add_monoid, AddMagma, AddSemigroup),
        ('OpMagma vs OpSemigroup', op_monoid, OpMagma, OpSemigroup),
        ('Monoid vs CommMonoid', monoid, Monoid, CommMonoid),
        ('AddMonoid vs AddCommMonoid', add_monoid, AddMonoid, AddCommMonoid),
        ('OpMonoid vs OpCommMonoid', op_monoid, OpMonoid, OpCommMonoid),
        ('Module vs VectorSpace', z_mod, Module, VectorSpace),
        ('Lattice vs DistributiveLattice', n5, Lattice, DistributiveLattice),
    ]

    results: list[dict[str, Any]] = []
    for label, instance, weak_proto, strong_proto in checks:
        weak_ok = isinstance(instance, weak_proto)
        strong_false_pos = isinstance(instance, strong_proto)
        results.append(
            {
                'pair': label,
                'weak_protocol': weak_proto.__name__,
                'strong_protocol': strong_proto.__name__,
                'weak_match': weak_ok,
                'strong_false_positive': strong_false_pos,
            }
        )
    return results


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    src_root = repo_root / 'src' / 'algebrax'
    out_path = Path(__file__).resolve().parent / 'surface_audit_snapshot.json'

    report = {
        'module_shells': audit_module_shells(src_root),
        'protocol_isomers': audit_protocol_isomers(),
    }
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

    isomer_count = sum(1 for row in report['protocol_isomers'] if row['strong_false_positive'])
    zero_class_shells = [
        row['module']
        for row in report['module_shells']
        if row['protocols'] and not row['concrete_classes'] and not row['public_functions']
    ]
    print(f'Wrote {out_path.name}')
    print(f'Protocol-only shells (0 concrete classes): {zero_class_shells}')
    print(f'Live protocol isomer false positives: {isomer_count}/{len(report["protocol_isomers"])}')


if __name__ == '__main__':
    main()
