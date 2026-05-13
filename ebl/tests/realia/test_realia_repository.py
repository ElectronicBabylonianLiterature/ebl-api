import pytest

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.domain.realia_entry import RealiaEntry, RealiaType
from ebl.realia.infrastructure.mongo_realia_repository import (
    MongoRealiaRepository,
    RealiaEntrySchema,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.tests.factories.realia import RealiaEntryFactory
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
    for rlex in entry.reallexikon:
        if rlex.reference is not None and rlex.reference.document:
            bibliography_repository.create(rlex.reference.document)


def test_find_existing_entry(
    realia_repository: RealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build()
    _create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    result = realia_repository.find(entry.id)

    assert result.id == entry.id
    assert result.related_terms == entry.related_terms
    assert result.type == entry.type
    assert result.wikidata_id == entry.wikidata_id


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
