from enum import Enum

import pytest
from marshmallow import Schema, ValidationError

from ebl.schemas import ValueEnum, NameEnum


class TestEnum(Enum):

    ONE = "one"
    TWO = "two"


class TestSchema(Schema):
    value = ValueEnum(TestEnum, required=True, allow_none=True)
    name = NameEnum(TestEnum, required=True, allow_none=True)


def test_value_enum():
    obj = {"value": TestEnum.ONE, "name": TestEnum.TWO}
    obj_deserialized = TestSchema().dump(obj)
    obj_dict = {"value": "one", "name": "TWO"}

    assert obj_deserialized == obj_dict
    assert TestSchema().load(obj_dict) == obj


def test_value_enum_none():
    obj = {"value": None, "name": None}
    obj_deserialized = TestSchema().dump(obj)
    obj_dict = {"value": None, "name": None}

    assert obj_deserialized == obj_dict
    assert TestSchema().load(obj_dict) == obj


def test_value_enum_exception():
    with pytest.raises(ValidationError):
        obj = {"value": "not an enum", "name": TestEnum.TWO}
        TestSchema().dump(obj)

    with pytest.raises(ValidationError):
        obj_dict = {"value": "invalid value", "name": "TWO"}
        TestSchema().load(obj_dict)
