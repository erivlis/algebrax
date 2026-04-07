# Viterbi Algorithm (Hidden Markov Models)

The **Viterbi Algorithm** finds the most likely sequence of hidden states in a Hidden Markov Model (HMM).
Algebraically, this is matrix multiplication over the **Max-Product Semiring** $(\max, \times)$.

*   **Add**: $\max$ (Select the best path).
*   **Mul**: $\times$ (Combine probabilities).

<!-- name: test_viterbi_semiring -->

```python linenums="1"
from algebrax.semiring import ViterbiSemiring
from algebrax.matrix import dot

# HMM State Transition (Probability of A->B)
# Healthy (H), Fever (F)
transitions = {
    'H': {'H': 0.7, 'F': 0.3},
    'F': {'H': 0.4, 'F': 0.6}
}

# Emission Probabilities (State -> Observation)
# Normal (N), Cold (C), Dizzy (D)
emissions = {
    'H': {'N': 0.5, 'C': 0.4, 'D': 0.1},
    'F': {'N': 0.1, 'C': 0.3, 'D': 0.6}
}

# Initial State Distribution
start = {'H': 0.6, 'F': 0.4}

# Observation Sequence: Normal -> Cold -> Dizzy
obs_seq = ['N', 'C', 'D']

# Viterbi Step
# Current State Probabilities
current_probs = start

semiring = ViterbiSemiring()

for obs in obs_seq:
    # 1. Emission: Multiply current state prob by emission prob
    # This is a diagonal matrix multiplication or element-wise product
    after_emission = {}
    for state, prob in current_probs.items():
        p_emit = emissions[state].get(obs, 0.0)
        after_emission[state] = semiring.mul(prob, p_emit)
        
    # 2. Transition: Propagate to next state (Matrix Vector Mul)
    # next_state = current * transition_matrix
    # We use dot() but we need to format vectors as matrices for the library
    # or just do it manually for this vector-matrix step.
    
    # Let's use the library's dot product.
    # Vector as 1xN matrix: {0: {'H': p1, 'F': p2}}
    vec_matrix = {0: after_emission}
    
    # Transition matrix needs to be in the right format
    # transitions is already dict-of-dicts
    
    next_step = dot(vec_matrix, transitions, semiring=semiring)
    current_probs = next_step[0]

print(f"Final Probabilities: {current_probs}")
# The max value indicates the probability of the most likely path ending in that state.
```
