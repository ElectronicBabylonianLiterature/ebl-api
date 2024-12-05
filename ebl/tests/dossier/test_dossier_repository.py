from ebl.tests.factories.dossier import DossierRecordFactory
from ebl.dossier.application.dossier_repository import DossierRepository


def test_fetch(dossier_repository: DossierRepository):
    dossier_record = DossierRecordFactory.build()
    dossier_repository.create(dossier_record)
    dossier_repository.create(DossierRecordFactory.build())

    assert dossier_repository.fetch(dossier_record.name) == dossier_record
