from enum import Enum
from marshmallow import Schema
from ebl.schemas import ValueEnum, NameEnum


class TestEnum(Enum):

    ONE = "one"
    TWO = "two"


class TestSchema(Schema):
    value = ValueEnum(TestEnum, required=True)
    name = NameEnum(TestEnum, required=True)


def test_value_enum():
    obj = {"value": TestEnum.ONE, "name": TestEnum.TWO}
    obj_deserialized = TestSchema().dump(obj)

    assert obj_deserialized == {"value": "one", "name": "TWO"}


def test_value_enum_none():
    obj = {"value": None, "name": None}
    obj_deserialized = TestSchema().dump(obj)

    assert obj_deserialized == {"value": None, "name": None}
