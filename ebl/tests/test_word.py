import pytest
from ebl.text.language import Language, DEFAULT_LANGUAGE
from ebl.text.lemmatization import LemmatizationToken, LemmatizationError
from ebl.text.token import (
    UniqueLemma, Token, Word, DEFAULT_NORMALIZED
)


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


@pytest.mark.parametrize("language,normalized,unique_lemma", [
    (Language.SUMERIAN, False, (UniqueLemma('ku II'), UniqueLemma('aklu I'))),
    (Language.SUMERIAN, True, tuple()),
    (Language.EMESAL, False, tuple()),
    (Language.EMESAL, True, tuple()),
    (Language.AKKADIAN, False, (UniqueLemma('aklu I'), )),
    (Language.AKKADIAN, True, tuple())
])
def test_word(language, normalized, unique_lemma):
    value = 'value'
    word = Word(value, language, normalized, unique_lemma)

    equal = Word(value, language, normalized, unique_lemma)
    other_language = Word(value, Language.UNKNOWN, normalized, unique_lemma)
    other_value = Word('other value', language, normalized, unique_lemma)
    other_unique_lemma =\
        Word(value, language, normalized, tuple(UniqueLemma('waklu I')))
    other_normalized =\
        Word('other value', language, not normalized, unique_lemma)

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
        'lemmatizable': word.lemmatizable
    }

    assert word == equal
    assert hash(word) == hash(equal)

    for not_equal in [
            other_language, other_value, other_unique_lemma, other_normalized
    ]:
        assert word != not_equal
        assert hash(word) != hash(not_equal)

    assert word != Token(value)


@pytest.mark.parametrize("word,expected", [
    (Word('un'), True),
    (Word('un', normalized=True), False),
    (Word('un', language=Language.SUMERIAN), False),
    (Word('un', language=Language.EMESAL), False),
    (Word('un-x'), False),
    (Word('X-un'), False),
    (Word('un-'), False),
    (Word('-un'), False),
    (Word('un/ia'), False)
])
def test_lemmatizable(word, expected):
    assert word.lemmatizable == expected


def test_set_language():
    value = 'value'
    unique_lemma = (UniqueLemma('aklu I'), )
    language = Language.SUMERIAN
    normalized = False
    word = Word(value, Language.AKKADIAN, not normalized, unique_lemma)
    expected_word = Word(value, language, normalized, unique_lemma)

    assert word.set_language(language, normalized) == expected_word


def test_set_unique_lemma():
    word = Word('bu')
    lemma = LemmatizationToken('bu', ('nu I', ))
    expected = Word('bu', unique_lemma=('nu I', ))

    assert word.set_unique_lemma(lemma) == expected


def test_set_unique_lemma_empty():
    word = Word('bu', Language.SUMERIAN)
    lemma = LemmatizationToken('bu', tuple())
    expected = Word('bu', Language.SUMERIAN)

    assert word.set_unique_lemma(lemma) == expected


@pytest.mark.parametrize("word", [
    Word('mu'),
    Word('bu', language=Language.SUMERIAN),
    Word('bu-x', language=Language.SUMERIAN),
    Word('X-bu', language=Language.SUMERIAN),
    Word('mu/bu', language=Language.SUMERIAN),
    Word('-bu', language=Language.SUMERIAN),
    Word('bu-', language=Language.SUMERIAN)
])
def test_set_unique_lemma_invalid(word):
    lemma = LemmatizationToken('bu', ('nu I', ))
    with pytest.raises(LemmatizationError):
        word.set_unique_lemma(lemma)


@pytest.mark.parametrize("word,expected", [
    (Word('mu-bu'), (False, False)),
    (Word('-mu-bu'), (True, False)),
    (Word('mu-bu-'), (False, True)),
    (Word('-mu-bu-'), (True, True))
])
def test_partial(word, expected):
    assert word.partial == expected
