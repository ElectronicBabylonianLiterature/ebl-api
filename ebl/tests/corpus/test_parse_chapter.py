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
from ebl.corpus.domain.parser import (
    parse_chapter,
    parse_paratext,
    parse_manuscript as _parse_manuscript,
)
from ebl.errors import DataError
from ebl.tests.factories.corpus import ManuscriptFactory
from ebl.tests.factories.provenance import DEFAULT_PROVENANCES
from ebl.transliteration.domain.atf_parsers.lark_parser import (
    parse_note_line,
    parse_parallel_line,
    parse_text_line,
    parse_translation_line,
    parse_labels,
)
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber

UNKNOWN_MANUSCRIPT: Manuscript = ManuscriptFactory.build()
MANUSCRIPTS: Sequence[Manuscript] = (
    ManuscriptFactory.build(with_old_sigla=True),
    ManuscriptFactory.build(with_old_sigla=True),
    ManuscriptFactory.build(with_old_sigla=True),
)


STANDARD_TEXT = next(
    record for record in DEFAULT_PROVENANCES if record.id == "STANDARD_TEXT"
)
URUK = next(record for record in DEFAULT_PROVENANCES if record.id == "URUK")
UR = next(record for record in DEFAULT_PROVENANCES if record.id == "UR")
PERIPHERY = next(record for record in DEFAULT_PROVENANCES if record.id == "PERIPHERY")


def parse_siglum(siglum, provenance_service):
    return _parse_manuscript(siglum, MANUSCRIPTS, provenance_service, "siglum")


@pytest.mark.parametrize("period", [Period.NEO_ASSYRIAN])
@pytest.mark.parametrize("provenance", [URUK, UR, PERIPHERY])
@pytest.mark.parametrize("type_", [ManuscriptType.SCHOOL, ManuscriptType.LIBRARY])
@pytest.mark.parametrize("disambiquator", ["", "a"])
def test_parse_siglum(
    period: Period,
    provenance,
    type_: ManuscriptType,
    disambiquator: str,
    seeded_provenance_service,
) -> None:
    assert parse_siglum(
        f"{provenance.abbreviation}{period.abbreviation}{type_.abbreviation}{disambiquator}",
        seeded_provenance_service,
    ) == Siglum(provenance, period, type_, disambiquator)


@pytest.mark.parametrize("disambiquator", ["", "a"])
def test_parse_siglum_standard_text(
    disambiquator: str, seeded_provenance_service
) -> None:
    assert parse_siglum(
        f"{STANDARD_TEXT.abbreviation}{disambiquator}", seeded_provenance_service
    ) == Siglum(STANDARD_TEXT, Period.NONE, ManuscriptType.NONE, disambiquator)


def parse_manuscript(atf, provenance_service):
    return _parse_manuscript(atf, MANUSCRIPTS, provenance_service, "manuscript_line")


@pytest.mark.parametrize(
    "lines,expected_builder",
    [
        (
            [
                f"{MANUSCRIPTS[0].siglum} o iii 1. kur",
                "#note: a note",
                "$ single ruling",
            ],
            lambda provenance_service: ManuscriptLine(
                MANUSCRIPTS[0].id,
                parse_labels("o iii"),
                parse_text_line("1. kur"),
                (
                    parse_paratext("#note: a note", provenance_service),
                    parse_paratext("$ single ruling", provenance_service),
                ),
            ),
        ),
        (
            [f"{MANUSCRIPTS[0].siglum} 1. kur"],
            lambda _: ManuscriptLine(
                MANUSCRIPTS[0].id, (), parse_text_line("1. kur")
            ),
        ),
        (
            [f"    {MANUSCRIPTS[0].siglum} 1. kur"],
            lambda _: ManuscriptLine(
                MANUSCRIPTS[0].id, (), parse_text_line("1. kur")
            ),
        ),
        (
            [f" {MANUSCRIPTS[0].siglum} 1. kur"],
            lambda _: ManuscriptLine(
                MANUSCRIPTS[0].id, (), parse_text_line("1. kur")
            ),
        ),
        (
            [f"{MANUSCRIPTS[0].siglum} o iii", "#note: a note", "$ single ruling"],
            lambda provenance_service: ManuscriptLine(
                MANUSCRIPTS[0].id,
                parse_labels("o iii"),
                EmptyLine(),
                (
                    parse_paratext("#note: a note", provenance_service),
                    parse_paratext("$ single ruling", provenance_service),
                ),
            ),
        ),
        (
            [f"{MANUSCRIPTS[0].siglum}"],
            lambda _: ManuscriptLine(MANUSCRIPTS[0].id, (), EmptyLine()),
        ),
    ],
)
def test_parse_manuscript(lines, expected_builder, seeded_provenance_service) -> None:
    atf = "\n".join(lines)
    assert (
        parse_manuscript(atf, seeded_provenance_service)
        == expected_builder(seeded_provenance_service)
    )


def test_parse_manuscript_invalid(seeded_provenance_service) -> None:
    with pytest.raises(DataError):
        parse_manuscript(
            f"{UNKNOWN_MANUSCRIPT.siglum} o iii 1. kur",
            seeded_provenance_service,
        )


def parse_reconstruction(atf, provenance_service):
    return parse_chapter(atf, MANUSCRIPTS, provenance_service, "reconstruction")


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
def test_parse_reconstruction(lines, expected, seeded_provenance_service) -> None:
    atf = "\n".join(lines)
    assert parse_reconstruction(atf, seeded_provenance_service) == expected


def parse_line_variant(atf, provenance_service):
    return parse_chapter(atf, MANUSCRIPTS, provenance_service, "line_variant")


@pytest.mark.parametrize(
    "lines,expected_builder",
    [
        (
            ["1. kur", f"{MANUSCRIPTS[0].siglum} o iii 1. kur"],
            lambda provenance_service: LineVariant(
                parse_text_line("1. kur").content,
                None,
                (
                    parse_manuscript(
                        f"{MANUSCRIPTS[0].siglum} o iii 1. kur",
                        provenance_service,
                    ),
                ),
                (),
            ),
        ),
        (
            [
                "1. kur",
                f"{MANUSCRIPTS[0].siglum} o iii 1. kur",
                f"{MANUSCRIPTS[1].siglum} o iii 2. kur",
            ],
            lambda provenance_service: LineVariant(
                parse_text_line("1. kur").content,
                None,
                (
                    parse_manuscript(
                        f"{MANUSCRIPTS[0].siglum} o iii 1. kur",
                        provenance_service,
                    ),
                    parse_manuscript(
                        f"{MANUSCRIPTS[1].siglum} o iii 2. kur",
                        provenance_service,
                    ),
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
            lambda provenance_service: LineVariant(
                parse_text_line("1. kur").content,
                parse_note_line("#note: a note"),
                (
                    parse_manuscript(
                        f"{MANUSCRIPTS[1].siglum} o iii 1. kur",
                        provenance_service,
                    ),
                    parse_manuscript(
                        f"{MANUSCRIPTS[2].siglum} o iii 2. kur\n"
                        "#note: a note\n$ single ruling",
                        provenance_service,
                    ),
                ),
                (parse_parallel_line("// (parallel line 1)"),),
            ),
        ),
    ],
)
def test_parse_line_variant(lines, expected_builder, seeded_provenance_service) -> None:
    atf = "\n".join(lines)
    assert parse_line_variant(atf, seeded_provenance_service) == (
        LineNumber(1),
        expected_builder(seeded_provenance_service),
    )


def parse_chapter_line(atf, provenance_service):
    return parse_chapter(atf, MANUSCRIPTS, provenance_service, "chapter_line")


@pytest.mark.parametrize(
    "lines,expected_builder",
    [
        (
            ["1. kur"],
            lambda provenance_service: Line(
                LineNumber(1),
                (parse_line_variant("1. kur", provenance_service)[1],),
            ),
        ),
        (
            ["1. kur", "1. ra"],
            lambda provenance_service: Line(
                LineNumber(1),
                (
                    parse_line_variant("1. kur", provenance_service)[1],
                    parse_line_variant("1. ra", provenance_service)[1],
                ),
            ),
        ),
        (
            [f"1. kur\n{MANUSCRIPTS[0].siglum} 1. kur", "1. ra"],
            lambda provenance_service: Line(
                LineNumber(1),
                (
                    parse_line_variant(
                        f"1. kur\n{MANUSCRIPTS[0].siglum} 1. kur",
                        provenance_service,
                    )[1],
                    parse_line_variant("1. ra", provenance_service)[1],
                ),
            ),
        ),
    ],
)
def test_parse_chapter_line(lines, expected_builder, seeded_provenance_service) -> None:
    atf = "\n".join(lines)
    assert parse_chapter_line(atf, seeded_provenance_service) == expected_builder(
        seeded_provenance_service
    )


@pytest.mark.parametrize(
    "lines,expected_builder",
    [
        (
            ["#tr.en: translation", "1. kur"],
            lambda provenance_service: Line(
                LineNumber(1),
                (parse_line_variant("1. kur", provenance_service)[1],),
                translation=(parse_translation_line("#tr.en: translation"),),
            ),
        ),
        (
            ["#tr.en: translation", "#tr.de: translation", "1. kur"],
            lambda provenance_service: Line(
                LineNumber(1),
                (parse_line_variant("1. kur", provenance_service)[1],),
                translation=(
                    parse_translation_line("#tr.en: translation"),
                    parse_translation_line("#tr.de: translation"),
                ),
            ),
        ),
    ],
)
def test_parse_translation(lines, expected_builder, seeded_provenance_service) -> None:
    atf = "\n".join(lines)
    assert parse_chapter_line(atf, seeded_provenance_service) == expected_builder(
        seeded_provenance_service
    )


@pytest.mark.parametrize(
    "lines,expected_builder",
    [
        (["1. kur"], lambda provenance_service: (parse_chapter_line("1. kur", provenance_service),)),
        (
            ["1. kur\n1. ra"],
            lambda provenance_service: (
                parse_chapter_line("1. kur\n1. ra", provenance_service),
            ),
        ),
        (
            ["1. kur", "2. ra"],
            lambda provenance_service: (
                parse_chapter_line("1. kur", provenance_service),
                parse_chapter_line("2. ra", provenance_service),
            ),
        ),
    ],
)
def test_parse_chapter(lines, expected_builder, seeded_provenance_service) -> None:
    atf = "\n\n".join(lines)
    assert parse_chapter(atf, MANUSCRIPTS, seeded_provenance_service) == expected_builder(
        seeded_provenance_service
    )


def test_parse_chapter_empty(seeded_provenance_service) -> None:
    with pytest.raises(DataError):
        f = parse_chapter("", MANUSCRIPTS, seeded_provenance_service)
        print(f)
