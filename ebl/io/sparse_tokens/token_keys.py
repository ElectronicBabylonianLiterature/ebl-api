from collections import Counter
from typing import Any, Dict, FrozenSet, List

from marshmallow.fields import Field

from ebl.transliteration.application.storage_serialization import (
    OMIT_FROM_STORAGE,
    OMIT_FROM_STORAGE_WHEN_DEFAULT,
    stored_default,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema

TOKEN_TYPES = frozenset(OneOfTokenSchema.type_schemas)
STORAGE_MARKERS = (OMIT_FROM_STORAGE, OMIT_FROM_STORAGE_WHEN_DEFAULT)


def is_marked(field: Field) -> bool:
    return any(field.metadata.get(marker, False) for marker in STORAGE_MARKERS)


def omittable_keys_by_type() -> Dict[str, FrozenSet[str]]:
    return {
        token_type: frozenset(
            field.data_key or name
            for name, field in schema._declared_fields.items()
            if is_marked(field)
        )
        for token_type, schema in OneOfTokenSchema.type_schemas.items()
    }


def derived_token_keys() -> FrozenSet[str]:
    return frozenset(
        field.data_key or name
        for schema in OneOfTokenSchema.type_schemas.values()
        for name, field in schema._declared_fields.items()
        if field.metadata.get(OMIT_FROM_STORAGE, False)
    )


def stored_token_defaults() -> Dict[str, List[Any]]:
    defaults: Dict[str, List[Any]] = {}
    for schema in OneOfTokenSchema.type_schemas.values():
        for name, field in schema._declared_fields.items():
            if field.metadata.get(OMIT_FROM_STORAGE_WHEN_DEFAULT, False):
                values = defaults.setdefault(field.data_key or name, [])
                value = stored_default(field)
                if value not in values:
                    values.append(value)
    return defaults


OMITTABLE_KEYS_BY_TYPE = omittable_keys_by_type()
OMITTABLE_TOKEN_KEYS = frozenset().union(*OMITTABLE_KEYS_BY_TYPE.values())
DERIVED_TOKEN_KEYS = derived_token_keys()
STORED_TOKEN_DEFAULTS = stored_token_defaults()


def is_token(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("type"), str)
        and value["type"] in TOKEN_TYPES
    )


def nested_values(value: Any) -> List[Any]:
    if isinstance(value, dict):
        return list(value.values())
    return list(value) if isinstance(value, list) else []


def key_counts(value: Any) -> Counter:
    counts: Counter = Counter(value.keys() if isinstance(value, dict) else ())
    for item in nested_values(value):
        counts.update(key_counts(item))
    return counts


def omittable_key_counts(value: Any) -> Counter:
    counts: Counter = Counter()
    if is_token(value):
        counts.update(set(value) & OMITTABLE_KEYS_BY_TYPE[value["type"]])
    for item in nested_values(value):
        counts.update(omittable_key_counts(item))
    return counts


def dropped_keys(original: Any, rewritten: Any) -> FrozenSet[str]:
    before = key_counts(original)
    after = key_counts(rewritten)
    allowed = omittable_key_counts(original)
    return frozenset(
        key for key, count in before.items() if count - after[key] > allowed[key]
    )


def name_part_count(token: Dict[str, Any]) -> int:
    parts = token.get("nameParts", [])
    return len(parts) if isinstance(parts, list) else 0


def is_legacy_name(token: Dict[str, Any]) -> bool:
    return name_part_count(token) > 1 and "nameBreaks" not in token


def is_stored_default(token: Dict[str, Any], key: str, value: Any) -> bool:
    if key == "nameBreaks" and name_part_count(token) > 1:
        return False
    return value in STORED_TOKEN_DEFAULTS.get(key, [])


def token_needs_rewrite(token: Dict[str, Any]) -> bool:
    return is_legacy_name(token) or any(
        key in DERIVED_TOKEN_KEYS or is_stored_default(token, key, value)
        for key, value in token.items()
    )


def needs_sparse_rewrite(value: Any) -> bool:
    if is_token(value) and token_needs_rewrite(value):
        return True
    return any(needs_sparse_rewrite(item) for item in nested_values(value))
