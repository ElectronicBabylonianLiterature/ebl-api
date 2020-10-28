import pytest  # pyre-ignore[21]

from ebl.transliteration.domain.lemmatization import LemmatizationToken
from ebl.transliteration.application.lemmatization_schema import (
    LemmatizationTokenSchema,
)


@pytest.mark.parametrize(
    "token,serialized",
    [
        (LemmatizationToken("kur", None), {"value": "kur", "uniqueLemma": []}),
        (
            LemmatizationToken("kur", ("aklu I",)),
            {"value": "kur", "uniqueLemma": ["aklu I"]},
        ),
    ],
)
def test_serialize_lemmatization_token(token, serialized):
    assert LemmatizationTokenSchema().dump(token) == serialized


@pytest.mark.parametrize(
    "token,serialized",
    [
        (LemmatizationToken("kur", None), {"value": "kur"}),
        (
            LemmatizationToken("kur", ("aklu I",)),
            {"value": "kur", "uniqueLemma": ["aklu I"]},
        ),
    ],
)
def test_deserialize_lemmatization_token(token, serialized):
    assert LemmatizationTokenSchema().load(serialized) == token
