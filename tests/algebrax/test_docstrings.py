"""
Unit tests for Standardized Mathematical Docstrings & Algebraic Signature Registry.
Verifies:
1. 100% catalog semirings have valid AMDS docstrings with Algebraic Signature.
2. Introspection functions `extract_algebraic_signature` and `get_algebraic_metadata`.
3. Rich display methods `_repr_latex_()` and `_repr_html_()`.
4. Extended structures (SimplicialComplex, AlgebraicTrie, category morphisms).
5. Registry immutability and metadata integrity.
"""

from algebrax import RectSparseMatrix
from algebrax.algebra import (
    CommGrothendieckRing,
    CommMonoidAlgebra,
    CommQuotientRing,
    CommSemiring,
)
from algebrax.analysis import pagerank
from algebrax.automata import nfa_closure
from algebrax.category import kan_extension_left, kleisli_compose
from algebrax.converters import canonical_sort_keys, make_zero_predicate
from algebrax.display import (
    AlgebraicMeta,
    extract_algebraic_signature,
    get_algebraic_metadata,
    semiring_card,
)
from algebrax.lie import LieAlgebra, RootSystem, StructureConstants
from algebrax.matrix import nullspace, rank, sparse_rref
from algebrax.rep import FiniteQuiver
from algebrax.semiring import Semiring, TropicalSemiring
from algebrax.topology import SimplicialComplex, SparseChainComplex, VectorBundleSemiring
from algebrax.trie import AlgebraicTrie
from algebrax.variety import (
    AffineVariety,
    CoordinateHopfAlgebra,
    GeometricVariety,
    PolynomialMap,
    SmoothableVariety,
)


def test_all_catalog_semirings_have_signatures():
    """Verify that every single semiring in Semiring.catalog() has an Algebraic Signature."""
    catalog = Semiring.catalog()
    assert len(catalog) >= 30, f'Expected at least 30 catalog semirings, got {len(catalog)}'

    missing = []
    for name, sem_cls in catalog.items():
        sig = extract_algebraic_signature(sem_cls)
        if not sig:
            missing.append(name)

    assert not missing, f'The following semirings are missing AMDS Algebraic Signatures: {missing}'


def test_registry_metadata_extraction():
    """Verify Semiring.registry() extracts complete AlgebraicMeta objects."""
    reg = Semiring.registry()
    assert isinstance(reg, dict)
    assert len(reg) == len(Semiring.catalog())

    tropical_meta = reg.get('Tropical')
    assert isinstance(tropical_meta, AlgebraicMeta)
    assert tropical_meta.name == 'TropicalSemiring'
    assert r'\min' in tropical_meta.signature
    assert r'+\infty' in tropical_meta.signature
    assert len(tropical_meta.summary) > 0


def test_extract_algebraic_signature_instance_and_class():
    """Verify extract_algebraic_signature works identically for instances and classes."""
    sem_cls = TropicalSemiring
    sem_inst = TropicalSemiring()

    sig_cls = extract_algebraic_signature(sem_cls)
    sig_inst = extract_algebraic_signature(sem_inst)

    assert sig_cls is not None
    assert sig_cls == sig_inst
    assert r'\mathbb{R} \cup \{+\infty\}' in sig_cls


def test_repr_latex_and_html():
    """Verify rich display hook generation for Jupyter notebooks."""
    t = TropicalSemiring()
    latex = t._repr_latex_()
    html = t._repr_html_()

    assert latex.startswith('$$')
    assert latex.endswith('$$')
    assert r'\min' in latex

    assert 'TropicalSemiring' in html
    assert '$$' in html
    assert 'Identity &oplus;' in html


def test_semiring_card_content():
    """Verify semiring_card outputs expected styling and values."""
    t = TropicalSemiring()
    card = semiring_card(t)

    assert 'TropicalSemiring' in card
    assert 'inf' in card
    assert '0.0' in card


def test_non_semiring_algebraic_structures():
    """Verify AMDS signature extraction on extended domain classes and categorical functions."""
    assert RectSparseMatrix is not None
    targets = [
        (CommSemiring, r'\langle V, \mathbf{0}, +, \mathbf{1}, \cdot \rangle'),
        (CommMonoidAlgebra, r'\langle R, R[M], \cdot_s'),
        (CommQuotientRing, r'\langle R / I, \mathbf{0}, +, -, \mathbf{1}, \cdot \rangle'),
        (CommGrothendieckRing, r'\langle S \times S / \sim'),
        (FiniteQuiver, r'Q = \langle V_Q, E_Q, s: E_Q \to V_Q, t: E_Q \to V_Q \rangle'),
        (SimplicialComplex, r'\cdots \xrightarrow{\partial_{k+1}}'),
        (SparseChainComplex, r'\cdots \xrightarrow{\partial_{k+1}} C_k'),
        (AlgebraicTrie, r'\mathcal{T}: \Sigma^* \to (S, \oplus, \otimes)'),
        (kleisli_compose, r'g \circ_T f: A \to T(C)'),
        (kan_extension_left, r'\mathrm{Lan}_P F'),
        (pagerank, r'\mathbf{p}^{(t+1)} = (\alpha \otimes \mathbf{p}^{(t)} \mathbf{P})'),
        (LieAlgebra, r'\langle \mathfrak{g}, [\cdot, \cdot], B \rangle'),
        (StructureConstants, r'[T_a, T_b] = \sum_c f_{ab}^c T_c'),
        (RootSystem, r'\Phi \subset \mathbb{Z}^r'),
        (GeometricVariety, r'\operatorname{contains\_point}'),
        (SmoothableVariety, r'\operatorname{is\_smooth\_at}'),
        (AffineVariety, r'V(I)'),
        (PolynomialMap, r'\phi^*: k[W] \to k[V]'),
        (CoordinateHopfAlgebra, r'\Delta, \epsilon, S'),
        (canonical_sort_keys, r'\operatorname{sort}: \mathcal{P}_{\text{fin}}(K) \to K^*'),
        (make_zero_predicate, r'\mathrm{zero?}_{\mathcal{S}}: V \to \mathbb{B}'),
        (nfa_closure, r'\delta^* = \left(\bigoplus_{a \in \Sigma} M_a\right)^*'),
        (
            VectorBundleSemiring,
            r'\langle \mathrm{Vect}_{\mathbb{R}}(K), \mathbf{0}, \oplus, \underline{\mathbb{R}}^1, \otimes \rangle',
        ),
        (sparse_rref, r'\mathrm{RREF}'),
        (rank, r'\operatorname{rank}_{\mathbb{K}}'),
        (nullspace, r'\ker_{\mathbb{K}}'),
    ]

    for target, expected_frag in targets:
        sig = extract_algebraic_signature(target)
        assert sig is not None, f'Failed to extract signature from {target}'
        assert expected_frag in sig, f"Signature '{sig}' does not contain expected fragment '{expected_frag}'"


def test_docstring_fallback_on_unannotated_object():
    """Verify behavior on unannotated classes or functions."""

    class Dummy:
        """Just a docstring without signature."""

    assert extract_algebraic_signature(Dummy) is None
    meta = get_algebraic_metadata(Dummy)
    assert meta.signature == r'\text{N/A}'
    assert meta.name == 'Dummy'
    assert meta.summary == 'Just a docstring without signature.'
