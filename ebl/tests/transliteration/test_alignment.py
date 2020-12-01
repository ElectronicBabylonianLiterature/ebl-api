from ebl.transliteration.domain.alignment import Alignment, AlignmentToken
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.language import Language


def test_alignment():
    assert Alignment.from_dict(
        [
            [
                [
                    {
                        "value": "ku]-nu-ši",
                        "alignment": 1,
                        "variant": "kunusi",
                        "language": "AKKADIAN",
                        "isNormalized": True,
                    }
                ]
            ],
            [
                [
                    {
                        "value": "ku]-nu-ši",
                        "alignment": 1,
                        "variant": "kur",
                        "language": "SUMERIAN",
                        "isNormalized": False,
                    }
                ]
            ],
            [
                [
                    {
                        "value": "ku]-nu-ši",
                        "alignment": 1,
                        "variant": "",
                        "language": "AKKADIAN",
                        "isNormalized": False,
                    }
                ]
            ],
        ]
    ) == Alignment(
        (
            (
                (
                    AlignmentToken(
                        "ku]-nu-ši", 1, AkkadianWord.of([ValueToken.of("kunusi")])
                    ),
                ),
            ),
            (
                (
                    AlignmentToken(
                        "ku]-nu-ši",
                        1,
                        Word.of([Reading.of_name("kur")], language=Language.SUMERIAN),
                    ),
                ),
            ),
            ((AlignmentToken("ku]-nu-ši", 1, None),),),
        )
    )


def test_number_of_lines():
    assert (
        Alignment(
            (((AlignmentToken("ku]-nu-ši", 0),), (AlignmentToken("ku]-nu-ši", 0),)),)
        ).get_number_of_lines()
        == 1
    )


def test_number_of_manuscripts():
    assert (
        Alignment(
            (
                ((AlignmentToken("ku]-nu-ši", 0),), (AlignmentToken("ku]-nu-ši", 0),)),
                ((AlignmentToken("ku]-nu-ši", 0),),),
            )
        ).get_number_of_manuscripts(0)
        == 2
    )


def test_only_value():
    assert Alignment.from_dict([[[{"value": "ku]-nu-ši"}]]]) == Alignment(
        (((AlignmentToken("ku]-nu-ši", None),),),)
    )
