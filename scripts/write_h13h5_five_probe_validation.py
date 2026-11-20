#!/usr/bin/env python3
"""Record the H13H-5 five-probe validation outcome.

When H13H-4 leaves no candidate policy, this receipt retains that blocker and
does not evaluate P2/P3 or invent a frozen numerical policy.
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

H13H4_JSON = Path("results/l5_reconstruction/h13h/h13h4_convergence_study.json")
RECEIPT_JSON = Path("results/l5_reconstruction/h13h/h13h5_five_probe_validation.json")
RECEIPT_MD = Path("docs/methods/R3A_H13H_FIVE_PROBE_VALIDATION.md")
SCHEMA = "r3a_h13h5_five_probe_validation_v1"


class ValidationError(RuntimeError):
    """The H13H-5 validation receipt could not be written."""


def _git_text(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def build_receipt() -> dict[str, Any]:
    path = ROOT / H13H4_JSON
    if not path.is_file():
        raise ValidationError(f"missing prerequisite {H13H4_JSON}")
    h13h4 = json.loads(path.read_text(encoding="utf-8"))
    if h13h4.get("schema_version") != "r3a_h13h4_convergence_study_v1":
        raise ValidationError("H13H-4 receipt schema mismatch")
    if h13h4.get("candidate_policy") is not None:
        raise ValidationError(
            "H13H-4 reports a candidate_policy; this blocked-validation path "
            "is only for a null candidate"
        )
    blocker = h13h4.get("blocker")
    if not isinstance(blocker, dict) or blocker.get("status") != "REQUIRED_INTERVALS_UNRESOLVED":
        raise ValidationError("H13H-4 blocker is missing or not REQUIRED_INTERVALS_UNRESOLVED")
    return {
        "schema_version": SCHEMA,
        "work_package": "H13H-5",
        "diagnostic_only": True,
        "accepted_reconstruction": False,
        "source_policy_validated": False,
        "h12_hub_replaced": False,
        "natural_budget_changed": False,
        "h13g_pilot_config_changed": False,
        "frozen_policy": None,
        "p2_p3_evaluated": False,
        "held_out_validation_claimed": False,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inspection": {
            "head": _git_text(["rev-parse", "HEAD"]),
            "branch": _git_text(["rev-parse", "--abbrev-ref", "HEAD"]),
        },
        "prerequisite": {
            "work_package": "H13H-4",
            "path": H13H4_JSON.as_posix(),
            "sha256": file_sha256(path),
            "schema_version": h13h4.get("schema_version"),
            "candidate_policy": None,
            "executed_profiles": h13h4.get("executed_profiles"),
        },
        "blocker": blocker,
        "next_action": (
            "Reopen source diagnosis on projection-backed MIXED_UNRESOLVED bins "
            "and the remaining P5 budget/raster failures before any freeze."
        ),
        "configured_probe_order": [
            "P1_DEEP_COMPLETE",
            "P2_INNER_COMPLETE",
            "P3_INNER_INCOMPLETE",
            "P4_OUTER_COMPLETE",
            "P5_OUTER_INCOMPLETE",
        ],
        "diagnostic_probe_ids": [
            "P1_DEEP_COMPLETE",
            "P4_OUTER_COMPLETE",
            "P5_OUTER_INCOMPLETE",
        ],
        "unevaluated_probe_ids": [
            "P2_INNER_COMPLETE",
            "P3_INNER_INCOMPLETE",
        ],
    }


def render_markdown(receipt: dict[str, Any]) -> str:
    blocker = receipt["blocker"]
    inspection = receipt["inspection"]
    prerequisite = receipt["prerequisite"]
    return "\n".join(
        [
            "# R3A-H13H-5 five-probe validation",
            "",
            (
                "**Status:** BLOCKED VALIDATION. No frozen policy. P2/P3 were not "
                "evaluated. Source policy validated: false. `accepted_reconstruction`: false."
            ),
            "",
            (
                "**Authority:** This file is the H13H-5 five-probe validation receipt. "
                "[R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md](R3A_H13H_SOURCE_CONTROL_CONVERGENCE.md) "
                "remains the sprint plan. [CURRENT_STATUS.md](../CURRENT_STATUS.md) remains the "
                "scientific status ledger. Machine-readable copy: "
                "[h13h5_five_probe_validation.json]"
                "(../../results/l5_reconstruction/h13h/h13h5_five_probe_validation.json)."
            ),
            "",
            "Regenerate with:",
            "",
            "```bash",
            "PYTHONPATH=src python scripts/write_h13h5_five_probe_validation.py",
            "```",
            "",
            "## 1. Prerequisite",
            "",
            (
                f"Inspection HEAD `{inspection['head']}` on `{inspection['branch']}`. "
                f"H13H-4 receipt `{prerequisite['path']}` "
                f"(sha256 `{prerequisite['sha256']}`) reports `candidate_policy: null`."
            ),
            "",
            f"Executed H13H-4 profiles: `{prerequisite['executed_profiles']}`.",
            "",
            "## 2. Validation decision",
            "",
            "`frozen_policy` is `null`. `p2_p3_evaluated` is `false`. "
            "`held_out_validation_claimed` is `false`.",
            "",
            (
                f"Blocker `{blocker['status']}` after `{blocker['after_profile']}`. "
                f"{blocker['detail']}"
            ),
            "",
            f"Remaining diagnostic-probe statuses: `{blocker.get('remaining')}`.",
            "",
            (
                "Configured probe order remains "
                f"`{receipt['configured_probe_order']}`. "
                f"Unevaluated probes: `{receipt['unevaluated_probe_ids']}`."
            ),
            "",
            "## 3. Next action",
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
