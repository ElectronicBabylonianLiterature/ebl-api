import pytest

from ebl.dictionary.domain.word import WordId
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.enclosure_tokens import BrokenAway, PerhapsBrokenAway
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.sign_tokens import (
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.tokens import (
    Joiner,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.word_tokens import (
    DEFAULT_NORMALIZED,
    ErasureState,
    Word,
)

LEMMATIZABLE_TEST_WORDS = [
    (Word.of([Reading.of_name("un")]), True),
    (Word.of([Reading.of_name("un")], normalized=True), False),
    (Word.of([Reading.of_name("un")], language=Language.SUMERIAN), False),
    (Word.of([Reading.of_name("un")], language=Language.EMESAL), False),
    (Word.of([Reading.of_name("un"), Joiner.hyphen(), UnclearSign.of()]), False),
    (Word.of([UnidentifiedSign.of(), Joiner.hyphen(), Reading.of_name("un")]), False),
    (Word.of([Reading.of_name("un"), Joiner.hyphen()]), False),
    (Word.of([Joiner.hyphen(), Reading.of_name("un")]), False),
    (Word.of([Reading.of_name("un"), Joiner.dot()]), False),
    (Word.of([Joiner.dot(), Reading.of_name("un")]), False),
    (Word.of([Reading.of_name("un"), Joiner.plus()]), False),
    (Word.of([Joiner.plus(), Reading.of_name("un")]), False),
    (Word.of([Reading.of_name("un"), Joiner.colon()]), False),
    (Word.of([Joiner.colon(), Reading.of_name("un")]), False),
    (Word.of([Variant.of(Reading.of_name("un"), Reading.of_name("ia"))]), False),
    (
        Word.of(
            [UnknownNumberOfSigns(frozenset()), Joiner.hyphen(), Reading.of_name("un")]
        ),
        False,
    ),
    (
        Word.of(
            [Reading.of_name("un"), Joiner.hyphen(), UnknownNumberOfSigns(frozenset())]
        ),
        False,
    ),
    (
        Word.of(
            parts=[
                Reading.of_name("un"),
                Joiner.hyphen(),
                UnknownNumberOfSigns(frozenset()),
                Joiner.hyphen(),
                Reading.of_name("un"),
            ]
        ),
        False,
    ),
]


def test_default_normalized():
    assert DEFAULT_NORMALIZED is False


def test_defaults():
    value = "value"
    reading = Reading.of_name(value)
    word = Word.of([reading])

    assert word.value == value
    assert word.get_key() == f"Word⁝{value}⟨{reading.get_key()}⟩"
    assert word.parts == (reading,)
    assert word.lemmatizable is True
    assert word.language == DEFAULT_LANGUAGE
    assert word.normalized is DEFAULT_NORMALIZED
    assert word.unique_lemma == tuple()
    assert word.erasure == ErasureState.NONE
    assert word.alignment is None


@pytest.mark.parametrize(
    "language,normalized,unique_lemma",
    [
        (Language.SUMERIAN, False, (WordId("ku II"), WordId("aklu I"))),
        (Language.SUMERIAN, True, tuple()),
        (Language.EMESAL, False, tuple()),
        (Language.EMESAL, True, tuple()),
        (Language.AKKADIAN, False, (WordId("aklu I"),)),
        (Language.AKKADIAN, True, tuple()),
    ],
)
def test_word(language, normalized, unique_lemma):
    value = "ku"
    parts = [Reading.of_name("ku")]
    erasure = ErasureState.NONE
    word = Word.of(parts, language, normalized, unique_lemma, erasure)

    equal = Word.of(parts, language, normalized, unique_lemma)
    other_language = Word.of(parts, Language.UNKNOWN, normalized, unique_lemma)
    other_parts = Word.of([Reading.of_name("nu")], language, normalized, unique_lemma)
    other_unique_lemma = Word.of(parts, language, normalized, tuple(WordId("waklu I")))
    other_normalized = Word.of(parts, language, not normalized, unique_lemma)
    other_erasure = Word.of(
        parts, language, normalized, unique_lemma, ErasureState.ERASED
    )
    expected_parts = f"⟨{'⁚'.join(part.get_key() for part in parts)}⟩" if parts else ""
    assert word.value == value
    assert word.get_key() == f"Word⁝{value}{expected_parts}"
    assert word.parts == tuple(parts)
    assert word.language == language
    assert word.normalized is normalized
    assert word.unique_lemma == unique_lemma

    serialized = {
        "type": "Word",
        "value": word.value,
        "uniqueLemma": [*unique_lemma],
        "normalized": normalized,
        "language": word.language.name,
        "lemmatizable": word.lemmatizable,
        "erasure": erasure.name,
        "parts": OneOfTokenSchema().dump(parts, many=True),
        "enclosureType": [type.name for type in word.enclosure_type],
    }
    assert_token_serialization(word, serialized)

    assert word == equal
    assert hash(word) == hash(equal)

    for not_equal in [
        other_language,
        other_parts,
        other_unique_lemma,
        other_normalized,
        other_erasure,
    ]:
        assert word != not_equal
        assert hash(word) != hash(not_equal)

    assert word != ValueToken.of(value)


@pytest.mark.parametrize("word,expected", LEMMATIZABLE_TEST_WORDS)
def test_lemmatizable(word, expected):
    assert word.lemmatizable == expected


@pytest.mark.parametrize("word,_", LEMMATIZABLE_TEST_WORDS)
def test_alignable(word, _):
    assert word.alignable == word.lemmatizable


def test_set_language():
    unique_lemma = (WordId("aklu I"),)
    language = Language.SUMERIAN
    normalized = False
    word = Word.of(
        [Reading.of_name("kur")], Language.AKKADIAN, not normalized, unique_lemma
    )
    expected_word = Word.of(
        [Reading.of_name("kur")], language, normalized, unique_lemma
    )

    assert word.set_language(language, normalized) == expected_word


def test_set_unique_lemma():
    word = Word.of([Reading.of_name("bu")])
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    expected = Word.of([Reading.of_name("bu")], unique_lemma=(WordId("nu I"),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_unique_lemma_empty():
    word = Word.of([Reading.of_name("bu")], Language.SUMERIAN)
    lemma = LemmatizationToken("bu", tuple())
    expected = Word.of([Reading.of_name("bu")], Language.SUMERIAN)

    assert word.set_unique_lemma(lemma) == expected


@pytest.mark.parametrize(
    "word",
    [
        Word.of([Reading.of_name("mu")]),
        Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen(), UnclearSign(frozenset())]),
        Word.of(
            [UnidentifiedSign(frozenset()), Joiner.hyphen(), Reading.of_name("bu")]
        ),
        Word.of([Variant.of(Reading.of_name("bu"), Reading.of_name("nu"))]),
        Word.of([Joiner.hyphen(), Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen()]),
    ],
)
def test_set_unique_lemma_invalid(word):
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    with pytest.raises(LemmatizationError):
        word.set_unique_lemma(lemma)


def test_set_alignment():
    word = Word.of([Reading.of_name("bu")])
    alignment = AlignmentToken("bu", 1)
    expected = Word.of([Reading.of_name("bu")], alignment=1)

    assert word.set_alignment(alignment) == expected


def test_set_alignment_empty():
    word = Word.of([Reading.of_name("bu")], Language.SUMERIAN)
    alignment = AlignmentToken("bu", None)
    expected = Word.of([Reading.of_name("bu")], Language.SUMERIAN)

    assert word.set_alignment(alignment) == expected


@pytest.mark.parametrize(
    "word",
    [
        Word.of([Reading.of_name("mu")]),
        Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen(), UnclearSign(frozenset())]),
        Word.of(
            [UnidentifiedSign(frozenset()), Joiner.hyphen(), Reading.of_name("bu")]
        ),
        Word.of([Variant.of(Reading.of_name("bu"), Reading.of_name("nu"))]),
        Word.of([Joiner.hyphen(), Reading.of_name("bu")]),
        Word.of([Reading.of_name("bu"), Joiner.hyphen()]),
    ],
)
def test_set_alignment_invalid(word):
    alignment = AlignmentToken("bu", 0)
    with pytest.raises(AlignmentError):
        word.set_alignment(alignment)


@pytest.mark.parametrize(
    "old,new,expected",
    [
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
            UnknownNumberOfSigns(frozenset()),
            UnknownNumberOfSigns(frozenset()),
        ),
        (
            Word.of(
                alignment=1,
                parts=[
                    BrokenAway.open(),
                    PerhapsBrokenAway.open(),
                    Reading.of_name("bu"),
                    PerhapsBrokenAway.close(),
                ],
            ),
            Word.of([Reading.of_name("bu")]),
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu", flags=[*atf.Flag])]),
            Word.of([Reading.of_name("bu")]),
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
            Word.of([Reading.of_name("bu", flags=[*atf.Flag])]),
            Word.of(alignment=1, parts=[Reading.of_name("bu", flags=[*atf.Flag])],),
        ),
        (
            Word.of(unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(alignment=1, parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
            Word.of(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        ),
        (
            Word.of(
                [
                    Variant.of(
                        Reading.of([ValueToken.of("k[ur")]),
                        Reading.of([ValueToken.of("r[a")]),
                    )
                ]
            ),
            Word.of(
                [
                    Variant.of(
                        Reading.of(
                            [
                                ValueToken.of("k"),
                                BrokenAway.open(),
                                ValueToken.of("ur"),
                            ]
                        ),
                        Reading.of(
                            [ValueToken.of("r"), BrokenAway.open(), ValueToken.of("a"),]
                        ),
                    )
                ]
            ),
            Word.of(
                [
                    Variant.of(
                        Reading.of(
                            [
                                ValueToken.of("k"),
                                BrokenAway.open(),
                                ValueToken.of("ur"),
                            ]
                        ),
                        Reading.of(
                            [ValueToken.of("r"), BrokenAway.open(), ValueToken.of("a"),]
                        ),
                    )
                ]
            ),
        ),
    ],
)
def test_merge(old, new, expected):
    assert old.merge(new) == expected


@pytest.mark.parametrize(
    "word,expected",
    [
        (
            Word.of([Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu")]),
            (False, False),
        ),
        (
            Word.of(
                parts=[
                    Joiner.hyphen(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                ]
            ),
            (True, False),
        ),
        (
            Word.of(
                parts=[
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.hyphen(),
                ]
            ),
            (False, True),
        ),
        (
            Word.of(
                parts=[
                    Joiner.hyphen(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.hyphen(),
                ]
            ),
            (True, True),
        ),
        (
            Word.of(
                parts=[
                    Joiner.colon(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                ]
            ),
            (True, False),
        ),
        (
            Word.of(
                parts=[
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.colon(),
                ]
            ),
            (False, True),
        ),
        (
            Word.of(
                parts=[
                    Joiner.colon(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.colon(),
                ]
            ),
            (True, True),
        ),
        (
            Word.of(
                parts=[
                    Joiner.plus(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                ]
            ),
            (True, False),
        ),
        (
            Word.of(
                parts=[
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.plus(),
                ]
            ),
            (False, True),
        ),
        (
            Word.of(
                parts=[
                    Joiner.plus(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.plus(),
                ]
            ),
            (True, True),
        ),
        (
            Word.of(
                parts=[
                    Joiner.dot(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                ]
            ),
            (True, False),
        ),
        (
            Word.of(
                parts=[
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.dot(),
                ]
            ),
            (False, True),
        ),
        (
            Word.of(
                parts=[
                    Joiner.dot(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    Reading.of_name("bu"),
                    Joiner.dot(),
                ]
            ),
            (True, True),
        ),
        (
            Word.of(
                parts=[
                    UnknownNumberOfSigns(frozenset()),
                    Joiner.hyphen(),
                    Reading.of_name("mu"),
                ]
            ),
            (True, False),
        ),
        (
            Word.of(
                [
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    UnknownNumberOfSigns(frozenset()),
                ]
            ),
            (False, True),
        ),
        (
            Word.of(
                [
                    UnknownNumberOfSigns(frozenset()),
                    Joiner.hyphen(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    UnknownNumberOfSigns(frozenset()),
                ]
            ),
            (True, True),
        ),
    ],
)
def test_partial(word, expected):
    assert word.partial == expected
