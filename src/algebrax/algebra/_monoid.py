r"""
Monoid protocols for single-operation algebraic structures with identity elements.

Algebraic Signatures (EP-0150 AMDS):
    Monoid:             $\langle M, \cdot, \mathbf{1} \rangle$ with $\mathbf{1} \cdot a = a \cdot \mathbf{1} = a$
    Commutative Monoid: $\langle M, \cdot, \mathbf{1} \rangle$ with $a \cdot b = b \cdot a$
    Additive Monoid:    $\langle M, +, \mathbf{0} \rangle$ with $\mathbf{0} + a = a + \mathbf{0} = a$
    Additive Commutative Monoid: $\langle M, +, \mathbf{0} \rangle$ with $a + b = b + a$
    Operation Monoid:   $\langle M, \operatorname{op}, \operatorname{identity} \rangle$
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._magma import AddSemigroup, OpSemigroup, Semigroup

V = TypeVar('V')


@runtime_checkable
class Monoid(Semigroup[V], Protocol[V]):
    r"""A semigroup equipped with a neutral multiplicative identity element $\mathbf{1}$.

    Algebraic Signature:
        $\langle M, \cdot, \mathbf{1} \rangle, \quad \mathbf{1} \cdot a = a \cdot \mathbf{1} = a$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `mul(a, b)`: Associative binary multiplication.
        - `one`: Multiplicative identity element.

    Properties:
        - Left Identity: $\mathbf{1} \cdot a = a$.
        - Right Identity: $a \cdot \mathbf{1} = a$.
        - Associativity: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.

    Applications:
        Path concatenation, automata word evaluation, safe empty stream folding, matrix multiplication monoids.
    """

    @property
    def one(self) -> V: ...


@runtime_checkable
class CommMonoid(Monoid[V], Protocol[V]):
    r"""A monoid whose multiplication is commutative: $a \cdot b = b \cdot a$.

    Algebraic Signature:
        $\langle M, \cdot, \mathbf{1} \rangle$ with $a \cdot b = b \cdot a$
    """

    ...


CommutativeMonoid = CommMonoid  # Canonical alias


# --- Additive Dual Branch ---


@runtime_checkable
class AddMonoid(AddSemigroup[V], Protocol[V]):
    r"""An additive semigroup equipped with a neutral additive identity element $\mathbf{0}$.

    Algebraic Signature:
        $\langle M, +, \mathbf{0} \rangle, \quad \mathbf{0} + a = a + \mathbf{0} = a$
    """

    @property
    def zero(self) -> V: ...


@runtime_checkable
class AddCommMonoid(AddMonoid[V], Protocol[V]):
    r"""An additive monoid whose addition is commutative: $a + b = b + a$.

    Algebraic Signature:
        $\langle M, +, \mathbf{0} \rangle$ with $a + b = b + a$
    """

    ...


# --- Domain-Agnostic Single-Operation Branch ---


@runtime_checkable
class OpMonoid(OpSemigroup[V], Protocol[V]):
    r"""Domain-agnostic monoid equipped with an arbitrary binary operation `op` and neutral `identity`.

    Algebraic Signature:
        $\langle M, \operatorname{op}, \operatorname{identity} \rangle$
    """

    @property
    def identity(self) -> V: ...


@runtime_checkable
class OpCommMonoid(OpMonoid[V], Protocol[V]):
    r"""Domain-agnostic monoid whose operation is commutative: `op(a, b) == op(b, a)`."""

    ...
