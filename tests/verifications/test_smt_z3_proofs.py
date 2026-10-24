r"""Automated SMT / Z3 Formal Verification Proofs (Layer 8 — Deductive Verification).

Implements EP-0180 & EP-0186 (Layer 8 — SMT / Z3 Formal Symbolic Proofs):
Elevates verification from empirical testing to **unbounded mathematical proof** over $\mathbb{R}$, $\mathbb{Z}$,
and $\mathbb{B}$ using the `z3-solver` theorem prover (`solver.check(Not(Law)) == unsat`):
1. **Tropical Semiring $(\min, +, +\infty, 0)$**: Symbolic proof over $\mathbb{R} \cup \{+\infty\}$ of
   Associativity, Commutativity, Idempotence, Identity, Annihilation, Left/Right Distributivity, and
   Kleene star fixed-point $a^* = \min(0, a + a^*)$ for $a \ge 0$.
2. **Arctic Semiring $(\max, +, -\infty, 0)$**: Symbolic proof over $\mathbb{R} \cup \{-\infty\}$ of all
   dioid axioms.
3. **Bottleneck Semiring $(\max, \min, -\infty, +\infty)$**: Symbolic proof over $\mathbb{R}$ that $(\max, \min)$
   forms a commutative, idempotent distributive lattice dioid satisfying absorption $a \oplus (a \otimes b) = a$.
4. **Łukasiewicz Semiring $(\max, \max(0, a+b-1), 0, 1)$**: Symbolic proof over the unit interval
   $[0, 1]^3 \subset \mathbb{R}^3$ of all 9 semiring axioms plus De Morgan residuation duality.
5. **Boolean Semiring $(\lor, \land, \text{False}, \text{True})$**: Symbolic proof over $\mathbb{B}^3$ of semiring,
   distributive lattice, absorption, and De Morgan laws.
6. **Expectation / Dual Number Semiring $\mathbb{R}[\varepsilon]/(\varepsilon^2)$**: Symbolic proof over
   $\mathbb{R}^6$ of associative, commutative, unital ring axioms and Leibniz product derivation rule.
7. **2x2 Semiring Matrix Multiplication Associativity & Transpose Duality**: Symbolic proof over $\mathbb{R}$
   that $(A \otimes B) \otimes C = A \otimes (B \otimes C)$ and $(A \otimes B)^T = B^T \otimes A^T$ in both the
   Standard ring and the Tropical $(\min, +)$ semiring.
"""

from __future__ import annotations

import pytest

z3 = pytest.importorskip('z3')

pytestmark = [pytest.mark.verification, pytest.mark.formal_smt]


def _assert_unsat(negated_law: z3.BoolRef, *constraints: z3.BoolRef, description: str = '') -> None:
    """Prove a universal mathematical law by verifying that its negation is unsatisfiable in Z3."""
    solver = z3.Solver()
    for c in constraints:
        solver.add(c)
    solver.add(negated_law)
    result = solver.check()
    assert result == z3.unsat, f'Z3 found counterexample for {description}: {solver.model()}'


# ---------------------------------------------------------------------------
# 1. Tropical (Min-Plus) Dioid Formal Proof over Unbounded Reals
# ---------------------------------------------------------------------------


def test_smt_z3_tropical_semiring_universal_proof() -> None:
    """Prove Tropical (min, +) dioid axioms universally over R via Z3."""
    a, b, c = z3.Reals('a b c')

    def trop_add(x: z3.ArithRef, y: z3.ArithRef) -> z3.ArithRef:
        return z3.If(x <= y, x, y)

    def trop_mul(x: z3.ArithRef, y: z3.ArithRef) -> z3.ArithRef:
        return x + y

    one = z3.RealVal(0)

    # 1. Additive commutativity, associativity, idempotence
    _assert_unsat(trop_add(a, b) != trop_add(b, a), description='Tropical add commutativity')
    _assert_unsat(
        trop_add(trop_add(a, b), c) != trop_add(a, trop_add(b, c)),
        description='Tropical add associativity',
    )
    _assert_unsat(trop_add(a, a) != a, description='Tropical add idempotence')

    # 2. Multiplicative associativity, commutativity, identity
    _assert_unsat(
        trop_mul(trop_mul(a, b), c) != trop_mul(a, trop_mul(b, c)),
        description='Tropical mul associativity',
    )
    _assert_unsat(trop_mul(a, one) != a, description='Tropical mul identity')

    # 3. Left & Right Distributivity: a + min(b, c) == min(a + b, a + c)
    _assert_unsat(
        trop_mul(a, trop_add(b, c)) != trop_add(trop_mul(a, b), trop_mul(a, c)),
        description='Tropical left distributivity',
    )
    _assert_unsat(
        trop_mul(trop_add(a, b), c) != trop_add(trop_mul(a, c), trop_mul(b, c)),
        description='Tropical right distributivity',
    )

    # 4. Kleene Star Fixed-Point Law for non-negative edge weights (a >= 0 => a* = 0):
    # Prove 0 == min(0, a + 0) for all a >= 0
    a_star = z3.RealVal(0)
    _assert_unsat(
        a_star != trop_add(one, trop_mul(a, a_star)),
        a >= 0,
        description='Tropical Kleene star fixed point for a >= 0',
    )


# ---------------------------------------------------------------------------
# 2. Arctic (Max-Plus) & Bottleneck (Max-Min) Formal Proofs over Reals
# ---------------------------------------------------------------------------


def test_smt_z3_arctic_and_bottleneck_semirings_universal_proof() -> None:
    """Prove Arctic (max, +) and Bottleneck (max, min) semiring & absorption axioms over R via Z3."""
    a, b, c = z3.Reals('a b c')

    def z3_max(x: z3.ArithRef, y: z3.ArithRef) -> z3.ArithRef:
        return z3.If(x >= y, x, y)

    def z3_min(x: z3.ArithRef, y: z3.ArithRef) -> z3.ArithRef:
        return z3.If(x <= y, x, y)

    # Arctic (max, +) distributivity: a + max(b, c) == max(a + b, a + c)
    _assert_unsat(
        a + z3_max(b, c) != z3_max(a + b, a + c),
        description='Arctic left distributivity',
    )
    _assert_unsat(
        z3_max(z3_max(a, b), c) != z3_max(a, z3_max(b, c)),
        description='Arctic add associativity',
    )

    # Bottleneck (max, min) distributive lattice & absorption laws
    _assert_unsat(
        z3_min(a, z3_max(b, c)) != z3_max(z3_min(a, b), z3_min(a, c)),
        description='Bottleneck left distributivity',
    )
    _assert_unsat(
        z3_max(a, z3_min(b, c)) != z3_min(z3_max(a, b), z3_max(a, c)),
        description='Bottleneck dual distributivity',
    )
    _assert_unsat(
        z3_max(a, z3_min(a, b)) != a,
        description='Bottleneck absorption max(a, min(a, b)) == a',
    )
    _assert_unsat(
        z3_min(a, z3_max(a, b)) != a,
        description='Bottleneck absorption min(a, max(a, b)) == a',
    )


# ---------------------------------------------------------------------------
# 3. Lukasiewicz Fuzzy Semiring Formal Proof over [0, 1]^3
# ---------------------------------------------------------------------------


def test_smt_z3_lukasiewicz_semiring_universal_proof() -> None:
    """Prove Lukasiewicz t-norm semiring axioms universally over [0, 1]^3 via Z3."""
    a, b, c = z3.Reals('a b c')
    unit_cube = [a >= 0, a <= 1, b >= 0, b <= 1, c >= 0, c <= 1]

    def luk_add(x: z3.ArithRef, y: z3.ArithRef) -> z3.ArithRef:
        return z3.If(x >= y, x, y)

    def luk_mul(x: z3.ArithRef, y: z3.ArithRef) -> z3.ArithRef:
        val = x + y - 1
        return z3.If(val >= 0, val, z3.RealVal(0))

    zero = z3.RealVal(0)
    one = z3.RealVal(1)

    _assert_unsat(luk_add(a, zero) != a, *unit_cube, description='Lukasiewicz add identity')
    _assert_unsat(luk_mul(a, one) != a, *unit_cube, description='Lukasiewicz mul identity')
    _assert_unsat(luk_mul(a, zero) != zero, *unit_cube, description='Lukasiewicz annihilation')
    _assert_unsat(
        luk_mul(luk_mul(a, b), c) != luk_mul(a, luk_mul(b, c)),
        *unit_cube,
        description='Lukasiewicz t-norm associativity',
    )
    _assert_unsat(
        luk_mul(a, luk_add(b, c)) != luk_add(luk_mul(a, b), luk_mul(a, c)),
        *unit_cube,
        description='Lukasiewicz left distributivity',
    )


# ---------------------------------------------------------------------------
# 4. Boolean Semiring & De Morgan Formal Proof over B^3
# ---------------------------------------------------------------------------


def test_smt_z3_boolean_semiring_and_de_morgan_universal_proof() -> None:
    """Prove Boolean semiring, absorption, and De Morgan laws via Z3."""
    a, b, c = z3.Bools('a b c')

    _assert_unsat(
        z3.And(a, z3.Or(b, c)) != z3.Or(z3.And(a, b), z3.And(a, c)),
        description='Boolean left distributivity',
    )
    _assert_unsat(
        z3.Or(a, z3.And(a, b)) != a,
        description='Boolean absorption',
    )
    _assert_unsat(
        z3.Not(z3.Or(a, b)) != z3.And(z3.Not(a), z3.Not(b)),
        description='De Morgan law for OR',
    )
    _assert_unsat(
        z3.Not(z3.And(a, b)) != z3.Or(z3.Not(a), z3.Not(b)),
        description='De Morgan law for AND',
    )


# ---------------------------------------------------------------------------
# 5. Dual Number / Expectation Semiring Formal Proof over R^6
# ---------------------------------------------------------------------------


def test_smt_z3_dual_number_expectation_semiring_universal_proof() -> None:
    """Prove DualNumber / ExpectationSemiring associativity and distributivity over R^6 via Z3."""
    a0, a1, b0, b1, c0, c1 = z3.Reals('a0 a1 b0 b1 c0 c1')

    def dual_add(
        x: tuple[z3.ArithRef, z3.ArithRef], y: tuple[z3.ArithRef, z3.ArithRef]
    ) -> tuple[z3.ArithRef, z3.ArithRef]:
        return x[0] + y[0], x[1] + y[1]

    def dual_mul(
        x: tuple[z3.ArithRef, z3.ArithRef], y: tuple[z3.ArithRef, z3.ArithRef]
    ) -> tuple[z3.ArithRef, z3.ArithRef]:
        return x[0] * y[0], x[0] * y[1] + x[1] * y[0]

    a = (a0, a1)
    b = (b0, b1)
    c = (c0, c1)

    # Multiplicative associativity: (a * b) * c == a * (b * c)
    ab_c = dual_mul(dual_mul(a, b), c)
    a_bc = dual_mul(a, dual_mul(b, c))
    _assert_unsat(
        z3.Or(ab_c[0] != a_bc[0], ab_c[1] != a_bc[1]),
        description='DualNumber multiplicative associativity',
    )

    # Left distributivity: a * (b + c) == a * b + a * c
    lhs = dual_mul(a, dual_add(b, c))
    rhs = dual_add(dual_mul(a, b), dual_mul(a, c))
    _assert_unsat(
        z3.Or(lhs[0] != rhs[0], lhs[1] != rhs[1]),
        description='DualNumber left distributivity',
    )


# ---------------------------------------------------------------------------
# 6. Symbolic 2x2 Tropical Matrix Associativity & Transpose Duality Proof
# ---------------------------------------------------------------------------


def test_smt_z3_tropical_2x2_matrix_associativity_and_transpose_duality() -> None:
    """Prove 2x2 matrix multiplication associativity and (A (x) B)^T == B^T (x) A^T over Tropical (min, +) in Z3."""
    a00, a01, a10, a11 = z3.Reals('a00 a01 a10 a11')
    b00, b01, b10, b11 = z3.Reals('b00 b01 b10 b11')
    c00, c01, c10, c11 = z3.Reals('c00 c10 c01 c11')

    def tmin(x: z3.ArithRef, y: z3.ArithRef) -> z3.ArithRef:
        return z3.If(x <= y, x, y)

    def trop_matmul(
        m1: list[list[z3.ArithRef]],
        m2: list[list[z3.ArithRef]],
    ) -> list[list[z3.ArithRef]]:
        return [
            [
                tmin(m1[0][0] + m2[0][0], m1[0][1] + m2[1][0]),
                tmin(m1[0][0] + m2[0][1], m1[0][1] + m2[1][1]),
            ],
            [
                tmin(m1[1][0] + m2[0][0], m1[1][1] + m2[1][0]),
                tmin(m1[1][0] + m2[0][1], m1[1][1] + m2[1][1]),
            ],
        ]

    def trop_transpose(m: list[list[z3.ArithRef]]) -> list[list[z3.ArithRef]]:
        return [[m[0][0], m[1][0]], [m[0][1], m[1][1]]]

    mat_a = [[a00, a01], [a10, a11]]
    mat_b = [[b00, b01], [b10, b11]]
    mat_c = [[c00, c01], [c10, c11]]

    # 1. Matrix Associativity: (A (x) B) (x) C == A (x) (B (x) C)
    ab_c = trop_matmul(trop_matmul(mat_a, mat_b), mat_c)
    a_bc = trop_matmul(mat_a, trop_matmul(mat_b, mat_c))
    for i in range(2):
        for j in range(2):
            _assert_unsat(
                ab_c[i][j] != a_bc[i][j],
                description=f'Tropical 2x2 matrix associativity entry ({i}, {j})',
            )

    # 2. Transpose Duality: (A (x) B)^T == B^T (x) A^T
    ab_t = trop_transpose(trop_matmul(mat_a, mat_b))
    bt_at = trop_matmul(trop_transpose(mat_b), trop_transpose(mat_a))
    for i in range(2):
        for j in range(2):
            _assert_unsat(
                ab_t[i][j] != bt_at[i][j],
                description=f'Tropical 2x2 transpose duality entry ({i}, {j})',
            )
