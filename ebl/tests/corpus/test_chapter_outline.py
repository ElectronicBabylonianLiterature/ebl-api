from typing import Union

import attr
import pytest

from ebl.common.domain.manuscript_type import ManuscriptType
from ebl.common.domain.period import Period
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_outline import (
    ChapterOutline,
    LineOutline,
    LineVariantOutline,
    ManuscriptOutline,
    museum_number_to_string,
)
from ebl.corpus.domain.line_variant import LineVariant
from ebl.tests.corpus.outline_support import (
    PROVENANCES_BY_LONG_NAME,
    RECONSTRUCTION,
    create_outline_chapter,
)
from ebl.tests.corpus.support import create_chapter_dto
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.translation_line import TranslationLine

Outline = Union[ChapterOutline, LineOutline, LineVariantOutline, ManuscriptOutline]

VARIANT = LineVariant(
    RECONSTRUCTION,
    NoteLine((StringPart("a note"),)),
    (
        ManuscriptLineFactory.build(manuscript_id=1),
        ManuscriptLineFactory.build(manuscript_id=5),
        ManuscriptLineFactory.build(manuscript_id=1),
    ),
    (ParallelComposition(False, "name", LineNumber(7)),),
)
VARIANT_OUTLINE = LineVariantOutline(
    "%n enūma || eliš\n#note: a note\n// (name 7)", (1, 5, 1)
)
VARIANT_WITHOUT_MANUSCRIPTS = LineVariant(VARIANT.reconstruction)
VARIANT_WITHOUT_MANUSCRIPTS_OUTLINE = LineVariantOutline("%n enūma || eliš", ())
LINE_OUTLINE = LineOutline(
    3,
    "3-4'",
    True,
    False,
    "#tr.en: foo\n#tr.de: bar",
    (VARIANT_OUTLINE, VARIANT_WITHOUT_MANUSCRIPTS_OUTLINE),
)
MANUSCRIPT_OUTLINE = ManuscriptOutline(1, "NinNA1a", "K.5419.C", "")


def test_museum_number_to_string() -> None:
    assert museum_number_to_string(MuseumNumber.of("K.5419.C")) == "K.5419.C"


def test_missing_museum_number_to_string() -> None:
    assert museum_number_to_string(None) == ""


def test_manuscript_outline_of_manuscript() -> None:
    manuscript = ManuscriptFactory.build(
        id=1,
        siglum_disambiguator="1a",
        museum_number=MuseumNumber.of("K.5419.C"),
        accession="",
        provenance=PROVENANCES_BY_LONG_NAME["Nineveh"],
        period=Period.NEO_ASSYRIAN,
        type=ManuscriptType.LIBRARY,
    )

    assert ManuscriptOutline.of_manuscript(manuscript) == MANUSCRIPT_OUTLINE


def test_manuscript_outline_of_manuscript_without_museum_number() -> None:
    manuscript = ManuscriptFactory.build(museum_number=None, accession="A.12")

    assert ManuscriptOutline.of_manuscript(manuscript) == ManuscriptOutline(
        manuscript.id, str(manuscript.siglum), "", "A.12"
    )


def test_line_variant_outline_of_variant() -> None:
    assert LineVariantOutline.of_variant(VARIANT) == VARIANT_OUTLINE


def test_line_variant_outline_of_variant_without_manuscripts() -> None:
    assert (
        LineVariantOutline.of_variant(VARIANT_WITHOUT_MANUSCRIPTS)
        == VARIANT_WITHOUT_MANUSCRIPTS_OUTLINE
    )


def test_line_outline_of_line() -> None:
    line = LineFactory.build(
        number=LineNumberRange(LineNumber(3), LineNumber(4, True)),
        variants=(VARIANT, VARIANT_WITHOUT_MANUSCRIPTS),
        is_second_line_of_parallelism=True,
        is_beginning_of_section=False,
        translation=(
            TranslationLine((StringPart("foo"),), "en", None),
            TranslationLine((StringPart("bar"),), "de", None),
        ),
    )

    assert LineOutline.of_line(3, line) == LINE_OUTLINE


def test_chapter_outline_of_chapter() -> None:
    chapter = create_outline_chapter()

    assert ChapterOutline.of_chapter(chapter) == ChapterOutline(
        chapter.text_id,
        chapter.classification,
        chapter.stage,
        chapter.version,
        chapter.name,
        chapter.order,
        ("K.1", "BM.2.a"),
        (
            ManuscriptOutline(1, str(chapter.manuscripts[0].siglum), "K.5419.C", ""),
            ManuscriptOutline(5, str(chapter.manuscripts[1].siglum), "", "A.12"),
        ),
        tuple(
            LineOutline.of_line(index, line) for index, line in enumerate(chapter.lines)
        ),
    )


def test_chapter_outline_of_empty_chapter() -> None:
    chapter = ChapterFactory.build(manuscripts=(), uncertain_fragments=(), lines=())
    outline = ChapterOutline.of_chapter(chapter)

    assert (outline.uncertain_fragments, outline.manuscripts, outline.lines) == (
        (),
        (),
        (),
    )


@pytest.mark.parametrize("chapter", [create_outline_chapter(), ChapterFactory.build()])
def test_lines_equal_api_chapter_lines(chapter: Chapter) -> None:
    api_lines = create_chapter_dto(chapter)["lines"]

    assert ChapterOutline.of_chapter(chapter).lines == tuple(
        LineOutline(
            index,
            line["number"],
            line["isSecondLineOfParallelism"],
            line["isBeginningOfSection"],
            line["translation"],
            tuple(
                LineVariantOutline(
                    variant["reconstruction"],
                    tuple(
                        manuscript_line["manuscriptId"]
                        for manuscript_line in variant["manuscripts"]
                    ),
                )
                for variant in line["variants"]
            ),
        )
        for index, line in enumerate(api_lines)
    )


@pytest.mark.parametrize("chapter", [create_outline_chapter(), ChapterFactory.build()])
def test_manuscripts_equal_api_chapter_manuscripts(chapter: Chapter) -> None:
    api_chapter = create_chapter_dto(chapter)
    outline = ChapterOutline.of_chapter(chapter)

    assert outline.uncertain_fragments == tuple(api_chapter["uncertainFragments"])
    assert [
        (manuscript.id, manuscript.museum_number, manuscript.accession)
        for manuscript in outline.manuscripts
    ] == [
        (manuscript["id"], manuscript["museumNumber"], manuscript["accession"])
        for manuscript in api_chapter["manuscripts"]
    ]


def test_manuscript_ids_refer_to_outline_manuscripts() -> None:
    outline = ChapterOutline.of_chapter(create_outline_chapter())
    manuscript_ids = {manuscript.id for manuscript in outline.manuscripts}

    assert {
        manuscript_id
        for line in outline.lines
        for variant in line.variants
        for manuscript_id in variant.manuscript_ids
    } == manuscript_ids


@pytest.mark.parametrize(
    "outline,attribute",
    [
        (MANUSCRIPT_OUTLINE, "siglum"),
        (VARIANT_OUTLINE, "reconstruction"),
        (LINE_OUTLINE, "number"),
        (ChapterOutline.of_chapter(create_outline_chapter()), "name"),
    ],
)
def test_outlines_are_frozen(outline: Outline, attribute: str) -> None:
    with pytest.raises(attr.exceptions.FrozenInstanceError):
        setattr(outline, attribute, "changed")
