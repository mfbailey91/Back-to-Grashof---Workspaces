from __future__ import annotations

import math
import random
from collections.abc import Iterable

from .models import GeometryDescriptor, GeometrySample, OrderedFamily

PARAMETER_INVENTORY: tuple[tuple[str, str, str], ...] = (
    ("center_distance_12", "distances", "Normalized adjacent joint-center distance L12/Lref"),
    ("center_distance_23", "distances", "Normalized adjacent joint-center distance L23/Lref"),
    ("center_distance_34", "distances", "Normalized adjacent joint-center distance L34/Lref"),
    ("twist_12_deg", "angles", "Angle between consecutive axes near joints 1 and 2"),
    ("twist_23_deg", "angles", "Angle between consecutive axes near joints 2 and 3"),
    ("twist_34_deg", "angles", "Angle between consecutive axes near joints 3 and 4"),
    ("common_normal_13", "offsets", "Shortest separation between selected nonadjacent axes 1 and 3"),
    ("common_normal_24", "offsets", "Shortest separation between selected nonadjacent axes 2 and 4"),
    ("offset_1", "offsets", "Signed offset along axis 1 to a common-normal construction"),
    ("offset_2", "offsets", "Signed offset along axis 2 to a common-normal construction"),
    (
        "axis_to_center_1",
        "axis-center descriptors",
        "Distance from selected revolute axis 1 to an opposite joint center",
    ),
    (
        "axis_to_center_2",
        "axis-center descriptors",
        "Distance from selected revolute axis 2 to an opposite joint center",
    ),
    ("tetra_volume", "shape descriptors", "Signed normalized tetrahedral volume built from four reference points"),
    ("coplanarity_residual", "shape descriptors", "Near-zero indicates nearly planar center geometry"),
    ("chirality", "flags", "Right- or left-handed center geometry flag"),
    ("has_intersection_pair", "flags", "Boolean flag for exact pairwise axis intersection"),
    ("has_mirror_symmetry", "flags", "Boolean flag for mirror-symmetric construction"),
)


def generate_geometry_samples(
    family: OrderedFamily,
    *,
    count: int,
    seed: int = 0,
) -> list[GeometrySample]:
    rng = random.Random(seed + hash(family.value) % 10000)
    samples: list[GeometrySample] = []
    for idx in range(count):
        sample_seed = rng.randint(0, 10_000_000)
        sample_rng = random.Random(sample_seed)
        raw_parameters = {
            "l12": round(sample_rng.uniform(0.5, 2.5), 6),
            "l23": round(sample_rng.uniform(0.5, 2.5), 6),
            "l34": round(sample_rng.uniform(0.5, 2.5), 6),
            "twist12": round(sample_rng.uniform(10.0, 170.0), 6),
            "twist23": round(sample_rng.uniform(10.0, 170.0), 6),
            "twist34": round(sample_rng.uniform(10.0, 170.0), 6),
            "offset1": round(sample_rng.uniform(-1.0, 1.0), 6),
            "offset2": round(sample_rng.uniform(-1.0, 1.0), 6),
            "common13": round(sample_rng.uniform(0.0, 1.5), 6),
            "common24": round(sample_rng.uniform(0.0, 1.5), 6),
        }
        chirality = "right" if sample_rng.random() >= 0.5 else "left"
        tetra_volume = (raw_parameters["l12"] * raw_parameters["l23"] * raw_parameters["l34"]) / 6.0
        tetra_volume *= math.sin(math.radians(raw_parameters["twist23"]))
        descriptors = [
            GeometryDescriptor("center_distance_12", raw_parameters["l12"], "distances", "Normalized adjacent joint-center distance L12/Lref"),
            GeometryDescriptor("center_distance_23", raw_parameters["l23"], "distances", "Normalized adjacent joint-center distance L23/Lref"),
            GeometryDescriptor("center_distance_34", raw_parameters["l34"], "distances", "Normalized adjacent joint-center distance L34/Lref"),
            GeometryDescriptor("twist_12_deg", raw_parameters["twist12"], "angles", "Angle between consecutive axes near joints 1 and 2"),
            GeometryDescriptor("twist_23_deg", raw_parameters["twist23"], "angles", "Angle between consecutive axes near joints 2 and 3"),
            GeometryDescriptor("twist_34_deg", raw_parameters["twist34"], "angles", "Angle between consecutive axes near joints 3 and 4"),
            GeometryDescriptor("common_normal_13", raw_parameters["common13"], "offsets", "Shortest separation between selected nonadjacent axes 1 and 3"),
            GeometryDescriptor("common_normal_24", raw_parameters["common24"], "offsets", "Shortest separation between selected nonadjacent axes 2 and 4"),
            GeometryDescriptor("offset_1", raw_parameters["offset1"], "offsets", "Signed offset along axis 1 to a common-normal construction"),
            GeometryDescriptor("offset_2", raw_parameters["offset2"], "offsets", "Signed offset along axis 2 to a common-normal construction"),
            GeometryDescriptor("axis_to_center_1", abs(raw_parameters["offset1"]) + raw_parameters["common13"], "axis-center", "Distance from selected revolute axis 1 to an opposite joint center"),
            GeometryDescriptor("axis_to_center_2", abs(raw_parameters["offset2"]) + raw_parameters["common24"], "axis-center", "Distance from selected revolute axis 2 to an opposite joint center"),
            GeometryDescriptor("tetra_volume", tetra_volume, "shape", "Signed normalized tetrahedral volume built from four reference points"),
            GeometryDescriptor("coplanarity_residual", abs(tetra_volume), "shape", "Near-zero indicates nearly planar center geometry"),
            GeometryDescriptor("chirality", chirality, "flags", "Right- or left-handed center geometry flag"),
            GeometryDescriptor("has_intersection_pair", raw_parameters["common13"] < 0.1 or raw_parameters["common24"] < 0.1, "flags", "Boolean flag for exact pairwise axis intersection"),
            GeometryDescriptor("has_mirror_symmetry", abs(raw_parameters["l12"] - raw_parameters["l34"]) < 0.05, "flags", "Boolean flag for mirror-symmetric construction"),
        ]
        samples.append(
            GeometrySample(
                sample_id=f"{family.value.lower()}_{idx:03d}",
                family=family,
                inversion="tool_to_ground",
                seed=sample_seed,
                raw_parameters=raw_parameters,
                descriptors=descriptors,
            )
        )
    return samples


def descriptor_names() -> list[str]:
    return [name for name, _, _ in PARAMETER_INVENTORY]


def grouped_descriptor_inventory() -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = {
        "distances": [],
        "angles": [],
        "offsets": [],
        "axis-center descriptors": [],
        "shape descriptors": [],
        "flags": [],
    }
    for name, group_name, description in PARAMETER_INVENTORY:
        grouped[group_name].append((name, description))
    return grouped


def sample_descriptor_values(samples: Iterable[GeometrySample], name: str) -> list[float]:
    values: list[float] = []
    for sample in samples:
        for descriptor in sample.descriptors:
            if descriptor.name == name and isinstance(descriptor.value, (float, int)):
                values.append(float(descriptor.value))
    return values
