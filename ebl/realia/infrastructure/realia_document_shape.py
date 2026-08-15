from typing import Sequence

from ebl.realia.infrastructure.realia_stub_filter import OWN_CONTENT_ARRAY_FIELDS

ABSENT_TYPES: Sequence[str] = ("missing", "null")

ARRAY_FIELDS: Sequence[str] = (
    *OWN_CONTENT_ARRAY_FIELDS,
    "crossReferences",
    "reallexikon",
)


def well_formed_arrays_expression() -> dict:
    return {"$and": [_is_absent_or_array(f"${field}") for field in ARRAY_FIELDS]}


def _is_absent_or_array(value: str) -> dict:
    return {
        "$or": [
            {"$in": [{"$type": value}, list(ABSENT_TYPES)]},
            {"$isArray": value},
        ]
    }
