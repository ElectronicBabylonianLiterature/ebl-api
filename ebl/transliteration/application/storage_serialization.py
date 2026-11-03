from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator

from marshmallow import Schema, fields, missing

OMIT_FROM_STORAGE_WHEN_DEFAULT = "omit_from_storage_when_default"

_storage_serialization = ContextVar[bool]("storage_serialization", default=False)


@contextmanager
def storage_serialization() -> Iterator[None]:
    token = _storage_serialization.set(True)
    try:
        yield
    finally:
        _storage_serialization.reset(token)


def is_storage_serialization() -> bool:
    return _storage_serialization.get()


def stored_default(field: fields.Field) -> Any:
    default = field.load_default
    value = default() if callable(default) else default
    return field._serialize(value, None, None)


def is_omitted_from_storage(field: fields.Field, value: Any) -> bool:
    return (
        field.metadata.get(OMIT_FROM_STORAGE_WHEN_DEFAULT, False)
        and field.load_default is not missing
        and value == stored_default(field)
    )


def omit_stored_defaults(schema: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    if not is_storage_serialization():
        return data
    omitted = {
        field.data_key or name
        for name, field in schema.dump_fields.items()
        if is_omitted_from_storage(field, data.get(field.data_key or name, missing))
    }
    return {key: value for key, value in data.items() if key not in omitted}
