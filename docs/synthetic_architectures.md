# Synthetic 6R architectures

Nominal dimensions (normalized):

\[
L_2 = 1.0,\qquad L_3 = 0.8,\qquad L_t = 0.25.
\]

All revolute joints are unrestricted (\(2\pi\)-periodic) in Sprints 0–1.

Configs: `configs/architecture_a.yaml`, `architecture_b.yaml`, `architecture_c.yaml`.

## Architecture A — Exact regional + exact spherical wrist

Canonical elbow manipulator:

\[
z_1 \perp z_2,\qquad z_2 \parallel z_3,
\]

concurrent wrist

\[
z_4 \cap z_5 \cap z_6 = C_w.
\]

**Default DH-style layout (meters / radians, but normalized):**

- Base frame origin at shoulder.
- Axis 1: \(\hat a_1 = (0,0,1)\), point \(p_1 = (0,0,0)\).
- Axis 2: \(\hat a_2 = (0,1,0)\) at \(q_1=0\) home; \(p_2 = (0,0,0)\) (intersecting).
- Axis 3: \(\hat a_3 = (0,1,0)\), \(p_3 = (L_2, 0, 0)\) in the link-2 frame at home (parallel to axis 2).
- Wrist center \(C_w\) at distance \(L_3\) along the forearm from joint 3.
- Axes 4,5,6 concurrent at \(C_w\), mutually orthogonal in sequence (spherical wrist).
- Tool frame offset \(L_t\) along \(\hat a_6\).

**Expected geometry reports:** exact planar regional reduction candidates; exact spherical wrist (\(\rho_C \le \rho_{\mathrm{exact}}\)).

## Architecture B — Exact regional + parameterized wrist offset

UR-like:

\[
z_2 \parallel z_3 \parallel z_4,
\]

distal wrist axes orthogonal in sequence but not concurrent when \(\epsilon_w > 0\).

Sweep:

\[
\epsilon_w \in \{0, 0.025, 0.05, 0.10, 0.20\}.
\]

At \(\epsilon_w = 0\), wrist is exactly spherical. Residual \(\rho_C\) must increase monotonically with \(\epsilon_w\). The offset is applied **perpendicular** to \(z_6\) (not along the axis), otherwise the directed line is unchanged.

## Architecture C — Parameterized shoulder offset + exact spherical wrist

Concurrent wrist for all \(\epsilon_s\). Proximal offset:

\[
\epsilon_s = d(z_1, z_2) \in \{0, 0.025, 0.05, 0.10, 0.20\}.
\]

Spherical residual stays exact; regional reduction quality is the quantity that degrades (Sprint 2+).

## Home configurations for visualization

Unless noted, plots and axis reports use the zero joint vector \(q = 0\) in each architecture’s joint convention.
