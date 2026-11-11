"""Tests for EP-0202: Functorial Sheaves, CellPosetCategory, and Categorical DEC."""

from __future__ import annotations

import pytest

from algebrax.category import Category, Cell, CellPosetCategory, FaceInclusion
from algebrax.topology import (
    CellularSheaf,
    ConstantSheaf,
    FunctorialSheaf,
    SimplicialComplex,
    build_sheaf_coboundary_matrix,
    build_sheaf_laplacian,
    exterior_derivative,
    hodge_laplacian,
)
from algebrax.verification import (
    verify_category_laws,
    verify_coboundary_nilpotency,
    verify_sheaf_functoriality,
    verify_sheaf_laplacian_properties,
)


def test_cell_poset_category_laws() -> None:
    v0 = Cell(0, (0,))
    v1 = Cell(0, (1,))
    v2 = Cell(0, (2,))
    e01 = Cell(1, (0, 1))
    e12 = Cell(1, (1, 2))
    e02 = Cell(1, (0, 2))
    t012 = Cell(2, (0, 1, 2))

    poset = CellPosetCategory(
        cells=[v0, v1, v2, e01, e12, e02, t012],
        faces=[
            (v0, e01),
            (v1, e01),
            (v1, e12),
            (v2, e12),
            (v0, e02),
            (v2, e02),
            (e01, t012),
            (e12, t012),
            (e02, t012),
        ],
    )

    assert isinstance(poset, Category)
    assert poset.cells_of_dim(0) == [v0, v1, v2]
    assert poset.cells_of_dim(2) == [t012]
    assert poset.is_face(v0, t012)
    assert not poset.is_face(t012, v0)
    assert not poset.is_face(v0, e12)
    assert not poset.is_face(Cell(0, (99,)), v0)

    f = FaceInclusion(v0, e01)
    g = FaceInclusion(e01, t012)
    fg = poset.compose(f, g)
    assert fg == FaceInclusion(v0, t012)
    assert poset.source(fg) == v0
    assert poset.target(fg) == t012

    cat_res = verify_category_laws(poset, [v0, e01, t012], [f, g, poset.id(t012)])
    assert all(cat_res.values())

    with pytest.raises(ValueError, match='not in Poset'):
        poset.id(Cell(0, (99,)))

    with pytest.raises(ValueError, match='Incompatible face composition'):
        poset.compose(FaceInclusion(v0, e01), FaceInclusion(v1, e12))

    with pytest.raises(ValueError, match='not a valid face inclusion'):
        poset.compose(FaceInclusion(v0, e12), FaceInclusion(e12, t012))


def test_constant_sheaf_equals_dec_exterior_derivative_and_hodge_laplacian() -> None:
    # Hollow tetrahedron (boundary of 3-simplex): 4 vertices, 6 edges, 4 triangles
    sc = SimplicialComplex([(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
    const_sheaf = ConstantSheaf.from_simplicial_complex(sc)

    assert isinstance(const_sheaf, FunctorialSheaf)
    for cell in const_sheaf.poset_category.cells:
        assert const_sheaf.stalk_dim(cell) == 1

    with pytest.raises(KeyError, match='not found'):
        const_sheaf.stalk_dim(Cell(0, (99,)))

    # Non-incident restriction map is empty
    assert const_sheaf.restriction_map(Cell(0, (0,)), Cell(1, (1, 2))) == {}

    # 1. Check delta^0 and delta^1 match DEC exterior_derivative d_0 and d_1
    for k in (0, 1):
        delta_k = build_sheaf_coboundary_matrix(const_sheaf, k)
        d_k = exterior_derivative(sc, k)
        unboxed_delta_k = {
            coface.id: {face.id: val for (face, _), val in row.items()}
            for (coface, _), row in delta_k.items()
        }
        assert unboxed_delta_k == d_k

    # Negative k returns empty matrix
    assert build_sheaf_coboundary_matrix(const_sheaf, -1) == {}

    # 2. Check coboundary nilpotency delta^1 o delta^0 == 0
    assert verify_coboundary_nilpotency(const_sheaf, k=0)
    assert verify_coboundary_nilpotency(const_sheaf, k=1)

    # 3. Check Hodge-Sheaf Laplacian L_k matches DEC hodge_laplacian Delta_k for k=0, 1, 2
    for k in (0, 1, 2):
        l_k = build_sheaf_laplacian(const_sheaf, k)
        dec_l_k = hodge_laplacian(sc, k)
        unboxed_l_k = {
            r_cell.id: {c_cell.id: val for (c_cell, _), val in row.items()}
            for (r_cell, _), row in l_k.items()
        }
        assert unboxed_l_k == dec_l_k


def test_cellular_sheaf_functorial_interface_and_verification() -> None:
    sheaf: CellularSheaf[int] = CellularSheaf()
    sheaf.add_vertex(0, dim=2)
    sheaf.add_vertex(1, dim=2)
    sheaf.add_edge(0, 1, dim=2, rho_u=[[1.0, 0.0], [0.0, 1.0]], rho_v=[[0.0, -1.0], [1.0, 0.0]])

    assert isinstance(sheaf, FunctorialSheaf)
    assert isinstance(sheaf.poset_category, CellPosetCategory)
    v0 = Cell(0, (0,))
    v1 = Cell(0, (1,))
    e01 = Cell(1, (0, 1))

    assert sheaf.stalk_dim(v0) == 2
    assert sheaf.stalk_dim(e01) == 2
    with pytest.raises(KeyError, match='not found'):
        sheaf.stalk_dim(Cell(0, (99,)))

    assert sheaf.restriction_map(v0, v1) == {}
    assert sheaf.restriction_map(Cell(0, (99,)), e01) == {}

    # Verify functoriality on reflexive paths (v0 <= v0 <= e01) and (v0 <= e01 <= e01)
    func_res = verify_sheaf_functoriality(
        sheaf,
        sample_paths=[(v0, v0, e01), (v0, e01, e01), (v1, v1, e01)],
    )
    assert all(func_res.values())

    # Compare build_sheaf_laplacian(sheaf, 0) with sheaf.laplacian_matrix()
    l0_functorial = build_sheaf_laplacian(sheaf, k=0)
    l0_direct = sheaf.laplacian_matrix()
    unboxed_l0 = {
        (r_cell.id[0], r_idx): {(c_cell.id[0], c_idx): val for (c_cell, c_idx), val in row.items()}
        for (r_cell, r_idx), row in l0_functorial.items()
    }
    assert unboxed_l0 == l0_direct

    # Verify Laplacian symmetry and positive semi-definiteness
    sample_x = {(v0, 0): 1.5, (v0, 1): -0.5, (v1, 0): 2.0, (v1, 1): 1.0}
    lap_props = verify_sheaf_laplacian_properties(sheaf, k=0, sample_cochains=[sample_x, {}])
    assert all(lap_props.values())


def test_sheaf_verification_negative_cases() -> None:
    v0 = Cell(0, (0,))
    e01 = Cell(1, (0, 1))
    t012 = Cell(2, (0, 1, 2))
    poset = CellPosetCategory([v0, e01, t012], [(v0, e01), (e01, t012), (v0, t012)])

    class BrokenSheaf(FunctorialSheaf):
        @property
        def poset_category(self) -> CellPosetCategory:
            return poset

        def stalk_dim(self, cell: Cell) -> int:
            return 1

        def restriction_map(self, face: Cell, coface: Cell) -> dict[int, dict[int, float]]:
            if face == coface:
                return {0: {0: 2.0}}  # Violates identity == 1.0
            if (face, coface) == (v0, e01):
                return {0: {0: 2.0}}
            if (face, coface) == (e01, t012):
                return {0: {0: 3.0}}
            if (face, coface) == (v0, t012):
                return {0: {0: 99.0}}  # 2 * 3 != 99
            return {}

    broken = BrokenSheaf()
    res = verify_sheaf_functoriality(broken, sample_paths=[(v0, e01, t012)])
    assert not res['identity_preservation']
    assert not res['composition_preservation']
    assert not verify_coboundary_nilpotency(broken, k=0)
    assert verify_coboundary_nilpotency(broken, k=5)

    # Test ConstantSheaf reflexive restriction and build_sheaf_laplacian on empty/isolated cells
    const_s = ConstantSheaf([v0, e01], {(v0, e01): 1.0})
    assert const_s.restriction_map(v0, v0) == {0: {0: 1.0}}
    assert build_sheaf_laplacian(const_s, k=2) == {}

    # CellularSheaf edge cases for stalk_dim and restriction_map
    sheaf: CellularSheaf[int] = CellularSheaf()
    sheaf.add_vertex(0, dim=1)
    assert sheaf.restriction_map(Cell(0, (0,)), Cell(2, (0, 1, 2))) == {}
    with pytest.raises(KeyError):
        sheaf.stalk_dim(Cell(1, (0, 1)))
    with pytest.raises(KeyError):
        sheaf.stalk_dim(Cell(2, (0, 1, 2)))

