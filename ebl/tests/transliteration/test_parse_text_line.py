from typing import List
from ebl.tests.transliteration.parse_text_line_cases_1 import PARSE_TEXT_LINE_CASES_1
from ebl.tests.transliteration.parse_text_line_cases_2 import PARSE_TEXT_LINE_CASES_2
from ebl.tests.transliteration.parse_text_line_cases_3 import PARSE_TEXT_LINE_CASES_3
from ebl.tests.transliteration.parse_text_line_cases_4 import PARSE_TEXT_LINE_CASES_4
from ebl.tests.transliteration.parse_text_line_cases_5 import PARSE_TEXT_LINE_CASES_5
from ebl.tests.transliteration.parse_text_line_cases_6 import PARSE_TEXT_LINE_CASES_6
from ebl.tests.transliteration.parse_text_line_cases_7 import PARSE_TEXT_LINE_CASES_7
from ebl.tests.transliteration.parse_text_line_fixtures import (
    DEFAULT_LANGUAGE,
)

import pytest
from hamcrest import starts_with

from ebl.tests.assertions import assert_exception_has_errors
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import (
    Divider,
    Reading,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    ValueToken,
)
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.word_tokens import (
    Word,
)


@pytest.mark.parametrize(
    "parser,version", [(parse_atf_lark, f"{atf.ATF_PARSER_VERSION}")]
)
def test_parser_version(parser, version):
    assert parser("1. kur").parser_version == version


@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        *PARSE_TEXT_LINE_CASES_1,
        *PARSE_TEXT_LINE_CASES_2,
        *PARSE_TEXT_LINE_CASES_3,
        *PARSE_TEXT_LINE_CASES_4,
        *PARSE_TEXT_LINE_CASES_5,
        *PARSE_TEXT_LINE_CASES_6,
        *PARSE_TEXT_LINE_CASES_7,
    ],
)
def test_parse_text_line(line: str, expected_tokens: List[Line]) -> None:
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


def test_parse_dividers() -> None:
    line, expected_tokens = (
        r'1. :? :#! :# ::? :.@v /@19* :"@20@c ;@v@19!',
        [
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Divider.of(":", (), (atf.Flag.UNCERTAIN,)),
                    Divider.of(":", (), (atf.Flag.DAMAGE, atf.Flag.CORRECTION)),
                    Divider.of(":", (), (atf.Flag.DAMAGE,)),
                    Divider.of("::", (), (atf.Flag.UNCERTAIN,)),
                    Divider.of(":.", ("@v",), ()),
                    Divider.of("/", ("@19",), (atf.Flag.COLLATION,)),
                    Divider.of(':"', ("@20", "@c"), ()),
                    Divider.of(";", ("@v", "@19"), (atf.Flag.CORRECTION,)),
                ),
            )
        ],
    )
    assert parse_atf_lark(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize(
    "code,expected_language",
    [
        ("%ma", Language.AKKADIAN),
        ("%mb", Language.AKKADIAN),
        ("%na", Language.AKKADIAN),
        ("%nb", Language.AKKADIAN),
        ("%lb", Language.AKKADIAN),
        ("%sb", Language.AKKADIAN),
        ("%a", Language.AKKADIAN),
        ("%akk", Language.AKKADIAN),
        ("%eakk", Language.AKKADIAN),
        ("%oakk", Language.AKKADIAN),
        ("%ur3akk", Language.AKKADIAN),
        ("%oa", Language.AKKADIAN),
        ("%ob", Language.AKKADIAN),
        ("%sux", Language.SUMERIAN),
        ("%es", Language.EMESAL),
        ("%hit", Language.HITTITE),
        ("%foo", DEFAULT_LANGUAGE),
    ],
)
def test_parse_atf_language_shifts(code: str, expected_language: Language) -> None:
    word = "ha-am"
    parts = [Reading.of_name("ha"), Joiner.hyphen(), Reading.of_name("am")]
    line = f"1. {word} {code} {word} %sb {word}"

    expected = Text(
        (
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of(parts, DEFAULT_LANGUAGE),
                    LanguageShift.of(code),
                    Word.of(parts, expected_language),
                    LanguageShift.of("%sb"),
                    Word.of(parts, Language.AKKADIAN),
                ),
            ),
        )
    )

    assert parse_atf_lark(line).lines == expected.lines


def test_parse_normalized_akkadain_shift() -> None:
    word = "ha"
    line = f"1. {word} %n {word} %sux {word}"

    expected = Text(
        (
            TextLine.of_iterable(
                LineNumber(1),
                (
                    Word.of((Reading.of_name(word),), DEFAULT_LANGUAGE),
                    LanguageShift.normalized_akkadian(),
                    AkkadianWord.of((ValueToken.of(word),)),
                    LanguageShift.of("%sux"),
                    Word.of((Reading.of_name(word),), Language.SUMERIAN),
                ),
            ),
        )
    )

    assert parse_atf_lark(line).lines == expected.lines


@pytest.mark.parametrize(
    "atf,line_numbers",
    [
        ("1. x\nthis is not valid", [2]),
        ("1'. ($____$) x [...]\n$ (too many underscores)", [1]),
        ("1. me°-e\\li°-ku", [1]),
        ("1. me-°e\\li-°ku", [1]),
        ("1. {[me}]\n2. [{me]}\n3. {[me]}", [1, 2, 3]),
        ("a+1.a+2. šu", [1]),
    ],
)
def test_invalid_text_line(atf, line_numbers) -> None:
    with pytest.raises(TransliterationError) as exc_info:
        parse_atf_lark(atf)

    assert_exception_has_errors(exc_info, line_numbers, starts_with("Invalid line"))


@pytest.mark.parametrize(
    "atf,line_numbers", [("1. x\n2. [", [2]), ("1. [\n2. ]", [1, 2])]
)
def test_invalid_brackets(atf, line_numbers) -> None:
    with pytest.raises(TransliterationError) as exc_info:
        parse_atf_lark(atf)

    assert_exception_has_errors(exc_info, line_numbers, "Invalid brackets.")
