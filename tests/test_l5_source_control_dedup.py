"""Wrapped-Q deduplication: duplicates merge, asymmetric subsets do not."""

from __future__ import annotations

from grashof_workspace.spatial_experiments.l5_reconstruction.source_control import (
    SourceControlFiber,
    deduplicate_fibers,
    directed_q_distance,
    symmetric_q_distance,
)


def _fiber(fid: str, qs: tuple[tuple[float, ...], ...]) -> SourceControlFiber:
    return SourceControlFiber(
        fiber_id=fid,
        c=0.1,
        q_samples=qs,
        pointing_samples=tuple((1.0, 0.0, 0.0) for _ in qs),
        branch_status="returned",
        returned=True,
        max_position_residual_m=0.0,
        max_h_residual=0.0,
    )


def test_duplicate_seeds_on_one_component_deduplicate() -> None:
    q = ((0.1, 0.2, 0.3, 0.4, 0.5), (0.15, 0.2, 0.3, 0.4, 0.5), (-0.1, 0.0, 0.1, 0.0, 0.0))
    a = _fiber("a", q)
    b = _fiber("b", q)
    out = deduplicate_fibers((a, b), tol=0.2)
    assert len(out) == 1


def test_asymmetric_components_are_not_merged() -> None:
    short = ((0.0, 0.0, 0.0, 0.0, 0.0), (0.1, 0.0, 0.0, 0.0, 0.0))
    long = short + ((1.5, 0.0, 0.0, 0.0, 0.0), (1.6, 0.0, 0.0, 0.0, 0.0))
    d_ab = directed_q_distance(short, long)
    d_ba = directed_q_distance(long, short)
    assert d_ab < d_ba
    out = deduplicate_fibers((_fiber("short", short), _fiber("long", long)), tol=0.2)
    assert len(out) == 2
    assert symmetric_q_distance(short, long) == d_ba
