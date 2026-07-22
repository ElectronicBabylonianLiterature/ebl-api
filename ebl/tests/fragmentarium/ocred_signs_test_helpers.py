import json
import tempfile


def build_sample_ocred_signs_file():
    data = [
        {
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
            "ocredSigns": "ABZ597 \nABZ342 \nABZ343",
            "filename": "BM.6789.jpg",
            "ocredSignsCoordinates": [
                [4136.69, 807.03, 4293.22, 1075.93],
                [3184.05, 861.30, 3449.97, 1088.34],
                [2392.63, 1569.90, 2627.44, 1767.15],
            ],
        },
        {
            "ocredSigns": "ABZ001 \nABZ002 \nABZ003",
            "filename": "K.1.jpg",
            "ocredSignsCoordinates": [
                [100.0, 200.0, 150.0, 250.0],
                [200.0, 300.0, 250.0, 350.0],
                [300.0, 400.0, 350.0, 450.0],
            ],
        },
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_file_path = f.name
    return temp_file_path


def build_sample_fragments(database):
    fragments_collection = database["fragments"]

    fragment_with_existing_ocred_signs = {
        "museumNumber": {"prefix": "K", "number": "1", "suffix": ""},
        "cdliNumber": "P000001",
        "description": "Ancient Babylonian tablet",
        "script": "Neo-Assyrian",
        "text": {"lines": []},
        "notes": "Test fragment K.1",
        "ocredSigns": "ABZ001 \nABZ002",
    }

    fragment_without_ocred_signs = {
        "museumNumber": {"prefix": "K", "number": "2", "suffix": ""},
        "cdliNumber": "P000002",
        "description": "Administrative text",
        "script": "Neo-Assyrian",
        "text": {"lines": []},
        "notes": "Test fragment K.2",
    }

    fragment_with_empty_ocred_signs = {
        "museumNumber": {"prefix": "BM", "number": "12345", "suffix": ""},
        "cdliNumber": "P000003",
        "description": "Literary text fragment",
        "script": "Standard Babylonian",
        "text": {"lines": []},
        "notes": "Test fragment from British Museum",
        "ocredSigns": "",
    }

    fragment_without_ocred_signs_field = {
        "museumNumber": {"prefix": "BM", "number": "6789", "suffix": ""},
        "cdliNumber": "P000004",
        "description": "Literary text fragment",
        "script": "Standard Babylonian",
        "text": {"lines": []},
        "notes": "Test fragment from British Museum",
    }

    test_fragments = [
        fragment_with_existing_ocred_signs,
        fragment_without_ocred_signs,
        fragment_with_empty_ocred_signs,
        fragment_without_ocred_signs_field,
    ]

    fragments_collection.insert_many(test_fragments)
    return test_fragments
