import json
from typing import Any, Dict, cast

from marshmallow import Schema

from ebl.transliteration.application.storage_serialization import (
    storage_serialization,
)


def stored_dump(schema: Schema, value: Any) -> Dict[str, Any]:
    with storage_serialization():
        return cast(Dict[str, Any], schema.dump(value))


def has_key(document: Any, key: str) -> bool:
    return f'"{key}"' in json.dumps(document, default=str)
