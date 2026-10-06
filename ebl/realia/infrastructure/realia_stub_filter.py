from typing import Sequence

EXACTLY_ONE_CROSS_REFERENCE = 1
SINGLE_REALLEXIKON_ENTRY = 1

OWN_CONTENT_ARRAY_FIELDS: Sequence[str] = (
    "afoRegister",
    "references",
    "afoCrossReferences",
)


def non_redirect_stub_expression() -> dict:
    return {"$not": [_is_redirect_stub_expression()]}


def _is_redirect_stub_expression() -> dict:
    return {
        "$and": [
            {
                "$eq": [
                    _array_size("crossReferences"),
                    EXACTLY_ONE_CROSS_REFERENCE,
                ]
            },
            {"$not": [_has_own_content_expression()]},
        ]
    }


def _has_own_content_expression() -> dict:
    return {
        "$or": [
            *({"$gt": [_array_size(field), 0]} for field in OWN_CONTENT_ARRAY_FIELDS),
            {"$gt": [_array_size("reallexikon"), SINGLE_REALLEXIKON_ENTRY]},
            {"$gt": [_resolvable_reallexikon_count(), 0]},
        ]
    }


def _as_array(value: str) -> dict:
    return {"$cond": [{"$isArray": value}, value, []]}


def _array_size(field: str) -> dict:
    return {"$size": _as_array(f"${field}")}


def _resolvable_reallexikon_count() -> dict:
    return {
        "$size": {
            "$filter": {
                "input": _as_array("$reallexikon"),
                "cond": _is_resolvable_reference("$$this.reference"),
            }
        }
    }


def _is_resolvable_reference(reference: str) -> dict:
    return {
        "$or": [
            _is_non_empty_string(reference),
            _is_non_empty_string(f"{reference}.id"),
        ]
    }


def _is_non_empty_string(value: str) -> dict:
    return {
        "$and": [
            {"$eq": [{"$type": value}, "string"]},
            {"$ne": [value, ""]},
        ]
    }
