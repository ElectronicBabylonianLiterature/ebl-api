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


def test_merge_no_changes():
    transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] KI DIŠ  as-tar DINGIR-šu₂\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    )
    tokens = transliteration.tokenize(lambda value: {
        'value': value,
        'uniqueLemma': [value]
    })

    lemmatization = Lemmatization(tokens)

    assert lemmatization.merge(transliteration) == lemmatization


def test_merge_add_line():
    transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    )
    tokens = transliteration.tokenize(lambda value: {
        'value': value,
        'uniqueLemma': [value]
    })

    new_transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] KI DIŠ as-tar DINGIR-šu₂\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    )
    new_tokens = new_transliteration.tokenize(lambda value: {
        'value': value,
        'uniqueLemma': []
    })

    expected_tokens = [
        tokens[0],
        new_tokens[1],
        tokens[1]
    ]

    lemmatization = Lemmatization(tokens)
    assert lemmatization.merge(new_transliteration).tokens ==\
        Lemmatization(expected_tokens).tokens


def test_merge_remove_line():
    transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] KI DIŠ as-tar DINGIR-šu₂\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    )
    tokens = transliteration.tokenize(lambda value: {
        'value': value,
        'uniqueLemma': [value]
    })

    new_transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    )

    expected_tokens = [
        tokens[0],
        tokens[2]
    ]

    lemmatization = Lemmatization(tokens)
    assert lemmatization.merge(new_transliteration).tokens ==\
        Lemmatization(expected_tokens).tokens


def test_merge_edit_line():
    transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] NA DIŠ as-tar DINGIR-šu₂\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    )
    tokens = transliteration.tokenize(lambda value: {
        'value': value,
        'uniqueLemma': [value]
    })

    new_transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] KI DIŠ as-tar DINGIR-šu₂\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    )

    expected_tokens = [
        [*tokens[0]],
        [*tokens[1]],
        [*tokens[2]]
    ]
    expected_tokens[1][2] = {
        'value': 'KI',
        'uniqueLemma': []
    }

    lemmatization = Lemmatization(tokens)
    assert lemmatization.merge(new_transliteration).tokens ==\
        Lemmatization(expected_tokens).tokens


def test_merge_edit_lines():
    transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] NA DIŠ as-tar DINGIR-šu₂\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
        '4. [...] x x an [...]'
    )
    tokens = transliteration.tokenize(lambda value: {
        'value': value,
        'uniqueLemma': [value]
    })

    new_transliteration = Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] dub₂-bu-da-na KI as-tar DINGIR-šu₂\n'
        '3. DINGIR ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
        '4. [...] x x an [...]'
    )

    expected_tokens = [
        [*tokens[0]],
        [*tokens[1]],
        [*tokens[2]],
        [*tokens[3]]
    ]
    expected_tokens[1][2] = {
        'value': 'dub₂-bu-da-na',
        'uniqueLemma': []
    }
    expected_tokens[1][3] = {
        'value': 'KI',
        'uniqueLemma': []
    }
    expected_tokens[2][1] = {
        'value': 'DINGIR',
        'uniqueLemma': []
    }

    lemmatization = Lemmatization(tokens)
    assert lemmatization.merge(new_transliteration).tokens ==\
        Lemmatization(expected_tokens).tokens
