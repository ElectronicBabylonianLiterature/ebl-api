import re
import pytest
from ebl.fragmentarium.transliteration_query import TransliterationQuery


SIGNS = (
    'KU NU IGI\n'
    'GI₆ DIŠ GI₆ UD MI\n'
    'KI DU U BA MA TI\n'
    'X MU TA MA UD'
)


FRAGMENT = {
    'transliteration': (
        '1\'. [...-ku]-nu-ši [...]\n'
        '\n'
        '@(obeverse)\n'
        '2\'. [...] GI₆ ana GI₆ u₄-m[i ...]\n'
        '3\'. [... k]i-du u ba-ma-t[i ...]\n'
        '6\'. [...] x mu ta-ma-tu₂\n'
    ),
    'signs': SIGNS
}


REGEXP_DATA = [
    ([['DU', 'U']], True),
    ([['KU']], True),
    ([['UD']], True),
    ([
        ['GI₆', 'DIŠ'],
        ['U', 'BA', 'MA']
    ], True),
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
        [['3\'. [... k]i-du u ba-ma-t[i ...]']]
    ),
    (
        [['GI₆']],
        [['2\'. [...] GI₆ ana GI₆ u₄-m[i ...]']]
    ),
    (
        [['GI₆', 'DIŠ'], ['U', 'BA', 'MA']],
        [[
            '2\'. [...] GI₆ ana GI₆ u₄-m[i ...]',
            '3\'. [... k]i-du u ba-ma-t[i ...]'
        ]]
    ),
    (
        [['NU', 'IGI'], ['GI₆', 'DIŠ']],
        [[
            '1\'. [...-ku]-nu-ši [...]',
            '2\'. [...] GI₆ ana GI₆ u₄-m[i ...]'
        ]]
    ),
    (
        [['MA']],
        [
            ['3\'. [... k]i-du u ba-ma-t[i ...]'],
            ['6\'. [...] x mu ta-ma-tu₂']
        ]
    )
]


@pytest.mark.parametrize("query,expected", GET_MATCHING_LINES_DATA)
def test_get_matching_lines(query, expected):
    query = TransliterationQuery(query)
    lines = query.get_matching_lines(FRAGMENT)
    assert lines == expected
