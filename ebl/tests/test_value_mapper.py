import pytest
from ebl.sign_list.value_mapper import create_value_mapper


MAP_DATA = [
    ('nu', 'NU'),
    ('šu', 'ŠU'),
    ('gid₂', 'BU'),
    ('BI', 'BI'),
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
    ('unknown', '?'),
    ('x', 'X'),
    ('X', 'X'),
    ('1(AŠ)', 'AŠ'),
    # 1, 2, 5, 10, 20, 30 should be inserted manually to the sign list
    ('1', 'DIŠ'),
    ('10', 'U'),
    ('2', '2'),
    ('20', '20'),
    ('30', '30'),
    ('256', '256'),
    ('foo(TUKUL)', 'TUKUL'),
    ('šu/gid₂', 'ŠU/BU'),
    ('šu/gid₂/nu', 'ŠU/BU/NU'),
    ('šu/|BI×IS|', 'ŠU/|BI×IS|'),
    ('|BI×IS|/šu', '|BI×IS|/ŠU'),
    ('šu/|BI×IS|/nu', 'ŠU/|BI×IS|/NU'),
    ('foo(TUKUL)/šu', 'TUKUL/ŠU'),
    ('šu/1(AŠ)', 'ŠU/AŠ'),
    ('256/nu', '256/NU'),
    ('x/nu', 'X/NU'),
    ('nu/unknown', 'NU/?'),
    ('unknown/x', '?/X')
]


@pytest.mark.parametrize("value,expected", MAP_DATA)
def test_create_value_mapper(value, expected, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    value_mapper = create_value_mapper(sign_repository)

    assert value_mapper(value) == expected
