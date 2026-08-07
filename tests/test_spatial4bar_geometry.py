from grashof_workspace.spatial4bar_explorer.geometry import (
    JointKind,
    canonical_geometry,
    distance,
)
from grashof_workspace.spatial4bar_explorer.geometry_descriptors import (
    derive_geometry_descriptors,
    generate_physical_geometry_samples,
    validate_physical_sample,
)
from grashof_workspace.spatial4bar_explorer.geometry_readouts import write_sprint02b_html
from grashof_workspace.spatial4bar_explorer.models import OrderedFamily, dataclass_to_jsonable


def test_canonical_geometry_matches_all_six_families() -> None:
    for family in OrderedFamily:
        geometry = canonical_geometry(family)
        assert geometry.is_valid_reference_geometry
        assert tuple(joint.kind.value for joint in geometry.joints) == tuple(family.value)
        assert geometry.joints[0].kind is JointKind.U
        assert len(geometry.joints[0].motion_axes) == 2
        assert not geometry.validation_errors()


def test_descriptors_are_measured_from_geometry() -> None:
    geometry = canonical_geometry(OrderedFamily.UUUR)
    descriptors = {descriptor.name: descriptor.value for descriptor in derive_geometry_descriptors(geometry)}
    direct_l12 = distance(geometry.joints[0].center, geometry.joints[1].center) / geometry.reference_length
    assert abs(float(descriptors["center_distance_12"]) - direct_l12) < 1e-12
    assert abs(float(descriptors["tool_u_internal_angle_deg"]) - 90.0) < 1e-9
    assert descriptors["reference_geometry_valid"] is True
    assert "center_distance_41" in descriptors
    assert "diagonal_distance_13" in descriptors


def test_physical_sampling_is_deterministic_and_valid() -> None:
    first = generate_physical_geometry_samples(OrderedFamily.URSR, count=3, seed=22)
    second = generate_physical_geometry_samples(OrderedFamily.URSR, count=3, seed=22)
    assert [sample.seed for sample in first] == [sample.seed for sample in second]
    assert first[1].geometry == second[1].geometry
    assert all(sample.provenance == "physical_geometry_v02b" for sample in first)
    assert all(not validate_physical_sample(sample) for sample in first)


def test_json_conversion_supports_geometry_tuples() -> None:
    sample = generate_physical_geometry_samples(OrderedFamily.USRR, count=1, seed=3)[0]
    payload = dataclass_to_jsonable(sample)
    assert isinstance(payload, dict)
    assert isinstance(payload["geometry"]["joints"], list)
    assert isinstance(payload["geometry"]["joints"][0]["center"], list)
    assert payload["geometry"]["joints"][0]["kind"] == "U"


def test_v02b_html_marks_physical_geometry_and_no_closure(tmp_path) -> None:
    samples = []
    image_map = {}
    for family in OrderedFamily:
        family_samples = generate_physical_geometry_samples(family, count=2, seed=5)
        samples.extend(family_samples)
        image_map[family_samples[0].sample_id] = f"figures/{family.value.lower()}_canonical.png"
        image_map[family_samples[1].sample_id] = f"figures/{family.value.lower()}_sample.png"
    write_sprint02b_html(
        tmp_path,
        samples,
        image_by_sample=image_map,
        json_path="data/physical_geometry_samples.json",
    )
    html = (tmp_path / "sprint_02b_physical_geometry.html").read_text(encoding="utf-8")
    assert "PHYSICAL GEOMETRY / NO CLOSURE SOLVE YET" in html
    assert "must not be used as crank evidence" in html
    assert "physical_geometry_v02b" in html
    for family in OrderedFamily:
        assert family.value in html
