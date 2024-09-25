import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize("prefix", ["$ ", "$"])
@pytest.mark.parametrize(
    "ruling,expected_ruling",
    [
        ("single", atf.Ruling.SINGLE),
        ("double", atf.Ruling.DOUBLE),
        ("triple", atf.Ruling.TRIPLE),
    ],
)
@pytest.mark.parametrize(
    "status,expected_status",
    [
        ("", None),
        ("*", atf.DollarStatus.COLLATED),
        ("?", atf.DollarStatus.UNCERTAIN),
        ("!", atf.DollarStatus.EMENDED_NOT_COLLATED),
        ("!?", atf.DollarStatus.NEEDS_COLLATION),
        ("°", atf.DollarStatus.NO_LONGER_VISIBLE),
    ],
)
@pytest.mark.parametrize("status_space", [True, False])
@pytest.mark.parametrize("parenthesis", [True, False])
def test_parse_ruling_dollar_line(
    prefix, ruling, expected_ruling, status, expected_status, status_space, parenthesis
):
    ruling = f"{ruling} ruling"
    ruling_with_status = (
        f"{ruling} {status}" if (status and status_space) else f"{ruling}{status}"
    )
    line = f"({ruling_with_status})" if parenthesis else ruling_with_status
    assert (
        parse_atf_lark(f"{prefix}{line}").lines
        == Text.of_iterable([RulingDollarLine(expected_ruling, expected_status)]).lines
    )
