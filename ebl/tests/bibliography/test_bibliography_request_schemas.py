"""The route contracts derive from the stored schema without sharing it."""

import jsonschema
import pytest

from ebl.bibliography.domain.bibliography_entry import (
    CSL_JSON_SCHEMA,
    DUPLICATE_OVERRIDE_JSON_SCHEMA,
    PARTNER_CSL_JSON_SCHEMA,
    PARTNER_DUPLICATE_OVERRIDE_JSON_SCHEMA,
    SERVER_OWNED_BIBLIOGRAPHY_FIELDS,
)
from ebl.bibliography.domain.bibliography_requests import (
    DUPLICATE_CANDIDATE_JSON_SCHEMA,
    INTERNAL_CREATE_JSON_SCHEMA,
    INTERNAL_METADATA_UPDATE_JSON_SCHEMA,
)

SCHEMAS = {
    "stored": CSL_JSON_SCHEMA,
    "create": INTERNAL_CREATE_JSON_SCHEMA,
    "update": INTERNAL_METADATA_UPDATE_JSON_SCHEMA,
    "partner": PARTNER_CSL_JSON_SCHEMA,
    "duplicate_candidate": DUPLICATE_CANDIDATE_JSON_SCHEMA,
}
REQUEST_CONTRACTS = sorted(name for name in SCHEMAS if name != "stored")


def properties(schema) -> dict:
    return schema["properties"]


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_every_contract_is_a_valid_schema(name):
    jsonschema.Draft7Validator.check_schema(SCHEMAS[name])


def test_create_drops_the_server_owned_properties():
    assert set(properties(INTERNAL_CREATE_JSON_SCHEMA)).isdisjoint(
        SERVER_OWNED_BIBLIOGRAPHY_FIELDS
    )


def test_create_keeps_every_client_editable_property():
    assert set(properties(INTERNAL_CREATE_JSON_SCHEMA)) == (
        set(properties(CSL_JSON_SCHEMA)) - SERVER_OWNED_BIBLIOGRAPHY_FIELDS
    )


def test_update_keeps_the_server_owned_properties_for_round_tripping():
    assert set(properties(INTERNAL_METADATA_UPDATE_JSON_SCHEMA)) == set(
        properties(CSL_JSON_SCHEMA)
    )


def test_update_keeps_the_stored_shape_of_every_property():
    assert properties(INTERNAL_METADATA_UPDATE_JSON_SCHEMA) == properties(
        CSL_JSON_SCHEMA
    )


def test_only_the_stored_schema_owns_the_lifecycle_invariant():
    assert "allOf" in CSL_JSON_SCHEMA
    assert "allOf" not in INTERNAL_CREATE_JSON_SCHEMA
    assert "allOf" not in INTERNAL_METADATA_UPDATE_JSON_SCHEMA


def test_the_stored_schema_still_rejects_an_invalid_tombstone():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {"id": "X", "type": "book", "deprecated": True}, CSL_JSON_SCHEMA
        )


def test_the_update_contract_accepts_a_legacy_stored_null_redirect():
    jsonschema.validate(
        {"id": "X", "type": "book", "redirectTo": None},
        INTERNAL_METADATA_UPDATE_JSON_SCHEMA,
    )


def test_duplicate_candidate_contract_drops_the_server_owned_properties():
    assert set(properties(DUPLICATE_CANDIDATE_JSON_SCHEMA)).isdisjoint(
        SERVER_OWNED_BIBLIOGRAPHY_FIELDS
    )


def test_duplicate_candidate_contract_has_no_lifecycle_invariant():
    assert "allOf" not in DUPLICATE_CANDIDATE_JSON_SCHEMA
    error = None
    try:
        jsonschema.validate(
            {"type": "book", "deprecated": True}, DUPLICATE_CANDIDATE_JSON_SCHEMA
        )
    except jsonschema.ValidationError as validation_error:
        error = validation_error

    assert error is not None
    assert "redirectTo' is a required property" not in error.message


def test_duplicate_candidate_contract_accepts_a_partner_style_id():
    jsonschema.validate(
        {"type": "book", "id": "10.1234/abc"}, DUPLICATE_CANDIDATE_JSON_SCHEMA
    )


@pytest.mark.parametrize("name", ["create", "update"])
def test_both_contracts_require_a_canonical_id(name):
    assert SCHEMAS[name]["required"] == ["type", "id"]
    assert SCHEMAS[name]["additionalProperties"] is False


@pytest.mark.parametrize("name", REQUEST_CONTRACTS)
def test_a_contract_does_not_alias_the_stored_schema(name):
    schema = SCHEMAS[name]

    assert schema is not CSL_JSON_SCHEMA
    assert properties(schema) is not properties(CSL_JSON_SCHEMA)
    for field, definition in properties(schema).items():
        if field in properties(CSL_JSON_SCHEMA):
            assert definition is not properties(CSL_JSON_SCHEMA)[field]


def test_the_partner_override_contract_does_not_alias_its_base_or_the_partner_contract():
    schema = PARTNER_DUPLICATE_OVERRIDE_JSON_SCHEMA
    embedded_entry = properties(schema)["bibliographyEntry"]

    assert schema["required"] is not DUPLICATE_OVERRIDE_JSON_SCHEMA["required"]
    assert embedded_entry is not PARTNER_CSL_JSON_SCHEMA
    assert properties(embedded_entry) is not properties(PARTNER_CSL_JSON_SCHEMA)


def test_the_contracts_do_not_alias_each_other():
    create_properties = properties(INTERNAL_CREATE_JSON_SCHEMA)
    update_properties = properties(INTERNAL_METADATA_UPDATE_JSON_SCHEMA)

    for field, definition in create_properties.items():
        assert definition is not update_properties[field]


def test_mutating_a_contract_leaves_the_stored_schema_intact():
    stored_type = properties(CSL_JSON_SCHEMA)["title"]["type"]
    properties(INTERNAL_CREATE_JSON_SCHEMA)["title"]["type"] = "number"
    try:
        assert properties(CSL_JSON_SCHEMA)["title"]["type"] == stored_type
        assert (
            properties(INTERNAL_METADATA_UPDATE_JSON_SCHEMA)["title"]["type"]
            == stored_type
        )
    finally:
        properties(INTERNAL_CREATE_JSON_SCHEMA)["title"]["type"] = stored_type


def test_mutating_the_partner_contract_leaves_the_stored_schema_intact():
    stored_type = properties(CSL_JSON_SCHEMA)["title"]["type"]
    properties(PARTNER_CSL_JSON_SCHEMA)["title"]["type"] = "number"
    try:
        assert properties(CSL_JSON_SCHEMA)["title"]["type"] == stored_type
        assert (
            properties(DUPLICATE_CANDIDATE_JSON_SCHEMA)["title"]["type"] == stored_type
        )
    finally:
        properties(PARTNER_CSL_JSON_SCHEMA)["title"]["type"] = stored_type
