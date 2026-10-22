import json
from typing import cast

import pytest
from pymongo.errors import BulkWriteError

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.io.fragments.fragment_writer import stored_fragment_of, write_to_db
from ebl.io.fragments.importer import (
    canonicalize,
    load_data,
    set_word_ids,
    validate,
)
from ebl.tests.io.fragment_importer_test_helpers import mock_json_file
from ebl.tests.transliteration.storage_test_helpers import has_key, stored_dump
from ebl.transliteration.application.text_schema import TextSchema


def stored_shape_of(fragment_data: dict, fragment) -> dict:
    return {**fragment_data, "text": stored_dump(TextSchema(), fragment.text)}


def test_import_persists_canonical_schema_output(
    tmp_path,
    fragment,
    fragment_repository,
    fragments_collection,
    seeded_provenance_service,
):
    schema = FragmentSchema(context={"provenance_service": seeded_provenance_service})
    data = cast(dict, schema.dump(fragment))
    data["_id"] = str(fragment.number)
    data["acquisitions"][0]["date"] = str(data["acquisitions"][0]["date"])
    data["unexpectedLegacyField"] = "junk"
    path = mock_json_file(json.dumps(data), tmp_path)

    [fragment_data] = load_data([path]).values()
    validate(fragment_data, provenance_service=seeded_provenance_service)
    canonical = canonicalize(fragment_data, seeded_provenance_service)
    write_to_db([canonical], fragments_collection)

    stored = fragments_collection.find_one_by_id(str(fragment.number))
    assert stored == stored_shape_of(canonical, fragment)
    assert "unexpectedLegacyField" not in stored
    assert isinstance(stored["acquisitions"][0]["date"], int)

    round_tripped = fragment_repository.query_by_museum_number(fragment.number)
    assert round_tripped.acquisitions == fragment.acquisitions
    assert round_tripped.text == fragment.text


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
    assert fragments_collection.find_one_by_id("mock.number") == stored_shape_of(
        valid_fragment_data, fragment
    )


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


def test_stored_fragment_omits_default_token_fields(valid_fragment_data):
    stored = stored_fragment_of(valid_fragment_data)

    assert has_key(valid_fragment_data["text"], "erasure")
    assert not has_key(stored["text"], "erasure")
    assert {key: value for key, value in stored.items() if key != "text"} == {
        key: value for key, value in valid_fragment_data.items() if key != "text"
    }


def test_stored_fragment_keeps_word_ids(valid_fragment_data):
    with_ids = set_word_ids(valid_fragment_data)

    stored = stored_fragment_of(with_ids)

    assert json.dumps(stored["text"]).count('"id": "Word-') == json.dumps(
        with_ids["text"]
    ).count('"id": "Word-')
    assert has_key(stored["text"], "id")


def test_stored_fragment_without_text_is_unchanged():
    fragment_data = {"_id": "X.1", "description": ""}

    assert stored_fragment_of(fragment_data) == fragment_data
