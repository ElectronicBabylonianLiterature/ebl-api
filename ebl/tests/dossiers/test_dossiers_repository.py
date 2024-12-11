from ebl.tests.factories.dossier import DossierRecordFactory
from ebl.dossiers.application.dossiers_repository import DossiersRepository


def test_query_by_ids(dossiers_repository: DossiersRepository):
    dossier_record = DossierRecordFactory.build()
    dossiers_repository.create(dossier_record)
    dossiers_repository.create(DossierRecordFactory.build())

    assert dossiers_repository.query_by_ids([dossier_record.id]) == [dossier_record]
