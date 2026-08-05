# ATR_EXP_030 — Alternate task-space `h` artifact control

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 05 — Explicit one-dimensional fiber
**Related claim IDs:** C11, H5, R06, A09
**Random seed:** none
**Implementation commit:** `9eaf0ff`

## 1. Purpose

Show that a second task-space scalar `h' = n' · d` with `n' = (1, 0, 0)` still yields a regular reversible pointing fiber, and that freezing `q2` produces a distinct path.

## 2. Expected result

Alternate `h'` is independent, reversible, and noncollapsed on both architectures. The `q2`-freeze control differs from the primary fiber by more than `1e-3` rad at shared `|σ|`.

## 3. Command

```bash
python scripts/validate_pointing_fiber.py
```

## 4. Results

- status: PASS
- observed: IP `alt_rev_ed=1.430e-08`, freeze `dq=1.482e-02`; UR-like `alt_rev_ed=3.300e-09`, freeze `dq=1.557e-01`; both distinct

## 5. Interpretation

- `PASS` is evidence against a pure coordinate-fixing artifact (R06) for this named pair of task-space slices. It does not close R06 globally or verify A09 by itself.
