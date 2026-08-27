import pytest
from marshmallow import Schema, ValidationError

from ebl.corpus.web.chapter_schemas import LineNumberString
from ebl.transliteration.domain.line_number import LineNumber


class _Schema(Schema):
    number = LineNumberString(required=True)


def test_a_valid_line_number_is_parsed() -> None:
    assert _Schema().load({"number": "1"})["number"] == LineNumber(1)


def test_a_primed_line_number_is_parsed() -> None:
    assert _Schema().load({"number": "2'"})["number"] == LineNumber(2, True)


@pytest.mark.parametrize("value", ["not a line number", "", "1.2.3", "#"])
def test_an_unparsable_line_number_is_a_validation_error(value: str) -> None:
    with pytest.raises(ValidationError) as error:
        _Schema().load({"number": value})

    assert "Invalid line number." in str(error.value)


def test_a_line_number_round_trips() -> None:
    loaded = _Schema().load({"number": "3'"})

    assert _Schema().dump(loaded) == {"number": "3'"}
