import pytest

from ebl.sign_list.value_mapper import INVALID_READING, NotReading, Reading, \
    Variant, map_cleaned_reading

MAP_DATA = [
    ('nu', Reading('nu', 1, INVALID_READING)),
    ('šu', Reading('šu', 1, INVALID_READING)),
    ('gid₂', Reading('gid', 2, INVALID_READING)),
    ('BI', NotReading('BI')),
    ('NUₓ', NotReading('NUₓ')),
    ('BIxIS', NotReading('BIxIS')),
    ('BI×IS', NotReading('BI×IS')),
    ('|BIxIS|', NotReading('|BIxIS|')),
    ('|BI×IS|', NotReading('|BI×IS|')),
    ('|BI.IS|', NotReading('|BI.IS|')),
    ('|BI+IS|', NotReading('|BI+IS|')),
    ('|BI&IS|', NotReading('|BI&IS|')),
    ('|BI%IS|', NotReading('|BI%IS|')),
    ('|BI@IS|', NotReading('|BI@IS|')),
    ('|3×BI|', NotReading('|3×BI|')),
    ('|3xBI|', NotReading('|3xBI|')),
    ('|GEŠTU~axŠE~a@t|', NotReading('|GEŠTU~axŠE~a@t|')),
    ('|(GI&GI)×ŠE₃|', NotReading('|(GI&GI)×ŠE₃|')),
    ('unknown', Reading('unknown', 1, INVALID_READING)),
    ('nuₓ', NotReading('?')),
    ('x', NotReading('X')),
    ('X', NotReading('X')),
    ('1(AŠ)', NotReading('AŠ')),
    # 1, 2, 5, 10, 20, 30 should be inserted manually to the sign list
    ('1', Reading('1', 1, '1')),
    ('foo(TUKUL)', NotReading('TUKUL')),
    ('šu/gid₂', Variant((
        Reading('šu', 1, INVALID_READING),
        Reading('gid', 2, INVALID_READING)
    ))),
    ('šu/gid₂/nu', Variant((
        Reading('šu', 1, INVALID_READING),
        Reading('gid', 2, INVALID_READING),
        Reading('nu', 1, INVALID_READING)
    ))),
    ('šu/|BI×IS|', Variant((
        Reading('šu', 1, INVALID_READING),
        NotReading('|BI×IS|')
    ))),
    ('|BI×IS|/šu', Variant((
        NotReading('|BI×IS|'),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('šu/|BI×IS|/nu', Variant((
        Reading('šu', 1, INVALID_READING),
        NotReading('|BI×IS|'),
        Reading('nu', 1, INVALID_READING)
    ))),
    ('foo(TUKUL)/šu', Variant((
        NotReading('TUKUL'),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('šu/1(AŠ)', Variant((
        Reading('šu', 1, INVALID_READING),
        NotReading('AŠ')
    ))),
    ('256/nu', Variant((
        Reading('256', 1, '256'),
        Reading('nu', 1, INVALID_READING)
    ))),
    ('x/nu', Variant((NotReading('X'), Reading('nu', 1, INVALID_READING)))),
    ('nu/unknown', Variant((
        Reading('nu', 1, INVALID_READING),
        Reading('unknown', 1, INVALID_READING)
    ))),
    ('unknown/x', Variant((
        Reading('unknown', 1, INVALID_READING),
        NotReading('X')
    ))),
    ('', NotReading(''))
]


@pytest.mark.parametrize("value,expected", MAP_DATA)
def test_create_value_mapper2(value, expected):
    assert map_cleaned_reading(value) == expected
