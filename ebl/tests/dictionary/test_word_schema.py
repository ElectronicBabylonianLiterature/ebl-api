from ebl.dictionary.application.word_schema import WordSchema


def test_serialization_and_deserialization(word):
    schema = WordSchema()
    data = schema.dump(word)
    loaded = schema.load(data)
    assert data == word
    assert loaded == word
