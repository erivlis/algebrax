# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

"""
Natural Language Parse Lineage & Ambiguity Audit Recipe using algebrax

================================================================================
THEORY & MATHEMATICAL FOUNDATION
================================================================================
1. Matrix CYK Parsing via Dot Product (algebrax.matrix.core.dot):
   Cocke-Younger-Kasami (CYK) parsing evaluates Context-Free Grammars in Chomsky
   Normal Form (CNF). By treating the parse chart as a triangular sparse matrix,
   multiplying the chart by itself (`dot(chart, chart, semiring=GrammarSemiring)`)
   combines adjacent spans (i..k) and (k..j) into (i..j) in O(N^3) time.

2. Symbolic Rule Provenance (algebrax.semiring.ProvenanceSemiring):
   The Provenance Semiring (Polynomials N[X]) tags grammar rules with symbolic
   variables (e.g. x_rule1, x_rule2). Matrix multiplication yields polynomials
   where each term represents a complete, auditable syntax tree derivation path.

3. Structural Entropy Audit (algebrax.probability.entropy):
   Shannon entropy H(P) = - sum p_i ln(p_i) over candidate parse tree probabilities
   quantifies syntactic ambiguity. Low entropy indicates a clear single parse;
   high entropy signals multiple competing parse interpretations.
================================================================================
"""

from algebrax.matrix.core import dot
from algebrax.probability import entropy
from algebrax.semiring import ProvenanceSemiring, Semiring


class GrammarSemiring(Semiring[set[str]]):
    """Semiring where multiplication applies Context-Free Grammar rules (A, B) -> C."""

    def __init__(self, rules: dict[tuple[str, str], set[str]]):
        self.rules = rules

    @property
    def zero(self) -> set[str]:
        return set()

    @property
    def one(self) -> set[str]:
        return set()

    def add(self, a: set[str], b: set[str]) -> set[str]:
        return a | b

    def mul(self, a: set[str], b: set[str]) -> set[str]:
        result = set()
        for nt1 in a:
            for nt2 in b:
                result |= self.rules.get((nt1, nt2), set())
        return result


def main() -> None:
    print('==========================================================================')
    print('Use Case: Natural Language Grammar Lineage & Ambiguity Audit')
    print('==========================================================================')
    print('Goal: Parse CNF grammar sentences via matrix multiplication (dot), track')
    print('      symbolic rule provenance polynomials, and audit syntactic entropy.')

    # 1. Define Lexicon and Grammar Rules in Chomsky Normal Form (CNF)
    print('\n[Step 0] Defining Lexicon and Grammar Rules (CNF)...')
    sentence = ['the', 'astronomer', 'saw', 'stars']
    lexicon = {
        'the': {'Det'},
        'astronomer': {'N', 'NP'},
        'saw': {'V'},
        'stars': {'N', 'NP'},
    }

    grammar_rules = {
        ('Det', 'N'): {'NP'},
        ('V', 'NP'): {'VP'},
        ('NP', 'VP'): {'S'},
    }

    print(f"Target Sentence: '{' '.join(sentence)}'")
    print('Chomsky Normal Form Binary Rules:')
    for (left, right), parents in grammar_rules.items():
        print(f'  ({left}, {right}) -> {parents}')

    # --- Step 1: Matrix CYK Parsing via Dot Product ---
    print('\n[Step 1] Matrix CYK Parsing via Dot Product (GrammarSemiring)...')
    print('Explanation: CYK matrix multiplication combines span (i..k) and (k..j) into (i..j).')
    grammar_semiring = GrammarSemiring(grammar_rules)

    n_len = len(sentence)
    chart = {}
    for i, word in enumerate(sentence):
        if i not in chart:
            chart[i] = {}
        chart[i][i + 1] = lexicon.get(word, set())

    for step in range(n_len):
        new_spans = dot(chart, chart, semiring=grammar_semiring)
        for r, row in new_spans.items():
            if r not in chart:
                chart[r] = {}
            for c, val in row.items():
                chart[r][c] = chart[r].get(c, set()) | val

    final_sentence_nonterminals = chart.get(0, {}).get(n_len, set())
    print(f'Parsed Full Sentence Non-Terminals (Span 0 -> {n_len}): {final_sentence_nonterminals}')
    assert 'S' in final_sentence_nonterminals

    # --- Step 2: Symbolic Rule Provenance (Provenance Semiring) ---
    print('\n[Step 2] Symbolic Rule Provenance (ProvenanceSemiring)...')
    print('Explanation: Multiplies symbolic rule variables into multivariate polynomials.')
    provenance_semiring = ProvenanceSemiring()

    rule_x = {('rule_DetN_to_NP',): 1}
    rule_y = {('rule_VNP_to_VP',): 1}
    rule_z = {('rule_NPVP_to_S',): 1}

    sentence_derivation = provenance_semiring.mul(
        provenance_semiring.mul(rule_x, rule_y),
        rule_z,
    )

    print('Symbolic Rule Derivation Polynomial:')
    for terms, coeff in sentence_derivation.items():
        terms_str = ' * '.join(terms)
        print(f'  Coeff {coeff}: {terms_str}')

    # --- Step 3: Information Entropy & Ambiguity Audit ---
    print('\n[Step 3] Syntax Tree Structural Entropy & Ambiguity Audit...')
    print('Explanation: Calculates Shannon entropy H(P) = -sum p_i ln(p_i) over parse trees.')
    candidate_parse_probs = {
        'Parse_Tree_Direct_Object': 0.75,
        'Parse_Tree_Prepositional_Attachment': 0.15,
        'Parse_Tree_Noun_Compound': 0.10,
    }

    parse_entropy = entropy(candidate_parse_probs)
    print('\nCandidate Parse Tree Probability Distribution:')
    for tree_id, prob in candidate_parse_probs.items():
        print(f'  - {tree_id}: {prob * 100:.1f}%')

    print(f'\nParse Tree Structural Entropy H(Trees): {parse_entropy:.4f} nats')
    if parse_entropy < 0.8:
        print('Audit Verdict: LOW AMBIGUITY - High confidence single parse tree.')
    else:
        print('Audit Verdict: HIGH AMBIGUITY - Multiple competing parse trees detected.')

    print('\n==========================================================================')
    print('Recipe Completed: Natural Language Grammar Lineage Analysis Finished!')
    print('==========================================================================')


if __name__ == '__main__':
    main()
