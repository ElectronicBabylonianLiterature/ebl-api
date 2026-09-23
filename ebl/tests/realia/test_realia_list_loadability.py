from typing import List

import falcon
import pytest

from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.realia.infrastructure.realia_loadability import is_loadable
from ebl.tests.realia.realia_repository_helpers import insert_stored

HEALTHY_DOCUMENT = {"_id": "Anu", "crossReferences": [], "type": ["Divine names"]}

NULLABLE_FIELDS = [
    "afoRegister",
    "references",
    "afoCrossReferences",
    "relatedTerms",
    "type",
    "wikidataId",
    "crossReferences",
    "reallexikon",
    "realiaId",
]

UNLOADABLE_DOCUMENTS: List[dict] = [
    {"_id": "BadTerm", "relatedTerms": [5]},
    {"_id": "BadType", "type": [{"name": "x"}]},
    {"_id": "BadReference", "references": [{"id": "bib_1"}]},
    {"_id": "BadAfoRegister", "afoRegister": ["x"]},
    {
        "_id": "BadCrossReferences",
        "crossReferences": [{"id": "a"}, {"id": "b", "lemma": "b"}],
    },
]

NON_STRING_IDENTIFIERS = [42, 4.2, True, {"id": "x"}]


@pytest.mark.parametrize("field", NULLABLE_FIELDS)
def test_entry_with_null_field_is_not_listed(
    field: str, realia_repository: MongoRealiaRepository
) -> None:
    insert_stored(realia_repository, HEALTHY_DOCUMENT)
    insert_stored(realia_repository, {"_id": "Legacy", field: None})

    assert realia_repository.list_non_redirect_ids() == ["Anu"]


@pytest.mark.parametrize("document", UNLOADABLE_DOCUMENTS)
def test_entry_the_schema_rejects_is_not_listed(
    document: dict, realia_repository: MongoRealiaRepository
) -> None:
    insert_stored(realia_repository, HEALTHY_DOCUMENT)
    insert_stored(realia_repository, document)

    assert realia_repository.list_non_redirect_ids() == ["Anu"]


@pytest.mark.parametrize("identifier", NON_STRING_IDENTIFIERS)
def test_entry_with_non_string_id_is_not_listed(
    identifier: object, realia_repository: MongoRealiaRepository
) -> None:
    insert_stored(realia_repository, HEALTHY_DOCUMENT)
    insert_stored(realia_repository, {"_id": identifier, "type": ["x"]})

    assert realia_repository.list_non_redirect_ids() == ["Anu"]


def test_is_loadable_accepts_healthy_document() -> None:
    assert is_loadable(HEALTHY_DOCUMENT) is True


@pytest.mark.parametrize("document", UNLOADABLE_DOCUMENTS)
def test_is_loadable_rejects_unloadable_document(document: dict) -> None:
    assert is_loadable(document) is False


def test_every_listed_id_is_retrievable_despite_malformed_entries(
    realia_repository: MongoRealiaRepository, client
) -> None:
    insert_stored(realia_repository, HEALTHY_DOCUMENT)
    for field in NULLABLE_FIELDS:
        insert_stored(realia_repository, {"_id": f"Null {field}", field: None})
    for document in UNLOADABLE_DOCUMENTS:
        insert_stored(realia_repository, document)
    insert_stored(realia_repository, {"_id": 42, "type": ["x"]})

    listed_identifiers = client.simulate_get("/realia/all").json

    assert listed_identifiers == ["Anu"]
    for identifier in listed_identifiers:
        assert client.simulate_get(f"/realia/{identifier}").status == falcon.HTTP_OK
