# CYK Parsing (Context-Free Grammars)

The **CYK Algorithm** parses a string using a Context-Free Grammar (CFG).
Surprisingly, this is just **Matrix Multiplication**!

*   **Values**: Sets of Non-Terminals (e.g., `{NP, VP}`).
*   **Add**: Set Union ($\cup$).
*   **Mul**: Grammar Production Rule Application.
    *   $A \otimes B = \{C \mid C \to A B \text{ is a rule}\}$.

This allows us to parse a sentence of length $N$ by computing the transitive closure of a chart matrix.

<!-- name: test_cyk_parsing -->

```python linenums="1"
from typing import Set, Dict, Tuple
from algebrax.semiring import Semiring
from algebrax.matrix import dot

# Grammar (Chomsky Normal Form)
# S -> NP VP
# NP -> 'I' | 'Python'
# VP -> V NP
# V -> 'love'
rules = {
    ('NP', 'VP'): {'S'},
    ('V', 'NP'): {'VP'}
}
lexicon = {
    'I': {'NP'},
    'love': {'V'},
    'Python': {'NP'}
}

class GrammarSemiring(Semiring[Set[str]]):
    @property
    def zero(self) -> Set[str]:
        return set()

    @property
    def one(self) -> Set[str]:
        # Identity for multiplication is tricky here.
        # Ideally, a special 'Identity' non-terminal, but for CYK we usually
        # don't need the identity matrix, just the closure.
        return set() 

    def add(self, a: Set[str], b: Set[str]) -> Set[str]:
        return a | b

    def mul(self, a: Set[str], b: Set[str]) -> Set[str]:
        # Apply rules: If we have non-terminals A in 'a' and B in 'b',
        # look for rules C -> A B.
        res = set()
        for lhs in a:
            for rhs in b:
                if (lhs, rhs) in rules:
                    res.update(rules[(lhs, rhs)])
        return res

# Sentence: "I love Python"
sentence = ['I', 'love', 'Python']
n = len(sentence)

# Initialize Chart (Upper Triangular Matrix)
# chart[i][j] contains non-terminals spanning words i to j
# But standard matrix multiplication works on indices differently.
# CYK is usually dynamic programming.
# To do it as Matrix Mul (Valiant's Algorithm), we treat the chart as an adjacency matrix.
# Edge i->j means "span from i to j".

# Initialize spans of length 1 (Diagonal + 1)
chart = {}
for i, word in enumerate(sentence):
    if i not in chart: chart[i] = {}
    chart[i][i+1] = lexicon[word]

# CYK Step: Combine spans
# Span(i, k) = Span(i, j) * Span(j, k)
# This is exactly Matrix Multiplication!
# chart = chart + chart * chart
# We iterate this n times.

semiring = GrammarSemiring()

for _ in range(n):
    # New spans = Old spans * Old spans
    new_spans = dot(chart, chart, semiring=semiring)
    
    # Union with existing spans (Add)
    for r, row in new_spans.items():
        if r not in chart: chart[r] = {}
        for c, val in row.items():
            current = chart[r].get(c, set())
            chart[r][c] = current | val

# Check if 'S' spans the whole sentence (0 to n)
final_tags = chart.get(0, {}).get(n, set())
print(f"Parses as: {final_tags}")
# output: {'S'}
```
