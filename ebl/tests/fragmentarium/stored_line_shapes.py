from typing import Any, Dict

from ebl.transliteration.application.token_schemas import OneOfTokenSchema

SPARSE_DEFAULTS: Dict[str, Any] = {"erasure": "NONE", "enclosureType": []}
STORAGE_DEFAULTS: Dict[str, Any] = {"erasure": "NONE", "nameBreaks": []}
TOKEN_TYPES = frozenset(OneOfTokenSchema.type_schemas)
TOKEN_LOAD_DEFAULTS: Dict[str, Any] = {
    "erasure": "NONE",
    "enclosureType": [],
    "modifiers": [],
    "flags": [],
    "sign": None,
    "surrogate": [],
    "variant": None,
    "alignment": None,
    "hasVariantAlignment": False,
    "hasOmittedAlignment": False,
    "namedEntities": [],
    "realia": [],
}
DERIVED_TOKEN_FIELDS = frozenset({"lemmatizable", "alignable"})


def is_omittable_token_field(key: str, value: Any) -> bool:
    return (
        key in DERIVED_TOKEN_FIELDS or TOKEN_LOAD_DEFAULTS.get(key, object()) == value
    )


def sparse_tokens(value: Any) -> Any:
    if isinstance(value, list):
        return [sparse_tokens(item) for item in value]
    if not isinstance(value, dict):
        return value
    is_token = isinstance(value.get("type"), str) and value["type"] in TOKEN_TYPES
    return {
        key: sparse_tokens(item)
        for key, item in value.items()
        if not (is_token and is_omittable_token_field(key, item))
    }


def sparse_shape(value: Any, defaults: Dict[str, Any] = SPARSE_DEFAULTS) -> Any:
    if isinstance(value, list):
        return [sparse_shape(item, defaults) for item in value]
    if isinstance(value, dict):
        return {
            key: sparse_shape(item, defaults)
            for key, item in value.items()
            if defaults.get(key, object()) != item
        }
    return value


def interleaved(parts: list, breaks: list) -> list:
    merged = []
    for index, part in enumerate(parts):
        merged.append(part)
        if index < len(breaks):
            merged.append(breaks[index])
    return merged


def legacy_shape(value: Any) -> Any:
    if isinstance(value, list):
        return [legacy_shape(item) for item in value]
    if not isinstance(value, dict):
        return value
    converted = {key: legacy_shape(item) for key, item in value.items()}
    if "nameBreaks" not in converted:
        return converted
    breaks = converted.pop("nameBreaks")
    return {**converted, "nameParts": interleaved(converted["nameParts"], breaks)}
