import pytest

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
    return Sign(
        mongo_sign_igi["_id"],
        tuple(map(lambda data: SignListRecord(**data), mongo_sign_igi["lists"])),
        tuple(
            map(
                lambda data: Value(data["value"], data["subIndex"]),
                mongo_sign_igi["values"],
            )
        ),
    )


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
    return Sign(
        mongo_sign_si["_id"],
        tuple(map(lambda data: SignListRecord(**data), mongo_sign_si["lists"])),
        tuple(
            map(
                lambda data: Value(data["value"], data.get("subIndex")),
                mongo_sign_si["values"],
            )
        ),
    )


@pytest.fixture
def mongo_sign_si_2():
    return {
        "_id": "SI_2",
        "lists": [],
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
    return Sign(
        mongo_sign_si_2["_id"],
        tuple(map(lambda data: SignListRecord(**data), mongo_sign_si_2["lists"])),
        tuple(
            map(
                lambda data: Value(data["value"], data.get("subIndex")),
                mongo_sign_si_2["values"],
            )
        ),
        mes_zl=mongo_sign_si_2["mesZl"],
        logograms=tuple(
            LogogramSchema().load(data) for data in mongo_sign_si_2["logograms"]
        ),
    )


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
        "logograms": [],
        "mesZl": "",
    }
    sign = Sign(
        SignName("KUR"),
        (SignListRecord("ABZ", "03+53"),),
        (Value("kur", 3), Value("ruk")),
    )
    assert SignSchema().load(data) == sign
    assert SignSchema().dump(sign) == data


def test_sign_schema_without_required():
    data = {
        "_id": "KUR",
        "lists": [{"name": "ABZ", "number": "03+53"}],
        "values": [{"value": "kur", "subIndex": 3}, {"value": "ruk"}],
    }
    sign = Sign(
        SignName("KUR"),
        (SignListRecord("ABZ", "03+53"),),
        (Value("kur", 3), Value("ruk")),
    )
    assert SignSchema().load(data) == sign
    data["logograms"] = []
    data["mesZl"] = ""
    assert SignSchema().dump(sign) == data


def test_create(database, sign_repository, sign_igi):
    sign_name = sign_repository.create(sign_igi)

    assert database[COLLECTION].find_one({"_id": sign_name}) == SignSchema().dump(
        sign_igi
    )


def test_find(database, sign_repository, sign_igi, mongo_sign_igi):
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
    # assert sign_repository.search("hu", None) == sign_si
    assert sign_repository.search("hu-2", None) == sign_si_2


def test_search_not_found(sign_repository):
    assert sign_repository.search("unknown", 1) is None
