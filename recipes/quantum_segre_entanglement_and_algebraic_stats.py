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
# # Quantum Segre Entanglement Varieties & Algebraic Statistics Independence Models
#
# ## Theoretical Foundations
# 1. **Segre Determinantal Variety (Quantum Separability)**:
#    A 2-qubit pure state $|\psi\rangle = z_{00}|00\rangle + z_{01}|01\rangle + z_{10}|10\rangle
#    + z_{11}|11\rangle$ is separable (tensor rank 1: $|\psi\rangle = |u\rangle \otimes |v\rangle$)
#    if and only if its amplitudes lie on the quadratic Segre cone
#    $V(z_{00} z_{11} - z_{01} z_{10}) \subseteq \mathbb{A}^4$.
#    Because $z_{00} z_{11} - z_{01} z_{10}$ is homogeneous, rescaling a ket by any non-zero factor
#    (e.g., omitting the $1/\sqrt{2}$ normalization constant) leaves ideal membership invariant.
#    Every Bell state ($z_{00} = z_{11} = 1, z_{01} = z_{10} = 0$) fails this ideal membership test,
#    providing an exact algebraic entanglement witness!
# 2. **Algebraic Statistics (Markov Independence Toric Variety)**:
#    A $2 \times 2$ joint probability table $P = (p_{00}, p_{01}, p_{10}, p_{11})$ represents two
#    statistically independent binary random variables ($I(X; Y) = 0$) if and only if $P$ lies on
#    the intersection of the Segre toric variety $p_{00} p_{11} - p_{01} p_{10} = 0$ and the
#    probability simplex hyperplane $p_{00} + p_{01} + p_{10} + p_{11} - 1 = 0$.
# 3. **Contravariant Segre Parameterization (`PolynomialMap`)**:
#    The outer-product map
#    $\sigma: \mathbb{A}^2 \times \mathbb{A}^2 \to \operatorname{Seg}(\mathbb{A}^2 \times \mathbb{A}^2)$
#    sending $(u_0, u_1, v_0, v_1) \mapsto (u_0 v_0, u_0 v_1, u_1 v_0, u_1 v_1)$ realizes the Segre
#    variety as the exact `syzygy_variety` of rank-1 bilinear monomials!

# %%
import math
from fractions import Fraction

import algebrax as ax
from algebrax.algebra import MultivariatePolynomialAlgebra, StandardField
from algebrax.variety import AffineVariety, PolynomialMap, syzygy_variety
from algebrax.verification import verify_affine_variety_laws, verify_polynomial_map_laws


def format_point(pt: tuple[Fraction, ...]) -> str:
    """Format an exact rational point tuple cleanly for display."""
    return '(' + ', '.join(str(c) for c in pt) + ')'


def build_segre_variety() -> AffineVariety[Fraction]:
    """Construct the 2x2 Segre determinantal variety V(z00*z11 - z01*z10) in A^4."""
    q_field = StandardField(Fraction)
    r4 = MultivariatePolynomialAlgebra(q_field, n_vars=4, order='grevlex')
    z00, z01, z10, z11 = (r4.gen(i) for i in range(4))
    det_2x2 = r4.sub(r4.mul(z00, z11), r4.mul(z01, z10))
    return AffineVariety(r4, [det_2x2])


# %% [markdown]
# ## Step 1: Exact Quantum Separability vs. Bell Entanglement Detection
#
# Working over exact rationals $\mathbb{Q}$ on the homogeneous Segre cone (using unnormalized ket
# amplitudes to keep exact `Fraction` coordinates without irrational $1/\sqrt{2}$ factors), we verify
# that the product state $|+\rangle \otimes |0\rangle \propto (1, 0, 1, 0)$ is a smooth point of the
# Segre variety while the maximally entangled Bell state $|\Phi^+\rangle \propto (1, 0, 0, 1)$ lies
# strictly outside it.

# %%
q_field = StandardField(Fraction)
segre = build_segre_variety()
assert segre.krull_dimension() == 3
assert all(verify_affine_variety_laws(segre).values())

# Unnormalized separable product state |+> (x) |0> ~ (1, 0, 1, 0) lies on the Segre cone
sep_state = (Fraction(1), Fraction(0), Fraction(1), Fraction(0))
# Unnormalized maximally entangled Bell state |Phi+> ~ (1, 0, 0, 1) lies strictly OFF the Segre cone
bell_state = (Fraction(1), Fraction(0), Fraction(0), Fraction(1))

assert segre.contains_point(sep_state)
assert segre.is_smooth_at(sep_state)
assert not segre.contains_point(bell_state)

# Confirm via algebrax.tensor outer product (rank-1 contraction)
u_vec = {0: 1.0, 1: 1.0}
v_vec = {0: 1.0, 1: 0.0}
prod_tensor = ax.tensor.einsum('i,j->ij', u_vec, v_vec)
prod_dict = dict(prod_tensor)
assert prod_dict.get((0, 0), 0.0) == float(sep_state[0])
assert prod_dict.get((0, 1), 0.0) == float(sep_state[1])
assert prod_dict.get((1, 0), 0.0) == float(sep_state[2])
assert prod_dict.get((1, 1), 0.0) == float(sep_state[3])

print('Step 1: Quantum 2-Qubit Segre Variety V(z00*z11 - z01*z10)')
print(f'  Krull dimension = {segre.krull_dimension()} (affine cone over P^1 x P^1)')
print(f'  Separable state {format_point(sep_state)} in Segre? {segre.contains_point(sep_state)} | tensor={prod_dict}')
print(f'  Bell state      {format_point(bell_state)} in Segre? {segre.contains_point(bell_state)} (ENTANGLED!)')

# %% [markdown]
# ## Step 2: Syzygy Implicitization & Contravariant Pullback (`PolynomialMap`)
#
# Given only the parametric rank-1 outer product $\sigma(u, v) = (u_0 v_0, u_0 v_1, u_1 v_0, u_1 v_1)$,
# `syzygy_variety` eliminates the latent qubit parameters $(u_0, u_1, v_0, v_1)$ automatically and
# recovers the defining equation $z_{00} z_{11} - z_{01} z_{10} = 0$.

# %%
r_uv = MultivariatePolynomialAlgebra(q_field, n_vars=4, order='grevlex')
u0, u1, v0, v1 = (r_uv.gen(i) for i in range(4))
segre_comps = [r_uv.mul(u0, v0), r_uv.mul(u0, v1), r_uv.mul(u1, v0), r_uv.mul(u1, v1)]

recovered_segre = syzygy_variety(r_uv, segre_comps)
assert recovered_segre.ideal.basis == segre.ideal.basis

domain = AffineVariety(r_uv, [])
segre_map = PolynomialMap(domain, segre, segre_comps)
r4 = segre.ring
assert all(
    verify_polynomial_map_laws(
        segre_map,
        [r4.one, r4.gen(0), r4.gen(3), r4.sub(r4.mul(r4.gen(0), r4.gen(3)), r4.mul(r4.gen(1), r4.gen(2)))],
        [(Fraction(1), Fraction(2), Fraction(3), Fraction(5))],
    ).values()
)

print('\nStep 2: Syzygy Implicitization & Contravariant Pullback')
print('  Recovered equation: z00*z11 - z01*z10 = 0')
print(f'  Sparse polynomial representation: {recovered_segre.ideal.basis[0]}')

# %% [markdown]
# ## Step 3: Algebraic Statistics — $2 \times 2$ Binary Independence Model ($\operatorname{Seg} \cap \Delta_3$)
#
# Intersecting the Segre variety with the probability simplex hyperplane
# $p_{00} + p_{01} + p_{10} + p_{11} = 1$ yields the 2-dimensional statistical independence surface
# parameterized by the two marginal probabilities $(p_X, p_Y)$. Points on this variety have exact
# zero mutual information $I(X; Y) = 0$.

# %%
z00, z01, z10, z11 = (r4.gen(i) for i in range(4))
simplex_eq = r4.sub(r4.add(r4.add(z00, z01), r4.add(z10, z11)), r4.one)
simplex = AffineVariety(r4, [simplex_eq])
indep_model = segre.intersect(simplex)
assert indep_model.krull_dimension() == 2

# Independent joint distribution P(X=0)=1/3, P(Y=0)=1/4
p_indep = (Fraction(1, 12), Fraction(3, 12), Fraction(2, 12), Fraction(6, 12))
# Correlated joint distribution (0.4, 0.1, 0.1, 0.4)
p_corr = (Fraction(2, 5), Fraction(1, 10), Fraction(1, 10), Fraction(2, 5))

assert indep_model.contains_point(p_indep)
assert not indep_model.contains_point(p_corr)

mi_indep = ax.probability.mutual_information(
    {
        0: {0: float(p_indep[0]), 1: float(p_indep[1])},
        1: {0: float(p_indep[2]), 1: float(p_indep[3])},
    }
)
mi_corr = ax.probability.mutual_information(
    {
        0: {0: float(p_corr[0]), 1: float(p_corr[1])},
        1: {0: float(p_corr[2]), 1: float(p_corr[3])},
    }
)
assert math.isclose(mi_indep, 0.0, abs_tol=1e-12)
assert mi_corr > 0.2

print('\nStep 3: Algebraic Statistics Independence Model (Segre cap Simplex)')
print(f'  Model dimension = {indep_model.krull_dimension()} (marginal DOF: p_X, p_Y)')
print(
    f'  Independent table {format_point(p_indep)} in model? '
    f'{indep_model.contains_point(p_indep)} | I(X;Y) = {mi_indep:.2e} bits'
)
print(
    f'  Correlated table  {format_point(p_corr)} in model? '
    f'{indep_model.contains_point(p_corr)} | I(X;Y) = {mi_corr:.4f} bits'
)
print('==========================================================================')
print('Recipe: Quantum Segre Entanglement & Algebraic Stats Finished Successfully!')
print('==========================================================================')
