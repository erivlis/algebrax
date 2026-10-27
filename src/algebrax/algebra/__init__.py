"""
Unified algebraic hierarchy — Lean 4 Mathlib-aligned protocols for abstract algebra.
"""

from algebrax.algebra._field import (
    Field,
    ModularField,
    StandardField,
)
from algebrax.algebra._group import (
    AbelianGroup,
    AddCommGroup,
    AddGroup,
    CommGroup,
    Group,
    GroupAction,
)
from algebrax.algebra._helpers import (
    fold_add,
    fold_mul,
    fold_op,
    nsum,
    power,
    zpow,
    zsmul,
)
from algebrax.algebra._lattice import (
    BooleanAlgebra,
    BoundedLattice,
    DistributiveLattice,
    JoinSemilattice,
    Lattice,
    MeetSemilattice,
)
from algebrax.algebra._magma import (
    AddMagma,
    AddSemigroup,
    Band,
    Magma,
    OpMagma,
    OpSemigroup,
    Quasigroup,
    Semigroup,
)
from algebrax.algebra._module import (
    Algebra,
    Module,
    NonAssocAlgebra,
    Semimodule,
    VectorSpace,
)
from algebrax.algebra._monoid import (
    AddCommMonoid,
    AddMonoid,
    CommMonoid,
    CommutativeMonoid,
    Monoid,
    OpCommMonoid,
    OpMonoid,
)
from algebrax.algebra._ring import (
    CommRing,
    CommutativeRing,
    DivisionRing,
    NonAssocRing,
    Ring,
)
from algebrax.algebra._semiring import Semiring

__all__ = [
    'AbelianGroup',
    'AddCommGroup',
    'AddCommMonoid',
    'AddGroup',
    'AddMagma',
    'AddMonoid',
    'AddSemigroup',
    'Algebra',
    'Band',
    'BooleanAlgebra',
    'BoundedLattice',
    'CommGroup',
    'CommMonoid',
    'CommRing',
    'CommutativeMonoid',
    'CommutativeRing',
    'DistributiveLattice',
    'DivisionRing',
    'Field',
    'Group',
    'GroupAction',
    'JoinSemilattice',
    'Lattice',
    'Magma',
    'MeetSemilattice',
    'ModularField',
    'Module',
    'Monoid',
    'NonAssocAlgebra',
    'NonAssocRing',
    'OpCommMonoid',
    'OpMagma',
    'OpMonoid',
    'OpSemigroup',
    'Quasigroup',
    'Ring',
    'Semigroup',
    'Semimodule',
    'Semiring',
    'StandardField',
    'VectorSpace',
    'fold_add',
    'fold_mul',
    'fold_op',
    'nsum',
    'power',
    'zpow',
    'zsmul',
]
