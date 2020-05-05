import pytest  # pyre-ignore

from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NoteLine,
    StringPart,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word


TRANSLITERATION = (Word.of([Reading.of_name("bu")]),)


def test_note_line():
    parts = (
        StringPart("this is a note "),
        EmphasisPart("italic text"),
        LanguagePart(Language.AKKADIAN, TRANSLITERATION),
        LanguagePart(Language.SUMERIAN, TRANSLITERATION),
    )
    line = NoteLine(parts)

    assert line.parts == parts
    assert line.prefix == "#note: "
    assert line.atf == (
        "#note: this is a note "
        "@i{italic text}@akk{bu}@sux{bu}"
    )
    assert line.content == [
        ValueToken.of("this is a note "),
        ValueToken.of("@i{italic text}"),
        ValueToken.of("@akk{bu}"),
        ValueToken.of("@sux{bu}"),
    ]


def test_invalid_language():
    with (pytest.raises(ValueError)):
        LanguagePart(Language.EMESAL, TRANSLITERATION)
