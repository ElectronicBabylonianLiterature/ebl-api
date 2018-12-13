import pytest
from ebl.fragmentarium.language import Language
from ebl.fragmentarium.tokens import Token, Word, UniqueLemma, Shift


def test_token():
    value = 'value'
    token = Token(value)
    equal = Token(value)
    other = Token('anothervalue')

    assert token.value == value
    assert token.lemmatizable is False
    assert str(token) == value
    assert repr(token) == f'Token("{value}")'

    assert token == equal
    assert hash(token) == hash(equal)

    assert token != other
    assert hash(token) != hash(other)

    assert token != value


def test_word_defaults():
    value = 'value'
    word = Word(value)

    assert word.value == value
    assert word.lemmatizable is True
    assert word.language == Language.AKKADIAN
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
    assert str(word) == value
    assert repr(word) ==\
        f'Word("{value}", "{language}", "{unique_lemma}")'

    assert word == equal
    assert hash(word) == hash(equal)

    for not_equal in [other_language, other_value, other_unique_lemma]:
        assert word != not_equal
        assert hash(word) != hash(not_equal)

    assert word != Token(value)
    assert word != value


@pytest.mark.parametrize("value,expected_language", [
    (r'%sux', Language.SUMERIAN,),
    (r'%es', Language.EMESAL),
    (r'%sb', Language.AKKADIAN),
    (r'%foo', Language.UNKNOWN)
])
def test_shift(value, expected_language):
    shift = Shift(value)
    equal = Shift(value)
    other = Token(r'%bar')

    assert shift.value == value
    assert shift.lemmatizable is False
    assert shift.language == expected_language
    assert str(shift) == value
    assert repr(shift) == f'Shift("{value}", "{expected_language}")'

    assert shift == equal
    assert hash(shift) == hash(equal)

    assert shift != other
    assert hash(shift) != hash(other)

    assert shift != Token(value)
    assert shift != value
