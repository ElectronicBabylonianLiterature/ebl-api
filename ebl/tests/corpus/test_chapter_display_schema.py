import attr

from ebl.corpus.application.display_schemas import ChapterDisplaySchema
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.tests.factories.corpus import (
    ChapterFactory,
    TextFactory,
)
from ebl.transliteration.application.line_number_schemas import (
    OneOfLineNumberSchema,
    OldLineNumberSchema,
)

from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.one_of_line_schema import (
    ParallelLineSchema,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.corpus.application.record_schemas import RecordSchema
from ebl.corpus.application.schemas import ManuscriptSchema, ManuscriptLineSchema


CHAPTER_DISPLAY = ChapterDisplay.of_chapter(TextFactory.build(), ChapterFactory.build())


def to_dict(
    chapter: ChapterDisplay, missing_translation: bool = False, for_loading=False
) -> dict:
    chapter_display = {
        "id": {
            "stage": chapter.id_.stage.value,
            "name": chapter.id_.name,
            "textId": {
                "genre": chapter.id_.text_id.genre.value,
                "category": chapter.id_.text_id.category,
                "index": chapter.id_.text_id.index,
            },
        },
        "textName": chapter.text_name,
        "textHasDoi": chapter.text_has_doi,
        "isSingleStage": chapter.is_single_stage,
        "lines": [
            {
                "index": index,
                "number": OneOfLineNumberSchema().dump(line.number),
                "oldLineNumbers": OldLineNumberSchema().dump(
                    line.old_line_numbers, many=True
                ),
                "isSecondLineOfParallelism": line.is_second_line_of_parallelism,
                "isBeginningOfSection": line.is_beginning_of_section,
                "variants": [
                    {
                        "index": index,
                        "intertext": OneOfNoteLinePartSchema().dump(
                            variant.intertext, many=True
                        ),
                        "reconstruction": OneOfTokenSchema().dump(
                            variant.reconstruction, many=True
                        ),
                        "note": variant.note and NoteLineSchema().dump(variant.note),
                        "manuscripts": ManuscriptLineSchema().dump(
                            variant.manuscripts, many=True
                        ),
                        "parallelLines": ParallelLineSchema().dump(
                            variant.parallel_lines, many=True
                        ),
                    }
                    for index, variant in enumerate(line.variants)
                ],
                "translation": []
                if missing_translation
                else TranslationLineSchema().dump(line.translation, many=True),
            }
            for index, line in enumerate(chapter.lines)
        ],
        "record": RecordSchema().dump(chapter.record),
        "manuscripts": ManuscriptSchema().dump(chapter.manuscripts, many=True),
        "atf": chapter.atf,
    }
    if for_loading:
        del chapter_display["atf"]
        for manuscript_index, manuscript in enumerate(CHAPTER_DISPLAY.manuscripts):
            for reference_index, reference in enumerate(manuscript.references):
                chapter_display["manuscripts"][manuscript_index]["references"][
                    reference_index
                ]["document"] = reference.document
    return chapter_display


def test_dump():
    assert ChapterDisplaySchema().dump(CHAPTER_DISPLAY) == {
        **to_dict(CHAPTER_DISPLAY),
        "title": OneOfNoteLinePartSchema().dump(CHAPTER_DISPLAY.title, many=True),
    }


def test_load():
    assert (
        ChapterDisplaySchema().load(to_dict(CHAPTER_DISPLAY, for_loading=True))
        == CHAPTER_DISPLAY
    )


def test_load_missing_data():
    lines = list(CHAPTER_DISPLAY.lines)
    lines[0] = attr.evolve(CHAPTER_DISPLAY.lines[0], translation=())
    chapter_display = attr.evolve(
        CHAPTER_DISPLAY,
        lines=tuple(lines),
    )
    assert (
        ChapterDisplaySchema().load(
            to_dict(chapter_display, missing_translation=True, for_loading=True)
        )
        == chapter_display
    )
