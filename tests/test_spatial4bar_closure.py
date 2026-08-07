from __future__ import annotations

import numpy as np
import pytest

from grashof_workspace.spatial4bar_explorer.closure import (
    build_uuur_closure_problem,
    closure_residual,
    corrupt_link_transform,
    is_near_singular,
    residual_norm,
    solve_seed_assembly,
)
from grashof_workspace.spatial4bar_explorer.continuation import (
    ContinuationConfig,
    continue_physical_uuur_sample,
    continue_uuur_branch,
)
from grashof_workspace.spatial4bar_explorer.descriptors import generate_geometry_samples
from grashof_workspace.spatial4bar_explorer.geometry import canonical_geometry
from grashof_workspace.spatial4bar_explorer.geometry_descriptors import generate_physical_geometry_samples
from grashof_workspace.spatial4bar_explorer.models import (
    ExplorerCase,
    OrderedFamily,
    ToolAxis,
    dataclass_to_jsonable,
)
from grashof_workspace.spatial4bar_explorer.readouts import write_sprint03_html


def test_uuur_reference_residual_is_numerically_zero() -> None:
    """Boundary/equality: the stored reference assembly is an exact seed."""
    geometry = canonical_geometry(OrderedFamily.UUUR)
    problem = build_uuur_closure_problem(geometry)
    angles = np.zeros(7, dtype=float)
    assert residual_norm(problem, angles) < 1e-12
    seed = solve_seed_assembly(problem)
    assert seed.success
    assert seed.residual_norm < 1e-12


def test_uuur_interior_continuation_exports_trajectory() -> None:
    """Interior: canonical UUUR continues with bounded residual samples."""
    geometry = canonical_geometry(OrderedFamily.UUUR)
    problem = build_uuur_closure_problem(geometry)
    case = ExplorerCase(OrderedFamily.UUUR, ToolAxis.A)
    trajectory, result = continue_uuur_branch(
        problem,
        case,
        sample_id="uuur_canonical",
        config=ContinuationConfig(step=0.08, max_steps=60),
    )
    assert len(trajectory.samples) >= 5
    assert all(sample.residual_norm < 1e-5 for sample in trajectory.samples[:-1])
    assert "mock_placeholder" not in result.notes
    assert "closure_continuation_v03" in result.notes
    assert result.w_alpha is None and result.w_beta is None
    payload = dataclass_to_jsonable(trajectory)
    assert isinstance(payload, dict)
    assert payload["samples"][0]["joint_angles"]


def test_exterior_corrupted_reference_pose_fails_assembly() -> None:
    """Exterior: a broken link transform makes the zero pose non-assembling."""
    geometry = canonical_geometry(OrderedFamily.UUUR)
    problem = build_uuur_closure_problem(geometry)
    broken = corrupt_link_transform(problem, scale=0.55)
    zero = np.zeros(7, dtype=float)
    assert residual_norm(broken, zero) > 0.2
    residual = closure_residual(broken, zero)
    assert residual.shape == (6,)


def test_singularity_hook_reports_finite_sigma() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    problem = build_uuur_closure_problem(geometry)
    # At the regular reference seed the constrained Jacobian should not be flagged singular.
    assert not is_near_singular(problem, np.zeros(7), free_index=0, tol=1e-4)


def test_v03_rejects_v01_descriptor_only_samples() -> None:
    v01 = generate_geometry_samples(OrderedFamily.UUUR, count=1, seed=1)[0]
    case = ExplorerCase(OrderedFamily.UUUR, ToolAxis.A)
    with pytest.raises(AttributeError):
        # V01 GeometrySample has no provenance/geometry contract for continuation.
        continue_physical_uuur_sample(v01, case)  # type: ignore[arg-type]


def test_physical_sample_continuation_path() -> None:
    sample = generate_physical_geometry_samples(OrderedFamily.UUUR, count=1, seed=9)[0]
    case = ExplorerCase(OrderedFamily.UUUR, ToolAxis.B)
    trajectory, result = continue_physical_uuur_sample(
        sample,
        case,
        config=ContinuationConfig(step=0.1, max_steps=40),
    )
    assert sample.provenance == "physical_geometry_v02b"
    assert trajectory.sample_id == sample.sample_id
    assert result.sample_id == sample.sample_id
    assert len(trajectory.samples) >= 1


def test_sprint03_html_marks_winding_pending(tmp_path) -> None:
    sample = generate_physical_geometry_samples(OrderedFamily.UUUR, count=1, seed=2)[0]
    case = ExplorerCase(OrderedFamily.UUUR, ToolAxis.A)
    trajectory, result = continue_physical_uuur_sample(
        sample,
        case,
        config=ContinuationConfig(step=0.1, max_steps=20),
    )
    write_sprint03_html(
        tmp_path,
        results=[result],
        trajectories=[trajectory],
        trajectory_plot="figures/uuur_branch_trajectory.png",
        trajectory_json="data/branch_trajectories.json",
    )
    html = (tmp_path / "sprint_03_closure.html").read_text(encoding="utf-8")
    assert "WINDING NOT COMPUTED YET" in html
    assert "branch_trajectories.json" in html
    assert "closure_continuation_v03" in html
