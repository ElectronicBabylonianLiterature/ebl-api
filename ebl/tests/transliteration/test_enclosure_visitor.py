import pytest

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_visitor import EnclosureVisitor
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.line import Line


def validate_line(atf):
    line: Line = parse_line(f"1. {atf}")
    visitor = EnclosureVisitor()
    for token in line.content:
        visitor.visit(token)
    visitor.done()


@pytest.mark.parametrize(
    "atf", ["...", "[...]", "[(...)]", "<(...)>", "<...>", "<<...>>", "{(...)}",],
)
def test_valid(atf):
    validate_line(atf)


@pytest.mark.parametrize(
    "atf",
    [
        "[...",
        "[(...",
        "<(...",
        "<...",
        "<<...",
        "{(...",
        "...]",
        "...)]",
        "...)>",
        "...>",
        "...>>",
        "...)}",
        "(...)",
        "[... [...] ...]",
        "[(... (...) ...)]",
        "[(... [...] ...)]",
        "<(... <(...)> ...)>",
        "<... <...> ...>",
        "<<... <<...>> ...>>",
        "{(... {(...)} ...)}",
        "<(... <...> ...)>",
        "<... <(...)> ...>",
    ],
)
def test_invalid(atf):
    with pytest.raises(EnclosureError):
        validate_line(atf)
