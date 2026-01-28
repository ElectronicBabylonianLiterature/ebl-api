import pytest

from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import Joiner, Variant
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import Word


def test_apply() -> None:
    word = Word.of([Reading.of_name("bu")])
    alignment_index = 1
    variant = Word.of([Reading.of_name("ra")])
    alignment = AlignmentToken(word.value, alignment_index, variant)
    expected = Word.of(
        [Reading.of_name("bu")], alignment=alignment_index, variant=variant
    )

    assert alignment.apply(word) == expected


@pytest.mark.parametrize(
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
    with pytest.raises(AlignmentError):  # pyre-ignore[16]
        alignment.apply(word)
