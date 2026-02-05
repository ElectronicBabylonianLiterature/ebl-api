from enum import Enum

import pytest
from marshmallow import Schema, ValidationError

from ebl.schemas import ValueEnumField, NameEnumField


class _TestEnumStr(Enum):
    ONE = "one"
    TWO = "two"


class _TestEnumInt(Enum):
    ONE = 0
    TWO = 1


class _TestSchemaStr(Schema):
    value = ValueEnumField(_TestEnumStr, required=True, allow_none=True)
    name = NameEnumField(_TestEnumStr, required=True, allow_none=True)


class _TestSchemaInt(Schema):
    value = ValueEnumField(_TestEnumInt, required=True, allow_none=True)
    name = NameEnumField(_TestEnumInt, required=True, allow_none=True)


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
