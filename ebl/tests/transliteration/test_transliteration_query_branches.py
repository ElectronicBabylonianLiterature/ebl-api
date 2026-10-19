from ebl.transliteration.domain.tokens import NullSignsCollectingVisitor
from ebl.transliteration.domain.transliteration_query import (
    TransliterationQuery,
    Type,
)


def _query(string: str) -> TransliterationQuery:
    return TransliterationQuery(string=string, visitor=NullSignsCollectingVisitor())


def test_a_string_of_only_separators_yields_no_children() -> None:
    query = _query("ku")

    assert query.create_children(" - . ") == []


def test_a_string_of_only_separators_has_an_empty_children_regexp() -> None:
    query = _query("ku")

    assert query.children_regexp(" - . ") == r""


def test_create_inline_children_falls_back_to_the_query_string() -> None:
    query = _query("ku nu")

    from_default = query.create_inline_children()
    from_explicit = query.create_inline_children("ku nu")

    assert [child.string for child in from_default] == ["ku nu"]
    assert [child.string for child in from_default] == [
        child.string for child in from_explicit
    ]


def test_create_inline_children_uses_the_argument_when_one_is_given() -> None:
    query = _query("ku nu")

    assert [child.string for child in query.create_inline_children("? ?")] == ["?", "?"]


def test_a_query_of_only_separators_is_undefined_and_empty() -> None:
    query = _query(" - . ")

    assert query.type == Type.UNDEFINED
    assert query.string == ""
    assert query.is_empty() is True
    assert query.regexp == r""
