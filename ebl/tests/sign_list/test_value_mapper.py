import pytest

from ebl.sign_list.value_mapper import map_cleaned_reading, Reading, \
    UNKNOWN_SIGN

MAP_DATA = [
    ('nu', Reading('nu', 1, UNKNOWN_SIGN)),
    ('šu', Reading('šu', 1, UNKNOWN_SIGN)),
    ('gid₂', Reading('gid', 2, UNKNOWN_SIGN)),
    ('BI', 'BI'),
    ('NUₓ', 'NUₓ'),
    ('BIxIS', 'BIxIS'),
    ('BI×IS', 'BI×IS'),
    ('|BIxIS|', '|BIxIS|'),
    ('|BI×IS|', '|BI×IS|'),
    ('|BI.IS|', '|BI.IS|'),
    ('|BI+IS|', '|BI+IS|'),
    ('|BI&IS|', '|BI&IS|'),
    ('|BI%IS|', '|BI%IS|'),
    ('|BI@IS|', '|BI@IS|'),
    ('|3×BI|', '|3×BI|'),
    ('|3xBI|', '|3xBI|'),
    ('|GEŠTU~axŠE~a@t|', '|GEŠTU~axŠE~a@t|'),
    ('|(GI&GI)×ŠE₃|', '|(GI&GI)×ŠE₃|'),
    ('unknown', Reading('unknown', 1, UNKNOWN_SIGN)),
    ('nuₓ', '?'),
    ('x', 'X'),
    ('X', 'X'),
    ('1(AŠ)', 'AŠ'),
    # 1, 2, 5, 10, 20, 30 should be inserted manually to the sign list
    ('1', Reading('1', 1, '1')),
    ('foo(TUKUL)', 'TUKUL'),
    ('šu/gid₂',
     [Reading('šu', 1, UNKNOWN_SIGN), Reading('gid', 2, UNKNOWN_SIGN)]),
    ('šu/gid₂/nu',
     [Reading('šu', 1, UNKNOWN_SIGN), Reading('gid', 2, UNKNOWN_SIGN),
      Reading('nu', 1, UNKNOWN_SIGN)]),
    ('šu/|BI×IS|', [Reading('šu', 1, UNKNOWN_SIGN), '|BI×IS|']),
    ('|BI×IS|/šu', ['|BI×IS|', Reading('šu', 1, UNKNOWN_SIGN)]),
    ('šu/|BI×IS|/nu', [
        Reading('šu', 1, UNKNOWN_SIGN),
        '|BI×IS|',
        Reading('nu', 1, UNKNOWN_SIGN)
    ]),
    ('foo(TUKUL)/šu', ['TUKUL', Reading('šu', 1, UNKNOWN_SIGN)]),
    ('šu/1(AŠ)', [Reading('šu', 1, UNKNOWN_SIGN), 'AŠ']),
    ('256/nu', [Reading('256', 1, '256'), Reading('nu', 1, UNKNOWN_SIGN)]),
    ('x/nu', ['X', Reading('nu', 1, UNKNOWN_SIGN)]),
    ('nu/unknown',
     [Reading('nu', 1, UNKNOWN_SIGN), Reading('unknown', 1, UNKNOWN_SIGN)]),
    ('unknown/x', [Reading('unknown', 1, UNKNOWN_SIGN), 'X'])
]


@pytest.mark.parametrize("value,expected", MAP_DATA)
def test_create_value_mapper2(value, expected):
    assert map_cleaned_reading(value) == expected
