import falcon
import pytest
from ebl.dossiers.domain.dossier_record import DossierRecord
from ebl.tests.factories.dossier import (
    DossierRecordFactory,
)
from ebl.dossiers.application.dossiers_repository import (
    DossiersRepository,
)
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    DossierRecordSchema,
    DossierPaginationSchema,
)
from ebl.bibliography.application.bibliography_repository import BibliographyRepository


@pytest.fixture
def dossier_record() -> DossierRecord:
    return DossierRecordFactory.build()


@pytest.fixture
def another_dossier_record() -> DossierRecord:
    return DossierRecordFactory.build()


@pytest.fixture
def unrelated_dossier_record() -> DossierRecord:
    return DossierRecordFactory.build()


def test_fetch_dossier_record_route(
    dossier_record,
    another_dossier_record,
    unrelated_dossier_record,
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    dossiers_repository.create(dossier_record)
    dossiers_repository.create(another_dossier_record)
    dossiers_repository.create(unrelated_dossier_record)
    for reference in dossier_record.references + another_dossier_record.references:
        bibliography_repository.create(reference.document)
    get_result = client.simulate_get(
        "/dossiers",
        params={"ids[]": [dossier_record.id, another_dossier_record.id]},
    )

    assert get_result.status == falcon.HTTP_OK
    assert sorted(
        get_result.json, key=lambda record: record["_id"]
    ) == DossierRecordSchema(many=True).dump(
        sorted([dossier_record, another_dossier_record], key=lambda record: record.id)
    )


def test_search_dossier_records_route(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    dossier1 = DossierRecordFactory.build(id="SEARCH123", description="test dossier")
    dossier2 = DossierRecordFactory.build(id="OTHER456", description="another one")
    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    for reference in dossier1.references + dossier2.references:
        bibliography_repository.create(reference.document)

    get_result = client.simulate_get(
        "/dossiers/search",
        params={"searchText": "SEARCH", "limit": 10, "page": 0},
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json["totalCount"] == 1
    assert len(get_result.json["dossiers"]) == 1
    assert get_result.json["dossiers"][0]["_id"] == dossier1.id


def test_search_dossier_records_with_pagination(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    dossiers = [DossierRecordFactory.build(description=f"match {i}") for i in range(5)]
    for dossier in dossiers:
        dossiers_repository.create(dossier)
        for reference in dossier.references:
            bibliography_repository.create(reference.document)

    page_1 = client.simulate_get(
        "/dossiers/search",
        params={"searchText": "match", "limit": 2, "page": 0},
    )
    page_2 = client.simulate_get(
        "/dossiers/search",
        params={"searchText": "match", "limit": 2, "page": 1},
    )

    assert page_1.status == falcon.HTTP_OK
    assert page_1.json["totalCount"] == 5
    assert len(page_1.json["dossiers"]) == 2

    assert page_2.status == falcon.HTTP_OK
    assert page_2.json["totalCount"] == 5
    assert len(page_2.json["dossiers"]) == 2


def test_search_dossier_records_default_params(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    dossier = DossierRecordFactory.build(description="test")
    dossiers_repository.create(dossier)
    for reference in dossier.references:
        bibliography_repository.create(reference.document)

    get_result = client.simulate_get("/dossiers/search")

    assert get_result.status == falcon.HTTP_OK
    assert "totalCount" in get_result.json
    assert "dossiers" in get_result.json


def test_search_dossier_records_invalid_limit(
    client,
) -> None:
    get_result = client.simulate_get(
        "/dossiers/search",
        params={"searchText": "test", "limit": 200, "page": 0},
    )

    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_dossier_records_invalid_page(
    client,
) -> None:
    get_result = client.simulate_get(
        "/dossiers/search",
        params={"searchText": "test", "limit": 10, "page": -1},
    )

    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_dossier_records_no_results(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    dossier = DossierRecordFactory.build(id="ABC", description="something")
    dossiers_repository.create(dossier)
    for reference in dossier.references:
        bibliography_repository.create(reference.document)

    get_result = client.simulate_get(
        "/dossiers/search",
        params={"searchText": "NONEXISTENT", "limit": 10, "page": 0},
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json["totalCount"] == 0
    assert get_result.json["dossiers"] == []
