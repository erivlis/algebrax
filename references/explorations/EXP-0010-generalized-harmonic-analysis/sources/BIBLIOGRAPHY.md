# Annotated Bibliography — EXP-0010: Generalized Harmonic Analysis

## Primary Archived Papers (`papers/`)

1. **[PUSCHEL-2006]** Markus Püschel and José M. F. Moura, *"Algebraic Signal Processing Theory"*, arXiv:cs/0612077 (published in *IEEE Transactions on Signal Processing*, Vol. 56, No. 8, pp. 3572–3585, 2008).
   - **Local Archive:** [`papers/Puschel_Moura_2006_Algebraic_Signal_Processing.pdf`](../papers/Puschel_Moura_2006_Algebraic_Signal_Processing.pdf)
   - **Relevance to AlgebraX:** Proves that every linear discrete signal processing model is a triple $(\mathcal{A}, \mathcal{M}, \Phi)$ where the filter space $\mathcal{A} = k[x_1, \dots, x_n]/I$ is a polynomial quotient ring (`QuotientRing` from `EP-0201`/`EP-0220`), the shift operator is multiplication by $x_i$ (the **Stickelberger companion matrix** $M_{x_i}$ from `EP-0221`), and the generalized Fourier transform is the eigenbasis that diagonalizes $\mathcal{A}$ into irreducible spectral components ($x^N - 1 \to$ DFT, $T_N(x) \to$ DCT/DST).

2. **[KONDOR-2007]** Risi Kondor, *"The skew spectrum of functions on finite groups and their homogeneous spaces"*, arXiv:0712.4259, 2007.
   - **Local Archive:** [`papers/Kondor_2007_NonAbelian_Fourier_Skew_Spectrum.pdf`](../papers/Kondor_2007_NonAbelian_Fourier_Skew_Spectrum.pdf)
   - **Relevance to AlgebraX:** Formalizes the non-Abelian Fourier transform $\hat{f}(\rho_\lambda) = \sum_{g \in G} f(g)\rho_\lambda(g)$ over matrix representations of finite groups (`EP-0210`), Plancherel inversion, bispectral invariants, and Clausen / Diaconis–Rockmore subgroup-chain fast transforms on $S_n$.

3. **[KONDOR-2018]** Risi Kondor and Shubhendu Trivedi, *"On the Generalization of Equivariance and Convolution in Neural Networks to the Action of Compact Groups"*, arXiv:1802.03690 (*ICML 2018*).
   - **Local Archive:** [`papers/Kondor_Trivedi_2018_Group_Equivariant_Convolution.pdf`](../papers/Kondor_Trivedi_2018_Group_Equivariant_Convolution.pdf)
   - **Relevance to AlgebraX:** Establishes via the Peter–Weyl theorem that equivariant linear layers on homogeneous spaces $G/H$ are precisely group convolutions diagonalized by the non-Abelian matrix Fourier transform $\hat{f}(\rho_\lambda) \cdot \hat{h}(\rho_\lambda)$.

4. **[HAMMOND-2009]** David K. Hammond, Pierre Vandergheynst, and Rémi Gribonval, *"Wavelets on Graphs via Spectral Graph Theory"*, arXiv:0912.3848 (*Applied and Computational Harmonic Analysis*, Vol. 30, No. 2, pp. 129–150, 2011).
   - **Local Archive:** [`papers/Hammond_Vandergheynst_Gribonval_2009_Spectral_Graph_Wavelets.pdf`](../papers/Hammond_Vandergheynst_Gribonval_2009_Spectral_Graph_Wavelets.pdf)
   - **Relevance to AlgebraX:** Introduces spectral graph wavelets $T_g^t = g(t\mathcal{L})$ and the fast Chebyshev polynomial recurrence $T_k(\tilde{\mathcal{L}})f = 2\tilde{\mathcal{L}}T_{k-1}(\tilde{\mathcal{L}})f - T_{k-2}(\tilde{\mathcal{L}})f$, allowing spectral filtering on Graph, Hodge (`EP-0160`), and Sheaf (`EP-0161`) Laplacians using purely sparse matrix-vector products without $O(N^3)$ diagonalization.

---

## Foundational Textbooks & Monographs

5. **[DIACONIS-1988]** Persi Diaconis, *Group Representations in Probability and Statistics*, IMS Lecture Notes–Monograph Series, Vol. 11, 1988.
   - **Relevance:** Classic monograph establishing non-Abelian Fourier analysis on $S_n$ for Markov chain mixing times (riffle shuffles, random transpositions) and spectral analysis of ranked voting data.

6. **[ROTA-1964]** Gian-Carlo Rota, *"On the Foundations of Combinatorial Theory I: Theory of Möbius Functions"*, *Zeitschrift für Wahrscheinlichkeitstheorie und Verwandte Gebiete*, Vol. 2, pp. 340–368, 1964.
   - **Relevance:** Formalizes the Incidence Algebra $I(P, R)$ of a locally finite poset $(P, \le)$, the Zeta function $\zeta(x, y) = 1_{x \le y}$, and the Möbius inversion theorem $\mu = \zeta^{-1}$, providing the harmonic analysis of `algebrax.lattice`.
