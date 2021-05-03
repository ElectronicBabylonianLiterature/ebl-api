import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.application.lemmatization_schema import (
    LemmatizationTokenSchema,
)

TOKENS = [
    (LemmatizationToken("kur", None), {"value": "kur", "uniqueLemma": None}),
    (
        LemmatizationToken("kur", (WordId("aklu I"),)),
        {"value": "kur", "uniqueLemma": ["aklu I"]},
    ),
]


@pytest.mark.parametrize("token,serialized", TOKENS)
def test_serialize_lemmatization_token(token, serialized):
    assert LemmatizationTokenSchema().dump(token) == serialized


@pytest.mark.parametrize("token,serialized", TOKENS)
def test_deserialize_lemmatization_token(token, serialized):
    assert LemmatizationTokenSchema().load(serialized) == token
