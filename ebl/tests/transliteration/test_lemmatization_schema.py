import pytest  # pyre-ignore[21]

from ebl.transliteration.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.transliteration.application.lemmatization_schema import (
    LemmatizationSchema,
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


TOKEN = LemmatizationToken("kur", tuple())
LEMMATIZATION = Lemmatization(((TOKEN,),))
SERIALIZED = [[LemmatizationTokenSchema().dump(TOKEN)]]  # pyre-ignore[16]


def test_serialize_lemmatization():
    assert LemmatizationSchema().dump(LEMMATIZATION) == SERIALIZED


def test_deserialize_lemmatization():
    assert LemmatizationSchema().load(SERIALIZED) == LEMMATIZATION
