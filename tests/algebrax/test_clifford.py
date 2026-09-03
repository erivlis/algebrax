import cmath
import math

from algebrax.clifford import (
    CliffordSemiring,
    GeneralizedCliffordSemiring,
    QuantumCliffordSemiring,
    gca_product,
    geometric_product,
    quantum_clifford_product,
    rotor_rotation,
)


def test_clifford_blade_multiplication_cl30():
    """
    Test Cl(3, 0) blade multiplication:
    - e1 * e1 = 1, e2 * e2 = 1
    - e1 * e2 = e12, e2 * e1 = -e12
    - (e1 + e2)^2 = e1^2 + e1 e2 + e2 e1 + e2^2 = 2.0
    """
    cs = CliffordSemiring(p=3, q=0, r=0)

    # v = e1 + e2 => {(1,): 1.0, (2,): 1.0}
    v = {(1,): 1.0, (2,): 1.0}
    v_sq = cs.mul(v, v)
    assert v_sq == {(): 2.0}


def test_clifford_3d_rotor_rotation():
    """
    Rotate vector e1 along e12 bivector plane by 90 degrees (pi/2).
    Expected result: e2 (0, 1.0, 0).
    """
    v = {(1,): 1.0}  # e1 vector
    v_rot = rotor_rotation(v, bivector=(1, 2), angle_rad=math.pi / 2.0, p=3, q=0, r=0)

    # Expected: e2 => {(2,): 1.0}
    assert abs(v_rot.get((2,), 0.0) - 1.0) < 1e-6
    assert abs(v_rot.get((1,), 0.0)) < 1e-6


def test_generalized_clifford_clock_and_shift():
    """
    Test Generalized Clifford Algebra C_3^(2) with omega = exp(2*pi*i / 3):
    - e1 * e2 = omega * e2 * e1
    - e1^3 = 1, e2^3 = 1
    - Multiplicative identity one = {(0, 0): 1.0}
    """
    gca = GeneralizedCliffordSemiring(n_order=3, num_generators=2)
    e1 = {(1, 0): 1.0 + 0j}
    e2 = {(0, 1): 1.0 + 0j}

    # e1 * e2 vs e2 * e1
    e1_e2 = gca.mul(e1, e2)
    e2_e1 = gca.mul(e2, e1)

    omega = cmath.exp(2j * cmath.pi / 3)
    assert (1, 1) in e1_e2
    assert (1, 1) in e2_e1
    assert cmath.isclose(e1_e2[(1, 1)] / e2_e1[(1, 1)], omega, abs_tol=1e-7)

    # e1^3 = 1
    e1_sq = gca.mul(e1, e1)
    e1_cube = gca.mul(e1_sq, e1)
    assert (0, 0) in e1_cube
    assert cmath.isclose(e1_cube[(0, 0)], 1.0 + 0j, abs_tol=1e-7)

    # Helper function gca_product
    prod = gca_product(e1, e2, n_order=3, num_generators=2)
    assert prod == e1_e2


def test_quantum_clifford_q_deformation():
    """
    Test q-Deformed Quantum Clifford Algebra Cl_q(2):
    - e2 * e1 = -q * e1 * e2
    - When q = 1, recovers standard anticommutation e2 * e1 = -e1 * e2
    """
    qc = QuantumCliffordSemiring(q=0.5, num_generators=2)
    e1 = {(1, 0): 1.0 + 0j}
    e2 = {(0, 1): 1.0 + 0j}

    e1_e2 = qc.mul(e1, e2)
    e2_e1 = qc.mul(e2, e1)

    assert e1_e2 == {(1, 1): 1.0 + 0j}
    assert e2_e1 == {(1, 1): -0.5 + 0j}

    # Helper function
    prod = quantum_clifford_product(e2, e1, q=0.5, num_generators=2)
    assert prod == e2_e1
