import pytest
from marshmallow import Schema, fields

from ebl.transliteration.application.storage_serialization import (
    OMIT_FROM_STORAGE_WHEN_DEFAULT,
    is_omitted_from_storage,
    is_storage_serialization,
    omit_stored_defaults,
    storage_serialization,
    stored_default,
)

OMIT = {OMIT_FROM_STORAGE_WHEN_DEFAULT: True}


class ExampleSchema(Schema):
    marked = fields.List(fields.String(), load_default=list, metadata=OMIT)
    renamed = fields.String(load_default="x", data_key="renamedKey", metadata=OMIT)
    unmarked = fields.List(fields.String(), load_default=list)
    required = fields.String(required=True, metadata=OMIT)


DEFAULTS = {"marked": [], "renamedKey": "x", "unmarked": [], "required": ""}


def test_storage_serialization_is_off_by_default():
    assert is_storage_serialization() is False


def test_storage_serialization_is_on_only_inside_the_block():
    with storage_serialization():
        assert is_storage_serialization() is True
    assert is_storage_serialization() is False


def fail_inside_storage_serialization() -> None:
    with storage_serialization():
        raise RuntimeError()


def test_storage_serialization_is_reset_after_an_error():
    with pytest.raises(RuntimeError):
        fail_inside_storage_serialization()
    assert is_storage_serialization() is False


def test_nested_storage_serialization_stays_on_until_the_outer_block_ends():
    with storage_serialization():
        with storage_serialization():
            pass
        assert is_storage_serialization() is True
    assert is_storage_serialization() is False


def test_stored_default_serializes_the_load_default():
    assert stored_default(ExampleSchema().fields["marked"]) == []
    assert stored_default(ExampleSchema().fields["renamed"]) == "x"


@pytest.mark.parametrize(
    "name,value,expected",
    [
        ("marked", [], True),
        ("marked", ["a"], False),
        ("unmarked", [], False),
        ("required", "", False),
    ],
)
def test_is_omitted_from_storage(name, value, expected):
    field = ExampleSchema().fields[name]

    assert is_omitted_from_storage(field, value) is expected


def test_omit_stored_defaults_keeps_everything_outside_storage():
    assert omit_stored_defaults(ExampleSchema(), DEFAULTS) == DEFAULTS


def test_omit_stored_defaults_drops_marked_defaults_by_data_key():
    with storage_serialization():
        stored = omit_stored_defaults(ExampleSchema(), DEFAULTS)

    assert stored == {"unmarked": [], "required": ""}


def test_omit_stored_defaults_keeps_marked_values_that_differ():
    data = {**DEFAULTS, "marked": ["a"], "renamedKey": "y"}

    with storage_serialization():
        assert omit_stored_defaults(ExampleSchema(), data) == data
