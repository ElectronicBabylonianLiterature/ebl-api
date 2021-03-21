from ebl.transliteration.domain.sign import Sign, SignListRecord, SignName, Value, \
    Logogram


def test_logogram():
    logogram = Logogram("AŠ-IKU",  "AŠ-IKU", ["ikû I"], "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)")
    assert logogram.logogram == "AŠ-IKU"
    assert logogram.atf == "AŠ-IKU"
    assert logogram.word_id == ["ikû I"]
    assert logogram.schramm_logogram == "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)"


def test_sign():
    name = SignName("KUR")
    lists = (SignListRecord("FOO", "123"),)
    values = (Value("kur", 8), Value("ruk"))
    logogram = tuple(Logogram("AŠ-IKU", "AŠ-IKU", ["ikû I"],
                        "AŠ-IKU; *iku* (Deich); ZL 290 (Lit.)"))
    sign = Sign(name, lists=lists, values=values, logograms=logogram)


    assert sign.name == name
    assert sign.lists == lists
    assert sign.values == values
    assert sign.logograms == logogram


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
