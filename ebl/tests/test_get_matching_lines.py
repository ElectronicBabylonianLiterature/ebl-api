import pytest
from ebl.fragmentarium.queries import create_query
from ebl.fragmentarium.queries import get_matching_lines


TRANSLITERATION = (
    '1\'. [...-ku]-nu-ši [...]\n'
    '\n'
    '@(obeverse)\n'
    '2\'. [...] GI₆ ana GI₆ u₄-m[i ...]\n'
    '3\'. [... k]i-du u ba-ma-t[i ...]\n'
    '6\'. [...] x mu ta-ma-tu₂\n'
)


SIGNS = (
    'KU NU IGI\n'
    'GI₆ DIŠ GI₆ UD MI\n'
    'KI DU U BA MA TI\n'
    'X MU TA MA UD'
)


TEST_DATA = [
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


@pytest.mark.parametrize("query,expected", TEST_DATA)
def test_get_matching_lines(query, expected):
    regexp = create_query(query)
    lines = get_matching_lines(TRANSLITERATION, SIGNS, regexp)
    assert lines == expected
