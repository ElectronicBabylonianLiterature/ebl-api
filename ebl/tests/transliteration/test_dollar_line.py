import pytest

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)


def test_loose_dollar_line() -> None:
    text = "this is a loose line"
    loose_line = LooseDollarLine(text)

    assert loose_line.lemmatization == (LemmatizationToken(f" ({text})"),)
    assert loose_line.text == text
    assert loose_line.atf == f"$ ({text})"
    assert loose_line.display_value == f"({text})"
    assert loose_line.is_end_of is False


def test_image_dollar_line() -> None:
    image = ImageDollarLine("1", "a", "great")

    assert image.lemmatization == (LemmatizationToken(" (image 1a = great)"),)
    assert image.number == "1"
    assert image.letter == "a"
    assert image.text == "great"
    assert image.atf == "$ (image 1a = great)"
    assert image.display_value == "(image 1a = great)"
    assert image.is_end_of is False


def test_ruling_dollar_line() -> None:
    ruling_line = RulingDollarLine(atf.Ruling.DOUBLE)

    assert ruling_line.lemmatization == (LemmatizationToken(" double ruling"),)
    assert ruling_line.number == atf.Ruling.DOUBLE
    assert ruling_line.status is None
    assert ruling_line.atf == "$ double ruling"
    assert ruling_line.display_value == "double ruling"
    assert ruling_line.is_end_of is False


def test_ruling_dollar_line_status() -> None:
    ruling_line = RulingDollarLine(
        atf.Ruling.DOUBLE, atf.DollarStatus.EMENDED_NOT_COLLATED
    )

    assert ruling_line.lemmatization == (LemmatizationToken(" double ruling !"),)
    assert ruling_line.number == atf.Ruling.DOUBLE
    assert ruling_line.status == atf.DollarStatus.EMENDED_NOT_COLLATED
    assert ruling_line.atf == "$ double ruling !"
    assert ruling_line.display_value == "double ruling !"
    assert ruling_line.is_end_of is False


def test_scope_container() -> None:
    scope = ScopeContainer(atf.Object.OBJECT, "what")

    assert scope.content == atf.Object.OBJECT
    assert scope.text == "what"


def test_strict_dollar_line_with_none() -> None:
    scope = ScopeContainer(atf.Object.OBJECT, "what")
    actual = StateDollarLine(None, atf.Extent.SEVERAL, scope, None, None)

    assert scope.content == atf.Object.OBJECT
    assert scope.text == "what"

    assert actual.scope == scope
    assert actual.lemmatization == (LemmatizationToken(" several object what"),)
    assert actual.atf == "$ several object what"
    assert actual.display_value == "several object what"
    assert actual.is_end_of is False


def test_state_dollar_line() -> None:
    scope = ScopeContainer(atf.Scope.COLUMNS, "")
    actual = StateDollarLine(
        atf.Qualification.AT_LEAST,
        atf.Extent.SEVERAL,
        scope,
        atf.State.BLANK,
        atf.DollarStatus.UNCERTAIN,
    )

    assert actual.qualification == atf.Qualification.AT_LEAST
    assert actual.scope == scope
    assert actual.extent == atf.Extent.SEVERAL
    assert actual.state == atf.State.BLANK
    assert actual.status == atf.DollarStatus.UNCERTAIN
    assert actual.lemmatization == (
        LemmatizationToken(" at least several columns blank ?"),
    )
    assert actual.atf == "$ at least several columns blank ?"
    assert actual.display_value == "at least several columns blank ?"
    assert actual.is_end_of is False


def test_state_dollar_line_content() -> None:
    scope = ScopeContainer(atf.Surface.OBVERSE)
    actual = StateDollarLine(
        atf.Qualification.AT_LEAST,
        1,
        scope,
        atf.State.BLANK,
        atf.DollarStatus.UNCERTAIN,
    )

    assert actual.scope == scope
    assert actual.lemmatization == (LemmatizationToken(" at least 1 obverse blank ?"),)
    assert actual.display_value == "at least 1 obverse blank ?"
    assert actual.is_end_of is False


def test_state_dollar_line_non_empty_string_error() -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        StateDollarLine(
            None, None, ScopeContainer(atf.Surface.REVERSE, "test"), None, None
        )


def test_state_dollar_line_range() -> None:
    scope = ScopeContainer(atf.Scope.LINES)
    actual = StateDollarLine(None, (2, 4), scope, atf.State.MISSING, None)

    assert actual.scope == scope
    assert actual.lemmatization == (LemmatizationToken(" 2-4 lines missing"),)
    assert actual.display_value == "2-4 lines missing"
    assert actual.is_end_of is False


def test_state_dollar_line_end_of() -> None:
    scope = ScopeContainer(atf.Surface.OBVERSE)
    actual = StateDollarLine(None, atf.Extent.END_OF, scope, None, None)

    assert actual.scope == scope
    assert actual.lemmatization == (LemmatizationToken(" end of obverse"),)
    assert actual.display_value == "end of obverse"
    assert actual.is_end_of is True
