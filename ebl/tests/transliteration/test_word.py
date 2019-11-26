import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.lemmatization import LemmatizationError, \
    LemmatizationToken
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import (UnknownNumberOfSigns,
                                               ValueToken)
from ebl.transliteration.domain.word_tokens import DEFAULT_NORMALIZED, \
    ErasureState, Word

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
    (Word('un/ia'), False),
    (Word('...-un'), False),
    (Word('un-...'), False),
    (Word('un-...-un'), False),
]


def test_default_normalized():
    assert DEFAULT_NORMALIZED is False


def test_defaults():
    value = 'value'
    word = Word(value)

    assert word.value == value
    assert word.get_key() == f'Word⁝{value}'
    assert word.parts == tuple()
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
    value = 'ku'
    parts = [Reading.of('ku')]
    erasure = ErasureState.NONE
    word = Word(value, language, normalized, unique_lemma, erasure,
                parts=parts)

    equal = Word(value, language, normalized, unique_lemma, parts=parts)
    other_language = Word(value, Language.UNKNOWN, normalized, unique_lemma)
    other_value = Word('other value', language, normalized, unique_lemma)
    other_unique_lemma =\
        Word(value, language, normalized, tuple(WordId('waklu I')))
    other_normalized =\
        Word('other value', language, not normalized, unique_lemma)
    other_erasure = Word(value, language, normalized, unique_lemma,
                         ErasureState.ERASED)

    assert word.value == value
    assert word.get_key() == \
        f'{"⁝".join(["Word", value] + [part.get_key("⁚") for part in parts])}'
    assert word.parts == tuple(parts)
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
        'erasure': erasure.name,
        'parts': [part.to_dict() for part in parts]
    }

    assert word == equal
    assert hash(word) == hash(equal)

    for not_equal in [
        other_language, other_value, other_unique_lemma, other_normalized,
        other_erasure
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
    (Word('bu', alignment=1, parts=[Reading.of('bu')]),
     UnknownNumberOfSigns(),
     UnknownNumberOfSigns()),
    (Word('nu', unique_lemma=(WordId('nu I'),), parts=[]),
     Word('nu', parts=[Reading.of('nu')]),
     Word('nu', unique_lemma=(WordId('nu I'),),
          parts=[Reading.of('nu')])),
    (Word('bu', alignment=1, unique_lemma=(WordId('nu I'),)),
     Word('bu', parts=[Reading.of('bu')]),
     Word('bu', alignment=1, unique_lemma=(WordId('nu I'),),
          parts=[Reading.of('bu')])),
    (Word('[(bu)', alignment=1),
     Word('bu', parts=[Reading.of('bu')]),
     Word('bu', alignment=1, parts=[Reading.of('bu')])),
    (Word('bu#!?*', alignment=1),
     Word('bu', parts=[Reading.of('bu')]),
     Word('bu', alignment=1, parts=[Reading.of('bu')])),
    (Word('bu', alignment=1, parts=[Reading.of('bu')]),
     Word('bu#!?*', parts=[Reading.of('bu', flags=[*atf.Flag])]),
     Word('bu#!?*', alignment=1, parts=[Reading.of('bu', flags=[*atf.Flag])])),
    (Word('bu', unique_lemma=(WordId('nu I'),), parts=[Reading.of('bu')]),
     Word('bu', language=Language.SUMERIAN, parts=[Reading.of('bu')]),
     Word('bu', language=Language.SUMERIAN, parts=[Reading.of('bu')])),
    (Word('bu', alignment=1, parts=[Reading.of('bu')]),
     Word('bu', language=Language.SUMERIAN, parts=[Reading.of('bu')]),
     Word('bu', language=Language.SUMERIAN, parts=[Reading.of('bu')])),
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
    (Word('.mu.bu.'), (True, True)),
    (Word('...-mu'), (True, False)),
    (Word('mu-...'), (False, True)),
    (Word('...-mu-...'), (True, True))
])
def test_partial(word, expected):
    assert word.partial == expected
