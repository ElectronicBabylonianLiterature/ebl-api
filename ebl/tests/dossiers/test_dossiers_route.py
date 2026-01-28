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


def test_fetch_all_dossiers_route(
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
    for reference in (
        dossier_record.references
        + another_dossier_record.references
        + unrelated_dossier_record.references
    ):
        bibliography_repository.create(reference.document)

    get_result = client.simulate_get("/dossiers")

    assert get_result.status == falcon.HTTP_OK
    assert len(get_result.json) == 3
    assert sorted(
        get_result.json, key=lambda record: record["_id"]
    ) == DossierRecordSchema(many=True).dump(
        sorted(
            [dossier_record, another_dossier_record, unrelated_dossier_record],
            key=lambda record: record.id,
        )
    )


def _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3):
    dossiers_repository.create(dossier1)
    dossiers_repository.create(dossier2)
    dossiers_repository.create(dossier3)


def _assert_search_result(result, expected_ids):
    assert result.status == falcon.HTTP_OK
    assert len(result.json) == len(expected_ids)
    assert {r["_id"] for r in result.json} == expected_ids


def test_search_dossiers_route(
    dossiers_repository: DossiersRepository,
    client,
) -> None:
    dossier1 = DossierRecordFactory.build(id="TEST001", description="First test")
    dossier2 = DossierRecordFactory.build(id="TEST002", description="Second test")
    dossier3 = DossierRecordFactory.build(id="OTHER001", description="Different")

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3)

    result = client.simulate_get("/dossiers/search", params={"query": "TEST"})

    _assert_search_result(result, {dossier1.id, dossier2.id})


def test_search_dossiers_by_description(
    dossiers_repository: DossiersRepository,
    client,
) -> None:
    dossier1 = DossierRecordFactory.build(id="ABC001", description="Test description")
    dossier2 = DossierRecordFactory.build(id="DEF002", description="Another test")
    dossier3 = DossierRecordFactory.build(id="GHI003", description="Different")

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3)

    result = client.simulate_get("/dossiers/search", params={"query": "test"})

    _assert_search_result(result, {dossier1.id, dossier2.id})


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


def test_search_dossiers_with_provenance(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    from ebl.common.domain.provenance import Provenance

    dossier1 = DossierRecordFactory.build(
        id="TEST001", description="Babylon test", provenance=Provenance.BABYLON
    )
    dossier2 = DossierRecordFactory.build(
        id="TEST002", description="Another test", provenance=Provenance.NIPPUR
    )
    dossier3 = DossierRecordFactory.build(
        id="TEST003", description="Babylon test 2", provenance=Provenance.BABYLON
    )

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3)
    for reference in dossier1.references + dossier2.references + dossier3.references:
        bibliography_repository.create(reference.document)

    result = client.simulate_get(
        "/dossiers/search", params={"query": "test", "provenance": "Babylon"}
    )

    _assert_search_result(result, {dossier1.id, dossier3.id})


def test_search_dossiers_with_script_period(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    from ebl.fragmentarium.domain.fragment import Script, Period, PeriodModifier

    dossier1 = DossierRecordFactory.build(
        id="TEST001",
        description="Neo test",
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier2 = DossierRecordFactory.build(
        id="TEST002",
        description="Old test",
        script=Script(Period.OLD_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier3 = DossierRecordFactory.build(
        id="TEST003",
        description="Neo test 2",
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3)
    for reference in dossier1.references + dossier2.references + dossier3.references:
        bibliography_repository.create(reference.document)

    result = client.simulate_get(
        "/dossiers/search", params={"query": "test", "scriptPeriod": "Neo-Babylonian"}
    )

    _assert_search_result(result, {dossier1.id, dossier3.id})


def test_search_dossiers_with_multiple_filters(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    from ebl.common.domain.provenance import Provenance
    from ebl.fragmentarium.domain.fragment import Script, Period, PeriodModifier

    dossier1 = DossierRecordFactory.build(
        id="TEST001",
        description="Matching test",
        provenance=Provenance.BABYLON,
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier2 = DossierRecordFactory.build(
        id="TEST002",
        description="Non matching",
        provenance=Provenance.BABYLON,
        script=Script(Period.OLD_BABYLONIAN, PeriodModifier.NONE),
    )
    dossier3 = DossierRecordFactory.build(
        id="TEST003",
        description="Non matching",
        provenance=Provenance.NIPPUR,
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
    )

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3)
    for reference in dossier1.references + dossier2.references + dossier3.references:
        bibliography_repository.create(reference.document)

    result = client.simulate_get(
        "/dossiers/search",
        params={
            "query": "test",
            "provenance": "Babylon",
            "scriptPeriod": "Neo-Babylonian",
        },
    )

    _assert_search_result(result, {dossier1.id})


def test_filter_dossiers_no_params(
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    dossier1 = DossierRecordFactory.build(id="TEST001")
    dossier2 = DossierRecordFactory.build(id="TEST002")
    dossier3 = DossierRecordFactory.build(id="TEST003")

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3)
    for reference in dossier1.references + dossier2.references + dossier3.references:
        bibliography_repository.create(reference.document)

    result = client.simulate_get("/dossiers/filter")

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 3
    assert {r["_id"] for r in result.json} == {dossier1.id, dossier2.id, dossier3.id}


def test_filter_dossiers_by_provenance(
    fragmentarium,
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    from ebl.common.domain.provenance import Provenance

    dossier1 = DossierRecordFactory.build(id="DOSS001")
    dossier2 = DossierRecordFactory.build(id="DOSS002")
    dossier3 = DossierRecordFactory.build(id="DOSS003")

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, dossier3)
    for reference in dossier1.references + dossier2.references + dossier3.references:
        bibliography_repository.create(reference.document)

    from ebl.tests.factories.fragment import FragmentDossierReferenceFactory

    fragment1 = FragmentFactory.build(
        archaeology__site=Provenance.BABYLON,
        dossiers=[FragmentDossierReferenceFactory.build(dossierId=dossier1.id)],
    )
    fragment2 = FragmentFactory.build(
        archaeology__site=Provenance.NIPPUR,
        dossiers=[FragmentDossierReferenceFactory.build(dossierId=dossier2.id)],
    )

    fragmentarium.create(fragment1)
    fragmentarium.create(fragment2)

    result = client.simulate_get("/dossiers/filter", params={"provenance": "Babylon"})

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 1
    assert result.json[0]["_id"] == dossier1.id


def test_filter_dossiers_by_script_period(
    fragmentarium,
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    from ebl.fragmentarium.domain.fragment import Script, Period, PeriodModifier

    dossier1 = DossierRecordFactory.build(id="DOSS001")
    dossier2 = DossierRecordFactory.build(id="DOSS002")

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, None)
    for reference in dossier1.references + dossier2.references:
        bibliography_repository.create(reference.document)

    from ebl.tests.factories.fragment import FragmentDossierReferenceFactory

    fragment1 = FragmentFactory.build(
        script=Script(Period.NEO_BABYLONIAN, PeriodModifier.NONE),
        dossiers=[FragmentDossierReferenceFactory.build(dossierId=dossier1.id)],
    )
    fragment2 = FragmentFactory.build(
        script=Script(Period.OLD_BABYLONIAN, PeriodModifier.NONE),
        dossiers=[FragmentDossierReferenceFactory.build(dossierId=dossier2.id)],
    )

    fragmentarium.create(fragment1)
    fragmentarium.create(fragment2)

    result = client.simulate_get(
        "/dossiers/filter", params={"scriptPeriod": "Neo-Babylonian"}
    )

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 1
    assert result.json[0]["_id"] == dossier1.id


def test_filter_dossiers_by_genre(
    fragmentarium,
    dossiers_repository: DossiersRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    dossier1 = DossierRecordFactory.build(id="DOSS001")
    dossier2 = DossierRecordFactory.build(id="DOSS002")

    _create_test_dossiers(dossiers_repository, dossier1, dossier2, None)
    for reference in dossier1.references + dossier2.references:
        bibliography_repository.create(reference.document)

    from ebl.tests.factories.fragment import FragmentDossierReferenceFactory
    from ebl.fragmentarium.domain.genres import Genre

    fragment1 = FragmentFactory.build(
        genres=(Genre(["LITERATURE", "HYMNS"], False),),
        dossiers=[FragmentDossierReferenceFactory.build(dossierId=dossier1.id)],
    )
    fragment2 = FragmentFactory.build(
        genres=(Genre(["MAGIC"], False),),
        dossiers=[FragmentDossierReferenceFactory.build(dossierId=dossier2.id)],
    )

    fragmentarium.create(fragment1)
    fragmentarium.create(fragment2)

    result = client.simulate_get(
        "/dossiers/filter", params={"genre": "LITERATURE:HYMNS"}
    )

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 1
    assert result.json[0]["_id"] == dossier1.id
