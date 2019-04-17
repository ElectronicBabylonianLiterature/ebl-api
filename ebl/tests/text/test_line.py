import pytest

from ebl.text.language import DEFAULT_LANGUAGE, Language
from ebl.text.lemmatization import (LemmatizationError, LemmatizationToken)
from ebl.text.line import (ControlLine, EmptyLine, Line, LineNumber, TextLine)
from ebl.text.token import (DEFAULT_NORMALIZED, DocumentOrientedGloss,
                            LanguageShift, LoneDeterminative, Token,
                            UniqueLemma, Word)


def test_line():
    prefix = '*'
    token = Token('value')
    line = Line(prefix, (token, ))

    assert line.prefix == prefix
    assert line.content == (token, )
    assert line.atf == '*value'


def test_empty_line():
    line = EmptyLine()

    assert line.prefix == ''
    assert line.content == tuple()
    assert line.atf == ''


@pytest.mark.parametrize("code,language,normalized", [
    ('%ma', Language.AKKADIAN, False),
    ('%mb', Language.AKKADIAN, False),
    ('%na', Language.AKKADIAN, False),
    ('%nb', Language.AKKADIAN, False),
    ('%lb', Language.AKKADIAN, False),
    ('%sb', Language.AKKADIAN, False),
    ('%a', Language.AKKADIAN, False),
    ('%akk', Language.AKKADIAN, False),
    ('%eakk', Language.AKKADIAN, False),
    ('%oakk', Language.AKKADIAN, False),
    ('%ur3akk', Language.AKKADIAN, False),
    ('%oa', Language.AKKADIAN, False),
    ('%ob', Language.AKKADIAN, False),
    ('%sux', Language.SUMERIAN, False),
    ('%es', Language.EMESAL, False),
    ('%n', Language.AKKADIAN, True),
    ('%foo', DEFAULT_LANGUAGE, DEFAULT_NORMALIZED)
])
def test_line_of_iterable(code, language, normalized):
    line_number = LineNumber('1.')
    tokens = [
        Word('first'),
        LanguageShift(code), Word('second'),
        LanguageShift('%sb'), LoneDeterminative('{third}')
    ]
    expected_tokens = (
        Word('first', DEFAULT_LANGUAGE, DEFAULT_NORMALIZED),
        LanguageShift(code), Word('second', language, normalized),
        LanguageShift('%sb'), LoneDeterminative(
            '{third}', Language.AKKADIAN, False
        ))
    line = TextLine.of_iterable(line_number, tokens)

    assert line.prefix == line_number
    assert line.line_number == line_number
    assert line == TextLine(line_number, expected_tokens)
    assert line.atf == f'1. first {code} second %sb {{third}}'


@pytest.mark.parametrize("word,token,expected", [
    (Word('mu-bu'), Token('[...]'), ' mu-bu '),
    (Word('-mu-bu'), Token('[...]'), '-mu-bu '),
    (Word('mu-bu-'), Token('[...]'), ' mu-bu-'),
    (Word('-mu-bu-'), Token('[...]'), '-mu-bu-'),
    (Word('-mu-bu-'), LanguageShift('%sux'), ' -mu-bu- ')
])
def test_text_line_atf_partials(word, token, expected):
    line = TextLine.of_iterable('1.', [
        token,
        word,
        token,
    ])
    assert line.atf == f'{line.prefix} {token.value}{expected}{token.value}'


def test_text_line_atf_partial_start():
    word = Word('-mu')
    line = TextLine.of_iterable('1.', [word])
    assert line.atf == f'{line.prefix} {word.value}'


def test_text_line_atf_gloss():
    line = TextLine.of_iterable('1.', [
        DocumentOrientedGloss('{('),
        Word('mu'),
        Word('bu'),
        DocumentOrientedGloss(')}')
    ])
    assert line.atf == f'{line.prefix} {{(mu bu)}}'


def test_line_of_single():
    prefix = '$'
    token = Token('only')
    line = ControlLine.of_single(prefix, token)

    assert line == ControlLine('$', (token, ))


@pytest.mark.parametrize("line,expected", [
    (ControlLine.of_single('@', Token('obverse')), {
        'type': 'ControlLine',
        'prefix': '@',
        'content': [Token('obverse').to_dict()]
    }),
    (TextLine.of_iterable(
        LineNumber('1.'),
        [
            DocumentOrientedGloss('{('),
            Word('bu')
        ]
    ), {
        'type': 'TextLine',
        'prefix': '1.',
        'content': [
            DocumentOrientedGloss('{(').to_dict(),
            Word('bu').to_dict()
        ]
    }),
    (EmptyLine(), {
        'type': 'EmptyLine',
        'prefix': '',
        'content': []
    })
])
def test_to_dict(line, expected):
    assert line.to_dict() == expected


@pytest.mark.parametrize("line", [
    ControlLine.of_single('@', Token('obverse')),
    EmptyLine()
])
def test_update_lemmatization(line):
    lemmatization = tuple(
        LemmatizationToken(token.value)
        for token in line.content
    )
    assert line.update_lemmatization(lemmatization) == line


def test_update_lemmatization_text_line():
    line = TextLine.of_iterable('1.', [Word('bu')])
    lemmatization = (LemmatizationToken('bu', ('nu I', )), )
    expected = TextLine.of_iterable(
        '1.',
        [Word('bu', unique_lemma=('nu I', ))]
    )

    assert line.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    line = TextLine.of_iterable('1.', [Word('mu')])
    lemmatization = (LemmatizationToken('bu', ('nu I', )), )
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lenght():
    line = TextLine.of_iterable('1.', [Word('bu'), Word('bu')])
    lemmatization = (LemmatizationToken('bu', ('nu I', )), )
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)


@pytest.mark.parametrize('old,new,expected', [
    (
        EmptyLine(),
        TextLine.of_iterable(LineNumber('1.'), [Word('bu')]),
        TextLine.of_iterable(LineNumber('1.'), [Word('bu')])
    ), (
        TextLine.of_iterable(LineNumber('1.'), [Word('bu')]),
        ControlLine.of_single('$', Token(' single ruling')),
        ControlLine.of_single('$', Token(' single ruling'))
    ), (
        TextLine.of_iterable(LineNumber('1.'), [Word('bu')]),
        TextLine.of_iterable(LineNumber('2.'), [Word('bu')]),
        TextLine.of_iterable(LineNumber('2.'), [Word('bu')])
    ), (
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ]),
        TextLine.of_iterable(LineNumber('1.'), [Word('bu')]),
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ])
    ), (
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ]),
        TextLine.of_iterable(LineNumber('1.'), [LanguageShift('%sux')]),
        TextLine.of_iterable(LineNumber('1.'), [LanguageShift('%sux')])
    ), (
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ]),
        TextLine.of_iterable(LineNumber('1.'), [Word('mu')]),
        TextLine.of_iterable(LineNumber('1.'), [Word('mu')])
    ), (
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), )),
            Word('mu', unique_lemma=(UniqueLemma('mu I'), )),
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ]),
        TextLine.of_iterable(LineNumber('1.'), [Word('bu'), Word('bu')]),
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), )),
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ])
    ), (
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), )),
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ]),
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu'), Word('mu'), Word('bu')
        ]),
        TextLine.of_iterable(LineNumber('1.'), [
            Word('bu', unique_lemma=(UniqueLemma('nu I'), )),
            Word('mu'),
            Word('bu', unique_lemma=(UniqueLemma('nu I'), ))
        ])
    ), (
        TextLine.of_iterable(LineNumber('1.'), [
            Token('{('),
        ]),
        TextLine.of_iterable(LineNumber('1.'), [
            DocumentOrientedGloss('{('),
        ]),
        TextLine.of_iterable(LineNumber('1.'), [
            DocumentOrientedGloss('{('),
        ])
    )
])
def test_merge(old, new, expected):
    assert old.merge(new) == expected
