import attr
import falcon
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.map_artifact_repository import (
    MapArtifactRepository,
)
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.map_data_test_helpers import (
    mapping_record,
    write_mappings,
)
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import Guest


def _seed_fragment(fragment_repository, site, findspot_id, number, scopes=()):
    fragment = FragmentFactory.build(
        number=MuseumNumber.of(number),
        archaeology=Archaeology(site=site, findspot_id=findspot_id),
        authorized_scopes=list(scopes),
    )
    fragment_repository.create(fragment)


@pytest.fixture
def map_data(
    tmp_path,
    context,
    findspot_repository,
    fragment_repository,
    seeded_provenance_service,
):
    assur = seeded_provenance_service.find_by_id("ASSUR")
    nippur = seeded_provenance_service.find_by_id("NIPPUR")

    write_mappings(
        tmp_path,
        "ASSUR",
        [
            mapping_record(100, "assur-a"),
            mapping_record(101, "assur-a", "assur-b"),
            mapping_record(102, "assur-a"),
        ],
    )
    write_mappings(tmp_path, "NIPPUR", [mapping_record(104, "nippur-a")])

    for findspot in [
        FindspotFactory.build(
            id_=100, site=assur, sector="S1", area="A1", building="B1", room="R1"
        ),
        FindspotFactory.build(
            id_=101, site=assur, sector="S2", area="A2", building="B2", room="R2"
        ),
        FindspotFactory.build(
            id_=102, site=assur, sector="S3", area="A3", building="B3", room="R3"
        ),
        FindspotFactory.build(id_=103, site=assur),
        FindspotFactory.build(id_=104, site=nippur),
    ]:
        findspot_repository.create(findspot)

    _seed_fragment(fragment_repository, assur, 100, "X.100")
    _seed_fragment(
        fragment_repository, assur, 100, "X.101", scopes=[Scope.READ_CAIC_FRAGMENTS]
    )
    _seed_fragment(fragment_repository, assur, 102, "X.102")
    _seed_fragment(fragment_repository, nippur, 104, "X.104")

    test_context = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(data_dir=tmp_path)
    )
    return testing.TestClient(ebl.app.create_app(test_context))


@pytest.fixture
def guest_map_data_client(tmp_path, context, map_data):
    test_context = attr.evolve(
        context,
        auth_backend=NoneAuthBackend(Guest),
        map_artifact_repository=MapArtifactRepository(data_dir=tmp_path),
    )
    return testing.TestClient(ebl.app.create_app(test_context))


def test_map_data_omits_unmapped_and_exposes_polygons(map_data):
    response = map_data.simulate_get("/findspots/map-data")
    payload = response.json["findspots"]

    assert response.status == falcon.HTTP_OK
    assert [item["findspotId"] for item in payload] == [100, 101, 102, 104]
    assert 103 not in [item["findspotId"] for item in payload]
    assert next(item for item in payload if item["findspotId"] == 101)[
        "polygonIds"
    ] == [
        "assur-a",
        "assur-b",
    ]
    assert (
        next(item for item in payload if item["findspotId"] == 100)["siteId"] == "ASSUR"
    )
    assert "fragmentCount" not in payload[0]


def test_map_data_counts_follow_visibility_rules(map_data, guest_map_data_client):
    auth_payload = {
        item["findspotId"]: item
        for item in map_data.simulate_get("/findspots/map-data").json["findspots"]
    }
    guest_payload = {
        item["findspotId"]: item
        for item in guest_map_data_client.simulate_get("/findspots/map-data").json[
            "findspots"
        ]
    }

    assert auth_payload[100]["accessibleFragmentCount"] == 2
    assert guest_payload[100]["accessibleFragmentCount"] == 1
    assert auth_payload[101]["accessibleFragmentCount"] == 0
    assert auth_payload[102]["accessibleFragmentCount"] == 1
    assert auth_payload[104]["accessibleFragmentCount"] == 1


def test_map_data_site_filter_and_invalid_site(map_data):
    filtered = map_data.simulate_get("/findspots/map-data?site=ASSUR")
    invalid = map_data.simulate_get("/findspots/map-data?site=assur")

    assert [item["findspotId"] for item in filtered.json["findspots"]] == [
        100,
        101,
        102,
    ]
    assert invalid.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_map_data_unmapped_site_returns_empty(map_data):
    response = map_data.simulate_get("/findspots/map-data?site=NINEVEH")

    assert response.status == falcon.HTTP_OK
    assert response.json["findspots"] == []


def test_map_data_uses_one_count_query(map_data, fragment_repository, monkeypatch):
    calls = {"count": 0}
    original = fragment_repository.count_fragments_by_findspot_ids

    def wrapped(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fragment_repository, "count_fragments_by_findspot_ids", wrapped)

    map_data.simulate_get("/findspots/map-data")

    assert calls["count"] == 1


def test_map_data_rejects_counts_that_are_not_json_safe(
    map_data, fragment_repository, monkeypatch
):
    monkeypatch.setattr(
        fragment_repository,
        "count_fragments_by_findspot_ids",
        lambda *args, **kwargs: {100: 2**53},
    )

    response = map_data.simulate_get("/findspots/map-data")

    assert response.status == falcon.HTTP_INTERNAL_SERVER_ERROR


def test_map_data_uses_narrow_findspot_read(map_data, findspot_repository, monkeypatch):
    def reject_full_collection_read():
        raise AssertionError("map data must not load the full findspot collection")

    monkeypatch.setattr(findspot_repository, "find_all", reject_full_collection_read)

    response = map_data.simulate_get("/findspots/map-data")

    assert response.status == falcon.HTTP_OK


def test_map_data_rejects_missing_and_wrong_site_metadata(
    tmp_path,
    context,
    findspot_repository,
    seeded_provenance_service,
):
    assur = seeded_provenance_service.find_by_id("ASSUR")
    nippur = seeded_provenance_service.find_by_id("NIPPUR")
    write_mappings(
        tmp_path,
        "ASSUR",
        [
            mapping_record(300, "assur-a"),
            mapping_record(301, "assur-b"),
            mapping_record(302, "assur-c"),
        ],
    )
    findspot_repository.create(FindspotFactory.build(id_=300, site=assur))
    findspot_repository.create(FindspotFactory.build(id_=301, site=nippur))
    findspot_repository.create(FindspotFactory.build(id_=302, site=None))
    test_context = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(data_dir=tmp_path)
    )
    client = testing.TestClient(ebl.app.create_app(test_context))

    payload = client.simulate_get("/findspots/map-data").json["findspots"]

    assert [item["findspotId"] for item in payload] == [300]
