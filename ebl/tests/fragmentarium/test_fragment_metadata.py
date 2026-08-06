import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.domain.fragment_metadata import (
    Acquisition,
    parse_markup_with_paragraphs,
)


def test_acquisition_of():
    assert Acquisition.of(
        {"description": "purchase", "supplier": "gallery", "date": 1925}
    ) == Acquisition(description="purchase", supplier="gallery", date=1925)


def test_acquisition_of_defaults():
    assert Acquisition.of({}) == Acquisition()


def test_parse_markup_with_paragraphs_empty():
    assert parse_markup_with_paragraphs("") == ()


def test_parse_markup_with_paragraphs_rejects_invalid_markup():
    with pytest.raises(ValidationError, match="Invalid markup"):
        parse_markup_with_paragraphs("@i{unclosed")
