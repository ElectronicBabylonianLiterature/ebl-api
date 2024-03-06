from ebl.signs.infrastructure.mongo_sign_repository import (
    SignSchema,
    LogogramSchema,
    FosseySchema,
    SignDtoSchema,
)
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.sign import (
    Sign,
    Logogram,
    Fossey,
    Value,
    SignName,
    SignListRecord,
)
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


def test_logogram_schema():
    data = {
        "logogram": "AŠ-IKU",
        "atf": "AŠ-IKU",
        "wordId": ["ikû I"],
        "schrammLogogramme": "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)",
        "unicode": "",
    }
    logogram = Logogram(
        "AŠ-IKU", Atf("AŠ-IKU"), ("ikû I",), "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)"
    )

    assert LogogramSchema().load(data) == logogram
    assert LogogramSchema().dump(logogram) == data


def test_fossey_schema():
    data = {
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
    fossey = Fossey(
        405,
        25728,
        "B",
        "Mai: MDP, VI, 11.I, 11",
        "Paulus AOAT 50, 981",
        "NABU 1997/1",
        "P123456",
        MuseumNumber.of("K.4562"),
        "dcclt",
        "Das Zeichen ist eigentlich ZA₇",
        "Marduk-apla-iddina I, 1171-1159 BC",
        "me-luḫ-ḫa",
        "M15,21.7c-0.1-0.1-0.2-0.4-0.2-0.8c-0.1-1-0.1-1.2-0.5-1.3c-0.2",
    )

    assert FosseySchema().load(data) == fossey
    assert FosseySchema().dump(fossey) == data


def test_sign_schema():
    data = {
        "_id": "KUR",
        "lists": [{"name": "ABZ", "number": "03+53"}],
        "values": [{"value": "kur", "subIndex": 3}, {"value": "ruk"}],
        "unicode": [],
        "mesZl": "",
        "LaBaSi": "",
        "reverseOrder": "12",
        "logograms": [],
        "fossey": [],
    }
    sign = Sign(
        SignName("KUR"),
        (SignListRecord("ABZ", "03+53"),),
        (Value("kur", 3), Value("ruk")),
    )
    assert SignSchema().dump(sign) == data
    assert SignSchema().load(data) == sign


def test_sign_dto_schema():
    sign = Sign(
        SignName("KUR"),
        (SignListRecord("ABZ", "03+53"),),
        (Value("kur", 3), Value("ruk")),
    )
    expected = {
        "name": "KUR",
        "lists": [{"name": "ABZ", "number": "03+53"}],
        "values": [{"value": "kur", "subIndex": 3}, {"value": "ruk"}],
        "mesZl": "",
        "LaBaSi": "",
        "reverseOrder": "12",
        "unicode": [],
        "logograms": [],
        "fossey": [],
    }
    assert SignDtoSchema().dump(sign) == expected
