from functools import partial
import json
import re
import attr
from marshmallow import ValidationError
import pymongo
import pytest
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from pymongo.errors import BulkWriteError
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.io.fragments.importer import (
    create_sort_index,
    load_collection,
    set_word_ids,
    validate,
    load_data,
    validate_id,
    ensure_unique,
    write_to_db,
    update_sort_keys,
)
from ebl.mongo_collection import MongoCollection

from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


MOCKFILE = "mock.json"

validate = partial(validate, filename=MOCKFILE)
validate_id = partial(validate_id, filename=MOCKFILE)
ensure_unique = partial(ensure_unique, filename=MOCKFILE)


@pytest.fixture
def fragment() -> Fragment:
    return LemmatizedFragmentFactory.build()


@pytest.fixture
def fragment_schema(seeded_provenance_service) -> FragmentSchema:
    return FragmentSchema(context={"provenance_service": seeded_provenance_service})


@pytest.fixture
def valid_fragment_data(fragment, fragment_schema) -> dict:
    return fragment_schema.dump(fragment)


@pytest.fixture
def fragments_collection(fragment_repository) -> MongoCollection:
    return fragment_repository._fragments


@pytest.fixture
def validate_fragment(seeded_provenance_service):
    return partial(
        validate, filename=MOCKFILE, provenance_service=seeded_provenance_service
    )


def mock_json_file(contents, path) -> str:
    path = path / "test.json"
    with path.open("w") as tmp_file:
        tmp_file.write(contents)
    return str(path)


def test_load_json(tmp_path):
    contents = {"test": "data"}
    path = mock_json_file(json.dumps(contents), tmp_path)
    assert load_data([path]) == {path: contents}


def test_load_collection(tmp_path):
    contents = [{"test": "data"}, {"foo": "bar"}]
    path = mock_json_file(json.dumps(contents), tmp_path)
    assert load_collection(path) == {
        f"{path}[{index}]": content for index, content in enumerate(contents)
    }


def test_load_invalid_json(tmp_path):
    contents = "{'broken_file': None}"
    path = mock_json_file(contents, tmp_path)

    with pytest.raises(ValueError, match=f"Invalid JSON: {path}"):
        load_data([path])


def test_validation(valid_fragment_data, validate_fragment):
    validate_fragment(valid_fragment_data)


def test_missing_required_field(valid_fragment_data, validate_fragment):
    del valid_fragment_data["museumNumber"]

    with pytest.raises(
        ValidationError,
        match=re.escape(
            f"Invalid data in {MOCKFILE}: "
            "{'museumNumber': ['Missing data for required field.']}"
        ),
    ):
        validate_fragment(valid_fragment_data)


def test_invalid_enum(valid_fragment_data, validate_fragment):
    unknown_period = "Neo-Foobarian"
    valid_fragment_data["script"]["period"] = unknown_period

    with pytest.raises(
        ValidationError,
        match=f"Invalid data in {MOCKFILE}: Unknown Period.long_name: {unknown_period}",
    ):
        validate_fragment(valid_fragment_data)


def test_invalid_input_type(valid_fragment_data, validate_fragment):
    with pytest.raises(
        ValidationError,
        match=re.escape(
            f"Invalid data in {MOCKFILE}: {{'_schema': ['Invalid input type.']}}"
        ),
    ):
        validate_fragment("invalid input")


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
    fragment,
    fragment_repository,
    fragments_collection,
):
    valid_fragment_data["_id"] = "mock.number"
    fragment_repository.create(fragment)
    ensure_unique(valid_fragment_data, fragments_collection)


def test_ensure_unique_duplicate(
    valid_fragment_data,
    fragment,
    fragment_repository,
    fragments_collection,
):
    museum_number = str(fragment.number)
    valid_fragment_data["_id"] = museum_number
    fragment_repository.create(fragment)
    with pytest.raises(
        ValidationError, match=f"ID {museum_number} of file {MOCKFILE} already exists"
    ):
        ensure_unique(valid_fragment_data, fragments_collection)


def test_write_to_db(
    valid_fragment_data,
    fragment_repository,
    fragment,
    fragments_collection,
):
    fragment_repository.create(fragment)
    valid_fragment_data["_id"] = "mock.number"

    assert write_to_db([valid_fragment_data], fragments_collection) == ["mock.number"]
    assert fragments_collection.count_documents({}) == 2
    assert fragments_collection.find_one_by_id("mock.number") == valid_fragment_data


def test_write_to_db_duplicate(
    valid_fragment_data,
    fragment,
    fragment_repository,
    fragments_collection,
):
    fragment_repository.create(fragment)
    valid_fragment_data["_id"] = str(fragment.number)

    with pytest.raises(BulkWriteError, match="E11000 duplicate key error"):
        write_to_db([valid_fragment_data], fragments_collection)


def test_update_sort_index(fragment, fragment_repository, fragments_collection):
    numbers = [1, 2, 3]
    for i in numbers:
        fragment_repository.create(
            attr.evolve(fragment, number=MuseumNumber.of(f"X.{i}"))
        )

    assert not fragments_collection.exists({"_sortKey": {"$exists": True}})

    update_sort_keys(fragments_collection)

    assert sorted(
        fragments_collection.find_many({}, projection={"_id": True, "_sortKey": True}),
        key=lambda entry: entry["_sortKey"],
    ) == [{"_id": f"X.{i}", "_sortKey": i - 1} for i in numbers]

    create_sort_index(fragments_collection)

    assert [("_sortKey", pymongo.ASCENDING)] in [
        index["key"] for index in fragments_collection.index_information().values()
    ]


def test_set_word_ids(valid_fragment_data, fragment_schema):
    data_with_ids = set_word_ids(valid_fragment_data)
    fragment = fragment_schema.load(data_with_ids)
    fragment_with_ids = fragment.set_text(fragment.text.set_token_ids())
    ids = [
        word.id_
        for line in fragment.text.text_lines
        for word in line.content
        if hasattr(word, "id_")
    ]
    expected_ids = [f"Word-{index + 1}" for index in range(len(ids))]

    assert ids and ids == expected_ids
    assert fragment_schema.load(data_with_ids) == fragment_with_ids
    assert fragment_schema.dump(fragment_with_ids) == data_with_ids
