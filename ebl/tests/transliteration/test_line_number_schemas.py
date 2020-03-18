import pytest

from ebl.transliteration.application.line_number_schemas import (
    dump_line_number,
    load_line_number,
)
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange


@pytest.mark.parametrize(
    "line_number,data",
    [
        (
            LineNumber(1),
            {
                "type": "LineNumber",
                "number": 1,
                "hasPrime": False,
                "prefixModifier": None,
                "suffixModifier": None,
            },
        ),
        (
            LineNumber(963, True, "D", "a"),
            {
                "type": "LineNumber",
                "number": 963,
                "hasPrime": True,
                "prefixModifier": "D",
                "suffixModifier": "a",
            },
        ),
        (
            LineNumberRange(LineNumber(1), LineNumber(963, True, "D", "a"),),
            {
                "type": "LineNumberRange",
                "start": {
                    "type": "LineNumber",
                    "number": 1,
                    "hasPrime": False,
                    "prefixModifier": None,
                    "suffixModifier": None,
                },
                "end": {
                    "type": "LineNumber",
                    "number": 963,
                    "hasPrime": True,
                    "prefixModifier": "D",
                    "suffixModifier": "a",
                },
            },
        ),
    ],
)
def test_line_number_schema(line_number, data):
    assert dump_line_number(line_number) == data
    assert load_line_number(data) == line_number
