from typing import Sequence

import pytest
from ebl.common.domain.period import Period

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import (
    Manuscript,
    Siglum,
)
from ebl.common.domain.manuscript_type import ManuscriptType
from ebl.common.domain.provenance import Provenance
from ebl.corpus.domain.parser import parse_chapter, parse_paratext
from ebl.errors import DataError
from ebl.tests.factories.corpus import ManuscriptFactory
from ebl.transliteration.domain.labels import parse_labels
from ebl.transliteration.domain.lark_parser import (
    parse_note_line,
    parse_parallel_line,
    parse_text_line,
    parse_translation_line,
)
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber

UNKNOWN_MANUSCRIPT: Manuscript = ManuscriptFactory.build()
MANUSCRIPTS: Sequence[Manuscript] = (
    ManuscriptFactory.build(with_old_sigla=True),
    ManuscriptFactory.build(with_old_sigla=True),
    ManuscriptFactory.build(with_old_sigla=True),
)


def parse_siglum(siglum):
    return parse_chapter(siglum, MANUSCRIPTS, "siglum")


@pytest.mark.parametrize("period", [Period.NEO_ASSYRIAN])
@pytest.mark.parametrize(
    "provenance", [Provenance.URUK, Provenance.UR, Provenance.PERIPHERY]
)
@pytest.mark.parametrize("type_", [ManuscriptType.SCHOOL, ManuscriptType.LIBRARY])
@pytest.mark.parametrize("disambiquator", ["", "a"])
def test_parse_siglum(
    period: Period, provenance: Provenance, type_: ManuscriptType, disambiquator: str
) -> None:
    assert parse_siglum(
        f"{provenance.abbreviation}{period.abbreviation}{type_.abbreviation}{disambiquator}"
    ) == Siglum(provenance, period, type_, disambiquator)


@pytest.mark.parametrize("disambiquator", ["", "a"])
def test_parse_siglum_standard_text(disambiquator: str) -> None:
    assert parse_siglum(
        f"{Provenance.STANDARD_TEXT.abbreviation}{disambiquator}"
    ) == Siglum(
        Provenance.STANDARD_TEXT, Period.NONE, ManuscriptType.NONE, disambiquator
    )


def parse_manuscript(atf):
    return parse_chapter(atf, MANUSCRIPTS, "manuscript_line")


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
            ManuscriptLine(MANUSCRIPTS[0].id, (), parse_text_line("1. kur")),
        ),
        (
            [f"    {MANUSCRIPTS[0].siglum} 1. kur"],
            ManuscriptLine(MANUSCRIPTS[0].id, (), parse_text_line("1. kur")),
        ),
        (
            [f" {MANUSCRIPTS[0].siglum} 1. kur"],
            ManuscriptLine(MANUSCRIPTS[0].id, (), parse_text_line("1. kur")),
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
            ManuscriptLine(MANUSCRIPTS[0].id, (), EmptyLine()),
        ),
    ],
)
def test_parse_manuscript(lines, expected) -> None:
    atf = "\n".join(lines)
    assert parse_manuscript(atf) == expected


def test_parse_manuscript_invalid() -> None:
    with pytest.raises(DataError):  # pyre-ignore[16]
        parse_manuscript(f"{UNKNOWN_MANUSCRIPT.siglum} o iii 1. kur")


def parse_reconstruction(atf):
    return parse_chapter(atf, MANUSCRIPTS, "reconstruction")


@pytest.mark.parametrize(
    "lines,expected",
    [
        (["1. kur"], (parse_text_line("1. kur"), None, ())),
        (
            ["1. kur", "#note: a note"],
            (parse_text_line("1. kur"), parse_note_line("#note: a note"), ()),
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


def parse_line_variant(atf):
    return parse_chapter(atf, MANUSCRIPTS, "line_variant")


@pytest.mark.parametrize(
    "lines,expected",
    [
        (
            ["1. kur", f"{MANUSCRIPTS[0].siglum} o iii 1. kur"],
            LineVariant(
                parse_text_line("1. kur").content,
                None,
                (parse_manuscript(f"{MANUSCRIPTS[0].siglum} o iii 1. kur"),),
                (),
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
                (),
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
    assert parse_line_variant(atf) == (LineNumber(1), expected)


def parse_chapter_line(atf):
    return parse_chapter(atf, MANUSCRIPTS, "chapter_line")


@pytest.mark.parametrize(
    "lines,expected",
    [
        (["1. kur"], Line(LineNumber(1), (parse_line_variant("1. kur")[1],))),
        (
            ["1. kur", "1. ra"],
            Line(
                LineNumber(1),
                (parse_line_variant("1. kur")[1], parse_line_variant("1. ra")[1]),
            ),
        ),
        (
            [f"1. kur\n{MANUSCRIPTS[0].siglum} 1. kur", "1. ra"],
            Line(
                LineNumber(1),
                (
                    parse_line_variant(f"1. kur\n{MANUSCRIPTS[0].siglum} 1. kur")[1],
                    parse_line_variant("1. ra")[1],
                ),
            ),
        ),
    ],
)
def test_parse_chapter_line(lines, expected) -> None:
    atf = "\n".join(lines)
    assert parse_chapter_line(atf) == expected


@pytest.mark.parametrize(
    "lines,expected",
    [
        (
            ["#tr.en: translation", "1. kur"],
            Line(
                LineNumber(1),
                (parse_line_variant("1. kur")[1],),
                translation=(parse_translation_line("#tr.en: translation"),),
            ),
        ),
        (
            ["#tr.en: translation", "#tr.de: translation", "1. kur"],
            Line(
                LineNumber(1),
                (parse_line_variant("1. kur")[1],),
                translation=(
                    parse_translation_line("#tr.en: translation"),
                    parse_translation_line("#tr.de: translation"),
                ),
            ),
        ),
    ],
)
def test_parse_translation(lines, expected) -> None:
    atf = "\n".join(lines)
    assert parse_chapter_line(atf) == expected


@pytest.mark.parametrize(
    "lines,expected",
    [
        (["1. kur"], (parse_chapter_line("1. kur"),)),
        (["1. kur\n1. ra"], (parse_chapter_line("1. kur\n1. ra"),)),
        (
            ["1. kur", "2. ra"],
            (parse_chapter_line("1. kur"), parse_chapter_line("2. ra")),
        ),
    ],
)
def test_parse_chapter(lines, expected) -> None:
    atf = "\n\n".join(lines)
    assert parse_chapter(atf, MANUSCRIPTS) == expected


def test_parse_chapter_empty() -> None:
    with pytest.raises(DataError):  # pyre-ignore[16]
        f = parse_chapter("", MANUSCRIPTS)
        print(f)
