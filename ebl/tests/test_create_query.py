import re
import pytest
from ebl.fragmentarium.queries import create_query


TEXT = (
    'KU NU IGI\n'
    'GI₆ DIŠ UD MI\n'
    'KI DU U BA MA TI\n'
    'X MU TA MA UD'
)


TEST_DATA = [
    ([['DIŠ', 'UD']], True),
    ([['KU']], True),
    ([['UD']], True),
    ([
        ['GI₆', 'DIŠ'],
        ['U', 'BA', 'MA']
    ], True),
    ([['IGI', 'UD']], False),
    ([['|U.BA|']], False),
]


@pytest.mark.parametrize("signs,is_match", TEST_DATA)
def test_create_query(signs, is_match):
    query = create_query(signs)
    match = re.search(query, TEXT)
    print(query)
    if is_match:
        assert match is not None
    else:
        assert match is None
