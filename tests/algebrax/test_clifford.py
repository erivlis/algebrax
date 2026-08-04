"""
Tests for Clifford Geometric Algebra Cl(p, q, r) and Rotors.
"""

import math

from algebrax.clifford import CliffordSemiring, geometric_product, rotor_rotation


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
