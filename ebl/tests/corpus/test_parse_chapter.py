from typing import Sequence

import pytest

from ebl.corpus.domain.chapter import LineVariant, ManuscriptLine
from ebl.corpus.domain.chapter_transformer import ChapterTransformer
from ebl.corpus.domain.manuscript import (
    Manuscript,
    ManuscriptType,
    Period,
    Provenance,
    Siglum,
)
from ebl.tests.factories.corpus import ManuscriptFactory
from ebl.transliteration.domain.labels import parse_labels
from ebl.transliteration.domain.lark_parser import (
    CHAPTER_PARSER,
    PARSE_ERRORS,
    parse_note_line,
    parse_parallel_line,
    parse_paratext,
    parse_text_line,
)
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber

UNKNOWN_MANUSCRIPT: Manuscript = ManuscriptFactory.build()
MANUSCRIPTS: Sequence[Manuscript] = (
    ManuscriptFactory.build(),
    ManuscriptFactory.build(),
    ManuscriptFactory.build(),
)


def parse_siglum(siglum):
    tree = CHAPTER_PARSER.parse(siglum, start="siglum")
    return ChapterTransformer(MANUSCRIPTS).transform(tree)


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
    return ChapterTransformer(MANUSCRIPTS).transform(tree)


@pytest.mark.parametrize(
    "lines,expected",
    [
        (
            [
                f"{MANUSCRIPTS[0].siglum} o iii 1. kur",
                "#note: a note",
                "$ single ruling",
            ],
            ManuscriptLine(
                MANUSCRIPTS[0].id,
                parse_labels("o iii"),
                parse_text_line("1. kur"),
                (parse_paratext("#note: a note"), parse_paratext("$ single ruling")),
            ),
        ),
        (
            [f"{MANUSCRIPTS[0].siglum} 1. kur"],
            ManuscriptLine(MANUSCRIPTS[0].id, tuple(), parse_text_line("1. kur")),
        ),
        (
            [f"{MANUSCRIPTS[0].siglum} o iii", "#note: a note", "$ single ruling"],
            ManuscriptLine(
                MANUSCRIPTS[0].id,
                parse_labels("o iii"),
                EmptyLine(),
                (parse_paratext("#note: a note"), parse_paratext("$ single ruling")),
            ),
        ),
        (
            [f"{MANUSCRIPTS[0].siglum}"],
            ManuscriptLine(MANUSCRIPTS[0].id, tuple(), EmptyLine()),
        ),
    ],
)
def test_parse_manuscript(lines, expected) -> None:
    atf = "\n".join(lines)
    assert parse_manuscript(atf) == expected


def test_parse_manuscript_invalid() -> None:
    with pytest.raises(PARSE_ERRORS):
        parse_manuscript(f"{UNKNOWN_MANUSCRIPT.siglum} o iii 1. kur")


def parse_reconstruction(atf):
    tree = CHAPTER_PARSER.parse(atf, start="reconstruction")
    return ChapterTransformer(MANUSCRIPTS).transform(tree)


@pytest.mark.parametrize(  # pyre-ignore[56]
    "lines,expected",
    [
        (["1. kur"], (parse_text_line("1. kur"), None, tuple())),
        (
            ["1. kur", "#note: a note"],
            (parse_text_line("1. kur"), parse_note_line("#note: a note"), tuple()),
        ),
        (
            ["1. kur", "// (parallel line 1)"],
            (
                parse_text_line("1. kur"),
                None,
                (parse_parallel_line("// (parallel line 1)"),),
            ),
        ),
        (
            ["1. kur", "#note: a note", "// (parallel line 1)", "// (parallel line 1)"],
            (
                parse_text_line("1. kur"),
                parse_note_line("#note: a note"),
                (
                    parse_parallel_line("// (parallel line 1)"),
                    parse_parallel_line("// (parallel line 1)"),
                ),
            ),
        ),
    ],
)
def test_parse_reconstruction(lines, expected) -> None:
    atf = "\n".join(lines)
    assert parse_reconstruction(atf) == expected


@pytest.mark.parametrize(
    "lines,expected",
    [
        (
            ["1. kur", f"{MANUSCRIPTS[0].siglum} o iii 1. kur"],
            LineVariant(
                parse_text_line("1. kur").content,
                None,
                (parse_manuscript(f"{MANUSCRIPTS[0].siglum} o iii 1. kur"),),
                tuple(),
            ),
        ),
        (
            [
                "1. kur",
                f"{MANUSCRIPTS[0].siglum} o iii 1. kur",
                f"{MANUSCRIPTS[1].siglum} o iii 2. kur",
            ],
            LineVariant(
                parse_text_line("1. kur").content,
                None,
                (
                    parse_manuscript(f"{MANUSCRIPTS[0].siglum} o iii 1. kur"),
                    parse_manuscript(f"{MANUSCRIPTS[1].siglum} o iii 2. kur"),
                ),
                tuple(),
            ),
        ),
        (
            [
                "1. kur",
                "#note: a note",
                "// (parallel line 1)",
                f"{MANUSCRIPTS[1].siglum} o iii 1. kur",
                f"{MANUSCRIPTS[2].siglum} o iii 2. kur",
                "#note: a note",
                "$ single ruling",
            ],
            LineVariant(
                parse_text_line("1. kur").content,
                parse_note_line("#note: a note"),
                (
                    parse_manuscript(f"{MANUSCRIPTS[1].siglum} o iii 1. kur"),
                    parse_manuscript(
                        f"{MANUSCRIPTS[2].siglum} o iii 2. kur\n"
                        "#note: a note\n$ single ruling"
                    ),
                ),
                (parse_parallel_line("// (parallel line 1)"),),
            ),
        ),
    ],
)
def test_parse_line_variant(lines, expected) -> None:
    atf = "\n".join(lines)
    tree = CHAPTER_PARSER.parse(atf, start="line_variant")
    assert ChapterTransformer(MANUSCRIPTS).transform(tree) == (LineNumber(1), expected)
