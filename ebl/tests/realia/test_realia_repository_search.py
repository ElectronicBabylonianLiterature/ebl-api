from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.tests.factories.realia import RealiaEntryFactory, ReallexikonEntryFactory
from ebl.tests.realia.realia_repository_helpers import (
    create_entry_with_bibliography,
    insert_minimal,
)


def test_search_by_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(id="Lion", related_terms=())
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search("Lion")

    assert len(results) == 1
    assert results[0].id == entry.id


def test_search_by_related_term(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(id="Horse", related_terms=("Pferd", "Equus"))
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search("Pferd")

    assert len(results) == 1
    assert results[0].id == entry.id


def test_search_strips_special_chars(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(id="Enki", related_terms=())
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search("“Enki”")

    assert len(results) == 1
    assert results[0].id == entry.id


def test_search_empty_query_returns_empty(
    realia_repository: RealiaRepository,
) -> None:
    results = realia_repository.search("")
    assert results == []


def test_search_no_match_returns_empty(
    realia_repository: RealiaRepository,
) -> None:
    results = realia_repository.search("zzz_no_match_xyz")
    assert results == []


def test_search_treats_regex_metacharacters_literally(
    realia_repository: MongoRealiaRepository,
) -> None:
    insert_minimal(realia_repository, "Lion")

    assert realia_repository.search(".*") == []
    assert realia_repository.search("Li.n") == []
    assert realia_repository.search("(a+)+") == []


def test_search_entry_with_reallexikon_no_reference(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(
        reallexikon=(ReallexikonEntryFactory.build(reference=None),)
    )
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search(entry.id)

    assert len(results) == 1
    assert results[0].reallexikon[0].reference is None


def test_search_ranks_exact_id_first(
    realia_repository: MongoRealiaRepository,
) -> None:
    for identifier in ["Amêl-Marduk", "Marduk A. I.", "Marduk"]:
        insert_minimal(realia_repository, identifier)

    results = realia_repository.search("Marduk")

    assert [result.id for result in results] == [
        "Marduk",
        "Marduk A. I.",
        "Amêl-Marduk",
    ]


def test_search_has_no_result_limit(
    realia_repository: MongoRealiaRepository,
) -> None:
    for index in range(20):
        insert_minimal(realia_repository, f"Lion {index:02d}")

    results = realia_repository.search("Lion")

    assert len(results) == 20


def test_search_ranks_richer_entry_first_within_tier(
    realia_repository: MongoRealiaRepository,
) -> None:
    sparse = RealiaEntryFactory.build(
        id="Lion A",
        related_terms=(),
        type=(),
        afo_register=(),
        references=(),
        wikidata_id=(),
        reallexikon=(),
    )
    rich = RealiaEntryFactory.build(
        id="Lion Z",
        related_terms=("Löwe", "Ur-mah"),
        type=("Fauna",),
        afo_register=(),
        references=(),
        wikidata_id=("Q140",),
        reallexikon=(),
    )
    for entry in (sparse, rich):
        realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))

    results = realia_repository.search("Lion")

    assert [result.id for result in results] == ["Lion Z", "Lion A"]
