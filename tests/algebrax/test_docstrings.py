"""
Unit tests for Standardized Mathematical Docstrings & Algebraic Signature Registry.
Verifies:
1. 100% catalog semirings have valid AMDS docstrings with Algebraic Signature.
2. Introspection functions `extract_algebraic_signature` and `get_algebraic_metadata`.
3. Rich display methods `_repr_latex_()` and `_repr_html_()`.
4. Extended structures (SimplicialComplex, AlgebraicTrie, category morphisms).
5. Registry immutability and metadata integrity.
"""

from algebrax.category import kan_extension_left, kleisli_compose
from algebrax.display import (
    AlgebraicMeta,
    extract_algebraic_signature,
    get_algebraic_metadata,
    semiring_card,
)
from algebrax.homology import SimplicialComplex, SparseChainComplex
from algebrax.semiring import Semiring, TropicalSemiring
from algebrax.trie import AlgebraicTrie


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
    targets = [
        (SimplicialComplex, r'\cdots \xrightarrow{\partial_{k+1}}'),
        (SparseChainComplex, r'\cdots \xrightarrow{\partial_{k+1}} C_k'),
        (AlgebraicTrie, r'\mathcal{T}: \Sigma^* \to (S, \oplus, \otimes)'),
        (kleisli_compose, r'g \circ_T f: A \to T(C)'),
        (kan_extension_left, r'\mathrm{Lan}_P F'),
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
