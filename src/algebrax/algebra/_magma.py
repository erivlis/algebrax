r"""
Magma and Semigroup protocols for single-operation algebraic structures.

Algebraic Signatures:
    Magma:              $\langle V, \cdot \rangle$
    Semigroup:          $\langle V, \cdot \rangle$ with $(a \cdot b) \cdot c = a \cdot (b \cdot c)$
    Band:               $\langle V, \cdot \rangle$ with $a \cdot a = a$
    Quasigroup:         $\langle V, \cdot, \backslash, / \rangle$
    Additive Magma:     $\langle V, + \rangle$
    Additive Semigroup: $\langle V, + \rangle$ with $(a + b) + c = a + (b + c)$
    Operation Magma:    $\langle V, \operatorname{op} \rangle$
"""

from typing import Protocol, TypeVar, runtime_checkable

from algebrax.algebra._mixins import HasAdd, HasMul, HasOp

V = TypeVar('V')


@runtime_checkable
class Magma(HasMul[V], Protocol):
    r"""Carrier set equipped with a single closed binary multiplication $\cdot: V \times V \to V$.

    Algebraic Signature:
        $\langle V, \cdot \rangle$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `mul(a, b)`: Binary multiplication (`HasMul[V]`).

    Properties:
        - Closure: $\forall a, b \in V, \ a \cdot b \in V$.

    Applications:
        Non-associative algebras, Cayley tables, loop quasigroups, rock-paper-scissors game dynamics.
    """

    ...


@runtime_checkable
class Semigroup(HasMul[V], Protocol):
    r"""An associative magma satisfying $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.

    Algebraic Signature:
        $\langle V, \cdot \rangle$ with $(a \cdot b) \cdot c = a \cdot (b \cdot c)$

    Operations:
        - `mul(a, b)`: Associative binary multiplication (`HasMul[V]`).

    Properties:
        - Associativity: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.

    Applications:
        Parallel stream reductions, MapReduce associative chunking, semi-Markov transition kernels.
    """

    ...


@runtime_checkable
class Band(HasMul[V], Protocol):
    r"""An idempotent semigroup satisfying $a \cdot a = a$.

    Algebraic Signature:
        $\langle V, \cdot \rangle$ with $a \cdot a = a$

    Operations:
        - `mul(a, b)`: Associative, idempotent binary multiplication (`HasMul[V]`).

    Properties:
        - Associativity: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.
        - Idempotence: $\forall a \in V, \ a \cdot a = a$.

    Applications:
        Projection algebras, idempotent routing caches, transitive reduction kernels.
    """

    ...


@runtime_checkable
class Quasigroup(HasMul[V], Protocol):
    r"""A magma with unique left and right division: $a \cdot x = b$ and $y \cdot a = b$.

    Algebraic Signature:
        $\langle V, \cdot, \backslash, / \rangle$

    Operations:
        - `mul(a, b)`: Binary multiplication (`HasMul[V]`).
        - `ldiv(a, b)`: Left division $a \backslash b$ (unique $x$ such that $a \cdot x = b$).
        - `rdiv(a, b)`: Right division $a / b$ (unique $y$ such that $y \cdot a = b$).
    """

    def ldiv(self, a: V, b: V) -> V:
        r"""Left division: unique $x$ such that $a \cdot x = b$."""
        ...

    def rdiv(self, a: V, b: V) -> V:
        r"""Right division: unique $y$ such that $y \cdot a = b$."""
        ...


# --- Additive Dual Branch ---


@runtime_checkable
class AddMagma(HasAdd[V], Protocol):
    r"""Carrier set equipped with a closed additive binary operation $+: V \times V \to V$.

    Algebraic Signature:
        $\langle V, + \rangle$

    Operations:
        - `add(a, b)`: Binary addition (`HasAdd[V]`).
    """

    ...


@runtime_checkable
class AddSemigroup(HasAdd[V], Protocol):
    r"""An associative additive magma satisfying $(a + b) + c = a + (b + c)$.

    Algebraic Signature:
        $\langle V, + \rangle$ with $(a + b) + c = a + (b + c)$

    Operations:
        - `add(a, b)`: Associative binary addition (`HasAdd[V]`).
    """

    ...


# --- Domain-Agnostic Single-Operation Branch ---


@runtime_checkable
class OpMagma(HasOp[V], Protocol):
    r"""Domain-agnostic magma equipped with an arbitrary binary operation `op(a, b)`.

    Algebraic Signature:
        $\langle V, \operatorname{op} \rangle$

    Operations:
        - `op(a, b)`: Binary composition (`HasOp[V]`).
    """

    ...


@runtime_checkable
class OpSemigroup(HasOp[V], Protocol):
    r"""Domain-agnostic associative semigroup satisfying `op(op(a, b), c) == op(a, op(b, c))`.

    Algebraic Signature:
        $\langle V, \operatorname{op} \rangle$
        with $\operatorname{op}(\operatorname{op}(a, b), c) = \operatorname{op}(a, \operatorname{op}(b, c))$

    Operations:
        - `op(a, b)`: Associative binary composition (`HasOp[V]`).
    """

    ...
