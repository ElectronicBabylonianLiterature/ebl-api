from ebl.dictionary.application.word_schema import WordSchema
from ebl.dictionary.domain.word import WordOrigin


def test_serialization_and_deserialization(word):
    schema = WordSchema()
    data = schema.dump(word)
    loaded = schema.load(data)
    assert data == word
    assert loaded == word


def test_origin_array_serialization(word):
    word_with_array_origin = {**word, "origin": ["CDA", "EBL"]}
    schema = WordSchema()
    data = schema.dump(word_with_array_origin)
    assert data["origin"] == ["CDA", "EBL"]
    loaded = schema.load(data)
    assert loaded["origin"] == ["CDA", "EBL"]


def test_single_origin_string_converted_to_array(word):
    word_with_string_origin = {**word, "origin": "CDA"}
    schema = WordSchema()
    data = schema.dump(word_with_string_origin)
    assert data["origin"] == ["CDA"]
    loaded = schema.load(data)
    assert loaded["origin"] == ["CDA"]


def test_origin_enum_list_normalized() -> None:
    schema = WordSchema()
    data = {"origin": [WordOrigin.CDA, WordOrigin.EBL]}

    normalized = schema._normalize_origin_after_load(data)

    assert normalized["origin"] == ["CDA", "EBL"]


def test_origin_enum_value_normalized() -> None:
    schema = WordSchema()
    data = {"origin": WordOrigin.CDA}

    normalized = schema._normalize_origin_after_load(data)

    assert normalized["origin"] == ["CDA"]
