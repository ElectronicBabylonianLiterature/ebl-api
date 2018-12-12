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


@pytest.mark.parametrize("language,unique_lemma", [
    (Language.SUMERIAN, None),
    (Language.EMESAL, tuple()),
    (Language.AKKADIAN, tuple(UniqueLemma('aklu I'))),
])
def test_word(language, unique_lemma):
    value = 'value'
    expected_unique_lemma = (
        tuple()
        if unique_lemma is None
        else unique_lemma
    )

    def create_word():
        return (
            Word(value, language)
            if unique_lemma is None
            else Word(value, language, unique_lemma)
        )

    word = create_word()

    equal = create_word()
    other_language = Word(value, Language.UNKNOWN, expected_unique_lemma)
    other_value = Word('other value', language, expected_unique_lemma)
    other_unique_lemma = Word(value, language, tuple(UniqueLemma('waklu I')))

    assert word.value == value
    assert word.lemmatizable is language.lemmatizable
    assert word.unique_lemma == expected_unique_lemma
    assert str(word) == value
    assert repr(word) ==\
        f'Word("{value}", "{language}", "{expected_unique_lemma}")'

    assert word == equal
    assert hash(word) == hash(equal)

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
