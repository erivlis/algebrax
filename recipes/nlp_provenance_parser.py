# %%
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "algebrax",
# ]
# [tool.uv.sources]
# algebrax = { path = ".." }
# ///

# %% [markdown]
# # Natural Language Parse Lineage & Ambiguity Audit
#
# ## Theory & Mathematical Foundation
#
# 1. **Matrix CYK Parsing via Dot Product (`algebrax.matrix.core.dot`)**:
#    Cocke-Younger-Kasami (CYK) parsing evaluates Context-Free Grammars in Chomsky
#    Normal Form (CNF). Multiplying the parse chart by itself (`ax.matrix.dot(chart, chart, semiring=GrammarSemiring)`)
#    combines adjacent spans $(i \dots k)$ and $(k \dots j)$ into $(i \dots j)$ in $\mathcal{O}(N^3)$ time.
#
# 2. **Symbolic Rule Provenance (`algebrax.semiring.ProvenanceSemiring`)**:
#    `ProvenanceSemiring` $\mathbb{N}[X]$ tags grammar rules with symbolic variables.
#    Matrix multiplication yields polynomials where each term represents
#    a complete, auditable syntax tree derivation path.
#
# 3. **Structural Entropy Audit (`algebrax.probability.entropy`)**:
#    Shannon entropy $H(P) = -\sum p_i \ln(p_i)$ over candidate parse tree probabilities quantifies syntactic ambiguity.

# %%
import algebrax as ax


class GrammarSemiring(ax.semiring.Semiring[set[str]]):
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


def parse_cyk(
    sentence: list[str],
    lexicon: dict[str, set[str]],
    grammar_rules: dict[tuple[str, str], set[str]],
) -> tuple[set[str], dict[int, dict[int, set[str]]]]:
    """Executes matrix-closure CYK parsing across a tokenized sentence."""
    grammar_semiring = GrammarSemiring(grammar_rules)
    n_len = len(sentence)
    chart: dict[int, dict[int, set[str]]] = {}
    for i, word in enumerate(sentence):
        if i not in chart:
            chart[i] = {}
        chart[i][i + 1] = lexicon.get(word, set())

    for _ in range(n_len):
        new_spans = ax.matrix.dot(chart, chart, semiring=grammar_semiring)
        for r, row in new_spans.items():
            if r not in chart:
                chart[r] = {}
            for c, val in row.items():
                chart[r][c] = chart[r].get(c, set()) | val

    final_nonterminals = chart.get(0, {}).get(n_len, set())
    return final_nonterminals, chart


def run_demo() -> None:
    """Executes CYK parsing, provenance polynomials, and ambiguity audit demonstrations."""
    # Step 1: Matrix CYK Parsing
    sentence = ["the", "astronomer", "saw", "stars"]
    lexicon = {
        "the": {"Det"},
        "astronomer": {"N", "NP"},
        "saw": {"V"},
        "stars": {"N", "NP"},
    }
    grammar_rules = {
        ("Det", "N"): {"NP"},
        ("V", "NP"): {"VP"},
        ("NP", "VP"): {"S"},
    }

    print(f"Target Sentence: '{' '.join(sentence)}'")
    final_sentence_nonterminals, _ = parse_cyk(sentence, lexicon, grammar_rules)
    print(f"Parsed Full Sentence Non-Terminals: {final_sentence_nonterminals}")
    assert "S" in final_sentence_nonterminals

    # Step 2: Symbolic Rule Provenance
    provenance_semiring = ax.semiring.ProvenanceSemiring()
    rule_x = {("rule_DetN_to_NP",): 1}
    rule_y = {("rule_VNP_to_VP",): 1}
    rule_z = {("rule_NPVP_to_S",): 1}
    sentence_derivation = provenance_semiring.mul(
        provenance_semiring.mul(rule_x, rule_y),
        rule_z,
    )
    print("\nSymbolic Rule Derivation Polynomial:")
    for terms, coeff in sentence_derivation.items():
        terms_str = " * ".join(terms)
        print(f"  Coeff {coeff}: {terms_str}")

    # Step 3: Syntax Tree Structural Entropy
    candidate_parse_probs = {
        "Parse_Tree_Direct_Object": 0.75,
        "Parse_Tree_Prepositional_Attachment": 0.15,
        "Parse_Tree_Noun_Compound": 0.10,
    }
    parse_entropy = ax.probability.entropy(candidate_parse_probs)
    print(f"\nParse Tree Structural Entropy H(Trees): {parse_entropy:.4f} nats")
    assert parse_entropy > 0.0


def main() -> None:
    """Entry point for CLI execution."""
    run_demo()
    print("==========================================================================")
    print("Recipe: Natural Language Grammar Lineage Finished Successfully!")
    print("==========================================================================")


if __name__ == "__main__":
    main()
