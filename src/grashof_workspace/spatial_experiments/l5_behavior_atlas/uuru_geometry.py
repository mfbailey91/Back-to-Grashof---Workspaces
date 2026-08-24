"""Full frozen-geometry serialization for the current exact R3A UURU child.

The E0 geometry payload deliberately excludes campaign / leaf identifiers.  Those
belong to source provenance, not mechanism geometry.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from grashof_workspace.spatial_experiments.axis_geometry import AxisLine
from grashof_workspace.spatial_experiments.l5_reconstruction.spherical_chart import (
    SphericalClosureChart,
)
from grashof_workspace.spatial_experiments.l5_reconstruction.uuru_leaf import (
    ClosedUURULeafProblem,
)
from grashof_workspace.spatial_experiments.open_chain import OpenChainModel
from grashof_workspace.spatial_experiments.serial_chain import SerialRevoluteChain

from .models import MechanismGeometryRecord

UURU_GEOMETRY_SCHEMA_ID = "uuru_frozen_geometry_v1"


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be a JSON object")
    return value


def _vec3(value: Any, *, field: str) -> tuple[float, float, float]:
    values = list(value)
    if len(values) != 3:
        raise ValueError(f"{field} must have length 3")
    return (float(values[0]), float(values[1]), float(values[2]))


def _mat3(
    value: Any,
    *,
    field: str,
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    rows = list(value)
    if len(rows) != 3:
        raise ValueError(f"{field} must be 3x3")
    return (
        _vec3(rows[0], field=f"{field}[0]"),
        _vec3(rows[1], field=f"{field}[1]"),
        _vec3(rows[2], field=f"{field}[2]"),
    )


def _chain_payload(
    chain: SerialRevoluteChain,
    *,
    include_joint_contract: tuple[tuple[str, ...], tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "home_axes": [
            {"r": list(axis.r), "w": list(axis.w)}
            for axis in chain.home_axes
        ],
        "p0": list(chain.p0),
        "d0": list(chain.d0),
        "R0": [list(row) for row in chain.R0],
    }
    if include_joint_contract is not None:
        kinds, roles = include_joint_contract
        payload["joint_kind_sequence"] = list(kinds)
        payload["joint_role_sequence"] = list(roles)
    return payload


def _chain_from_payload(payload: Mapping[str, Any], *, field: str) -> SerialRevoluteChain:
    axes_raw = list(payload["home_axes"])
    axes = tuple(
        AxisLine(
            _vec3(_mapping(item, field=f"{field}.home_axes[{i}]")["r"], field=f"{field}.home_axes[{i}].r"),
            _vec3(_mapping(item, field=f"{field}.home_axes[{i}]")["w"], field=f"{field}.home_axes[{i}].w"),
        )
        for i, item in enumerate(axes_raw)
    )
    return SerialRevoluteChain(
        home_axes=axes,
        p0=_vec3(payload["p0"], field=f"{field}.p0"),
        d0=_vec3(payload["d0"], field=f"{field}.d0"),
        R0=_mat3(payload["R0"], field=f"{field}.R0"),
    )


def uuru_geometry_payload(problem: ClosedUURULeafProblem) -> dict[str, Any]:
    """Return the complete E0 frozen-geometry payload for one UURU child."""

    return {
        "schema_id": UURU_GEOMETRY_SCHEMA_ID,
        "conventions": {
            "length_unit": "m",
            "angle_unit": "rad",
            "frame": "W",
        },
        "source_chain": _chain_payload(
            problem.source.chain,
            include_joint_contract=(
                problem.source.joint_kind_sequence,
                problem.source.joint_role_sequence,
            ),
        ),
        "independent_chain": _chain_payload(problem.independent_chain),
        "virtual_closure": {
            "chart_id": problem.chart.chart_id,
            "sequence": problem.chart.sequence,
            "basis": np.asarray(problem.chart.basis, dtype=float).tolist(),
            "reference": np.asarray(problem.chart.reference, dtype=float).tolist(),
            "singularity_tol": float(problem.chart.singularity_tol),
            "lambda_fixed": float(problem.lambda_fixed),
        },
        "fixed_position": {
            "p_star": list(problem.p_star),
        },
        "child_contract": {
            "joint_kind_sequence": list(problem.joint_kind_sequence),
            "joint_role_sequence": list(problem.joint_role_sequence),
            "ambient_dimension": int(problem.ambient_dimension),
            "constraint_dimension": int(problem.constraint_dimension),
            "periodic_coordinates": list(problem.periodic_coordinates),
        },
    }


def geometry_record_from_uuru_problem(
    problem: ClosedUURULeafProblem,
) -> MechanismGeometryRecord:
    """Serialize a frozen UURU problem into the A0 canonical geometry record."""

    return MechanismGeometryRecord.from_payload(
        geometry_schema_id=UURU_GEOMETRY_SCHEMA_ID,
        payload=uuru_geometry_payload(problem),
    )


def reconstruct_uuru_problem(
    record: MechanismGeometryRecord,
    *,
    problem_id: str = "E0_RECONSTRUCTED_UURU",
    source_chain_id: str = "E0_RECONSTRUCTED_SOURCE",
) -> ClosedUURULeafProblem:
    """Recreate the UURU closure problem from the E0 geometry payload alone."""

    if record.geometry_schema_id != UURU_GEOMETRY_SCHEMA_ID:
        raise ValueError(
            f"unsupported geometry schema {record.geometry_schema_id!r}; "
            f"expected {UURU_GEOMETRY_SCHEMA_ID!r}"
        )
    root = _mapping(record.payload(), field="geometry")
    if str(root.get("schema_id")) != UURU_GEOMETRY_SCHEMA_ID:
        raise ValueError("geometry payload schema_id does not match record schema")

    source_payload = _mapping(root["source_chain"], field="source_chain")
    source_chain = _chain_from_payload(source_payload, field="source_chain")
    source_kinds = tuple(str(v) for v in source_payload["joint_kind_sequence"])
    source_roles = tuple(str(v) for v in source_payload["joint_role_sequence"])
    source = OpenChainModel(
        architecture_id=source_chain_id,
        chain=source_chain,
        joint_kind_sequence=source_kinds,
        joint_role_sequence=source_roles,
        notes=("Reconstructed from E0 UURU frozen geometry.",),
    )

    independent_payload = _mapping(root["independent_chain"], field="independent_chain")
    independent_chain = _chain_from_payload(
        independent_payload,
        field="independent_chain",
    )

    closure = _mapping(root["virtual_closure"], field="virtual_closure")
    chart = SphericalClosureChart(
        chart_id=str(closure["chart_id"]),
        basis=np.asarray(_mat3(closure["basis"], field="virtual_closure.basis"), dtype=float),
        reference=np.asarray(
            _mat3(closure["reference"], field="virtual_closure.reference"),
            dtype=float,
        ),
        sequence=str(closure["sequence"]),
        singularity_tol=float(closure["singularity_tol"]),
    )

    fixed_position = _mapping(root["fixed_position"], field="fixed_position")
    contract = _mapping(root["child_contract"], field="child_contract")
    periodic = tuple(bool(v) for v in contract["periodic_coordinates"])
    kinds = tuple(str(v) for v in contract["joint_kind_sequence"])
    roles = tuple(str(v) for v in contract["joint_role_sequence"])

    return ClosedUURULeafProblem(
        source=source,
        independent_chain=independent_chain,
        chart=chart,
        lambda_fixed=float(closure["lambda_fixed"]),
        p_star=_vec3(fixed_position["p_star"], field="fixed_position.p_star"),
        problem_id=problem_id,
        ambient_dimension=int(contract["ambient_dimension"]),
        constraint_dimension=int(contract["constraint_dimension"]),
        periodic_coordinates=periodic,
        joint_kind_sequence=kinds,
        joint_role_sequence=roles,
    )
