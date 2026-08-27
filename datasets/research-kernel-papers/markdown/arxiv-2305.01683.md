# arXiv:2305.01683v1 [astro-ph.EP] 2 May 2023

## Timescales of Chaos in the Inner Solar System: Lyapunov Spectrum and Quasi-integrals of Motion

Federico Mogavero,∗ Nam H. Hoang,† and Jacques Laskar‡

IMCCE, CNRS UMR 8028, Observatoire de Paris, Universit´e PSL, Sorbonne Universit´e 77 Avenue Denfert-Rochereau, 75014 Paris, France (Dated: May 4, 2023)

Numerical integrations of the Solar System reveal a remarkable stability of the orbits of the inner planets over billions of years, in spite of their chaotic variations characterized by a Lyapunov time of only 5 million years and the lack of integrals of motion able to constrain their dynamics. To open a window on such long-term behavior, we compute the entire Lyapunov spectrum of a forced secular model of the inner planets. We uncover a hierarchy of characteristic exponents that spans two orders of magnitude, manifesting a slow-fast dynamics with a broad separation of timescales. A systematic analysis of the Fourier harmonics of the Hamiltonian, based on computer algebra, reveals three symmetries that characterize the strongest resonances responsible for the orbital chaos. These symmetries are broken only by weak resonances, leading to the existence of quasi-integrals of motion that are shown to relate to the smallest Lyapunov exponents. A principal component analysis of the orbital solutions independently conﬁrms that the quasi-integrals are among the slowest degrees of freedom of the dynamics. Strong evidence emerges that they eﬀectively constrain the chaotic diﬀusion of the orbits, playing a crucial role in the statistical stability over the Solar System lifetime.

##### I. INTRODUCTION

The planetary orbits in the inner Solar System (ISS) are chaotic, with a Lyapunov time distributed around 5 million years (Myr) [1–4]. Still, they are statistically very stable over a timescale that is a thousand times longer. The probability that the eccentricity of Mercury exceeds 0.7, leading to catastrophic events (i.e., close encounters, collisions, or ejections of planets), is only about 1% over the next 5 billion years (Gyr) [5–7]. The dynamical halflife of Mercury orbit has recently been estimated at 30–40 billion years [4, 7]. A disparity of nearly four orders of magnitude between the Lyapunov time and the timescale of dynamical instability is intriguing, since the chaotic variations of the orbits of the inner planets cannot be constrained a priori. While the total energy and angular momentum of the Solar System are conserved, the disproportion of masses between the outer and inner planets implies that unstable states of the ISS are in principle easily realizable through exchanges of these quantities. The surprising stability of the ISS deserves a global picture in which it can emerge more naturally.

To our knowledge, the only study addressing the timescale separation in the long-term dynamics of the ISS is based on the simpliﬁed secular dynamics of a massless Mercury [8]: All the other planets are frozen on regular quasi-periodic orbits; secular interactions are expanded to ﬁrst order in masses and degree 4 in eccentricities and inclinations; an a priori choice of the relevant terms of the Hamiltonian is made. The typical instability time of about 1 Gyr [8, 9] is, however, too short and in signiﬁcant contrast with realistic numerical integrations of the Solar

∗ Corresponding author. federico.mogavero@obspm.fr † Corresponding author. nam.hoang-hoai@obspm.fr ‡ jacques.laskar@obspm.fr

System, which show a general increase of the instability rate with the complexity of the dynamical model [7]. We have shown that truncating the secular Hamiltonian of the ISS at degree 4 in eccentricities and inclinations results in an even more stable dynamics, with an instability rate at 5 Gyr that drops by orders of magnitude when compared to the full system[10]. From the perspective of these latest ﬁndings, the small probability of 1% of an instability over the age of the Solar System may be naturally regarded as a perturbative eﬀect of terms of degree 6 and higher. Clearly, the striking stability of the dynamics at degree 4 is even more impressive in the present context, and remains to be explained.

A strong separation in dynamical timescales is not uncommon among classical quasi-integrable systems [e.g., 11, 12]. This is notably evinced by the Fermi-PastaUlam-Tsingou (FPUT) problem, which deals with a chain of coupled weakly-anharmonic oscillators [13]. Far from Kolmogorov-Arnold-Moser (KAM) and Nekhoroshev regimes (as is likely to be pertinent to the ISS, see Sect. III), one can generally state that the exponential divergence of close trajectories occurring over a Lyapunov time is mostly tangent to the invariant tori deﬁned by the action variables of the underlying integrable problem, and hence contributes little to the diﬀusion in the action space [14, 15]. In other words, the Lyapunov time and the diﬀusion/instability time scale diﬀerently with the size of the terms that break integrability, and this can result in very diﬀerent timescales [12]. However, this argument is as general as poorly satisfactory in addressing quantitatively the timescale separation in a complex problem as the present one. Moreover, even though order-of-magnitude estimates of the chaotic diffusion in the ISS suggest that it may take hundreds of million years to reach the destabilizing secular resonance g1 − g5[16], the low probability of an instability over 5 Gyr still remains unexplained [4]. Establishing more pre-

cisely why the ISS is statistically stable over a timescale comparable to its age is a valuable step in understanding the secular evolution of planetary systems through metastable states [4, 17][18]. With its 8 secular degrees of freedom (d.o.f.), this system also constitutes a peculiar bridge between the low-dimensional dynamics often addressed in celestial mechanics and the systems with a large number of bodies studied in statistical mechanics: It cannot beneﬁt from the straightforward application of standard methods of the two ﬁelds [e.g., 19, Appendix A].

This work aims to open a window on the long-term statistical behavior of the inner planet orbits. Section II brieﬂy recalls the dynamical model of forced secular ISS introduced in Ref. [4]. Section III presents the numerical computation of its Lyapunov spectrum. Section IV introduces the quasi-symmetries of the resonant harmonics of the Hamiltonian and the corresponding quasiintegrals (QIs) of motion. Section V establishes a geometric connection between the quasi-integrals and the slowest d.o.f. of the dynamics via a principal component analysis (PCA) of the orbital solutions. Section VI states the implications of the new ﬁndings on the long-term stability of the ISS. We ﬁnally discuss the connections with other classical quasi-integrable systems and the methods used in this work.

##### II. DYNAMICAL MODEL

The long-term dynamics of the Solar System planets consists essentially of the slow precession of their perihelia and nodes, driven by secular, orbit-averaged gravitational interactions [2, 20]. At ﬁrst order in planetary masses, the secular Hamiltonian corrected for the leading contribution of general relativity reads [e.g. 4, 21]

i−1

8

3G2m20mi c2a2i 1 − e2i

Gmiml ri − rl

H = −

+

. (1)

i=1

l=1

The planets are indexed in order of increasing semi-major axes (ai)8i=1, m0 and mi are the Sun and planet masses, respectively, ei the eccentricities, G the gravitational constant and c the speed of light. The vectors ri are the heliocentric positions of the planets, and the bracket operator represents the averaging over the mean longitudes resulting from the elimination of the non-resonant Fourier harmonics of the N-body Hamiltonian [4, 21]. Hamiltonian (1) generates Gauss’s dynamics of Keplerian rings [4, 22], whose semi-major axes ai are constants of motion of the secular dynamics.

By developing the 2-body perturbing function [23, 24] in the computer algebra system TRIP [25, 26], the secular Hamiltonian can be systematically expanded in series of the Poincar´e rectangular coordinates in complex form,

xi = Λi 1 − 1 − e2iEj 

,

i

1 4

sin(Ii/2)EjΩ

yi = 2Λi 1 − e2i

,

i

(2)

where Λi = µi[G(m0 + mi)ai]1/2, µi = m0mi/(m0 + mi) being the reduced masses of the planets, Ii the inclinations, i the longitudes of the perihelia and Ωi the longitudes of the nodes[27]. Pairs (xi,−jxi) and (yi,−jyi) are canonically conjugate momentum-coordinate variables. When truncating at a given total degree 2n in eccentricities and inclinations, the expansion provides Hamiltonians H2n = H2n[(xi,x¯i,yi,y¯i)8i=1] that are multivariate polynomials.

Valuable insight into the dynamics of the inner planets is provided by the model of a forced ISS recently proposed [4]. It exploits the great regularity of the long-term motion of the outer planets [2, 20, 28] to predetermine their orbits to a quasi-periodic form:

xi(t) =

Mi

il·ωot, yi(t) =

x˜il Ejm

l=1

Ni

il·ωot, (3)

y˜il Ejn

l=1

for i ∈ {5,6,7,8}, where t denotes time, x˜il and y˜il are complex amplitudes, mil and nil integer vectors, and ωo = (g5,g6,g7,g8,s6,s7,s8) represents the septuple of the constant fundamental frequencies of the outer orbits. Frequencies and amplitudes of this Fourier decomposition are established numerically by frequency analysis [29, 30] of a comprehensive orbital solution of the Solar System [4, Appendix D]. Gauss’s dynamics of the forced ISS is obtained by substituting the predetermined time dependence in Eq. (1),

H = H[(xi,yi)4i=1,(xi = xi(t),yi = yi(t))8i=5], (4)

so that H = H[(xi,yi)4i=1,t]. The resulting dynamics consists of two d.o.f. for each inner planet, corresponding

to the xi and yi variables, respectively. Therefore, the forced secular ISS is described by 8 d.o.f. and an explicit time dependence. As a result of the forcing from the outer planets, no trivial integrals of motion exist and its orbital solutions live in a 16-dimensional phase space.

A truncated Hamiltonian H2n for the forced ISS is readily obtained by substituting Eq. (3) in the truncated Hamiltonian H2n of the entire Solar System. At the lowest degree, H2 generates a linear, forced LaplaceLagrange (LL) dynamics. This can be analytically integrated by introducing complex proper mode variables (ui,vi)4i=1 via a time-dependent canonical transformation (xi,−jxi) → (ui,−jui), (yi,−jyi) → (vi,−jvi) [4]. Action-angle pairs (Xi,χi), (Ψi,ψi) are introduced as

ui = XiE−jχ

, vi = ΨiE−jψ

. (5)

i

i

When expressed in the proper modes, the truncated Hamiltonian can be expanded as a ﬁnite Fourier series:

H2n(I,θ,t) =

k,

Hk 2n, (I)Ej(k·θ+ ·φ(t)), (6)

### where I = (X,Ψ) and θ = (χ,ψ) are the 8-dimensional vectors of the action and angle variables, respectively, and we introduce the external angles φ(t) = −ωot. The

TABLE I. Summary of the diﬀerent models of forced secular ISS considered in this work. Gauss’s dynamics results from ﬁrst-order averaging of the N-body Hamiltonian over the mean longitudes of the planets. The dynamics generated by H2n and H2n are practically equivalent and treated as such. The H•2n models are introduced and discussed in Sec. IV D.

Hamiltonian Description Reference H Gauss’s dynamics in complex Poincar´e variables Eq. (4) H2n Truncation of Gauss’s dynamics at total degree 2n in eccentricities and inclinations Ref. [4] H2n Truncated dynamics in the action-angle variables of the Laplace-Lagrange dynamics H2 Eq. (6) and Ref. [4] H•2n Fourier harmonics that involve outer planet modes other than g5 are dropped from H2n Eq. (24)

wave vectors (k, ) belong to a ﬁnite subset of Z8×Z7. At degree 2, one has H2 = −ωLL·I, where ωLL = (gLL,sLL) ∈ R4×R4 are the LL fundamental precession frequencies of the inner planet perihelia and nodes. Hamiltonian H2n is in quasi-integrable form.

The quasi-periodic form of the outer orbits in Eq. (3) contains harmonics of order higher than one, that is, mil 1 &gt; 1 and nil 1 &gt; 1 for some i and l, where

· 1 denotes the 1-norm. Therefore, the dynamics of H2n and H2n are not exactly the same [4]. Still, the difference is irrelevant for the results of this work, so we treat the two Hamiltonians as equivalent from now on. Despite the simpliﬁcations behind Eqs. (1) and (3), the forced secular ISS has been shown to constitute a realistic model that is consistent with the predictions of reference integrations of the Solar System [2, 5, 6, 20]. It correctly reproduces the ﬁnite-time maximum Lyapunov exponent (FT-MLE) and the statistics of the high eccentricities of Mercury over 5 Gyr [4]. Table I presents a summary of the diﬀerent Hamiltonians and corresponding dynamics we consider in this work.

##### III. LYAPUNOV SPECTRUM

Ergodic theory provides a way, through the Lyapunov characteristic exponents (LCEs), to introduce a fundamental set of timescales for any diﬀerentiable dynamical system z˙ = F(z,t) deﬁned on a phase space P ⊆ RP [31–34]. If Φ(z,t) denotes the associated ﬂow and z(t) = Φ(z0,t) the orbit that emanates from the initial condition z0, the LCEs λ1 ≥ λ2 ≥ ··· ≥ λP are the logarithms of the eigenvalues of the matrix Λ(z0) deﬁned as

lim

t→∞

M(z0,t)TM(z0,t) 1/2t = Λ(z0), (7)

where M(z0,t) = ∂Φ/∂z0 is the fundamental matrix and T stands for transposition [32, 33]. Introducing the Jacobian J = ∂F/∂z, the fundamental matrix allows us to write the solution of the variational equations ζ˙ = J(z(t),t)ζ as ζ(t) = M(z0,t)ζ0, where ζ(t) ∈ Tz(t)P belongs to the tangent space of P at point z(t) and ζ0 = ζ(0). The multiplicative ergodic theorem of Oseledec [31] states that if ρ is an ergodic (i.e. invariant and indecomposable) measure for the time evolution and has compact support, then the limit in Eq. (7) exists for ρ-almost all z0, and the LCEs are ρ-almost everywhere

constant and only depend on ρ [32]. Moreover, one has

1 t

\Ez(i+1)

log M(z0,t)ζ0 = λ(i) if ζ0 ∈ Ez(i)

lim

, (8)

0

0

t→∞

for ρ-almost all z0, where λ(1) &gt; λ(2) &gt; ... are the LCEs without repetition by multiplicity, and Ez(i)

is the subspace of RP corresponding to the eigenvalues of Λ(z0) that are smaller than or equal to expλ(i), with Tz0P = Ez(1)

0

0 ⊃ Ez(2)

0 ⊃ ···. The speciﬁc choice of the RPnorm  ·  in Eq. (8) is irrelevant [32, 34]. Once the LCEs have been introduced, a characteristic timescale can be deﬁned from each positive exponent as λ−i 1. In the case of the maximum Lyapunov exponent λ1, the corresponding timescale is commonly called the Lyapunov time.

For a Hamiltonian system with p d.o.f. (i.e., P = 2p), the fundamental matrix is symplectic and the set of LCEs is symmetric with respect to zero, that is,

∆λi := λi + λ2p−i+1 = 0 for all 1 ≤ i ≤ p. (9)

If the Hamiltonian is time independent, a pair of exponents vanishes. In general, the existence of an integral of motion C = C(z) implies a pair of null exponents, one of them being associated with the direction of the tangent space that is normal to the surface of constant C [e.g. 33].

The ISS is a clear example of a dynamical system that is out of equilibrium. Its phase-space density diﬀuses seamlessly over any meaningful timescale [5, 28]. Therefore, the inﬁnite time limit in Eq. (7) is not physically relevant. The non-null probability of a collisional evolution of the inner planets [5, 6, 35, 36] implies that such limit does not even exist as a general rule. Most of the orbital solutions stemming from the current knowledge of the Solar System are indeed asymptotically unstable [4, 7]. Physically relevant quantities are the ﬁnite-time LCEs (FT-LCEs), λi(z0,t), deﬁned from the eigenvalues m1 ≥ m2 ≥ ··· ≥ mP of the time-dependent symmetric positive-deﬁned matrix M(z0,t)TM(z0,t) as

λi(z0,t) =

- 1

- 2t


log mi(z0,t). (10)

The time dependence of the phase-space density translates in the fact that no ergodic measure is realized by the dynamics, and the FT-LCEs depend on the initial condition z0 in a non-trivial way[37].

The FT-MLE of the forced secular ISS has been numerically computed over 5 Gyr for an ensemble of stable orbital solutions of the Hamiltonian H with initial

λ1

λ2

λ3

λ4

λ5

λ6

λ7

λ8

λ1

λ2

λ3

λ4

λ5

λ6

λ7

λ8

| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


110100100010000

110100100010000

0.0001 0.001 0.01 0.1 1 −12 FT-LCEs (arcsec yr )π

0.0001 0.001 0.01 0.1 1 −12 FT-LCEs (arcsec yr )π

Lyapunov characteristic times (Myr)

Lyapunov characteristic times (Myr)

107 108 109 1010 Time (yr)

107 108 109 1010 1011 Time (yr)

(b) H•4

(a) H4

- FIG. 1. Positive FT-LCEs λi of the forced secular ISS from Hamiltonians H4 (a) and H•4 [Eq. (24)] (b), and corresponding characteristic timescales λ−i 1. The bands represent the [5th, 95th] percentile range of the marginal PDFs estimated from an ensemble of 150 stable orbital solutions with very close initial conditions. The lines denote the distribution medians. The H•4 model is introduced and discussed in Sec. IV D.


conditions very close to their nominal values[38]. Its long-term distribution is quite large and does not shrink over time [4, Fig. 3]. At 5 Gyr, the probability density function (PDF) of the Lyapunov time peaks at around 4 Myr, it decays very fast below 2 Myr, while its 99th percentile reaches 10 Myr [4, Fig. 4]. The signiﬁcant width of the distribution relates to the aforementioned out-of-equilibrium dynamics of the ISS, as the FT-MLE of each orbital solution continues to vary over time. The dependence of the exponent on the initial condition is associated with the non-ergodic exploration of the phase space by the dynamics. As a remark, the fact that the lower tail of the FT-MLE distribution, estimated from more than 1000 solutions, does not extend to zero implies that invariant (KAM) tori are rare in a neighborhood of the nominal initial conditions (if they exist at all). This fact excludes that the dynamics is in a Nekhoroshev regime [12, 39], in agreement with the indications of a multidimensional resonance overlapping at the origin of chaos [19, 40]. In such a case, the long dynamical half-life of the ISS should not be interpreted in terms of an exponentially-slow Arnold diﬀusion.

Computations of the FT-MLE of the Solar System planets have been reported for more than thirty years [1, 3]. However, the retrieval of the entire spectrum of exponents still represents a challenging task. Integrating an N-body orbital solution for the Sun and the eight planets that spans 5 Gyr requires the order of a month of wall-clock time [e.g. 41]. The computation by a standard method of the entire Lyapunov spectrum for a system with p d.o.f. also requires the simultaneous time evolution of a set of 2p tangent vectors [42]. On the top of that, a computation of the exponents for an ensemble of trajectories is advisable for a non-ergodic dynamics

[4]. These considerations show how demanding the computation of the Lyapunov spectrum of the Solar System planets is. By contrast, a 5-Gyr integration of the forced ISS takes only a couple of hours for Gauss’s dynamics (H) and a few minutes at degree 4 (H4). This dynamical model thus provides a unique opportunity to compute all the FT-LCEs that are mainly related to the secular evolution of the inner orbits.

We compute the Lyapunov spectrum of the truncated forced ISS using the standard method of Benettin et al. [43], based on Gram-Schmidt orthogonalization. Manipulation of the truncated Hamiltonian H2n in TRIP allows us to systematically derive the equations of motion and the corresponding variational equations, which we integrate through an Adams PECE method of order 12 and a timestep of 250 years. Parallelization of the time evolution of the 16 tangent vectors, between two consecutive reorthonormalization steps of the Benettin et al. [43] algorithm, signiﬁcantly reduces the computation time. Figure 1a shows the positive FT-LCEs expressed as angular frequencies over the next 10 Gyr for the Hamiltonian truncated at degree 4. The FT-LCEs are computed for 150 stable solutions, with initial conditions very close to the nominal values of Gauss’s dynamics and random sets of initial tangent vectors [19, Appendix C]. The ﬁgure shows the [5th, 95th] percentile range of the marginal PDF of each exponent estimated from the ensemble of solutions. For large times, the exponents of each solution become independent of the initial tangent vectors, the renormalization time, and the norm chosen for the phase-space vectors (see Appendix A and Fig. 8a). In this asymptotic regime, the Benettin et al. [43] algorithm purely retrieves the FT-LCEs as deﬁned in Eq. (10), and the width of their distributions only reﬂects the out-of-

equilibrium dynamics of the system. The convergence of our numerical computation is also assessed by verifying the symmetry of the spectrum stated in Eq. (9) (see Appendix A and Fig. 8b).

The spectrum in Fig. 1a has distinctive features. A set of intermediate exponents follow the MLE, ranging from 0.1 to 0.01 yr−1, while the smallest ones fall below 0.01 yr−1. Figure 1a reveals the existence of a hierarchy of exponents and corresponding timescales that spans two orders of magnitude, down to a median value of λ−8 1 ≈ 500 Myr. The number of positive exponents conﬁrms that no integral of motion exists, as one may expect from the forcing of the outer planets. We also compute the spectrum for the Hamiltonian truncated at degree 6. As shown in Appendix A (Fig. 9), the asymptotic distributions of the exponents are very similar to those at degree 4. This result suggests that long-term diﬀusion of the phase-space density is very close in the two cases. The diﬀerent instability rates of the two truncated dynamics mainly relates to the geometry of the instability boundary, which is closer to the initial position of the system for H6 than for H4 [7].

The relevance of the Lyapunov spectrum in Fig. 1a emerges from the fact that the existence of an integral of motion implies a pair of vanishing exponents. This is a pivotal point: By a continuity argument, the presence of positive exponents much smaller than the leading one constitutes a compelling indication that there are dynamical quantities whose chaotic decoherence over initially very close trajectories takes place over timescales much longer than the Lyapunov time. In the long term, such quantities should diﬀuse much more slowly than any LL action variable. Therefore, Fig. 1a suggests that the secular orbits of the inner planets are characterized by a slowfast dynamics that is much more pronounced than the well-known timescale separation arising from the LL integrable approximation. The existence of slow quantities, which are a priori complicated functions of the phasespace variables, is crucial in the context of ﬁnite-time stability, as they can eﬀectively constrain the long-term diﬀusion of the phase-space density toward the unstable states. The next section addresses the emergence of these slow quantities from the symmetries of the Fourier harmonics that compose the Hamiltonian.

##### IV. QUASI-INTEGRALS OF MOTION

The emergence of a chaotic behavior of the planetary orbits can be explained in terms of the pendulum-like dynamics generated by each Fourier harmonic that composes the Hamiltonian in Eq. (6) [e.g. 44]. One can write

H2n(I,θ,t) = H02n,0(I) + Mi=12n Fi(I,θ,t), with Fi(I,θ,t) = Hk

i, i

2n (I)Ej(ki·θ+ i·φ(t)) + c.c., (11)

where (ki, i) = (0,0), M2n is the number of harmonics in H2n with a non-null wave vector, and c.c. stands

TABLE II. Top of ranking R1. First 30 resonant harmonics of H10 along the 5-Gyr nominal solution of Gauss’s dynamics, in order of decreasing time median of the resonance half-width ∆ω (arcsec yr−1). Adapted from Table 2 of Ref. [19].

i Fourier harmonic Fi Oi τires ∆ωi

- 1 g3 − g4 − s3 + s4 4 12% 0.33200..526093
- 2 g1 − g2 + s1 − s2 4 19% 0.30200..611154
- 3 g2 − g5 − 2s1 + 2s2 6 23% 0.10500..223041
- 4 2g3 − 2g4 − s3 + s4 6 70% 0.07600..159023
- 5 g1 − g5 − s1 + s2 4 10% 0.07400..178056
- 6 g2 − g4 + s2 − s4 4 6% 0.06600..098025
- 7 g1 − 2g2 + g4 + s1 − 2s2 + s4 8 5% 0.06100..074051
- 8 g1 − g3 + s2 − s3 4 17% 0.05600..090028
- 9 g1 + g3 − 2g4 + s2 − s3 6 5% 0.05300..061037
- 10 3g3 − 3g4 − s3 + s4 8 9% 0.05200..140007
- 11 g2 − g3 − s1 + 2s2 − s3 6 5% 0.03800..047028
- 12 g1 − 2g3 + g4 + s2 − s4 6 36% 0.03800..083016
- 13 2g1 − g3 − g5 + s2 − s4 6 5% 0.03700..043028
- 14 g4 − g5 − s2 + 2s3 − s4 6 2% 0.03300..036031
- 15 g1 − 2g3 + g4 + s1 + s3 − 2s4 8 25% 0.03300..045014
- 16 g1 − g4 + s1 − s4 4 23% 0.03200..054017
- 17 g1 − 2g2 + g5 + 3s1 − 3s2 10 6% 0.03200..039023
- 18 g1 − g4 + s2 − s3 4 18% 0.03100..073016
- 19 3g1 − g2 − g4 − g5 + s1 − s3 8 2% 0.03100..042023
- 20 2g1 − g2 − g3 + s1 − s3 6 29% 0.02800..051016
- 21 2g1 − g2 − g4 + s1 − s3 6 3% 0.02600..028021
- 22 3g3 − 3g4 − 2s3 + 2s4 10 8% 0.02500..055012
- 23 2g1 − g2 − 2g3 + g4 + s1 − s4 8 3% 0.02300..036012
- 24 2g3 − g4 − g5 − s1 + s4 6 16% 0.02300..048010
- 25 g1 − 3g3 + 2g4 + s2 − s4 8 7% 0.02100..030008
- 26 g1 − g2 − g3 + g4 + s1 − s2 6 6% 0.02100..032004
- 27 g1 + g3 − 2g4 + s1 − s4 6 3% 0.02100..022017
- 28 g1 + g2 − 2g5 − 3s1 + 3s2 10 4% 0.02000..028006
- 29 3g1 − g2 − g4 − g5 + s2 − s3 8 4% 0.02000..027008
- 30 2g1 − g4 − g5 + s2 − s4 6 7% 0.02000..029007


- a O is the order of the harmonic.
- b τres is the fraction of time the harmonic is resonant. Only harmonics with τres &gt; 1% are shown.
- c 5th and 95th percentiles of the time distribution of ∆ω as subscripts and superscripts, respectively.


for complex conjugate. Chaos arises from the interaction of resonant harmonics, that is, those harmonics Fi whose frequency combination ki · θ˙ + i · φ˙(t) vanishes at some point along the motion. Using the computer algebra system TRIP, the harmonics of H10 that enter into resonance along the 5-Gyr nominal solution of Gauss’s dynamics have been systematically retrieved, together with the corresponding time statistics of the resonance half-widths ∆ω [19]. The resonances have then been ordered by decreasing time median of their halfwidths. The resulting ranking of resonances is denoted as R1 from now on. Table II recalls the 30 strongest resonances that are active for more than 1% of the 5-Gyr time span of the orbital solution. The wave vector of each harmonic is identiﬁed by the corresponding combination of frequency labels (gi,si)8i=1, that is, k·ωi+ ·ωo, with ωi = (g1,g2,g3,g4,s1,s2,s3,s4). Table II also shows

the order of each harmonic, deﬁned as the even integer O = (k, ) 1. The support of the asymptotic ensemble distribution of the FT-MLE shown in Fig. 1a overlaps in a robust way with that of the time distribution of the half-width of the strongest resonances. In other words,

2πλ1 ≈ ∆ωR

, (12) where ∆ωR

1

stands for the half-width of the uppermost

1

- resonances of ranking R1. Equation (12) shows the dynamical sources of chaos in the ISS by connecting the top of the Lyapunov spectrum with the head of the resonance spectrum. Computer algebra allows us to establish such a connection in an unbiased way despite the multidimensional nature of the dynamics. We stress that such analysis is built on the idea that the time statistics of the resonant harmonics along a 5-Gyr ordinary orbital solution should be representative of their ensemble statistics (deﬁned by a set of stable solutions with very close initial conditions) at some large time of the order of billions of years. This assumption was inspired by the good level of stationarity that characterizes the ensemble distribution of the MLE beyond 1 Gyr [4, 19], and that extends to the entire spectrum in Fig. 1a.


We remark that, strictly speaking, ranking R1 is established on the Fourier harmonics of the Lie-transformed Hamiltonian H 2n [19, Appendix G]. New canonical variables are indeed deﬁned to transform H2n in a Birkhoﬀ normal form to degree 4. The goal is to let the interactions of the terms of degree 4 in H2n appear more explicitly in the amplitudes of the harmonics of higher degrees in H 2n, the physical motivation being that the non-linear interaction of the harmonics at degree 4 constitutes the primary source of chaos [19]. Keeping in mind the quasiidentity nature of the Lie transform, here we drop for simplicity the diﬀerence between the two Hamiltonians. Moreover, all the new analyses of this work involve the original variables of Eq. (5).

A. Quasi-symmetries of the resonant harmonics

In addition to the dynamical interactions responsible for the chaotic behavior of the orbits, Table II provides information on the geometry of the dynamics in the action variable space. Ranking the Fourier harmonics allows us to consider partial Hamiltonians constructed from a limited number m of leading terms [7, 19], that is,

H2n,m = H02n,0 + mi=1Fi. (13)

The dynamics of a Hamiltonian reduced to a small set of harmonics is generally characterized by several symmetries and corresponding integrals of motion. We are interested in how these symmetries are progressively destroyed when one increases the number of terms taken into account in Eq. (13).

Consider a set of m harmonics of H2n and a dynamical quantity that is a linear combination of the action

variables, that is,

Cγ = γ · I, (14)

γ ∈ R8 being a parameter vector. From Eq. (11), the partial contribution of the m harmonics to the time derivative of Cγ along the ﬂow of H2n is

m

C˙γ,m = 2

i=1

i, i

2n (I)Ej(ki·θ+ i·φ(t))}, (15)

γ · ki Im{ Hk

and C˙γ = C˙γ,M

, where M2n is the total number of harmonics with a non-null wave vector that appear in H2n. Any quantity Cγ with γ · ki = 0 is conserved by the one-d.o.f. dynamics generated by the single harmonic Fi. In other words, such a quantity would be an integral of motion if Fi were the only harmonic to appear in the Hamiltonian. Considering now m diﬀerent harmonics, these do not contribute to the change of the quantity Cγ if γ ⊥ span(k1,k2,...,km), that is, if the vector γ belongs to the orthogonal complement of the linear subspace of R8 spanned by the wave vectors (ki)mi=1. We also consider the quantity

2n

C γ = H2n + γ · I. (16)

Because of the explicit time dependence in the Hamiltonian, the partial contribution of a set of m harmonics to the time derivative of C γ along the ﬂow of H2n is

m

i, i

2n (I)Ej(ki·θ+ i·φ(t))}, (17)

(γ·ki+ i·ωo)Im{ Hk

C˙ γ,m = 2

i=1

and one has C˙ γ = C˙ γ,M

. Quantity C γ is unchanged by the m harmonics if γ·ki+ i·ωo = 0 for i ∈ {1,2,...,m}. Dynamical quantities Cγ or C γ that are unaﬀected by a given set of leading harmonics, that is, with null partial contribution in Eq. (15) or (17), are denoted as quasiintegrals of motion from now on. More speciﬁcally, we build our analysis on ranking R1, since the resonant harmonics are those responsible for changes that accumulate stochastically over long timescales, driving chaotic diﬀusion.

2n

In the framework of the aforementioned considerations, the resonances listed in Table II possess three diﬀerent symmetries.

a. First symmetry. The rotational invariance of

the entire Solar System implies the d’Alembert rule 8 i=1 ki + 7i=1 i = 0, where k = (k1,k2,...,k8) and

= ( 1, 2,..., 7) [21, 24, 45, 46]. Moreover, the Jupiterdominated eccentricity mode g5 is the only fundamental Fourier mode of the outer planet forcing to appear in Table II. The quantity

518 = H2n + g5 4i=1(Xi + Ψi), (18)

E2n := C g

with 18 = (1,1,...,1) ∈ R8, is therefore unaﬀected by the resonances listed in Table II. In an equivalent way, the

time-dependent canonical transformation θ → θ+g5t18, with unchanged action variables, allows us to remove the explicit time dependence in these harmonics. Quantity E2n coincides with the transformed Hamiltonian and the harmonics in Table II do not contribute to its time derivative.

b. Second symmetry. We write the eccentricity and inclination parts of the harmonic wave vectors explicitly, that is, k = (kecc,kinc) with kecc,kinc ∈ R4. One can visually check that the harmonics in Table II verify the relation 4i=1 kiinc = 0, where kinc = (k1inc,...,k4inc). Therefore, denoting γ1 = (04,14), the quantity

Cinc := Cγ

= Ψ1 + Ψ2 + Ψ3 + Ψ4 (19)

1

is conserved by these resonances. Cinc is the angular momentum deﬁcit (AMD) [47] contained in the inclination d.o.f. This symmetry can then be interpreted as a remnant of the conservation of the AMD of the entire (secular) Solar System. We remark that the AMD contained

in the eccentricity d.o.f., Cecc = 4i=1 Xi, is not invariant under the leading resonances because of the eccentricity

forcing mainly exerted by Jupiter through the mode g5. The conservation of Cinc depends on two facts: the inclination modes s6,s7,s8 of the external forcing do not appear in Table II; low-order harmonics like 2g1−s1−s2, 2g1 − 2s1, and 2g1 − 2s2 are never resonant (even if they can raise large quasi-periodic contributions), so that two AMD reservoirs Cecc and Cinc are decoupled in Table II. We recall that the absence of an inclination mode s5 in the external forcing relates to the ﬁxed direction of the angular momentum of the entire Solar System [2, 21, 46].

c. Third symmetry. The ﬁrst two symmetries could be expected to some extent on the basis of physical intuition of the interaction between outer and inner planets. However, it is not easy to even visually guess the third one from Table II. Consider the 30 × 8 matrix K30 whose rows are the wave vectors (ki)30i=1 of the listed resonances. A singular value decomposition shows that the rank of K30 is equal to 6. Therefore, the linear subspace V30 = span(k1,k2,...,k30) spanned by the wave vectors has dimension 6. A Gram–Schmidt orthogonalization allows us to determine two linearly independent vectors that span its orthogonal complement V30⊥. One choice consists in V30⊥ = span(γ2,γ2⊥), with

C2 := Cγ2

= −X3 − X4 + Ψ1 + Ψ2 + 2Ψ3 + 2Ψ4, C2⊥ := Cγ2⊥ = X3 + X4 + Ψ1 + Ψ2.

(20)

Since the second symmetry clearly requires that γ1 ∈ V30⊥, the three quantities Cinc,C2,C2⊥ are not independent and one has indeed Cinc = (C2 + C2⊥)/2. We remark that (C2 − C2⊥)/2 = −X3 − X4 + Ψ3 + Ψ4. The additional symmetry can thus be interpreted in terms of a certain decoupling between the d.o.f. 3,4 and 1,2, representing in the proper modes the Earth-Mars and Mercury-Venus subsystems, respectively.

The aforementioned symmetries, that exactly characterize the resonances listed in Table II, naturally repre-

sent quasi-symmetries when considering the entire spectrum of resonances R1. They are indeed broken at some point by weak resonances (see Sect. IVC). Quantities E2n, Cinc, and C2 are the corresponding QIs of motion. The persistence of the three symmetries under the 30 leading resonances is somewhat surprising. Concerning Cinc and C2, for example, one might reasonably expect that, since the ISS has 8 d.o.f., the subspace spanned by the wave vectors of just a dozen of harmonics should already have maximal dimension, destroying all possible symmetries.

We remark that, diﬀerently from Cinc and C2, the quantity E2n is a non-linear function of the action-angle variables. However, as far as stable orbital evolutions are concerned, the convergence of the series expansion of the Hamiltonian is suﬃciently fast that the linear LL approximation E2 = H2+g518·I = Cγ

, with γ3 = −ωLL+g518, reproduces reasonably well E2n along the ﬂow of H2n for n &gt; 1. The vector γ3 is used in Sect. V, together with γ1 and γ2, to deal with the geometry of the linear action subspace spanned by the QIs. The explicit expressions of these vectors are given in Appendix B. We mention that, diﬀerently from γ1 and γ2, the components of γ3 are not integer and they have the dimension of a frequency.

3

B. Slow variables

The QIs of motion E2n,Cinc,C2 are clearly strong candidates for slow variables once evaluated along the orbital solutions. In what follows, to assess the slowness of a dynamical quantity when compared to the typical variations of the action variables, we consider the variance of its time series along a numerical solution.

We deﬁne the dimensionless QIs

Cinc = Cinc

, C2 = C2

, E2n = E2n

, (21)

γ1 C0

γ2 C0

γ3 C0

where C0 stands for the current total AMD of the inner planets, that is, the value of Cecc + Cinc at time zero. We stress that, by introducing the unit vectors γi = γi/ γi

for i ∈ {1,2,3}, one has Cinc = C γ

/C0 and C2 = C γ

/C0. At degree 2, one also has E2 = C γ

1

2

/C0. We then consider the ensembles of numerical integrations of H4 and H6, with very close initial conditions and spanning 100 Gyr in the future, that have been presented in Ref. [7]. The top row of Fig. 2 shows the time evolution over 5 Gyr of the dimensionless QIs and of two components of the dimensionless action vector I = I/C0 along the nominal orbital solutions of the two ensembles. We subtract from each time series its mean over the plotted time span. The time series are low-pass ﬁltered by employing the Kolmogorov-Zurbenko (KZ) ﬁlter with three iterations of the moving average [4, 48]. A cutoﬀ frequency of 1 Myr−1 is chosen to highlight the long-term diﬀusion that can be hidden by short-time quasi-periodic oscillations. This is in line with our deﬁnition of quasi-integrals based

3

X1 Ψ3 Cinc C2 E

|| |
|---|
<br><br>H4<br><br>−0.02<br><br>0.00<br><br>0.02| |
|---|---|
| | |
| | |
| | |
| | |
| | |


| |H6<br><br>−0.02<br><br>| | | |
|---|---|---|
| | | |
<br><br>0.00<br><br>0.02|
|---|---|
| | |
| | |
| | |
| | |


0.6

0.4

0.2

0.0

−0.2

|| |
|---|
<br><br>H•4<br><br>−0.005<br><br>0.000<br><br>0.005| |
|---|---|
| | |
| | |
| | |
| | |


|0.00|H•6<br><br>5<br><br>0<br><br>5<br><br>|
|---|---|
|0.00| |
|−0.00| |
| | |
| | |
| | |


0.6

0.4

0.2

0.0

−0.2

0 1 2 3 4 5 Time (Gyr)

0 1 2 3 4 5 Time (Gyr)

- FIG. 2. Time evolution over 5 Gyr of the dimensionless QIs ( Cinc, C2, E) and of two representatives of the dimensionless action variables ( X1, Ψ3) along the nominal orbital solutions of diﬀerent models. Top row: H4 and H6 ( E stands for E4 and E6,


respectively). Bottom row: H•4 and H•6 from Eq. (24) ( E2•n is exactly conserved and not shown). The time series are low-pass ﬁltered with a cutoﬀ frequency of 1 Myr−1 and the mean over 5 Gyr is subtracted. The variations of the QIs are enlarged in

the insets. The H•2n models are introduced and discussed in Sec. IV D.

on contribution from resonant harmonics only. Figure 2 clearly shows that the QIs are slowly-diﬀusing variables when compared to an arbitrary function of the action variables. The behavior of the QIs along the nominal orbital solutions of Fig. 2 is conﬁrmed by a statistical analysis in Appendix C. Figure 10 shows the time evolution of the distributions of the same quantities as Fig. 2 over the stable orbital solutions of the entire ensembles of 1080 numerical integrations of Ref. [7]. Figure 11 details the growth of the QI dispersion over time.

We remark that C2 and E2n show very similar time evolutions along stable orbital solutions, as can be seen in the top row Fig. 2. This is explained by the interesting observation that the components of the unit vectors γ2 and γ3 diﬀer from each other by only a few percent, as shown in Appendix B. However, we stress that the two vectors are in fact linearly independent: C2 does not depend on the actions X1 and X2, while E2n does. The two QIs move away from each other when high eccentricities of Mercury are reached, that is, for large excursions of the Mercury-dominated action X1.

C. Weak resonances and Lyapunov spectrum

A fundamental result from Table II is that the symmetries introduced in Sect. IVA are still preserved by resonances that have half-widths an order of magnitude smaller than those of the strongest terms. It is natural to extract from ranking R1 the weak resonances that break the three symmetries. A new ranking of reso-

nances R2 is deﬁned in this way. Table III reports the 10 strongest symmetry-breaking resonances that change E2n,Cinc,C2, respectively. As in Table II, only harmonics that are resonant for more than 1% of the 5-Gyr time span of the nominal solution of Gauss’s dynamics are shown. The leading symmetry-breaking resonances have half-widths of about 0.01 yr−1. For each QI, the dominant contribution comes from harmonics involving Fourier modes of the outer planet forcing other than g5: the Saturn-dominated modes g6,s6 and the modes g7,s7 mainly associated to Uranus. In the case of Cinc, there is also a contribution that starts at about 0.006 yr−1 with F8 = 4g1 − g2 − g3 − s1 − 2s2 + s4 and comes from high-order internal resonances, that is, resonances that involve only the d.o.f. of the inner planets. We remark that the decrease of the resonance half-width with the index of the harmonic in Table III is steeper for Cinc than for E2n,C2, and is accompanied by a greater presence of high-order resonances. This may notably explain why the secular variations of Cinc are somewhat smaller in the top row of Fig. 2. We ﬁnally point out the important symmetry-breaking role of the modes g7,s7, representing the forcing mainly exerted by Uranus. Diﬀerently from what one might suppose, these modes cannot be completely neglected when addressing the long-term diffusion of ISS. This recalls the role of the modes s7 and s8 in the spin dynamics of Venus [49], and is basically a manifestation of the long-range nature of the gravitational interaction.

As we state in Sect. III, a pair of Lyapunov exponents would vanish if there were an exact integral of motion.

TABLE III. Top of ranking R2. First 10 symmetry-breaking resonances of H10 along the 5-Gyr nominal solution of Gauss’s dynamics, that change E2n, Cinc, and C2, respectively (see Table II for details).

i Fourier harmonic Fi Oi τires ∆ωi E2n

- 1 g1 + g2 − 2g5 + s2 − s7 6 1% 0.01800..020016
- 2 g1 − 2g2 + g6 − s2 + s6 6 4% 0.01700..024008
- 3 g3 − g6 + s2 − s4 4 10% 0.01700..022009
- 4 g5 − g7 + s3 − s4 4 5% 0.01700..024010
- 5 g4 − g6 + s2 − s4 4 4% 0.01600..021007
- 6 g2 − 2g4 + g6 4 12% 0.01600..027009
- 7 g1 − g3 − g5 + g6 − s1 + s4 6 6% 0.01500..024011
- 8 2g3 − 2g4 + g5 − g7 6 25% 0.01400..022006
- 9 g2 + g3 − 3g4 + g6 6 3% 0.01400..017010
- 10 g2 − 2g3 + g6 + s3 − s4 6 3% 0.01100..018003 Cinc


- 1 g1 + g2 − 2g5 + s2 − s7 6 1% 0.01800..020016
- 2 g1 − 2g2 + g6 − s2 + s6 6 4% 0.01700..024008
- 3 g2 − g6 + s1 − s6 4 8% 0.01100..017003
- 4 g4 − g6 − 2s3 + 3s4 − s6 8 5% 0.01000..012002
- 5 2g1 − 2g5 + s1 − s7 6 1% 0.00700..008005
- 6 4g1 − 3g2 − g5 − s2 + s7 10 7% 0.00600..015003
- 7 g3 − g6 − 2s3 + 3s4 − s6 8 2% 0.00600..011003
- 8 4g1 − g2 − g3 − s1 − 2s2 + s4 10 2% 0.00600..009001
- 9 2g1 − g2 − g5 + 3s1 − 2s2 − s7 10 3% 0.00600..008002
- 10 3g1 − 3g2 + s1 − 2s2 + s7 10 19% 0.00600..009002 C2


- 1 g1 + g2 − 2g5 + s2 − s7 6 1% 0.01800..020016
- 2 g1 − 2g2 + g6 − s2 + s6 6 4% 0.01700..024008
- 3 g3 − g6 + s2 − s4 4 10% 0.01700..022009
- 4 g4 − g6 + s2 − s4 4 4% 0.01600..021007
- 5 g2 − 2g4 + g6 4 12% 0.01600..027009
- 6 g1 − g3 − g5 + g6 − s1 + s4 6 6% 0.01500..024011
- 7 g2 + g3 − 3g4 + g6 6 3% 0.01400..017010
- 8 g2 − 2g3 + g6 + s3 − s4 6 3% 0.01100..018003
- 9 g1 − g3 − g4 + g6 + s1 − s2 6 4% 0.01100..013008
- 10 g2 − g6 + s1 − s6 4 8% 0.01100..017003


In the presence of a weakly broken symmetry, one may expect a small positive Lyapunov exponent whose value relates to the half-width of the strongest resonances driving the time variation of the corresponding QI. Such an argument is a natural extension of the correspondence between the FT-MLE and the top of the resonance spectrum given in Eq. (12). Comparison of Table III with the Lyapunov spectrum in Fig. 1a shows that the time statistics of the half-widths of the symmetry-breaking resonances of ranking R2 overlaps with the ensemble distribution of the three smallest FT-LCEs, that is, λ6,λ7,λ8. One can indeed write

2πλ6 ≈ ∆ωR

, (22)

2

where ∆ωR

stands for the half-width of the uppermost

2

- resonances of ranking R2. Table III and Fig. 1a suggest a relation between the QIs and the smallest Lyapunov


TABLE IV. Top of ranking R3. First 10 symmetry-breaking resonances of H10 along the 5-Gyr nominal solution of Gauss’s dynamics, that only involve g5 among the external modes and change E2n, Cinc, and C2, respectively.

i Fourier harmonic Fi Oi τires ∆ωi

E2n No resonances Cinca

- 1 4g1 − g2 − g3 − s1 − 2s2 + s4 10 2.0% 0.00600..009001
- 2 2g1 + g2 − g4 − 2s1 − s2 + s3 8 2.5% 0.00300..008002
- 3 3g1 − g2 − s1 − 3s2 + s3 + s4 10 1.5% 0.00300..005001
- 4 2g1 − g4 + g5 − s1 − 2s2 + s4 8 1.3% 0.00300..006001
- 5 4g1 − g2 − g4 − s1 − 2s2 + s4 10 1.4% 0.00300..004001
- 6 4g1 − g2 − g4 − 3s2 + s3 10 1.3% 0.00300..005001
- 7 3g1 − g4 − 2s1 − s2 + s4 8 1.8% 0.00300..004001
- 8 3g1 − g3 − 2s1 − s2 + s4 8 1.6% 0.00200..006000
- 9 2g1 − g3 + g5 − s1 − 2s2 + s4 8 1.0% 0.00200..004000
- 10 g1 + g2 − g3 + g5 − 2s1 − s2 + s3 8 1.3% 0.00200..003001 C2


- 1 g1 − 3g2 + 2g5 − s1 + 2s2 − s4 10 0.01 1e−41e1e−−44
- 2 2g1 − 4g2 + 2g5 + s2 − s4 10 0.08 8e−52e1e−−54
- 3 3g2 − 3g5 + s1 − 2s2 + s3 10 0.01 3e−53e3e−−55
- 4 g1 − 4g2 + g3 + 2g5 − s1 + s2 10 0.13 3e−52e5e−−65
- 5 g1 + 3g2 − 4g5 − s2 + s4 10 0.56 3e−52e4e−−55
- 6 g1 − 4g2 + 3g5 + s2 − s4 10 0.01 2e−52e2e−−55
- 7 3g2 − 3g5 + s1 − 2s2 + s4 10 0.13 1e−53e7e−−56
- 8 4g2 − g3 − g4 − 2g5 + s1 − s3 10 0.03 1e−51e9e−−56
- 9 2g1 − 5g2 + g4 + 2g5 10 0.02 9e−69e9e−−66
- 10 2g1 − 5g2 + g3 + 2g5 10 0.14 6e−68e3e−−66


a Only harmonics that are resonant for more than one percent of time are shown, i.e., τres &gt; 1%.

exponents:

λ6,λ7,λ8 ←→ E2n,Cinc,C2. (23)

Equation (23) is not a one-to-one correspondence, nor should it be understood as an exact relation since, for example, λ6 is not well separated from the larger exponents. Its physical meaning is that the QIs are among the slowest d.o.f. of the ISS dynamics. Such a claim is one of the core points of this work. In Sect. V, we show its statistical validity in the geometric framework established by a principal component analysis of the orbital solutions. Moreover, Sect. IVD shows that Eq. (23) can be stated more precisely in the case of a simpliﬁed dynamics that underlies H2n. We remark that E2n,Cinc,C2 constitute a set of three QIs that are independent and nearly in involution, and it is thus meaningful to associate three diﬀerent Lyapunov exponents with them. On the one hand, the independence is easily checked at degree 2 as the vectors γ1,γ2,γ3 are linearly independent. On the other hand, one has the Poisson bracket {Cinc,C2} = 0, since the two quantities are functions of the action variables only. One also has {E2n,Cinc} = {H2n,Cinc} = C˙inc and {E2n,C2} = C˙2. Only weak resonances contribute to

these Poisson brackets and the three QIs are therefore nearly in involution.

D. New truncation of the Hamiltonian

The fundamental role of the external modes g6,g7,s6,s7 in Table III raises the question of which symmetry-breaking resonances persist if one excludes all the Fourier harmonics that involve external modes other than g5. Therefore, we deﬁne a new ranking R3 by extracting such resonances from ranking R2. Table IV reports the 10 strongest resonances per each broken symmetry. The diﬀerence with respect to Table III is manifest. As g5 is the only external mode remaining, there are no resonances left that can contribute to the time evolution of E2n. For the remaining two QIs, the only harmonics that appear in Table IV are of order 8 or higher, and this is accompanied by a signiﬁcant drop in the half-width of the leading resonances. In the case of Cinc, the half-width of the uppermost resonances is now around 0.005 yr−1. One can appreciate that the activation times τres of the resonances do not exceed a few percent, diﬀerently from Table III. The most impressive change is, however, related to C2: only harmonics of order 10 appear in Table IV and the half-width of the uppermost resonances drops by two orders of magnitude. We stress that such harmonics are resonant for very short periods of time along the 5 Gyr spanned by the nominal solution of Gauss’s dynamics. To retrieve the time statistics of the resonances aﬀecting C2, we indeed choose to repeat the computations of Ref. [19] by increasing the cutoﬀ frequency of the low-pass ﬁlter applied to time series of the action-angle variables from (5 Myr)−1 to 1 Myr−1 [19, Appendices F.2 and G.5]. The ﬁltered time series have then been resampled with a timestep of 50 kyr. Many harmonics we show in Table IV and related to C2 are resonant for a few timesteps and their time statistics is very tentative. More precise estimations of the half-widths should be obtained over an ensemble of diﬀerent orbital solutions, possibly spanning more than 5 Gyr. In any case, the fundamental point here is the drastic reduction in the size of the uppermost resonances with respect to Table III, and this is a robust result. We remark that resonances of order 12 and higher may also carry an important contribution at these scales, but they are excluded by the truncation at degree 10 adopted in Ref. [19] to establish the resonant harmonics, so they do not appear in the tables of this work.

Hamiltonian H•2n. The implications of Table IV suggest to introduce an additional truncation in the Hamiltonian H2n. This consists in dropping the harmonics of Eq. (6) that involve external modes other than g5:

H•2n(I,θ,t) =

k, 1

•

Hk,

2n (I)Ej(k·θ+

1φ1(t)), (24)

where φ1(t) = −g5t and • = ( 1,0,...,0), with 1 ∈ Z. Consistently with the absence of symmetry-breaking

resonances related to E2n in Table IV, the corresponding dynamics admits the exact integral of motion

E2•n = H•2n + g5 4i=1(Xi + Ψi), (25)

which represents the transformed Hamiltonian under the canonical change of variables that eliminates the explicit time dependence in Eq. (24). We point out that, as the additional truncation is applied to the action-angle formulation of Eq. (6), the external modes other than g5 still enter the deﬁnition of the proper modes of the forced Laplace-Lagrange dynamics [4]. The orbital solution arising from H•2n is initially very close to that of H2n. A frequency analysis over the ﬁrst 20 Myr shows that the differences in the fundamental frequencies of the motion between H•2n and H2n are of the order of 10−3 arcsec yr−1, an order of magnitude smaller than the typical frequency diﬀerences between H4 and H6 [4, Table 3]. Therefore, even though H•2n constitutes a simpliﬁcation of H2n, it should not be regarded as a toy model. Its dynamics, in particular, still possesses 8 d.o.f.

We compute the Lyapunov spectrum of the Hamiltonian H•4 in the same way as described in Sect. III in the case of H2n. Since its dynamics turns out to be much more stable than that of H4 (see Sect. VI, Fig. 7), we extend the computation to a time span of 100 Gyr. The marginal ensemble PDFs of the positive FT-LCEs are shown in Fig 1b. Comparing to the Lyapunov spectrum of H4, one notices that the distributions of the leading exponents turn out to be quite similar, apart from being more spaced and except for a slight decrease in their median values. However, such a decrease is more pronounced for smaller exponents, and the drop in the smallest exponents is drastic. The smallest one, λ8, decreases monotonically, consistently with the fact that E4• from Eq. (25) is an exact integral of motion. The exponent λ7 drops by more than an order of magnitude, and apparently begins to stabilize around a few 10−4 arcsec yr−1, while λ6 also reduces signiﬁcantly, by a factor of three, to about 0.005 yr−1. The drop in the smallest exponents agrees remarkably well with that of the half-width of the leading symmetry-breaking resonances when switching from Table III to Table IV. One can indeed write

- 2πλ6 ≈ ∆ωR

3,Cinc,

- 2πλ7 ≈ ∆ωR


3,C2, λ8 = 0,

(26)

where ∆ωR

3,Q stands for the half-width of the uppermost resonances of ranking R3 related to the quasi-integral Q. The hierarchy of the three smallest exponents in the spectrum of Fig. 1b consistently follows that of the QIs suggested in Table IV by the very diﬀerent sizes of the leading resonances. In other words, one can state:

- λ6 ←→ Cinc,
- λ7 ←→ C2,
- λ8 ←→ E2•n.


(27)

These one-to-one correspondences are a particular case of Eq. (23) and support the physical intuition behind it. In Sect. V, we prove the validity of Eq. (27) in the geometric framework established by a principal component analysis of the orbital solutions of H•2n.

Numerical integrations. We compute ensembles of 1080 orbital solutions of the dynamical models H•4 and H•6, with initial conditions very close to the nominal ones of Gauss’s dynamics and spanning 100 Gyr in the future. This closely follows what we did in Ref. [7] in the case of the models H2n. The bottom row of Fig. 2 shows the ﬁltered dimensionless QIs along the nominal solutions of the two models over the ﬁrst 5 Gyr. The hierarchy of the QIs stated in Eq. (27) is manifest. The quantity C2 has secular variations much slower than Cinc, while the latter is itself slower with respect to its counterpart in the orbital solutions of H2n. We remark that, as E2•n is an exact integral of motion for the model H•2n, we do not plot it. From Fig. 2 it is also evident how diﬃcult can be the retrieval of the short-lasting resonances aﬀecting C2 from a solution of H•2n spanning only a few billion years.

The hierarchy of the QIs is conﬁrmed by a statistical analysis in Appendix C. Figure 10 shows the entire time evolution of the distributions of the ﬁltered dimensionless QIs over the stable orbital solutions of the ensembles of 1080 numerical integrations. Figure 11 details the growth of the QI dispersion over time. As suggested by Table IV, the drop in the diﬀusion rates of the QIs when switching from H2n to H•2n is manifest.

##### V. STATISTICAL DETECTION OF SLOW VARIABLES

Section IV shows how the slow-fast nature of the ISS dynamics, indicated by the Lyapunov spectrum, emerges from the quasi-symmetries of the resonant harmonics of the Hamiltonian. QIs of motion can be introduced semianalytically and they constitute slow quantities when evaluated along stable orbital solutions. In this section, we consider the slow variables that can be systematically retrieved from a numerically integrated orbital solution by means of a statistical technique, the principal component analysis. We show that, in the case of the forced secular ISS, the slowest variables are remarkably close to the QIs, and this can be established in a precise geometric framework.

A. Principal component analysis

PCA is a widely used classical technique for multivariate analysis [50, 51]. For a given dataset, PCA aims to ﬁnd an orthogonal linear transformation of the variables such that the new coordinates oﬀer a more condensed and representative view of the data. The new variables are called principal components (PCs). They are uncorrelated and ordered according to decreasing variance:

the ﬁrst PC and last one have, respectively, the largest and the smallest variance of any linear combination of the original variables. While one is typically interested in the PCs of largest variance, in this work we employ the variance of the time series of a dynamical quantity to assess its slowness when compared to the typical variations of the action variables (see Sect. IVB). We thus perform a PCA of the action variables I and focus on the last PCs, as they give a pertinent statistical deﬁnition of slow variables. We stress that, when coupled to a lowpass ﬁltering of the time series, the statistical variance provides a measure of chaotic diﬀusion.

Implementation. Our procedure for the PCA is described brieﬂy as follows [for general details see, e.g., 52, 53]. Let I(t) = (X(t),Ψ(t)) be the 8-dimensional time series of the action variables evaluated along a numerical solution of the equations of motion. As in Sect. IVB, we apply the KZ low-pass ﬁlter with three iterations of the moving average and a cutoﬀ frequency of 1 Myr−1 to obtain the ﬁltered time series Iˆ(t) [4, 48]. In this way, the short-term quasi-periodic oscillations are mostly suppressed, which better reveals the chaotic diﬀusion over longer timescales. We ﬁnally deﬁne the meansubtracted ﬁltered action variables over the time interval [t0,t0 + T] as I˜(t) = Iˆ(t) − n−1 ni=0−1 Iˆ(t0 + i∆t), where the mean is estimated by discretization of the time series with a sampling step ∆t such that T = (n − 1)∆t. The discretized time series over the given interval is stored in an 8 × n matrix:

D = [I˜(t0), I˜(t0 + ∆t), ..., I˜(t0 + (n − 1)∆t)]. (28)

The PCA of the data matrix D consists in a linear transformation P = ATD, where A is an 8 × 8 orthogonal matrix (i.e. A−1 = AT) deﬁned as follows. By writing A = [a1,...,a8], the column vectors ai ∈ R8 are chosen to be the normalized eigenvectors of the sample covariance matrix, in order of decreasing eigenvalues: (n − 1)−1DDT = AΣAT, where Σ = diag(σ1,...,σ8) and σ1 ≥ ··· ≥ σ8. The PCs are deﬁned as the new variables after the transformation, that is, PCi = ai · I with i ∈ {1,...,8}. The uncorrelatedness and the ordering of the PCs can be easily seen from the diagonal form of their sample covariance matrix, (n − 1)−1PPT = Σ, from which it follows that the variance of PCi is σi.

Among all the linear combinations in the action variables I, the last PC, i.e., PC8, has the smallest variance over the time interval [t0,t0 + T] of a given orbital solution. The second last PC, i.e., PC7, has the second smallest variance and is uncorrelated with PC8, and so on. It follows that the linear subspace spanned by the last k PCs is the k-dimensional subspace of minimum variance: the variance of the sample projection onto this subspace is the minimum among all the subspaces of the same dimension. These properties indicate that the last PCs provide a pertinent statistical deﬁnition of slow variables along numerically integrated solutions of a dynamical system. The linear structure of the PCA, in particular, seems adapted to quasi-integrable systems close

to a quadratic Hamiltonian, like the ISS. In such a case, one may reasonably expect that the slow variables are, to a ﬁrst approximation, linear combinations of the action variables. We remark that the mutual orthogonality allows us to associate a linear d.o.f. to each PC.

Aggregated sample. Instead of considering a speciﬁc solution, it is also possible to take the same time interval from m diﬀerent solutions, and stack them together to form an aggregated sample: Dagg = [D1,D2,...,Dm], where Di is the data matrix of Eq. (28) for the ith solution. Since this work deals with a non-stationary dynamics, as the ISS ceaselessly diﬀuses in the phase space [7], we always consider the same time interval for each of the m solutions. The aggregated sample is useful in capturing globally the behavior of the dynamics, because it averages out temporary and rare episodes arising along speciﬁc solutions.

B. Principal components and quasi-integrals

Both the QIs and the last PCs represent slow variables, but are established through two diﬀerent methods. Equations (23) and (27) claim that the QIs found semianalytically in Sect. IV are among the slowest d.o.f. of the ISS dynamics. This naturally suggests to compare the three QIs with the three last PCs retrieved from numerically integrated orbital solutions. In this part, we ﬁrst introduce the procedure that we implement to establish a consistent and systematic correspondence between QIs and PCs. We then present both a visual and a quantitative geometric comparison between them.

1. Tweaking the QIs

The three last components PC8, PC7, PC6 are represented by the set of vectors SPCs = {a8,a7,a6} belonging to R8. By construction, these PCs have a linear, hierarchical, and orthogonal structure. In other words: the PCs are linear combinations of the action variables I; denoting by the order of statistical variance, one has PC8 PC7 PC6; the unit vectors (ai)8i=6 are orthogonal to each other. On the other hand, the QIs of motion Cinc,C2,E2n do not possess these properties. Therefore, we adjust them in such a way to reproduce the same structure.

a. Linearity. While Cinc and C2 are linear functions of the action variables, E2n is not when n &gt; 1. Nevertheless, as we explain in Sect. IVA, as far as one considers stable orbital solutions, the linear LL approximation E2 = γ3·I reproduces E2n reasonably well. Therefore, we consider the three linear QIs of motion Cinc,C2,E2, which are respectively represented by the set of R8-vectors SQIs = {γ1,γ2,γ3}. In this way, the 3-dimensional linear subspaces of the action space spanned by the sets SQIs and SPCs can be compared.

b. Ordering. We deﬁne a set of QIs that are ordered by statistical variance, as it is the case for the PCs. We follow two diﬀerent approaches according to model H•2n in Eq. (24) or H2n in Eq. (6) (clearly n &gt; 1).

H•2n: A strong hierarchy of statistical variances among the QIs emerges from the size of the leading symmetry-breaking resonances in Table IV and from the orbital solutions in Figs. 2, 10, and 11. One has E2•n ≺ C2 ≺ Cinc. While E2•n is an exact non-linear integral of motion, we expect that its linear truncation E2• = E2 varies more than C2 and Cinc. Therefore, we consider the ordered set of QIs of motion {C2,Cinc,E2} represented by the ordered set of vectors S QIs = {γ2,γ1,γ3}.

H2n: Since the leading resonances aﬀecting the QIs in Table III have comparable sizes, there is no clear order of statistical variances that can be inferred. We then implement a systematic approach that orders the QIs by simply inheriting the ordering of the PCs. More precisely, we deﬁne a set of ordered vectors S QIs through the projections of the three last PCs onto the linear subspace generated by the QIs: S QIs = {projS

(a6)}[54]. As a result, the new set of QIs mirrors the hierarchical structure of the PCs. We stress that S QI spans the same subspace of R8 as SQI, since the ordered QIs are just linear combinations of the original ones.

(a7),projS

(a8),projS

QIs

QIs

QIs

c. Orthogonality. We apply the Gram-Schmidt process to the ordered set S QIs to obtain the orthonormal basis S QIs = {α1,α2,α3}. The set S QIs clearly spans the same subspace as SQIs. Moreover, the Gram-Schmidt process preserves the hierarchical structure, that is, the two m-dimensional subspaces spanned by the ﬁrst m ≤ 3 vectors of S QIs and S QIs, respectively, are identical.

In the end, we obtain a linear, ordered, and orthogonal set of modiﬁed QIs of motion {QI1,QI2,QI3}, where QIi = αi · I.

2. Visual comparison

We now visually compare the vectors α1,2,3 of the modiﬁed QIs with the corresponding vectors a8,7,6 of the last three PCs. We use the ensembles of 1080 numerically in-

tegrated orbital solutions of the models H4 and H4 considered in Sects. IVB and IVD, respectively. The nominal solution of each set is denoted as sol. #1 from now on. For the model H4, we also consider two other solutions: sol. #2 that represents a typical evolution among the 1080 solutions, and sol. #3 representing a rarer one. The particular choice of these two solutions is detailed in Sect. VB3.

Hamiltonian H•4. The modiﬁed QIs can be explicitly derived in this case and comprise interpretable physical

H•4, [0, 500] Myr

H•4, [1000, 2000] Myr sol. #1

H•4, [0, 5000] Myr

- 1


QI1 PC8

0

−1

1 QI2 PC7

0

−1

1 QI3 PC6

0

−1

1080 sols.

1 QI1 PC8

0

−1

1 QI2 PC7

0

−1

1 QI3 PC6

0

−1

X1 X2 X3 X4 Ψ1 Ψ2 Ψ3 Ψ4

X1 X2 X3 X4 Ψ1 Ψ2 Ψ3 Ψ4 X1 X2 X3 X4 Ψ1 Ψ2 Ψ3 Ψ4

FIG. 3. Vectors α1,2,3 representing the three modiﬁed QIs (QI1,2,3, black circles) compared to the corresponding vectors a8,7,6 of the three last PCs (PC8,7,6, red dots), for the intervals [0, 500] Myr (left-hand column), [1000, 2000] Myr (middle column) and [0, 5000] Myr (right-hand column) of sol. #1 and of the aggregated sample of 1080 solutions of model H•4. Here, QI1 is proportional to C2 and QI2 is proportional to C2⊥; see Eq. (20).

quantities. One has QI1 proportional to C2 and QI2 proportional to C2⊥. Moreover, QI3 is the component of E2 that is orthogonal to both C2 and C2⊥. Figure 3 shows the comparison between the modiﬁed QIs and the corresponding PCs for three diﬀerent time intervals along

- sol. #1 of H•4 (see Fig. 2 bottom left for its time evolution). The agreement of the pairs (QI1,PC8), (QI2,PC7),


and (QI3,PC6) across diﬀerent intervals is manifest and even impressive. One can appreciate that the “slower” the PC, the more similar it is to its corresponding QI. The overlap between the modiﬁed QIs and the three last PCs means that the QIs of motion span the slowest 3dimensional linear subspace of the action space. Therefore, to a linear approximation, they represent the three slowest d.o.f. of the H•4 dynamics. The quasi-integral C2 represents the slowest linear d.o.f.: it coincides with the last principal component PC8, which has the smallest variance among all the linear combinations of the action variables. Cinc and E2 represent the second and the third slowest linear d.o.f., respectively: the component of Cinc orthogonal to C2, i.e., C2⊥, matches the second last principal component PC7; the component of E2 orthogonal to the subspace generated by (C2, Cinc) matches the third

H4, [0, 500] Myr

H4, [1000, 2000] Myr sol. #1

H4, [0, 5000] Myr

1

QI1 PC8

0

−1

1 QI2 PC7

0

−1

1 QI3 PC6

0

−1

sol. #2

1 QI1 PC8

0

−1

1 QI2 PC7

0

−1

1 QI3 PC6

0

−1

sol. #3

1 QI1 PC8

0

−1

1 QI2 PC7

0

−1

1 QI3 PC6

0

−1

1080 sols.

1 QI1 PC8

0

−1

1 QI2 PC7

0

−1

1 QI3 PC6

0

−1

X1 X2 X3 X4 Ψ1 Ψ2 Ψ3 Ψ4

X1 X2 X3 X4 Ψ1 Ψ2 Ψ3 Ψ4 X1 X2 X3 X4 Ψ1 Ψ2 Ψ3 Ψ4

FIG. 4. Vectors α1,2,3 representing the three modiﬁed QIs (QI1,2,3, black circles) compared to the corresponding vectors a8,7,6 of the three last PCs (PC8,7,6, red dots), for the intervals [0, 500] Myr (left-hand column), [1000, 2000] Myr (middle column) and [0, 5000] Myr (right-hand column) of sol. #1, sol. #2, and sol. #3 and of the aggregated sample of 1080 solutions of model H4.

last principal component PC6. The strong hierarchical structure of the slow variables for the simpliﬁed dynam-

ics H•4 is clearly conﬁrmed by the almost frozen basis vectors of the PCs.

Hamiltonian H4. In this case, the QIs of motion Cinc,C2,E2 do not show a clear hierarchical structure in terms of statistical variance. Therefore, we consider the whole subspace spanned by the three QIs with respect to that spanned by the three last PCs. Since it is not easy to visually compare two 3-dimensional subspaces of R8, we compare their basis vectors instead. The basis α1,2,3 of modiﬁed quasi-integrals QI1,2,3 is computed according to the algorithm presented in Sect. VB1.

Figure 4 presents the comparison between the modiﬁed QIs and the corresponding PCs across three diﬀerent time intervals of three solutions of H4 (see Fig. 5 for their time evolution). The ﬁrst two, sols. #1 and #2, show thorough agreement between the pairs of QIs and PCs across all intervals, which indicates close proximity between the two subspaces VQIs = span(SQIs) and VPCs = span(SPCs). One can appreciate that the directions of the basis vectors are quite stable. The last component PC8, in particular, remains close to Cinc. The slowest linear d.o.f. of H4 can thus be deduced to be close to Cinc, in line with the discussion in Sect. IVC. Such a result shows how interesting physical insight can be gained through the PCA. Some changes in the basis vectors can arise, however, as for the ﬁrst time interval of

- sol. #2. This may be expected from a dynamical point


of view. Diﬀerently from H•4, there is no pronounced separation between the slowest d.o.f. at the bottom of the Lyapunov spectrum in Fig. 1a: the marginal distributions of consecutive exponents can indeed touch or overlap each other. Therefore, the hierarchy of slow variables is not as frozen as in H•4 and it can change along a given orbital solution.

Solutions #1 and #2 represent typical orbital evolutions. If the same time intervals of all the 1080 solutions are stacked together to form an aggregated sample on which the PCA is applied, the features mentioned above persist: the agreement between QIs and PCs, the stability of the basis vectors, and the similarity between PC8 and Cinc (see Fig. 4). Once again, the PCA conﬁrms that the subspace spanned by the three QIs is overall close to the slowest 3-dimensional linear subspace of the action space. Therefore, to a linear approximation, they represent the three slowest d.o.f. of the H4 dynamics. We remark that the slowness of the 3-dimensional subspace spanned by the QIs is a much stronger constraint than the observation that each QI is a slow variable. To give an example, let Q = q · I be a slow variable with unit vector q. If is an arbitrary small vector, i.e. 1, then Q = ( q + ) · I can also be considered as a slow variable, whereas the normalized diﬀerence of two quantities, ·I, is generally not. Therefore, the linear subspace spanned by Q and Q , that is, by q and , is not a slow

- 2-dimensional subspace. Solution #3 in Fig. 4 represents an edge case (see Fig. 5


X1 Ψ3 Cinc C2 E

0.6

sol. #1

0.4

0.2

0.0

−0.2

0.6

sol. #2

0.4

0.2

0.0

−0.2

0.6

sol. #3

0.4

0.2

0.0

−0.2

0 1 2 3 4 5

Time (Gyr)

FIG. 5. Time evolution over 5 Gyr of the dimensionless QIs of motions ( Cinc, C2, E) and of two representatives of the dimensionless action variables ( X1, Ψ3) for three solutions of H4, that is, sol. #1 (top), sol. #2 (middle), and sol. #3 (bottom). E stands for E4. The time series are low-pass ﬁltered with a cutoﬀ frequency of 1 Myr−1 and the mean over 5 Gyr is subtracted.

for its time evolution). Typically, the variances of the QIs are at least one order of magnitude smaller than those of the action variables, which allows a clear separation. Nevertheless, the distinction between the QIs and faster d.o.f. can be more diﬃcult in two rare possibilities. Firstly, if the change in a QI accumulates continually in one direction, its variance can inﬂate over a long time interval. This is the case for the interval [0, 5] Gyr of sol. #3. Secondly, the variance of a variable that is typically fast can suddenly dwindle during a certain period of time, for example, Ψ3 over the interval [1, 2] Gyr of sol. #3. In both cases, the slow subspace deﬁned by the three last PCs can move away from the QI subspace due to the contamination by d.o.f. that are typically faster.

This is reﬂected in the mismatch of QI3 and PC6 on the last two time intervals of sol. #3 in Fig. 4. We remark

that PC8,7 are still relatively close to QI1,2, which indicates that the slowest 2-dimensional subspace spanned

by PC8,7 still resides inside the QI subspace. It should be stressed that this disagreement between QIs and PCs does not mean that the QIs are not slow variables in this case. The mismatch has a clear dynamical origin instead. The resonance tables of this work have been retrieved from a single, very long orbital solution, with the idea that its time statistics is representative of the ensemble statistics over a set of initially very close solutions [19]. Therefore, the QIs derived from these tables characterize the dynamics in a global sense. The network of resonances can temporarily change in an appreciable way along speciﬁc solution, or be very particular along rare orbital solutions. In these cases, a mismatch between the last PCs and the present QIs may naturally arise. Moreover, the contamination of the QIs by d.o.f. that are typically faster may also be expected from the previously mentioned lack of a strong hierarchical structure of the slow variables. The Lyapunov spectrum in Fig. 1a shows that the marginal distributions of the exponents λ5 and λ6, for example, are not separate but overlap each other.

3. Distance between the subspaces of PCs and QIs

The closeness of the two 3-dimensional linear subspaces VPCs,VQIs ⊂ R8 spanned by the sets of vectors SPCs and SQIs, respectively, can be quantitatively measured in terms of a geometric distance. This can be formulated using the principal (canonical) angles [55–57].

Let A and B be two sets of m ≤ n independent vec-

tors in Rn. The principal vectors (pk,qk)mk=1 are deﬁned recursively as solutions to the optimization problem:

maximize p · q

p ∈ span(A), q ∈ span(B), subject to p = 1, q = 1,

p · pi = 0, q · qi = 0, i = 1,...,k − 1,

(29) for k = 1,...,m. The principal angles 0 ≤ θ1 ≤ ··· ≤ θm ≤ π/2 between the two subspaces span(A) and span(B) are then deﬁned by

cosθk = pk · qk, k = 1,...,m. (30)

The principal angle θ1 is the smallest angle between all pairs of unit vectors in span(A) and span(B); the principal angle θ2 is the smallest angle between all pairs of unit vectors that are orthogonal to the ﬁrst pair; and so on. Given the matrices deﬁning the two subspaces, the principal angles can be computed from the singular value decomposition of their correlation matrix. The result is the canonical correlation matrix diag(cosθ1,...,cosθm). This cosine-based method is often ill-conditioned for

Random (PC8,7,6, QI1,2,3)

18

|H•4<br><br>sols.|
|---|


sol. #1 1080

16

14

12

10

8

6

4

2

0

18

|sol. #1|10|80|sol. #2 sol. #3 0 sols.|H4|
|---|---|---|---|---|


16

14

12

10

8

6

4

2

0

0.0 0.2 0.4 0.6 0.8 1.0 Subspace distance

FIG. 6. PDF of the distance between two random 3dimensional linear subspaces of R8 (blue, 105 draws) compared with the PDF of the distance between the two subspaces VPCs (PC8,7,6) and VQIs (QI1,2,3) arising from the time interval [0, 5] Gyr of 1080 solutions of H•4 (top) and 10 800 solutions of H4 (bottom) (green). For each model, the subspace distance from the same time interval of representative solutions (vertical red lines) and of the aggregated sample of all the solutions (vertical dark green line) are indicated. The subspace distance is given by Eq. (31).

small angles. In such case, a sine-based algorithm can be employed [58]. In this work, we use the combined technique detailed in Ref. [59].

Once the principal angles have been introduced, different metrics can be deﬁned to measure the distance between two subspaces. In this work, we choose the normalized chordal distance [57]:

d(A,B) =

m

1 m

sin2 θk

k=1

1/2

. (31)

The distance is null if A and B are the same subspace and equal to 1 when they are orthogonal. We use this metric to show that the subspace closeness suggested by Figs. 3 and 4 is indeed statistically signiﬁcantly. More precisely, we provide evidence against the null hypothesis that the distribution of distances between VPCs and VPCs, arising from the H•4 and H4 dynamics, coincides with that of randomly drawn 3-dimensional subspaces of R8. The PDF of the distance between two random 3-dimensional

subspaces of R8 is shown in Fig. 6 in blue (such random subspaces can be easily generated by sampling sets of

- 3 vectors uniformly on the unit 7-sphere [60]). While the range of possible distances is [0,1], the distribution concentrates on the right-hand side of the interval, with a probability of approximately 99.3% that the distance is larger than 0.6. In this regard, we remark that the notion of distance in high-dimensional spaces is very diﬀerent from our intuition in a 3-dimensional world. If we draw randomly two vectors in a very high-dimensional space, it is extremely likely that they will be close to mutual orthogonality.


The upper panel of Fig. 6 shows in green the PDF of the distance between VPCs and VQIs arising from the time interval [0, 5] Gyr of the 1080 orbital solutions of model

H•4. In the lower panel, we consider a larger ensemble of 10800 solutions of model H4 spanning the same time interval [7], and plot the corresponding PDF of the distance between VPCs and VQIs. In both cases, the distance stemming from the aggregated sample of all the solutions is indicated by a vertical dark green line. We also report the distances from the speciﬁc solutions considered in Figs. 3 and 4 as vertical red lines. As the PDFs of both models peak at small distances, there results a strong evidence that the distribution of distances between the subspaces spanned by the PCs and the QIs is not that of random subspaces. In this sense, the closeness of the subspaces VPCs and VQIs is a statistically robust result. In the case of the simpliﬁed dynamics H•4, the PDF peaks around a median of roughly 0.08 and has small variance. Switching to model H4, the median increases to about 0.26 and the PDF is more spread out, with a long tail toward larger distances. The diﬀerences between the PDFs of the two models follow quite naturally the discussion in Sect. VB2: a quasi frozen hierarchy of the slowest variables for H•4; a larger variance for H4 related to contamination by d.o.f. that are typically faster and to variations of the resonant network with respect to the nominal solution of Gauss’s dynamics which is used to infer the QIs. Solution #3 in Fig. 4 represents in this sense an edge case of the distance distribution, while sol. #2 is a typical solution close to the PDF median.

##### VI. IMPLICATIONS ON LONG-TERM STABILITY

The existence of slow variables can have crucial implications on the stability of the ISS. The QIs of motion can eﬀectively constraint in an adiabatic way the chaotic diﬀusion of the planet orbits over long timescales, forbidding in general a dynamical instability over a limited time span, e.g., several billions of years. Here we give compelling arguments for such a mechanism.

Figure 7 shows the cumulative distribution function (CDF) of the ﬁrst time that Mercury eccentricity reaches a value of 0.7, from the ensembles of 1080 orbital solutions of H•4 and H•6 introduced in Sect. IVD. We recall

100

H4 H6 H•4 H•6 1%

10

CDF (%)

1

0.1

0.01

1 10 100 Time (Gyr)

FIG. 7. Cumulative distribution function of the ﬁrst time that Mercury eccentricity reaches a value of 0.7, from 1080 orbital solutions of diﬀerent models over 100 Gyr. The shaded regions represent the 90% piecewise conﬁdence intervals from bootstrap.

that such a high eccentricity is a precursor of the dynamical instability (i.e., close encounters, collisions, or ejections of planets) of the ISS [6]. We also report the same CDF for the models H4 and H6, which we recently computed in Ref. [7]. One can appreciate that the time corresponding to a probability of instability of 1% is greater than 100 Gyr for the H•4 model, while it is about 15 Gyr for H4. At degree 6, this time still increases from 5 Gyr for H6 to about 20 Gyr in H•6. The dynamics arising from H•4 and H•6 can be considered as stable in an astronomical sense. Recalling that the main diﬀerence between H•2n and H2n relates to the smallest Lyapunov exponents (Fig. 1), and this is accompanied by a much slower diffusion of the QIs for H•2n (Figs. 2, 10, and 11), Fig. 7 indicates that the dynamical half-life of the ISS is linked to the speed of diﬀusion of these slow quantities in a critical way. We stress that the slower diﬀusion toward the dynamical instability in the H•2n model derives from neglecting the external forcing mainly exerted by Saturn, Uranus, and Neptune.

We also observe that, to a linear approximation, the knowledge of Cinc and E2 allows us to bound the variations of the action variables X,Ψ. Recalling that the actions are positive quantities, from Eq. (19) one sees that ﬁxing a value of Cinc puts an upper bound to the variations of the inclination actions Ψ. As a consequence, at degree 2 in eccentricities and inclinations, ﬁxing a value of the QI

E2 = γ3 · I = γ3ecc · X + γ3inc · Ψ, (32)

with γ3 = (γ3ecc,γ3inc), also bounds the upper variations of the eccentricity actions X, since the components of

γ3ecc have all the same sign, as those of γ3inc (see Appendix B). This is an important point, as we state in Sect. I that the lack of any bound on the chaotic variations of the planet orbits is one of the reasons that complicate the understanding of their long-term stability. We

remark that the secular planetary phase space can be bound by ﬁxing the value of the total AMD, that is, Cecc+Cinc [47]. A statistical study of the density of states that are a priori accessible can then be realized [61]. It is not, however, fully satisfying to consider a ﬁxed value of total AMD of the ISS, as we show that Cecc is changed by some of the leading resonances of the Hamiltonian,

- as a result of the eccentricity forcing mainly exerted by


Jupiter through the mode g5. Moreover, the destabilization of the ISS consists indeed in a large transfer of eccentricity AMD, Cecc, from the outer system to the inner planets through the resonance g1 − g5 [5, 6, 36, 62]. It should be noted that Cecc can still be consider as a slow quantity with respect to an arbitrary function of the action variables, as it is only changed by the subset of the leading resonances involving the external mode g5. This slowness has indeed been observed on stable orbital solutions of the Solar System [47] and supports the statistical hypothesis in Ref. [61] that allows one to obtain a very reasonable ﬁrst guess of the long-term PDFs of the eccentricities and inclinations of the inner planets.

The emerging picture explains the statistical stability of the ISS over billions of years in a physically intuitive way. The chaotic behavior of the planet orbits arises from the interaction of a number of leading resonant harmonics of the Hamiltonian, which determine the Lyapunov time. The strongest resonances are characterized by some exact symmetries, which are only broken by weak resonant interactions. These quasi-symmetries naturally give birth to QIs of motion, quantities that diffuse much more slowly than the LL action variables, constraining the variations of the orbits. The long dynamical half-life of the ISS is connected to the speed of this diﬀusion, which eventually drives the system to the instability. It should be stressed that, besides the speed of diﬀusion, the lifetime of the inner orbits also depends on the initial distance of the system from the instability boundary deﬁned by the resonance g1−g5. This geometric aspect includes the stabilizing role of general relativity [5, 6], which moves the system away from the instability boundary by 0.43 yr−1, and the destabilizing eﬀect of terms of degree 6 in eccentricities and inclinations of the planets [7].

##### VII. DISCUSSION

This work introduces a framework that naturally justiﬁes the statistical stability shown by the ISS over a timescale comparable to its age. Considering a forced secular model of the inner planet orbits, the computation of the Lyapunov spectrum indicates the existence of very diﬀerent dynamical timescales. Using the computer algebra system TRIP, we systematically analyze the Fourier harmonics of the Hamiltonian that become resonant along a numerically integrated orbital solution spanning 5 Gyr. We uncover three symmetries that characterize the strongest resonances and that are broken by

weak resonant interactions. These quasi-symmetries generate three QIs of motion that represent slow variables of the secular dynamics. The size of the leading symmetrybreaking resonances suggests that the QIs are related to the smallest Lyapunov exponents. The claim that the QIs are among the slowest d.o.f. of the dynamics constitutes the central point of this work. On the one hand, it is supported by the analysis of the underlying Hamiltonian H•2n, in which one neglects the forcing mainly exerted by Saturn, Uranus, and Neptune and, as a consequence, the diﬀusion of the QIs is greatly reduced. On the other hand, the geometric framework established by the PCA of the orbital solutions independently conﬁrms that the QIs are statistically the slowest linear variables of the dynamics. We give strong evidence that the QIs of motion play a critical role in the statistical stability of the ISS over the Solar System lifetime, by adiabatically constraining the long-term chaotic diﬀusion of the orbits.

A. Inner Solar System among classical quasi-integrable systems

It is valuable to contextualize the dynamics of the ISS in the class of classical quasi-integrable systems. A comparison with the Fermi-Pasta-Ulam-Tsingou problem, in particular, deserves to be made. This concerns the dynamics of a one-dimensional chain of identical masses coupled by nonlinear springs. For weak nonlinearity, the normal modes of oscillation remain far from the energy equipartition expected from statistical mechanics for a very long time [13]. One way to explain the lack of energy equipartition reported by Fermi and collaborators is through the closeness of the FPUT problem to the integrable Toda dynamics [63–65]. This translates in a very slow thermalization of the action variables of the Toda problem and of the corresponding integrals of motion along the FPUT ﬂow [15, 65–69]. In the framework of the present study, the very long dynamical half-life of the ISS is also likely to be the result of the slow diffusion of some dynamical quantities, the QIs of motion. We ﬁnd, in particular, an underlying Hamiltonian H•2n for which this diﬀusion is greatly reduced, as a consequence of neglecting the forcing mainly exerted by Saturn, Uranus, and Neptune. This results in a dynamics that can be considered as stable in an astronomical sense. We stress that, diﬀerently from the FPUT problem, H•2n is not integrable as the Toda Hamiltonian. It is indeed chaotic and shares with the original Hamiltonian H2n the leading Lyapunov exponents. The QIs that we ﬁnd in this work are only a small number of functions of the action-angle variables of the integrable LL dynamics, and are related to the smallest Lyapunov exponents of the dynamics. Our study suggests that in the FPUT problem the very slow thermalization occurring beyond the Lyapunov time might be understood in terms of combinations of the Toda integrals of motion diﬀusing over very diﬀerent timescales.

The long-term diﬀusion in chaotic quasi-integrable systems should be generally characterized by a broad range of timescales that results from the progressive, hierarchical breaking of the symmetries of the underlying integrable problem by resonant interactions [70–72]. A hierarchy of Lyapunov exponents spanning several orders of magnitude, in particular, should be common among this class of systems [e.g., 73].

B. Methods

The long-term dynamics of the ISS is described by a moderate but not small number of d.o.f., which places it far from the typical application ﬁelds of celestial mechanics and statistical physics. The ﬁrst discipline often studies dynamical models with very few degrees of freedom, while the second one deals with the limit of a very large number of bodies. Chaos also requires a statistical description of the inner planet orbits. But the lack of a statistical equilibrium, resulting from a slow but ceaseless diﬀusion of the system, places the ISS outside the standard framework of ergodic theory. The kind of approach we develop in this work is heavily based on computer algebra, in terms of systematic series expansion of the Hamiltonian, manipulation of the truncated equations of motion, extraction of given Fourier harmonics, retrieval of polynomial roots, etc. [4, 19]. This allows us to introduce QIs of motion in a 16-dimensional dynamics by analyzing how action-space symmetries are progressively broken by resonant interactions. Our eﬀective method based on the time statistics of resonances arising along a single, very long numerical integration is alternative to formal approaches that deﬁne QIs via series expansions [e.g. 74, 75]. The practical usefulness of these formal expansions for a dynamics that covers an intricate, high-dimensional network of resonances seems indeed doubtful. Through the retrieval of the half-widths of the symmetry-breaking resonances, computer algebra also permits us to extend the correspondence between the Lyapunov spectrum and the spectrum of resonances well beyond the standard relation linking the Lyapunov time to the strongest resonances[76].

In the context of dynamical systems with a number of d.o.f. that is not small, this work also considers an approach based on PCA. The role of this statistical technique can be twofold. We use PCA as an independent test to systematically validate the slowness of the QIs. While being introduced semi-analytically as dynamical quantities that are not aﬀected by the leading resonances, they can indeed be related to the last PCs. By extension, the ﬁrst PCs should probe the directions of the main resonances. This leads to a second potential application of the PCA, which should oﬀer a way to retrieve the principal resonant structure of a dynamical system. In this sense, PCA represents a tool to systematically probe numerical integrations of a complex dynamics and distill important hidden insights. We emphasize that PCA is

the most basic linear technique of dimensionality reduction and belongs to the more general class of the unsupervised learning algorithms. There are more sophisticated methods of feature extraction that can be more robust [e.g. 77, 78] and can incorporate nonlinearity [79]. These methods are often less intuitive to understand, less straightforward to apply, and harder to interpret than PCA. Yet, they might be more eﬀective and worth pursuing for future works.

With long-term numerical integration and a computer algebra system at one’s disposal, the entire strategy we develop in this work can in principle be applied to other planetary systems and quasi-integrable Hamiltonian dynamics with a moderate number of d.o.f.

##### ACKNOWLEDGMENTS

The authors thank M. Gastineau for his assistance with TRIP. F.M. is supported by a grant of the French Agence Nationale de la Recherche (AstroMeso ANR19-CE31-0002-01). N.H.H. is supported by a Ph.D. scholarship of the Capital Fund Management (CFM) Foundation for Research. This project has been supported by the European Research Council (ERC) under the European Union’s Horizon 2020 research and innovation program (Advanced Grant AstroGeo-885250). This work was granted access to the HPC resources of MesoPSL ﬁnanced by the Region ˆIle-de-France and the project Equip@Meso (reference ANR-10-EQPX-29-01) of the program Investissements d’Avenir supervised by the Agence Nationale pour la Recherche.

Appendix A: Lyapunov spectrum

Convergence. We perform two tests to address the convergence of our implementation of the Benettin et al. [43] method. We ﬁrst compute the FT-LCEs for a single initial condition of H4 and an ensemble of 150 diﬀerent random sets of initial tangent vectors. Figure 8a shows the [5th, 95th] percentile range of the resulting marginal distributions of the positive FT-LCEs over a time span of 10 Gyr. The distributions shrink with increasing time, eventually collapsing on single time-dependent values. In this asymptotic regime, the Benettin et al. [43] algorithm loses memory of the initial tangent vectors and purely retrieves the FT-LCEs as deﬁned in Eq. (10). Therefore, Fig. 1a shows asymptotically the dependence of the FT-LCEs on the initial condition z0 and represents their statistical distribution over the phase-space domain explored by the dynamics in a non-ergodic way. The convergence of the computation is clearly slower for smaller exponents, but a comparison with Fig. 1a indicates that, even in the case of λ8, the numerical uncertainty on the FT-LCEs of each orbital solution at 10 Gyr is negligible with respect to the width of their ensemble distributions.

λ1

λ2

λ3

λ4

λ5

λ6

λ7

λ8

| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


110100100010000

0.0001 0.001 0.01 0.1 1 −12 FT-LCEs (arcsec yr )π

Lyapunov characteristic times (Myr)

107 108 109 1010 Time (yr)

(a) H4: Single orbital solution

1 2 3 4 5 6 7 8

| |
|---|


0.001 0.01 0.1 1

107 108 109 1010 Time (yr)

(b) H4: Relative numerical errors

- FIG. 8. (a) Positive FT-LCEs of Hamiltonian H4 and corresponding characteristic timescales for a single initial condition and an ensemble of 150 random sets of initial tangent vectors. The bands represent the [5th, 95th] percentile range of the marginal


PDFs. The lines denote the distribution medians. (b) Medians of the relative numerical errors i on the FT-LCEs λi, as deﬁned in Eq. (A1), for the ensemble of 150 orbital solution of Fig. 1a.

To quantitatively estimate the numerical precision on the computed FT-LCEs, we exploit the symmetry of the spectrum stated in Eq. (9). For a single orbital solution, the relative numerical error on each exponent λi can be estimated as

i =

∆λi λi

. (A1)

We plot in Fig. 8b the medians of i for the ensemble of 150 orbital solutions of Fig. 1a. The relative errors decrease asymptotically with time, as expected. Even in the case of the smallest exponent, λ8, the median error is less than 10% at 10 Gyr.

Hamiltonian H6. We compute for comparison the FT-LCEs of the forced ISS truncated at degree 6 in eccentricities and inclinations, that is, H6. We consider 150 stable orbital solutions with initial conditions very close to the nominal values of Gauss’s dynamics and random sets of initial tangent vectors, as we do for the truncation

- at degree 4. Figure 9 shows the [5th, 95th] percentile range of the marginal PDF of each FT-LCE estimated from the ensemble of solutions. Apart from being somewhat larger, the asymptotic distributions of the exponents are very similar to those of H4 shown in Fig. 1a.


Appendix B: Vectors γ1, γ2, γ3

We report here the explicit expressions of the vectors (γi)3i=1. We ﬁrst give the components of the vector ωLL of the fundamental precession frequencies of the inner orbits in the forced Laplace-Lagrange dynamics (including the

leading correction of general relativity) [4]:

ωLL = (gLL,sLL) ≈

(5.87,7.46,17.4,18.1,−5.21,−6.59,−18.8,−17.7),

- (B1) in units of arcsec yr−1 (see [80–82] for comparison with the frequencies of the Laplace-Lagrange dynamics of the entire Solar System). One then has

- γ1 = (04,14) = (0,0,0,0,1,1,1,1),
- γ2 = (0,0,−1,−1,1,1,2,2),
- γ3 = −ωLL + g518 ≈ (−1.61,−3.20,−13.2,−13.9,9.47,10.8,23.0,22.0),


- (B2) with the components of γ3 in units of arcsec yr−1. We recall that g5 ≈ 4.257 yr−1 is a constant in the forced model of the ISS. The corresponding unit vectors ( γi)3i=1 are given by


- γ1 = (0,0,0,0,1,1,1,1)/2,
- γ2 = (0,0,−1,−1,1,1,2,2)/2

√

3,

- γ3 ≈ (−0.04,−0.08,−0.33,−0.35,0.24,0.27,0.58,0.55). (B3)


Since 1/2√3 ≈ 0.289, the components of γ3 are only a few percent away from those of γ2. Therefore, along stable orbital solutions with typical bounded variations of the Mercury-dominated action variable X1, the two quantities C2 and E2n exhibit very similar time evolutions. This is not the case anymore when Mercury orbit reaches high eccentricities.

λ1

λ2

λ3

λ4

λ5

λ6

λ7

λ8

| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


| |
|---|


110100100010000

0.0001 0.001 0.01 0.1 1 −12 FT-LCEs (arcsec yr )π

Lyapunov characteristic times (Myr)

107 108 109 1010 Time (yr)

- FIG. 9. Positive FT-LCEs λi of Hamiltonian H6 and corre-


sponding characteristic timescales λ−i 1. The bands represent the [5th, 95th] percentile range of the marginal PDFs estimated from an ensemble of 150 stable orbital solutions with very close initial conditions. The lines denote the distribution medians.

Appendix C: Ensemble distributions of the quasi-integrals over time

To retrieve the long-term statistical behavior of the QIs, we consider the ensembles of 1080 numerical integrations of the dynamical models H4 and H6, with very close initial conditions and spanning 100 Gyr in the future, that have been presented in Ref. [7]. We also consider the similar ensembles of solutions for the simpliﬁed Hamiltonians H•4 and H•6 that we introduce in Sect. IVD. We report in Fig. 10 the time evolution of the ensemble PDFs of the low-pass ﬁltered dimensionless QIs and dimensionless actions X1,Ψ3 for the diﬀerent models (the cutoﬀ frequency of the time ﬁlter is set to 1 Myr−1, as in Sec. IVB). More precisely, to highlight the growth of the statistical dispersion, we consider at each time the PDF of the signed deviation from the ensemble mean, so that all the plotted distributions have a null mean. At each time, the PDF estimation takes into account only the stable orbital solutions, that is, those solutions whose running maximum of Mercury eccentricity is smaller than 0.7 [7]. Figure 10 shows that the QIs are indeed slow quantities when compared to the LL action variables. The growth of the QI dispersion is detailed in Fig. 11, where we report the time evolution of the interquartile range (IQR) of their distributions. After a transient phase lasting about 100 Myr and characterized by the exponential separation of close trajectories, the time growth of the IQR follows a power law typical of diﬀusion processes. Figures 10 and 11 clearly show the slower diﬀusion of Cinc and C2 in the model H•2n when compared to H2n. We recall that E2•n is an exact integral of motion for the model H•2n (see Sect. IVD) and its PDF has null dispersion.

###### H•4

###### H•6

###### H4

###### H6

60

60

300

300

40

40

200

200

Cinc

20

20

100

100

Time

100 Gyr

0

0

0

0

−0.2 0.0 0.2

−0.2 0.0 0.2

−0.04 −0.02 0.00 0.02 0.04

−0.04 −0.02 0.00 0.02 0.04

1.5 ×104

1.5 ×104

60

60

40

40

1.0

1.0

###### C2

20

20

0.5

0.5

0

0

0.0

0.0

−0.2 0.0 0.2

−0.2 0.0 0.2

−0.0005 0.0000 0.0005

−0.0005 0.0000 0.0005

60

60

40

40

###### E

10 Gyr

20

20

0

0

−0.2 0.0 0.2

−0.2 0.0 0.2

6

6

6

6

4

4

4

4

###### X1

2

2

2

2

0

0

0

0

−1.0 −0.5 0.0 0.5 1.0

−1.0 −0.5 0.0 0.5 1.0

−1.0 −0.5 0.0 0.5 1.0

−1.0 −0.5 0.0 0.5 1.0

1 Gyr

6

6

6

6

4

4

4

4

###### Ψ3

2

2

2

2

0

0

0

0

−1.0 −0.5 0.0 0.5 1.0

−1.0 −0.5 0.0 0.5 1.0

−1.0 −0.5 0.0 0.5 1.0

−1.0 −0.5 0.0 0.5 1.0

- FIG. 10. Time evolution over 100 Gyr of the PDF of the signed deviation from the mean of the low-pass ﬁltered dimensionless QIs and dimensionless actions X1, Ψ3. Estimation from an ensemble of 1080 numerical orbital solutions for diﬀerent models

(H4, H6, H•4, and H•6). First row: Cinc. Second row: C2. Third row: E4 (H4) and E6 (H6). Fourth row: X1. Fifth row: Ψ3. The time of each curve is color coded. At each time, the estimation only takes into account stable solutions, that are those with a

running maximum of Mercury eccentricity smaller than 0.7. The quantity E2•n is an exact integral of motion for the model H•2n and its PDF has null dispersion.

107 108 109 1010 1011

Time (yr)

10−5

10−3

10−1

IQR

Cinc

H4 H6

H•4 H•6

107 108 109 1010 1011

Time (yr)

C2

107 108 109 1010 1011

Time (yr)

E

- FIG. 11. Time evolution of the interquartile range (IQR) of the ensemble PDFs of the QIs shown in Fig. 10. Left: Cinc.


Middle: C2. Right: E4 (H4) and E6 (H6). The quantity E2•n is an exact integral of motion for the model H•2n and its PDF has a null IQR.

- [1] J. Laskar, A numerical experiment on the chaotic behaviour of the solar system, Nature (London) 338, 237

(1989).

- [2] J. Laskar, The chaotic motion of the solar system - A numerical estimate of the size of the chaotic zones, Icarus 88, 266 (1990).
- [3] G. J. Sussman and J. Wisdom, Chaotic evolution of the solar system, Science 257, 56 (1992).
- [4] F. Mogavero and J. Laskar, Long-term dynamics of the inner planets in the Solar System, Astronomy and Astrophysics 655, A1 (2021), arXiv:2105.14976 [astro-ph.EP].
- [5] J. Laskar, Chaotic diﬀusion in the Solar System, Icarus 196, 1 (2008), arXiv:0802.3371.
- [6] J. Laskar and M. Gastineau, Existence of collisional trajectories of Mercury, Mars and Venus with the Earth, Nature (London) 459, 817 (2009).
- [7] N. H. Hoang, F. Mogavero, and J. Laskar, Long-term instability of the inner Solar system: numerical experiments, Monthly Notices of the RAS 514, 1342 (2022), arXiv:2205.04170 [astro-ph.EP].
- [8] K. Batygin, A. Morbidelli, and M. J. Holman, Chaotic Disintegration of the Inner Solar System, Astrophys. J. 799, 120 (2015), arXiv:1411.5066 [astro-ph.EP].
- [9] E. Woillez and F. Bouchet, Instantons for the Destabilization of the Inner Solar System, Phys. Rev. Lett. 125, 021101 (2020), arXiv:1910.04005 [nlin.CD].
- [10] The dynamics truncated at degree 4 produces nevertheless the same chaos of the full system, as measured by the ﬁnite-time maximum Lyapunov exponent [19].
- [11] A. Milani and A. M. Nobili, An example of stable chaos in the Solar System, Nature (London) 357, 569 (1992).
- [12] A. Morbidelli and C. Froeschle´, On the Relationship Between Lyapunov Times and Macroscopic Instability Times, Celestial Mechanics and Dynamical Astronomy 63, 227 (1996).
- [13] E. Fermi, P. Pasta, S. Ulam, and M. Tsingou, Studies of Nonlinear Problems, Tech. Rep. (Los Alamos National Laboratory, 1955).
- [14] K.-D. N. T. Lam and J. Kurchan, Stochastic Perturbation of Integrable Systems: A Window to Weakly Chaotic Systems, Journal of Statistical Physics 156, 619 (2014).
- [15] T. Goldfriend and J. Kurchan, Equilibration of quasiintegrable systems, Phys. Rev. E 99, 022146 (2019), arXiv:1810.06121 [cond-mat.stat-mech].
- [16] This resonance involves the fundamental precession frequencies of Mercury and Jupiter perihelia [5, 36, 62].
- [17] J. Laskar, Large Scale Chaos and Marginal Stability in the Solar System, Celestial Mechanics and Dynamical Astronomy 64, 115 (1996).
- [18] “At each stage of its evolution, the system should have a time of stability comparable with its age” [17].
- [19] F. Mogavero and J. Laskar, The origin of chaos in the Solar System through computer algebra, Astronomy and Astrophysics 662, L3 (2022), arXiv:2205.03298 [astroph.EP].
- [20] J. Laskar, P. Robutel, F. Joutel, M. Gastineau, A. C. M. Correia, and B. Levrard, A long-term numerical solution for the insolation quantities of the Earth, Astronomy and Astrophysics 428, 261 (2004).
- [21] A. Morbidelli, Modern celestial mechanics: aspects of solar system dynamics (Taylor &amp; Francis, 2002).


- [22] C. F. Gauss, Determinatio attrationis, quam in punctum quodvis positionis datae exerceret planeta, SI eius massa per tota orbitam, ratione temporis, quo singulae partes describuntur, uniformiter errat dispertita (Heinrich Dieterich, Go¨ttingen, 1818).
- [23] J. Laskar, Analytical framework in Poincare´ variables for the motion of the solar system, in Predictability, Stability, and Chaos in N-Body Dynamical Systems, NATO Advanced Study Institute (ASI) Series B, Vol. 272, edited by A. Roy (Plenum Press, New York, 1991) pp. 93–114.
- [24] J. Laskar and P. Robutel, Stability of the Planetary Three-Body Problem. I. Expansion of the Planetary Hamiltonian, Celestial Mechanics and Dynamical Astronomy 62, 193 (1995).
- [25] M. Gastineau and J. Laskar, Trip: A computer algebra system dedicated to celestial mechanics and perturbation series, ACM Commun. Comput. Algebra 44, 194 (2011).
- [26] M. Gastineau and J. Laskar, TRIP 1.4.120, TRIP Reference manual (IMCCE, Paris Observatory, 2021).
- [27] E represents the exponential operator and j stands for the imaginary unit. The overline on variables denotes complex conjugate.
- [28] N. H. Hoang, F. Mogavero, and J. Laskar, Chaotic diffusion of the fundamental frequencies in the Solar System, Astronomy and Astrophysics 654, A156 (2021), arXiv:2106.00584 [astro-ph.EP].
- [29] J. Laskar, Secular evolution of the solar system over 10 million years, Astronomy and Astrophysics 198, 341

(1988).

- [30] J. Laskar, Frequency map analysis and quasiperiodic decompositions, in Hamiltonian Systems and Fourier Analysis: New Prospects For Gravitational Dynamics, edited by D. Benest, C. Froeschl´e, and E. Lega (Cambridge Scientiﬁc Publishers Ltd, Cambridge, 2005) pp. 93–114, arXiv:math/0305364.
- [31] V. I. Oseledec, A multiplicative ergodic theorem. Lyapunov characteristic numbers for dynamical systems, Trans.Moscow Math.Soc. 19, 197 (1968).
- [32] J. P. Eckmann and D. Ruelle, Ergodic theory of chaos and strange attractors, Reviews of Modern Physics 57, 617 (1985).
- [33] P. Gaspard, Chaos, Scattering and Statistical Mechanics, Cambridge Nonlinear Science Series (Cambridge University Press, 1998).
- [34] C. Skokos, The Lyapunov characteristic exponents and their computation, in Dynamics of Small Solar System Bodies and Exoplanets, edited by J. J. Souchay and R. Dvorak (Springer Berlin Heidelberg, Berlin, Heidelberg, 2010) p. 63–135.
- [35] J. Laskar, Large-scale chaos in the solar system., Astronomy and Astrophysics 287, L9 (1994).
- [36] K. Batygin and G. Laughlin, On the Dynamical Stability of the Solar System, Astrophys. J. 683, 1207 (2008), arXiv:0804.1946 [astro-ph].
- [37] The FT-LCEs do not depend on any tangent vector ζ0.
- [38] All the initial conditions mentioned in this work are sampled from a multidimensional Gaussian distribution that is centered at the nominal initial conditions of Gauss’s dynamics [4, Appendix D] and has a relative width of 10−9 (see [19, Appendix C] and [7, Sect. 3] for details).


- [39] A. Morbidelli and A. Giorgilli, On a connection between KAM and Nekhoroshev’s theorems, Physica D Nonlinear Phenomena 86, 514 (1995).
- [40] J. Laskar, A Few Points on the Stability of the Solar System (lecture), in Chaos, Resonance, and Collective Dynamical Phenomena in the Solar System, IAU Symposium, Vol. 152, edited by S. Ferraz-Mello (Kluwer Academic Publishers, Dordrecht, 1992) p. 1.
- [41] G. Brown and H. Rein, A Repository of Vanilla Longterm Integrations of the Solar System, Research Notes of the American Astronomical Society 4, 221 (2020), arXiv:2012.05177 [astro-ph.EP].
- [42] G. Benettin, L. Galgani, A. Giorgilli, and J. M. Strelcyn, All Lyapunov characteristic numbers are eﬀectively computable., Academie des Sciences Paris Comptes Rendus Serie B Sciences Physiques 286, 431 (1978).
- [43] G. Benettin, L. Galgani, A. Giorgilli, and J. M. Strelcyn, Lyapunov characteristic exponents for smooth dynamical systems and for Hamiltonian systems - A method for computing all of them. I - Theory. II - Numerical application, Meccanica 15, 9 (1980).
- [44] B. V. Chirikov, A universal instability of manydimensional oscillator systems, Physics Reports 52, 263

(1979).

- [45] J. Laskar, Syste`mes de Variables et El´ements, in Modern Methods in Celestial Mechanics, edited by D. Benest and C. Froeschle (Editions Fronti`eres, Gif -Sur-Yvette, 1990) pp. 63–87.
- [46] G. Boue´ and J. Laskar, Spin axis evolution of two interacting bodies, Icarus 201, 750 (2009).
- [47] J. Laskar, Large scale chaos and the spacing of the inner planets., Astronomy and Astrophysics 317, L75 (1997).
- [48] I. G. Zurbenko and D. Smith, Kolmogorov–Zurbenko ﬁlters in spatiotemporal analysis, WIREs Computational Statistics 10, e1419 (2018).
- [49] A. C. M. Correia and J. Laskar, Long-term evolution of the spin of Venus. II. numerical simulations, Icarus 163, 24 (2003).
- [50] K. Pearson, LIII. On lines and planes of closest ﬁt to systems of points in space, The London, Edinburgh, and Dublin philosophical magazine and journal of science 2, 559 (1901).
- [51] H. Hotelling, Analysis of a complex of statistical variables into principal components., Journal of educational psychology 24, 417 (1933).
- [52] I. T. Jolliﬀe, Principal component analysis (Springer, 2002).
- [53] I. T. Jolliﬀe and J. Cadima, Principal component analysis: a review and recent developments, Philosophical Transactions of the Royal Society A: Mathematical, Physical and Engineering Sciences 374, 20150202 (2016).
- [54] The projection of a vector q onto the subspace spanned by a set of vectors S can be written in a vectorial form as B(BTB)−1BTq, where the column space of the matrix B is the subspace spanned by the set S.
- [55] C. Jordan, Essai sur la ge´ome´trie a` n dimensions, Bulletin de la Soci´et´e mathe´matique de France 3, 103 (1875).
- [56] C. F. Van Loan and G. Golub, Matrix computations (The Johns Hopkins University Press, London, 1996).
- [57] K. Ye and L.-H. Lim, Schubert varieties and distances between subspaces of diﬀerent dimensions, SIAM Journal on Matrix Analysis and Applications 37, 1176 (2016).
- [58] A. Bjo¨rck and G. H. Golub, Numerical methods for computing angles between linear subspaces, Mathematics of


- computation 27, 579 (1973).
- [59] A. V. Knyazev and M. E. Argentati, Principal angles between subspaces in an a-based scalar product: algorithms and perturbation estimates, SIAM Journal on Scientiﬁc Computing 23, 2008 (2002).
- [60] M. E. Muller, A note on a method for generating points uniformly on n-dimensional spheres, Commun. ACM 2, 19–20 (1959).
- [61] F. Mogavero, Addressing the statistical mechanics of planet orbits in the solar system, Astronomy and Astrophysics 606, A79 (2017), arXiv:1703.09225 [astroph.EP].
- [62] G. Bou´e, J. Laskar, and F. Farago, A simple model of the chaotic eccentricity of Mercury, Astronomy and Astrophysics 548, A43 (2012), arXiv:1210.5221 [astro-ph.EP].
- [63] M. He´non, Integrals of the Toda lattice, Phys. Rev. B 9, 1921 (1974).
- [64] H. Flaschka, The Toda lattice. II. Existence of integrals, Phys. Rev. B 9, 1924 (1974).
- [65] S. V. Manakov, Complete integrability and stochastization of discrete dynamical systems, Zhurnal Eksperimentalnoi i Teoreticheskoi Fiziki 67, 543 (1974).
- [66] J. Ferguson, W. E., H. Flaschka, and D. W. McLaughlin, Nonlinear Normal Modes for the Toda Chain, Journal of Computational Physics 45, 157 (1982).
- [67] G. Benettin, H. Christodoulidi, and A. Ponno, The Fermi-Pasta-Ulam Problem and Its Underlying Integrable Dynamics, Journal of Statistical Physics 152, 195

(2013).

- [68] H. Christodoulidi and C. Efthymiopoulos, Stages of dynamics in the Fermi-Pasta-Ulam system as probed by the ﬁrst Toda integral, Mathematics in Engineering 1, 359 (2019).
- [69] T. Grava, A. Maspero, G. Mazzuca, and A. Ponno, Adiabatic Invariants for the FPUT and Toda Chain in the Thermodynamic Limit, Communications in Mathematical Physics 380, 811 (2020), arXiv:2001.08070 [math-ph].
- [70] J. Ford, Equipartition of Energy for Nonlinear Systems, Journal of Mathematical Physics 2, 387 (1961).
- [71] M. Onorato, L. Vozella, D. Proment, and Y. V. Lvov, Route to thermalization in the α-Fermi-Pasta-Ulam system, Proceedings of the National Academy of Science 112, 4208 (2015), arXiv:1402.1603 [nlin.CD].
- [72] L. Pistone, S. Chibbaro, M. D. Bustamante, Y. V. Lvov, and M. Onorato, Universal route to thermalization in weakly-nonlinear one-dimensional chains, Mathematics in Engineering 1, 672–698 (2019).
- [73] M. Malishava and S. Flach, Lyapunov Spectrum Scaling for Classical Many-Body Dynamics Close to Integrability, Phys. Rev. Lett. 128, 134102 (2022), arXiv:2109.01361 [nlin.CD].
- [74] G. Contopoulos, A third Integral of Motion in a Galaxy, Zeitschrift fuer Astrophysik 49, 273 (1960).
- [75] M. Kruskal, Asymptotic Theory of Hamiltonian and other Systems with all Solutions Nearly Periodic, Journal of Mathematical Physics 3, 806 (1962).
- [76] In this regard, it should be noted that a relation between QIs and Lyapunov exponents has already been highlighted in simple systems [43, 83].
- [77] E. J. Cand`es, X. Li, Y. Ma, and J. Wright, Robust principal component analysis?, Journal of the ACM (JACM) 58, 1 (2011).
- [78] P. P. Markopoulos, G. N. Karystinos, and D. A. Pados, Optimal algorithms for l {1}-subspace signal processing,


- IEEE Transactions on Signal Processing 62, 5046 (2014).
- [79] J. A. Lee and M. Verleysen, Nonlinear dimensionality reduction, Vol. 1 (Springer, 2007).
- [80] V. A. Brumberg and J. Chapront, Construction of a General Planetary Theory of the First Order, Celestial Mechanics 8, 335 (1973).
- [81] P. Bretagnon, Long-period terms in the solar system, Astronomy and Astrophysics 30, 141 (1974).


- [82] J. Laskar, Accurate methods in general planetary theory, Astronomy and Astrophysics 144, 133 (1985).
- [83] G. Contopoulos, L. Galgani, and A. Giorgilli, On the number of isolating integrals in Hamiltonian systems, Phys. Rev. A 18, 1183 (1978).


