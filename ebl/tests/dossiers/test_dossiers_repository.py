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


def test_search_by_id(dossiers_repository: DossiersRepository):
    dossier1 = DossierRecordFactory.build(id="ABC123", description="Test description")
    dossier2 = DossierRecordFactory.build(id="DEF456", description="Another test")
    dossier3 = DossierRecordFactory.build(id="XYZ789", description="Different one")

    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)

    result = dossiers_repository.search("ABC")
    assert len(result) == 1
    assert result[0].id == dossier1.id


def test_search_by_description(dossiers_repository: DossiersRepository):
    dossier1 = DossierRecordFactory.build(id="ABC123", description="Test description")
    dossier2 = DossierRecordFactory.build(id="DEF456", description="Another test")
    dossier3 = DossierRecordFactory.build(id="XYZ789", description="Different one")

    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)

    result = dossiers_repository.search("test")
    assert len(result) == 2
    assert {r.id for r in result} == {dossier1.id, dossier2.id}


def test_search_case_insensitive(dossiers_repository: DossiersRepository):
    dossier = DossierRecordFactory.build(id="ABC123", description="Test Description")
    dossiers_repository.create(dossier)

    result_upper = dossiers_repository.search("ABC")
    result_lower = dossiers_repository.search("abc")
    result_desc_upper = dossiers_repository.search("TEST")
    result_desc_lower = dossiers_repository.search("test")

    assert len(result_upper) == 1
    assert len(result_lower) == 1
    assert len(result_desc_upper) == 1
    assert len(result_desc_lower) == 1


def test_search_empty_query(dossiers_repository: DossiersRepository):
    result = dossiers_repository.search("")
    assert result == []


def test_search_no_matches(dossiers_repository: DossiersRepository):
    dossier = DossierRecordFactory.build(id="ABC123", description="Test description")
    dossiers_repository.create(dossier)

    result = dossiers_repository.search("nonexistent")
    assert len(result) == 0


def test_search_limits_results(dossiers_repository: DossiersRepository):
    for i in range(15):
        dossier = DossierRecordFactory.build(
            id=f"TEST{i:03d}", description="Test description"
        )
        dossiers_repository.create(dossier)

    result = dossiers_repository.search("TEST")
    assert len(result) == 10


def test_search_with_provenance_filter(dossiers_repository: DossiersRepository):
    from ebl.common.domain.provenance import Provenance

    dossier1 = DossierRecordFactory.build(
        id="TEST001", description="Test", provenance=Provenance.BABYLON
    )
    dossier2 = DossierRecordFactory.build(
        id="TEST002", description="Test", provenance=Provenance.NIPPUR
    )
    dossier3 = DossierRecordFactory.build(
        id="TEST003", description="Test", provenance=Provenance.BABYLON
    )

    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)

    result = dossiers_repository.search("TEST", provenance="Babylon")
    assert len(result) == 2
    assert {r.id for r in result} == {dossier1.id, dossier3.id}


def test_search_with_script_period_filter(dossiers_repository: DossiersRepository):
    from ebl.fragmentarium.domain.fragment import Script, Period, PeriodModifier

    dossier1 = DossierRecordFactory.build(
        id="TEST001",
        description="Test",
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier2 = DossierRecordFactory.build(
        id="TEST002",
        description="Test",
        script=Script(Period.OLD_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier3 = DossierRecordFactory.build(
        id="TEST003",
        description="Test",
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )

    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)

    result = dossiers_repository.search("TEST", script_period="Neo-Babylonian")
    assert len(result) == 2
    assert {r.id for r in result} == {dossier1.id, dossier3.id}


def test_search_with_multiple_filters(dossiers_repository: DossiersRepository):
    from ebl.common.domain.provenance import Provenance
    from ebl.fragmentarium.domain.fragment import Script, Period, PeriodModifier

    dossier1 = DossierRecordFactory.build(
        id="TEST001",
        description="Test",
        provenance=Provenance.BABYLON,
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier2 = DossierRecordFactory.build(
        id="TEST002",
        description="Test",
        provenance=Provenance.BABYLON,
        script=Script(Period.OLD_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier3 = DossierRecordFactory.build(
        id="TEST003",
        description="Test",
        provenance=Provenance.NIPPUR,
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )

    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)

    result = dossiers_repository.search(
        "TEST", provenance="Babylon", script_period="Neo-Babylonian"
    )
    assert len(result) == 1
    assert result[0].id == dossier1.id
