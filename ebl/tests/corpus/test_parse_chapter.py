import pytest

from ebl.corpus.domain.chapter import ManuscriptLine
from ebl.corpus.domain.chapter_transformer import ChapterTransformer
from ebl.corpus.domain.manuscript import ManuscriptType, Period, Provenance, Siglum
from ebl.transliteration.domain.labels import parse_labels
from ebl.transliteration.domain.lark_parser import (
    CHAPTER_PARSER,
    parse_paratext,
    parse_text_line,
)
from ebl.transliteration.domain.line import EmptyLine


def parse_siglum(siglum):
    tree = CHAPTER_PARSER.parse(siglum, start="siglum")
    return ChapterTransformer().transform(tree)


@pytest.mark.parametrize("period", [Period.NEO_ASSYRIAN])
@pytest.mark.parametrize("provenance", [Provenance.DILBAT, Provenance.PERIPHERY])
#  pyre-ignore[56]
@pytest.mark.parametrize("type_", [ManuscriptType.SCHOOL, ManuscriptType.LIBRARY])
@pytest.mark.parametrize("disambiquator", ["", "a"])
def test_parse_siglum(
    period: Period, provenance: Provenance, type_: ManuscriptType, disambiquator
) -> None:
    assert parse_siglum(
        f"{provenance.abbreviation}{period.abbreviation}{type_.abbreviation}{disambiquator}"
    ) == Siglum(provenance, period, type_, disambiquator)


def parse_manuscript(atf):
    tree = CHAPTER_PARSER.parse(atf, start="manuscript_line")
    return ChapterTransformer().transform(tree)


@pytest.mark.parametrize(
    "lines,expected",
    [
        (
            ["NinNA o iii 1. kur", "#note: a note", "$ single ruling"],
            ManuscriptLine(
                0,
                parse_labels("o iii"),
                parse_text_line("1. kur"),
                (parse_paratext("#note: a note"), parse_paratext("$ single ruling")),
            ),
        ),
        (["NinNA 1. kur"], ManuscriptLine(0, tuple(), parse_text_line("1. kur"))),
        (
            ["NinNA o iii", "#note: a note", "$ single ruling"],
            ManuscriptLine(
                0,
                parse_labels("o iii"),
                EmptyLine(),
                (parse_paratext("#note: a note"), parse_paratext("$ single ruling")),
            ),
        ),
        (["NinNA"], ManuscriptLine(0, tuple(), EmptyLine())),
    ],
)
def test_parse_manuscript(lines, expected) -> None:
    atf = "\n".join(lines)
    assert parse_manuscript(atf) == expected
