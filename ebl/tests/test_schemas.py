from enum import Enum

import pytest
from marshmallow import Schema, ValidationError

from ebl.schemas import ValueEnum, NameEnum


class _TestEnum(Enum):
    ONE = "one"
    TWO = "two"


class _TestSchema(Schema):
    value = ValueEnum(_TestEnum, required=True, allow_none=True)
    name = NameEnum(_TestEnum, required=True, allow_none=True)


def test_value_enum():
    obj = {"value": _TestEnum.ONE, "name": _TestEnum.TWO}
    obj_deserialized = _TestSchema().dump(obj)
    obj_dict = {"value": "one", "name": "TWO"}

    assert obj_deserialized == obj_dict
    assert _TestSchema().load(obj_dict) == obj


def test_value_enum_none():
    obj = {"value": None, "name": None}
    obj_deserialized = _TestSchema().dump(obj)
    obj_dict = {"value": None, "name": None}

    assert obj_deserialized == obj_dict
    assert _TestSchema().load(obj_dict) == obj


def test_value_enum_exception():
    with pytest.raises(ValidationError):
        obj = {"value": "not an enum", "name": _TestEnum.TWO}
        _TestSchema().dump(obj)

    with pytest.raises(ValidationError):
        obj_dict = {"value": "invalid value", "name": "TWO"}
        _TestSchema().load(obj_dict)
