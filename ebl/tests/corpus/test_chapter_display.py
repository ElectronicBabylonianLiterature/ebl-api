from ebl.corpus.domain.chapter_display import ChapterDisplay, LineDisplay
from ebl.tests.factories.corpus import ChapterFactory, LineFactory, TextFactory
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.translation_line import (
    TranslationLine,
    DEFAULT_LANGUAGE,
)


def test_line_display_of_line() -> None:
    expected_translation = (StringPart("foo"),)
    translation_lines = (
        TranslationLine((StringPart("bar"),), "de", None),
        TranslationLine(expected_translation, DEFAULT_LANGUAGE, None),
    )
    line = LineFactory.build(translation=translation_lines)
    assert LineDisplay.of_line(line) == LineDisplay(
        line.number, line.variants[0].reconstruction, expected_translation
    )


def test_chapter_display_of_chapter() -> None:
    text = TextFactory.build()
    chapter = ChapterFactory.build()
    assert ChapterDisplay.of_chapter(text, chapter) == ChapterDisplay(
        chapter.id_,
        text.name,
        tuple(LineDisplay.of_line(line) for line in chapter.lines),
    )
