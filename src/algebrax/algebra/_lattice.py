r"""
Order and lattice protocols for algebraic structures with meet and join operations.

Algebraic Signatures (EP-0150 AMDS):
    Join-Semilattice:     $\langle L, \vee \rangle$ (associative, commutative, idempotent)
    Meet-Semilattice:     $\langle L, \wedge \rangle$ (associative, commutative, idempotent)
    Lattice:              $\langle L, \vee, \wedge \rangle$ satisfying absorption:
                          $a \wedge (a \vee b) = a$ and $a \vee (a \wedge b) = a$
    Bounded Lattice:      $\langle L, \vee, \wedge, \bot, \top \rangle$ with $\bot \vee a = a, \ \top \wedge a = a$
    Distributive Lattice: $\langle L, \vee, \wedge \rangle$ with $a \wedge (b \vee c) = (a \wedge b) \vee (a \wedge c)$
    Boolean Algebra:      $\langle B, \vee, \wedge, \neg, \bot, \top \rangle$ (complemented distributive lattice)
"""

from typing import Protocol, TypeVar, runtime_checkable

V = TypeVar('V')


@runtime_checkable
class JoinSemilattice(Protocol[V]):
    r"""Carrier equipped with an associative, commutative, idempotent join ($\vee$, sup).

    Algebraic Signature:
        $\langle L, \vee \rangle, \quad a \vee a = a, \quad a \vee b = b \vee a$
    """

    def join(self, a: V, b: V) -> V: ...


@runtime_checkable
class MeetSemilattice(Protocol[V]):
    r"""Carrier equipped with an associative, commutative, idempotent meet ($\wedge$, inf).

    Algebraic Signature:
        $\langle L, \wedge \rangle, \quad a \wedge a = a, \quad a \wedge b = b \wedge a$
    """

    def meet(self, a: V, b: V) -> V: ...


@runtime_checkable
class Lattice(JoinSemilattice[V], MeetSemilattice[V], Protocol[V]):
    r"""A lattice equipped with meet and join satisfying the absorption laws.

    Algebraic Signature:
        $\langle L, \vee, \wedge \rangle, \quad a \wedge (a \vee b) = a, \quad a \vee (a \wedge b) = a$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `join(a, b)`: Least upper bound ($\vee$).
        - `meet(a, b)`: Greatest lower bound ($\wedge$).

    Properties:
        - Absorption 1: $a \wedge (a \vee b) = a$.
        - Absorption 2: $a \vee (a \wedge b) = a$.

    Applications:
        Access control role graphs, type inference lattices, CRDT state merges, domain theory.
    """

    ...


@runtime_checkable
class BoundedLattice(Lattice[V], Protocol[V]):
    r"""A lattice equipped with bottom ($\bot$) and top ($\top$) elements.

    Algebraic Signature:
        $\langle L, \vee, \wedge, \bot, \top \rangle$
    """

    @property
    def bot(self) -> V: ...

    @property
    def top(self) -> V: ...


@runtime_checkable
class DistributiveLattice(Lattice[V], Protocol[V]):
    r"""A lattice satisfying mutual distributivity of meet over join and join over meet.

    Algebraic Signature:
        $\langle L, \vee, \wedge \rangle$ with $a \wedge (b \vee c) = (a \wedge b) \vee (a \wedge c)$
    """

    ...


@runtime_checkable
class BooleanAlgebra(BoundedLattice[V], DistributiveLattice[V], Protocol[V]):
    r"""A complemented distributive lattice equipped with unary negation (complement).

    Algebraic Signature:
        $\langle B, \vee, \wedge, \neg, \bot, \top \rangle, \quad a \vee \neg a = \top, \quad a \wedge \neg a = \bot$
    """

    def complement(self, a: V) -> V: ...
