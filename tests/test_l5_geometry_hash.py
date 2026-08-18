"""Geometry identity is canonical SHA-256, stable across processes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    charts_from_config,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import geometry_hash

CONFIG = Path("configs/l5_positive_control_v1.json")
_SNIPPET = r"""
from pathlib import Path
from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import charts_from_config
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import geometry_hash
config = load_campaign_config(Path("configs/l5_positive_control_v1.json"))
chart = charts_from_config(config.charts)[0]
print(geometry_hash(chart, 0.3))
"""


def test_geometry_hash_is_sha256_and_stable_in_subprocess() -> None:
    config = load_campaign_config(CONFIG)
    chart = charts_from_config(config.charts)[0]
    local = geometry_hash(chart, 0.3)
    assert len(local) == 64
    assert int(local, 16) >= 0
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = "src"
    proc = subprocess.run(
        [sys.executable, "-c", _SNIPPET],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),
        env=env,
    )
    remote = proc.stdout.strip().splitlines()[-1]
    assert remote == local
