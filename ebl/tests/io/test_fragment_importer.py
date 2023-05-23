from functools import partial
import json
import re
import attr
from marshmallow import ValidationError
import pytest
import os
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from pymongo.errors import BulkWriteError
from ebl.io.fragments.importer import (
    validate,
    load_data,
    validate_id,
    ensure_unique,
    write_to_db,
    create_sort_index,
)
from ebl.mongo_collection import MongoCollection

from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


FRAGMENT = LemmatizedFragmentFactory.build()
MOCKFILE = "mock.json"

validate = partial(validate, filename=MOCKFILE)
validate_id = partial(validate_id, filename=MOCKFILE)
ensure_unique = partial(ensure_unique, filename=MOCKFILE)


@pytest.fixture
def valid_fragment_data() -> dict:
    return FragmentSchema().dump(FRAGMENT)


@pytest.fixture
def fragments_collection(fragment_repository) -> MongoCollection:
    return fragment_repository._fragments


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
            f"Invalid data in {MOCKFILE}: "
            "{'museumNumber': ['Missing data for required field.']}"
        ),
    ):
        validate(valid_fragment_data)


def test_invalid_enum(valid_fragment_data):
    unknown_period = "Neo-Foobarian"
    valid_fragment_data["script"]["period"] = unknown_period

    with pytest.raises(
        ValidationError,
        match=f"Invalid data in {MOCKFILE}: Unknown enum long_name: {unknown_period}",
    ):
        validate(valid_fragment_data)


def test_invalid_input_type(valid_fragment_data):
    with pytest.raises(
        ValidationError,
        match=re.escape(
            f"Invalid data in {MOCKFILE}: {{'_schema': ['Invalid input type.']}}"
        ),
    ):

        validate("invalid input")


def test_ensure_id(valid_fragment_data):
    valid_fragment_data["_id"] = "mock.id"
    validate_id(valid_fragment_data)


def test_missing_id(valid_fragment_data):
    with pytest.raises(ValidationError, match=f"Missing _id in {MOCKFILE}"):
        validate_id(valid_fragment_data)


def test_invalid_id(valid_fragment_data):
    invalid_number = "invalid museum number"
    valid_fragment_data["_id"] = invalid_number
    with pytest.raises(
        ValidationError,
        match=f"id {invalid_number!r} of {MOCKFILE} is not a valid museum number",
    ):
        validate_id(valid_fragment_data)


def test_ensure_unique(
    valid_fragment_data,
    fragment_repository: MongoFragmentRepository,
    fragments_collection: MongoCollection,
):
    valid_fragment_data["_id"] = "mock.number"
    fragment_repository.create(FRAGMENT)
    ensure_unique(valid_fragment_data, fragments_collection)


def test_ensure_unique_duplicate(
    valid_fragment_data,
    fragment_repository: MongoFragmentRepository,
    fragments_collection: MongoCollection,
):
    museum_number = str(FRAGMENT.number)
    valid_fragment_data["_id"] = museum_number
    fragment_repository.create(FRAGMENT)
    with pytest.raises(
        ValidationError, match=f"ID {museum_number} of file {MOCKFILE} already exists"
    ):
        ensure_unique(valid_fragment_data, fragments_collection)


def test_write_to_db(
    valid_fragment_data,
    fragment_repository: MongoFragmentRepository,
    fragments_collection: MongoCollection,
):
    fragment_repository.create(FRAGMENT)
    valid_fragment_data["_id"] = "mock.number"

    assert write_to_db([valid_fragment_data], fragments_collection) == ["mock.number"]
    assert fragments_collection.count_documents({}) == 2
    assert fragments_collection.find_one_by_id("mock.number") == valid_fragment_data


def test_write_to_db_duplicate(
    valid_fragment_data,
    fragment_repository: MongoFragmentRepository,
    fragments_collection: MongoCollection,
):
    fragment_repository.create(FRAGMENT)
    valid_fragment_data["_id"] = str(FRAGMENT.number)

    with pytest.raises(BulkWriteError, match="E11000 duplicate key error"):
        write_to_db([valid_fragment_data], fragments_collection)


def test_create_sort_index(
    fragment_repository: MongoFragmentRepository, fragments_collection: MongoCollection
):
    for i in [3, 2, 1]:
        fragment_repository.create(
            attr.evolve(FRAGMENT, number=MuseumNumber.of(f"X.{i}"))
        )

    assert not fragments_collection.exists({"_sortKey": {"$exists": True}})

    create_sort_index(fragments_collection)

    assert sorted(
        fragments_collection.find_many({}, projection={"_id": True, "_sortKey": True}),
        key=lambda entry: entry["_sortKey"],
    ) == [{"_id": f"X.{i+1}", "_sortKey": i} for i in [0, 1, 2]]
