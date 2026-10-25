r"""
Magma and Semigroup protocols for single-operation algebraic structures.

Algebraic Signatures (EP-0150 AMDS):
    Magma:            $\langle M, \cdot \rangle$
    Semigroup:        $\langle S, \cdot \rangle$ with $(a \cdot b) \cdot c = a \cdot (b \cdot c)$
    Band:             $\langle B, \cdot \rangle$ with $a \cdot a = a$
    Additive Magma:   $\langle M, + \rangle$
    Additive Semigroup: $\langle S, + \rangle$
    Operation Magma:  $\langle M, \operatorname{op} \rangle$
"""

from typing import Protocol, TypeVar, runtime_checkable

V = TypeVar('V')


@runtime_checkable
class Magma(Protocol[V]):
    r"""Carrier set equipped with a single closed binary operation $\cdot: V \times V \to V$.

    Algebraic Signature:
        $\langle M, \cdot \rangle, \quad \cdot: M \times M \to M$

    Carrier:
        Arbitrary unboxed carrier $V$.

    Operations:
        - `mul(a, b)`: Binary composition yielding another element in $V$.

    Properties:
        - Closure: $\forall a, b \in M, \ a \cdot b \in M$.

    Applications:
        Non-associative algebras, Cayley tables, loop quasigroups, rock-paper-scissors game dynamics.
    """

    def mul(self, a: V, b: V) -> V: ...


@runtime_checkable
class Semigroup(Magma[V], Protocol[V]):
    r"""An associative magma satisfying $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.

    Algebraic Signature:
        $\langle S, \cdot \rangle$ with associativity

    Properties:
        - Associativity: $(a \cdot b) \cdot c = a \cdot (b \cdot c)$.

    Applications:
        Parallel stream reductions, MapReduce associative chunking, semi-Markov transition kernels.
    """

    ...


@runtime_checkable
class Band(Semigroup[V], Protocol[V]):
    r"""An idempotent semigroup satisfying $a \cdot a = a$.

    Algebraic Signature:
        $\langle B, \cdot \rangle$ with $a^2 = a$

    Properties:
        - Idempotence: $\forall a \in B, \ a \cdot a = a$.

    Applications:
        Projection algebras, idempotent routing caches, transitive reduction kernels.
    """

    ...


@runtime_checkable
class Quasigroup(Magma[V], Protocol[V]):
    r"""A magma with unique left and right division: $a \cdot x = b$ and $y \cdot a = b$.

    Algebraic Signature:
        $\langle Q, \cdot, /, \backslash \rangle$
    """

    def ldiv(self, a: V, b: V) -> V:
        r"""Left division: unique $x$ such that $a \cdot x = b$."""
        ...

    def rdiv(self, a: V, b: V) -> V:
        r"""Right division: unique $y$ such that $y \cdot a = b$."""
        ...


# --- Additive Dual Branch ---


@runtime_checkable
class AddMagma(Protocol[V]):
    r"""Carrier set equipped with a closed additive binary operation $+: V \times V \to V$.

    Algebraic Signature:
        $\langle M, + \rangle, \quad +: M \times M \to M$
    """

    def add(self, a: V, b: V) -> V: ...


@runtime_checkable
class AddSemigroup(AddMagma[V], Protocol[V]):
    r"""An associative additive magma: $(a + b) + c = a + (b + c)$."""

    ...


# --- Domain-Agnostic Single-Operation Branch ---


@runtime_checkable
class OpMagma(Protocol[V]):
    r"""Domain-agnostic magma equipped with an arbitrary binary operation `op(a, b)`."""

    def op(self, a: V, b: V) -> V: ...


@runtime_checkable
class OpSemigroup(OpMagma[V], Protocol[V]):
    r"""Domain-agnostic associative semigroup: `op(op(a, b), c) == op(a, op(b, c))`."""

    ...
