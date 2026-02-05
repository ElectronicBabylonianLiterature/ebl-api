from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.corpus.web.alignment_schema import AlignmentSchema, AlignmentTokenSchema
from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import Word


def test_alignment() -> None:
    assert AlignmentSchema().load(
        {
            "alignment": [
                [
                    [
                        {
                            "alignment": [
                                {
                                    "value": "ku]-nu-ši",
                                    "alignment": 1,
                                    "variant": "kunusi",
                                    "type": "AkkadianWord",
                                    "language": "AKKADIAN",
                                }
                            ],
                            "omittedWords": [],
                        }
                    ],
                    [
                        {
                            "alignment": [
                                {
                                    "value": "ku]-nu-ši",
                                    "alignment": 1,
                                    "variant": "kur",
                                    "type": "Word",
                                    "language": "SUMERIAN",
                                }
                            ],
                            "omittedWords": [1],
                        }
                    ],
                    [
                        {
                            "alignment": [
                                {
                                    "value": "ku]-nu-ši",
                                    "alignment": 1,
                                    "variant": "",
                                    "type": "",
                                    "language": "",
                                }
                            ],
                            "omittedWords": [],
                        }
                    ],
                    [
                        {
                            "alignment": [
                                {
                                    "value": "ku]-nu-ši",
                                    "alignment": 1,
                                    "variant": "β",
                                    "type": "GreekWord",
                                    "language": "AKKADIAN",
                                }
                            ],
                            "omittedWords": [],
                        }
                    ],
                ]
            ]
        }
    ) == Alignment(
        (
            (
                (
                    ManuscriptLineAlignment(
                        (
                            AlignmentToken(
                                "ku]-nu-ši",
                                1,
                                AkkadianWord.of([ValueToken.of("kunusi")]),
                            ),
                        )
                    ),
                ),
                (
                    ManuscriptLineAlignment(
                        (
                            AlignmentToken(
                                "ku]-nu-ši",
                                1,
                                Word.of(
                                    [Reading.of_name("kur")], language=Language.SUMERIAN
                                ),
                            ),
                        ),
                        (1,),
                    ),
                ),
                (ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 1, None),)),),
                (
                    ManuscriptLineAlignment(
                        (
                            AlignmentToken(
                                "ku]-nu-ši",
                                1,
                                GreekWord.of(
                                    [GreekLetter.of("β")], language=Language.AKKADIAN
                                ),
                            ),
                        )
                    ),
                ),
            ),
        )
    )


def test_only_value():
    assert AlignmentTokenSchema().load({"value": "ku]-nu-ši"}) == AlignmentToken(
        "ku]-nu-ši", None
    )
