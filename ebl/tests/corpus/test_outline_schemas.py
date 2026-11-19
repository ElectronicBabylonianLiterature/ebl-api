from typing import Any, Callable, Dict

import pytest
from marshmallow import ValidationError

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.corpus.application.outline_schemas import load_chapter_outline
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript import Manuscript
from ebl.tests.corpus.outline_support import (
    OUTLINE_MANUSCRIPT_KEYS,
    create_outline_chapter,
    create_outline_document,
    create_provenance_service,
    dump_to_dict,
    project_outline_document,
)
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
)
from ebl.tests.transliteration.storage_test_helpers import has_key
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.one_of_line_schema import ParallelLineSchema
from ebl.transliteration.application.storage_serialization import (
    storage_serialization,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema

Document = Dict[str, Any]
Selector = Callable[[Document], Document]


def select_chapter(document: Document) -> Document:
    return document


def select_manuscript(document: Document) -> Document:
    return document["manuscripts"][0]


def select_line(document: Document) -> Document:
    return document["lines"][0]


def select_variant(document: Document) -> Document:
    return select_line(document)["variants"][0]


def create_manuscript_document(manuscript: Manuscript) -> Document:
    return {
        "id": manuscript.id,
        "siglumDisambiguator": manuscript.siglum_disambiguator,
        "museumNumber": manuscript.museum_number
        and MuseumNumberSchema().dump(manuscript.museum_number),
        "accession": manuscript.accession,
        "periodModifier": manuscript.period_modifier.value,
        "period": manuscript.period.long_name,
        "provenance": manuscript.provenance.long_name,
        "type": manuscript.type.long_name,
        "notes": manuscript.notes,
        "references": ReferenceSchema().dump(manuscript.references, many=True),
    }


def create_variant_document(variant: LineVariant) -> Document:
    return {
        "reconstruction": OneOfTokenSchema().dump(variant.reconstruction, many=True),
        "note": variant.note and NoteLineSchema().dump(variant.note),
        "parallelLines": ParallelLineSchema().dump(variant.parallel_lines, many=True),
        "manuscriptIds": [
            manuscript_line.manuscript_id for manuscript_line in variant.manuscripts
        ],
    }


def create_line_document(line: Line) -> Document:
    return {
        "number": OneOfLineNumberSchema().dump(line.number),
        "isSecondLineOfParallelism": line.is_second_line_of_parallelism,
        "isBeginningOfSection": line.is_beginning_of_section,
        "translation": TranslationLineSchema().dump(line.translation, many=True),
        "variants": [create_variant_document(variant) for variant in line.variants],
    }


def create_chapter_document(chapter: Chapter) -> Document:
    return {
        "textId": {
            "genre": chapter.text_id.genre.value,
            "category": chapter.text_id.category,
            "index": chapter.text_id.index,
        },
        "classification": chapter.classification.value,
        "stage": chapter.stage.long_name,
        "version": chapter.version,
        "name": chapter.name,
        "order": chapter.order,
        "uncertainFragments": MuseumNumberSchema().dump(
            chapter.uncertain_fragments, many=True
        ),
        "manuscripts": [
            create_manuscript_document(manuscript) for manuscript in chapter.manuscripts
        ],
        "lines": [create_line_document(line) for line in chapter.lines],
    }


def test_outline_document_is_the_projected_storage_document() -> None:
    chapter = create_outline_chapter()
    with storage_serialization():
        expected = create_chapter_document(chapter)

    assert create_outline_document(chapter) == expected


def test_outline_document_uses_the_sparse_storage_encoding() -> None:
    chapter = create_outline_chapter()

    assert has_key(create_chapter_document(chapter), "erasure")
    assert not has_key(create_outline_document(chapter), "erasure")


def test_outline_document_omits_heavy_manuscript_fields() -> None:
    stored_chapter = dump_to_dict(ChapterSchema(), create_outline_chapter())

    assert set(select_manuscript(stored_chapter)) - set(OUTLINE_MANUSCRIPT_KEYS) == {
        "oldSigla",
        "colophon",
        "unplacedLines",
    }


@pytest.mark.parametrize(
    "chapter",
    [
        create_outline_chapter(),
        ChapterFactory.build(),
        ChapterFactory.build(manuscripts=(), uncertain_fragments=(), lines=()),
    ],
)
def test_load_chapter_outline(chapter: Chapter) -> None:
    document = create_outline_document(chapter)

    assert load_chapter_outline(
        document, create_provenance_service()
    ) == ChapterOutline.of_chapter(chapter)


def test_load_chapter_outline_with_explicit_token_defaults() -> None:
    chapter = create_outline_chapter()
    document = project_outline_document(dump_to_dict(ChapterSchema(), chapter))

    assert document == create_chapter_document(chapter)
    assert load_chapter_outline(
        document, create_provenance_service()
    ) == ChapterOutline.of_chapter(chapter)


def test_load_chapter_outline_defaults() -> None:
    chapter = ChapterFactory.build(
        uncertain_fragments=(),
        lines=(
            LineFactory.build(
                manuscript_id=1,
                translation=(),
                variants=(
                    LineVariantFactory.build(manuscript_id=1, parallel_lines=()),
                ),
            ),
        ),
    )
    document = create_outline_document(chapter)
    del document["uncertainFragments"]
    del select_line(document)["translation"]
    del select_variant(document)["parallelLines"]

    assert load_chapter_outline(
        document, create_provenance_service()
    ) == ChapterOutline.of_chapter(chapter)


def test_loaded_outline_keeps_positions_and_manuscript_references() -> None:
    outline = load_chapter_outline(
        create_outline_document(create_outline_chapter()), create_provenance_service()
    )

    assert [manuscript.id for manuscript in outline.manuscripts] == [1, 5]
    assert [line.index for line in outline.lines] == [0, 1, 2]
    assert [
        variant.manuscript_ids for line in outline.lines for variant in line.variants
    ] == [(1, 5), (), (5,), (1,)]


@pytest.mark.parametrize(
    "select,key,value",
    [
        (select_chapter, "_id", "id"),
        (select_chapter, "signs", ["KU"]),
        (select_manuscript, "provenance", "Atlantis"),
        (select_line, "oldLineNumbers", []),
        (select_variant, "manuscripts", []),
        (select_variant, "intertext", []),
        (select_variant, "manuscriptIds", [0]),
    ],
)
def test_load_chapter_outline_rejects_unexpected_values(
    select: Selector, key: str, value: object
) -> None:
    document = create_outline_document(create_outline_chapter())
    select(document)[key] = value

    with pytest.raises(ValidationError, match=key):
        load_chapter_outline(document, create_provenance_service())


@pytest.mark.parametrize(
    "select,key",
    [
        (select_chapter, "textId"),
        (select_chapter, "manuscripts"),
        (select_chapter, "lines"),
        (select_line, "number"),
        (select_line, "isBeginningOfSection"),
        (select_line, "variants"),
        (select_variant, "reconstruction"),
        (select_variant, "note"),
        (select_variant, "manuscriptIds"),
    ],
)
def test_load_chapter_outline_rejects_missing_fields(
    select: Selector, key: str
) -> None:
    document = create_outline_document(create_outline_chapter())
    del select(document)[key]

    with pytest.raises(ValidationError, match=key):
        load_chapter_outline(document, create_provenance_service())
