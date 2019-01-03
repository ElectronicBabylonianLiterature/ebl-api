# pylint: disable=W0621
import copy
import json
import pytest
from ebl.text.lemmatization import Lemmatization
from ebl.fragmentarium.transliteration import Transliteration


@pytest.fixture
def transliteration():
    return Transliteration(
        '1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
        '2. [...] NA DIŠ as-tar DINGIR-šu₂\n'
        '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
        '4. [...] x x an [...]'
    )


def create_token(value, unique_lemma=None):
    return {
        'value': value,
        'uniqueLemma': [] if unique_lemma is None else unique_lemma
    }


def create_lemmatized_token(value):
    return create_token(value, [value])


TOKENS = [[create_token('token')]]


def test_equality():
    lemmatization = Lemmatization(TOKENS)
    similar = Lemmatization(TOKENS)
    different = Lemmatization([[
        create_token('another token')
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


def test_atf():
    atf = ('1. [...-ku]-nu-ši [...]\n'
           '2. [...] GI₆ ana u₄-š[u ...]')
    transliteration = Transliteration(atf)
    lemmatization = Lemmatization.of_transliteration(transliteration)

    assert lemmatization.atf == atf


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

    expected_tokens = transliteration.tokenize(create_token)

    assert lemmatization == Lemmatization(expected_tokens)


def test_of_transliteration_empty():
    transliteration = Transliteration('')

    lemmatization = Lemmatization.of_transliteration(transliteration)

    assert lemmatization == Lemmatization([])


def test_merge_no_changes(transliteration):
    tokens = transliteration.tokenize(create_lemmatized_token)

    lemmatization = Lemmatization(tokens)

    assert lemmatization.merge(transliteration) == lemmatization


def test_merge_add_line(transliteration):
    tokens = transliteration.tokenize(create_lemmatized_token)

    lines = transliteration.atf.split('\n')
    lines.insert(2, '2. [...] mu [...]')
    new_transliteration = Transliteration('\n'.join(lines))
    new_tokens = new_transliteration.tokenize(create_token)

    expected_tokens = copy.deepcopy(tokens)
    expected_tokens.insert(2, new_tokens[2])

    lemmatization = Lemmatization(tokens)
    assert lemmatization.merge(new_transliteration).tokens ==\
        Lemmatization(expected_tokens).tokens


def test_merge_remove_line(transliteration):
    tokens = transliteration.tokenize(create_lemmatized_token)

    lines = transliteration.atf.split('\n')
    lines.pop(1)
    new_transliteration = Transliteration('\n'.join(lines))

    expected_tokens = copy.deepcopy(tokens)
    expected_tokens.pop(1)

    lemmatization = Lemmatization(tokens)
    assert lemmatization.merge(new_transliteration).tokens ==\
        Lemmatization(expected_tokens).tokens


def test_merge_edit_line(transliteration):
    tokens = transliteration.tokenize(create_lemmatized_token)

    lines = transliteration.atf.split('\n')
    lines[1] = '2. [...] KI DIŠ as-tar DINGIR-šu₂'
    new_transliteration = Transliteration('\n'.join(lines))

    expected_tokens = copy.deepcopy(tokens)
    expected_tokens[1][2] = {
        'value': 'KI',
        'uniqueLemma': []
    }

    lemmatization = Lemmatization(tokens)
    assert lemmatization.merge(new_transliteration).tokens ==\
        Lemmatization(expected_tokens).tokens


def test_merge_edit_lines(transliteration):
    tokens = transliteration.tokenize(create_lemmatized_token)

    lines = transliteration.atf.split('\n')
    lines[1] = '2. [...] dub₂-bu-da-na KI as-tar DINGIR-šu₂'
    lines[2] = '3. DINGIR ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un'
    new_transliteration = Transliteration('\n'.join(lines))

    expected_tokens = copy.deepcopy(tokens)
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


def test_is_compatible(transliteration):
    lemmatization = Lemmatization.of_transliteration(transliteration)

    assert lemmatization.is_compatible(lemmatization)
    assert lemmatization.is_compatible(
        Lemmatization.of_transliteration(transliteration)
    )


@pytest.mark.parametrize("other", [
    ('1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
     '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
     '4. [...] x x an [...]'),
    ('1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
     '2. [...] NA DIŠ as-tar DINGIR-šu₂\n'
     '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
     '4. [...] x x an [...]\n'
     '5. x x x'),
    ('1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
     '2. [...] NA as-tar DINGIR-šu₂\n'
     '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
     '4. [...] x x an [...]'),
    ('1. [...] DIŠ NA DINGIR-šu₂ [...]\n'
     '2. [...] NA DIŠ as-tar DINGIR-šu₂\n'
     '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
     '4. [...] x x an  as-tar [...]'),
    ('1. [...] DIŠ KI DINGIR-šu₂ [...]\n'
     '2. [...] NA DIŠ as-tar DINGIR-šu₂\n'
     '3. {e#}a₂#-ki-it ni₂ dub₂-bu-da-na | {giš}kiri₆-mah u₃-mu-un\n'
     '4. [...] x x an [...]'),
])
def test_is_not_compatible(other, transliteration):
    lemmatization = Lemmatization.of_transliteration(transliteration)

    assert not lemmatization.is_compatible(
        Lemmatization.of_transliteration(Transliteration(other))
    )
