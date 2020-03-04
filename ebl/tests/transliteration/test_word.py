import pytest

from ebl.dictionary.domain.word import WordId
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import dump_tokens
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
    (Word(parts=[Reading.of_name("un")]), True),
    (Word(parts=[Reading.of_name("un")], normalized=True), False),
    (Word(parts=[Reading.of_name("un")], language=Language.SUMERIAN), False),
    (Word(parts=[Reading.of_name("un")], language=Language.EMESAL), False),
    (Word(parts=[Reading.of_name("un"), Joiner.hyphen(), UnclearSign()]), False),
    (Word(parts=[UnidentifiedSign(), Joiner.hyphen(), Reading.of_name("un")]), False),
    (Word(parts=[Reading.of_name("un"), Joiner.hyphen()]), False),
    (Word(parts=[Joiner.hyphen(), Reading.of_name("un")]), False),
    (Word(parts=[Reading.of_name("un"), Joiner.dot()]), False),
    (Word(parts=[Joiner.dot(), Reading.of_name("un")]), False),
    (Word(parts=[Reading.of_name("un"), Joiner.plus()]), False),
    (Word(parts=[Joiner.plus(), Reading.of_name("un")]), False),
    (Word(parts=[Reading.of_name("un"), Joiner.colon()]), False),
    (Word(parts=[Joiner.colon(), Reading.of_name("un")]), False),
    (Word(parts=[Variant([Reading.of_name("un"), Reading.of_name("ia")])]), False),
    (
        Word(parts=[UnknownNumberOfSigns(), Joiner.hyphen(), Reading.of_name("un")]),
        False,
    ),
    (
        Word(parts=[Reading.of_name("un"), Joiner.hyphen(), UnknownNumberOfSigns()]),
        False,
    ),
    (
        Word(
            parts=[
                Reading.of_name("un"),
                Joiner.hyphen(),
                UnknownNumberOfSigns(),
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
    word = Word(parts=[reading])

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
    word = Word(language, normalized, unique_lemma, erasure, parts=parts)

    equal = Word(language, normalized, unique_lemma, parts=parts)
    other_language = Word(Language.UNKNOWN, normalized, unique_lemma, parts=parts)
    other_parts = Word(
        language, normalized, unique_lemma, parts=[Reading.of_name("nu")]
    )
    other_unique_lemma = Word(
        language, normalized, tuple(WordId("waklu I")), parts=parts
    )
    other_normalized = Word(language, not normalized, unique_lemma, parts=parts)
    other_erasure = Word(
        language, normalized, unique_lemma, ErasureState.ERASED, parts=parts
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
        "parts": dump_tokens(parts),
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

    assert word != ValueToken(value)


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
    word = Word(
        Language.AKKADIAN, not normalized, unique_lemma, parts=[Reading.of_name("kur")]
    )
    expected_word = Word(
        language, normalized, unique_lemma, parts=[Reading.of_name("kur")]
    )

    assert word.set_language(language, normalized) == expected_word


def test_set_unique_lemma():
    word = Word(parts=[Reading.of_name("bu")])
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    expected = Word(parts=[Reading.of_name("bu")], unique_lemma=(WordId("nu I"),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_unique_lemma_empty():
    word = Word(Language.SUMERIAN, parts=[Reading.of_name("bu")])
    lemma = LemmatizationToken("bu", tuple())
    expected = Word(Language.SUMERIAN, parts=[Reading.of_name("bu")])

    assert word.set_unique_lemma(lemma) == expected


@pytest.mark.parametrize(
    "word",
    [
        Word(parts=[Reading.of_name("mu")]),
        Word(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        Word(parts=[Reading.of_name("bu"), Joiner.hyphen(), UnclearSign()]),
        Word(parts=[UnidentifiedSign(), Joiner.hyphen(), Reading.of_name("bu")]),
        Word(parts=[Variant([Reading.of_name("bu"), Reading.of_name("nu")])]),
        Word(parts=[Joiner.hyphen(), Reading.of_name("bu")]),
        Word(parts=[Reading.of_name("bu"), Joiner.hyphen()]),
    ],
)
def test_set_unique_lemma_invalid(word):
    lemma = LemmatizationToken("bu", (WordId("nu I"),))
    with pytest.raises(LemmatizationError):
        word.set_unique_lemma(lemma)


def test_set_alignment():
    word = Word(parts=[Reading.of_name("bu")])
    alignment = AlignmentToken("bu", 1)
    expected = Word(parts=[Reading.of_name("bu")], alignment=1)

    assert word.set_alignment(alignment) == expected


def test_set_alignment_empty():
    word = Word(Language.SUMERIAN, parts=[Reading.of_name("bu")])
    alignment = AlignmentToken("bu", None)
    expected = Word(Language.SUMERIAN, parts=[Reading.of_name("bu")])

    assert word.set_alignment(alignment) == expected


@pytest.mark.parametrize(
    "word",
    [
        Word(parts=[Reading.of_name("mu")]),
        Word(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        Word(parts=[Reading.of_name("bu"), Joiner.hyphen(), UnclearSign()]),
        Word(parts=[UnidentifiedSign(), Joiner.hyphen(), Reading.of_name("bu")]),
        Word(parts=[Variant([Reading.of_name("bu"), Reading.of_name("nu")])]),
        Word(parts=[Joiner.hyphen(), Reading.of_name("bu")]),
        Word(parts=[Reading.of_name("bu"), Joiner.hyphen()]),
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
            Word(alignment=1, parts=[Reading.of_name("bu")]),
            UnknownNumberOfSigns(),
            UnknownNumberOfSigns(),
        ),
        (
            Word(
                alignment=1,
                parts=[
                    BrokenAway.open(),
                    PerhapsBrokenAway.open(),
                    Reading.of_name("bu"),
                    PerhapsBrokenAway.close(),
                ],
            ),
            Word(parts=[Reading.of_name("bu")]),
            Word(alignment=1, parts=[Reading.of_name("bu")]),
        ),
        (
            Word(alignment=1, parts=[Reading.of_name("bu", flags=[*atf.Flag])]),
            Word(parts=[Reading.of_name("bu")]),
            Word(alignment=1, parts=[Reading.of_name("bu")]),
        ),
        (
            Word(alignment=1, parts=[Reading.of_name("bu")]),
            Word(parts=[Reading.of_name("bu", flags=[*atf.Flag])]),
            Word(alignment=1, parts=[Reading.of_name("bu", flags=[*atf.Flag])],),
        ),
        (
            Word(unique_lemma=(WordId("nu I"),), parts=[Reading.of_name("bu")]),
            Word(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
            Word(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        ),
        (
            Word(alignment=1, parts=[Reading.of_name("bu")]),
            Word(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
            Word(language=Language.SUMERIAN, parts=[Reading.of_name("bu")]),
        ),
    ],
)
def test_merge(old, new, expected):
    assert old.merge(new) == expected


@pytest.mark.parametrize(
    "word,expected",
    [
        (
            Word(parts=[Reading.of_name("mu"), Joiner.hyphen(), Reading.of_name("bu")]),
            (False, False),
        ),
        (
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
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
            Word(
                parts=[UnknownNumberOfSigns(), Joiner.hyphen(), Reading.of_name("mu")]
            ),
            (True, False),
        ),
        (
            Word(
                parts=[Reading.of_name("mu"), Joiner.hyphen(), UnknownNumberOfSigns()]
            ),
            (False, True),
        ),
        (
            Word(
                parts=[
                    UnknownNumberOfSigns(),
                    Joiner.hyphen(),
                    Reading.of_name("mu"),
                    Joiner.hyphen(),
                    UnknownNumberOfSigns(),
                ]
            ),
            (True, True),
        ),
    ],
)
def test_partial(word, expected):
    assert word.partial == expected
