# ATR_EXP_036 — Tangent and continued-motion equivalence

**Status:** Deferred
**Date:** 2026-08-05
**Related sprint:** Sprint 06 — Candidate spherical equivalence
**Related claim IDs:** C12, H5

## 1. Purpose

If an IP candidate were exact under ATR_EXP_033/034, design local tangent and continued-motion equivalence to a well-posed spherical `RRRR` model.

## 2. Deferral reason

Both IP candidates returned verdict `fail` after the corrected `S−UA−UB−R5` construction: global concurrency residuals of order `0.2–0.3 m`, center drift of order `0.08–0.09 m`, arc residuals of order `0.8 rad`, and body-fixed axis drift of order `0.5 rad`. No exact spherical model is well-posed, so 036 is not designed or coded.

## 3. Still blocked

- spherical chain class / `spherical_equivalence.py`
- McCarthy–Soh `T1`–`T4`
- exact UR / URDF work
