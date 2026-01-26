from abc import ABC, abstractmethod
from enum import Enum
from typing import Type, Any

from marshmallow import fields

from ebl.common.domain.scopes import Scope
from ebl.common.domain.project import ResearchProject
from ebl.common.domain.stage import Stage


class EnumField(fields.Field, ABC):
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
            raise self.make_error("invalid_value") from error

    @abstractmethod
    def _serialize_enum(self, value): ...

    @abstractmethod
    def _deserialize_enum(self, value) -> Enum: ...


class ValueEnumField(EnumField):
    def _serialize_enum(self, value: Enum) -> Any:
        return value.value

    def _deserialize_enum(self, value: Any) -> Enum:
        return self._enum_class(value)


class NameEnumField(EnumField):
    def _serialize_enum(self, value: Enum) -> str:
        return value.name

    def _deserialize_enum(self, value: str) -> Enum:
        return self._enum_class[value]


class StageField(EnumField):
    def __init__(self, **kwargs):
        super().__init__(Stage, **kwargs)

    def _serialize_enum(self, value: Stage) -> str:
        return value.long_name

    def _deserialize_enum(self, value: str) -> Enum:
        return Stage.from_name(value)


class ScopeField(EnumField):
    def __init__(self, **kwargs):
        super().__init__(Scope, **kwargs)

    def _serialize_enum(self, value: Scope) -> str:
        return str(value)

    def _deserialize_enum(self, value: str) -> Enum:
        return Scope.from_string(value)


class ResearchProjectField(EnumField):
    def __init__(self, **kwargs):
        super().__init__(ResearchProject, **kwargs)

    def _serialize_enum(self, value: ResearchProject) -> str:
        return value.abbreviation

    def _deserialize_enum(self, value: str) -> Enum:
        return ResearchProject.from_abbreviation(value)
