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


def test_search_dossiers_route(
    dossiers_repository: DossiersRepository,
    client,
) -> None:
    dossier1 = DossierRecordFactory.build(id="TEST001", description="First test")
    dossier2 = DossierRecordFactory.build(id="TEST002", description="Second test")
    dossier3 = DossierRecordFactory.build(id="OTHER001", description="Different")

    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)

    result = client.simulate_get("/dossiers/search", params={"query": "TEST"})

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 2
    assert {r["_id"] for r in result.json} == {dossier1.id, dossier2.id}


def test_search_dossiers_by_description(
    dossiers_repository: DossiersRepository,
    client,
) -> None:
    dossier1 = DossierRecordFactory.build(id="ABC001", description="Test description")
    dossier2 = DossierRecordFactory.build(id="DEF002", description="Another test")
    dossier3 = DossierRecordFactory.build(id="GHI003", description="Different")

    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)

    result = client.simulate_get("/dossiers/search", params={"query": "test"})

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 2
    assert {r["_id"] for r in result.json} == {dossier1.id, dossier2.id}


def test_search_dossiers_empty_query(
    dossiers_repository: DossiersRepository,
    client,
) -> None:
    dossier = DossierRecordFactory.build()
    dossiers_repository.create(dossier)

    result = client.simulate_get("/dossiers/search", params={"query": ""})

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 0


def test_search_dossiers_no_query_param(
    dossiers_repository: DossiersRepository,
    client,
) -> None:
    dossier = DossierRecordFactory.build()
    dossiers_repository.create(dossier)

    result = client.simulate_get("/dossiers/search")

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 0
