from typing import Sequence
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.context import Context
from pathlib import Path
from typing import cast
import attr
import falcon
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend
import ebl.app
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.tests.fragmentarium.map_data_test_helpers import (
    mapping_record,
    write_mappings,
    seed_map_fragment,
)
from ebl.users.domain.user import Guest


@pytest.fixture
def map_data(
    tmp_path: Path,
    context: Context,
    findspot_repository: MongoFindspotRepository,
    fragment_repository: FragmentRepository,
    seeded_provenance_service: ProvenanceService,
) -> testing.TestClient:
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
    seed_map_fragment(fragment_repository, assur, 100, "X.100")
    seed_map_fragment(
        fragment_repository, assur, 100, "X.101", scopes=[Scope.READ_CAIC_FRAGMENTS]
    )
    seed_map_fragment(fragment_repository, assur, 102, "X.102")
    seed_map_fragment(fragment_repository, nippur, 104, "X.104")
    test_context = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(data_dir=tmp_path)
    )
    return testing.TestClient(ebl.app.create_app(test_context))


@pytest.fixture
def guest_map_data_client(
    tmp_path: Path, context: Context, map_data: testing.TestClient
) -> testing.TestClient:
    test_context = attr.evolve(
        context,
        auth_backend=NoneAuthBackend(Guest),
        map_artifact_repository=MapArtifactRepository(data_dir=tmp_path),
    )
    return testing.TestClient(ebl.app.create_app(test_context))


def test_map_data_omits_unmapped_and_exposes_polygons(
    map_data: testing.TestClient,
) -> None:
    response = cast(testing.Result, map_data.simulate_get("/findspots/map-data"))
    payload = cast(dict, response.json)["findspots"]
    assert response.status == falcon.HTTP_OK
    assert [item["findspotId"] for item in payload] == [100, 101, 102, 104]
    assert 103 not in [item["findspotId"] for item in payload]
    assert next((item for item in payload if item["findspotId"] == 101))[
        "polygonIds"
    ] == ["assur-a", "assur-b"]
    assert (
        next((item for item in payload if item["findspotId"] == 100))["siteId"]
        == "ASSUR"
    )
    assert "fragmentCount" not in payload[0]


def test_map_data_counts_follow_visibility_rules(
    map_data: testing.TestClient, guest_map_data_client: testing.TestClient
) -> None:
    auth_payload = {
        item["findspotId"]: item
        for item in cast(
            dict,
            cast(testing.Result, map_data.simulate_get("/findspots/map-data")).json,
        )["findspots"]
    }
    guest_payload = {
        item["findspotId"]: item
        for item in cast(
            dict,
            cast(
                testing.Result,
                guest_map_data_client.simulate_get("/findspots/map-data"),
            ).json,
        )["findspots"]
    }
    assert auth_payload[100]["accessibleFragmentCount"] == 2
    assert guest_payload[100]["accessibleFragmentCount"] == 1
    assert auth_payload[101]["accessibleFragmentCount"] == 0
    assert auth_payload[102]["accessibleFragmentCount"] == 1
    assert auth_payload[104]["accessibleFragmentCount"] == 1


def test_map_data_site_filter_and_invalid_site(map_data: testing.TestClient) -> None:
    filtered = cast(
        testing.Result, map_data.simulate_get("/findspots/map-data?site=ASSUR")
    )
    invalid = cast(
        testing.Result, map_data.simulate_get("/findspots/map-data?site=assur")
    )
    assert [item["findspotId"] for item in cast(dict, filtered.json)["findspots"]] == [
        100,
        101,
        102,
    ]
    assert invalid.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_map_data_unmapped_site_returns_empty(map_data: testing.TestClient) -> None:
    response = cast(
        testing.Result, map_data.simulate_get("/findspots/map-data?site=NINEVEH")
    )
    assert response.status == falcon.HTTP_OK
    assert cast(dict, response.json)["findspots"] == []


def test_map_data_uses_one_count_query(
    map_data: testing.TestClient,
    fragment_repository: FragmentRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}
    original = fragment_repository.count_fragments_by_findspot_ids

    def wrapped(
        findspot_ids: Sequence[int],
        user_scopes: Sequence[Scope] = (),
        script_period: str | None = None,
        script_period_modifier: str | None = None,
        genre: Sequence[str] | None = None,
    ) -> dict[int, int]:
        calls["count"] += 1
        return original(
            findspot_ids, user_scopes, script_period, script_period_modifier, genre
        )

    monkeypatch.setattr(fragment_repository, "count_fragments_by_findspot_ids", wrapped)
    cast(testing.Result, map_data.simulate_get("/findspots/map-data"))
    assert calls["count"] == 1


@pytest.mark.parametrize("count", [2**53, True, -1, "1", None])
def test_map_data_rejects_counts_that_are_not_json_safe(
    count: object,
    map_data: testing.TestClient,
    fragment_repository: FragmentRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        fragment_repository,
        "count_fragments_by_findspot_ids",
        lambda *args, **kwargs: {100: count},
    )
    response = cast(testing.Result, map_data.simulate_get("/findspots/map-data"))
    assert response.status == falcon.HTTP_INTERNAL_SERVER_ERROR


def test_map_data_uses_narrow_findspot_read(
    map_data: testing.TestClient,
    findspot_repository: MongoFindspotRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def reject_full_collection_read() -> None:
        raise AssertionError("map data must not load the full findspot collection")

    monkeypatch.setattr(findspot_repository, "find_all", reject_full_collection_read)
    response = cast(testing.Result, map_data.simulate_get("/findspots/map-data"))
    assert response.status == falcon.HTTP_OK

    payload = cast(dict[str, list[dict[str, object]]], response.json)["findspots"]
    assert [row["findspotId"] for row in payload] == [100, 101, 102, 104]


def test_map_data_rejects_missing_and_wrong_site_metadata(
    tmp_path: Path,
    context: Context,
    findspot_repository: MongoFindspotRepository,
    seeded_provenance_service: ProvenanceService,
    caplog: pytest.LogCaptureFixture,
) -> None:
    assur = seeded_provenance_service.find_by_id("ASSUR")
    nippur = seeded_provenance_service.find_by_id("NIPPUR")
    write_mappings(
        tmp_path,
        "ASSUR",
        [
            mapping_record(300, "assur-a"),
            mapping_record(301, "assur-b"),
            mapping_record(302, "assur-c"),
            mapping_record(303, "assur-d"),
        ],
    )
    findspot_repository.create(FindspotFactory.build(id_=300, site=assur))
    findspot_repository.create(FindspotFactory.build(id_=301, site=nippur))
    findspot_repository.create(FindspotFactory.build(id_=302, site=None))
    test_context = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(data_dir=tmp_path)
    )
    client = testing.TestClient(ebl.app.create_app(test_context))
    result = cast(testing.Result, client.simulate_get("/findspots/map-data"))
    payload = cast(dict[str, list[dict[str, object]]], cast(dict, result.json))[
        "findspots"
    ]
    assert [item["findspotId"] for item in payload] == [300]
    assert "[301, 302, 303]" in caplog.text
