"""Parsed-word test cases, part 5 of 5."""

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    IntentionalOmission,
    LinguisticGloss,
)
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Grapheme,
    Logogram,
    Reading,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import (
    InWordNewline,
    Word,
)

WORD_CASES = [
    (
        "ša#-[<(mu-un-u₅)>]",
        Word.of(
            [
                Reading.of_name("ša", flags=[atf.Flag.DAMAGE]),
                Joiner.hyphen(),
                BrokenAway.open(),
                IntentionalOmission.open(),
                Reading.of_name("mu"),
                Joiner.hyphen(),
                Reading.of_name("un"),
                Joiner.hyphen(),
                Reading.of_name("u", 5),
                IntentionalOmission.close(),
                BrokenAway.close(),
            ]
        ),
    ),
    (
        "|UM×(ME.DA)|-b[i?",
        Word.of(
            [
                CompoundGrapheme.of(["UM×(ME.DA)"]),
                Joiner.hyphen(),
                Reading.of(
                    (ValueToken.of("b"), BrokenAway.open(), ValueToken.of("i")),
                    flags=[atf.Flag.UNCERTAIN],
                ),
            ]
        ),
    ),
    (
        "mu-un;-e₃",
        Word.of(
            [
                Reading.of_name("mu"),
                Joiner.hyphen(),
                Reading.of_name("un"),
                InWordNewline.of(),
                Joiner.hyphen(),
                Reading.of_name("e", 3),
            ]
        ),
    ),
    (
        "du₃-am₃{{mu-un-<(du₃)>}}",
        Word.of(
            [
                Reading.of_name("du", 3),
                Joiner.hyphen(),
                Reading.of_name("am", 3),
                LinguisticGloss.of(
                    [
                        Reading.of_name("mu"),
                        Joiner.hyphen(),
                        Reading.of_name("un"),
                        Joiner.hyphen(),
                        IntentionalOmission.open(),
                        Reading.of_name("du", 3),
                        IntentionalOmission.close(),
                    ]
                ),
            ]
        ),
    ),
    ("kurₓ", Word.of([Reading.of_name("kur", None)])),
    ("KURₓ", Word.of([Logogram.of_name("KUR", None)])),
    (
        "kurₓ(KUR)",
        Word.of([Reading.of_name("kur", None, sign=Grapheme.of(SignName("KUR")))]),
    ),
]
