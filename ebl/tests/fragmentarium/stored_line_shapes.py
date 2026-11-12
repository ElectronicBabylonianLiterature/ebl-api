from typing import Any, Dict

from ebl.transliteration.application.token_schemas import OneOfTokenSchema

SPARSE_DEFAULTS: Dict[str, Any] = {"erasure": "NONE", "enclosureType": []}
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


def is_omittable_name_breaks(token: Dict[str, Any], key: str) -> bool:
    return (
        key == "nameBreaks"
        and token[key] == []
        and len(token.get("nameParts", [])) <= 1
    )


def is_token(value: Dict[str, Any]) -> bool:
    return isinstance(value.get("type"), str) and value["type"] in TOKEN_TYPES


def is_omitted_token_key(value: Dict[str, Any], key: str) -> bool:
    return is_token(value) and (
        is_omittable_token_field(key, value[key])
        or is_omittable_name_breaks(value, key)
    )


def sparse_tokens(value: Any) -> Any:
    if isinstance(value, list):
        return [sparse_tokens(item) for item in value]
    if not isinstance(value, dict):
        return value
    return {
        key: sparse_tokens(item)
        for key, item in value.items()
        if not is_omitted_token_key(value, key)
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
