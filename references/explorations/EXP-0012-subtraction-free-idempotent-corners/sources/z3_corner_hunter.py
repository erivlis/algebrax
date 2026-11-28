"""Reproducible Z3 finite-model hunter for subtraction-free idempotent algebraic corners.

Discovers, verifies, and exports minimal finite models and UNSAT lower bounds across
the subtraction-free idempotent quadrant of AlgebraX's mixin hypercube:
  1. J_4  - Minimal non-associative Jordan-Kleene quantale (n=4; n=3 UNSAT)
  2. E_5  - Minimal provably exceptional (non-special) Jordan quantale (n=5; n=4 UNSAT)
  3. A_5  - Minimal non-flexible Artin-alternative quantale (n=5; n=3,4 UNSAT)
  4. F_5  - Minimal flexible-alternative non-Moufang quantale (n=5)
  5. M_7  - Minimal chain-ordered non-associative Moufang quantale (n=7; n=5,6 chain UNSAT)
  6. D_3  - Minimal non-inner unital-drift idempotent derivation (n=3)
  7. DK_4 - Minimal unital-drift separation of D*(a*) != (D*(a))* (n=4), confirming
            the exact corrected law D*(a*) == D*(1) * (D*(a))*.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import z3


def _add_join_semilattice_axioms(
    s: z3.Solver,
    add: z3.FuncDeclRef,
    elems: list[z3.ExprRef],
) -> None:
    """Constrain (elems, add, elems[0]) to be an idempotent commutative monoid."""
    n = len(elems)
    e0 = elems[0]
    for i in range(n):
        s.add(add(e0, elems[i]) == elems[i])
        s.add(add(elems[i], e0) == elems[i])
        s.add(add(elems[i], elems[i]) == elems[i])
        for j in range(i + 1, n):
            s.add(add(elems[i], elems[j]) == add(elems[j], elems[i]))
        for j in range(n):
            for k in range(n):
                s.add(add(add(elems[i], elems[j]), elems[k]) == add(elems[i], add(elems[j], elems[k])))


def _add_distributive_unital_mul_axioms(
    s: z3.Solver,
    add: z3.FuncDeclRef,
    mul: z3.FuncDeclRef,
    elems: list[z3.ExprRef],
    *,
    commutative: bool = False,
) -> None:
    """Constrain mul to have zero elems[0], unit elems[1], and distribute over add."""
    n = len(elems)
    e0, e1 = elems[0], elems[1]
    for i in range(n):
        s.add(mul(e0, elems[i]) == e0, mul(elems[i], e0) == e0)
        s.add(mul(e1, elems[i]) == elems[i], mul(elems[i], e1) == elems[i])
        if commutative:
            for j in range(i + 1, n):
                s.add(mul(elems[i], elems[j]) == mul(elems[j], elems[i]))
        for j in range(n):
            for k in range(n):
                s.add(mul(elems[i], add(elems[j], elems[k])) == add(mul(elems[i], elems[j]), mul(elems[i], elems[k])))
                if not commutative:
                    s.add(
                        mul(add(elems[j], elems[k]), elems[i])
                        == add(mul(elems[j], elems[i]), mul(elems[k], elems[i]))
                    )


def _extract_table2(
    model: z3.ModelRef,
    fn: z3.FuncDeclRef,
    elems: list[z3.ExprRef],
) -> list[list[int]]:
    idx = {str(e): i for i, e in enumerate(elems)}
    return [[idx[str(model.evaluate(fn(a, b)))] for b in elems] for a in elems]


def _extract_table1(
    model: z3.ModelRef,
    fn: z3.FuncDeclRef,
    elems: list[z3.ExprRef],
) -> list[int]:
    idx = {str(e): i for i, e in enumerate(elems)}
    return [idx[str(model.evaluate(fn(a)))] for a in elems]


def hunt_jordan_kleene(n: int, timeout_ms: int = 10000) -> dict[str, Any]:
    """Search for a strictly non-associative Jordan-Kleene quantale of size n."""
    t0 = time.perf_counter()
    s = z3.Solver()
    s.set('timeout', timeout_ms)
    elem_sort, elems = z3.EnumSort(f'JK_{n}', [f'e{i}' for i in range(n)])
    add = z3.Function('add', elem_sort, elem_sort, elem_sort)
    mul = z3.Function('mul', elem_sort, elem_sort, elem_sort)
    star = z3.Function('star', elem_sort, elem_sort)
    e1 = elems[1]

    _add_join_semilattice_axioms(s, add, elems)
    _add_distributive_unital_mul_axioms(s, add, mul, elems, commutative=True)

    for x in elems:
        for y in elems:
            s.add(mul(mul(x, y), mul(x, x)) == mul(x, mul(y, mul(x, x))))

    s.add(
        z3.Or(
            [
                mul(mul(elems[i], elems[j]), elems[k]) != mul(elems[i], mul(elems[j], elems[k]))
                for i in range(2, n)
                for j in range(2, n)
                for k in range(2, n)
            ]
        )
    )

    for x in elems:
        s.add(add(e1, mul(x, star(x))) == star(x))
        for y in elems:
            s.add(z3.Implies(add(add(e1, mul(x, y)), y) == y, add(star(x), y) == y))

    chk = s.check()
    dt = round(time.perf_counter() - t0, 3)
    if chk != z3.sat:
        return {'n': n, 'status': str(chk), 'elapsed_s': dt}
    m = s.model()
    return {
        'n': n,
        'status': 'sat',
        'elapsed_s': dt,
        'add': _extract_table2(m, add, elems),
        'mul': _extract_table2(m, mul, elems),
        'star': _extract_table1(m, star, elems),
    }


def hunt_exceptional_jordan_quantale(n: int, timeout_ms: int = 10000) -> dict[str, Any]:
    """Search for a provably non-special Jordan quantale violating (a -o a)^2 <= (a -o a)."""
    t0 = time.perf_counter()
    s = z3.Solver()
    s.set('timeout', timeout_ms)
    elem_sort, elems = z3.EnumSort(f'EJ_{n}', [f'e{i}' for i in range(n)])
    add = z3.Function('add', elem_sort, elem_sort, elem_sort)
    mul = z3.Function('mul', elem_sort, elem_sort, elem_sort)
    res = z3.Function('res', elem_sort, elem_sort, elem_sort)

    def leq(x: z3.ExprRef, y: z3.ExprRef) -> z3.BoolRef:
        return add(x, y) == y

    _add_join_semilattice_axioms(s, add, elems)
    _add_distributive_unital_mul_axioms(s, add, mul, elems, commutative=True)

    for x in elems:
        for y in elems:
            s.add(mul(mul(x, y), mul(x, x)) == mul(x, mul(y, mul(x, x))))
    for a in elems:
        for b in elems:
            for x in elems:
                s.add(leq(mul(a, x), b) == leq(x, res(a, b)))

    s.add(z3.Or([z3.Not(leq(mul(res(a, a), res(a, a)), res(a, a))) for a in elems]))

    chk = s.check()
    dt = round(time.perf_counter() - t0, 3)
    if chk != z3.sat:
        return {'n': n, 'status': str(chk), 'elapsed_s': dt}
    m = s.model()
    return {
        'n': n,
        'status': 'sat',
        'elapsed_s': dt,
        'add': _extract_table2(m, add, elems),
        'mul': _extract_table2(m, mul, elems),
        'res': _extract_table2(m, res, elems),
    }


def hunt_alternative_tier(n: int, mode: str, timeout_ms: int = 10000) -> dict[str, Any]:
    """Search for non-associative alternative idempotent semirings by tier.

    Modes:
      - 'artin_non_flex': Left + Right Alternative, violating Flexibility.
      - 'flex_non_moufang': Left + Right Alternative + Flexible, violating Moufang.
      - 'moufang_general': All three Moufang identities, strictly non-associative.
    """
    t0 = time.perf_counter()
    s = z3.Solver()
    s.set('timeout', timeout_ms)
    elem_sort, elems = z3.EnumSort(f'ALT_{mode}_{n}', [f'e{i}' for i in range(n)])
    add = z3.Function('add', elem_sort, elem_sort, elem_sort)
    mul = z3.Function('mul', elem_sort, elem_sort, elem_sort)

    _add_join_semilattice_axioms(s, add, elems)
    _add_distributive_unital_mul_axioms(s, add, mul, elems, commutative=False)

    for x in elems:
        for y in elems:
            s.add(mul(mul(x, x), y) == mul(x, mul(x, y)))
            s.add(mul(mul(y, x), x) == mul(y, mul(x, x)))
            if mode in ('flex_non_moufang', 'moufang_general'):
                s.add(mul(mul(x, y), x) == mul(x, mul(y, x)))

    if mode == 'artin_non_flex':
        s.add(z3.Or([mul(mul(x, y), x) != mul(x, mul(y, x)) for x in elems[2:] for y in elems[2:]]))
    elif mode == 'flex_non_moufang':
        m_fails = []
        for x in elems[2:]:
            for y in elems[2:]:
                for z in elems[2:]:
                    m_fails.append(mul(x, mul(y, mul(x, z))) != mul(mul(mul(x, y), x), z))
                    m_fails.append(mul(mul(x, y), mul(z, x)) != mul(x, mul(mul(y, z), x)))
        s.add(z3.Or(m_fails))
    elif mode == 'moufang_general':
        for x in elems:
            for y in elems:
                for z in elems:
                    s.add(mul(x, mul(y, mul(x, z))) == mul(mul(mul(x, y), x), z))
                    s.add(mul(z, mul(x, mul(y, x))) == mul(mul(mul(z, x), y), x))
                    s.add(mul(mul(x, y), mul(z, x)) == mul(x, mul(mul(y, z), x)))

    s.add(
        z3.Or(
            [
                mul(mul(x, y), z) != mul(x, mul(y, z))
                for x in elems[2:]
                for y in elems[2:]
                for z in elems[2:]
            ]
        )
    )

    chk = s.check()
    dt = round(time.perf_counter() - t0, 3)
    if chk != z3.sat:
        return {'n': n, 'mode': mode, 'status': str(chk), 'elapsed_s': dt}
    m = s.model()
    return {
        'n': n,
        'mode': mode,
        'status': 'sat',
        'elapsed_s': dt,
        'add': _extract_table2(m, add, elems),
        'mul': _extract_table2(m, mul, elems),
    }


def hunt_chain_moufang(n: int, one_idx: int, timeout_ms: int = 10000) -> dict[str, Any]:
    """Search for a strictly non-associative Moufang quantale on the chain 0 < 1 < ... < n-1."""
    t0 = time.perf_counter()
    s = z3.Solver()
    s.set('timeout', timeout_ms)
    elem_sort, elems = z3.EnumSort(f'CM_{n}_{one_idx}', [f'e{i}' for i in range(n)])
    mul = z3.Function('mul', elem_sort, elem_sort, elem_sort)
    rank = z3.Function('rank', elem_sort, z3.IntSort())

    for i in range(n):
        s.add(rank(elems[i]) == i)
        s.add(mul(elems[0], elems[i]) == elems[0], mul(elems[i], elems[0]) == elems[0])
        s.add(mul(elems[one_idx], elems[i]) == elems[i], mul(elems[i], elems[one_idx]) == elems[i])

    for i in range(n):
        for j in range(n - 1):
            s.add(rank(mul(elems[i], elems[j])) <= rank(mul(elems[i], elems[j + 1])))
            s.add(rank(mul(elems[j], elems[i])) <= rank(mul(elems[j + 1], elems[i])))

    for x in elems:
        for y in elems:
            s.add(mul(mul(x, x), y) == mul(x, mul(x, y)))
            s.add(mul(mul(y, x), x) == mul(y, mul(x, x)))
            s.add(mul(mul(x, y), x) == mul(x, mul(y, x)))
            for z in elems:
                s.add(mul(x, mul(y, mul(x, z))) == mul(mul(mul(x, y), x), z))
                s.add(mul(z, mul(x, mul(y, x))) == mul(mul(mul(z, x), y), x))
                s.add(mul(mul(x, y), mul(z, x)) == mul(x, mul(mul(y, z), x)))

    non_assoc = [
        mul(mul(elems[i], elems[j]), elems[k]) != mul(elems[i], mul(elems[j], elems[k]))
        for i in range(1, n)
        for j in range(1, n)
        for k in range(1, n)
        if i != one_idx and j != one_idx and k != one_idx
    ]
    s.add(z3.Or(non_assoc))

    chk = s.check()
    dt = round(time.perf_counter() - t0, 3)
    if chk != z3.sat:
        return {'n': n, 'one_idx': one_idx, 'status': str(chk), 'elapsed_s': dt}
    m = s.model()
    return {
        'n': n,
        'one_idx': one_idx,
        'status': 'sat',
        'elapsed_s': dt,
        'chain_order': list(range(n)),
        'mul': _extract_table2(m, mul, elems),
    }


def hunt_differential_kleene_drift(n: int, *, require_star_gap: bool = False) -> dict[str, Any]:
    """Search for unital-drift derivations and test D*(a*) == D*(1) * (D*(a))*."""
    t0 = time.perf_counter()
    s = z3.Solver()
    s.set('timeout', 8000)
    elem_sort, elems = z3.EnumSort(f'DK_{n}_{int(require_star_gap)}', [f'e{i}' for i in range(n)])
    add = z3.Function('add', elem_sort, elem_sort, elem_sort)
    mul = z3.Function('mul', elem_sort, elem_sort, elem_sort)
    d = z3.Function('d', elem_sort, elem_sort)
    ds = z3.Function('ds', elem_sort, elem_sort)
    st = z3.Function('st', elem_sort, elem_sort)
    e0, e1 = elems[0], elems[1]

    def leq(x: z3.ExprRef, y: z3.ExprRef) -> z3.BoolRef:
        return add(x, y) == y

    _add_join_semilattice_axioms(s, add, elems)
    _add_distributive_unital_mul_axioms(s, add, mul, elems, commutative=False)
    for x in elems:
        for y in elems:
            for z in elems:
                s.add(mul(mul(x, y), z) == mul(x, mul(y, z)))

    s.add(d(e0) == e0)
    for x in elems:
        for y in elems:
            s.add(d(add(x, y)) == add(d(x), d(y)))
            s.add(d(mul(x, y)) == add(mul(d(x), y), mul(x, d(y))))

    for x in elems:
        s.add(add(x, d(ds(x))) == ds(x))
        s.add(add(e1, mul(x, st(x))) == st(x))
        for y in elems:
            s.add(z3.Implies(leq(add(x, d(y)), y), leq(ds(x), y)))
            s.add(z3.Implies(leq(add(e1, mul(x, y)), y), leq(st(x), y)))

    if require_star_gap:
        s.add(z3.Or([ds(st(x)) != st(ds(x)) for x in elems]))
    else:
        s.add(d(e1) != e0)
        s.add(z3.Or([d(x) != add(mul(d(e1), x), mul(x, d(e1))) for x in elems]))

    chk = s.check()
    dt = round(time.perf_counter() - t0, 3)
    if chk != z3.sat:
        return {'n': n, 'status': str(chk), 'elapsed_s': dt}
    m = s.model()
    add_tbl = _extract_table2(m, add, elems)
    mul_tbl = _extract_table2(m, mul, elems)
    d_tbl = _extract_table1(m, d, elems)
    ds_tbl = _extract_table1(m, ds, elems)
    st_tbl = _extract_table1(m, st, elems)
    corrected_law = all(ds_tbl[st_tbl[x]] == mul_tbl[ds_tbl[1]][st_tbl[ds_tbl[x]]] for x in range(n))
    return {
        'n': n,
        'status': 'sat',
        'elapsed_s': dt,
        'add': add_tbl,
        'mul': mul_tbl,
        'd': d_tbl,
        'd_star': ds_tbl,
        'star': st_tbl,
        'corrected_drift_star_law_holds': corrected_law,
    }


def run_all() -> dict[str, Any]:
    """Execute the full Z3 discovery battery and return a structured report."""
    report: dict[str, Any] = {'z3_version': z3.get_version_string(), 'hunts': {}}

    report['hunts']['jordan_kleene'] = [hunt_jordan_kleene(n) for n in (3, 4)]
    report['hunts']['exceptional_jordan_quantale'] = [hunt_exceptional_jordan_quantale(n) for n in (4, 5)]
    report['hunts']['artin_non_flexible'] = [hunt_alternative_tier(n, 'artin_non_flex') for n in (4, 5)]
    report['hunts']['flexible_non_moufang'] = [hunt_alternative_tier(n, 'flex_non_moufang') for n in (4, 5)]
    report['hunts']['moufang_general_n5'] = hunt_alternative_tier(5, 'moufang_general')

    chain_moufang_results = []
    for n in (5, 6, 7):
        found = False
        for one_idx in range(1, n):
            res = hunt_chain_moufang(n, one_idx)
            chain_moufang_results.append(res)
            if res['status'] == 'sat':
                found = True
                break
        if found:
            break
    report['hunts']['chain_moufang'] = chain_moufang_results

    report['hunts']['differential_drift_non_inner'] = hunt_differential_kleene_drift(3, require_star_gap=False)
    report['hunts']['differential_star_gap'] = hunt_differential_kleene_drift(4, require_star_gap=True)
    return report


def main() -> None:
    report = run_all()
    out_path = Path(__file__).with_name('z3_findings.json')
    out_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Wrote verified Z3 findings to {out_path}')
    for key, val in report['hunts'].items():
        if isinstance(val, list):
            summary = [(item.get('n'), item.get('one_idx'), item.get('status')) for item in val]
            print(f'  {key}: {summary}')
        else:
            print(f"  {key}: n={val.get('n')} status={val.get('status')}")


if __name__ == '__main__':
    main()
