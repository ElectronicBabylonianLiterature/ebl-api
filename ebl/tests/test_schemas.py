from enum import Enum

import pytest  # pyre-ignore
from marshmallow import Schema, ValidationError  # pyre-ignore

from ebl.schemas import StringValueEnum, NameEnum


class _TestEnumStr(Enum):
    ONE = "one"
    TWO = "two"


class _TestEnumInt(Enum):
    ONE = 0
    TWO = 1


class _TestSchemaStr(Schema):  # pyre-ignore[11]
    value = StringValueEnum(_TestEnumStr, required=True, allow_none=True)
    name = NameEnum(_TestEnumStr, required=True, allow_none=True)


class _TestSchemaInt(Schema):
    value = StringValueEnum(_TestEnumInt, required=True, allow_none=True)
    name = NameEnum(_TestEnumInt, required=True, allow_none=True)


def test_str_value_enum():
    obj = {"value": _TestEnumStr.ONE, "name": _TestEnumStr.TWO}
    obj_deserialized = _TestSchemaStr().dump(obj)
    obj_dict = {"value": "one", "name": "TWO"}

    assert obj_deserialized == obj_dict
    assert _TestSchemaStr().load(obj_dict) == obj


def test_int_value_enum():
    obj = {"value": _TestEnumInt.ONE, "name": _TestEnumInt.TWO}
    obj_deserialized = _TestSchemaInt().dump(obj)
    obj_dict = {"value": 0, "name": "TWO"}

    assert obj_deserialized == obj_dict
    assert _TestSchemaInt().load(obj_dict) == obj


def test_value_enum_none():
    obj = {"value": None, "name": None}
    obj_deserialized = _TestSchemaStr().dump(obj)
    obj_dict = {"value": None, "name": None}

    assert obj_deserialized == obj_dict
    assert _TestSchemaStr().load(obj_dict) == obj


def test_value_enum_exception():
    with pytest.raises(ValidationError):
        obj = {"value": "not an enum", "name": _TestEnumStr.TWO}
        _TestSchemaStr().dump(obj)

    with pytest.raises(ValidationError):
        obj_dict = {"value": "invalid value", "name": "TWO"}
        _TestSchemaStr().load(obj_dict)
