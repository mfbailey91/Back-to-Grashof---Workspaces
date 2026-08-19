#!/usr/bin/env python3
"""Compact R3A campaign evidence and record the raw-bundle SHA-256."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.l5_reconstruction.campaign_package import main

if __name__ == "__main__":
    raise SystemExit(main())
