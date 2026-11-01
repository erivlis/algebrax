r"""
Monoid protocols for single-operation algebraic structures with identity elements.

Algebraic Signatures:
    Monoid:                      $\langle V, \mathbf{1}, \cdot \rangle$
                                 with $\mathbf{1} \cdot a = a \cdot \mathbf{1} = a$
    Commutative Monoid:          $\langle V, \mathbf{1}, \cdot \rangle$ with $a \cdot b = b \cdot a$
    Additive Monoid:             $\langle V, \mathbf{0}, + \rangle$ with $\mathbf{0} + a = a + \mathbf{0} = a$
    Additive Commutative Monoid: $\langle V, \mathbf{0}, + \rangle$ with $a + b = b + a$
    Operation Monoid:            $\langle V, \operatorname{identity}, \operatorname{op} \rangle$
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import HasAdd, HasIdentity, HasMul, HasOne, HasOp, HasZero

V = TypeVar('V')


@runtime_checkable
class Monoid(HasOne[V], HasMul[V], Protocol):
    r"""A semigroup equipped with a neutral multiplicative identity element $\mathbf{1}$.

    Algebraic Signature:
        $\langle V, \mathbf{1}, \cdot \rangle, \quad \mathbf{1} \cdot a = a \cdot \mathbf{1} = a$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Associative binary multiplication (`HasMul[V]`).

    Properties:
        - Left Identity: $\mathbf{1} \cdot a = a$.
        - Right Identity: $a \cdot \mathbf{1} = a$.
        - Associativity: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.

    Applications:
        Path concatenation, automata word evaluation, safe empty stream folding, matrix multiplication monoids.
    """

    ...


@runtime_checkable
class CommMonoid(HasOne[V], HasMul[V], Protocol):
    r"""A monoid whose multiplication is commutative: $a \cdot b = b \cdot a$.

    Algebraic Signature:
        $\langle V, \mathbf{1}, \cdot \rangle$ with $a \cdot b = b \cdot a$

    Operations:
        - `one`: Multiplicative identity element (`HasOne[V]`).
        - `mul(a, b)`: Commutative, associative multiplication (`HasMul[V]`).
    """

    ...


CommutativeMonoid = CommMonoid  # Canonical alias


# --- Additive Dual Branch ---


@runtime_checkable
class AddMonoid(HasZero[V], HasAdd[V], Protocol):
    r"""An additive semigroup equipped with a neutral additive identity element $\mathbf{0}$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, + \rangle, \quad \mathbf{0} + a = a + \mathbf{0} = a$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Associative binary addition (`HasAdd[V]`).
    """

    ...


@runtime_checkable
class AddCommMonoid(HasZero[V], HasAdd[V], Protocol):
    r"""An additive monoid whose addition is commutative: $a + b = b + a$.

    Algebraic Signature:
        $\langle V, \mathbf{0}, + \rangle$ with $a + b = b + a$

    Operations:
        - `zero`: Additive neutral element (`HasZero[V]`).
        - `add(a, b)`: Commutative, associative addition (`HasAdd[V]`).
    """

    ...


# --- Domain-Agnostic Single-Operation Branch ---


@runtime_checkable
class OpMonoid(HasIdentity[V], HasOp[V], Protocol):
    r"""Domain-agnostic monoid equipped with a neutral `identity` and associative operation `op`.

    Algebraic Signature:
        $\langle V, \operatorname{identity}, \operatorname{op} \rangle$

    Operations:
        - `identity`: Neutral identity element (`HasIdentity[V]`).
        - `op(a, b)`: Associative binary composition (`HasOp[V]`).
    """

    ...


@runtime_checkable
class OpCommMonoid(HasIdentity[V], HasOp[V], Protocol):
    r"""Domain-agnostic monoid whose operation is commutative: `op(a, b) == op(b, a)`.

    Algebraic Signature:
        $\langle V, \operatorname{identity}, \operatorname{op} \rangle$
        with $\operatorname{op}(a, b) = \operatorname{op}(b, a)$

    Operations:
        - `identity`: Neutral identity element (`HasIdentity[V]`).
        - `op(a, b)`: Commutative, associative binary composition (`HasOp[V]`).
    """

    ...
