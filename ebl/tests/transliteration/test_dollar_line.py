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
    loose_line = LooseDollarLine("this is a loose line")

    assert loose_line.prefix == "$"
    assert loose_line.content == (ValueToken(" (this is a loose line)"),)
    assert loose_line.text == "this is a loose line"


def test_image_dollar_line():
    actual = ImageDollarLine("1", "a", "great")

    assert actual.prefix == "$"
    assert actual.content == (ValueToken(" (image 1a = great)"),)
    assert actual.number == "1"
    assert actual.letter == "a"
    assert actual.text == "great"


def test_ruling_dollar_line():
    ruling_line = RulingDollarLine(atf.Ruling.DOUBLE)

    assert ruling_line.prefix == "$"
    assert ruling_line.content == (ValueToken(" double ruling"),)
    assert ruling_line.number == atf.Ruling.DOUBLE


def test_strict_dollar_line_with_none():
    scope = ScopeContainer(atf.Object.OBJECT, "what")
    actual = StrictDollarLine(None, atf.Extent.SEVERAL, scope, None, None)

    this = str(scope)
    assert actual.prefix == "$"
    assert actual.scope.content == atf.Object.OBJECT
    assert actual.scope.text == "what"
    assert actual.content == (ValueToken(" several object what"),)


def test_strict_dollar_line():
    actual = StrictDollarLine(
        atf.Qualification.AT_LEAST,
        atf.Extent.SEVERAL,
        ScopeContainer(atf.Scope.COLUMNS, ""),
        atf.State.BLANK,
        atf.Status.UNCERTAIN,
    )

    assert actual.prefix == "$"
    assert actual.qualification == atf.Qualification.AT_LEAST
    assert actual.scope.content == atf.Scope.COLUMNS
    assert actual.scope.text == ""
    assert actual.extent == atf.Extent.SEVERAL
    assert actual.state == atf.State.BLANK
    assert actual.status == atf.Status.UNCERTAIN
    assert actual.content == (ValueToken(" at least several columns blank ?"),)


def test_strict_dollar_line_content():
    scope = ScopeContainer(atf.Surface.OBVERSE)
    actual = StrictDollarLine(
        atf.Qualification.AT_LEAST, 1, scope, atf.State.BLANK, atf.Status.UNCERTAIN,
    )

    assert actual.content == (ValueToken(" at least 1 obverse blank ?"),)
