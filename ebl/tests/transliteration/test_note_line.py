import pytest  # pyre-ignore

from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NoteLine,
    StringPart,
)
from ebl.transliteration.domain.tokens import ValueToken


def test_note_line():
    parts = (
        StringPart("this is a note "),
        EmphasisPart("italic text"),
        LanguagePart("Akkadian language", Language.AKKADIAN),
        LanguagePart("Sumerian language", Language.SUMERIAN),
    )
    line = NoteLine(parts)

    assert line.parts == parts
    assert line.prefix == "#note: "
    assert line.atf == (
        "#note: this is a note "
        "@i{italic text}@akk{Akkadian language}@sux{Sumerian language}"
    )
    assert line.content == [
        ValueToken.of("this is a note "),
        ValueToken.of("@i{italic text}"),
        ValueToken.of("@akk{Akkadian language}"),
        ValueToken.of("@sux{Sumerian language}"),
    ]


def test_invalid_language():
    with (pytest.raises(ValueError)):
        LanguagePart("bad language", Language.EMESAL)
