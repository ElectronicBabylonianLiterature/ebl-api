import attr
import pytest

from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.application.suggestion_finder import SuggestionFinder
from ebl.tests.factories.fragment import (
    FragmentFactory,
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Erasure,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ErasureState, Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word

COLLECTION = "fragments"


ANOTHER_LEMMATIZED_FRAGMENT = attr.evolve(
    TransliteratedFragmentFactory.build(),
    text=Text(
        (
            TextLine(
                LineNumber(1),
                (
                    Word.of(
                        [Logogram.of_name("GI", 6)], unique_lemma=(WordId("ginâ I"),)
                    ),
                    Word.of([Reading.of_name("ana")], unique_lemma=(WordId("ana II"),)),
                    Word.of([Reading.of_name("ana")], unique_lemma=(WordId("ana II"),)),
                    Word.of(
                        [
                            Reading.of_name("u", 4),
                            Joiner.hyphen(),
                            Reading.of_name("šu"),
                        ],
                        unique_lemma=(WordId("ūsu I"),),
                    ),
                    AkkadianWord.of(
                        [ValueToken.of("ana")], unique_lemma=(WordId("normalized I"),)
                    ),
                ),
            ),
        )
    ),
    signs="MI DIŠ DIŠ UD ŠU",
)


def test_query_lemmas(fragment_repository, lemma_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create_many([ANOTHER_LEMMATIZED_FRAGMENT, lemmatized_fragment])

    assert lemma_repository.query_lemmas("GI₆", False) == [["ginâ I"]]


def test_query_lemmas_normalized(fragment_repository, lemma_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create_many([lemmatized_fragment, ANOTHER_LEMMATIZED_FRAGMENT])

    assert lemma_repository.query_lemmas("ana", True) == [["normalized I"]]


def test_query_lemmas_multiple(fragment_repository, lemma_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create_many([lemmatized_fragment, ANOTHER_LEMMATIZED_FRAGMENT])

    assert lemma_repository.query_lemmas("ana", False) == [["ana II"], ["ana I"]]


@pytest.mark.parametrize(
    "parts,expected",
    [
        (
            [
                Reading.of(
                    [ValueToken.of("ana")],
                    flags=[
                        Flag.DAMAGE,
                        Flag.COLLATION,
                        Flag.UNCERTAIN,
                        Flag.CORRECTION,
                    ],
                )
            ],
            [["ana I"]],
        ),
        (
            [
                BrokenAway.open(),
                PerhapsBrokenAway.open(),
                Reading.of([ValueToken.of("ana")]),
                PerhapsBrokenAway.close(),
                BrokenAway.close(),
            ],
            [["ana I"]],
        ),
        (
            [
                Reading.of(
                    [
                        ValueToken.of("a"),
                        BrokenAway.open(),
                        ValueToken.of("n"),
                        PerhapsBrokenAway.close(),
                        ValueToken.of("a"),
                    ]
                )
            ],
            [["ana I"]],
        ),
        (
            [
                Erasure.open(),
                Erasure.center(),
                Reading.of_name("ana").set_erasure(ErasureState.OVER_ERASED),
                Erasure.close(),
            ],
            [["ana I"]],
        ),
        (
            [
                Erasure.open(),
                Reading.of_name("ana").set_erasure(ErasureState.ERASED),
                Erasure.center(),
                Erasure.close(),
            ],
            [],
        ),
    ],
)
def test_query_lemmas_ignores_in_value(
    parts, expected, fragment_repository, lemma_repository
):
    fragment = FragmentFactory.build(
        text=Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumber(1), [Word.of(parts, unique_lemma=(WordId("ana I"),))]
                )
            ]
        ),
        signs="DIŠ",
    )
    fragment_repository.create(fragment)

    assert lemma_repository.query_lemmas("ana", False) == expected


@pytest.mark.parametrize("is_normalized", [False, True])
def test_query_lemmas_not_found(is_normalized, fragment_repository, lemma_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)
    assert lemma_repository.query_lemmas("aklu", is_normalized) == []


def test_find_suggestions(dictionary, word, lemma_repository, when):
    suggestion_finder = SuggestionFinder(dictionary, lemma_repository)
    query = "GI₆"
    lemma = WordId(word["_id"])
    when(lemma_repository).query_lemmas(query, False).thenReturn([[lemma]])
    when(dictionary).find(lemma).thenReturn(word)

    assert suggestion_finder.find_lemmas(query, False) == [[word]]
