import pytest  # pyre-ignore[21]

from ebl.transliteration.domain.alignment import (
    Alignment,
    AlignmentError,
    AlignmentToken,
)
from ebl.transliteration.domain.tokens import Joiner, Variant
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.language import Language


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


def test_apply() -> None:
    word = Word.of([Reading.of_name("bu")])
    alignment_index = 1
    variant = Word.of([Reading.of_name("ra")])
    alignment = AlignmentToken(word.value, alignment_index, variant)
    expected = Word.of(
        [Reading.of_name("bu")], alignment=alignment_index, variant=variant
    )

    assert alignment.apply(word) == expected


@pytest.mark.parametrize(  # pyre-ignore[56]
    "word",
    [
        Word.of([Reading.of_name("mu")]),
        Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen(), UnclearSign.of()]),
        Word.of([UnidentifiedSign.of(), Joiner.hyphen(), Reading.of_name("bu")]),
        Word.of([Variant.of(Reading.of_name("bu"), Reading.of_name("nu"))]),
        Word.of([Joiner.hyphen(), Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen()]),
    ],
)
def test_apply_invalid(word) -> None:
    alignment = AlignmentToken("bu", 0)
    with pytest.raises(AlignmentError):
        alignment.apply(word)
