import pytest
from marshmallow import EXCLUDE

from ebl.errors import NotFoundError
from ebl.signs.infrastructure.mongo_sign_repository import SignSchema

from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema

COLLECTION = "signs"


@pytest.fixture
def mongo_sign_igi():
    return {
        "_id": "IGI",
        "lists": [{"name": "HZL", "number": "288"}],
        "unicode": [74054],
        "notes": [],
        "internalNotes": [],
        "literature": [],
        "values": [
            {
                "value": "ši",
                "subIndex": 1,
                "questionable": False,
                "deprecated": False,
                "notes": [],
                "internalNotes": [],
            },
            {
                "value": "panu",
                "subIndex": 1,
                "questionable": False,
                "deprecated": False,
                "languageRestriction": "akk",
                "notes": [],
                "internalNotes": [],
            },
        ],
        "forms": [],
        "sortKeys": {
            "neoAssyrianOnset": [126],
            "neoBabylonianOnset": [39],
            "neoAssyrianOffset": [25],
        },
    }


@pytest.fixture
def sign_igi(mongo_sign_igi):
    return SignSchema(unknown=EXCLUDE).load(mongo_sign_igi)


@pytest.fixture
def mongo_sign_si():
    return {
        "_id": "SI",
        "lists": [],
        "unicode": [],
        "notes": [],
        "internalNotes": [],
        "literature": [],
        "values": [
            {
                "value": "ši",
                "subIndex": 2,
                "questionable": False,
                "deprecated": False,
                "notes": [],
                "internalNotes": [],
            },
            {
                "value": "hu",
                "questionable": False,
                "deprecated": False,
                "notes": [],
                "internalNotes": [],
            },
        ],
        "forms": [],
        "sortKeys": {
            "neoAssyrianOnset": [125],
            "neoBabylonianOnset": [38],
            "neoAssyrianOffset": [24],
        },
    }


@pytest.fixture
def sign_si(mongo_sign_si):
    return SignSchema(unknown=EXCLUDE).load(mongo_sign_si)


@pytest.fixture
def mongo_sign_si_2():
    return {
        "_id": "SI_2",
        "lists": [{"name": "HZL", "number": "13a"}],
        "unicode": [],
        "notes": [],
        "internalNotes": [],
        "literature": [],
        "values": [
            {
                "value": "ši-2",
                "subIndex": 2,
                "questionable": False,
                "deprecated": False,
                "notes": [],
                "internalNotes": [],
            },
            {
                "value": "hu-2",
                "questionable": False,
                "deprecated": False,
                "notes": [],
                "internalNotes": [],
            },
        ],
        "forms": [],
        "mesZl": """<div align="center">1	**AŠ**	𒀸</div>""",
        "LaBaSi": "12",
        "reverseOrder": "",
        "logograms": [
            {
                "logogram": "AŠ-IKU",
                "atf": "AŠ-IKU",
                "wordId": ["ikû I"],
                "schrammLogogramme": "AŠ-IKU; *ikû* (ein Flächenmaß); ME 43 CD 126b ZL "
                "290",
            },
            {
                "logogram": "<sup>mul</sup>AŠ-IKU",
                "atf": "{mul}AŠ-IKU",
                "wordId": ["ikû I"],
                "schrammLogogramme": "<sup>mul</sup>AŠ-IKU; *ikû* (Sternbild Pegasus); "
                "ME 43 CD 126b ZL 290",
            },
        ],
        "sortKeys": {
            "neoAssyrianOnset": [1, 3],
            "neoBabylonianOnset": [1, 3],
            "neoAssyrianOffset": [1, 3],
            "neoBabylonianOffset": [1, 3],
        },
        "fossey": [
            {
                "page": 405,
                "number": 25728,
                "suffix": "B",
                "reference": "Mai: MDP, VI, 11.I, 11",
                "newEdition": "Paulus AOAT 50, 981",
                "secondaryLiterature": "NABU 1997/1",
                "cdliNumber": "P123456",
                "museumNumber": MuseumNumberSchema().dump(MuseumNumber.of("K.4562")),
                "externalProject": "dcclt",
                "notes": "Das Zeichen ist eigentlich ZA₇",
                "date": "Marduk-apla-iddina I, 1171-1159 BC",
                "transliteration": "me-luḫ-ḫa",
                "sign": "M15,21.7c-0.1-0.1-0.2-0.4-0.2-0.8c-0.1-1-0.1-1.2-0.5-1.3c-0.2",
            }
        ],
    }


@pytest.fixture
def sign_si_2(mongo_sign_si_2):
    return SignSchema(unknown=EXCLUDE).load(mongo_sign_si_2)


def test_create(database, sign_repository, sign_igi):
    sign_name = sign_repository.create(sign_igi)

    assert database[COLLECTION].find_one({"_id": sign_name}) == SignSchema().dump(
        sign_igi
    )


def test_find(database, sign_repository, mongo_sign_igi, sign_igi):
    database[COLLECTION].insert_one(mongo_sign_igi)

    assert sign_repository.find(mongo_sign_igi["_id"]) == sign_igi


def test_sign_not_found(sign_repository):
    with pytest.raises(NotFoundError):
        sign_repository.find("unknown id")


def test_search(
    database,
    sign_repository,
    sign_igi,
    mongo_sign_igi,
    sign_si,
    mongo_sign_si,
    sign_si_2,
    mongo_sign_si_2,
):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si, mongo_sign_si_2])
    assert sign_repository.search("ši", 1) == sign_igi
    assert sign_repository.search("hu", None) == sign_si
    assert sign_repository.search("hu-2", None) == sign_si_2


def test_search_all(
    database, sign_repository, sign_igi, mongo_sign_igi, mongo_sign_si, mongo_sign_si_2
):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si, mongo_sign_si_2])
    assert sign_repository.search_all("ši", 1) == [sign_igi]


def test_search_all_no_result(
    database, sign_repository, mongo_sign_igi, mongo_sign_si, mongo_sign_si_2
):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si, mongo_sign_si_2])
    assert sign_repository.search_all("None", 1) == []


def test_search_by_id(
    database,
    sign_repository,
    mongo_sign_igi,
    sign_si,
    mongo_sign_si,
    sign_si_2,
    mongo_sign_si_2,
):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si, mongo_sign_si_2])

    assert sign_repository.search_by_id("SI") == [sign_si, sign_si_2]
    assert sign_repository.search_by_id("none") == []


def test_search_by_id_no_result(
    database, sign_repository, mongo_sign_igi, mongo_sign_si, mongo_sign_si_2
):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si, mongo_sign_si_2])
    assert sign_repository.search_by_id("none") == []


def test_search_by_lists_name(
    database, sign_repository, mongo_sign_igi, mongo_sign_si, sign_si_2, mongo_sign_si_2
):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si, mongo_sign_si_2])

    assert sign_repository.search_by_lists_name("HZL", "13a") == [sign_si_2]


def test_search_not_found(sign_repository):
    assert sign_repository.search("unknown", 1) is None


def test_find_signs_by_order(database, sign_repository, mongo_sign_igi, mongo_sign_si):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si])
    assert sign_repository.find_signs_by_order("IGI", "neoBabylonianOnset") == [
        [
            {"name": "SI", "unicode": []},
            {"name": "IGI", "unicode": [74054]},
        ]
    ]


def test_get_unicode_from_atf(database, sign_repository, mongo_sign_igi, mongo_sign_si):
    database[COLLECTION].insert_many([mongo_sign_igi, mongo_sign_si])
    transliteration_line = "ši ši"
    assert sign_repository.get_unicode_from_atf(transliteration_line) == [
        {"unicode": [74054]},
        {"unicode": [9999]},
        {"unicode": [74054]},
    ]


def test_find_signs_by_order_not_found(sign_repository):
    assert sign_repository.find_signs_by_order("SI", "not_existing_era") == []


def test_list_all_signs(sign_repository, signs) -> None:
    for sign in signs:
        sign_repository.create(sign)
    assert sign_repository.list_all_signs() == sorted([sign.name for sign in signs])
