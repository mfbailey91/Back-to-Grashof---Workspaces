"""McCarthy–Soh / Murray–Larochelle spherical 4R classification."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Literal

MotionClass = Literal["crank", "rocker"]
GrashofFamily = Literal["grashof", "non-grashof", "change-point"]
ReductionNote = Literal["exact", "approximate", "invalid", "not_applicable"]


@dataclass(frozen=True, slots=True)
class SphericalFourBar:
    """Ordered spherical 4R angular lengths.

    Convention (Murray–Larochelle / McCarthy–Soh):

        alpha = input (driving) link
        beta  = output link  (hand-orientation link in this project)
        gamma = ground (fixed) link
        eta   = coupler link

    All angles must lie in (0, pi].
    """

    alpha: float
    beta: float
    gamma: float
    eta: float

    def __post_init__(self) -> None:
        for name, value in (
            ("alpha", self.alpha),
            ("beta", self.beta),
            ("gamma", self.gamma),
            ("eta", self.eta),
        ):
            if not (0.0 < value <= math.pi):
                raise ValueError(f"{name} must lie in (0, pi], got {value}")


@dataclass(frozen=True, slots=True)
class SphericalClassification:
    """Full classification record for one spherical four-bar state."""

    T1: float
    T2: float
    T3: float
    T4: float
    sign_tuple: tuple[int, int, int, int]
    T_product: float
    grashof_family: GrashofFamily
    linkage_type: int | None
    linkage_name: str
    equivalent_type: int | None
    wrap_around: bool
    input_motion_class: MotionClass | Literal["boundary"]
    output_motion_class: MotionClass | Literal["boundary"]
    hand_link_motion_class: MotionClass | Literal["boundary"]
    hand_orientation_link: Literal["beta"]
    is_boundary: bool
    boundary_indices: tuple[int, ...]
    dexterity_candidate_hypothesis: bool


def evaluate_T(
    linkage: SphericalFourBar,
) -> tuple[float, float, float, float]:
    """Return (T1, T2, T3, T4) for a spherical four-bar.

    Formulas (Murray and Larochelle, 1998, eqs. 26 and 30)::

        T1 = gamma - alpha + eta - beta
        T2 = gamma - alpha - eta + beta
        T3 = eta + beta - gamma - alpha
        T4 = 2*pi - (alpha + beta + gamma + eta)
    """
    a, b, g, h = linkage.alpha, linkage.beta, linkage.gamma, linkage.eta
    t1 = g - a + h - b
    t2 = g - a - h + b
    t3 = h + b - g - a
    t4 = 2.0 * math.pi - (a + b + g + h)
    return (t1, t2, t3, t4)


def _sign(value: float, *, tol: float) -> int:
    if abs(value) <= tol:
        return 0
    return 1 if value > 0.0 else -1


def input_is_crank(t1: float, t2: float, t3: float, t4: float, *, tol: float) -> bool | None:
    """Return True if input fully rotates, False if rocker, None on boundary."""
    if any(abs(v) <= tol for v in (t1, t2, t3, t4)):
        return None
    return (t1 * t2 >= 0.0) and (t3 * t4 >= 0.0)


def output_is_crank(t1: float, t2: float, t3: float, t4: float, *, tol: float) -> bool | None:
    """Return True if output fully rotates, False if rocker, None on boundary."""
    if any(abs(v) <= tol for v in (t1, t2, t3, t4)):
        return None
    return (t2 * t4 <= 0.0) and (t1 * t3 <= 0.0)


def _as_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"expected int, got {type(value)!r}")
    return value


def _as_str(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"expected str, got {type(value)!r}")
    return value


def _as_bool(value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"expected bool, got {type(value)!r}")
    return value


@lru_cache(maxsize=1)
def _load_type_table() -> dict[str, object]:
    root = resources.files("sixr_grashof").joinpath("data")
    payload = root.joinpath("mccarthy_soh_types.json").read_text(encoding="utf-8")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise TypeError("type table root must be a JSON object")
    return data


def type_table() -> list[dict[str, object]]:
    data = _load_type_table()
    types = data["types"]
    if not isinstance(types, list):
        raise TypeError("types must be a list")
    out: list[dict[str, object]] = []
    for row in types:
        if not isinstance(row, dict):
            raise TypeError("each type row must be an object")
        out.append(row)
    return out


def fixtures() -> list[dict[str, object]]:
    data = _load_type_table()
    rows = data["fixtures"]
    if not isinstance(rows, list):
        raise TypeError("fixtures must be a list")
    out: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("each fixture row must be an object")
        out.append(row)
    return out


def lookup_type(sign_tuple: tuple[int, int, int, int]) -> dict[str, object] | None:
    """Map a nonzero sign pattern to its table row, or None if not found."""
    if 0 in sign_tuple:
        return None
    for row in type_table():
        signs = row["signs"]
        if not isinstance(signs, list):
            raise TypeError("signs must be a list")
        if tuple(int(s) for s in signs) == sign_tuple:
            return row
    return None


def classify_spherical(
    linkage: SphericalFourBar,
    *,
    boundary_tol: float = 1e-12,
) -> SphericalClassification:
    """Classify a spherical four-bar; never infer dexterity from the product alone."""
    t1, t2, t3, t4 = evaluate_T(linkage)
    signs = (
        _sign(t1, tol=boundary_tol),
        _sign(t2, tol=boundary_tol),
        _sign(t3, tol=boundary_tol),
        _sign(t4, tol=boundary_tol),
    )
    product = t1 * t2 * t3 * t4
    boundary_indices = tuple(i + 1 for i, s in enumerate(signs) if s == 0)
    is_boundary = bool(boundary_indices)

    if is_boundary:
        family: GrashofFamily = "change-point"
        row = None
    elif product > 0.0:
        family = "grashof"
        row = lookup_type(signs)
    else:
        family = "non-grashof"
        row = lookup_type(signs)

    in_crank = input_is_crank(t1, t2, t3, t4, tol=boundary_tol)
    out_crank = output_is_crank(t1, t2, t3, t4, tol=boundary_tol)

    def _motion(flag: bool | None) -> MotionClass | Literal["boundary"]:
        if flag is None:
            return "boundary"
        return "crank" if flag else "rocker"

    input_class = _motion(in_crank)
    output_class = _motion(out_crank)

    linkage_type = _as_int(row["type"]) if row is not None else None
    linkage_name = _as_str(row["name"]) if row is not None else "boundary-or-unknown"
    equivalent = _as_int(row["equivalent_type"]) if row is not None else None
    wrap = _as_bool(row["wrap_around"]) if row is not None else t4 < -boundary_tol

    # Hypothesis only: types 2, 3, 10, 11 under output-hand convention.
    candidate_types = {2, 3, 10, 11}
    dexterity_candidate = (
        linkage_type in candidate_types and output_class == "crank" and not is_boundary
    )

    return SphericalClassification(
        T1=t1,
        T2=t2,
        T3=t3,
        T4=t4,
        sign_tuple=signs,
        T_product=product,
        grashof_family=family,
        linkage_type=linkage_type,
        linkage_name=linkage_name,
        equivalent_type=equivalent,
        wrap_around=wrap,
        input_motion_class=input_class,
        output_motion_class=output_class,
        hand_link_motion_class=output_class,
        hand_orientation_link="beta",
        is_boundary=is_boundary,
        boundary_indices=boundary_indices,
        dexterity_candidate_hypothesis=dexterity_candidate,
    )
