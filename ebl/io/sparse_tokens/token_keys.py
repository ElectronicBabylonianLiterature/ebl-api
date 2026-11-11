from collections import Counter
from typing import Any, Dict, FrozenSet, List

from ebl.transliteration.application.storage_serialization import (
    OMIT_FROM_STORAGE,
    OMIT_FROM_STORAGE_WHEN_DEFAULT,
    stored_default,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema

TOKEN_TYPES = frozenset(OneOfTokenSchema.type_schemas)
STORAGE_MARKERS = (OMIT_FROM_STORAGE, OMIT_FROM_STORAGE_WHEN_DEFAULT)


def omittable_token_keys() -> FrozenSet[str]:
    return frozenset(
        field.data_key or name
        for schema in OneOfTokenSchema.type_schemas.values()
        for name, field in schema._declared_fields.items()
        if any(field.metadata.get(marker, False) for marker in STORAGE_MARKERS)
    )


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


OMITTABLE_TOKEN_KEYS = omittable_token_keys()
DERIVED_TOKEN_KEYS = derived_token_keys()
STORED_TOKEN_DEFAULTS = stored_token_defaults()


def is_token(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("type"), str)
        and value["type"] in TOKEN_TYPES
    )


def token_key_counts(value: Any) -> Counter:
    counts: Counter = Counter()
    if isinstance(value, list):
        for item in value:
            counts.update(token_key_counts(item))
    elif isinstance(value, dict):
        if is_token(value):
            counts.update(value.keys())
        for item in value.values():
            counts.update(token_key_counts(item))
    return counts


def dropped_token_keys(original: Any, rewritten: Any) -> FrozenSet[str]:
    before = token_key_counts(original)
    after = token_key_counts(rewritten)
    return frozenset(
        key
        for key, count in before.items()
        if after[key] < count and key not in OMITTABLE_TOKEN_KEYS
    )


def is_legacy_or_multi_part_name(token: Dict[str, Any]) -> bool:
    return len(token.get("nameParts", [])) > 1 and not token.get("nameBreaks")


def token_needs_rewrite(token: Dict[str, Any]) -> bool:
    return is_legacy_or_multi_part_name(token) or any(
        key in DERIVED_TOKEN_KEYS or value in STORED_TOKEN_DEFAULTS.get(key, [])
        for key, value in token.items()
    )


def needs_sparse_rewrite(value: Any) -> bool:
    if isinstance(value, list):
        return any(needs_sparse_rewrite(item) for item in value)
    if not isinstance(value, dict):
        return False
    if is_token(value) and token_needs_rewrite(value):
        return True
    return any(needs_sparse_rewrite(item) for item in value.values())
