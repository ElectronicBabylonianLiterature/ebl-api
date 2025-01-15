from ebl.tests.factories.dossier import DossierRecordFactory
from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.bibliography.application.bibliography_repository import BibliographyRepository


def test_query_by_ids(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossier_record = DossierRecordFactory.build()
    dossiers_repository.create(dossier_record)
    for reference in dossier_record.references:
        bibliography_repository.create(reference.document)
    dossiers_repository.create(DossierRecordFactory.build())

    assert dossiers_repository.query_by_ids([dossier_record.id]) == [dossier_record]
