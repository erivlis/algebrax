"""Reproducible Z3 finite-model separation suite for EXP-0013 (Lattice & Order Continent).

Machine-verifies sharp minimal separation landmarks across lattice varieties:
  1. M_3 - Minimal modular non-distributive lattice (n=4 UNSAT, n=5 SAT)
  2. N_5 - Minimal non-modular lattice (n=4 UNSAT, n=5 SAT)
  3. O_6 - Minimal orthocomplemented non-orthomodular lattice (n=4 UNSAT, n=6 SAT)
  4. H_3 - Minimal non-Boolean Heyting algebra (n=2 UNSAT, n=3 SAT)
  5. RL_5 - Minimal non-distributive commutative residuated lattice (n=4 UNSAT, n=5 SAT)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import z3


def _add_bounded_lattice_axioms(
    s: z3.Solver,
    join: z3.FuncDeclRef,
    meet: z3.FuncDeclRef,
    elems: list[z3.ExprRef],
) -> None:
    """Constrain (elems, join, meet, elems[0], elems[1]) to be a bounded lattice."""
    n = len(elems)
    bot, top = elems[0], elems[1]
    for i in range(n):
        x = elems[i]
        s.add(join(x, x) == x, meet(x, x) == x)
        s.add(join(bot, x) == x, meet(top, x) == x)
        s.add(meet(bot, x) == bot, join(top, x) == top)
        for j in range(i + 1, n):
            y = elems[j]
            s.add(join(x, y) == join(y, x))
            s.add(meet(x, y) == meet(y, x))
        for y in elems:
            s.add(meet(x, join(x, y)) == x)
            s.add(join(x, meet(x, y)) == x)
            for z in elems:
                s.add(join(join(x, y), z) == join(x, join(y, z)))
                s.add(meet(meet(x, y), z) == meet(x, meet(y, z)))


def _extract_tbl2(model: z3.ModelRef, fn: z3.FuncDeclRef, elems: list[z3.ExprRef]) -> list[list[int]]:
    idx = {str(e): i for i, e in enumerate(elems)}
    return [[idx[str(model.evaluate(fn(a, b)))] for b in elems] for a in elems]


def _extract_tbl1(model: z3.ModelRef, fn: z3.FuncDeclRef, elems: list[z3.ExprRef]) -> list[int]:
    idx = {str(e): i for i, e in enumerate(elems)}
    return [idx[str(model.evaluate(fn(a)))] for a in elems]


def hunt_lattice_separation(n: int, mode: str, timeout_ms: int = 10000) -> dict[str, Any]:
    """Search for minimal separating lattice of size n.

    Modes:
      - 'modular_non_distributive': M_3 diamond
      - 'non_modular': N_5 pentagon
      - 'ortho_non_orthomodular': O_6 benzene hexagon
      - 'non_boolean_heyting': C_3 3-element chain
      - 'non_distributive_residuated': non-distributive integral commutative residuated lattice
    """
    t0 = time.perf_counter()
    s = z3.Solver()
    s.set('timeout', timeout_ms)
    sort, elems = z3.EnumSort(f'L_{mode}_{n}', [f'e{i}' for i in range(n)])
    join = z3.Function('join', sort, sort, sort)
    meet = z3.Function('meet', sort, sort, sort)
    bot, top = elems[0], elems[1]

    def leq(x: z3.ExprRef, y: z3.ExprRef) -> z3.BoolRef:
        return join(x, y) == y

    _add_bounded_lattice_axioms(s, join, meet, elems)

    extra_fns: dict[str, tuple[int, z3.FuncDeclRef]] = {}

    if mode == 'modular_non_distributive':
        for x in elems:
            for y in elems:
                for z in elems:
                    s.add(z3.Implies(leq(x, z), join(x, meet(y, z)) == meet(join(x, y), z)))
        s.add(
            z3.Or(
                [
                    meet(x, join(y, z)) != join(meet(x, y), meet(x, z))
                    for x in elems
                    for y in elems
                    for z in elems
                ]
            )
        )

    elif mode == 'non_modular':
        s.add(
            z3.Or(
                [
                    z3.And(leq(x, z), join(x, meet(y, z)) != meet(join(x, y), z))
                    for x in elems
                    for y in elems
                    for z in elems
                ]
            )
        )

    elif mode == 'ortho_non_orthomodular':
        ortho = z3.Function('ortho', sort, sort)
        extra_fns['ortho'] = (1, ortho)
        for x in elems:
            s.add(ortho(ortho(x)) == x)
            s.add(join(x, ortho(x)) == top)
            s.add(meet(x, ortho(x)) == bot)
            for y in elems:
                s.add(z3.Implies(leq(x, y), leq(ortho(y), ortho(x))))
        # Violate orthomodular law: x <= y => y == x v (y ^ x')
        s.add(
            z3.Or(
                [
                    z3.And(leq(x, y), y != join(x, meet(y, ortho(x))))
                    for x in elems
                    for y in elems
                ]
            )
        )

    elif mode == 'non_boolean_heyting':
        imp = z3.Function('imp', sort, sort, sort)
        extra_fns['imp'] = (2, imp)
        for a in elems:
            for b in elems:
                for x in elems:
                    s.add(leq(meet(a, x), b) == leq(x, imp(a, b)))
        # Violate excluded middle: exists a: a v (a -> bot) != top
        s.add(z3.Or([join(a, imp(a, bot)) != top for a in elems]))

    elif mode == 'non_distributive_residuated':
        mul = z3.Function('mul', sort, sort, sort)
        res = z3.Function('res', sort, sort, sort)
        extra_fns['mul'] = (2, mul)
        extra_fns['res'] = (2, res)
        for x in elems:
            s.add(mul(top, x) == x, mul(x, top) == x)
            for y in elems:
                s.add(mul(x, y) == mul(y, x))
                for z in elems:
                    s.add(mul(mul(x, y), z) == mul(x, mul(y, z)))
                    s.add(leq(mul(x, z), y) == leq(z, res(x, y)))
        # Non-distributive lattice!
        s.add(
            z3.Or(
                [
                    meet(x, join(y, z)) != join(meet(x, y), meet(x, z))
                    for x in elems
                    for y in elems
                    for z in elems
                ]
            )
        )

    chk = s.check()
    dt = round(time.perf_counter() - t0, 3)
    if chk != z3.sat:
        return {'n': n, 'mode': mode, 'status': str(chk), 'elapsed_s': dt}
    m = s.model()
    out: dict[str, Any] = {
        'n': n,
        'mode': mode,
        'status': 'sat',
        'elapsed_s': dt,
        'join': _extract_tbl2(m, join, elems),
        'meet': _extract_tbl2(m, meet, elems),
    }
    for name, (arity, fn) in extra_fns.items():
        out[name] = _extract_tbl1(m, fn, elems) if arity == 1 else _extract_tbl2(m, fn, elems)
    return out


def run_all() -> dict[str, Any]:
    """Run all Z3 lattice-variety separation checks."""
    report: dict[str, Any] = {'z3_version': z3.get_version_string(), 'hunts': {}}
    report['hunts']['M3_modular_non_distributive'] = [
        hunt_lattice_separation(n, 'modular_non_distributive') for n in (4, 5)
    ]
    report['hunts']['N5_non_modular'] = [hunt_lattice_separation(n, 'non_modular') for n in (4, 5)]
    report['hunts']['O6_ortho_non_orthomodular'] = [
        hunt_lattice_separation(n, 'ortho_non_orthomodular') for n in (4, 5, 6)
    ]
    report['hunts']['H3_non_boolean_heyting'] = [
        hunt_lattice_separation(n, 'non_boolean_heyting') for n in (2, 3)
    ]
    report['hunts']['RL6_non_distributive_residuated'] = [
        hunt_lattice_separation(n, 'non_distributive_residuated') for n in (4, 5, 6)
    ]
    return report


def main() -> None:
    report = run_all()
    out_path = Path(__file__).with_name('z3_lattice_findings.json')
    out_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Wrote verified Z3 lattice findings to {out_path}')
    for key, items in report['hunts'].items():
        summary = [(it['n'], it['status'], f"{it['elapsed_s']}s") for it in items]
        print(f'  {key:32s}: {summary}')


if __name__ == '__main__':
    main()
