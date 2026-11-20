#!/usr/bin/env python3
"""Record the H13H-6 documented-stop evidence package.

When H13H-5 leaves no frozen policy, this closeout packages the H13H-0–5
evidence chain with the precise blocker and does not invent a frozen config
or authorize H13I.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grashof_workspace.spatial_experiments.l5_reconstruction.models import (
    file_sha256,
    json_dumps_strict,
)

CHAIN: tuple[tuple[str, Path, str], ...] = (
    (
        "H13H-0",
        Path("results/l5_reconstruction/h13h/h13h0_baseline_receipt.json"),
        "r3a_h13h0_baseline_receipt_v1",
    ),
    (
        "H13H-2",
        Path("results/l5_reconstruction/h13h/h13h2_continuation_diagnosis.json"),
        "r3a_h13h2_continuation_diagnosis_v1",
    ),
    (
        "H13H-3",
        Path("results/l5_reconstruction/h13h/h13h3_raster_diagnosis.json"),
        "r3a_h13h3_raster_diagnosis_v1",
    ),
    (
        "H13H-4",
        Path("results/l5_reconstruction/h13h/h13h4_convergence_study.json"),
        "r3a_h13h4_convergence_study_v1",
    ),
    (
        "H13H-5",
        Path("results/l5_reconstruction/h13h/h13h5_five_probe_validation.json"),
        "r3a_h13h5_five_probe_validation_v1",
    ),
)

RECEIPT_JSON = Path("results/l5_reconstruction/h13h/h13h6_documented_stop.json")
RECEIPT_MD = Path("docs/methods/R3A_H13H_DOCUMENTED_STOP.md")
SCHEMA = "r3a_h13h6_documented_stop_v1"
NEXT_ACTION = (
    "Reopen source diagnosis on projection-backed MIXED_UNRESOLVED bins "
    "and the remaining P5 budget/raster failures before any freeze."
)


class StopError(RuntimeError):
    """The H13H-6 documented-stop receipt could not be written."""


def _git_text(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _load_json(rel: Path) -> dict[str, Any]:
    path = ROOT / rel
    if not path.is_file():
        raise StopError(f"missing prerequisite {rel.as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_receipt() -> dict[str, Any]:
    loaded: dict[str, dict[str, Any]] = {}
    evidence_chain: list[dict[str, Any]] = []
    for work_package, rel, schema in CHAIN:
        payload = _load_json(rel)
        if payload.get("schema_version") != schema:
            raise StopError(f"{work_package} schema mismatch for {rel.as_posix()}")
        loaded[work_package] = payload
        evidence_chain.append(
            {
                "work_package": work_package,
                "path": rel.as_posix(),
                "sha256": file_sha256(ROOT / rel),
                "schema_version": schema,
            }
        )

    h13h0 = loaded["H13H-0"]
    h13h4 = loaded["H13H-4"]
    h13h5 = loaded["H13H-5"]

    if h13h5.get("frozen_policy") is not None:
        raise StopError("H13H-5 reports a frozen_policy; documented-stop path requires null")
    if h13h4.get("candidate_policy") is not None:
        raise StopError("H13H-4 reports a candidate_policy; documented-stop path requires null")
    blocker = h13h5.get("blocker")
    if not isinstance(blocker, dict) or blocker.get("status") != "REQUIRED_INTERVALS_UNRESOLVED":
        raise StopError("H13H-5 blocker is missing or not REQUIRED_INTERVALS_UNRESOLVED")
    if blocker != h13h4.get("blocker"):
        raise StopError("H13H-5 blocker does not match H13H-4 blocker")

    protected = h13h0.get("protected")
    if not isinstance(protected, dict):
        raise StopError("H13H-0 protected identity block is missing")

    gates = h13h4.get("gates")
    if not isinstance(gates, dict):
        raise StopError("H13H-4 gates are missing")
    attempted_profiles: list[dict[str, Any]] = []
    for profile_id in h13h4.get("executed_profiles") or []:
        gate = gates.get(profile_id)
        if not isinstance(gate, dict):
            raise StopError(f"H13H-4 missing gate for executed profile {profile_id}")
        attempted_profiles.append(
            {
                "profile_id": profile_id,
                "axis": gate.get("axis"),
                "config": gate.get("config"),
                "declared": gate.get("declared"),
                "passed": gate.get("passed"),
            }
        )

    return {
        "schema_version": SCHEMA,
        "work_package": "H13H-6",
        "sprint": "R3A-H13H",
        "closeout_kind": "documented_stop",
        "diagnostic_only": True,
        "accepted_reconstruction": False,
        "source_policy_validated": False,
        "h12_hub_replaced": False,
        "natural_budget_changed": False,
        "h13g_pilot_config_changed": False,
        "frozen_policy": None,
        "frozen_config_created": False,
        "adr": "ADR-063",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inspection": {
            "head": _git_text(["rev-parse", "HEAD"]),
            "branch": _git_text(["rev-parse", "--abbrev-ref", "HEAD"]),
        },
        "evidence_chain": evidence_chain,
        "protected": protected,
        "attempted_settings": {
            "executed_profiles": h13h4.get("executed_profiles"),
            "profiles": attempted_profiles,
            "skipped_axes": h13h4.get("skipped_axes"),
            "candidate_policy": None,
        },
        "failure_classification": {
            "status": blocker["status"],
            "after_profile": blocker.get("after_profile"),
            "summary": blocker.get("detail"),
            "remaining": blocker.get("remaining"),
            "three_probe_candidate": False,
            "p2_p3_evaluated": False,
            "unevaluated_probe_ids": h13h5.get("unevaluated_probe_ids"),
            "notes": [
                "P1 and P4 retain projection-backed MIXED_UNRESOLVED required bins.",
                "P5 retains BUDGET_EXHAUSTED and MIXED_UNRESOLVED with raster failures.",
                "Continuation escalation through 192 steps did not clear required intervals.",
                "Section 3.3 cross-run comparisons were not formed.",
            ],
        },
        "repairs_landed": [
            {
                "work_package": "H13H-2",
                "result": "No demonstrated continuation solver defect; production solver unchanged.",
            },
            {
                "work_package": "H13H-3",
                "result": (
                    "Chord-section midpoint correction for raster midpoints; "
                    "open-ray closing gaps remain unresolved."
                ),
            },
            {
                "work_package": "Gate-B",
                "result": (
                    "Unknown source-policy tokens reject; "
                    "continuation_max_steps_per_ray is an explicit opt-in."
                ),
            },
        ],
        "blocker": blocker,
        "h13i_handoff": {
            "authorized": False,
            "blocker": "H13H source-policy validation unmet",
            "prerequisites": [
                "Resolve projection-backed MIXED_UNRESOLVED bins on diagnostic probes.",
                "Clear remaining P5 BUDGET_EXHAUSTED and raster-failure obligations.",
                "Obtain one candidate policy that passes P1/P4/P5 and five-probe validation.",
            ],
            "remaining_limitations": [
                "No frozen H13H numerical policy exists.",
                "P2 and P3 were not evaluated under a candidate policy.",
                "The H12 hub remains the authoritative full closeout.",
                "Natural UURU interpretation and all-column H13I packaging are not authorized.",
            ],
        },
        "next_action": NEXT_ACTION,
    }


def render_markdown(receipt: dict[str, Any]) -> str:
    blocker = receipt["blocker"]
    inspection = receipt["inspection"]
    handoff = receipt["h13i_handoff"]
    chain_lines = [
        (
            f"- `{item['work_package']}`: `{item['path']}` "
            f"(sha256 `{item['sha256']}`)"
        )
        for item in receipt["evidence_chain"]
    ]
    profile_lines = [
        (
            f"- `{item['profile_id']}` axis `{item['axis']}` "
            f"declared `{item['declared']}` passed=`{item['passed']}`"
        )
        for item in receipt["attempted_settings"]["profiles"]
    ]
    skipped = receipt["attempted_settings"]["skipped_axes"] or []
    skipped_lines = [
        f"- `{item['axis']}`: {item['reason']}" for item in skipped
    ]
    repair_lines = [
        f"- `{item['work_package']}`: {item['result']}"
        for item in receipt["repairs_landed"]
    ]
    prereq_lines = [f"- {item}" for item in handoff["prerequisites"]]
    limit_lines = [f"- {item}" for item in handoff["remaining_limitations"]]
    hub = receipt["protected"]["h12_hub"]
    return "\n".join(
        [
            "# R3A-H13H-6 documented stop",
            "",
            (
                "**Status:** DOCUMENTED STOP. No frozen policy. No frozen config. "
                "H13I not authorized. Source policy validated: false. "
                "`accepted_reconstruction`: false."
            ),
            "",
            (
                "**Authority:** This file is the H13H-6 documented-stop receipt. "
                "[R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) "
                "is the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) is the scientific "
                "status ledger. Decision: [ADR-063](../reference/DECISIONS.md#adr-063--h13h-"
                "closes-as-a-documented-source-control-stop). Machine-readable copy: "
                "[h13h6_documented_stop.json]"
                "(../../results/l5_reconstruction/h13h/h13h6_documented_stop.json)."
            ),
            "",
            "Regenerate with:",
            "",
            "```bash",
            "PYTHONPATH=src python scripts/write_h13h6_documented_stop.py",
            "```",
            "",
            "## 1. Closeout identity",
            "",
            (
                f"Inspection HEAD `{inspection['head']}` on `{inspection['branch']}`. "
                f"`closeout_kind` is `{receipt['closeout_kind']}`. "
                f"`frozen_config_created` is `{receipt['frozen_config_created']}`."
            ),
            "",
            (
                f"Blocker `{blocker['status']}` after `{blocker['after_profile']}`. "
                f"{blocker['detail']}"
            ),
            "",
            f"Remaining diagnostic-probe statuses: `{blocker.get('remaining')}`.",
            "",
            "## 2. Evidence chain",
            "",
            *chain_lines,
            "",
            "## 3. Protected H12 identity",
            "",
            (
                f"H12 hub `{hub['path']}` file sha256 `{hub['file_sha256']}`; "
                f"raw bundle sha256 `{hub['raw_bundle_sha256']}`; "
                f"campaign blocker `{hub['campaign_blocker']}`; "
                f"`accepted_reconstruction` `{hub['accepted_reconstruction']}`."
            ),
            "",
            "Protected configs and hub hashes are copied from the H13H-0 baseline receipt. "
            "This package does not mutate the hub.",
            "",
            "## 4. Attempted settings",
            "",
            *profile_lines,
            "",
            "Skipped axes:",
            "",
            *skipped_lines,
            "",
            "## 5. Failure classification",
            "",
            (
                "No three-probe candidate. P2/P3 were not evaluated. "
                "Projection-backed MIXED_UNRESOLVED bins remain on P1/P4; "
                "P5 retains budget exhaustion, MIXED_UNRESOLVED, and raster failures."
            ),
            "",
            "## 6. Repairs landed",
            "",
            *repair_lines,
            "",
            "## 7. H13I handoff",
            "",
            (
                f"`authorized` is `{handoff['authorized']}`. "
                f"Blocker: {handoff['blocker']}."
            ),
            "",
            "Prerequisites:",
            "",
            *prereq_lines,
            "",
            "Remaining limitations:",
            "",
            *limit_lines,
            "",
            "## 8. Next action",
            "",
            receipt["next_action"],
            "",
            "Natural continuation budgets and the committed H13G pilot config are unchanged.",
            "",
        ]
    )


def write_receipt(receipt: dict[str, Any]) -> None:
    json_path = ROOT / RECEIPT_JSON
    md_path = ROOT / RECEIPT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json_dumps_strict(receipt) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(receipt), encoding="utf-8")
    print(f"wrote {RECEIPT_JSON}")
    print(f"wrote {RECEIPT_MD}")


def main() -> None:
    write_receipt(build_receipt())


if __name__ == "__main__":
    main()
