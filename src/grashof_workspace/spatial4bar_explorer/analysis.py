from __future__ import annotations

import math
from collections import Counter
from typing import Iterable

from .models import BranchClass, BranchResult, ExplorerCase, GeometrySample, OrderedFamily, ToolAxis

MOCK_PLACEHOLDER_NOTE = "mock_placeholder"


def classify_mock_branch(sample: GeometrySample, case: ExplorerCase) -> BranchResult:
    """Return a deterministic placeholder branch result for Sprint V02 scaffolding.

    Classifications and windings are heuristic stand-ins only. True closure
    continuation and winding arrive in later sprints.
    """
    d = sample.descriptor_map()
    twist_bias = float(d["twist_23_deg"])
    l12 = float(d["center_distance_12"])
    l23 = float(d["center_distance_23"])
    l34 = float(d["center_distance_34"])
    symmetry = bool(d["has_mirror_symmetry"])
    planarish = float(d["coplanarity_residual"]) < 0.12
    score = l12 + l34 - l23
    seed_tag = sample.seed % 17

    # Deterministic placeholder edge paths so every BranchClass appears in corpora.
    if seed_tag == 0 and case.tool_axis is ToolAxis.A:
        return _placeholder_result(
            sample,
            case,
            branch_id="branch_no_assembly",
            branch_closed=False,
            singularity_count=0,
            w_alpha=None,
            w_beta=None,
            class_alpha=BranchClass.NO_ASSEMBLY,
            class_beta=BranchClass.NO_ASSEMBLY,
            tool_range_alpha=None,
            tool_range_beta=None,
            extra_notes=["placeholder no-assembly edge case"],
        )
    if seed_tag == 1 and case.tool_axis is ToolAxis.B:
        return _placeholder_result(
            sample,
            case,
            branch_id="branch_open",
            branch_closed=False,
            singularity_count=1,
            w_alpha=0,
            w_beta=0,
            class_alpha=BranchClass.OPEN_BRANCH,
            class_beta=BranchClass.OPEN_BRANCH,
            tool_range_alpha=math.pi * 0.7,
            tool_range_beta=math.pi * 0.55,
            extra_notes=["placeholder open-branch edge case"],
        )
    if seed_tag == 2 and case.family is OrderedFamily.URRS:
        return _placeholder_result(
            sample,
            case,
            branch_id="branch_invalid",
            branch_closed=False,
            singularity_count=0,
            w_alpha=None,
            w_beta=None,
            class_alpha=BranchClass.INVALID,
            class_beta=BranchClass.INVALID,
            tool_range_alpha=None,
            tool_range_beta=None,
            extra_notes=["placeholder invalid geometry edge case"],
        )

    if case.tool_axis is ToolAxis.A:
        w_alpha = 1 if score > 0.55 and twist_bias > 55.0 else 0
        w_beta = 1 if symmetry and twist_bias > 100.0 else 0
    else:
        w_alpha = 1 if symmetry and twist_bias > 110.0 else 0
        w_beta = 1 if score < 1.8 and twist_bias > 70.0 else 0

    class_alpha = _class_from_winding(w_alpha, score, planarish)
    class_beta = _class_from_winding(w_beta, score, planarish)
    notes: list[str] = [MOCK_PLACEHOLDER_NOTE]
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
        singularity_count=1 if class_alpha is BranchClass.CHANGE_POINT else 0,
        w_alpha=w_alpha,
        w_beta=w_beta,
        class_alpha=class_alpha,
        class_beta=class_beta,
        tool_range_alpha=(2.0 * math.pi) if w_alpha else (math.pi * (0.4 + min(score / 3.0, 0.5))),
        tool_range_beta=(2.0 * math.pi) if w_beta else (math.pi * (0.35 + min(abs(score - 1.0) / 3.0, 0.5))),
        notes=notes,
    )


def _placeholder_result(
    sample: GeometrySample,
    case: ExplorerCase,
    *,
    branch_id: str,
    branch_closed: bool,
    singularity_count: int,
    w_alpha: int | None,
    w_beta: int | None,
    class_alpha: BranchClass,
    class_beta: BranchClass,
    tool_range_alpha: float | None,
    tool_range_beta: float | None,
    extra_notes: list[str],
) -> BranchResult:
    return BranchResult(
        sample_id=sample.sample_id,
        case=case,
        branch_id=branch_id,
        branch_closed=branch_closed,
        singularity_count=singularity_count,
        w_alpha=w_alpha,
        w_beta=w_beta,
        class_alpha=class_alpha,
        class_beta=class_beta,
        tool_range_alpha=tool_range_alpha,
        tool_range_beta=tool_range_beta,
        notes=[MOCK_PLACEHOLDER_NOTE, *extra_notes],
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


def summarize_winding_pairs(results: Iterable[BranchResult]) -> dict[str, int]:
    """Count mock winding pairs as strings like '(0,1)' or '(none,none)'."""
    counter: Counter[str] = Counter()
    for result in results:
        alpha = "none" if result.w_alpha is None else str(result.w_alpha)
        beta = "none" if result.w_beta is None else str(result.w_beta)
        counter[f"({alpha},{beta})"] += 1
    return dict(sorted(counter.items()))
