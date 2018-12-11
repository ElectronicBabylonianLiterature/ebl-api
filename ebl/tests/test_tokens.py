from ebl.fragmentarium.tokens import Token


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

    assert token == equal
    assert hash(token) == hash(equal)

    assert token != other
    assert hash(token) != hash(other)

    assert token != value
