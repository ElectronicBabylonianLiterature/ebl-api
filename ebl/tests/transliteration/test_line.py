import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language
from ebl.transliteration.domain.lemmatization import (LemmatizationError,
                                                      LemmatizationToken)
from ebl.transliteration.domain.line import (ControlLine, EmptyLine, Line,
                                             TextLine)
from ebl.transliteration.domain.text_parser import TEXT_LINE
from ebl.transliteration.domain.token import (BrokenAway, DEFAULT_NORMALIZED,
                                              DocumentOrientedGloss, Erasure,
                                              LanguageShift,
                                              LoneDeterminative, Side, Token,
                                              Word)

LINE_NUMBER = LineNumberLabel.from_atf('1.')


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
    line = TextLine.of_iterable(LINE_NUMBER, tokens)

    assert line.prefix == LINE_NUMBER.to_atf()
    assert line.line_number == LINE_NUMBER

    assert line == TextLine(LINE_NUMBER.to_atf(), expected_tokens)
    assert line.atf == f'1. first {code} second %sb {{third}}'


@pytest.mark.parametrize('atf', [
    '1. [{(he-pi₂ e]š-šu₂)}',
    '2. [he₂-<(pa₃)>]',
    '3. [{iti}...]',
    '4. [(x x x)]',
    '5. [...]-qa-[...]-ba-[...]',
    '6. [...+ku....] [....ku+...]',
    '7. [...] {bu} [...]',
    '8. [...]{bu} [...]',
    '9. [...] {bu}[...]',
    '10. [...]{bu}[...]',
    '11. in]-<(...)>'
])
def test_text_line_atf(atf):
    line = TEXT_LINE.parse(atf)
    assert line.atf == atf


@pytest.mark.parametrize("word,token,expected", [
    (Word('mu-bu'), Token('[...]'), ' mu-bu '),
    (Word('-mu-bu'), Token('[...]'), '-mu-bu '),
    (Word('mu-bu-'), Token('[...]'), ' mu-bu-'),
    (Word('-mu-bu-'), Token('[...]'), '-mu-bu-'),
    (Word('-mu-bu-'), LanguageShift('%sux'), ' -mu-bu- ')
])
def test_text_line_atf_partials(word, token, expected):
    line = TextLine.of_iterable(LINE_NUMBER, [
        token,
        word,
        token,
    ])
    assert line.atf == f'{line.prefix} {token.value}{expected}{token.value}'


def test_text_line_atf_partial_start():
    word = Word('-mu')
    line = TextLine.of_iterable(LINE_NUMBER, [word])
    assert line.atf == f'{line.prefix} {word.value}'


def test_text_line_atf_gloss():
    line = TextLine.of_iterable(LINE_NUMBER, [
        DocumentOrientedGloss('{('),
        Word('mu'),
        Word('bu'),
        DocumentOrientedGloss(')}')
    ])
    assert line.atf == f'{line.prefix} {{(mu bu)}}'


@pytest.mark.parametrize('erasure,expected', [
    ([Erasure('°', Side.LEFT), Erasure('\\', Side.CENTER),
      Erasure('°', Side.RIGHT)], '°\\°'),
    ([Erasure('°', Side.LEFT), Word('mu-bu'), Erasure('\\', Side.CENTER),
      Erasure('°', Side.RIGHT)], '°mu-bu\\°'),
    ([Erasure('°', Side.LEFT), Erasure('\\', Side.CENTER),  Word('mu-bu'),
      Erasure('°', Side.RIGHT)], '°\\mu-bu°'),
    ([Erasure('°', Side.LEFT),  Word('mu-bu'), Erasure('\\', Side.CENTER),
      Word('mu-bu'), Erasure('°', Side.RIGHT)], '°mu-bu\\mu-bu°'),
])
def test_text_line_atf_erasure(word, erasure, expected):
    word = Word('mu-bu')
    line = TextLine.of_iterable(LINE_NUMBER, [word, *erasure, word])
    assert line.atf == f'{line.prefix} {word.value} {expected} {word.value}'


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
        LineNumberLabel.from_atf('1.'),
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
    line = TextLine.of_iterable(LINE_NUMBER, [Word('bu')])
    lemmatization = (LemmatizationToken('bu', (WordId('nu I'),)),)
    expected = TextLine.of_iterable(
        LINE_NUMBER,
        [Word('bu', unique_lemma=(WordId('nu I'),))]
    )

    assert line.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    line = TextLine.of_iterable(LINE_NUMBER, [Word('mu')])
    lemmatization = (LemmatizationToken('bu', (WordId('nu I'),)),)
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lenght():
    line = TextLine.of_iterable(LINE_NUMBER, [Word('bu'), Word('bu')])
    lemmatization = (LemmatizationToken('bu', (WordId('nu I'),)),)
    with pytest.raises(LemmatizationError):
        line.update_lemmatization(lemmatization)


@pytest.mark.parametrize('old,new,expected', [
    (
        EmptyLine(),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('bu')]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('bu')])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('bu')]),
        ControlLine.of_single('$', Token(' single ruling')),
        ControlLine.of_single('$', Token(' single ruling'))
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('bu')]),
        TextLine.of_iterable(LineNumberLabel.from_atf('2.'), [Word('bu')]),
        TextLine.of_iterable(LineNumberLabel.from_atf('2.'), [Word('bu')])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),))
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('bu')]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),))
        ])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),))
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            LanguageShift('%sux')
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            LanguageShift('%sux')
        ])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),))
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('mu')]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('mu')])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),)),
            Word('mu', unique_lemma=(WordId('mu I'),)),
            Word('bu', unique_lemma=(WordId('nu I'),))
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu'), Word('bu')
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),)),
            Word('bu', unique_lemma=(WordId('nu I'),))
        ])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),)),
            Word('bu', unique_lemma=(WordId('nu I'),))
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu'), Word('mu'), Word('bu')
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('bu', unique_lemma=(WordId('nu I'),)),
            Word('mu'),
            Word('bu', unique_lemma=(WordId('nu I'),))
        ])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Token('{('),
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            DocumentOrientedGloss('{('),
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            DocumentOrientedGloss('{('),
        ])
    ), (
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('{ku}#?', unique_lemma=(WordId('nu I'),)),
            Word('{bu}', unique_lemma=(WordId('bu I'),)),
            Word('ku-[nu]#?', unique_lemma=(WordId('kunu I'),), alignment=4),
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('{ku#?}'),  Word('{bu}'),  Word('[k(u)-nu#?'), BrokenAway(']')
        ]),
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('{ku#?}', unique_lemma=(WordId('nu I'),)),
            Word('{bu}', unique_lemma=(WordId('bu I'),)),
            Word('[k(u)-nu#?', unique_lemma=(WordId('kunu I'),), alignment=4),
            BrokenAway(']')
        ])
    )
])
def test_merge(old: Line, new: Line, expected: Line):
    assert old.merge(new) == expected
