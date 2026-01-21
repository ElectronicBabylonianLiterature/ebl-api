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


def test_search_by_text_id_match(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossier1 = DossierRecordFactory.build(id="ABC123")
    dossier2 = DossierRecordFactory.build(id="XYZ789")
    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    for reference in dossier1.references + dossier2.references:
        bibliography_repository.create(reference.document)

    result = dossiers_repository.search("ABC", 0, 10)

    assert result.total_count == 1
    assert result.dossiers == [dossier1]


def test_search_by_text_description_match(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossier1 = DossierRecordFactory.build(description="Ancient Babylon tablet")
    dossier2 = DossierRecordFactory.build(description="Assyrian inscription")
    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    for reference in dossier1.references + dossier2.references:
        bibliography_repository.create(reference.document)

    result = dossiers_repository.search("Babylon", 0, 10)

    assert result.total_count == 1
    assert result.dossiers == [dossier1]


def test_search_case_insensitive(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossier = DossierRecordFactory.build(id="test123", description="TEST description")
    dossiers_repository.create(dossier)
    for reference in dossier.references:
        bibliography_repository.create(reference.document)

    result_lower = dossiers_repository.search("test", 0, 10)
    result_upper = dossiers_repository.search("TEST", 0, 10)

    assert result_lower.total_count == 1
    assert result_upper.total_count == 1
    assert result_lower.dossiers == [dossier]
    assert result_upper.dossiers == [dossier]


def test_search_empty_text_returns_all(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossier1 = DossierRecordFactory.build()
    dossier2 = DossierRecordFactory.build()
    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    for reference in dossier1.references + dossier2.references:
        bibliography_repository.create(reference.document)

    result = dossiers_repository.search("", 0, 10)

    assert result.total_count == 2
    assert len(result.dossiers) == 2


def test_search_no_matches(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossier = DossierRecordFactory.build(id="ABC", description="something")
    dossiers_repository.create(dossier)
    for reference in dossier.references:
        bibliography_repository.create(reference.document)

    result = dossiers_repository.search("NONEXISTENT", 0, 10)

    assert result.total_count == 0
    assert result.dossiers == []


def test_search_pagination(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossiers = [DossierRecordFactory.build(description=f"item {i}") for i in range(5)]
    for dossier in dossiers:
        dossiers_repository.create(dossier)
        for reference in dossier.references:
            bibliography_repository.create(reference.document)

    page_1 = dossiers_repository.search("item", 0, 2)
    page_2 = dossiers_repository.search("item", 2, 2)
    page_3 = dossiers_repository.search("item", 4, 2)

    assert page_1.total_count == 5
    assert len(page_1.dossiers) == 2
    assert page_2.total_count == 5
    assert len(page_2.dossiers) == 2
    assert page_3.total_count == 5
    assert len(page_3.dossiers) == 1


def test_search_limit(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
):
    dossiers = [DossierRecordFactory.build(description=f"match {i}") for i in range(10)]
    for dossier in dossiers:
        dossiers_repository.create(dossier)
        for reference in dossier.references:
            bibliography_repository.create(reference.document)

    result = dossiers_repository.search("match", 0, 3)

    assert result.total_count == 10
    assert len(result.dossiers) == 3
