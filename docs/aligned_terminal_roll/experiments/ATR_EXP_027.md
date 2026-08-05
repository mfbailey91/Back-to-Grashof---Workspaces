# ATR_EXP_027 — Independence of `h = n · d`

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 05 — Explicit one-dimensional fiber
**Related claim IDs:** C11, H1, A09
**Random seed:** none
**Implementation commit:** TBD (regenerate after clean commit)

## 1. Purpose

Test that the locked primary scalar `h(q) = n · d(q)` with `n = (0, 1, 0)` is independent of `p = p0` and of terminal roll at the regular IP and UR-like seeds.

## 2. Expected result

Stacked `(p, h)` Jacobian on `q1…q5` has rank 4 and nullity 1. `dh/dq6 = 0`.

## 3. Command

```bash
python scripts/validate_pointing_fiber.py
```

## 4. Results

- status: PASS
- observed: IP and UR-like both rank 4 / nullity 1, `dh/dq6 = 0`

## 5. Interpretation

- `PASS` supports H1 at the locked seeds. It does not by itself establish a continued fiber.
