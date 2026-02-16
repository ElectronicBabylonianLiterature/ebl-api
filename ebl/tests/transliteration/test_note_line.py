from typing import Sequence

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.markup import EmphasisPart, LanguagePart, StringPart
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import (
    EnclosureType,
    ErasureState,
    LanguageShift,
    Token,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import Word

TRANSLITERATION: Sequence[Token] = (
    Word.of([Reading.of_name("bu")]),
    LanguageShift.of("%es"),
    Word.of([BrokenAway.open(), Reading.of_name("kur")]),
    UnknownNumberOfSigns.of(),
    BrokenAway.close(),
)
EXPECTED_ATF = "bu %es [kur ...]"


def expected_transliteration(language: Language) -> Sequence[Token]:
    return (
        Word.of([Reading.of_name("bu")], language),
        LanguageShift.of("%es"),
        Word.of(
            [
                BrokenAway.open(),
                Reading.of(
                    (
                        ValueToken(
                            frozenset({EnclosureType.BROKEN_AWAY}),
                            ErasureState.NONE,
                            "kur",
                        ),
                    )
                ).set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
            ],
            Language.EMESAL,
        ),
        UnknownNumberOfSigns(frozenset({EnclosureType.BROKEN_AWAY}), ErasureState.NONE),
        BrokenAway.close().set_enclosure_type(frozenset({EnclosureType.BROKEN_AWAY})),
    )


def test_note_line():
    parts = (
        StringPart("this is a note "),
        EmphasisPart("italic text"),
        LanguagePart.of_transliteration(Language.AKKADIAN, TRANSLITERATION),
        LanguagePart.of_transliteration(Language.SUMERIAN, TRANSLITERATION),
        LanguagePart.of_transliteration(Language.EMESAL, TRANSLITERATION),
    )
    line = NoteLine(parts)

    assert line.parts == (
        StringPart("this is a note "),
        EmphasisPart("italic text"),
        LanguagePart(Language.AKKADIAN, expected_transliteration(Language.AKKADIAN)),
        LanguagePart(Language.SUMERIAN, expected_transliteration(Language.SUMERIAN)),
        LanguagePart(Language.EMESAL, expected_transliteration(Language.EMESAL)),
    )
    assert line.atf == (
        "#note: this is a note "
        "@i{italic text}"
        f"@akk{{{EXPECTED_ATF}}}@sux{{{EXPECTED_ATF}}}@es{{{EXPECTED_ATF}}}"
    )
    assert line.lemmatization == (
        LemmatizationToken("this is a note "),
        LemmatizationToken("@i{italic text}"),
        LemmatizationToken(f"@akk{{{EXPECTED_ATF}}}"),
        LemmatizationToken(f"@sux{{{EXPECTED_ATF}}}"),
        LemmatizationToken(f"@es{{{EXPECTED_ATF}}}"),
    )
