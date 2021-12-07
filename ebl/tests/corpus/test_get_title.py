from ebl.corpus.domain.chapter import get_title
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.translation_line import TranslationLine

TRANSLATION = (
    TranslationLine([StringPart("not the title")], "de"),
    TranslationLine([StringPart("the title,")], "en"),
)


def test_get_title() -> None:
    assert get_title(TRANSLATION) == (StringPart("The Title"),)
