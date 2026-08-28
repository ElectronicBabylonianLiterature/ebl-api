"""Request contract for the trusted bibliography identity operation."""

from ebl.bibliography.domain.bibliography_entry import BIBLIOGRAPHY_ALIAS_SCHEMA

BIBLIOGRAPHY_IDENTITY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "addAliases": {
            "type": "array",
            "items": {
                "allOf": [
                    BIBLIOGRAPHY_ALIAS_SCHEMA,
                    {"properties": {"value": {"minLength": 1}}},
                ]
            },
            "minItems": 1,
        },
        "removeAliases": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "minItems": 1,
        },
        "citationKey": {"type": ["string", "null"], "minLength": 1},
        "deprecateTo": {"type": "string", "minLength": 1},
        "reactivate": {"type": "boolean", "const": True},
    },
    "minProperties": 1,
    "additionalProperties": False,
    "not": {"required": ["deprecateTo", "reactivate"]},
}
