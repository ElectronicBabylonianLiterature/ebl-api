import attr
import falcon
import pytest

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.domain.map_location import (
    MapLocation,
    MapLocationMatchMethod,
    MapLocationPrecision,
)
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def _map_location(*polygon_ids, match_method=MapLocationMatchMethod.VERIFIED_SOURCE):
    return MapLocation(
        polygon_ids=tuple(polygon_ids),
        location_precision=MapLocationPrecision.EXCAVATION_AREA,
        match_method=match_method,
        source="Assur Tafeln.ods",
        source_revision="2026-07-27",
    )


def _seed_fragment(fragment_repository, site, findspot_id, number, scopes=()):
    fragment = FragmentFactory.build(
        number=MuseumNumber.of(number),
        archaeology=Archaeology(site=site, findspot_id=findspot_id),
        authorized_scopes=list(scopes),
    )
    fragment_repository.create(fragment)


@pytest.fixture
def map_data(findspot_repository, fragment_repository, seeded_provenance_service):
    assur = seeded_provenance_service.find_by_id("ASSUR")
    nineveh = seeded_provenance_service.find_by_id("NINEVEH")
    shared = _map_location("assur-a")
    multi = _map_location("assur-a", "assur-b")

    for findspot in [
        attr.evolve(
            FindspotFactory.build(
                id_=100,
                site=assur,
                sector="S1",
                area="A1",
                building="B1",
                room="R1",
                map_location=shared,
            )
        ),
        attr.evolve(
            FindspotFactory.build(
                id_=101,
                site=assur,
                sector="S2",
                area="A2",
                building="B2",
                room="R2",
                map_location=multi,
            )
        ),
        attr.evolve(
            FindspotFactory.build(
                id_=102,
                site=assur,
                sector="S3",
                area="A3",
                building="B3",
                room="R3",
                map_location=shared,
            )
        ),
        attr.evolve(FindspotFactory.build(id_=103, site=assur, map_location=None)),
        attr.evolve(
            FindspotFactory.build(
                id_=104,
                site=nineveh,
                map_location=_map_location("nineveh-a"),
            )
        ),
    ]:
        findspot_repository.create(findspot)

    _seed_fragment(fragment_repository, assur, 100, "X.100")
    _seed_fragment(
        fragment_repository,
        assur,
        100,
        "X.101",
        scopes=[Scope.READ_CAIC_FRAGMENTS],
    )
    _seed_fragment(fragment_repository, assur, 102, "X.102")
    _seed_fragment(fragment_repository, nineveh, 104, "X.104")


def test_map_data_omits_unmapped_and_exposes_polygons(client, map_data):
    response = client.simulate_get("/findspots/map-data")
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


def test_map_data_counts_follow_visibility_rules(client, guest_client, map_data):
    auth_payload = {
        item["findspotId"]: item
        for item in client.simulate_get("/findspots/map-data").json["findspots"]
    }
    guest_payload = {
        item["findspotId"]: item
        for item in guest_client.simulate_get("/findspots/map-data").json["findspots"]
    }

    assert auth_payload[100]["accessibleFragmentCount"] == 2
    assert guest_payload[100]["accessibleFragmentCount"] == 1
    assert auth_payload[101]["accessibleFragmentCount"] == 0
    assert auth_payload[102]["accessibleFragmentCount"] == 1
    assert auth_payload[104]["accessibleFragmentCount"] == 1


def test_map_data_site_filter_and_invalid_site(client, map_data):
    filtered = client.simulate_get("/findspots/map-data?site=ASSUR")
    invalid = client.simulate_get("/findspots/map-data?site=assur")

    assert [item["findspotId"] for item in filtered.json["findspots"]] == [
        100,
        101,
        102,
    ]
    assert invalid.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_map_data_uses_one_count_query(
    client, map_data, fragment_repository, monkeypatch
):
    calls = {"count": 0}
    original = fragment_repository.count_fragments_by_findspot_ids

    def wrapped(*args, **kwargs):
        calls["count"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fragment_repository, "count_fragments_by_findspot_ids", wrapped)

    client.simulate_get("/findspots/map-data")

    assert calls["count"] == 1
