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

**Decision:** Use NumPy and Matplotlib only.

**Reason:** The initial mathematics is small enough to inspect directly. URDF parsing, symbolic packages, and general robot libraries can be added after the core result is stable.

## ADR-005 — Capability fields begin only after workspace validation

**Decision:** Do not build task decomposition or capability scoring into Sprint 1.

**Reason:** The first research claim is the workspace boundary. Capability fields should be layered on a trusted geometric kernel rather than developed simultaneously.
