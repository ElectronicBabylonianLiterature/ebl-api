import pytest

from ebl.corpus.alignment import AlignmentError, AlignmentToken
from ebl.dictionary.word import WordId
from ebl.transliteration.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.lemmatization import LemmatizationError, \
    LemmatizationToken
from ebl.transliteration.token import (DEFAULT_NORMALIZED, ErasureState, Token,
                                       Word)

LEMMATIZABLE_TEST_WORDS = [
    (Word('un'), True),
    (Word('un', normalized=True), False),
    (Word('un', language=Language.SUMERIAN), False),
    (Word('un', language=Language.EMESAL), False),
    (Word('un-x'), False),
    (Word('X-un'), False),
    (Word('un-'), False),
    (Word('-un'), False),
    (Word('un.'), False),
    (Word('.un'), False),
    (Word('un+'), False),
    (Word('+un'), False),
    (Word('un/ia'), False)
]


def test_default_normalized():
    assert DEFAULT_NORMALIZED is False


def test_defaults():
    value = 'value'
    word = Word(value)

    assert word.value == value
    assert word.lemmatizable is True
    assert word.language == DEFAULT_LANGUAGE
    assert word.normalized is DEFAULT_NORMALIZED
    assert word.unique_lemma == tuple()
    assert word.erasure == ErasureState.NONE
    assert word.alignment is None


@pytest.mark.parametrize("language,normalized,unique_lemma", [
    (Language.SUMERIAN, False, (WordId('ku II'), WordId('aklu I'))),
    (Language.SUMERIAN, True, tuple()),
    (Language.EMESAL, False, tuple()),
    (Language.EMESAL, True, tuple()),
    (Language.AKKADIAN, False, (WordId('aklu I'),)),
    (Language.AKKADIAN, True, tuple())
])
def test_word(language, normalized, unique_lemma):
    value = 'value'
    erasure = ErasureState.NONE
    word = Word(value, language, normalized, unique_lemma, erasure)

    equal = Word(value, language, normalized, unique_lemma)
    other_language = Word(value, Language.UNKNOWN, normalized, unique_lemma)
    other_value = Word('other value', language, normalized, unique_lemma)
    other_unique_lemma =\
        Word(value, language, normalized, tuple(WordId('waklu I')))
    other_normalized =\
        Word('other value', language, not normalized, unique_lemma)
    other_erasure = Word(value, language, normalized, unique_lemma,
                         ErasureState.ERASED)

    assert word.value == value
    assert word.language == language
    assert word.normalized is normalized
    assert word.unique_lemma == unique_lemma
    assert word.to_dict() == {
        'type': 'Word',
        'value': word.value,
        'uniqueLemma': [*unique_lemma],
        'normalized': normalized,
        'language': word.language.name,
        'lemmatizable': word.lemmatizable,
        'erasure': erasure.name
    }

    assert word == equal
    assert hash(word) == hash(equal)

    for not_equal in [
        other_language, other_value, other_unique_lemma, other_normalized,
        other_erasure
    ]:
        assert word != not_equal
        assert hash(word) != hash(not_equal)

    assert word != Token(value)


@pytest.mark.parametrize("word,expected", LEMMATIZABLE_TEST_WORDS)
def test_lemmatizable(word, expected):
    assert word.lemmatizable == expected


@pytest.mark.parametrize("word,_", LEMMATIZABLE_TEST_WORDS)
def test_alignable(word, _):
    assert word.alignable == word.lemmatizable


def test_set_language():
    value = 'value'
    unique_lemma = (WordId('aklu I'),)
    language = Language.SUMERIAN
    normalized = False
    word = Word(value, Language.AKKADIAN, not normalized, unique_lemma)
    expected_word = Word(value, language, normalized, unique_lemma)

    assert word.set_language(language, normalized) == expected_word


def test_set_unique_lemma():
    word = Word('bu')
    lemma = LemmatizationToken('bu', (WordId('nu I'),))
    expected = Word('bu', unique_lemma=(WordId('nu I'),))

    assert word.set_unique_lemma(lemma) == expected


def test_set_unique_lemma_empty():
    word = Word('bu', Language.SUMERIAN)
    lemma = LemmatizationToken('bu', tuple())
    expected = Word('bu', Language.SUMERIAN)

    assert word.set_unique_lemma(lemma) == expected


@pytest.mark.parametrize("word,value", [
    (Word('mu'), 'bu'),
    (Word('bu', language=Language.SUMERIAN), 'bu'),
    (Word('bu-x'), 'bu-x'),
    (Word('X-bu'), 'X-bu'),
    (Word('mu/bu'), 'mu/bu'),
    (Word('-bu'), '-bu'),
    (Word('bu-'), 'bu-')
])
def test_set_unique_lemma_invalid(word, value):
    lemma = LemmatizationToken(value, (WordId('nu I'),))
    with pytest.raises(LemmatizationError):
        word.set_unique_lemma(lemma)


def test_set_alignment():
    word = Word('bu')
    alignment = AlignmentToken('bu', 1)
    expected = Word('bu', alignment=1)

    assert word.set_alignment(alignment) == expected


def test_set_alignment_empty():
    word = Word('bu', Language.SUMERIAN)
    alignment = AlignmentToken('bu', None)
    expected = Word('bu', Language.SUMERIAN)

    assert word.set_alignment(alignment) == expected


@pytest.mark.parametrize("word,value", [
    (Word('mu'), 'bu'),
    (Word('bu', language=Language.SUMERIAN), 'bu'),
    (Word('bu-x'), 'bu-x'),
    (Word('X-bu'), 'X-bu'),
    (Word('mu/bu'), 'mu/bu'),
    (Word('-bu'), '-bu'),
    (Word('bu-'), 'bu-')
])
def test_set_alignment_invalid(word, value):
    alignment = AlignmentToken(value, 0)
    with pytest.raises(AlignmentError):
        word.set_alignment(alignment)


@pytest.mark.parametrize('old,new,expected', [
    (Word('bu', alignment=1),
     Token('...'),
     Token('...')),
    (Word('bu', alignment=1, unique_lemma=(WordId('nu I'),)),
     Word('bu'),
     Word('bu', alignment=1, unique_lemma=(WordId('nu I'),))),
    (Word('[(bu)', alignment=1),
     Word('bu'),
     Word('bu', alignment=1)),
    (Word('bu#!?*', alignment=1),
     Word('bu'),
     Word('bu', alignment=1)),
    (Word('bu', alignment=1),
     Word('bu#!?*'),
     Word('bu#!?*', alignment=1)),
    (Word('bu', unique_lemma=(WordId('nu I'),)),
     Word('bu', language=Language.SUMERIAN),
     Word('bu', language=Language.SUMERIAN)),
    (Word('bu', alignment=1),
     Word('bu', language=Language.SUMERIAN),
     Word('bu', language=Language.SUMERIAN)),
])
def test_merge(old, new, expected):
    assert old.merge(new) == expected


@pytest.mark.parametrize("word,expected", [
    (Word('mu-bu'), (False, False)),
    (Word('-mu-bu'), (True, False)),
    (Word('mu-bu-'), (False, True)),
    (Word('-mu-bu-'), (True, True)),
    (Word('+mu+bu'), (True, False)),
    (Word('mu+bu+'), (False, True)),
    (Word('+mu+bu+'), (True, True)),
    (Word('.mu.bu'), (True, False)),
    (Word('mu.bu.'), (False, True)),
    (Word('.mu.bu.'), (True, True))
])
def test_partial(word, expected):
    assert word.partial == expected
