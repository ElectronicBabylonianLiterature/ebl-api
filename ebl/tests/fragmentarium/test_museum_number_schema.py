import pytest

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber

MUSEUM_NUMBER = MuseumNumber("K", "1", "a")
SERIALIZED = {"prefix": "K", "number": "1", "suffix": "a"}


def test_dump():
    assert MuseumNumberSchema().dump(MUSEUM_NUMBER) == SERIALIZED


def test_load():
    assert MuseumNumberSchema().load(SERIALIZED) == MUSEUM_NUMBER


@pytest.mark.parametrize(
    "property_,value",
    [("prefix", ""), ("number", ""), ("number", "."), ("suffix", ".")],
)
def test_invalid(property_, value):
    assert MuseumNumberSchema().validate({**SERIALIZED, property_: value})


@pytest.mark.parametrize("property_", ["prefix", "number", "suffix"])
def test_missing(property_):
    data = {**SERIALIZED}
    data.pop(property_)
    assert MuseumNumberSchema().validate(data)
