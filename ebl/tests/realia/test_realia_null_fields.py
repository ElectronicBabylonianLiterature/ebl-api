import falcon
import pytest
from marshmallow import ValidationError

from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.tests.realia.realia_repository_helpers import insert_stored

NULLABLE_FIELDS = [
    "realiaId",
    "relatedTerms",
    "type",
    "afoRegister",
    "references",
    "wikidataId",
    "reallexikon",
    "crossReferences",
    "afoCrossReferences",
]


@pytest.mark.parametrize("field", NULLABLE_FIELDS)
def test_null_field_loads_as_absent(field: str) -> None:
    loaded = RealiaEntrySchema().load({"_id": "Anu", field: None})

    assert loaded == RealiaEntrySchema().load({"_id": "Anu"})


def test_null_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RealiaEntrySchema().load({"_id": None})


def test_non_mapping_input_is_passed_through() -> None:
    assert RealiaEntrySchema().treat_null_as_absent(["Anu"]) == ["Anu"]


def test_wrong_element_type_is_still_rejected() -> None:
    with pytest.raises(ValidationError):
        RealiaEntrySchema().load({"_id": "Anu", "relatedTerms": [5]})


@pytest.mark.parametrize("field", NULLABLE_FIELDS)
def test_entry_with_null_field_is_retrievable(
    field: str, realia_repository: MongoRealiaRepository, client
) -> None:
    insert_stored(realia_repository, {"_id": "Bare"})
    insert_stored(realia_repository, {"_id": "Legacy", field: None})

    legacy_result = client.simulate_get("/realia/Legacy")
    bare_result = client.simulate_get("/realia/Bare")

    assert legacy_result.status == falcon.HTTP_OK
    assert legacy_result.json == {**bare_result.json, "_id": "Legacy"}
