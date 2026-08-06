from __future__ import annotations

import math
from typing import Iterable

from .models import BranchClass, BranchResult, ExplorerCase, GeometrySample, OrderedFamily, ToolAxis


def classify_mock_branch(sample: GeometrySample, case: ExplorerCase) -> BranchResult:
    d = sample.descriptor_map()
    twist_bias = float(d["twist_23_deg"])
    l12 = float(d["center_distance_12"])
    l23 = float(d["center_distance_23"])
    l34 = float(d["center_distance_34"])
    symmetry = bool(d["has_mirror_symmetry"])
    planarish = float(d["coplanarity_residual"]) < 0.12
    score = l12 + l34 - l23
    if case.tool_axis is ToolAxis.A:
        w_alpha = 1 if score > 0.55 and twist_bias > 55.0 else 0
        w_beta = 1 if symmetry and twist_bias > 100.0 else 0
    else:
        w_alpha = 1 if symmetry and twist_bias > 110.0 else 0
        w_beta = 1 if score < 1.8 and twist_bias > 70.0 else 0

    class_alpha = _class_from_winding(w_alpha, score, planarish)
    class_beta = _class_from_winding(w_beta, score, planarish)
    notes: list[str] = []
    if planarish:
        notes.append("near-planar center geometry")
    if symmetry:
        notes.append("mirror-symmetric candidate")
    if case.family in {OrderedFamily.USRR, OrderedFamily.URSR, OrderedFamily.URRS}:
        notes.append("RRUS-like family; expect S-joint descriptors to matter strongly")

    return BranchResult(
        sample_id=sample.sample_id,
        case=case,
        branch_id="branch_00",
        branch_closed=True,
        singularity_count=0,
        w_alpha=w_alpha,
        w_beta=w_beta,
        class_alpha=class_alpha,
        class_beta=class_beta,
        tool_range_alpha=(2.0 * math.pi) if w_alpha else (math.pi * (0.4 + min(score / 3.0, 0.5))),
        tool_range_beta=(2.0 * math.pi) if w_beta else (math.pi * (0.35 + min(abs(score - 1.0) / 3.0, 0.5))),
        notes=notes,
    )


def _class_from_winding(winding: int, score: float, planarish: bool) -> BranchClass:
    if winding != 0:
        return BranchClass.CRANK
    if planarish and abs(score - 0.5) < 0.1:
        return BranchClass.CHANGE_POINT
    return BranchClass.ROCKER


def summarize_class_counts(results: Iterable[BranchResult]) -> dict[str, int]:
    counts = {classification.value: 0 for classification in BranchClass}
    for result in results:
        counts[result.class_alpha.value] += 1
        counts[result.class_beta.value] += 1
    return counts
