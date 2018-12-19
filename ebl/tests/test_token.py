import pytest
from ebl.fragmentarium.language import Language, DEFAULT_LANGUAGE
from ebl.fragmentarium.token import UniqueLemma, Token, Word, LanguageShift


def test_token():
    value = 'value'
    token = Token(value)
    equal = Token(value)
    other = Token('anothervalue')

    assert token.value == value
    assert token.lemmatizable is False

    assert token == equal
    assert hash(token) == hash(equal)

    assert token != other
    assert hash(token) != hash(other)


def test_word_defaults():
    value = 'value'
    word = Word(value)

    assert word.value == value
    assert word.lemmatizable is True
    assert word.language == DEFAULT_LANGUAGE
    assert word.unique_lemma == tuple()


@pytest.mark.parametrize("language,unique_lemma", [
    (Language.SUMERIAN, (UniqueLemma('ku II'), UniqueLemma('aklu I'))),
    (Language.EMESAL, tuple()),
    (Language.AKKADIAN, (UniqueLemma('aklu I'), )),
])
def test_word(language, unique_lemma):
    value = 'value'
    word = Word(value, language, unique_lemma)

    equal = Word(value, language, unique_lemma)
    other_language = Word(value, Language.UNKNOWN, unique_lemma)
    other_value = Word('other value', language, unique_lemma)
    other_unique_lemma = Word(value, language, tuple(UniqueLemma('waklu I')))

    assert word.value == value
    assert word.lemmatizable is language.lemmatizable
    assert word.language == language
    assert word.unique_lemma == unique_lemma

    assert word == equal
    assert hash(word) == hash(equal)

    for not_equal in [other_language, other_value, other_unique_lemma]:
        assert word != not_equal
        assert hash(word) != hash(not_equal)

    assert word != Token(value)


def test_word_set_language():
    value = 'value'
    unique_lemma = (UniqueLemma('aklu I'), )
    language = Language.SUMERIAN
    word = Word(value, Language.AKKADIAN, unique_lemma)
    expected_word = Word(value, language, unique_lemma)

    assert word.set_language(language) == expected_word


@pytest.mark.parametrize("value,expected_language", [
    (r'%sux', Language.SUMERIAN,),
    (r'%es', Language.EMESAL),
    (r'%sb', Language.AKKADIAN),
    (r'%foo', Language.UNKNOWN)
])
def test_language_shift(value, expected_language):
    shift = LanguageShift(value)
    equal = LanguageShift(value)
    other = Token(r'%bar')

    assert shift.value == value
    assert shift.lemmatizable is False
    assert shift.language == expected_language

    assert shift == equal
    assert hash(shift) == hash(equal)

    assert shift != other
    assert hash(shift) != hash(other)

    assert shift != Token(value)
