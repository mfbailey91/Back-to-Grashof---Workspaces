from __future__ import annotations

import math
import random

from .geometry import (
    PhysicalGeometrySample,
    SpatialFourBarGeometry,
    angle_deg,
    canonical_geometry,
    distance,
    line_to_line_distance,
    perturb_geometry,
    point_to_axis_distance,
    signed_tetrahedral_volume,
    stable_family_seed,
    subtract,
    dot,
)
from .models import GeometryDescriptor, OrderedFamily

PHYSICAL_DESCRIPTOR_INVENTORY: tuple[tuple[str, str, str], ...] = (
    ("center_distance_12", "distances", "L12 divided by mean loop-link center distance"),
    ("center_distance_23", "distances", "L23 divided by mean loop-link center distance"),
    ("center_distance_34", "distances", "L34 divided by mean loop-link center distance"),
    ("center_distance_41", "distances", "L41 divided by mean loop-link center distance"),
    ("diagonal_distance_13", "distances", "J1-J3 center distance divided by reference length"),
    ("diagonal_distance_24", "distances", "J2-J4 center distance divided by reference length"),
    ("twist_12_deg", "angles", "Angle between the primary motion axes at J1 and J2"),
    ("twist_23_deg", "angles", "Angle between the primary motion axes at J2 and J3"),
    ("twist_34_deg", "angles", "Angle between the primary motion axes at J3 and J4"),
    ("twist_41_deg", "angles", "Angle between the primary motion axes at J4 and J1"),
    ("tool_u_internal_angle_deg", "angles", "Angle between the two tool-U axes; should be 90 degrees"),
    ("tool_to_ground_axis_angle_deg", "angles", "Angle between tool-U primary axis and ground-joint primary axis"),
    ("common_normal_13", "offsets", "Shortest distance between primary axes J1/J3, normalized"),
    ("common_normal_24", "offsets", "Shortest distance between primary axes J2/J4, normalized"),
    ("offset_1", "offsets", "Signed J1-axis projection toward J3, normalized"),
    ("offset_2", "offsets", "Signed J2-axis projection toward J4, normalized"),
    ("axis_to_center_1", "axis-center descriptors", "Distance from J1 primary axis to J3 center, normalized"),
    ("axis_to_center_2", "axis-center descriptors", "Distance from J2 primary axis to J4 center, normalized"),
    ("tetra_volume", "shape descriptors", "Signed J1-J2-J3-J4 tetrahedral volume normalized by Lref^3"),
    ("coplanarity_residual", "shape descriptors", "Absolute normalized scalar triple product; zero is coplanar"),
    ("chirality", "flags", "Sign of the center tetrahedron: right, left, or planar"),
    ("has_intersection_pair", "flags", "Whether adjacent primary joint axes intersect within numerical tolerance"),
    ("has_mirror_symmetry", "flags", "Whether opposite center-distance pairs are approximately equal"),
    ("reference_geometry_valid", "flags", "Geometry object passes V02B structural validation"),
)


def derive_geometry_descriptors(geometry: SpatialFourBarGeometry) -> tuple[GeometryDescriptor, ...]:
    joints = geometry.joints
    c1, c2, c3, c4 = (joint.center for joint in joints)
    a1, a2, a3, a4 = (joint.primary_axis for joint in joints)
    lref = geometry.reference_length
    if lref <= 0:
        raise ValueError("reference length must be positive")

    l12 = distance(c1, c2) / lref
    l23 = distance(c2, c3) / lref
    l34 = distance(c3, c4) / lref
    l41 = distance(c4, c1) / lref
    diagonal13 = distance(c1, c3) / lref
    diagonal24 = distance(c2, c4) / lref

    volume = signed_tetrahedral_volume(c1, c2, c3, c4) / (lref**3)
    triple_residual = abs(volume * 6.0)
    chirality = "right" if volume > 1e-10 else "left" if volume < -1e-10 else "planar"

    adjacent_axis_distances = (
        line_to_line_distance(c1, a1, c2, a2),
        line_to_line_distance(c2, a2, c3, a3),
        line_to_line_distance(c3, a3, c4, a4),
        line_to_line_distance(c4, a4, c1, a1),
    )
    intersection_tol = max(1e-8, 1e-7 * lref)
    has_intersection_pair = any(value <= intersection_tol for value in adjacent_axis_distances)
    has_mirror_symmetry = abs(l12 - l34) <= 0.05 and abs(l23 - l41) <= 0.05

    tool_axes = joints[0].motion_axes
    if len(tool_axes) != 2:
        raise ValueError("tool joint must provide exactly two U axes")

    values: tuple[tuple[str, str, float | str | bool], ...] = (
        ("center_distance_12", "distances", l12),
        ("center_distance_23", "distances", l23),
        ("center_distance_34", "distances", l34),
        ("center_distance_41", "distances", l41),
        ("diagonal_distance_13", "distances", diagonal13),
        ("diagonal_distance_24", "distances", diagonal24),
        ("twist_12_deg", "angles", angle_deg(a1, a2)),
        ("twist_23_deg", "angles", angle_deg(a2, a3)),
        ("twist_34_deg", "angles", angle_deg(a3, a4)),
        ("twist_41_deg", "angles", angle_deg(a4, a1)),
        ("tool_u_internal_angle_deg", "angles", angle_deg(tool_axes[0], tool_axes[1])),
        ("tool_to_ground_axis_angle_deg", "angles", angle_deg(a1, a4)),
        ("common_normal_13", "offsets", line_to_line_distance(c1, a1, c3, a3) / lref),
        ("common_normal_24", "offsets", line_to_line_distance(c2, a2, c4, a4) / lref),
        ("offset_1", "offsets", dot(subtract(c3, c1), a1) / lref),
        ("offset_2", "offsets", dot(subtract(c4, c2), a2) / lref),
        ("axis_to_center_1", "axis-center descriptors", point_to_axis_distance(c3, c1, a1) / lref),
        ("axis_to_center_2", "axis-center descriptors", point_to_axis_distance(c4, c2, a2) / lref),
        ("tetra_volume", "shape descriptors", volume),
        ("coplanarity_residual", "shape descriptors", triple_residual),
        ("chirality", "flags", chirality),
        ("has_intersection_pair", "flags", has_intersection_pair),
        ("has_mirror_symmetry", "flags", has_mirror_symmetry),
        ("reference_geometry_valid", "flags", geometry.is_valid_reference_geometry),
    )
    descriptions = {name: description for name, _, description in PHYSICAL_DESCRIPTOR_INVENTORY}
    return tuple(
        GeometryDescriptor(name=name, value=value, group=group, description=descriptions[name])
        for name, group, value in values
    )


def physical_descriptor_inventory_by_group() -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for name, group, description in PHYSICAL_DESCRIPTOR_INVENTORY:
        grouped.setdefault(group, []).append((name, description))
    return grouped


def generate_physical_geometry_samples(
    family: OrderedFamily,
    *,
    count: int,
    seed: int = 0,
) -> list[PhysicalGeometrySample]:
    if count < 1:
        return []
    canonical = canonical_geometry(family)
    stable_seed = seed * 1009 + stable_family_seed(family)
    rng = random.Random(stable_seed)
    samples: list[PhysicalGeometrySample] = []
    for index in range(count):
        if index == 0:
            geometry = canonical
            sample_seed = stable_seed
        else:
            sample_seed = rng.randint(0, 2_147_483_647)
            geometry = perturb_geometry(canonical, seed=sample_seed)
        samples.append(
            PhysicalGeometrySample(
                sample_id=f"{family.value.lower()}_physical_{index:03d}",
                family=family,
                inversion="tool_to_ground",
                seed=sample_seed,
                geometry=geometry,
                descriptors=derive_geometry_descriptors(geometry),
            )
        )
    return samples


def validate_physical_sample(sample: PhysicalGeometrySample) -> list[str]:
    errors = sample.geometry.validation_errors()
    descriptors = sample.descriptor_map()
    if descriptors.get("reference_geometry_valid") is not True:
        errors.append("descriptor does not report valid reference geometry")
    tool_angle = float(descriptors["tool_u_internal_angle_deg"])
    if not math.isclose(tool_angle, 90.0, abs_tol=1e-7):
        errors.append(f"tool U internal angle is {tool_angle}, expected 90")
    return errors
