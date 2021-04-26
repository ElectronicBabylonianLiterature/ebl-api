import pytest
from marshmallow import EXCLUDE

from ebl.errors import NotFoundError
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.sign import (
    Sign,
    SignListRecord,
    SignName,
    Value,
    Logogram,
)
from ebl.transliteration.infrastructure.mongo_sign_repository import (
    SignSchema,
    LogogramSchema,
)

COLLECTION = "signs"


def test_logogram_schema():
    data = {
        "logogram": "AŠ-IKU",
        "atf": "AŠ-IKU",
        "wordId": ["ikû I"],
        "schrammLogogramme": "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)",
    }
    logogram = Logogram(
        "AŠ-IKU", Atf("AŠ-IKU"), ("ikû I",), "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)"
    )

    assert LogogramSchema().load(data) == logogram
    assert LogogramSchema().dump(logogram) == data


def test_sign_schema():
    data = {
        "_id": "KUR",
        "lists": [{"name": "ABZ", "number": "03+53"}],
        "values": [{"value": "kur", "subIndex": 3}, {"value": "ruk"}],
        "mesZl": None,
        "unicode": [],
        "logograms": [],
    }
    sign = Sign(
        SignName("KUR"),
        (SignListRecord("ABZ", "03+53"),),
        (Value("kur", 3), Value("ruk")),
    )
    sign_dumped = SignSchema().dump(sign)
    sign_dumped["name"] = sign_dumped.pop("_id")
    assert SignSchema(unknown=EXCLUDE).load(data) == sign
    assert SignSchema().dump(sign) == data


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
    }


@pytest.fixture
def sign_si(mongo_sign_si):
    return SignSchema(unknown=EXCLUDE).load(mongo_sign_si)


@pytest.fixture
def mongo_sign_si_2():
    return {
        "_id": "SI_2",
        "lists": [
            {"name": "HZL", "number": "13a"},
        ],
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
    assert sign_repository.search_all("ši", 1) == [sign_igi]
    assert sign_repository.search_all("none", 1) == []


def test_search_by_id(
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

    assert sign_repository.search_by_id("SI") == [sign_si, sign_si_2]
    assert sign_repository.search_by_id("none") == []


def test_search_by_lists_name(
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

    assert sign_repository.search_by_lists_name("HZL", "13a") == [sign_si_2]


def test_search_not_found(sign_repository):
    assert sign_repository.search("unknown", 1) is None


def test_sign_schema_include_homophones(
    database,
    sign_repository,
    sign_igi,
    mongo_sign_igi,
    sign_si,
    mongo_sign_si,
    sign_si_2,
    mongo_sign_si_2,
):
    database[COLLECTION].insert_many([mongo_sign_igi])
    assert sign_repository.search_include_homophones("ši") == [sign_igi]


def test_search_composite_signs(
    database,
    sign_repository,
    sign_igi,
    mongo_sign_igi,
    sign_si,
    mongo_sign_si,
    sign_si_2,
    mongo_sign_si_2,
):
    database[COLLECTION].insert_many([mongo_sign_igi])
    assert sign_repository.search_composite_signs("ši", 1) == [sign_igi]
