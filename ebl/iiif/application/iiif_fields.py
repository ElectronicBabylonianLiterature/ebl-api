from typing import Any, Mapping, Optional, Sequence, Tuple

from marshmallow import Schema, fields, post_dump

from ebl.iiif.domain.language_map import LanguageMap

EMPTY_CONTAINERS: Tuple[object, ...] = ((), [], {})


class LanguageMapField(fields.Field):
    def _serialize(
        self, value: Optional[LanguageMap], attr, obj, **kwargs
    ) -> Optional[Mapping[str, Sequence[str]]]:
        return None if value is None else value.to_dict()


class OmitEmptyMixin(Schema):
    @post_dump
    def remove_empty_values(self, data: dict, **kwargs) -> dict:
        return {key: value for key, value in data.items() if not _is_empty(value)}


def _is_empty(value: Any) -> bool:
    return value is None or any(value == empty for empty in EMPTY_CONTAINERS)
