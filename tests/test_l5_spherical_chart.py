"""ZYZ spherical chart compose/decompose round trip and singularities."""

from __future__ import annotations

import numpy as np

from grashof_workspace.spatial_experiments.l5_reconstruction.models import load_campaign_config
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    SphericalClosureChart,
    charts_from_config,
)

CONFIG = "configs/l5_positive_control_v1.json"


def test_chart_round_trip_away_from_poles() -> None:
    config = load_campaign_config(CONFIG)
    charts = charts_from_config(config.charts)
    assert len(charts) == 3
    rng = np.random.default_rng(7)
    for chart in charts:
        for _ in range(8):
            a, b, lam = (float(rng.uniform(-np.pi, np.pi)), float(rng.uniform(0.2, np.pi - 0.2)), float(rng.uniform(-np.pi, np.pi)))
            R = chart.compose(a, b, lam)
            err = chart.round_trip_error(R)
            assert err <= 1e-6
            coords = chart.decompose(R)
            assert coords.singular is False


def test_singular_poles_are_reported() -> None:
    chart = SphericalClosureChart(
        chart_id="ZYZ_WORLD",
        basis=np.eye(3),
        reference=np.eye(3),
        singularity_tol=1e-6,
    )
    R = chart.compose(0.3, 0.0, -0.2)
    coords = chart.decompose(R)
    assert coords.singular
