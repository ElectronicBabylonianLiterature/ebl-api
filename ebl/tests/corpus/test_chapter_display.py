from ebl.corpus.domain.chapter import make_title
from ebl.corpus.domain.chapter_display import ChapterDisplay, LineDisplay
from ebl.tests.factories.corpus import ChapterFactory, LineFactory, TextFactory
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.translation_line import (
    TranslationLine,
    DEFAULT_LANGUAGE,
)


def test_line_display_of_line() -> None:
    translation_lines = (
        TranslationLine((StringPart("bar"),), "de", None),
        TranslationLine((StringPart("foo"),), DEFAULT_LANGUAGE, None),
    )
    line = LineFactory.build(translation=translation_lines)

    line_display = LineDisplay.of_line(line)

    assert line_display == LineDisplay(
        line.number,
        (),
        line.is_second_line_of_parallelism,
        line.is_beginning_of_section,
        line.variants,
        translation_lines,
    )

    assert line_display.title == make_title(translation_lines)


def test_chapter_display_of_chapter() -> None:
    text = TextFactory.build()
    chapter = ChapterFactory.build()

    chapter_display = ChapterDisplay.of_chapter(text, chapter)

    assert chapter_display == ChapterDisplay(
        chapter.id_,
        text.name,
        text.has_doi,
        not text.has_multiple_stages,
        tuple(LineDisplay.of_line(line) for line in chapter.lines),
        chapter.record,
        chapter.manuscripts,
    )
    assert chapter_display.title == make_title(chapter.lines[0].translation)
