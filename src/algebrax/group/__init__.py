"""
Group Theory, Finite Groups, Coset Decompositions, and Permutation Symmetries.

Modules:
    - finite: `FiniteGroup`, `FiniteCommGroup`, `conjugacy_classes`, subgroups, cosets, double cosets, quotients.
    - canonical: Concrete finite groups (`cyclic_group`, `dihedral_group`, `quaternion_group`,
      `symmetric_group`, `alternating_group`, `direct_product`).
    - permutation: Sparse mapping permutation utilities (`compose`, `invert`, `signature`).
"""

from algebrax.algebra._group import AddCommGroup, AddGroup, CommGroup, Group, GroupAction
from algebrax.group.canonical import (
    alternating_elements,
    alternating_group,
    cyclic_group,
    dihedral_elements,
    dihedral_group,
    dihedral_inv,
    dihedral_mul,
    direct_product,
    quaternion_elements,
    quaternion_group,
    quaternion_inv,
    quaternion_mul,
    symmetric_elements,
    symmetric_group,
    symmetric_inv,
    symmetric_mul,
)
from algebrax.group.finite import FiniteCommGroup, FiniteGroup, conjugacy_classes
from algebrax.group.permutation import compose, invert, signature

__all__ = [
    'AddCommGroup',
    'AddGroup',
    'CommGroup',
    'FiniteCommGroup',
    'FiniteGroup',
    'Group',
    'GroupAction',
    'alternating_elements',
    'alternating_group',
    'compose',
    'conjugacy_classes',
    'cyclic_group',
    'dihedral_elements',
    'dihedral_group',
    'dihedral_inv',
    'dihedral_mul',
    'direct_product',
    'invert',
    'quaternion_elements',
    'quaternion_group',
    'quaternion_inv',
    'quaternion_mul',
    'signature',
    'symmetric_elements',
    'symmetric_group',
    'symmetric_inv',
    'symmetric_mul',
]
