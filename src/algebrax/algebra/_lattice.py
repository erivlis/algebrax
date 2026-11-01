r"""
Order and lattice protocols for algebraic structures with meet and join operations.

Algebraic Signatures:
    Join-Semilattice:     $\langle V, \vee \rangle$ (associative, commutative, idempotent)
    Meet-Semilattice:     $\langle V, \wedge \rangle$ (associative, commutative, idempotent)
    Lattice:              $\langle V, \vee, \wedge \rangle$ satisfying absorption:
                          $a \wedge (a \vee b) = a$ and $a \vee (a \wedge b) = a$
    Bounded Lattice:      $\langle V, \vee, \wedge, \bot, \top \rangle$ with $\bot \vee a = a, \ \top \wedge a = a$
    Distributive Lattice: $\langle V, \vee, \wedge \rangle$ with $a \wedge (b \vee c) = (a \wedge b) \vee (a \wedge c)$
    Boolean Algebra:      $\langle V, \vee, \wedge, \bot, \top, \neg \rangle$ (complemented distributive lattice)
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import HasBounds, HasComplement, HasJoin, HasMeet

V = TypeVar('V')


@runtime_checkable
class JoinSemilattice(HasJoin[V], Protocol):
    r"""Carrier equipped with an associative, commutative, idempotent join ($\vee$, sup).

    Algebraic Signature:
        $\langle V, \vee \rangle, \quad a \vee a = a, \quad a \vee b = b \vee a$

    Operations:
        - `join(a, b)`: Least upper bound $\vee$ (`HasJoin[V]`).
    """

    ...


@runtime_checkable
class MeetSemilattice(HasMeet[V], Protocol):
    r"""Carrier equipped with an associative, commutative, idempotent meet ($\wedge$, inf).

    Algebraic Signature:
        $\langle V, \wedge \rangle, \quad a \wedge a = a, \quad a \wedge b = b \wedge a$

    Operations:
        - `meet(a, b)`: Greatest lower bound $\wedge$ (`HasMeet[V]`).
    """

    ...


@runtime_checkable
class Lattice(HasJoin[V], HasMeet[V], Protocol):
    r"""A lattice equipped with join and meet satisfying the absorption laws.

    Algebraic Signature:
        $\langle V, \vee, \wedge \rangle, \quad a \wedge (a \vee b) = a, \quad a \vee (a \wedge b) = a$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `join(a, b)`: Least upper bound $\vee$ (`HasJoin[V]`).
        - `meet(a, b)`: Greatest lower bound $\wedge$ (`HasMeet[V]`).

    Properties:
        - Absorption 1: $a \wedge (a \vee b) = a$.
        - Absorption 2: $a \vee (a \wedge b) = a$.

    Applications:
        Access control role graphs, type inference lattices, CRDT state merges, domain theory.
    """

    ...


@runtime_checkable
class BoundedLattice(HasJoin[V], HasMeet[V], HasBounds[V], Protocol):
    r"""A lattice equipped with bottom ($\bot$) and top ($\top$) elements.

    Algebraic Signature:
        $\langle V, \vee, \wedge, \bot, \top \rangle$

    Operations:
        - `join(a, b)`: Least upper bound $\vee$ (`HasJoin[V]`).
        - `meet(a, b)`: Greatest lower bound $\wedge$ (`HasMeet[V]`).
        - `bot`: Least element $\bot$ (`HasBounds[V]`).
        - `top`: Greatest element $\top$ (`HasBounds[V]`).
    """

    ...


@runtime_checkable
class DistributiveLattice(HasJoin[V], HasMeet[V], Protocol):
    r"""A lattice satisfying mutual distributivity of meet over join and join over meet.

    Algebraic Signature:
        $\langle V, \vee, \wedge \rangle$ with $a \wedge (b \vee c) = (a \wedge b) \vee (a \wedge c)$

    Operations:
        - `join(a, b)`: Least upper bound $\vee$ (`HasJoin[V]`).
        - `meet(a, b)`: Greatest lower bound $\wedge$ (`HasMeet[V]`).
    """

    ...


@runtime_checkable
class BooleanAlgebra(HasJoin[V], HasMeet[V], HasBounds[V], HasComplement[V], Protocol):
    r"""A complemented distributive lattice equipped with unary negation (complement).

    Algebraic Signature:
        $\langle V, \vee, \wedge, \bot, \top, \neg \rangle, \quad a \vee \neg a = \top, \quad a \wedge \neg a = \bot$

    Operations:
        - `join(a, b)`: Disjunction / least upper bound $\vee$ (`HasJoin[V]`).
        - `meet(a, b)`: Conjunction / greatest lower bound $\wedge$ (`HasMeet[V]`).
        - `bot`: Bottom element $\bot$ (`HasBounds[V]`).
        - `top`: Top element $\top$ (`HasBounds[V]`).
        - `complement(a)`: Unary complement $\neg a$ (`HasComplement[V]`).
    """

    ...
