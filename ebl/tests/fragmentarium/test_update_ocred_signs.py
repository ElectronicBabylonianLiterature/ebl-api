import pytest
import json
import tempfile
import os
import argparse
from mockito import when, verify
import ebl.fragmentarium.update_ocred_signs as update_ocred_signs


@pytest.fixture
def sample_ocred_signs_file():
    data = [
        {
            # ocred signs is ""
            "ocredSigns": "ABZ427 \nABZ354 \nABZ328 \nABZ579 \nABZ128",
            "filename": "BM.12345.jpg",
            "ocredSignsCoordinates": [
                [1469.80, 451.92, 1604.26, 563.18],
                [1753.32, 612.91, 1897.67, 736.16],
                [1346.76, 649.14, 1486.03, 778.64],
                [1037.14, 701.65, 1112.39, 830.00],
                [1316.21, 851.92, 1452.95, 978.90],
            ],
        },
        {
            # ocred signs not exist
            "ocredSigns": "ABZ597 \nABZ342 \nABZ343",
            "filename": "BM.6789.jpg",
            "ocredSignsCoordinates": [
                [4136.69, 807.03, 4293.22, 1075.93],
                [3184.05, 861.30, 3449.97, 1088.34],
                [2392.63, 1569.90, 2627.44, 1767.15],
            ],
        },
        {
            # ocred signs already exist
            "ocredSigns": "ABZ001 \nABZ002 \nABZ003",
            "filename": "K.1.jpg",
            "ocredSignsCoordinates": [
                [100.0, 200.0, 150.0, 250.0],
                [200.0, 300.0, 250.0, 350.0],
                [300.0, 400.0, 350.0, 450.0],
            ],
        },
    ]
    # Create a temporary JSON file with the sample data
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_file_path = f.name
    return temp_file_path


@pytest.fixture
def sample_fragments(database):
    fragments_collection = database["fragments"]

    test_fragments = [
        {
            "museumNumber": {"prefix": "K", "number": "1", "suffix": ""},
            "cdliNumber": "P000001",
            "description": "Ancient Babylonian tablet",
            "script": "Neo-Assyrian",
            "text": {"lines": []},
            "notes": "Test fragment K.1",
            "ocredSigns": "ABZ001 \nABZ002",
        },
        {
            "museumNumber": {"prefix": "K", "number": "2", "suffix": ""},
            "cdliNumber": "P000002",
            "description": "Administrative text",
            "script": "Neo-Assyrian",
            "text": {"lines": []},
            "notes": "Test fragment K.2",
        },
        {
            "museumNumber": {"prefix": "BM", "number": "12345", "suffix": ""},
            "cdliNumber": "P000003",
            "description": "Literary text fragment",
            "script": "Standard Babylonian",
            "text": {"lines": []},
            "notes": "Test fragment from British Museum",
            "ocredSigns": "",
        },
        {
            "museumNumber": {"prefix": "BM", "number": "6789", "suffix": ""},
            "cdliNumber": "P000004",
            "description": "Literary text fragment",
            "script": "Standard Babylonian",
            "text": {"lines": []},
            "notes": "Test fragment from British Museum",
        },
    ]

    fragments_collection.insert_many(test_fragments)
    return test_fragments


def test_update_single_fragment(database, sample_fragments):
    collection = database["fragments"]
    number_str = "K.2"
    ocred_signs = "ABZ100 \nABZ101"

    # check there is no ocredSigns before update
    original_fragment = collection.find_one({"museumNumber.number": "2"})
    assert (
        "ocredSigns" not in original_fragment or original_fragment["ocredSigns"] == ""
    )

    result = update_ocred_signs.update_single_fragment(
        collection, number_str, ocred_signs
    )

    # check
    assert result is True
    updated_fragment = collection.find_one({"museumNumber.number": "2"})
    assert updated_fragment is not None
    assert updated_fragment["ocredSigns"] == ocred_signs


def test_update_single_fragment_without_match(database, sample_fragments):
    collection = database["fragments"]
    number_str = "K.999"  # Non-existent fragment number
    ocred_signs = "ABZ999 \nABZ998"

    # check there is no fragment before update
    original_fragment = collection.find_one({"museumNumber.number": "999"})
    assert original_fragment is None

    result = update_ocred_signs.update_single_fragment(
        collection, number_str, ocred_signs
    )

    # check
    assert result is False
    updated_fragment = collection.find_one({"museumNumber.number": "999"})
    assert updated_fragment is None


def test_update_single_fragment_error(database, sample_fragments):
    collection = database["fragments"]
    invalid_number_str = ["INVALID.NUMBER.FORMAT"]
    ocred_signs = "ABZ100 \nABZ101"

    # Attempt to update with invalid museum number format
    result = update_ocred_signs.update_single_fragment(
        collection, invalid_number_str, ocred_signs
    )

    # Should return False due to parsing error
    assert result is False

    # Verify no unintended changes were made
    all_fragments = list(collection.find({}))
    assert len(all_fragments) == len(sample_fragments)


def test_update_from_json_file(database, sample_fragments, sample_ocred_signs_file):
    collection = database["fragments"]
    temp_file_path = sample_ocred_signs_file

    results = update_ocred_signs.update_from_json_file(collection, temp_file_path)

    # Clean up the temporary file
    os.unlink(temp_file_path)

    # Verify results
    assert results["success"] == 3  # All 3 fragments should be updated
    assert results["failed"] == 0

    # Verify database updates
    k1 = collection.find_one({"museumNumber.number": "1"})
    assert k1["ocredSigns"] == "ABZ001 \nABZ002 \nABZ003"

    bm_12345 = collection.find_one({"museumNumber.number": "12345"})
    assert bm_12345["ocredSigns"] == "ABZ427 \nABZ354 \nABZ328 \nABZ579 \nABZ128"

    bm_6789 = collection.find_one({"museumNumber.number": "6789"})
    assert bm_6789["ocredSigns"] == "ABZ597 \nABZ342 \nABZ343"


def test_update_from_json_file_with_errors(database, sample_fragments):
    collection = database["fragments"]

    # Create test data with errors
    data_with_errors = [
        {
            # Valid entry
            "ocredSigns": "ABZ100 \nABZ101",
            "filename": "K.1.jpg",
        },
        {
            # Missing filename
            "ocredSigns": "ABZ200 \nABZ201",
        },
        {
            # Non-existent fragment
            "ocredSigns": "ABZ300 \nABZ301",
            "filename": "NONEXISTENT.999.jpg",
        },
        {
            # Invalid museum number format
            "ocredSigns": "ABZ400 \nABZ401",
            "filename": "INVALID_FORMAT.jpg",
        },
    ]

    # Create a temporary JSON file with error data
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data_with_errors, f)
        temp_file_path = f.name

    results = update_ocred_signs.update_from_json_file(collection, temp_file_path)

    # Clean up the temporary file
    os.unlink(temp_file_path)

    # Verify results
    assert results["success"] == 1  # Only K.1 should succeed
    assert results["failed"] == 3  # Three should fail
    assert len(results["errors"]) == 3

    # Verify error messages
    expected_errors = [
        {"number": "unknown", "error": "Missing filename"},
        {"number": "NONEXISTENT.999", "error": "Fragment not found"},
        {
            "number": "INVALID_FORMAT.jpg",
            "error": "Invalid museum number: INVALID_FORMAT",
        },
    ]

    assert results["errors"] == expected_errors

    # Verify that the valid fragment was updated
    k1 = collection.find_one({"museumNumber.number": "1"})
    assert k1["ocredSigns"] == "ABZ100 \nABZ101"

    # Verify other fragments were not updated
    bm_12345 = collection.find_one({"museumNumber.number": "12345"})
    assert bm_12345["ocredSigns"] == ""


def test_main(database):
    collection = database["fragments"]

    # Mock get_database to return our test database
    when(update_ocred_signs).get_database().thenReturn(database)

    # Mock update_from_json_file to verify it gets called
    expected_results = {"success": 5, "failed": 2, "errors": []}
    when(update_ocred_signs).update_from_json_file(
        collection, "test_ocred_signs.json"
    ).thenReturn(expected_results)

    args = argparse.Namespace(file="test_ocred_signs.json", number=None, signs=None)

    update_ocred_signs.main(args)

    # Verify update_from_json_file was called with correct argument

    verify(update_ocred_signs).update_from_json_file(
        collection, "test_ocred_signs.json"
    )

    # Test the single fragment update path
    when(update_ocred_signs).update_single_fragment(
        collection, "K.1", "ABZ100 \nABZ101"
    ).thenReturn(True)

    args2 = argparse.Namespace(file=None, number="K.1", signs="ABZ100 \nABZ101")

    update_ocred_signs.main(args2)

    # Verify update_single_fragment was called with correct arguments
    verify(update_ocred_signs).update_single_fragment(
        collection, "K.1", "ABZ100 \nABZ101"
    )
