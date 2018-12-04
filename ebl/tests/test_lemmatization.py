import json
from ebl.fragmentarium.lemmatization import Lemmatization
from ebl.fragmentarium.transliteration import Transliteration


TOKENS = [[{'value': 'token', 'uniqueLemma': []}]]


def test_equality():
    lemmatization = Lemmatization(TOKENS)
    similar = Lemmatization(TOKENS)
    different = Lemmatization([[
        {'value': 'another token', 'uniqueLemma': []}
    ]])

    assert lemmatization == similar
    assert lemmatization != different


def test_hash():
    lemmatization = Lemmatization(TOKENS)

    assert hash(lemmatization) == hash(json.dumps(TOKENS))


def test_tokens():
    tokens = [[]]
    lemmatization = Lemmatization(tokens)

    assert lemmatization.tokens == tokens


def test_of_transliteration():
    transliteration = Transliteration(
        '&K11111\n'
        '@reverse\n'
        '\n'
        '$ (end of side)\n'
        '#some notes\n'
        '=: foo\n'
        '1. [...] šu-gid₂ k[u ...]\n'
        '2. x X'
    )

    lemmatization = Lemmatization.of_transliteration(transliteration)

    expected = transliteration.tokenize(lambda value: {
        'value': value,
        'uniqueLemma': []
    })

    assert lemmatization.tokens == expected
