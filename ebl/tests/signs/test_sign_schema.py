from ebl.signs.infrastructure.mongo_sign_repository import (
    SignSchema,
    LogogramSchema,
    SignDtoSchema,
)
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.sign import (
    Sign,
    Logogram,
    Value,
    SignName,
    SignListRecord,
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
        "unicode": [],
        "mesZl": "",
        "logograms": [],
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
        "unicode": [],
        "logograms": [],
    }
    assert SignDtoSchema().dump(sign) == expected
