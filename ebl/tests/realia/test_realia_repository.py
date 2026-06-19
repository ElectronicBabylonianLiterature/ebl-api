import pytest

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.domain.realia_entry import RealiaEntry
from ebl.realia.infrastructure.mongo_realia_repository import (
    MongoRealiaRepository,
    RealiaEntrySchema,
)
from ebl.tests.factories.realia import RealiaEntryFactory, ReallexikonEntryFactory
from ebl.errors import NotFoundError


def _create_entry_with_bibliography(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    entry: RealiaEntry,
) -> None:
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))
    for ref in entry.references:
        if ref.document:
            bibliography_repository.create(ref.document)
    rlex = entry.reallexikon
    if rlex is not None and rlex.reference is not None and rlex.reference.document:
        bibliography_repository.create(rlex.reference.document)


def test_find_existing_entry(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build()
    _create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    result = realia_repository.find(entry.id)

    assert result.id == entry.id
    assert result.related_terms == entry.related_terms
    assert result.type == entry.type
    assert result.wikidata_id == entry.wikidata_id
    assert any(ref.document is not None for ref in result.references)
    assert result.reallexikon is not None
    assert result.reallexikon.reference is not None
    assert result.reallexikon.reference.document is not None


def test_find_not_found(realia_repository: RealiaRepository) -> None:
    with pytest.raises(NotFoundError):
        realia_repository.find("nonexistent-id")


def test_search_by_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(id="Lion", related_terms=())
    _create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search("Lion")

    assert len(results) == 1
    assert results[0].id == entry.id


def test_search_by_related_term(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(id="Horse", related_terms=("Pferd", "Equus"))
    _create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search("Pferd")

    assert len(results) == 1
    assert results[0].id == entry.id


def test_search_strips_special_chars(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(id="Enki", related_terms=())
    _create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search("\u201cEnki\u201d")

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


def test_search_entry_with_reallexikon_no_reference(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(
        reallexikon=ReallexikonEntryFactory.build(reference=None)
    )
    _create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    results = realia_repository.search(entry.id)

    assert len(results) == 1
    assert results[0].reallexikon is not None
    assert results[0].reallexikon.reference is None


def _insert_minimal(realia_repository: MongoRealiaRepository, identifier: str) -> None:
    entry = RealiaEntryFactory.build(
        id=identifier, related_terms=(), references=(), reallexikon=None
    )
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))


def test_search_ranks_exact_id_first(
    realia_repository: MongoRealiaRepository,
) -> None:
    for identifier in ["Amêl-Marduk", "Marduk A. I.", "Marduk"]:
        _insert_minimal(realia_repository, identifier)

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
        _insert_minimal(realia_repository, f"Lion {index:02d}")

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
        reallexikon=None,
    )
    rich = RealiaEntryFactory.build(
        id="Lion Z",
        related_terms=("Löwe", "Ur-mah"),
        type=("Fauna",),
        afo_register=(),
        references=(),
        wikidata_id=("Q140",),
        reallexikon=None,
    )
    for entry in (sparse, rich):
        realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))

    results = realia_repository.search("Lion")

    assert [result.id for result in results] == ["Lion Z", "Lion A"]
