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
