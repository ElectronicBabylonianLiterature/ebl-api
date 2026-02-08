import pytest

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.line import ControlLine, EmptyLine


def test_empty_line() -> None:
    line = EmptyLine()

    assert line.lemmatization == ()
    assert line.key == f"EmptyLine⁞⁞{hash(line)}"
    assert line.atf == ""


def test_control_line() -> None:
    prefix = "#"
    content = "only"
    line = ControlLine(prefix, content)

    assert line.prefix == prefix
    assert line.content == content
    assert line.key == f"ControlLine⁞#only⁞{hash(line)}"
    assert line.lemmatization == (LemmatizationToken(content),)


@pytest.mark.parametrize(
    "line,lemmatization",
    [
        (ControlLine("#", " a comment"), (LemmatizationToken(" a comment"),)),
        (EmptyLine(), ()),
    ],
)
def test_update_lemmatization(line, lemmatization) -> None:
    assert line.update_lemmatization(lemmatization) == line
