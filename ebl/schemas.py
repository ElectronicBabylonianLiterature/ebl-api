from abc import ABC, abstractmethod
from enum import Enum
from typing import Type, Any

from marshmallow import fields  # pyre-ignore[21]


class EnumField(fields.Field, ABC):  # pyre-ignore[11]
    default_error_messages = {
        "invalid_value": "Invalid value.",
        "not_enum": "Not a valid Enum.",
    }

    def __init__(self, enum_class: Type[Enum], **kwargs):
        self._enum_class = enum_class
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, Enum) or value is None:
            return self._serialize_enum(value) if value is not None else None
        else:
            raise self.make_error("not_enum")

    def _deserialize(self, value, attr, data, **kwargs) -> Any:
        try:
            return self._deserialize_enum(value)
        except (KeyError, ValueError) as error:
            raise self.make_error("invalid_value") from error  # pyre-ignore[16]

    @abstractmethod
    def _serialize_enum(self, value: Enum):
        ...

    @abstractmethod
    def _deserialize_enum(self, value) -> Enum:
        ...


class StringValueEnum(EnumField):
    def _serialize_enum(self, value: Enum) -> str:
        return value.value

    def _deserialize_enum(self, value: str) -> Enum:
        return self._enum_class(value)


class NameEnum(EnumField):
    def _serialize_enum(self, value: Enum) -> str:
        return value.name

    def _deserialize_enum(self, value: str) -> Enum:
        return self._enum_class[value]


class IntValueEnum(EnumField):
    def _serialize_enum(self, value: Enum) -> int:
        return value.value

    def _deserialize_enum(self, value: int) -> Enum:
        return self._enum_class(value)
