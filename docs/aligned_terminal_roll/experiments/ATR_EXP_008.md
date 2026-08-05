# ATR_EXP_008 — Full-chain terminal-roll check

**Status:** Complete
**Date:** 2026-08-04
**Related sprint:** Sprint 02
**Related claim IDs:** C3, C4, C5

## 1. Purpose

Confirm `dp/dq6=0`, `dd/dq6=0`, and recoverable roll about `d` on the full 6R chain, not only the isolated fixture.

## 2. Expected result

Position and pointing invariant under `Δq6`; world relative rotation is roll about `d`.

## 3. Results

PASS. `||J_p e6|| ~ 0`, `||J_d e6|| = 0`, position change `0 m`, roll error `4.4e-16 rad`.

## 4. Interpretation

- `PASS`
