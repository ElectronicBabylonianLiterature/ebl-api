import json

import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.map_artifact_repository import (
    MapArtifactRepository,
    SiteMapLocation,
)
from ebl.fragmentarium.application.map_artifact_storage import publish_artifact_set
from ebl.fragmentarium.application.map_paths import MAP_DATA_DIR
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)


def _mapping(findspot_id: object, **extra: object) -> dict[str, object]:
    return {
        "findspotId": findspot_id,
        "polygonIds": ["assur-a"],
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": "test source",
        "sourceRevision": "test revision",
        **extra,
    }


def _publish(tmp_path, site_id: str, mappings: object) -> None:
    prefix = site_id.lower()
    filename = f"{prefix}_findspot_polygon_mappings.json"
    publish_artifact_set(
        tmp_path,
        prefix,
        "test revision",
        {filename: json.dumps(mappings)},
    )


def test_default_data_directory_is_absolute():
    assert MAP_DATA_DIR.is_absolute()


def test_loads_strict_mapping_and_preserves_site_identity(tmp_path):
    _publish(tmp_path, "ASSUR", [_mapping(17)])

    assert MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR") == {
        17: SiteMapLocation(
            site_id="ASSUR",
            location=MapLocation(
                polygon_ids=("assur-a",),
                location_precision=MapLocationPrecision.EXCAVATION_AREA,
                match_method=MapLocationMatchMethod.VERIFIED_SOURCE,
                source="test source",
                source_revision="test revision",
            ),
        )
    }


def test_combines_distinct_site_mappings_and_lists_manifest_activated_sites(tmp_path):
    _publish(tmp_path, "ASSUR", [_mapping(17)])
    _publish(tmp_path, "URUK", [_mapping(18)])
    repository = MapArtifactRepository(tmp_path)

    assert repository.known_site_ids() == ("ASSUR", "URUK")
    assert {
        findspot_id: site_location.site_id
        for findspot_id, site_location in repository.load_map_locations(
            ("ASSUR", "URUK")
        ).items()
    } == {17: "ASSUR", 18: "URUK"}


def test_default_load_uses_only_manifest_activated_sites(tmp_path):
    _publish(tmp_path, "ASSUR", [_mapping(17)])

    locations = MapArtifactRepository(tmp_path).load_map_locations()

    assert {findspot_id: item.site_id for findspot_id, item in locations.items()} == {
        17: "ASSUR"
    }


@pytest.mark.parametrize("findspot_id", [True, "17", -1, 2**63])
def test_rejects_invalid_findspot_id(tmp_path, findspot_id):
    _publish(tmp_path, "ASSUR", [_mapping(findspot_id)])

    with pytest.raises(ValueError, match="invalid findspotId"):
        MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR")


def test_rejects_unknown_mapping_fields_after_extracting_findspot_id(tmp_path):
    _publish(tmp_path, "ASSUR", [_mapping(17, unexpected="value")])

    with pytest.raises(ValidationError, match="Unknown field"):
        MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR")


def test_rejects_non_array_artifact(tmp_path):
    _publish(tmp_path, "ASSUR", {"findspotId": 17})

    with pytest.raises(ValueError, match="must be a JSON array"):
        MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR")


@pytest.mark.parametrize("entry", [17, {"polygonIds": ["assur-a"]}])
def test_rejects_non_object_or_missing_findspot_id(tmp_path, entry):
    _publish(tmp_path, "ASSUR", [entry])

    with pytest.raises(ValueError, match="JSON object|has no findspotId"):
        MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR")


def test_rejects_duplicate_findspot_ids_within_site(tmp_path):
    _publish(tmp_path, "ASSUR", [_mapping(17), _mapping(17)])

    with pytest.raises(ValueError, match="Duplicate findspot ID 17 in ASSUR"):
        MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR")


def test_rejects_duplicate_findspot_ids_across_sites(tmp_path):
    _publish(tmp_path, "ASSUR", [_mapping(17)])
    _publish(tmp_path, "URUK", [_mapping(17)])

    with pytest.raises(ValueError, match="across sites ASSUR and URUK"):
        MapArtifactRepository(tmp_path).load_map_locations(("ASSUR", "URUK"))


def test_rejects_missing_configured_site_artifact(tmp_path):
    with pytest.raises(FileNotFoundError, match="manifest does not exist"):
        MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR")


def test_rejects_unknown_site(tmp_path):
    with pytest.raises(ValueError, match="Unknown map site ID"):
        MapArtifactRepository(tmp_path).load_site_map_locations("UNKNOWN")


def test_rejects_artifact_changed_after_manifest_publication(tmp_path):
    _publish(tmp_path, "ASSUR", [_mapping(17)])
    path = tmp_path / "assur_findspot_polygon_mappings.json"
    path.write_text(json.dumps([_mapping(18)]), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum mismatch"):
        MapArtifactRepository(tmp_path).load_site_map_locations("ASSUR")
