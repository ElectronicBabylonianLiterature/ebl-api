from typing import Any, Dict, cast

import pytest
from marshmallow import Schema, ValidationError

from ebl.corpus.web.chapter_manuscript_schemas import (
    ApiManuscriptLineSchema,
    MuseumNumberString,
    _deserialize_transliteration,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


class _MuseumNumberSchema(Schema):
    museum_number = MuseumNumberString(required=True)


def test_museum_number_string_deserializes_a_valid_number() -> None:
    loaded = cast(Dict[str, Any], _MuseumNumberSchema().load({"museum_number": "X.1"}))

    assert loaded["museum_number"] == MuseumNumber.of("X.1")


def test_museum_number_string_deserializes_an_empty_string_to_none() -> None:
    loaded = cast(Dict[str, Any], _MuseumNumberSchema().load({"museum_number": ""}))

    assert loaded["museum_number"] is None


def test_museum_number_string_rejects_an_invalid_number() -> None:
    with pytest.raises(ValidationError, match="Invalid museum number."):
        _MuseumNumberSchema().load({"museum_number": "not a museum number"})


def test_deserialize_transliteration_rejects_an_invalid_colophon() -> None:
    with pytest.raises(ValidationError, match="Invalid colophon"):
        _deserialize_transliteration("1. $$$")


MANUSCRIPT_LINE_DATA = {
    "manuscriptId": 1,
    "labels": ["o"],
    "number": "1",
    "atf": "ku",
    "omittedWords": [],
}


def test_manuscript_line_requires_a_provenance_service() -> None:
    with pytest.raises(ValidationError, match="Provenance service not configured."):
        ApiManuscriptLineSchema().load(MANUSCRIPT_LINE_DATA)


def test_manuscript_line_rejects_an_unparsable_atf(provenance_service) -> None:
    schema = ApiManuscriptLineSchema(context={"provenance_service": provenance_service})

    with pytest.raises(ValidationError, match="Invalid manuscript line"):
        schema.load({**MANUSCRIPT_LINE_DATA, "atf": "$$$"})
