from typing import cast
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.context import Context
from pathlib import Path
import attr
import falcon
import pytest
from falcon import testing
import ebl.app
from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.tests.fragmentarium.map_data_test_helpers import mapping_record, write_mappings


@pytest.fixture
def map_client(tmp_path: Path, context: Context) -> testing.TestClient:
    test_context = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(data_dir=tmp_path)
    )
    return testing.TestClient(ebl.app.create_app(test_context))


@pytest.mark.parametrize(
    "site",
    [("ASSUR", "Aššur"), ("KALHU", "Kalḫu"), ("NIPPUR", "Nippur"), ("URUK", "Uruk")],
)
def test_map_data_uses_canonical_artifact_site_identity(
    tmp_path: Path,
    map_client: testing.TestClient,
    findspot_repository: MongoFindspotRepository,
    seeded_provenance_service: ProvenanceService,
    site: tuple[str, str],
) -> None:
    site_id, site_name = site
    write_mappings(tmp_path, site_id, [mapping_record(400, "polygon-a")])
    live_site = seeded_provenance_service.find_by_id(site_id)
    findspot_repository.create(
        FindspotFactory.build(
            id_=400, site=live_site, sector="", area="", building="", room=""
        )
    )
    response = cast(
        testing.Result, map_client.simulate_get(f"/findspots/map-data?site={site_id}")
    )
    assert response.status == falcon.HTTP_OK
    assert cast(dict, response.json)["findspots"] == [
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


def test_configured_unpublished_site_does_not_masquerade_as_empty(
    map_client: testing.TestClient,
) -> None:
    response = cast(
        testing.Result, map_client.simulate_get("/findspots/map-data?site=KALHU")
    )
    assert response.status == falcon.HTTP_NOT_FOUND


def test_map_data_rejects_findspot_ids_that_are_not_json_safe(
    tmp_path: Path, map_client: testing.TestClient
) -> None:
    write_mappings(tmp_path, "ASSUR", [mapping_record(2**53, "unsafe-findspot-id")])
    response = cast(
        testing.Result, map_client.simulate_get("/findspots/map-data?site=ASSUR")
    )
    assert response.status == falcon.HTTP_INTERNAL_SERVER_ERROR
