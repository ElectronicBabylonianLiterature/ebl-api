import pytest

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.tests.factories.realia import RealiaEntryFactory
from ebl.tests.realia.realia_repository_helpers import (
    create_entry_with_bibliography,
    insert_minimal,
    insert_stored,
    stored_reallexikon_entry,
)
from ebl.errors import DuplicateError, NotFoundError


def test_create_indexes_declares_partial_unique_realia_id(
    database,
    realia_repository: MongoRealiaRepository,
) -> None:
    realia_repository.create_indexes()

    indexes = database["realia"].index_information().values()
    realia_id_index = next(
        index for index in indexes if index["key"] == [("realiaId", 1)]
    )
    assert realia_id_index["unique"] is True
    assert realia_id_index["partialFilterExpression"] == {"realiaId": {"$gt": ""}}


def test_create_indexes_rejects_duplicate_realia_id(
    realia_repository: MongoRealiaRepository,
) -> None:
    realia_repository.create_indexes()
    realia_repository._realia_collection.insert_one(
        {"_id": "Elam", "realiaId": "realia_003277"}
    )

    with pytest.raises(DuplicateError):
        realia_repository._realia_collection.insert_one(
            {"_id": "Anšan", "realiaId": "realia_003277"}
        )


def test_create_indexes_allows_blank_and_missing_realia_id(
    realia_repository: MongoRealiaRepository,
) -> None:
    realia_repository.create_indexes()

    realia_repository._realia_collection.insert_one({"_id": "A", "realiaId": ""})
    realia_repository._realia_collection.insert_one({"_id": "B", "realiaId": ""})
    realia_repository._realia_collection.insert_one({"_id": "C"})
    realia_repository._realia_collection.insert_one({"_id": "D"})

    assert realia_repository._realia_collection.count_documents({}) == 4


def test_find_existing_entry(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build()
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    result = realia_repository.find(entry.id)

    assert result.id == entry.id
    assert result.related_terms == entry.related_terms
    assert result.type == entry.type
    assert result.wikidata_id == entry.wikidata_id
    assert any(ref.document is not None for ref in result.references)
    assert any(
        rlex.reference is not None and rlex.reference.document is not None
        for rlex in result.reallexikon
    )


def test_find_not_found(realia_repository: RealiaRepository) -> None:
    with pytest.raises(NotFoundError):
        realia_repository.find("nonexistent-id")


def test_find_by_realia_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    entry = RealiaEntryFactory.build(id="Elam (Geschichte)", realia_id="realia_003277")
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    result = realia_repository.find_by_realia_id("realia_003277")

    assert result.id == "Elam (Geschichte)"
    assert result.realia_id == "realia_003277"


def test_find_by_realia_id_not_found(realia_repository: RealiaRepository) -> None:
    with pytest.raises(NotFoundError):
        realia_repository.find_by_realia_id("realia_999999")


def test_list_all_realia(realia_repository: MongoRealiaRepository) -> None:
    for identifier in ("Pig", "Anu", "Enlil, Ellil"):
        insert_minimal(realia_repository, identifier)

    assert realia_repository.list_all_realia() == ["Anu", "Enlil, Ellil", "Pig"]


def test_list_all_realia_empty(realia_repository: RealiaRepository) -> None:
    assert realia_repository.list_all_realia() == []


def test_list_all_realia_returns_every_id_without_limit(
    realia_repository: MongoRealiaRepository,
) -> None:
    identifiers = [f"Realia {index:02d}" for index in range(25)]
    for identifier in identifiers:
        insert_minimal(realia_repository, identifier)

    assert realia_repository.list_all_realia() == sorted(identifiers)


def test_list_all_realia_excludes_redirect_stubs(
    realia_repository: MongoRealiaRepository,
) -> None:
    canonical = {"id": "Canonical", "lemma": "Canonical"}
    stubs: dict[str, dict] = {
        "Empty stub": {"crossReferences": [canonical]},
        "Reallexikon stub": {
            "crossReferences": [canonical],
            "reallexikon": [{"id": "r", "reference": None}],
        },
    }
    listable: dict[str, dict] = {
        "Has afoRegister": {
            "crossReferences": [canonical],
            "afoRegister": [{"mainWord": "x"}],
        },
        "Has references": {
            "crossReferences": [canonical],
            "references": [{"id": "bib_1"}],
        },
        "Has afoCrossReferences": {
            "crossReferences": [canonical],
            "afoCrossReferences": [{"id": "a", "lemma": "b"}],
        },
        "Has two reallexikon": {
            "crossReferences": [canonical],
            "reallexikon": [
                {"id": "a", "reference": None},
                {"id": "b", "reference": None},
            ],
        },
        "Has reallexikon reference": {
            "crossReferences": [canonical],
            "reallexikon": [{"id": "a", "reference": {"id": "bib_1"}}],
        },
        "Two cross references": {
            "crossReferences": [canonical, {"id": "o", "lemma": "o"}],
        },
        "No cross references": {},
    }
    for identifier, document in {**stubs, **listable}.items():
        insert_stored(realia_repository, {"_id": identifier, **document})

    result = realia_repository.list_all_realia()

    assert set(result) == set(listable)
    assert not set(stubs) & set(result)


def test_find_injects_lean_reallexikon_reference(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    bibliography_repository.create(BibliographyEntryFactory.build(id="rla_1_170e"))
    insert_stored(
        realia_repository,
        {
            "_id": "Aššur",
            "reallexikon": [stored_reallexikon_entry("A", "rla_1_170e", "170–195")],
        },
    )

    reference = realia_repository.find("Aššur").reallexikon[0].reference

    assert reference is not None
    assert reference.id == "rla_1_170e"
    assert reference.pages == "170–195"
    assert reference.document is not None
    assert reference.document["id"] == "rla_1_170e"


def test_find_injects_all_reallexikon_entries(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    for bibliography_id in ("rla_1_170e", "rla_1_195"):
        bibliography_repository.create(
            BibliographyEntryFactory.build(id=bibliography_id)
        )
    insert_stored(
        realia_repository,
        {
            "_id": "Aššur",
            "reallexikon": [
                stored_reallexikon_entry("A", "rla_1_170e", "170–195"),
                stored_reallexikon_entry("B", "rla_1_195", "195–198"),
                {"id": "C", "title": "Aššur C", "reference": None},
            ],
        },
    )

    reallexikon = realia_repository.find("Aššur").reallexikon

    injected = [rlex.reference for rlex in reallexikon[:2]]
    documents = [
        reference.document["id"]
        for reference in injected
        if reference is not None and reference.document is not None
    ]
    assert documents == ["rla_1_170e", "rla_1_195"]
    assert reallexikon[2].reference is None
