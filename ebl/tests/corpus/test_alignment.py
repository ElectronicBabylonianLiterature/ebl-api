from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.corpus.domain.text import ManuscriptLine
from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word


def test_apply() -> None:
    word = Word.of([Reading.of_name("bu")])
    alignment_index = 1
    omitted_words = (1,)
    line = ManuscriptLine(
        1, [], TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])])
    )
    alignment = ManuscriptLineAlignment(
        (AlignmentToken(word.value, alignment_index),), omitted_words
    )
    expected = ManuscriptLine(
        1,
        [],
        TextLine.of_iterable(
            LineNumber(1), [Word.of([Reading.of_name("bu")], alignment=alignment_index)]
        ),
        omitted_words=omitted_words,
    )

    assert alignment.apply(line) == expected


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
