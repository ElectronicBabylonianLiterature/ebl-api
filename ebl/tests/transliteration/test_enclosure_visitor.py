import pytest

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_visitor import EnclosureVisitor
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.line import Line


def validate_line(atf):
    line: Line = parse_line(f"1. {atf}")
    visitor = EnclosureVisitor()
    for token in line.content:
        token.accept(visitor)
    visitor.done()


@pytest.mark.parametrize(
    "atf",
    [
        "...",
        "[...]",
        "[(...)]",
        "<(...)>",
        "<...>",
        "<<...>>",
        "{(...)}",
        "kur-[kur ...]",
        "[... kur]-kur",
        "kur-[kur]-kur",
    ],
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
        "kur-[kur",
        "kur]-kur",
        "[kur-(kur]",
        "[kur)-kur]",
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
