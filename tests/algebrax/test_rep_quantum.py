"""Tests for Quantum Groups U_q(sl_2), Yang-Baxter Equation, Braiding & Jones Polynomial."""

from __future__ import annotations

import cmath

import pytest

from algebrax.algebra._hopf import Bialgebra, Coalgebra, HopfAlgebra
from algebrax.matrix.core import dot
from algebrax.rep import (
    QuantumSL2,
    braid_to_matrix,
    braiding_operator,
    jones_polynomial_eval,
    quantum_trace,
    universal_r_matrix_sl2_fundamental,
)
from algebrax.rep.lie import spin_representation as classical_spin_representation
from algebrax.rep.quantum import _embed_two_site_operator
from algebrax.verification import (
    semiring_elements_equal,
    verify_artin_braid_relations,
    verify_hopf_algebra_laws,
    verify_quantum_sl2_relations,
    verify_yang_baxter_equation,
)


def _mat_close(
    lhs: dict[int, dict[int, complex | float]],
    rhs: dict[int, dict[int, complex | float]],
    tol: float = 1e-9,
) -> bool:
    for r in set(lhs.keys()) | set(rhs.keys()):
        row_l = lhs.get(r, {})
        row_r = rhs.get(r, {})
        for c in set(row_l.keys()) | set(row_r.keys()):
            if abs(complex(row_l.get(c, 0.0)) - complex(row_r.get(c, 0.0))) > tol:
                return False
    return True


def _kron_sparse(
    a: dict[int, dict[int, complex]],
    b: dict[int, dict[int, complex]],
    dim_b: int,
) -> dict[int, dict[int, complex]]:
    out: dict[int, dict[int, complex]] = {}
    for r1, row_a in a.items():
        for c1, va in row_a.items():
            for r2, row_b in b.items():
                for c2, vb in row_b.items():
                    val = complex(va) * complex(vb)
                    if abs(val) > 1e-13:
                        out.setdefault(r1 * dim_b + r2, {})[c1 * dim_b + c2] = val
    return out


def _add_sparse(
    a: dict[int, dict[int, complex]],
    b: dict[int, dict[int, complex]],
) -> dict[int, dict[int, complex]]:
    out: dict[int, dict[int, complex]] = {r: dict(row) for r, row in a.items()}
    for r, row in b.items():
        target = out.setdefault(r, {})
        for c, v in row.items():
            target[c] = target.get(c, 0.0 + 0.0j) + complex(v)
    return {r: {c: v for c, v in row.items() if abs(v) > 1e-13} for r, row in out.items()}


# =============================================================================
# 1. QuantumSL2 Protocol, q-Combinatorics & Non-Cocommutative Hopf Axioms
# =============================================================================


class TestQuantumSL2HopfAlgebra:
    """Verify U_q(sl_2) as a concrete non-cocommutative HopfAlgebra."""

    def test_protocol_conformance(self) -> None:
        u_q = QuantumSL2(1.4)
        assert isinstance(u_q, Coalgebra)
        assert isinstance(u_q, Bialgebra)
        assert isinstance(u_q, HopfAlgebra)

    def test_q_combinatorics_and_pascal_identity(self) -> None:
        q = cmath.exp(0.37j) * 1.1
        u_q = QuantumSL2(q)
        assert abs(u_q.q_bracket(0)) < 1e-14
        assert abs(u_q.q_bracket(1) - 1.0) < 1e-14
        assert abs(u_q.q_bracket(2) - (q + 1.0 / q)) < 1e-13
        assert abs(u_q.q_bracket(-3) + u_q.q_bracket(3)) < 1e-13
        assert abs(u_q.q_factorial(0) - 1.0) < 1e-14
        assert abs(u_q.q_factorial(3) - u_q.q_bracket(1) * u_q.q_bracket(2) * u_q.q_bracket(3)) < 1e-13

        # Gaussian q-Pascal identity: C_q(n, k) = q^k C_q(n-1, k) + q^{-(n-k)} C_q(n-1, k-1)
        for n in range(1, 6):
            for k in range(1, n):
                lhs = u_q.q_binomial(n, k)
                rhs = (q**k) * u_q.q_binomial(n - 1, k) + (q ** (-(n - k))) * u_q.q_binomial(n - 1, k - 1)
                assert abs(lhs - rhs) < 1e-12
        assert abs(u_q.q_binomial(4, -1)) < 1e-14
        assert abs(u_q.q_binomial(4, 5)) < 1e-14

    def test_q_combinatorics_classical_limits(self) -> None:
        u_pos = QuantumSL2(1.0)
        assert abs(u_pos.q_bracket(5) - 5.0) < 1e-14
        assert abs(u_pos.q_factorial(5) - 120.0) < 1e-14
        assert abs(u_pos.q_binomial(5, 2) - 10.0) < 1e-14

        u_neg = QuantumSL2(-1.0)
        assert abs(u_neg.q_bracket(3) - 3.0) < 1e-14
        assert abs(u_neg.q_bracket(4) + 4.0) < 1e-14

    def test_non_cocommutativity_and_non_involutive_antipode(self) -> None:
        q = cmath.exp(0.4j)
        u_q = QuantumSL2(q)

        # Coproduct Delta(E) != Delta^{op}(E)
        delta_e = u_q.coproduct(u_q.E)
        delta_e_op = {(v, u): coeff for (u, v), coeff in delta_e.items()}
        assert not semiring_elements_equal(delta_e, delta_e_op, tol=1e-9)

        # Antipode S^2 != id: S^2(E) = q^{-2} E, S^2(F) = q^2 F
        s2_e = u_q.antipode(u_q.antipode(u_q.E))
        s2_f = u_q.antipode(u_q.antipode(u_q.F))
        assert semiring_elements_equal(s2_e, u_q.smul(q ** (-2), u_q.E), tol=1e-11)
        assert semiring_elements_equal(s2_f, u_q.smul(q**2, u_q.F), tol=1e-11)
        assert not semiring_elements_equal(s2_e, u_q.E, tol=1e-6)

    @pytest.mark.parametrize('q', [1.4, cmath.exp(0.35j), 1.2 * cmath.exp(-0.5j)])
    def test_verify_hopf_algebra_laws(self, q: complex) -> None:
        u_q = QuantumSL2(q)
        r_samples: list[complex] = [1.0 + 0.0j, -0.5 + 0.25j, 0.0 + 1.0j]
        c_samples = [
            u_q.one,
            u_q.E,
            u_q.F,
            u_q.K,
            u_q.K_inv,
            u_q.mul(u_q.E, u_q.K),
            u_q.mul(u_q.E, u_q.F),
            u_q.add(u_q.E, u_q.smul(0.5j, u_q.F)),
        ]
        results = verify_hopf_algebra_laws(u_q, r_samples, c_samples, tol=1e-8)
        assert all(results.values()), f'Failed Hopf axioms for q={q}: {results}'

    def test_coproduct_is_algebra_homomorphism(self) -> None:
        q = cmath.exp(0.42j) * 1.15
        u_q = QuantumSL2(q)
        elems = [u_q.E, u_q.F, u_q.K, u_q.K_inv, u_q.mul(u_q.E, u_q.F)]
        for a in elems:
            for b in elems:
                lhs = u_q.coproduct(u_q.mul(a, b))
                rhs = u_q._mul_tensor(u_q.coproduct(a), u_q.coproduct(b))
                assert semiring_elements_equal(lhs, rhs, tol=1e-9)

    def test_validation_errors(self) -> None:
        with pytest.raises(ValueError, match='non-zero'):
            QuantumSL2(0.0)
        with pytest.raises(ValueError, match='finite'):
            QuantumSL2(float('nan'))
        u_q = QuantumSL2(1.3)
        with pytest.raises(ValueError, match='n >= 0'):
            u_q.q_factorial(-1)
        with pytest.raises(ValueError, match='n >= 0'):
            u_q.q_binomial(-1, 0)
        u_one = QuantumSL2(1.0)
        with pytest.raises(ValueError, match='PBW commutation'):
            u_one.mul(u_one.F, u_one.E)


# =============================================================================
# 2. Spin-j Representations & Classical q -> 1 Limit
# =============================================================================


class TestQuantumSpinRepresentations:
    """Verify q-deformed spin-j modules and smooth classical sl_2 convergence."""

    @pytest.mark.parametrize('j_halves', [0, 1, 2, 3, 4])
    @pytest.mark.parametrize('q', [1.35, cmath.exp(0.45j), 1.0, -1.0])
    def test_spin_representation_relations(self, j_halves: int, q: complex) -> None:
        u_q = QuantumSL2(q)
        rep = u_q.spin_representation(j_halves)
        checks = verify_quantum_sl2_relations(q, rep, tol=1e-9)
        assert all(checks.values()), f'Failed relations for j_halves={j_halves}, q={q}: {checks}'

    def test_evaluate_rep_is_algebra_homomorphism(self) -> None:
        q = 1.2 * cmath.exp(0.3j)
        u_q = QuantumSL2(q)
        rep = u_q.spin_representation(3)  # spin 3/2 (4x4)
        x = u_q.add(u_q.mul(u_q.F, u_q.E), u_q.smul(0.7j, u_q.K))
        y = u_q.add(u_q.mul(u_q.E, u_q.K_inv), u_q.F)
        lhs = u_q.evaluate_rep(u_q.mul(x, y), rep)
        rhs = dot(u_q.evaluate_rep(x, rep), u_q.evaluate_rep(y, rep))
        assert _mat_close(lhs, rhs, tol=1e-9)

    @pytest.mark.parametrize('j_halves', [0, 1, 2, 3, 4])
    def test_classical_limit_matches_lie_spin_representation(self, j_halves: int) -> None:
        q_rep = QuantumSL2(1.0).spin_representation(j_halves)
        lie_rep = classical_spin_representation(j_halves, form='sl2')
        # In classical sl_2 form: generators=['E_{01}', 'E_{10}', 'H_0'] -> 0: E, 1: F, 2: H
        e_classical = lie_rep(0)
        f_classical = lie_rep(1)
        h_classical = lie_rep(2)

        assert _mat_close(q_rep['E'], e_classical, tol=1e-11)
        assert _mat_close(q_rep['F'], f_classical, tol=1e-11)
        # [E, F] = H in classical limit
        ef = dot(q_rep['E'], q_rep['F'])
        fe = dot(q_rep['F'], q_rep['E'])
        neg_fe = {r: {c: -v for c, v in row.items()} for r, row in fe.items()}
        comm = _add_sparse(ef, neg_fe)
        assert _mat_close(comm, h_classical, tol=1e-11)

    def test_negative_spin_rejected(self) -> None:
        with pytest.raises(ValueError, match='non-negative'):
            QuantumSL2(1.3).spin_representation(-1)


# =============================================================================
# 3. Universal R-Matrix, Yang-Baxter Equation & Artin Braid Group
# =============================================================================


class TestYangBaxterAndBraiding:
    """Verify QYBE, U_q(sl_2) intertwining, Hecke quadratic relation, and Artin braid relations."""

    @pytest.mark.parametrize('q', [1.4, cmath.exp(0.37j), 0.9 * cmath.exp(-0.8j), 1.0])
    def test_yang_baxter_equation_passes(self, q: complex) -> None:
        r_mat = universal_r_matrix_sl2_fundamental(q)
        checks = verify_yang_baxter_equation(r_mat, dim=2, tol=1e-9)
        assert all(checks.values()), f'QYBE failed for q={q}: {checks}'

    def test_braiding_operator_intertwines_coproduct_and_satisfies_hecke(self) -> None:
        q = 1.15 * cmath.exp(0.37j)
        u_q = QuantumSL2(q)
        rep = u_q.spin_representation(1)
        eye2 = {0: {0: 1.0 + 0.0j}, 1: {1: 1.0 + 0.0j}}

        delta_e = _add_sparse(_kron_sparse(rep['E'], eye2, 2), _kron_sparse(rep['K'], rep['E'], 2))
        delta_f = _add_sparse(_kron_sparse(rep['F'], rep['K_inv'], 2), _kron_sparse(eye2, rep['F'], 2))
        delta_k = _kron_sparse(rep['K'], rep['K'], 2)

        b_mat = braiding_operator(universal_r_matrix_sl2_fundamental(q), dim=2)
        for gen_delta in (delta_e, delta_f, delta_k):
            assert _mat_close(dot(b_mat, gen_delta), dot(gen_delta, b_mat), tol=1e-11)

        # Hecke relation: (B - q I)(B + q^-1 I) = 0
        eye4 = {i: {i: 1.0 + 0.0j} for i in range(4)}
        b_minus_q = _add_sparse(b_mat, {i: {i: -q} for i in range(4)})
        b_plus_qinv = _add_sparse(b_mat, {i: {i: 1.0 / q} for i in range(4)})
        assert _mat_close(dot(b_minus_q, b_plus_qinv), {}, tol=1e-11)

        # Non-symmetric braiding: B^2 != I for q^2 != 1
        assert not _mat_close(dot(b_mat, b_mat), eye4, tol=1e-6)

        # Classical limit q = 1 recovers symmetric flip P with P^2 = I
        b_classical = braiding_operator(universal_r_matrix_sl2_fundamental(1.0), dim=2)
        assert _mat_close(dot(b_classical, b_classical), eye4, tol=1e-12)

    def test_artin_braid_relations_three_and_four_strands(self) -> None:
        q = cmath.exp(0.52j) * 1.08
        b_mat = braiding_operator(universal_r_matrix_sl2_fundamental(q), dim=2)

        # 3 strands
        b1_3 = _embed_two_site_operator(b_mat, 0, 3, dim=2)
        b2_3 = _embed_two_site_operator(b_mat, 1, 3, dim=2)
        checks_3 = verify_artin_braid_relations(b1_3, b2_3, tol=1e-10)
        assert all(checks_3.values())

        # 4 strands (includes far commutativity B_1 B_3 = B_3 B_1)
        b1_4 = _embed_two_site_operator(b_mat, 0, 4, dim=2)
        b2_4 = _embed_two_site_operator(b_mat, 1, 4, dim=2)
        b3_4 = _embed_two_site_operator(b_mat, 2, 4, dim=2)
        checks_4 = verify_artin_braid_relations(b1_4, b2_4, b3_4, tol=1e-10)
        assert all(checks_4.values())

    def test_braid_inverse_cancellation(self) -> None:
        q = cmath.exp(0.33j) * 1.2
        eye8 = {i: {i: 1.0 + 0.0j} for i in range(8)}
        mat = braid_to_matrix([1, 2, -2, -1], 3, q)
        assert _mat_close(mat, eye8, tol=1e-11)


# =============================================================================
# 4. Quantum Trace & Jones Polynomial Invariants
# =============================================================================


class TestQuantumTraceAndJonesPolynomial:
    """Verify quantum trace, Markov I/II invariance, and exact knot/link polynomials."""

    def test_quantum_trace_identity_equals_quantum_dimension_power(self) -> None:
        q = cmath.exp(0.41j) * 1.1
        for n in (1, 2, 3, 4):
            eye = {i: {i: 1.0 + 0.0j} for i in range(2**n)}
            expected = (q + 1.0 / q) ** n
            assert abs(quantum_trace(eye, n, q) - expected) < 1e-11

    @pytest.mark.parametrize('q', [1.3, cmath.exp(0.37j), 1.15 * cmath.exp(-0.6j)])
    def test_canonical_knots_and_links(self, q: complex) -> None:
        t = q ** (-2)

        # Unknot in multiple braid presentations (Markov II invariance)
        for word, strands in (([], 1), ([1], 2), ([-1], 2), ([1, 2], 3), ([1, -2], 3)):
            assert abs(jones_polynomial_eval(word, strands, q) - 1.0) < 1e-11

        # 2-component and 3-component unlinks
        assert abs(jones_polynomial_eval([], 2, q) - (-(q + 1.0 / q))) < 1e-11
        assert abs(jones_polynomial_eval([], 3, q) - ((q + 1.0 / q) ** 2)) < 1e-11

        # Positive Hopf link & its Markov II stabilizations: -(t^{1/2} + t^{5/2}) with t^{1/2} = q^{-1}
        hopf_expected = -(q ** (-1) + q ** (-5))
        for word, strands in (([1, 1], 2), ([1, 1, 2], 3), ([1, 1, -2], 3)):
            assert abs(jones_polynomial_eval(word, strands, q) - hopf_expected) < 1e-11

        # Right-handed trefoil 3_1: t + t^3 - t^4
        trefoil_r = jones_polynomial_eval([1, 1, 1], 2, q)
        assert abs(trefoil_r - (t + t**3 - t**4)) < 1e-11

        # Left-handed trefoil (mirror): t^{-1} + t^{-3} - t^{-4}
        trefoil_l = jones_polynomial_eval([-1, -1, -1], 2, q)
        assert abs(trefoil_l - (t ** (-1) + t ** (-3) - t ** (-4))) < 1e-11

        # Chiral distinction between right-handed and left-handed trefoil
        assert abs(trefoil_r - trefoil_l) > 1e-3

        # Figure-eight knot 4_1: t^{-2} - t^{-1} + 1 - t + t^2 (amphichiral!)
        fig8 = jones_polynomial_eval([1, -2, 1, -2], 3, q)
        fig8_expected = t ** (-2) - t ** (-1) + 1.0 - t + t**2
        assert abs(fig8 - fig8_expected) < 1e-10
        assert abs(fig8 - jones_polynomial_eval([1, -2, 1, -2], 3, 1.0 / q)) < 1e-10

    def test_markov_conjugation_invariance(self) -> None:
        q = cmath.exp(0.49j) * 1.07
        v1 = jones_polynomial_eval([1, 2, 1, 1, -2], 3, q)
        v2 = jones_polynomial_eval([2, 1, 1, -2, 1], 3, q)
        v3 = jones_polynomial_eval([1, -2, 1, 2, 1], 3, q)
        assert abs(v1 - v2) < 1e-11
        assert abs(v1 - v3) < 1e-11

    def test_jones_classical_limit_q_equals_one(self) -> None:
        # At q = 1 (t = 1): V_L(1) = (-2)^{c(L) - 1}
        assert abs(jones_polynomial_eval([1, 1, 1], 2, 1.0) - 1.0) < 1e-12
        assert abs(jones_polynomial_eval([1, -2, 1, -2], 3, 1.0) - 1.0) < 1e-12
        assert abs(jones_polynomial_eval([1, 1], 2, 1.0) + 2.0) < 1e-12

    def test_jones_and_braid_validation_errors(self) -> None:
        with pytest.raises(ValueError, match='singular'):
            jones_polynomial_eval([1, 1, 1], 2, 1.0j)
        with pytest.raises(ValueError, match='out of bounds'):
            braid_to_matrix([2], 2, 1.3)
        with pytest.raises(ValueError, match='out of bounds'):
            braid_to_matrix([0], 3, 1.3)
        with pytest.raises(ValueError, match='num_strands'):
            braid_to_matrix([], 0, 1.3)


# =============================================================================
# 5. Popper Falsification Tests
# =============================================================================


class TestQuantumFalsification:
    """Ensure every quantum verifier genuinely rejects broken/perturbed inputs."""

    def test_perturbed_r_matrix_fails_yang_baxter(self) -> None:
        q = 1.3 * cmath.exp(0.25j)
        r_bad = universal_r_matrix_sl2_fundamental(q)
        r_bad[2][1] = r_bad[2][1] + 0.35
        checks = verify_yang_baxter_equation(r_bad, dim=2, tol=1e-9)
        assert not checks['yang_baxter']
        assert not checks['braid_form']

    def test_zero_r_matrix_fails_non_zero_check(self) -> None:
        checks = verify_yang_baxter_equation({}, dim=2, tol=1e-9)
        assert not checks['non_zero']

    def test_corrupted_spin_rep_fails_quantum_sl2_relations(self) -> None:
        q = 1.35
        rep = QuantumSL2(q).spin_representation(2)
        rep['E'][0][1] = rep['E'][0][1] * 1.25
        checks = verify_quantum_sl2_relations(q, rep, tol=1e-9)
        assert not checks['e_f_commutator']

    def test_non_braiding_matrices_fail_artin_relations(self) -> None:
        q = 1.4
        b_mat = braiding_operator(universal_r_matrix_sl2_fundamental(q), dim=2)
        b1 = _embed_two_site_operator(b_mat, 0, 3, dim=2)
        b2 = _embed_two_site_operator(b_mat, 1, 3, dim=2)
        # Corrupt one diagonal entry of b2
        b2[0][0] = b2[0][0] + 0.5
        checks = verify_artin_braid_relations(b1, b2, tol=1e-9)
        assert not checks['braid_relation']
