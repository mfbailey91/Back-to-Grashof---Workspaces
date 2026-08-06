"""Aligned terminal-roll visual mechanism probe.

Isolated from the planar workspace kernel and from ATR continuation /
fiber / Jacobian research code. Homogeneous-transform forward kinematics
and exact axis geometry only.

This package is explanatory and diagnostic. It is not a spherical-four-bar
certification tool and must not be treated as production kinematics.
"""

from __future__ import annotations

__all__ = ["DISCLAIMER"]

DISCLAIMER = (
    "VISUAL PROBE ONLY — not production code, not spherical-four-bar "
    "certification, and not part of the trusted planar workspace kernel."
)
