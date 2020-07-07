import pytest  # pyre-ignore

from ebl.transliteration.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
)
from ebl.transliteration.domain.tokens import ValueToken


def test_empty_line():
    line = EmptyLine()

    assert line.prefix == ""
    assert line.content == tuple()
    assert line.key == "EmptyLine⁞⟨⟩"
    assert line.atf == ""


def test_control_line_of_single():
    prefix = "#"
    content = "only"
    line = ControlLine(prefix, content)

    assert line.prefix == prefix
    assert line.content == (ValueToken.of(content),)


@pytest.mark.parametrize(
    "line", [ControlLine("#", ' a comment'), EmptyLine()]
)
def test_update_lemmatization(line):
    lemmatization = tuple(LemmatizationToken(token.value) for token in line.content)
    assert line.update_lemmatization(lemmatization) == line
