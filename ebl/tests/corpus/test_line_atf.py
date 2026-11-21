from typing import Optional, Sequence

import pytest

from ebl.corpus.domain.line_atf import reconstruction_to_atf, translation_to_atf
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.web.chapter_schemas import ApiLineSchema, ApiLineVariantSchema
from ebl.tests.corpus.outline_support import RECONSTRUCTION, dump_to_dict
from ebl.tests.factories.corpus import LineFactory
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelComposition, ParallelLine
from ebl.transliteration.domain.translation_line import Extent, TranslationLine

RECONSTRUCTION_ATF = "%n enūma || eliš"
NOTE = NoteLine((StringPart("a note"),))
NOTE_ATF = "#note: a note"
PARALLEL_LINES: Sequence[ParallelLine] = (
    ParallelComposition(False, "name", LineNumber(7)),
    ParallelComposition(True, "other", LineNumber(8)),
)
PARALLEL_LINES_ATF = "// (name 7)\n// cf. (other 8)"
ENGLISH_TRANSLATION = TranslationLine(
    (StringPart("When on high"),), "en", Extent(LineNumber(2))
)
ARABIC_TRANSLATION = TranslationLine((StringPart("bar"),), "ar", None)
ENGLISH_TRANSLATION_ATF = "#tr.en.(2): When on high"
ARABIC_TRANSLATION_ATF = "#tr.ar: bar"


@pytest.mark.parametrize(
    "note,parallel_lines,expected",
    [
        (None, (), RECONSTRUCTION_ATF),
        (NOTE, (), f"{RECONSTRUCTION_ATF}\n{NOTE_ATF}"),
        (None, PARALLEL_LINES, f"{RECONSTRUCTION_ATF}\n{PARALLEL_LINES_ATF}"),
        (
            NOTE,
            PARALLEL_LINES,
            f"{RECONSTRUCTION_ATF}\n{NOTE_ATF}\n{PARALLEL_LINES_ATF}",
        ),
    ],
)
def test_reconstruction_to_atf(
    note: Optional[NoteLine], parallel_lines: Sequence[ParallelLine], expected: str
) -> None:
    assert reconstruction_to_atf(RECONSTRUCTION, note, parallel_lines) == expected


def test_reconstruction_to_atf_without_tokens() -> None:
    assert reconstruction_to_atf((), None, ()) == ""


def test_api_line_variant_schema_dumps_reconstruction_atf() -> None:
    variant = LineVariant(RECONSTRUCTION, NOTE, (), PARALLEL_LINES)

    assert (
        dump_to_dict(ApiLineVariantSchema(), variant)["reconstruction"]
        == f"{RECONSTRUCTION_ATF}\n{NOTE_ATF}\n{PARALLEL_LINES_ATF}"
    )


@pytest.mark.parametrize(
    "translation,expected",
    [
        ((), ""),
        ((ENGLISH_TRANSLATION,), ENGLISH_TRANSLATION_ATF),
        (
            (ENGLISH_TRANSLATION, ARABIC_TRANSLATION),
            f"{ENGLISH_TRANSLATION_ATF}\n{ARABIC_TRANSLATION_ATF}",
        ),
    ],
)
def test_translation_to_atf(
    translation: Sequence[TranslationLine], expected: str
) -> None:
    assert translation_to_atf(translation) == expected


def test_api_line_schema_dumps_translation_atf() -> None:
    line = LineFactory.build(translation=(ENGLISH_TRANSLATION, ARABIC_TRANSLATION))

    assert (
        dump_to_dict(ApiLineSchema(), line)["translation"]
        == f"{ENGLISH_TRANSLATION_ATF}\n{ARABIC_TRANSLATION_ATF}"
    )
