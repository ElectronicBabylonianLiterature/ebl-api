import json
import re
from marshmallow import ValidationError
import pytest
import os
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.io.fragments.importer import (
    validate,
    load_data,
    validate_id,
    ensure_unique,
)

from ebl.tests.factories.fragment import LemmatizedFragmentFactory


FRAGMENT = LemmatizedFragmentFactory.build()


@pytest.fixture
def valid_fragment_data() -> dict:
    return FragmentSchema().dump(FRAGMENT)


def mock_json_file(contents, path) -> os.PathLike:
    path = path / "test.json"
    with path.open("w") as tmp_file:
        tmp_file.write(contents)
    return path


def test_load_json(tmp_path):
    contents = {"test": "data"}
    path = str(mock_json_file(json.dumps(contents), tmp_path))
    assert load_data([path]) == {path: contents}


def test_load_invalid_json(tmp_path):
    contents = "{'broken_file': None}"
    path = str(mock_json_file(contents, tmp_path))

    with pytest.raises(ValueError, match=f"Invalid JSON: {path}"):
        load_data([path])


def test_validation(valid_fragment_data):
    validate(valid_fragment_data)


def test_missing_required_field(valid_fragment_data):
    del valid_fragment_data["museumNumber"]

    with pytest.raises(
        ValidationError,
        match=re.escape(
            "Invalid data in mock.json: {'museumNumber': ['Missing data for required field.']}"
        ),
    ):
        validate(valid_fragment_data, "mock.json")


def test_invalid_input_type(valid_fragment_data):
    with pytest.raises(
        ValidationError,
        match=re.escape(
            "Invalid data in mock.json: {'_schema': ['Invalid input type.']}"
        ),
    ):

        validate("invalid input", "mock.json")


def test_ensure_id(valid_fragment_data):
    valid_fragment_data["_id"] = "mock.id"
    validate_id(valid_fragment_data, "mock.json")


def test_missing_id(valid_fragment_data):
    with pytest.raises(ValidationError, match="Missing _id in mock.json"):
        validate_id(valid_fragment_data, "mock.json")


def test_invalid_id(valid_fragment_data):
    valid_fragment_data["_id"] = "invalid museum number"
    with pytest.raises(
        ValueError, match="'invalid museum number' is not a valid museum number"
    ):
        validate_id(valid_fragment_data)


def test_ensure_unique(
    valid_fragment_data, fragment_repository: MongoFragmentRepository
):
    valid_fragment_data["_id"] = "mock.number"
    fragment_repository.create(FRAGMENT)
    ensure_unique(valid_fragment_data, fragment_repository._fragments, "mock.json")


def test_ensure_unique_duplicate(
    valid_fragment_data, fragment_repository: MongoFragmentRepository
):
    museum_number = str(FRAGMENT.number)
    valid_fragment_data["_id"] = museum_number
    fragment_repository.create(FRAGMENT)
    with pytest.raises(
        ValidationError, match=f"ID {museum_number} of file mock.json already exists"
    ):
        ensure_unique(valid_fragment_data, fragment_repository._fragments, "mock.json")


# TODO: test write to db
