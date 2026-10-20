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

NON_STRING_REFERENCE_IDS = [
    pytest.param(5, id="integer"),
    pytest.param({"nested": "bib_1"}, id="object"),
    pytest.param(["bib_1"], id="list"),
]

NON_STRING_IDENTIFIERS = [
    pytest.param(42, id="integer"),
    pytest.param(4.2, id="float"),
    pytest.param(True, id="boolean"),
    pytest.param({"id": "x"}, id="object"),
]


@pytest.mark.parametrize("field", NULLABLE_FIELDS)
def test_entry_with_null_field_is_listed_only_if_retrievable(
    field: str, realia_repository: MongoRealiaRepository, client
) -> None:
    insert_stored(realia_repository, HEALTHY_DOCUMENT)
    insert_stored(realia_repository, {"_id": "Legacy", field: None})

    listed_identifiers = client.simulate_get("/realia/all").json
    legacy_status = client.simulate_get("/realia/Legacy").status

    assert "Anu" in listed_identifiers
    assert ("Legacy" in listed_identifiers) == (legacy_status == falcon.HTTP_OK)


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
        insert_stored(realia_repository, {"_id": f"Null-{field}", field: None})
    for document in UNLOADABLE_DOCUMENTS:
        insert_stored(realia_repository, document)
    insert_stored(realia_repository, {"_id": 42, "type": ["x"]})

    listed_identifiers = client.simulate_get("/realia/all").json
    unloadable_identifiers = {document["_id"] for document in UNLOADABLE_DOCUMENTS}

    assert "Anu" in listed_identifiers
    assert unloadable_identifiers.isdisjoint(listed_identifiers)
    for identifier in listed_identifiers:
        assert client.simulate_get(f"/realia/{identifier}").status == falcon.HTTP_OK


@pytest.mark.parametrize("reference_id", NON_STRING_REFERENCE_IDS)
def test_entry_with_non_string_reallexikon_reference_id_is_retrievable(
    reference_id: object, realia_repository: MongoRealiaRepository, client
) -> None:
    reallexikon = [{"id": "r", "reference": {"id": reference_id}}]
    insert_stored(realia_repository, {"_id": "Legacy", "reallexikon": reallexikon})

    listed_identifiers = client.simulate_get("/realia/all").json
    entry = client.simulate_get("/realia/Legacy")

    assert listed_identifiers == ["Legacy"]
    assert entry.status == falcon.HTTP_OK
    assert entry.json["reallexikon"][0]["reference"] is None
