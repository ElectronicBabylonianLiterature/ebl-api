import pytest
import json
import tempfile
import os
import argparse
from mockito import verify
import ebl.fragmentarium.update_ocred_signs as update_ocred_signs
from ebl.tests.fragmentarium.ocred_signs_test_helpers import build_sample_fragments


@pytest.fixture
def sample_fragments(database):
    return build_sample_fragments(database)


def test_update_from_json_file_with_errors(database, sample_fragments):
    collection = database["fragments"]

    valid_entry = {
        "ocredSigns": "ABZ100 \nABZ101",
        "filename": "K.1.jpg",
    }

    entry_missing_filename = {
        "ocredSigns": "ABZ200 \nABZ201",
    }

    entry_with_nonexistent_fragment = {
        "ocredSigns": "ABZ300 \nABZ301",
        "filename": "NONEXISTENT.999.jpg",
    }

    entry_with_invalid_museum_number_format = {
        "ocredSigns": "ABZ400 \nABZ401",
        "filename": "INVALID_FORMAT.jpg",
    }

    data_with_errors = [
        valid_entry,
        entry_missing_filename,
        entry_with_nonexistent_fragment,
        entry_with_invalid_museum_number_format,
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data_with_errors, f)
        temp_file_path = f.name

    results = update_ocred_signs.update_from_json_file(collection, temp_file_path)

    os.unlink(temp_file_path)

    assert results["success"] == 1
    assert results["failed"] == 3
    assert len(results["errors"]) == 3

    expected_errors = [
        {"number": "unknown", "error": "Missing filename"},
        {"number": "NONEXISTENT.999", "error": "Fragment not found"},
        {
            "number": "INVALID_FORMAT.jpg",
            "error": "Invalid museum number: INVALID_FORMAT",
        },
    ]

    assert results["errors"] == expected_errors

    fragment_k1 = collection.find_one({"museumNumber.number": "1"})
    assert fragment_k1["ocredSigns"] == "ABZ100 \nABZ101"

    fragment_bm_12345 = collection.find_one({"museumNumber.number": "12345"})
    assert fragment_bm_12345["ocredSigns"] == ""


def test_main(database, when):
    collection = database["fragments"]

    when(update_ocred_signs).get_database().thenReturn(database)

    expected_results = {"success": 5, "failed": 2, "errors": []}
    when(update_ocred_signs).update_from_json_file(
        collection, "test_ocred_signs.json"
    ).thenReturn(expected_results)

    args = argparse.Namespace(file="test_ocred_signs.json", number=None, signs=None)

    update_ocred_signs.main(args)

    verify(update_ocred_signs).update_from_json_file(
        collection, "test_ocred_signs.json"
    )

    when(update_ocred_signs).update_single_fragment(
        collection, "K.1", "ABZ100 \nABZ101"
    ).thenReturn(True)

    args_for_single_update = argparse.Namespace(
        file=None, number="K.1", signs="ABZ100 \nABZ101"
    )

    update_ocred_signs.main(args_for_single_update)

    verify(update_ocred_signs).update_single_fragment(
        collection, "K.1", "ABZ100 \nABZ101"
    )
