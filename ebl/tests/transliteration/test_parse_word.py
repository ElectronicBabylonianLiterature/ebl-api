import pytest
from lark import ParseError
from lark.exceptions import UnexpectedInput

from ebl.tests.transliteration.parse_word_cases_1 import WORD_CASES as WORD_CASES_1
from ebl.tests.transliteration.parse_word_cases_2 import WORD_CASES as WORD_CASES_2
from ebl.tests.transliteration.parse_word_cases_3 import WORD_CASES as WORD_CASES_3
from ebl.tests.transliteration.parse_word_cases_4 import WORD_CASES as WORD_CASES_4
from ebl.tests.transliteration.parse_word_cases_5 import WORD_CASES as WORD_CASES_5
from ebl.tests.transliteration.parse_word_cases_determinatives import (
    LONE_DETERMINATIVE_CASES,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_word

WORD_CASES = [
    *WORD_CASES_1,
    *WORD_CASES_2,
    *WORD_CASES_3,
    *WORD_CASES_4,
    *WORD_CASES_5,
]


@pytest.mark.parametrize("atf,expected", WORD_CASES)
def test_word(atf, expected) -> None:
    assert parse_word(atf) == expected


@pytest.mark.parametrize("atf,expected", LONE_DETERMINATIVE_CASES)
def test_lone_determinative(atf, expected) -> None:
    assert parse_word(atf) == expected


@pytest.mark.parametrize("atf", ["{udu}?"])
def test_invalid_lone_determinative(atf) -> None:
    with pytest.raises(UnexpectedInput):
        parse_word(atf)


@pytest.mark.parametrize(
    "invalid_atf",
    [
        "Kur",
        "ku(r",
        "K)UR",
        "K[(UR",
        "ku)]r",
        "sal/: šim",
        "<GAR>?",
        "KA₂]?.DINGIR.RA[{ki?}",
        "KA₂?].DINGIR.RA[{ki}?",
        "k[a]?",
        ":-sal",
        "gam/://sal",
        "Š[A₃?...]",
        "|KU]R|",
        "|KUR.[KUR|",
        "-kur",
        "kur-",
        "]-kur",
        "kur-[",
    ],
)
def test_invalid(invalid_atf) -> None:
    with pytest.raises((UnexpectedInput, ParseError)):
        parse_word(invalid_atf)
