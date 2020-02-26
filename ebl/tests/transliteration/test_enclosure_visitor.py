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
        "ku[r ...]",
        "[... k]ur",
        "k[u]r",
        "KUR-[KUR ...]",
        "[... KUR]-KUR",
        "KUR-[KUR]-KUR",
        "KU[R ...]",
        "[... K]UR",
        "K[U]R",
        "123-[123 ...]",
        "[... 123]-123",
        "123-[123]-123",
        "12[3 ...]",
        "[... 1]23",
        "1[2]3",
        "ku[r/12[3 ...]",
        "[... K]UR/1]23",
        "k[u]r/K[U]R",
        "[... k]u[r/1 ...]",
        "{k[ur} ...]",
        "{+k[ur} ...]",
        "{{k[ur}} ...]",
        "[... {k]ur}-kur",
        "[... {+k]ur}-kur",
        "[... {{k]ur}}-kur",
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
        "ku]r",
        "k]ur",
        "[kur-(kur]",
        "[kur)-kur]",
        "k[ur",
        "ku]r",
        "k[ur-(kur]",
        "[kur)-ku]r",
        "KUR-[KUR",
        "KUR]-KUR",
        "KU]R",
        "K]UR",
        "[KUR-(KUR]",
        "[KUR)-KUR]",
        "K[UR",
        "KU]R",
        "K[UR-(KUR]",
        "[KUR)-KU]R",
        "123-[123",
        "123]-123",
        "12]3",
        "1]23",
        "[123-(123]",
        "[123)-123]",
        "1[23",
        "12]3",
        "1[23-(123]",
        "[123)-12]3",
        "ku[r/1 ...]",
        "[... KUR/1]23",
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
        "[... (...] ...)",
        "[... [...] ...]",
        "[(... (...) ...)]",
        "[(... [...] ...)]",
        "<(... <(...)> ...)>",
        "<(... (...) ...)>",
        "<([... (...) ...])>",
        "<... <...> ...>",
        "<... (...) ...>",
        "<[... (...) ...]>",
        "<<... <<...>> ...>>",
        "{(... {(...)} ...)}",
        "<(... <...> ...)>",
        "<... <(...)> ...>",
        "{ku[r}",
        "{+ku[r}",
        "{{ku[r}}",
    ],
)
def test_invalid(atf):
    with pytest.raises(EnclosureError):
        validate_line(atf)
