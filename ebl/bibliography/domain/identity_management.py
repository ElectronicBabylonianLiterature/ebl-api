"""Request contract for the trusted bibliography identity operation.

The contract is a set of explicit commands rather than the full intended
identity state. Full-state replacement would turn an omitted array element
into a silent alias removal, and under concurrency it would overwrite another
operation's addition instead of conflicting with it. Explicit commands make a
removal deliberate and let the compare-and-set in the identity primitive turn
a concurrent change into a conflict.

Deprecation is expressed as `deprecateTo`/`reactivate` instead of the stored
`deprecated`/`redirectTo` pair so that an invalid tombstone cannot be
requested: there is no way to ask for `deprecated` without naming a target.
"""

from ebl.bibliography.domain.bibliography_entry import BIBLIOGRAPHY_ALIAS_SCHEMA

BIBLIOGRAPHY_IDENTITY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "addAliases": {
            "type": "array",
            "items": BIBLIOGRAPHY_ALIAS_SCHEMA,
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
