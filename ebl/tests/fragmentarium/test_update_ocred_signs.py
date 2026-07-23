import pytest
import os
import ebl.fragmentarium.update_ocred_signs as update_ocred_signs
from ebl.tests.fragmentarium.ocred_signs_test_helpers import (
    build_sample_fragments,
    build_sample_ocred_signs_file,
)


@pytest.fixture
def sample_fragments(database):
    return build_sample_fragments(database)


@pytest.fixture
def sample_ocred_signs_file():
    return build_sample_ocred_signs_file()


def test_update_single_fragment(database, sample_fragments):
    collection = database["fragments"]
    number_str = "K.2"
    ocred_signs = "ABZ100 \nABZ101"

    original_fragment = collection.find_one({"museumNumber.number": "2"})
    assert (
        "ocredSigns" not in original_fragment or original_fragment["ocredSigns"] == ""
    )

    result = update_ocred_signs.update_single_fragment(
        collection, number_str, ocred_signs
    )

    assert result is True
    updated_fragment = collection.find_one({"museumNumber.number": "2"})
    assert updated_fragment is not None
    assert updated_fragment["ocredSigns"] == ocred_signs


def test_update_single_fragment_without_match(database, sample_fragments):
    collection = database["fragments"]
    nonexistent_number = "K.999"
    ocred_signs = "ABZ999 \nABZ998"

    original_fragment = collection.find_one({"museumNumber.number": "999"})
    assert original_fragment is None

    result = update_ocred_signs.update_single_fragment(
        collection, nonexistent_number, ocred_signs
    )

    assert result is False
    updated_fragment = collection.find_one({"museumNumber.number": "999"})
    assert updated_fragment is None


def test_update_single_fragment_error(database, sample_fragments):
    collection = database["fragments"]
    invalid_number_format = "INVALID"
    ocred_signs = "ABZ100 \nABZ101"

    result = update_ocred_signs.update_single_fragment(
        collection, invalid_number_format, ocred_signs
    )

    assert result is False

    all_fragments = list(collection.find({}))
    assert len(all_fragments) == len(sample_fragments)


def test_update_from_json_file(database, sample_fragments, sample_ocred_signs_file):
    collection = database["fragments"]
    temp_file_path = sample_ocred_signs_file

    results = update_ocred_signs.update_from_json_file(collection, temp_file_path)

    os.unlink(temp_file_path)

    assert results["success"] == 3
    assert results["failed"] == 0

    fragment_k1 = collection.find_one({"museumNumber.number": "1"})
    assert fragment_k1["ocredSigns"] == "ABZ001 \nABZ002 \nABZ003"

    fragment_bm_12345 = collection.find_one({"museumNumber.number": "12345"})
    assert (
        fragment_bm_12345["ocredSigns"] == "ABZ427 \nABZ354 \nABZ328 \nABZ579 \nABZ128"
    )

    fragment_bm_6789 = collection.find_one({"museumNumber.number": "6789"})
    assert fragment_bm_6789["ocredSigns"] == "ABZ597 \nABZ342 \nABZ343"
