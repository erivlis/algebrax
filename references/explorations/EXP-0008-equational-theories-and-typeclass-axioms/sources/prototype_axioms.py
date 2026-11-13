"""Prototypes and comparative empirical benchmarks for EXP-0008:
Equational Theories, Law Witness Mixins, and Characteristic Derived Methods.

Demonstrates:
1. False-positive isinstance collision in current signature-only protocols.
2. Pillar 2: Law Witness Mixins (zero-cost inheritance, correct isinstance, mypy typing).
3. Pillar 3: Canonical Derived Operations (associator, jordan_triple, jacobian).
"""

from __future__ import annotations

import sys
from typing import ClassVar, Generic, Literal, Protocol, TypeVar, runtime_checkable

V = TypeVar("V")
R = TypeVar("R")
M = TypeVar("M")


# =============================================================================
# Baseline: Current Status Quo (Signature-only, blind to equational axioms)
# =============================================================================

@runtime_checkable
class BaselineHasScale(Protocol[R, M]):
    def smul(self, r: R, m: M) -> M: ...

@runtime_checkable
class BaselineHasZero(Protocol[V]):
    @property
    def zero(self) -> V: ...

@runtime_checkable
class BaselineHasAdd(Protocol[V]):
    def add(self, a: V, b: V) -> V: ...

@runtime_checkable
class BaselineHasNeg(Protocol[V]):
    def neg(self, a: V) -> V: ...

@runtime_checkable
class BaselineHasMul(Protocol[V]):
    def mul(self, a: V, b: V) -> V: ...

@runtime_checkable
class BaselineJordanAlgebra(
    BaselineHasScale[R, M], BaselineHasZero[M], BaselineHasAdd[M], BaselineHasNeg[M], BaselineHasMul[M], Protocol[R, M]
): ...

@runtime_checkable
class BaselineAlternativeAlgebra(
    BaselineHasScale[R, M], BaselineHasZero[M], BaselineHasAdd[M], BaselineHasNeg[M], BaselineHasMul[M], Protocol[R, M]
): ...

@runtime_checkable
class BaselineMalcevAlgebra(
    BaselineHasScale[R, M], BaselineHasZero[M], BaselineHasAdd[M], BaselineHasNeg[M], BaselineHasMul[M], Protocol[R, M]
): ...


class BaselineLieSo3(BaselineMalcevAlgebra[float, dict[int, float]]):
    """Anticommutative Lie algebra so(3)."""
    @property
    def zero(self) -> dict[int, float]:
        return {}
    def add(self, a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
        out = dict(a)
        for k, v in b.items():
            out[k] = out.get(k, 0.0) + v
        return out
    def neg(self, a: dict[int, float]) -> dict[int, float]:
        return {k: -v for k, v in a.items()}
    def smul(self, r: float, m: dict[int, float]) -> dict[int, float]:
        return {k: r * v for k, v in m.items()}
    def mul(self, a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
        # Cross product [e_i, e_j]
        c: dict[int, float] = {}
        # Simple commutator
        c[2] = a.get(0, 0.0) * b.get(1, 0.0) - a.get(1, 0.0) * b.get(0, 0.0)
        c[0] = a.get(1, 0.0) * b.get(2, 0.0) - a.get(2, 0.0) * b.get(1, 0.0)
        c[1] = a.get(2, 0.0) * b.get(0, 0.0) - a.get(0, 0.0) * b.get(2, 0.0)
        return {k: v for k, v in c.items() if abs(v) > 1e-12}


# =============================================================================
# Proposed Pillar 2: Law Witness Mixins
# =============================================================================

@runtime_checkable
class LawCommutative(Protocol):
    """Equational axiom witness: binary multiplication is commutative."""
    @property
    def is_commutative(self) -> Literal[True]: ...

@runtime_checkable
class LawAnticommutative(Protocol):
    """Equational axiom witness: binary multiplication/bracket is anticommutative."""
    @property
    def is_anticommutative(self) -> Literal[True]: ...

@runtime_checkable
class LawAssociative(Protocol):
    """Equational axiom witness: binary multiplication is associative."""
    @property
    def is_associative(self) -> Literal[True]: ...

@runtime_checkable
class LawJordan(Protocol):
    """Equational axiom witness: satisfies Jordan identity (xy)x^2 = x(yx^2)."""
    @property
    def is_jordan(self) -> Literal[True]: ...

@runtime_checkable
class LawAlternative(Protocol):
    """Equational axiom witness: satisfies Artin alternativity (xx)y = x(xy), (yx)x = y(xx)."""
    @property
    def is_alternative(self) -> Literal[True]: ...

@runtime_checkable
class LawMalcev(Protocol):
    """Equational axiom witness: satisfies Malcev identity J(x, y, [x, z]) = [J(x, y, z), x]."""
    @property
    def is_malcev(self) -> Literal[True]: ...


# =============================================================================
# Proposed Pillar 3: Layer 2 Protocols with Axiom Witness & Derived Ops
# =============================================================================

@runtime_checkable
class ProposedJordanAlgebra(
    BaselineHasScale[R, M], BaselineHasZero[M], BaselineHasAdd[M], BaselineHasNeg[M], BaselineHasMul[M],
    LawCommutative, LawJordan,
    Protocol[R, M],
):
    @property
    def is_commutative(self) -> Literal[True]:
        return True

    @property
    def is_jordan(self) -> Literal[True]:
        return True

    def jordan_triple(self, x: M, y: M, z: M) -> M:
        r"""Jordan triple product $\{x, y, z\} = (x \circ y) \circ z + x \circ (y \circ z) - y \circ (x \circ z)$."""
        xy_z = self.mul(self.mul(x, y), z)
        x_yz = self.mul(x, self.mul(y, z))
        y_xz = self.mul(y, self.mul(x, z))
        return self.add(self.add(xy_z, x_yz), self.neg(y_xz))

    def quadratic_repr(self, x: M, y: M) -> M:
        r"""Quadratic representation $U_x(y) = 2 x \circ (x \circ y) - x^2 \circ y$."""
        x_xy = self.mul(x, self.mul(x, y))
        two_x_xy = self.add(x_xy, x_xy)
        x2_y = self.mul(self.mul(x, x), y)
        return self.add(two_x_xy, self.neg(x2_y))


@runtime_checkable
class ProposedAlternativeAlgebra(
    BaselineHasScale[R, M], BaselineHasZero[M], BaselineHasAdd[M], BaselineHasNeg[M], BaselineHasMul[M],
    LawAlternative,
    Protocol[R, M],
):
    @property
    def is_alternative(self) -> Literal[True]:
        return True

    def associator(self, x: M, y: M, z: M) -> M:
        r"""Associator $[x, y, z] = (x \cdot y) \cdot z - x \cdot (y \cdot z)$."""
        xy_z = self.mul(self.mul(x, y), z)
        x_yz = self.mul(x, self.mul(y, z))
        return self.add(xy_z, self.neg(x_yz))


@runtime_checkable
class ProposedMalcevAlgebra(
    BaselineHasScale[R, M], BaselineHasZero[M], BaselineHasAdd[M], BaselineHasNeg[M], BaselineHasMul[M],
    LawAnticommutative, LawMalcev,
    Protocol[R, M],
):
    @property
    def is_anticommutative(self) -> Literal[True]:
        return True

    @property
    def is_malcev(self) -> Literal[True]:
        return True

    def jacobian(self, x: M, y: M, z: M) -> M:
        r"""Jacobian operator $J(x, y, z) = [[x, y], z] + [[y, z], x] + [[z, x], y]$."""
        xy_z = self.mul(self.mul(x, y), z)
        yz_x = self.mul(self.mul(y, z), x)
        zx_y = self.mul(self.mul(z, x), y)
        return self.add(self.add(xy_z, yz_x), zx_y)


# Concrete implementation subclassing ProposedMalcevAlgebra
class ProposedLieSo3(ProposedMalcevAlgebra[float, dict[int, float]]):
    """Anticommutative Lie algebra so(3) nominally subclassing ProposedMalcevAlgebra."""
    @property
    def zero(self) -> dict[int, float]:
        return {}
    def add(self, a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
        out = dict(a)
        for k, v in b.items():
            out[k] = out.get(k, 0.0) + v
        return out
    def neg(self, a: dict[int, float]) -> dict[int, float]:
        return {k: -v for k, v in a.items()}
    def smul(self, r: float, m: dict[int, float]) -> dict[int, float]:
        return {k: r * v for k, v in m.items()}
    def mul(self, a: dict[int, float], b: dict[int, float]) -> dict[int, float]:
        c: dict[int, float] = {}
        c[2] = a.get(0, 0.0) * b.get(1, 0.0) - a.get(1, 0.0) * b.get(0, 0.0)
        c[0] = a.get(1, 0.0) * b.get(2, 0.0) - a.get(2, 0.0) * b.get(1, 0.0)
        c[1] = a.get(2, 0.0) * b.get(0, 0.0) - a.get(0, 0.0) * b.get(2, 0.0)
        return {k: v for k, v in c.items() if abs(v) > 1e-12}


def run_demonstration() -> None:
    print("=== EXP-0008 Empirical Demonstration ===")

    # 1. Baseline False Positive Collision
    so3_old = BaselineLieSo3()
    print("\n1. Baseline Structural Subtyping (Status Quo):")
    print(
        f"   isinstance(so3, BaselineMalcevAlgebra):     {isinstance(so3_old, BaselineMalcevAlgebra)} (Expected True)"
    )
    print(
        f"   isinstance(so3, BaselineJordanAlgebra):     {isinstance(so3_old, BaselineJordanAlgebra)} "
        "(ERROR: False Positive! Lie != Jordan)"
    )
    print(
        f"   isinstance(so3, BaselineAlternativeAlgebra):{isinstance(so3_old, BaselineAlternativeAlgebra)} "
        "(ERROR: False Positive! Lie != Alternative)"
    )

    # 2. Proposed Axiom & Operational Separation
    so3_new = ProposedLieSo3()
    print("\n2. Proposed Axiom-Witness Subtyping (Pillars 2 & 3):")
    print(f"   isinstance(so3, ProposedMalcevAlgebra):     {isinstance(so3_new, ProposedMalcevAlgebra)} (True)")
    print(
        f"   isinstance(so3, ProposedJordanAlgebra):     {isinstance(so3_new, ProposedJordanAlgebra)} "
        "(Correctly False!)"
    )
    print(
        f"   isinstance(so3, ProposedAlternativeAlgebra):{isinstance(so3_new, ProposedAlternativeAlgebra)} "
        "(Correctly False!)"
    )
    print(f"   isinstance(so3, LawAnticommutative):        {isinstance(so3_new, LawAnticommutative)} (True)")
    print(f"   isinstance(so3, LawCommutative):            {isinstance(so3_new, LawCommutative)} (Correctly False!)")

    # 3. Canonical Derived Operations for free
    e1, e2, e3 = {0: 1.0}, {1: 1.0}, {2: 1.0}
    jac = so3_new.jacobian(e1, e2, e3)
    print("\n3. Canonical Derived Operation in Action:")
    print(f"   so3.jacobian(e1, e2, e3): {jac} (Jacobi identity holds -> equals zero!)")
    assert jac == {}
    print("\nAll assertions verified successfully.")


if __name__ == "__main__":
    run_demonstration()
