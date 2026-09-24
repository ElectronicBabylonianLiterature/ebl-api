from ebl.bibliography.domain.bibliography_entry import BIBLIOGRAPHY_ALIAS_SCHEMA

NON_BLANK_STRING_SCHEMA = {"type": "string", "minLength": 1, "pattern": r"\S"}

BIBLIOGRAPHY_IDENTITY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "addAliases": {
            "type": "array",
            "items": {
                "allOf": [
                    BIBLIOGRAPHY_ALIAS_SCHEMA,
                    {"properties": {"value": NON_BLANK_STRING_SCHEMA}},
                ]
            },
            "minItems": 1,
        },
        "removeAliases": {
            "type": "array",
            "items": NON_BLANK_STRING_SCHEMA,
            "minItems": 1,
        },
        "citationKey": {
            **NON_BLANK_STRING_SCHEMA,
            "type": ["string", "null"],
        },
        "deprecateTo": NON_BLANK_STRING_SCHEMA,
        "reactivate": {"type": "boolean", "const": True},
    },
    "minProperties": 1,
    "additionalProperties": False,
    "not": {"required": ["deprecateTo", "reactivate"]},
}
