import json

import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.fragmentarium.domain.map_location import MapLocation


@pytest.fixture
def mappings(tmp_path):
    records = {}
    for site_id, findspot_id in (("ASSUR", 1), ("NIPPUR", 2)):
        entry = {
            "findspotId": findspot_id,
            "polygonIds": [f"{site_id.lower()}-a"],
            "locationPrecision": "excavation-area",
            "matchMethod": "verified-source",
            "source": "test source",
            "sourceRevision": "test revision",
        }
        path = tmp_path / f"{site_id.lower()}_findspot_polygon_mappings.json"
        path.write_text(json.dumps([entry]), encoding="utf-8")
        records[site_id] = (path, entry)
    return MapArtifactRepository(tmp_path), records


def test_mapping_identity_is_separate_from_location_payload(mappings):
    repository, _ = mappings

    locations = repository.load_site_map_locations("ASSUR")

    assert set(locations) == {1}
    assert isinstance(locations[1], MapLocation)
    assert locations[1].polygon_ids == ("assur-a",)
    assert locations[1].source == "test source"
    assert locations[1].source_revision == "test revision"


@pytest.mark.parametrize("change", ["unknown", "missing"])
def test_location_payload_validation_remains_strict(mappings, change):
    repository, records = mappings
    path, entry = records["ASSUR"]
    if change == "unknown":
        entry["unexpected"] = "reject this"
    else:
        del entry["source"]
    path.write_text(json.dumps([entry]), encoding="utf-8")

    with pytest.raises(ValidationError) as error:
        repository.load_site_map_locations("ASSUR")

    field = "unexpected" if change == "unknown" else "source"
    assert field in error.value.messages


@pytest.mark.parametrize("site_id", ["KALHU", "UNKNOWN"])
def test_unavailable_site_has_no_locations(mappings, site_id):
    repository, _ = mappings

    assert repository.load_site_map_locations(site_id) == {}
    assert set(repository.known_site_ids()) == {"ASSUR", "NIPPUR"}


@pytest.mark.parametrize(
    "site_ids, expected", [(None, {1, 2}), (("NIPPUR",), {2}), ((), set())]
)
def test_only_requested_site_locations_are_loaded(mappings, site_ids, expected):
    repository, _ = mappings

    assert set(repository.load_map_locations(site_ids)) == expected
