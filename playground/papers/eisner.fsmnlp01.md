In Proc. of the ESSLLI Workshop on Finite-State Methods in NLP (FSMNLP), Helsinki, August 2001.

Expectation Semirings: Flexible EM for Learning Finite-State Transducers∗

Jason Eisner, Johns Hopkins University (jason@cs.jhu.edu)

1 Motivation

Most recent work on ﬁnite-state transducers (FSTs) falls into two camps according to how the transducers
are constructed. The algebraic camp employs experts who write (possibly weighted) regular expressions by
hand, using an ever-growing language of powerful algebraic operators [10, 7]. The statistical camp, which
prefers to extract expertise automatically from data, builds transducers with much simpler topology so that
their arc probabilities can be easily trained (e.g., [17, 12, 11]).1

This paper oﬀers a clean way to combine the two traditions: an Expectation-Maximation (EM) [4]
algorithm for training arbitrary FSTs. First the human expert uses domain knowledge to specify the topology
and parameterization of the transducer in any convenient way. Then the EM algorithm automatically chooses
parameter values that (locally) maximize the joint likelihood of fully or partly observed data.

Unlike previous specialized methods, the EM algorithm here allows transducers having (cid:15)’s and arbitrary
topology. It also allows parameterizations that are independent of the transducer topology (hence unaﬀected
by determinization and minimization). But it remains surprisingly simple because all the diﬃcult work can
be subcontracted to existing algorithms for semiring-weighted automata. The trick is to use a novel semiring.
To combine the two traditions, a domain expert might build a weighted transducer by using weighted
expressions in the full ﬁnite-state calculus. Weighted regexps can also optionally refer to machines that are
speciﬁed directly in terms of states, arcs, and weights, or even derived by approximating PCFGs [16]. But
the various weights are written in terms of unknown parameters and estimated automatically. The semiring
approach ensures that the method works even if the transducer is built with operations such as composition,
directed replacement, and minimization, which distribute the parameters over the arcs in a complex way.

This parameter estimation yields a transducer that models the joint probability P (x, y), where x and y
are input and output strings. As usual, this transducer can easily be manipulated to obtain the marginal
distributions P (x), P (y) and the conditional distributions P (x | y), P (y | x), and to ﬁnd strings maximizing
these distributions. For example, argmaxx∈X P (x | y ∈ Y ) = argmaxx∈X P (x, (y ∈ Y )) is the most likely
underlying string in regular set X when the corresponding surface string is known to be in regular set Y .

Learning weights for such transducers has many applications. Some examples:

• Simple special cases include parameter estimation for common probability models—alignment models
[23], HMMs [2], n-gram models for segmentation or classiﬁcation, and transformation models [5]—as
well as the usual variations of these to allow variable-length history, epsilons, partly-observed input or
output, tied parameters, mixtures, etc. Treating all these models in a uniﬁed framework makes them
easy to implement and modify, as well as providing a testbed for improved learning algorithms.

• One could stochasticize hand-built machines. For example, given a nondeterministic transducer for
morphological analysis, one could learn parameters that predict the probabilities of diﬀerent analyses.

• Existing statistical ﬁnite-state models could be trained “end-to-end.” [12] contains a noisy-channel
component that maps English phonology ep to Japanese phonology jp, trained solely on hard-to-obtain
(ep, jp) pairs. Composing this channel with other transducers yields [12]’s full model that transliterates
English text et to Japanese text jt. EM can use (et, jt) pairs to help train all the parameters at once.

• One could try to learn underlying representations with little or no supervision (as with HMMs). Build-
ing on [8], one could construct a stochastic transducer that concatenates randomly-selected possible
stems and aﬃxes, then passes the result through randomly selected hand-built phonological rules or
constraints. Observations of unanalyzed (or analyzed) words could then be used to set the parameters
that govern the random choices—thereby inducing a morphological lexicon and a phonology.

∗Thanks to Gideon Mann, Charles Schafer, and Mehryar Mohri for useful conversations. Apologies for these 4 pages’ density.
1The typical statistical approach is to compose an n-gram source model with a cascade of noisy-channel models that distort
the source locally. Each of these component models handles one level of intermediate representation, and is implemented as a
transducer that is either hand-built or of an especially simple and trainable form. This lets the component models be trained
separately (i.e., before composition). The n-gram source model can be trained by standard ML estimation with backoﬀ [1].
The channel models are one-state transducers with arc labels in Σ∗ × Σ∗, and can be trained by an “alignment” EM algorithm
that is folklore in computational linguistics and biology; see [23] for a ﬁnite-state presentation as weighted edit distance.

1

In short, ﬁnite-state devices are so broadly applicable that any learning method should be extremely useful.

2 The Problem: EM for Parameterized Probabilistic Relations

A (real-)weighted regular relation is a function f : Σ∗ × ∆∗ → R≥0 that can be computed by a weighted
ﬁnite-state transducer—or, equivalently, by a regular expression (regexp) built up by concatenation, union,
and closure from atomic expressions of the form p ∈ R and a : b ∈ (Σ ∪ {(cid:15)}) × (∆ ∪ {(cid:15)}).

Such an f is called probabilistic if

(cid:80)x,y f (x, y) = 1, so that it is a probability distribution over string
pairs. We oﬀer two theorems:2 (1) f is probabilistic iﬀ it can be computed by a Markovian transducer, i.e.,
one in which each state has total outgoing probability of 1 (out-arc probabilities plus stopping probability)
and the expected path length is ﬁnite.
(2) f is probabilistic iﬀ it can be expressed as a probabilistic
regexp, that is, a regexp built up from atomic expressions a : b using concatenation, probabilistic union +p,
and probabilistic closure ∗p. Here f +p g def= pf + (1 − p)g, and f ∗p

def= (pf )∗(1 − p), for 0 ≤ p < 1.

Probabilistic regexps can be extended with other operators (crossprod, multi-way +p, PCFG approxima-
tion [16], . . . ). In particular, probabilistic relations are closed under compositions of the form f ◦condit(g) (if
(cid:80)y(cid:48) g(x, y(cid:48)): it is a
range(f ) ⊆ domain(g)). Here condit(g) is the conditional probability distribution g(x, y)/
weighted regular relation expressible as recip(weighted-domain(g))◦g, where recip(h) is constructed by taking
the reciprocal of all nonzero weights in a determinized acceptor for h. Conditional-distribution transducers for
use in composition can also be built by stochastic variants of directed replacement, including directed replace-
ment by another conditional transducer [18, 7]. Finally, notice that since any weighted relation can be normal-
ized to a probabilistic one, reweighting or log-linear constructions are possible: e.g., let f1, . . . fn be weighted
acceptors that separately score a string, and consider the transducer normalize(f1 (cid:12) f2 (cid:12) · · · (cid:12) fn) ◦ condit(g),
where (cid:12) is weighted intersection (Hadamard product) so that (f1 (cid:12) f2)(x) def= f1(x)f2(x).

A parameterized probabilistic relation f is a recipe for turning a parameter vector θ into a probabilistic
relation, denoted fθ. For example, the recipe might use θ to obtain arc probabilities for a transducer of ﬁxed
topology, or to obtain operator probabilities for an otherwise ﬁxed probabilistic regexp.

It is important not to simply identify parameters with transducer arcs. For example, if f is deﬁned as
the composition of g and h, then we wish its parameter set to be the union of g’s and h’s (few parameters),
even though its arc set is the product of g’s and h’s (many arcs). The fewer parameters, the easier learning
is. Indeed it often pays to reuse parameters explicitly: a single parameter for gemination might determine,
or at least aﬀect, the probabilities of arcs mapping t : tt, k : kk, etc. in a transducer from English to Japanese
phonology. We particularly like log-linear (maximum-entropy) parameterizations, since then the weights of
several meaningful domain-speciﬁc features (like gemination) can interact to determine an arc probability or
operator probability. In [5] we suggest several log-linear parameterizations of arc weights for both Markovian
and non-Markovian probabilistic transducers, including one inspired by current ﬂow in electrical networks.
Given a sample of pairs (xi, yi) from the unknown distribution fˆθ, we want to ﬁnd θ that maximizes
(cid:81)i fθ(xi, yi).3 The EM method [4] starts with some guess fθ and repeatedly reestimates θ,
the likelihood
converging to a local optimum. Roughly, the E step of reestimation ﬁgures out what paths were probably
used to generate the sample if it came from the current fθ, and the M step updates θ to make those paths
more likely. The M step depends on the parameterization and the E step serves the M step’s needs.

In the simplest case, fθ is a Markovian transducer and the parameters θ are the arc probabilities. Then
the E step needs to ﬁnd the expected count of visits to each arc; the M step sets an arc’s new probability
as proportional to its count. But if fθ is implemented as a (possibly minimized) composition of two such
Markovian transducers, T1 ◦ T2, the M step will have to compute new probabilities for arcs in the original
T1 and T2—so the E step must implicitly “undo” the composition and minimization, and ﬁnd the expected
count of visits to each arc in T1 and T2.4 We now see how to make the composed machine carry out such an
E step without “undoing” anything. The idea also works for machines built using other operators.

2To prove (2)⇒, get a machine for f and apply the Kleene-Sch¨utzenberger (= Floyd-Warshall) construction, taking care to
write each regexp in the construction as a constant times a probabilistic regexp. To prove (1)⇒, just convert this probabilistic
regexp into a Markovian transducer. Full proofs are straightforward but suppressed here for space reasons.

3Perhaps times a prior probability P (θ), which EM allows if the M step does. Or one can choose to maximize the conditional

probability

(cid:81)i fθ(yi | xi) instead of the joint: just make the M step improve the likelihood of the expected paths given xi.

4As deﬁned by a distribution over pairs of paths that could have generated (xi, yi) via some intermediate representation zi.

2

3 The Technique: Expectation Semirings

A unifying framework for ﬁnite-state computation is given in [3]. A ﬁnite-state function is represented by
a ﬁnite-state machine over an input alphabet Σ, with arc weights in a semiring (K, ⊕, ⊗).5 The machine
maps each input x ∈ Σ∗ to a weight in K, found by using ⊕ to sum over the weights of all paths that accept
x. The weight of each path is found by multiplying its arcs’ weights using ⊗. If the machine has (cid:15)-cycles,
it may be necessary to sum over inﬁnitely many paths; then the semiring also needs a closure operation ∗,
interpreted as k∗ =

∞
i=0 ki, which makes it possible to eliminate all (cid:15) arcs.

To obtain weighted transducers from Σ∗ to ∆∗, one labels each arc with an output string as well as an
input symbol and a weight. Then the machine assigns a weight to each string pair (x, y) ∈ Σ∗ × ∆∗. This is
found by summing the weights of all paths that accept x while outputting y.6

(cid:76)

A probabilistic regular relation can be computed by a transducer weighted with the semiring (R≥0, +, ×).7
The key idea of this paper is to augment this semiring with expectation information. Then a weight records
not only a probability but also (e.g.) the degree to which each arc has contributed to that probability.

Let us deﬁne the problem abstractly. Suppose we assign each arc in the stochastic transducer a value
drawn from a set V . The total value val(π) of a path π is the sum of its arcs’ values. If Π is a set of paths,
the expected value given that we took a path in Π is E[val(π) | Π] def=
if every arc has value 1, this is the expected length of a random path in Π. We will see in the next section
that, given an appropriate assignment of values to arcs, the E step of EM can be formulated as computing
E[val(π) | Π] where Π is the set of paths compatible with an observation (xi, yi).

(cid:80)π P (π | Π) · val(π). For instance,

As always, there is also an algebraic view. Values in V can be interspersed through a probabilistic regexp.
They may be regarded as outputs onto an extra tape—or rather, into an accumulator, since they are summed
rather than concatenated. The regexp can then be regarded as deﬁning P (x, y, v). We desire the expected
value of the accumulator when xi is transduced nondeterministically to yi, namely

How to compute these expected values by ﬁnite-state methods? Notice E[val(π) | Π] = E[val(π)&Π]/P (Π),
where E[val(π)&Π] def=
(cid:80)π∈Π P (π)). We will now modify the automaton
to use a semiring in which the total weight of the paths in Π is the ordered pair t = (P (Π), E[val(π)&Π]) ∈
R≥0 × V . Once we obtain the pair t, just dividing one element by the other will give E[val(π) | Π] as desired.
The semiring we introduce for this purpose is the V -expectation semiring, (R≥0 × V, ⊕, ⊗), where

(cid:80)π∈Π P (π) · val(π) (and P (Π) def=

(cid:80)v P (v | xi, yi) · v.

(p1, v1) ⊕ (p2, v2) def= (p1 + p2, v1 + v2)

(p1, v1) ⊗ (p2, v2) def= (p1p2, p1v2 + v1p2)

(p, v)∗ def=

(p∗, p∗vp∗)

if p∗ deﬁned

We augment the machine’s arc weights to fall in this semiring. We want an invariant that the total weight of
any pathset Π is (P (Π), E[val(π)&Π]). If an arc has probability p and value v, we give it the weight (p, pv),
so that the invariant holds if Π consists of a single length-0 or length-1 path. The above deﬁnitions preserve
the invariant when we build up longer paths with ⊗ and sets of paths with ⊕ or ∗, as discussed earlier. For
example, concatenating paths π1, π2 with weights (P (π1), P (π1) · val(π1)) and (P (π2), P (π2) · val(π2)) gives
a longer path π with weight (P (π1)P (π2), P (π1)P (π2) · (val(π1) + val(π2))) = (P (π), P (π) · val(π)).

So to ﬁnd the expected value, we need the total weight ti of paths in machine T compatible with
observation (xi, yi). Standard methods now apply. ti is just the total weight of all accepting paths in xi◦T ◦yi.
Finding such totals is the single-source algebraic path problem (= semiring “shortest” path), which can
Indeed, the generalization to all-pairs algebraic path (=
be solved approximately by relaxation [13].
semiring transitive closure)—where various exact O(n3) algorithms are known [6]—is already implemented
inside any WFSA (cid:15)-elimination routine [15]. So for convenience, one could simply minimize the machine
((cid:15) × xi) ◦ T ◦ (yi × (cid:15)), yielding a one-state machine that maps ((cid:15), (cid:15)) to ti, and then just read ti oﬀ the machine.
Thus, if weights are augmented with expectations, the entire E step reduces to “compose + minimize”!
In general xi and yi can be regular languages rather than strings, representing incomplete observations.
E.g., in the traditional EM algorithm for HMMs [2], yi = Σ∗ (wholly unobserved), though [22] allows any yi.
When is the V -expectation semiring really a semiring? Notice that to take expected values, we had
Indeed, V must have the structure of a module

to assume that linear combinations of V were deﬁned.

5Such a function can be described as a formal power series over non-commuting variables Σ with coeﬃcients in (K, ⊕, ⊗).
Semiring axioms: (K, ⊗) is a monoid (meaning ⊗ : K × K → K is associative) with identity 1, (K, ⊕) is a commutative monoid
with identity 0, ⊗ distributes over ⊕ from both sides, and 0 ⊗ k = k ⊗ 0 = 0. Also k∗ = 1 ⊕ k ⊗ k∗ if deﬁned.

6By treating the (weight,output) pair on each arc as a kind of complex weight, such a transducer can be regarded as simply

a weighted automaton. However, in this paper, K denotes just the ordinary weight without the output string.

7The closure operation is deﬁned for p ∈ [0, 1) as p∗ = 1/(1 − p), so cycles are allowed if they have weights in [0, 1).

3

(a generalization of a vector space).
If R is the semiring of probabilities (any semiring will do), then
K = (R × V, ⊕, ⊗) as deﬁned above is a semiring provided that V is a two-sided R-semimodule.8 Its additive
and multiplicative identities are (0, 0) and (1, 0). K is commutative iﬀ R is commutative and commutes with
V (r ⊗ v = v ⊗ r). K has additive inverses iﬀ R does: −(r, v) = (−r, (−1) ⊗ v). If so, K has multiplicative left
inverses iﬀ R does: (r, v)−1 = (r−1, −r−1 ⊗ v ⊗ r−1). These properties hold for R = R, and the last (as we
will show elsewhere) nontrivially leads to an eﬃcient minimization algorithm for our K-weighted transducers
(cf. [14]). We have not yet investigated the eﬀect on determinizability of replacing semiring R with K.

4 Computing the Expectation in Practice

As an example, we use an expectation semiring to perform the E step for composed Markovian transducers
T1 ◦ T2, as promised at the end of section 2. Number the arcs in (T1, T2) from 1 to m. Let V = Rm (length-m
vectors) and let the value of arc i be the ith basis vector. Now proceed as in section 3. The arc values are
used to deﬁne arc weights in R × V for T1 and T2, and hence also for their composition T . Then for each pair
(xi, yi), compute ti ∈ R × V and thence the expected value, i.e., the expected # of traversals of each arc, as
desired. (A similar technique gets the expected traversals of each subexpression in a probabilistic regexp.)
As another example, consider a log-linear parameterization where each arc has a vector of features that
determines its probability. The M step is now a convex maximization problem traditionally solved by iterative
scaling [19], which needs to know how many times each feature was observed in the sample.9 To reconstruct
the expectation of this (the E step), simply let each arc’s value be its feature vector and proceed as before.
def= xi ◦ T ◦ yi in order
to ﬁnd ti = w0n, the total semiring weight of paths from initial state 0 to ﬁnal state n (assumed WLOG to be
unique and unweighted). An exact answer takes O(n3) time in the worst case. But when Ti is acyclic10—e.g.,
it is often an HMM-style trellis—w0n can easily be found in O(m) time (for m arcs) by computing w0j for
all j in topologically sorted order. As a generalization, one can partition the transducer graph into strongly
connected components (in linear time) and run all-pairs algebraic path on each component separately to ﬁnd
some of the wjk values, after which all the w0j can be computed in O(m) time roughly as before [13].

Now for some important remarks on eﬃciency. Section 3 runs algebraic path on Ti

When V counts arcs and Ti is a trellis, this method is a variant of the forward-backward algorithm [2] with
no backward pass: instead of pushing cumulative probabilities backward to the arcs, it pushes cumulative
arcs (more generally, values in V ) forward to the probabilities. This is slower because our ⊕ and ⊗ are vector
operations, and the vectors rapidly lose sparsity as they are added together. Luckily, the forward-backward
idea can be used here—indeed in a fully general form allowing any V and (perhaps cyclic) Ti. It exploits our
semiring structure to avoid ⊕ and ⊗ (though they are still crucial to construct Ti!). Write wjk as (pjk, vjk),
and let w1
jk denote the total weight of length-1 paths from j to k. The forward probabilities p0j can be
computed just like w0j in the previous paragraph, but using only operations on (R, +, ×) without V , and the
backward probabilities pkn similarly. (Indeed this just solves a R-linear system, a well-studied problem at
jkpkn).
O(n) space, O(nm) time, approximation faster [9].) Then w0n = (p0n, v0n) is found as (p0n,

(cid:80)j,k p0jv1

5 Conclusions

We know of no previously published EM algorithm for general FSTs (with (cid:15)), even for the simplest param-
eterization. Our expectation-semiring solution seems general enough to work with many parameterizations,
though details will vary. It may also be a starting point for faster or more robust parameter estimation
methods. Conjugate gradient is an easy variation because of the linearity of transducers (vs. neural nets):
the gradient of the mapping from arc weights θ to fθ(xi, yi) is exactly the v0n vector computed above, with
the change that arc i must be given weight (p, v) instead of (p, pv) (where v = ith basis vector). To avoid local
maxima, one might try deterministic annealing [20], or randomized methods, or place a prior on θ. Finally,
parameter estimation enables experiments with FSA model merging methods [24] to learn FST topology.

8Module axioms: V is a commutative monoid with operation denoted by ⊕ and identity by 0 (note the overloaded notation!).
It is equipped with a left scalar multiplication ⊗ : R × V → V that satisﬁes 0 ⊗ v = 0 = r ⊗ 0, 1 × v = v, r ⊗ (s ⊗ v) = (r ⊗ s) ⊗ v,
(r ⊕ s) ⊗ v = r ⊗ v ⊕ s ⊗ v, r ⊗ (v ⊕ w) = r ⊗ v ⊕ r ⊗ w. Similarly it has a right scalar multiplication ⊗ : V × R → V .

9This is for a log-linear distribution P (path). For a Markovian machine, we need a conditional log-linear distribution
P (arc | state); then the M step needs the E step to collect counts of states as well as features [5], which is straightforward. In
either case, iterative scaling needn’t be run to convergence on each M step; [21] runs just one iteration to get a GEM algorithm.
10In particular, if xi and yi are acyclic (e.g., fully observed strings), then eliminating (cid:15) : (cid:15) cycles from T ensures that the
composition will “unroll” T into an acyclic machine Ti. If only xi is acyclic, then Ti is still acyclic if domain(T ) has no (cid:15) cycles.

4

References

[1] Lalit R. Bahl, Frederick Jelinek, and Robert L. Mercer. A maximum likelihood approach to continuous
speech recognition. IEEE Trans. on Pattern Analysis and Machine Intelligence, 5(2):179–190, 1983.

[2] L. E. Baum. An inequality and associated maximization technique in statistical estimation of proba-

bilistic functions of a Markov process. Inequalities, 3, 1972.

[3] Jean Berstel and Christophe Reutenauer. Rational Series and their Languages. Springer-Verlag, 1988.

[4] A. P. Dempster, N. M. Laird, and D. B. Rubin. Maximum likelihood from incomplete data via the EM

algorithm. J. Royal Statist. Soc. Ser. B, 39(1):1–38, 1977. With discussion.

[5] Jason Eisner. Smoothing a Probabilistic Lexicon Via Syntactic Transformations. PhD thesis, University

of Pennsylvania, 2001.

[6] Eugene Fink. A survey of sequential and systolic algorithms for the algebraic path problem. Technical

Report CS-92-37, Department of Computer Science, University of Waterloo, 1992.

[7] D. Gerdemann & G. van Noord. Transducers from rewrite rules with backreferences. Proc. EACL, 1999.

[8] John Goldsmith. Unsupervised learning of the morphology of a natural language. Comp. Ling., 2001.

[9] Anne Greenbaum. Iterative Methods for Solving Linear Systems. Number 17 in Frontiers in Applied

Mathematics. Society for Industrial and Applied Mathematics (SIAM), 1997.

[10] Lauri Karttunen, Jean-Pierre Chanod, Gregory Grefenstette, , and Anne Schiller. Regular expressions

for language engineering. Journal of Natural Language Engineering, 2(4):305–328, 1996.

[11] Kevin Knight and Yaser Al-Onaizan. Translation with ﬁnite-state devices. In Proc. of 4th AMTA, 1998.

[12] Kevin Knight and Jonathan Graehl. Machine transliteration. Computational Linguistics, 24(4), 1998.

[13] Mehryar Mohri. General algebraic frameworks and algorithms for shortest-distance problems. Technical

Memorandum 981210-10TM, AT&T Labs—Research, 1998.

[14] Mehryar Mohri. Minimization algorithms for sequential transducers. Theoretical CS, 324:177–201, 2000.

[15] Mehryar Mohri. Generic Epsilon-Removal and Input Epsilon-Normalization Algorithms for Weighted

Transducers. International Journal of Foundations of Computer Science, to appear 2001.

[16] Mehryar Mohri and Mark-Jan Nederhof. Regular approximation of context-free grammars through
transformation. In Jean-Claude Junqua and Gertjan van Noord, editors, Robustness in Language and
Speech Technology, chapter 9, pages 153–163. Kluwer Academic Publishers, The Netherlands, 2001.

[17] Mehryar Mohri, Fernando Pereira, and Michael Riley. Weighted automata in text and speech processing.

In Workshop on Extended Finite-State Models of Language (ECAI-96), pages 46–50, Budapest, 1996.

[18] Mehryar Mohri and Richard Sproat. An eﬃcient compiler for weighted rewrite rules. In Proceedings of

the 34th Annual Meeting of the ACL, pages 231–238, Santa Cruz, 1996.

[19] S. Della Pietra, V. Della Pietra, and J. Laﬀerty. Inducing features of random ﬁelds. IEEE Transactions

Pattern Analysis and Machine Intelligence, 19(4), 1997.

[20] A. V. Rao, K. Rose, and A. Gersho. A deterministic annealing approach to discriminative hidden
Markov model design. In IEEE Workshop on Neural Networks and Signal Processing, September 1997.

[21] Stefan Riezler. Probabilistic Constraint Logic Programming. PhD thesis, Universit¨at T¨ubingen, 1999.

[22] Eric Sven Ristad. Hidden markov models with ﬁnite state supervision.

In Andr´as Kornai, editor,

Extended Finite State Models of Language. Cambridge University Press, 1998.

[23] Eric Sven Ristad and Peter N. Yianilos. Learning string edit distance. Princeton CS-TR-532-96, 1996.

[24] Andreas Stolcke and Stephen M. Omohundro. Best-ﬁrst model merging for hidden Markov model

induction. Technical Report ICSI TR-94-003, ICSI, Berkeley, CA, 1994.

5

