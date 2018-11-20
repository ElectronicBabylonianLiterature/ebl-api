from ebl.fragmentarium.lemmatization import Lemmatization
from ebl.fragmentarium.transliteration import Transliteration


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

    expected = [
        ['&K11111'],
        ['@reverse'],
        [''],
        ['$ (end of side)'],
        ['#some notes'],
        ['=: foo'],
        ['1.', '[...]', 'šu-gid₂', 'k[u', '...]'],
        ['2.', 'x', 'X']
    ]
    assert lemmatization.tokens == [
        [
            {
                'token': token,
                'uniqueLemma': None
            }
            for token in line
        ]
        for line in expected
    ]
