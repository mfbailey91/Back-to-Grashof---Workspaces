# Architecture Decisions

## ADR-001 — Start with unrestricted planar 3R

**Decision:** Phase 1 assumes all three revolute joints can traverse \(2\pi\).

**Reason:** This exposes rotational symmetry and produces a clean analytical baseline. Joint limits are a separate mechanism that break or restrict that symmetry and should not be mixed into the first proof.

## ADR-002 — Keep analytical and sampled methods independent

**Decision:** The analytical workspace is computed from interval containment. Direct orientation sampling is used only for validation.

**Reason:** A sampled map must not silently become the definition of the workspace being claimed as analytical.

## ADR-003 — Track link-specific rotatability

**Decision:** Use Grashof classification as metadata, but determine whether \(l_3\) rotates fully through exact loop-closure bounds.

**Reason:** The generic Grashof condition only states that at least one link may rotate in a linkage family. The workspace question concerns one specific link in one specific inversion.

## ADR-004 — No robotics framework dependency in the MVP

**Decision:** Use Matplotlib only for visualization. The analytical kernel is pure Python.

**Reason:** The initial mathematics is small enough to inspect directly. URDF parsing, symbolic packages, NumPy, and general robot libraries can be added after the core result is stable.

## ADR-005 — Capability fields begin only after workspace validation

**Decision:** Do not build task decomposition or capability scoring into Sprint 1–2.

**Reason:** The first research claim is the workspace boundary. Capability fields should be layered on a trusted geometric kernel rather than developed simultaneously.

## ADR-006 — Classification precedence and radial mechanism state

**Decision:** Classify equivalent four-bars with assemblability and degeneracy before conventional Grashof inversion names, and expose a single radial-state record for atlas CSV and radial plots.

**Reason:** Non-assemblable and coincident-ground loops must not inherit misleading mechanism labels, and the Grashof-to-dexterity relationship must be inspectable from one API.

## ADR-007 — Exact radial partitions and static dashboard

**Decision:** Analytical transition radii drive regime labels; dense sampling is visualization/validation only. The atlas dashboard is a static HTML/CSS/JS site with no framework and no remote assets. Dexterity is never derived from Grashof class in plots or JavaScript.

**Reason:** The research claim is that designated-input rotatability, not generic Grashof membership, defines the dexterous workspace. Exact boundaries and a standalone dashboard make that claim inspectable.

## ADR-008 — Synthetic 6R package beside planar kernel

**Decision:** Implement spherical 6R Sprints 0–1 as a separate package `sixr_grashof` in the same repository, leaving `grashof_workspace` unchanged. Begin with idealized architectures A/B/C (no URDF). Encode McCarthy–Soh types 1–16 fully; treat hand-link crank types `{2,3,10,11}` only as a documented hypothesis.

**Reason:** Phase 5 needs its own conventions and fixtures without risking planar regressions, and the project plan’s Gate 1 requires unambiguous spherical closure math before IK sampling or commercial models.
