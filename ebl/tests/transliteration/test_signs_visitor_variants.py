from typing import Sequence

from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.atf import VARIANT_SEPARATOR
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line

VARIANT_LINE = "1. ku/nu"


def _visit(sign_repository, signs, to_unicode: bool) -> SignsVisitor:
    for sign in signs:
        sign_repository.create(sign)
    visitor = SignsVisitor(sign_repository, False, to_unicode)
    parse_line(VARIANT_LINE).accept(visitor)
    return visitor


def test_a_variant_joins_its_signs_with_the_separator_as_strings(
    sign_repository, signs
) -> None:
    visitor = _visit(sign_repository, signs, to_unicode=False)

    assert visitor.result_string == [f"KU{VARIANT_SEPARATOR}ABZ075"]


def test_a_variant_keeps_each_sign_separate_in_unicode(sign_repository, signs) -> None:
    visitor = _visit(sign_repository, signs, to_unicode=True)
    plain = SignsVisitor(sign_repository, False, True)
    parse_line("1. ku").accept(plain)
    other = SignsVisitor(sign_repository, False, True)
    parse_line("1. nu").accept(other)

    unicode_result: Sequence[int] = visitor.result_unicode

    assert unicode_result[: len(plain.result_unicode)] == plain.result_unicode
    assert unicode_result[-len(other.result_unicode) :] == other.result_unicode
    assert len(unicode_result) > len(plain.result_unicode) + len(other.result_unicode)


def test_a_unicode_variant_puts_a_separator_between_its_signs(
    sign_repository, signs
) -> None:
    visitor = _visit(sign_repository, signs, to_unicode=True)

    assert list(visitor.result_unicode) == [
        74154,
        ord(VARIANT_SEPARATOR),
        74337,
    ]


def test_a_three_way_unicode_variant_has_two_separators(sign_repository, signs) -> None:
    for sign in signs:
        sign_repository.create(sign)
    two = SignsVisitor(sign_repository, False, True)
    parse_line("1. ku/nu").accept(two)
    three = SignsVisitor(sign_repository, False, True)
    parse_line("1. ku/nu/ku").accept(three)

    assert len(three.result_unicode) > len(two.result_unicode)
