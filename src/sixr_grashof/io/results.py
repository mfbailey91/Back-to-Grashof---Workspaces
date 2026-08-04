"""Serialize and load experiment result records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sixr_grashof.io.schemas import ExperimentRecord


def write_records_json(records: list[ExperimentRecord], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [r.to_dict() for r in records]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_json(data: Any, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
