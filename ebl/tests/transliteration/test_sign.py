from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.sign import (
    Sign,
    SignListRecord,
    SignName,
    SortKeys,
    Value,
    Logogram,
    Fossey,
)


def test_logogram():
    logogram = Logogram(
        "AŠ-IKU", Atf("AŠ-IKU"), ["ikû I"], "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)"
    )
    assert logogram.logogram == "AŠ-IKU"
    assert logogram.atf == Atf("AŠ-IKU")
    assert logogram.word_id == ["ikû I"]
    assert logogram.schramm_logogramme == "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)"


def test_sort_keys():
    sort_keys = SortKeys(
        [1, 2],
        [1, 2],
        [1, 2],
        [1, 2],
    )
    assert sort_keys.neo_assyrian_onset == [1, 2]
    assert sort_keys.neo_babylonian_onset == [1, 2]
    assert sort_keys.neo_assyrian_offset == [1, 2]
    assert sort_keys.neo_babylonian_offset == [1, 2]


def test_fossey():
    fossey = Fossey(
        405,
        25728,
        "B",
        "Mai: MDP, VI, 11.I, 11",
        "Paulus AOAT 50, 981",
        "NABU 1997/1",
        "P123456",
        MuseumNumber("K", "4562"),
        "dcclt",
        "Das Zeichen ist eigentlich ZA₇",
        "Marduk-apla-iddina I, 1171-1159 BC",
        "me-luḫ-ḫa",
        "M15,21.7c-0.1-0.1-0.2-0.4-0.2-0.8c-0.1-1-0.1-1.2-0.5-1.3c-0.2",
    )
    assert fossey.page == 405
    assert fossey.number == 25728
    assert fossey.suffix == "B"
    assert fossey.reference == "Mai: MDP, VI, 11.I, 11"
    assert fossey.new_edition == "Paulus AOAT 50, 981"
    assert fossey.secondary_literature == "NABU 1997/1"
    assert fossey.cdli_number == "P123456"
    assert fossey.museum_number == MuseumNumber("K", "4562")
    assert fossey.external_project == "dcclt"
    assert fossey.notes == "Das Zeichen ist eigentlich ZA₇"
    assert fossey.date == "Marduk-apla-iddina I, 1171-1159 BC"
    assert fossey.transliteration == "me-luḫ-ḫa"
    assert (
        fossey.sign == "M15,21.7c-0.1-0.1-0.2-0.4-0.2-0.8c-0.1-1-0.1-1.2-0.5-1.3c-0.2"
    )


def test_sign():
    name = SignName("KUR")
    lists = (SignListRecord("FOO", "123"),)
    values = (Value("kur", 8), Value("ruk"))
    logogram = Logogram(
        "AŠ-IKU", Atf("AŠ-IKU"), ["ikû I"], "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)"
    )
    fossey = Fossey(
        405,
        25728,
        "B",
        "Mai: MDP, VI, 11.I, 11",
        "Paulus AOAT 50, 981",
        "NABU 1997/1",
        "P123456",
        MuseumNumber("K", "4562"),
        "dcclt",
        "Das Zeichen ist eigentlich ZA₇",
        "Marduk-apla-iddina I, 1171-1159 BC",
        "me-luḫ-ḫa",
        "M15,21.7c-0.1-0.1-0.2-0.4-0.2-0.8c-0.1-1-0.1-1.2-0.5-1.3c-0.2",
    )
    sort_keys = SortKeys([1, 2], [1, 2], [1, 2], [1, 2])
    sign = Sign(
        name,
        lists=lists,
        values=values,
        logograms=logogram,
        fossey=fossey,
        mes_zl="test_mesZl",
        labasi="test_LaBaSi",
        sort_keys=sort_keys,
    )

    assert sign.name == name
    assert sign.lists == lists
    assert sign.values == values
    assert sign.logograms == logogram
    assert sign.fossey == fossey
    assert sign.mes_zl == "test_mesZl"
    assert sign.labasi == "test_LaBaSi"
    assert sign.sort_keys == sort_keys


def test_standardization_abz():
    name = "ABZ"
    number = "123"
    sign = Sign(SignName("KUR"), lists=(SignListRecord(name, number),))
    assert sign.standardization == f"{name}{number}"


def test_standardization_multiple_abz():
    name = "ABZ"
    number = "123"
    sign = Sign(
        SignName("KUR"),
        lists=(SignListRecord(name, number), SignListRecord(name, "999")),
    )
    assert sign.standardization == f"{name}{number}"


def test_standardization_no_abz():
    sign = Sign(SignName("KUR"))
    assert sign.standardization == sign.name
