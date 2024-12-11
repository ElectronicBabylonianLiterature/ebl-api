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


@pytest.fixture
def dossier_record() -> DossierRecord:
    return DossierRecordFactory.build()


def test_fetch_dossier_record_route(
    dossier_record, dossiers_repository: DossiersRepository, client
) -> None:
    dossiers_repository.create(dossier_record)
    get_result = client.simulate_get("/dossiers", params={"id": dossier_record.id})

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json[0] == DossierRecordSchema().dump(dossier_record)
