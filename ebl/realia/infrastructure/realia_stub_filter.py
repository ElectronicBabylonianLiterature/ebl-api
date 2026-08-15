from typing import Sequence

EXACTLY_ONE_CROSS_REFERENCE = 1

OWN_CONTENT_ARRAY_FIELDS: Sequence[str] = (
    "afoRegister",
    "references",
    "afoCrossReferences",
    "relatedTerms",
    "type",
    "wikidataId",
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
        "$switch": {
            "branches": [
                {
                    "case": {"$eq": [{"$type": reference}, "string"]},
                    "then": {"$ne": [reference, ""]},
                },
                {
                    "case": {"$eq": [{"$type": reference}, "object"]},
                    "then": {"$ne": [{"$ifNull": [f"{reference}.id", ""]}, ""]},
                },
            ],
            "default": False,
        }
    }
