from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    StrictDollarLine,
    ScopeContainer,
)
from ebl.transliteration.domain.tokens import ValueToken


def test_loose_dollar_line():
    expected = LooseDollarLine("end of side")

    assert expected.prefix == "$"
    assert expected.content == (ValueToken(" (end of side)"),)
    assert expected.text == "end of side"


def test_image_dollar_line():
    expected = ImageDollarLine("1", "a", "great")

    assert expected.prefix == "$"
    assert expected.content == (ValueToken(" (image 1a = great)"),)
    assert expected.number == "1"
    assert expected.letter == "a"
    assert expected.text == "great"


def test_ruling_dollar_line():
    expected = RulingDollarLine(atf.Ruling.DOUBLE)

    assert expected.prefix == "$"
    assert expected.content == (ValueToken(" double ruling"),)
    assert expected.number == atf.Ruling.DOUBLE


def test_strict_dollar_line_with_none():
    scope = ScopeContainer(atf.Object.OBJECT, "what")
    expected = StrictDollarLine(None, atf.Extent.SEVERAL, scope, None, None)
    assert expected.prefix == "$"
    assert expected.scope.content == atf.Object.OBJECT
    assert expected.scope.text == "what"
    assert expected.content == (ValueToken(" several object what"),)


def test_strict_dollar_line():
    expected = StrictDollarLine(
        atf.Qualification.AT_LEAST,
        atf.Extent.SEVERAL,
        ScopeContainer(atf.Scope.COLUMNS, ""),
        atf.State.BLANK,
        atf.Status.UNCERTAIN,
    )

    assert expected.prefix == "$"
    assert expected.qualification == atf.Qualification.AT_LEAST
    assert expected.scope.content == atf.Scope.COLUMNS
    assert expected.scope.text == ""
    assert expected.extent == atf.Extent.SEVERAL
    assert expected.state == atf.State.BLANK
    assert expected.status == atf.Status.UNCERTAIN
    assert expected.content == (ValueToken(" at least several columns blank ?"),)


def test_strict_dollar_line_content():
    scope = ScopeContainer(atf.Surface.OBVERSE)
    expected = StrictDollarLine(
        atf.Qualification.AT_LEAST, 1, scope, atf.State.BLANK, atf.Status.UNCERTAIN,
    )

    assert expected.content == (ValueToken(" at least 1 obverse blank ?"),)
