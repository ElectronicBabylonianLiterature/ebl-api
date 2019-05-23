import pytest

from ebl.text.text_parser import ERASURE


@pytest.mark.parametrize('atf,expected', [
    ('°ku\\ku°', ['°', ['ku'], '\\', ['ku'], '°']),
    ('°\\ku°', ['°', [], '\\', ['ku'], '°']),
    ('°ku\\°', ['°', ['ku'], '\\', [], '°']),
    ('°\\°', ['°', [], '\\', [], '°']),
    ('°x X\\X x°', ['°', ['x', 'X'], '\\', ['X', 'x'], '°'])
])
def test_word(atf, expected):
    assert ERASURE.parse(atf) == expected
