from abc import ABC, abstractmethod
from enum import Enum
from typing import Type, Optional, Any, List, Union, Sequence, cast

from marshmallow import fields  # pyre-ignore


class EnumField(fields.Field, ABC):  # pyre-ignore[11]
    default_error_messages = {
        "invalid_value": "Invalid value.",
        "not_enum": "Not a valid Enum.",
    }

    def __init__(self, enum_class: Type[Enum], **kwargs):
        self._enum_class = enum_class
        super().__init__(enum=self._values(), **kwargs)  # pyre-ignore[28]

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[Union[str, int]]:
        if isinstance(value, Enum) or value is None:
            return super()._serialize(  # pyre-ignore[16]
                (self._serialize_enum(value) if value is not None else None),
                attr,
                obj,
                **kwargs
            )
        else:
            raise self.make_error("not_enum")  # pyre-ignore[16]

    def _deserialize(self, value, attr, data, **kwargs) -> Any:
        try:
            return self._deserialize_enum(
                super()._deserialize(value, attr, data, **kwargs)  # pyre-ignore[16]
            )
        except (KeyError, ValueError) as error:
            raise self.make_error("invalid_value") from error  # pyre-ignore[16]

    @abstractmethod
    def _serialize_enum(self, value: Enum) -> Union[int, str]:
        ...

    @abstractmethod
    def _deserialize_enum(self, value: Union[int, str]) -> Enum:
        ...

    @abstractmethod
    def _values(self) -> Sequence[Union[int, str]]:
        ...


class ValueEnum(EnumField):
    def _serialize_enum(self, value: Enum) -> Union[int, str]:
        return value.value

    def _deserialize_enum(self, value: Union[int, str]) -> Enum:
        return self._enum_class(value)

    def _values(self) -> List[Union[int, str]]:
        return [e.value for e in self._enum_class]


class NameEnum(EnumField):
    def _serialize_enum(self, value: Enum) -> str:
        return value.name

    def _deserialize_enum(self, value: Union[int, str]) -> Enum:
        return self._enum_class[cast(str, value)]

    def _values(self) -> List[str]:
        return [e.name for e in self._enum_class]
