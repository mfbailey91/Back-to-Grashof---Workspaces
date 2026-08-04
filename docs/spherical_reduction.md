# Spherical and regional reductions (Sprints 2–3)

Conventions for reducing synthetic 6R architectures to virtual planar and spherical four-bars. Complements [`docs/theory.md`](theory.md) and [`docs/MATH_NOTES.md`](MATH_NOTES.md) §7–8.

## 1. Separation of claims

| Claim | Meaning |
|-------|---------|
| Regional reachability | Wrist center \(C_w\) is reachable by the proximal chain |
| Orientation capability at a reachable position | Residual orientation motion admits a spherical 4R classification |

Never conflate the two. Never infer orientation dexterity from the Grashof product alone.

## 2. Base-azimuth quotient (Architecture A)

Architecture A has unrestricted revolute \(q_1\) about \(\hat a_1=(0,0,1)\) through the shoulder. Task-space membership of the wrist center is invariant under global rotation about \(\hat a_1\).

**Quotient:** work in the arm’s meridional plane. Record

\[
\psi=\operatorname{atan2}(C_{w,y},C_{w,x})
\]

as the quotiented base azimuth, then classify regional geometry using

\[
\rho_w=\|C_w\|.
\]

Architecture C breaks \(d(z_1,z_2)=0\); the same quotient is only a candidate and must be labeled when \(\epsilon_s>0\).

## 3. Regional planar structure (Architecture A)

Proximal chain to the wrist is an RR with lengths \(L_2,L_3\) in the arm plane.

**Reachability predicate**

\[
|L_2-L_3|\le \rho_w\le L_2+L_3.
\]

**Virtual planar four-bar (tool tip in the meridional plane)**

After the base quotient, treat the planar chain to the tool tip (including tool offset \(L_t\) as the terminal planar link) as the ordered four-bar

\[
(d,a,b,c)=(\rho_p,\ L_t,\ L_3,\ L_2),
\]

where \(\rho_p\) is the distance from the shoulder origin to the tool tip **projected into the arm plane** (for Architecture A with intersecting shoulder, this equals the planar radius of the tool point in that plane).

Link roles (docstring convention):

| Symbol | Role |
|--------|------|
| \(d=\rho_p\) | ground |
| \(a=L_t\) | input (planar terminal / tool) |
| \(b=L_3\) | coupler (forearm) |
| \(c=L_2\) | output (upper arm) |

Assemblability and Grashof labels use the planar `FourBar` rules; **designated-link rotatability** remains a separate predicate (planar research kernel).

## 4. Spherical virtual four-bar (Architecture A)

**Status gate:** compute wrist concurrency residual \(\rho_C\). If status is `invalid`, do **not** emit spherical angles — fail explicitly.

**Construction (Architecture A, concurrent orthogonal wrist):** on the unit sphere centered at \(C_w\), form four unit directions:

1. \(n=\widehat{a_2\times e_f}\) — meridional normal (\(e_f\): forearm direction toward \(C_w\));
2. \(f=\hat a_4\) — first wrist axis;
3. \(m=\hat a_5\) — second wrist axis;
4. \(t=\hat a_6\) — tool / hand approach axis.

Spherical link angles (Murray–Larochelle order):

\[
\begin{aligned}
\alpha&=\angle(n,f),\\
\eta&=\angle(f,m),\\
\beta&=\angle(m,t)\quad\text{(hand-orientation / output link)},\\
\gamma&=\angle(t,n).
\end{aligned}
\]

All angles are clamped to \((0,\pi]\). If any angle is numerically \(0\) or the directions are undefined, the reduction is `invalid`.

**Home-pose check (Architecture A, \(q=0\)):** \(\alpha=\eta=\beta=\pi/2\), \(\gamma=\pi\), which classifies as McCarthy–Soh type 11 (wrap-around double-crank) under the output-hand convention — a dexterity **candidate** under the working hypothesis, not a proven \(SO(3)\) claim.

This axis-sphere construction is the **locked Sprint 2 convention** for Architecture A. Extending it unchanged to arbitrary skew wrists is **unverified**; Architectures B/C must pass the residual gate first.

## 5. Architectures B and C

| Architecture | Regional | Spherical |
|--------------|----------|-----------|
| B (\(\epsilon_w\)) | Parallel \(z_2\|z_3\|z_4\) regional candidate | Exact only at \(\epsilon_w=0\); else approximate/invalid by \(\rho_C\) |
| C (\(\epsilon_s\)) | Shoulder offset breaks exact base coincidence | Spherical remains exact (concurrent wrist) for all \(\epsilon_s\) |

When spherical status is `invalid`, predictors must not invent \(T_i\) values.

## 6. Predictor output (Sprint 3)

Every evaluated state returns the §6.5 record from the project plan: \(T_i\), signs, product, family, type 1–16, input/output/hand crank-rocker, wrap-around flag, residual status, boundary warning, and `dexterity_candidate_hypothesis` true only for hand-crank types \(\{2,3,10,11\}\).

Hand-link assignment defaults to output \(\beta\). Alternate assignments (e.g. input \(\alpha\)) are explicit and recorded for sensitivity analysis.
