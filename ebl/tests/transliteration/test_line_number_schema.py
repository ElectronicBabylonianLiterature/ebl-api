import pytest

from ebl.transliteration.application.line_number_schema import LineNumberSchema
from ebl.transliteration.domain.line_number import LineNumber


@pytest.mark.parametrize(
    "line_number,data",
    [
        (
            LineNumber(1),
            {
                "number": 1,
                "hasPrime": False,
                "prefixModifier": None,
                "suffixModifier": None,
            },
        ),
        (
            LineNumber(963, True, "D", "a"),
            {
                "number": 963,
                "hasPrime": True,
                "prefixModifier": "D",
                "suffixModifier": "a",
            },
        ),
    ],
)
def test_line_number_schema(line_number, data):
    assert LineNumberSchema().dump(line_number) == data
    assert LineNumberSchema().load(data) == line_number
