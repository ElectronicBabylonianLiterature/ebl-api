from typing import Sequence

ABSENT_TYPES: Sequence[str] = ("missing", "null")

ARRAY_FIELDS: Sequence[str] = (
    "afoRegister",
    "references",
    "afoCrossReferences",
    "relatedTerms",
    "type",
    "wikidataId",
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
