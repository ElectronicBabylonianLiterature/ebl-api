import re

import pytest

from ebl.atf.domain.atf import Atf
from ebl.fragmentarium.domain.transliteration_query import \
    TransliterationQuery
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.atf_parser import parse_atf

ATF = Atf(
    '1\'. [...-ku]-nu-ši [...]\n'
    '\n'
    '@obverse\n'
    '2\'. [...] GI₆ ana GI₆ u₄-m[a ...]\n'
    '3\'. [... k]i-du u ba-ma-t[a ...]\n'
    '6\'. [...] x mu ta-ma-tu₂\n'
    '7\'. šu/gid'
)

SIGNS = (
    'KU NU IGI\n'
    'GI₆ DIŠ GI₆ UD MA\n'
    'KI DU U BA MA TA\n'
    'X MU TA MA UD\n'
    'ŠU/BU'
)

REGEXP_DATA = [
    ([['DU', 'U']], True),
    ([['KU']], True),
    ([['UD']], True),
    ([
        ['GI₆', 'DIŠ'],
        ['U', 'BA', 'MA']
    ], True),
    ([['ŠU']], True),
    ([['IGI', 'UD']], False),
    ([['|U.BA|']], False),
]


@pytest.mark.parametrize("signs,is_match", REGEXP_DATA)
def test_regexp(signs, is_match):
    query = TransliterationQuery(signs)
    match = re.search(query.regexp, SIGNS)

    if is_match:
        assert match is not None
    else:
        assert match is None


GET_MATCHING_LINES_DATA = [
    (
        [['KU', 'NU']],
        [['1\'. [...-ku]-nu-ši [...]']]
    ),
    (
        [['U', 'BA', 'MA']],
        [['3\'. [... k]i-du u ba-ma-t[a ...]']]
    ),
    (
        [['GI₆']],
        [['2\'. [...] GI₆ ana GI₆ u₄-m[a ...]']]
    ),
    (
        [['GI₆', 'DIŠ'], ['U', 'BA', 'MA']],
        [[
            '2\'. [...] GI₆ ana GI₆ u₄-m[a ...]',
            '3\'. [... k]i-du u ba-ma-t[a ...]'
        ]]
    ),
    (
        [['NU', 'IGI'], ['GI₆', 'DIŠ']],
        [[
            '1\'. [...-ku]-nu-ši [...]',
            '2\'. [...] GI₆ ana GI₆ u₄-m[a ...]'
        ]]
    ),
    (
        [['MA']],
        [
            ['2\'. [...] GI₆ ana GI₆ u₄-m[a ...]'],
            ['3\'. [... k]i-du u ba-ma-t[a ...]'],
            ['6\'. [...] x mu ta-ma-tu₂']
        ]
    ),
    (
        [['MA'], ['TA']],
        [
            [
                '2\'. [...] GI₆ ana GI₆ u₄-m[a ...]',
                '3\'. [... k]i-du u ba-ma-t[a ...]'
            ], [
                '3\'. [... k]i-du u ba-ma-t[a ...]',
                '6\'. [...] x mu ta-ma-tu₂'
            ]
        ]
    ),
    (
        [['BU']],
        [['7\'. šu/gid']]
    )
]


@pytest.mark.parametrize("query,expected", GET_MATCHING_LINES_DATA)
def test_get_matching_lines(query, expected):
    transliterated_fragment = FragmentFactory.build(
        text=parse_atf(ATF),
        signs=SIGNS
    )

    query = TransliterationQuery(query)
    lines = query.get_matching_lines(transliterated_fragment)
    assert lines == tuple(map(tuple, expected))
