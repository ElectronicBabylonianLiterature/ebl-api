import attr
import falcon
import pytest
from falcon import testing

import ebl.app
from ebl.fragmentarium.application.map_artifact_repository import (
    MapArtifactRepository,
)
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.tests.fragmentarium.map_data_test_helpers import (
    mapping_record,
    write_mappings,
)


@pytest.fixture
def map_client(tmp_path, context):
    test_context = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(data_dir=tmp_path)
    )
    return testing.TestClient(ebl.app.create_app(test_context))


@pytest.mark.parametrize(
    "site",
    [
        ("ASSUR", "Aššur"),
        ("KALHU", "Kalḫu"),
        ("NIPPUR", "Nippur"),
        ("URUK", "Uruk"),
    ],
)
def test_map_data_uses_canonical_artifact_site_identity(
    tmp_path, map_client, findspot_repository, seeded_provenance_service, site
):
    site_id, site_name = site
    write_mappings(tmp_path, site_id, [mapping_record(400, "polygon-a")])
    live_site = seeded_provenance_service.find_by_id(site_id)
    findspot_repository.create(
        FindspotFactory.build(
            id_=400,
            site=live_site,
            sector="",
            area="",
            building="",
            room="",
        )
    )

    response = map_client.simulate_get(f"/findspots/map-data?site={site_id}")

    assert response.status == falcon.HTTP_OK
    assert response.json["findspots"] == [
        {
            "findspotId": 400,
            "siteId": site_id,
            "siteName": site_name,
            "polygonIds": ["polygon-a"],
            "accessibleFragmentCount": 0,
            "locationPrecision": "excavation-area",
            "matchMethod": "verified-source",
            "sector": None,
            "area": None,
            "building": None,
            "room": None,
        }
    ]


def test_configured_unpublished_site_does_not_masquerade_as_empty(map_client):
    response = map_client.simulate_get("/findspots/map-data?site=KALHU")

    assert response.status == falcon.HTTP_INTERNAL_SERVER_ERROR


def test_map_data_rejects_findspot_ids_that_are_not_json_safe(tmp_path, map_client):
    write_mappings(tmp_path, "ASSUR", [mapping_record(2**53, "unsafe-findspot-id")])

    response = map_client.simulate_get("/findspots/map-data?site=ASSUR")

    assert response.status == falcon.HTTP_INTERNAL_SERVER_ERROR
